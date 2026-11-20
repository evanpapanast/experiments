"""Data quality, governance and privacy gate for the Customer 360 report.

Runs on the committed files only, so it also runs in GitHub Actions on every change.
The checks inside BigQuery (sql/04_quality_checks.sql) cover the warehouse and the source reconciliation;
this gate covers what is published: the extract, the data files, the report data and the dashboard.
FAIL checks stop the pipeline (exit code 1); WARN checks are reported only. Writes data_quality/dq_report.md.
Only the Python standard library is used.

Usage: python 02_data_quality.py
"""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"
MIN_GROUP = 50
CHANNELS = {"Email", "Google Ads", "Facebook", "YouTube", "Organic"}
APPROVED = {  # every column allowed in a published data file
    "channels.csv": {"channel", "orders", "customers", "net_revenue", "revenue_share", "product_cost", "gross_margin", "gm_pct",
                     "returned_value", "return_rate", "cancelled_value", "cancel_rate", "aov", "sessions", "visit_to_purchase",
                     "visit_to_cart", "cart_to_purchase", "repeat_rate_first_channel", "preferred_by_buyers", "preferred_share"},
    "acquisition_channels.csv": {"channel", "registered", "buyers", "repeat_buyers", "net_revenue", "gross_margin", "returned_value",
                                 "gross_sales", "revenue_share", "buyer_rate", "repeat_rate", "revenue_per_buyer", "gm_pct"},
    "segments.csv": {"segment", "definition", "action", "customers", "customer_share", "net_revenue", "revenue_share", "gross_margin",
                     "orders", "aov", "revenue_per_customer", "return_rate", "net_revenue_12m", "visiting_customers"},
    "segment_channel.csv": {"segment", "preferred_channel", "customers", "net_revenue"},
    "demographics.csv": {"dim", "val", "customers", "buyers", "net_revenue", "gross_margin", "returned_value", "gross_sales",
                         "buyer_rate", "revenue_per_buyer", "gm_pct", "return_rate"},
    "region_channel.csv": {"region", "preferred_channel", "customers"},
    "categories.csv": {"category", "net_revenue", "gross_margin", "returned_value", "gross_sales", "gm_pct", "return_rate"},
    "monthly_by_channel.csv": {"month", "Email", "Google Ads", "Facebook", "YouTube", "Organic", "gross_margin"},
}
# column names that would mean personal data or row-level customer data
FORBIDDEN = re.compile(r"(name|email_addr|address|postal|zip|city|state|ip_|browser|latitude|longitude|geom|customer_id|user_id|"
                       r"session_id|order_id|^age$|birth|phone|country)", re.I)
GROUP_COUNT_COLS = {"segments.csv": "customers", "segment_channel.csv": "customers", "demographics.csv": "customers",
                    "region_channel.csv": "customers", "acquisition_channels.csv": "registered", "channels.csv": "customers"}


