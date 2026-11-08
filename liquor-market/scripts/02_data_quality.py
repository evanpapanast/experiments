"""Data quality, governance and privacy gate for the Iowa spirits report.

Runs on the committed files only, so it also runs in GitHub Actions on every change.
The checks inside BigQuery (sql/06_data_quality_checks.sql) cover the warehouse and the source reconciliation;
this gate covers what is published: the extract, the report data and the documents.
FAIL checks stop the pipeline (exit code 1); WARN checks are reported only. Writes data_quality/dq_report.md.

Usage: python 02_data_quality.py
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"
FAMILIES = {"Vodka", "American whiskey", "Canadian whisky", "Scotch & Irish whisky", "Tequila & mezcal", "Rum",
            "Liqueurs & schnapps", "Brandy", "Gin", "Ready-to-drink cocktails", "Gift packs & other"}
APPROVED = {  # every column allowed in a published data file
    "year_family.csv": {"year", "family", "sales_usd", "cost_usd", "liters"},
    "month_total.csv": {"month", "sales_usd", "cost_usd", "liters"},
    "seasonality.csv": {"month_of_year", "avg_share", "min_share", "max_share"},
    "budget_vs_actual_month.csv": {"month", "budget_sales", "budget_liters", "actual_sales", "actual_liters"},
    "budget_vs_actual_family.csv": {"family", "budget_sales", "budget_liters", "actual_sales", "actual_liters"},
    "budget_2026_family.csv": {"family", "budget_sales", "budget_liters"},
    "pvm_family.csv": {"comparison", "family", "sales_before", "sales_after", "liters_before", "liters_after"},
    "outlook_family.csv": {"family", "year", "sales_usd", "liters"},
    "outlook_month_sum.csv": {"measure", "month", "forecast", "lower_80_sum", "upper_80_sum"},
    "forecast_total.csv": {"version", "month", "forecast", "lower_80", "upper_80"},
}
FORBIDDEN = re.compile(r"(store|vendor|supplier|item|address|zip|city|county|invoice|name)", re.I)
LICENCE_URL = "https://creativecommons.org/licenses/by/4.0/"


def main():
    res = []

    def check(cid, cat, sev, rule, bad, detail=""):
        res.append({"id": cid, "category": cat, "severity": sev, "rule": rule, "failures": int(bad),
                    "status": "PASS" if bad == 0 else sev, "detail": detail})

    man = json.loads((D / "manifest.json").read_text())
    files = {f.name: pd.read_csv(f) for f in sorted(D.glob("*.csv"))}
    js = (ROOT / "dashboard" / "data.js").read_text(encoding="utf-8")
    data = json.loads(js[js.index("=") + 1:].strip().rstrip(";"))
    html = (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    yf, mt = files["year_family.csv"], files["month_total.csv"]
    last_year = int(mt.month.str[:4].max()); fy = last_year - 1

    # ---- privacy and licence ----
    bad_cols = [f"{n}: {c}" for n, df in files.items() for c in df.columns
                if n not in APPROVED or c not in APPROVED[n] or (FORBIDDEN.search(c) and c != "family")]
    check("P01", "Privacy", "FAIL", "Published data files contain only approved columns (no store, supplier, product or place)",
          len(bad_cols), "; ".join(bad_cols[:5]))
    fam_cols = [df.family for df in files.values() if "family" in df.columns]
    unknown = sorted(set(pd.concat(fam_cols)) - FAMILIES)
    check("P02", "Privacy", "FAIL", "Only the 11 approved product families appear (no brand or company names)", len(unknown), ", ".join(unknown))
    long_txt = [f"{n}.{c}" for n, df in files.items() for c in df.columns if df[c].dtype == object and df[c].astype(str).str.len().max() > 40]
    check("P03", "Privacy", "FAIL", "No free-text cell longer than 40 characters in the data files", len(long_txt), ", ".join(long_txt))
    lic = int(man["source"]["licence_url"] != LICENCE_URL) + int("CC BY 4.0" not in html) + int(LICENCE_URL not in html) \
        + int("CC BY 4.0" not in readme) + int("Iowa Department of Revenue" not in html)
    check("L01", "Licence", "FAIL", "Licence is CC BY 4.0 and the report and README credit the source and link the licence", lic)

    # ---- lineage and reconciliation ----
    sha = hashlib.sha256((D / "bigquery_extract.txt").read_bytes()).hexdigest()
    check("R01", "Lineage", "FAIL", "The extract file is the one recorded in the manifest (SHA-256)", int(sha != man["extract_sha256"]))
    ct = man["control_totals_source"]
    diffs = [abs(yf.sales_usd.sum() - ct["sales_usd"]), abs(mt.sales_usd.sum() - ct["sales_usd"]),
             abs(yf.liters.sum() - ct["liters"]), abs(mt.liters.sum() - ct["liters"])]
    check("R02", "Reconciliation", "FAIL", "Yearly and monthly totals match the source control totals (within $5 / 5 litres of rounding)",
          sum(d > 5 for d in diffs), f"largest difference {max(diffs):.0f}")
    pf = files["pvm_family.csv"]
    fyc = f"FY{fy} vs FY{fy - 1}"; ytc = f"YTD{last_year} vs YTD{fy}"
    a = pf[pf.comparison == fyc]
    k1 = [abs(a.sales_after.sum() - yf[yf.year == fy].sales_usd.sum()), abs(a.sales_before.sum() - yf[yf.year == fy - 1].sales_usd.sum()),
          abs(pf[pf.comparison == ytc].sales_after.sum() - yf[yf.year == last_year].sales_usd.sum())]
    check("R03", "Reconciliation", "FAIL", "Price/volume inputs agree with the yearly totals", sum(d > 5 for d in k1))
    bf, bm = files["budget_vs_actual_family.csv"], files["budget_vs_actual_month.csv"]
    k2 = [abs(bf.actual_sales.sum() - bm.actual_sales.sum()), abs(bf.budget_sales.sum() - bm.budget_sales.sum()),
          abs(bf.actual_sales.sum() - yf[yf.year == last_year].sales_usd.sum())]
    check("R04", "Reconciliation", "FAIL", "Budget vs actual agrees by month, by family and with the yearly totals", sum(d > 5 for d in k2))
    of = files["outlook_family.csv"]
    k3 = abs(of[of.year == fy].sales_usd.sum() - yf[yf.year == fy].sales_usd.sum())
    check("R05", "Reconciliation", "FAIL", f"The outlook starts from the real {fy} sales", int(k3 > 5))

    # ---- completeness ----
    months = pd.period_range(mt.month.min()[:7], mt.month.max()[:7], freq="M").astype(str)
    check("C01", "Completeness", "FAIL", "Every month from January 2017 to the latest month is present",
          len(set(months) - set(mt.month.str[:7])))
    per_year = yf.groupby("year").family.nunique()
    check("C02", "Completeness", "FAIL", "All 11 families are present in every year", int((per_year != 11).sum()))
    se = files["seasonality.csv"]
    check("C03", "Completeness", "FAIL", "Seasonality covers 12 months and its shares add up to 100%",
          int(len(se) != 12) + int(abs(se.avg_share.sum() - 1) > 0.001))
    fo = files["outlook_month_sum.csv"]
    check("C04", "Completeness", "FAIL", "The forecast covers every month from the next month to December of next year",
          len(set(pd.period_range(pd.Period(mt.month.max()[:7], "M") + 1, f"{last_year + 1}-12", freq="M").astype(str))
              - set(fo[fo.measure == "sales_usd"].month.str[:7])))

    # ---- validity ----
    yt = yf.groupby("year")[["sales_usd", "cost_usd", "liters"]].sum()
    margin = 1 - yt.cost_usd / yt.sales_usd
    check("V01", "Validity", "FAIL", "Yearly gross margin is between 30% and 36% (fixed 50% markup by law)",
          int((~margin.between(0.30, 0.36)).sum()), f"range {margin.min():.1%} to {margin.max():.1%}")
    neg = sum(int((df.select_dtypes("number") < 0).sum().sum()) for n, df in files.items() if n != "pvm_family.csv")
    check("V02", "Validity", "FAIL", "No negative sales, litres or forecasts", neg)
    band = int(((fo.lower_80_sum > fo.forecast) | (fo.upper_80_sum < fo.forecast)).sum())
    check("V03", "Validity", "FAIL", "Every forecast lies inside its likely range", band)

    # ---- report consistency ----
    k = data["kpi"]
    kbad = int(abs(k["sales_fy"] - yt.loc[fy, "sales_usd"]) > 1) + int(abs(k["ytd_sales"] - yt.loc[last_year, "sales_usd"]) > 1) \
        + int(abs(k["bva_pct"] - (bf.actual_sales.sum() / bf.budget_sales.sum() - 1) * 100) > 0.01)
    check("K01", "Consistency", "FAIL", "Headline numbers in the report equal the data files", kbad)
    bsum = sum(int(abs(b["volume"] + b["mix"] + b["price"] - (b["after"] - b["before"])) > 1) for b in (data["bridge_fy"], data["bridge_ytd"]))
    check("K02", "Consistency", "FAIL", "Price + volume + mix add up to the sales change in the report", bsum)
    vb = sum(int(abs(r["var_volume"] + r["var_price"] - r["var_total"]) > 1) for r in data["bva_family"])
    check("K03", "Consistency", "FAIL", "Budget gap = volume part + price part, for every family", vb)
    check("K04", "Consistency", "FAIL", "The report data was built from the current extract (same last month)",
          int(data["meta"]["last_month"] != mt.month.max()[:7]))

    # ---- accuracy and freshness (warnings) ----
    acc = abs(data["kpi"]["bva_pct"])
    check("A01", "Accuracy", "WARN", "Forecast-based budget within 5% of actual sales so far this year", int(acc > 5), f"{acc:.1f}% off")
    lag = (pd.Timestamp.today().to_period("M") - pd.Period(mt.month.max()[:7], "M")).n
    check("F01", "Freshness", "WARN", "Latest month is no more than 8 months old (the source publishes with a delay)", int(lag > 8),
          f"latest month {mt.month.max()[:7]}, {lag} months ago")

    r = pd.DataFrame(res); n = r.status.value_counts()
    icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}
    lines = ["# Data quality report: Iowa spirits market", "",
             f"Checks on the published files. **{n.get('PASS', 0)} PASS, {n.get('WARN', 0)} WARN, {n.get('FAIL', 0)} FAIL.** "
             "The warehouse checks in BigQuery are in [bigquery_dq_results.md](bigquery_dq_results.md).", "",
             "| ID | Area | Rule | Result | Problems | Detail |", "|---|---|---|---|---|---|"]
    lines += [f"| {x['id']} | {x['category']} | {x['rule']} | {icon[x['status']]} {x['status']} | {x['failures']} | {x['detail']} |" for x in res]
    (ROOT / "data_quality" / "dq_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(r[["id", "category", "status", "failures", "detail"]].to_string(index=False))
    print(f"\n{n.get('PASS', 0)} PASS, {n.get('WARN', 0)} WARN, {n.get('FAIL', 0)} FAIL  ->  data_quality/dq_report.md")
    sys.exit(1 if n.get("FAIL", 0) else 0)


if __name__ == "__main__":
    main()
