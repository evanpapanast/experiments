"""Build the published data files and the report data for the Customer 360 experiment.

Input : data/bigquery_extract.json  (output of sql/05_extract.sql, group totals only)
Output: data/*.csv, data/manifest.json, dashboard/data.js

Every number in the report is calculated here from the extract, so the report and the CSV files always agree.
Only the Python standard library is used.

Usage: python 01_build_report_data.py
"""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"
X = json.loads((D / "bigquery_extract.json").read_text(encoding="utf-8"))

CHANNELS = ["Email", "Google Ads", "Facebook", "YouTube", "Organic"]
SEGMENTS = ["Champions", "Loyal", "New", "At risk", "One-time buyers", "Lapsed", "Never bought"]
WINDOW = "20 Nov 2024 - 19 Nov 2026"


def pct(a, b):
    return round(a / b, 4) if b else None


def write_csv(name, rows, cols):
    with open(D / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main():
    seg = {r["segment"]: r for r in X["segments"]}
    chp = {r["channel"]: r for r in X["channel_purchase"]}
    fun = {r["channel"]: r for r in X["funnel"]}
    rep = {r["channel"]: r for r in X["repeat_by_first_channel"]}
    pref_buyers = {c: sum(r["customers"] for r in X["region_channel"] if r["preferred_channel"] == c) for c in CHANNELS}

    # ---------- headline KPIs ----------
    buyers_segs = ["Champions", "Loyal", "New", "At risk", "One-time buyers"]
    net = sum(seg[s]["net_revenue"] for s in buyers_segs)
    gm = sum(seg[s]["gross_margin"] for s in buyers_segs)
    returned = sum(seg[s]["returned_value"] for s in buyers_segs)
    gross_sales = sum(seg[s]["gross_sales"] for s in buyers_segs)
    cancelled = sum(r["cancelled_value"] for r in X["channel_purchase"])
    orders = sum(seg[s]["orders"] for s in buyers_segs)
    buyers = sum(seg[s]["customers"] for s in buyers_segs)
    repeaters = sum(seg[s]["customers"] for s in ["Champions", "Loyal", "At risk"])
    registered = sum(r["customers"] for r in X["segments"])
    net_12m = sum(seg[s]["net_revenue_12m"] for s in buyers_segs)
    ordered_value = gross_sales + cancelled
    kpi = {
        "net_revenue": net, "gross_margin": gm, "gm_pct": pct(gm, net), "product_cost": net - gm,
        "buyers": buyers, "registered": registered, "inactive": seg["Lapsed"]["customers"] + seg["Never bought"]["customers"],
        "orders": orders, "aov": round(net / orders, 2), "repeat_rate": pct(repeaters, buyers),
        "ordered_value": ordered_value, "cancelled_value": cancelled, "cancel_rate": pct(cancelled, ordered_value),
        "returned_value": returned, "return_rate": pct(returned, gross_sales),
        "net_last_12m": net_12m, "net_prior_12m": net - net_12m, "growth_12m": pct(net_12m - (net - net_12m), net - net_12m),
    }

    # ---------- channels (purchase visit) ----------
    channels = []
    for c in CHANNELS:
        p, f, r = chp[c], fun[c], rep[c]
        channels.append({
            "channel": c, "orders": p["orders"], "customers": p["customers"],
            "net_revenue": p["net_revenue"], "revenue_share": pct(p["net_revenue"], net),
            "product_cost": p["product_cost"], "gross_margin": p["net_revenue"] - p["product_cost"],
            "gm_pct": pct(p["net_revenue"] - p["product_cost"], p["net_revenue"]),
            "returned_value": p["returned_value"], "return_rate": pct(p["returned_value"], p["gross_sales"]),
            "cancelled_value": p["cancelled_value"], "cancel_rate": pct(p["cancelled_value"], p["gross_sales"] + p["cancelled_value"]),
            "aov": round(p["net_revenue"] / p["orders"], 2),
            "sessions": f["sessions"], "visit_to_purchase": pct(f["purchase"], f["sessions"]),
            "visit_to_cart": pct(f["cart"], f["sessions"]), "cart_to_purchase": pct(f["purchase"], f["cart"]),
            "repeat_rate_first_channel": pct(r["repeaters"], r["first_buyers"]),
            "preferred_by_buyers": pref_buyers[c], "preferred_share": pct(pref_buyers[c], buyers),
        })
    write_csv("channels.csv", channels, list(channels[0].keys()))

    # ---------- acquisition channel ----------
    acq = []
    for r in sorted(X["channel_acquisition"], key=lambda r: -r["net_revenue"]):
        acq.append({**r, "revenue_share": pct(r["net_revenue"], net), "buyer_rate": pct(r["buyers"], r["registered"]),
                    "repeat_rate": pct(r["repeat_buyers"], r["buyers"]), "revenue_per_buyer": round(r["net_revenue"] / r["buyers"], 2),
                    "gm_pct": pct(r["gross_margin"], r["net_revenue"])})
    write_csv("acquisition_channels.csv", acq, list(acq[0].keys()))

    # ---------- segments ----------
    seg_info = {
        "Champions": ("3+ orders, last order within 6 months", "Keep them: early access, loyalty perks. Do not discount."),
        "Loyal": ("2 orders, last order within 6 months", "Turn into Champions: third-order offer in their favourite category."),
        "New": ("First order in the last 90 days", "Get the second order within 60 days: welcome series by email."),
        "At risk": ("2+ orders, but silent for 6+ months", "Win back now: personal email with new arrivals in categories they bought."),
        "One-time buyers": ("1 order, more than 90 days ago", "Biggest pool: a second-order campaign, mainly by email and Google Ads."),
        "Lapsed": ("Bought before Nov 2024, nothing since", "Low-cost reactivation only; most no longer visit."),
        "Never bought": ("Registered, never bought", "Target the ones who still visit; leave the rest."),
    }
    segments = []
    for s in SEGMENTS:
        r = seg[s]
        mix = {x["preferred_channel"]: x["customers"] for x in X["segment_channel"] if x["segment"] == s}
        visiting = sum(v for k, v in mix.items() if k != "No visits" and v)
        segments.append({
            "segment": s, "definition": seg_info[s][0], "action": seg_info[s][1],
            "customers": r["customers"], "customer_share": pct(r["customers"], registered),
            "net_revenue": r["net_revenue"], "revenue_share": pct(r["net_revenue"], net),
            "gross_margin": r["gross_margin"], "orders": r["orders"],
            "aov": round(r["net_revenue"] / r["orders"], 2) if r["orders"] else None,
            "revenue_per_customer": round(r["net_revenue"] / r["customers"], 2),
            "return_rate": pct(r["returned_value"], r["gross_sales"]), "net_revenue_12m": r["net_revenue_12m"],
            "visiting_customers": visiting,
            "channel_mix": {c: mix.get(c) for c in CHANNELS + ["No visits"]},
        })
    write_csv("segments.csv", [{k: v for k, v in s.items() if k != "channel_mix"} for s in segments],
              [k for k in segments[0] if k != "channel_mix"])
    write_csv("segment_channel.csv", X["segment_channel"], ["segment", "preferred_channel", "customers", "net_revenue"])

    # ---------- demographics, regions, categories, monthly ----------
    demo = []
    for r in X["demographics"]:
        demo.append({**r, "buyer_rate": pct(r["buyers"], r["customers"]), "revenue_per_buyer": round(r["net_revenue"] / r["buyers"], 2),
                     "gm_pct": pct(r["gross_margin"], r["net_revenue"]), "return_rate": pct(r["returned_value"], r["gross_sales"])})
    write_csv("demographics.csv", demo, list(demo[0].keys()))
    write_csv("region_channel.csv", X["region_channel"], ["region", "preferred_channel", "customers"])

    cats = []
    for r in X["category"]:
        cats.append({"category": f'{r["category"]} ({r["department"]})', **{k: r[k] for k in ("net_revenue", "gross_margin", "returned_value", "gross_sales")},
                     "gm_pct": pct(r["gross_margin"], r["net_revenue"]), "return_rate": pct(r["returned_value"], r["gross_sales"])})
    write_csv("categories.csv", cats, list(cats[0].keys()))

    months = sorted({r["m"] for r in X["monthly"]})
    monthly = [{"month": m, **{c: next(r["r"] for r in X["monthly"] if r["m"] == m and r["c"] == c) for c in CHANNELS},
                "gross_margin": sum(r["g"] for r in X["monthly"] if r["m"] == m)} for m in months]
    write_csv("monthly_by_channel.csv", monthly, ["month"] + CHANNELS + ["gross_margin"])

    # ---------- opportunity sizing (what-if on real averages; the rate is set by the reader) ----------
    nb_visitors = segments[SEGMENTS.index("Never bought")]["visiting_customers"]
    opps = [
        {"id": "second", "label": "One-time buyers place a second order", "pool": seg["One-time buyers"]["customers"],
         "value": round(seg["One-time buyers"]["net_revenue"] / seg["One-time buyers"]["orders"], 2), "basis": "their own average order value"},
        {"id": "winback", "label": "At-risk customers come back for one order", "pool": seg["At risk"]["customers"],
         "value": round(seg["At risk"]["net_revenue"] / seg["At risk"]["orders"], 2), "basis": "their own average order value"},
        {"id": "first", "label": "Registered visitors who never bought place a first order", "pool": nb_visitors,
         "value": round(seg["New"]["net_revenue"] / seg["New"]["orders"], 2), "basis": "average first order of New customers"},
        {"id": "cancel", "label": "Cancelled order value is saved", "pool": cancelled, "value": 1, "basis": "cancelled value in the period", "money_pool": True},
        {"id": "returns", "label": "Returned order value is kept", "pool": returned, "value": 1, "basis": "returned value in the period", "money_pool": True},
    ]

    # ---------- insights (all numbers from the data above) ----------
    ch = {c["channel"]: c for c in channels}
    top2 = ch["Email"]["revenue_share"] + ch["Google Ads"]["revenue_share"]
    gm_range = (min(c["gm_pct"] for c in channels), max(c["gm_pct"] for c in channels))
    conv_range = (min(c["visit_to_purchase"] for c in channels), max(c["visit_to_purchase"] for c in channels))
    rep_range = (min(c["repeat_rate_first_channel"] for c in channels), max(c["repeat_rate_first_channel"] for c in channels))
    one = seg["One-time buyers"]
    meta = {
        "window": WINDOW, "snapshot": "2026-11-19", "built": "2026-11-20",
        "source": "TheLook eCommerce (bigquery-public-data.thelook_ecommerce), a fully synthetic dataset created by Google's Looker team",
        "partial_months": ["2024-11", "2026-11"],
    }
    insights = {
        "headline": [
            f"Email and Google Ads bring {top2:.0%} of net revenue. Email alone is {ch['Email']['revenue_share']:.0%}, and {ch['Email']['preferred_share']:.0%} of buyers visit mostly through email.",
            f"All five channels earn the same gross margin ({gm_range[0]:.1%} to {gm_range[1]:.1%}) and convert visits to orders at the same rate ({conv_range[0]:.1%} to {conv_range[1]:.1%}). Channels differ in size, not in quality.",
            f"Only {kpi['repeat_rate']:.0%} of buyers ordered more than once. {one['customers']:,} one-time buyers hold {pct(one['net_revenue'], net):.0%} of revenue: the biggest growth pool.",
            f"Cancellations ({kpi['cancel_rate']:.0%} of ordered value) cost more than returns ({kpi['return_rate']:.0%} of shipped value): together ${(cancelled + returned) / 1e6:.2f}m that never became revenue.",
            f"{kpi['inactive']:,} of {registered:,} registered adult customers ({pct(kpi['inactive'], registered):.0%}) did not buy in the last 24 months, and most of them did not visit either.",
        ],
        "channel_note": f"Repeat rate by the channel of the first order is {rep_range[0]:.1%} to {rep_range[1]:.1%}: no channel brings clearly more loyal customers.",
    }

    out = {"meta": meta, "kpi": kpi, "channels": channels, "acquisition": acq, "segments": segments, "demographics": demo,
           "region_channel": X["region_channel"], "categories": cats, "monthly": monthly, "opportunities": opps,
           "insights": insights, "qa_bigquery": X["qa_bigquery"]}
    js = ("// Generated by scripts/01_build_report_data.py from data/bigquery_extract.json. Group totals only: no customer IDs or personal data.\n"
          "window.C360 = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")
    (ROOT / "dashboard" / "data.js").write_text(js, encoding="utf-8")

    manifest = {"source_extract": "bigquery_extract.json",
                "sha256": hashlib.sha256((D / "bigquery_extract.json").read_bytes()).hexdigest(),
                "window": WINDOW, "snapshot": meta["snapshot"], "built": meta["built"],
                "files": sorted(p.name for p in D.glob("*.csv"))}
    (D / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("net revenue", net, "| gm%", kpi["gm_pct"], "| buyers", buyers, "| repeat", kpi["repeat_rate"])
    for line in insights["headline"]:
        print("-", line)


if __name__ == "__main__":
    main()