def read(name):
    with open(D / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def f(x):
    return float(x) if x not in ("", None) else None


def main():
    res = []

    def check(area, name, ok, detail, severity="FAIL"):
        res.append((area, name, "PASS" if ok else severity, detail))

    manifest = json.loads((D / "manifest.json").read_text(encoding="utf-8"))
    sha = hashlib.sha256((D / "bigquery_extract.json").read_bytes()).hexdigest()
    check("Traceability", "Extract fingerprint matches manifest (SHA-256)", sha == manifest["sha256"], sha[:16] + "…")
    files = sorted(p.name for p in D.glob("*.csv"))
    check("Traceability", "Every data file is listed in the manifest", files == manifest["files"], f"{len(files)} files")

    # ---- privacy ----
    unknown, forbidden = [], []
    for name in files:
        cols = set(read(name)[0].keys())
        if name not in APPROVED or cols - APPROVED[name]:
            unknown.append(f"{name}: {sorted(cols - APPROVED.get(name, set()))}")
        forbidden += [f"{name}.{c}" for c in cols if FORBIDDEN.search(c)]
    check("Privacy", "Only approved columns are published", not unknown, "; ".join(unknown) or "all columns approved")
    check("Privacy", "No personal-data or row-level ID columns", not forbidden, ", ".join(forbidden) or "none")
    small = []
    for name, col in GROUP_COUNT_COLS.items():
        for r in read(name):
            v = f(r[col])
            if v is not None and v < MIN_GROUP:
                small.append(f"{name}:{r}")
    check("Privacy", f"Every published group has at least {MIN_GROUP} customers", not small, f"{len(small)} small groups")
    sup = [r for r in read("segment_channel.csv") if r["customers"] == ""]
    check("Privacy", "Small cells are suppressed, not dropped", len(sup) == 2, f"{len(sup)} suppressed cells (expected 2)")
    extract_text = (D / "bigquery_extract.json").read_text(encoding="utf-8")
    check("Privacy", "Extract holds no e-mail addresses or IP addresses",
          not re.search(r"[\w.]+@[\w-]+\.\w+|\b\d{1,3}(\.\d{1,3}){3}\b", extract_text), "pattern scan")

    # ---- accuracy and consistency ----
    seg = read("segments.csv")
    ch = read("channels.csv")
    net_seg = sum(f(r["net_revenue"]) for r in seg)
    net_ch = sum(f(r["net_revenue"]) for r in ch)
    net_cat = sum(f(r["net_revenue"]) for r in read("categories.csv"))
    net_acq = sum(f(r["net_revenue"]) for r in read("acquisition_channels.csv"))
    monthly = read("monthly_by_channel.csv")
    net_month = sum(f(r[c]) for r in monthly for c in CHANNELS)
    for label, v in [("channels", net_ch), ("categories", net_cat), ("first channels", net_acq), ("months", net_month)]:
        check("Accuracy", f"Net revenue: groups = {label}", abs(v - net_seg) <= 50, f"{v:,.0f} vs {net_seg:,.0f}")
    gm_ch = sum(f(r["gross_margin"]) for r in ch)
    gm_seg = sum(f(r["gross_margin"]) for r in seg)
    check("Accuracy", "Gross margin: groups = channels", abs(gm_ch - gm_seg) <= 50, f"{gm_ch:,.0f} vs {gm_seg:,.0f}")
    reg = sum(f(r["customers"]) for r in seg)
    for dim in ("region", "age_band", "gender"):
        v = sum(f(r["customers"]) for r in read("demographics.csv") if r["dim"] == dim)
        check("Completeness", f"Customers by {dim} add up to all customers", v == reg, f"{v:,.0f} vs {reg:,.0f}")
    buyers = sum(f(r["customers"]) for r in seg if f(r["net_revenue"]) > 0)
    rc = sum(f(r["customers"]) for r in read("region_channel.csv"))
    check("Completeness", "Buyers by region and preferred channel add up to all buyers", rc == buyers, f"{rc:,.0f} vs {buyers:,.0f}")
    check("Completeness", "All five channels present", {r["channel"] for r in ch} == CHANNELS, ", ".join(sorted(r["channel"] for r in ch)))
    shares = [f(r[c]) for r in ch for c in ("revenue_share", "gm_pct", "return_rate", "cancel_rate", "visit_to_purchase")]
    check("Validity", "Rates and shares are between 0 and 1", all(0 <= s <= 1 for s in shares), f"{len(shares)} values")
    check("Validity", "Revenue shares add up to 100%", abs(sum(f(r["revenue_share"]) for r in ch) - 1) < 0.002,
          f"{sum(f(r['revenue_share']) for r in ch):.4f}")
    neg = [n for n in files for r in read(n) for k, v in r.items() if re.fullmatch(r"-\d.*", v or "")]
    check("Validity", "No negative values", not neg, f"{len(neg)} negative values")
    months = [r["month"] for r in monthly]
    check("Validity", "Months cover the 24-month window", months[0] == "2024-11" and months[-1] == "2026-11" and len(months) == 25,
          f"{months[0]} to {months[-1]} ({len(months)} months, first and last partial)")

    # ---- BigQuery checks and report ----
    qa = json.loads(extract_text)["qa_bigquery"]
    check("Governance", "All BigQuery checks passed", all(q["passed"] for q in qa), f"{sum(q['passed'] for q in qa)} of {len(qa)}")
    js = (ROOT / "dashboard" / "data.js").read_text(encoding="utf-8")
    check("Governance", "Report data was generated from the extract", js.startswith("// Generated by scripts/01_build_report_data.py"), "header present")
    html = (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
    check("Governance", "Report states that the data is synthetic", "Synthetic data." in html, "banner present")
    check("Governance", "Report loads no external scripts or trackers", not re.search(r"<script[^>]+src=\"https?:", html), "local scripts only")
    check("Governance", "Marketing spend is not invented", not re.search(r"\b(ROAS|CAC|cost per click|ad spend)\b", js, re.I),
          "no spend-based metrics in report data")

    fails = [r for r in res if r[2] == "FAIL"]
    lines = ["# Data quality report: Customer 360", "",
             f"Run on the published files. {len(res) - len(fails)} of {len(res)} checks passed.", "",
             "| Area | Check | Result | Detail |", "|---|---|---|---|"]
    lines += [f"| {a} | {n} | {s} | {d} |" for a, n, s, d in res]
    lines += ["", "## Checks inside BigQuery (sql/04_quality_checks.sql)", "", "| Area | Check | Result | Status |", "|---|---|---|---|"]
    lines += [f"| {q['area']} | {q['check']} | {q['result']} | {'PASS' if q['passed'] else 'FAIL'} |" for q in qa]
    (ROOT / "data_quality" / "dq_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for a, n, s, d in res:
        print(f"{s:4}  {a:13} {n}  ({d})")
    print(f"\n{len(res) - len(fails)} of {len(res)} passed")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
