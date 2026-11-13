"""Monthly close for the Iowa spirits market: one script, no hidden steps.

Reads only the query results saved in ../data (exactly as BigQuery returned them),
checks the data and every calculation, and writes:
  ../governance/checks.md      every check, its result and status
  ../governance/run_log.md     every query that ran, its cost, and a fingerprint of every input file
  ../data/close_by_family.csv  the calculated close by product family
  ../dashboard/data.js         the only source of numbers for the report page

If any FAIL check fails, the script stops with exit code 1 and does NOT write the report data,
so a wrong number can never reach the page. Python standard library only.
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
GOV = ROOT / "governance"
PUBLISHED = ROOT.parent / "liquor-market" / "data" / "budget_vs_actual_month.csv"  # earlier published figures

CLOSE_MONTH = "2026-04-01"
PRIOR_MONTH = "2026-03-01"
TOLERANCE = 1.0  # dollars: rounding allowance for reconciliations


def read(name, path=None):
    with open(path or DATA / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(r, k):
    return float(r[k])


def m(v):
    return round(v / 1e6, 2)


# ---------------------------------------------------------------- inputs
src_months = {r["month"]: r for r in read("source_months.csv")}
src_checks = {r["month"]: r for r in read("source_checks.csv")}
outliers = read("price_outliers.csv")
actuals = {r["family"]: r for r in read("actuals_by_family.csv")}
budget = {r["family"]: r for r in read("budget_by_family.csv")}
fc_check = read("forecast_check.csv")[0]
reforecast = read("reforecast.csv")
query_log = read("query_log.csv")
published = {r["month"]: r for r in read(None, PUBLISHED)}

checks = []  # (id, area, severity, rule, result, passed)


def check(cid, area, severity, rule, passed, result):
    checks.append(dict(id=cid, area=area, severity=severity, rule=rule, result=result,
                       status="PASS" if passed else severity))


# ---------------------------------------------------------------- step 1: new data
latest = max(src_months)
check("N1", "New data", "INFO", "The month being closed is the newest month in the source",
      latest == CLOSE_MONTH,
      f"Newest month in the source: {latest[:7]}. No newer month published yet, so this is a replay of the "
      f"{CLOSE_MONTH[:7]} close. A scheduled run would stop here and log it.")

# ---------------------------------------------------------------- step 2: source data quality
cur, prev = src_checks[CLOSE_MONTH], src_checks[PRIOR_MONTH]
lines, lines_prev = int(cur["order_lines"]), int(prev["order_lines"])
month_sales = num(src_months[CLOSE_MONTH], "sales_usd")
chg = lines / lines_prev - 1
check("Q1", "Source data", "FAIL", "No order lines without sales, litres or category",
      int(cur["missing_key_fields"]) == 0, f"{int(cur['missing_key_fields'])} lines")
check("Q2", "Source data", "FAIL", "No duplicate invoice lines",
      int(cur["duplicate_invoice_lines"]) == 0, f"{int(cur['duplicate_invoice_lines'])} duplicates")
check("Q3", "Source data", "FAIL", "Every category is mapped to a product family",
      int(cur["unmapped_lines"]) == 0, f"{int(cur['unmapped_lines'])} unmapped lines")
gm = float(cur["gross_margin"])
check("Q4", "Source data", "FAIL", "Gross margin between 30% and 36% (fixed markup set by law)",
      0.30 <= gm <= 0.36, f"{gm:.1%}")
check("Q5", "Source data", "FAIL", "Order lines within ±15% of the prior month",
      abs(chg) <= 0.15,
      f"{lines:,} vs {lines_prev:,} ({chg:+.1%}); {cur['trading_days']} trading days vs {prev['trading_days']}")
cr = int(cur["credit_lines"])
check("Q6", "Source data", "WARN", "Returns (credit lines) below 1% of lines",
      cr / lines < 0.01, f"{cr} lines ({cr / lines:.2%})")
nb = int(cur["sale_not_bottles_x_price"])
check("Q7", "Source data", "WARN", "Sale equals bottles × shelf price on every line",
      nb == 0, f"{nb:,} lines ({nb / lines:.1%}) differ, vs {int(prev['sale_not_bottles_x_price']):,} last month. "
               f"Likely discounts or rounding; totals use the recorded sale amount.")
minis = sum(int(r["order_lines"]) for r in outliers if r["bottle_size"] == "up to 100ml")
real = [r for r in outliers if r["bottle_size"] != "up to 100ml"]
real_n, real_s = sum(int(r["order_lines"]) for r in real), sum(num(r, "sales_usd") for r in real)
check("Q8", "Source data", "WARN", "No line priced above $500 per litre, apart from miniatures (≤100 ml)",
      real_n == 0, f"{int(cur['price_per_litre_over_500']):,} lines above $500/litre: {minis:,} are miniatures, "
                   f"{real_n} are real outliers worth ${real_s:,.0f} ({real_s / month_sales:.2%} of sales). Kept and flagged.")

# ---------------------------------------------------------------- step 3: actual vs budget
fams = sorted(actuals)
rows = []
for f in fams:
    a, b = actuals[f], budget[f]
    s, l, c = num(a, "sales_month"), num(a, "liters_month"), num(a, "cost_month")
    sb, lb = num(b, "budget_sales_month"), num(b, "budget_liters_month")
    pb, pa = sb / lb, s / l
    rows.append(dict(
        family=f, actual=s, budget=sb, variance=s - sb, variance_pct=s / sb - 1,
        volume_effect=(l - lb) * pb,           # litres above/below budget, valued at budget price
        price_effect=(pa - pb) * l,            # price above/below budget, on actual litres
        liters=l, liters_budget=lb, liters_last_year=num(a, "liters_same_month_last_year"),
        last_year=num(a, "sales_same_month_last_year"), prior_month=num(a, "sales_prior_month"),
        ytd=num(a, "sales_ytd"), ytd_budget=num(b, "budget_sales_ytd"), ytd_last_year=num(a, "sales_ytd_last_year"),
        cost=c, budget_full_year=num(b, "budget_sales_full_year"), budget_rest=num(b, "budget_sales_rest_of_year"),
    ))
    r = rows[-1]
    r["ytd_variance"] = r["ytd"] - r["ytd_budget"]
    r["yoy_pct"] = s / r["last_year"] - 1
    r["liters_yoy_pct"] = l / r["liters_last_year"] - 1

T = lambda k: sum(r[k] for r in rows)
act, bud, lit, lit_b = T("actual"), T("budget"), T("liters"), T("liters_budget")
price_b = bud / lit_b
volume = (lit - lit_b) * price_b                 # total litres effect at average budget price
mix = T("volume_effect") - volume                # shift between cheaper and dearer families
price = T("price_effect")
ytd, ytd_b, ytd_ly = T("ytd"), T("ytd_budget"), T("ytd_last_year")

# calculation checks: every figure must add up before it is shown
pub_cur = published[CLOSE_MONTH]
pub_ytd_months = [k for k in published if k[:4] == CLOSE_MONTH[:4] and k <= CLOSE_MONTH]
check("K1", "Calculation", "FAIL", "Families add up to the source total for the month (reconciliation)",
      abs(act - month_sales) <= TOLERANCE, f"${act:,.0f} vs source ${month_sales:,.0f}")
check("K2", "Calculation", "FAIL", "Families' budget adds up to the published budget for the month",
      abs(bud - num(pub_cur, "budget_sales")) <= TOLERANCE, f"${bud:,.0f} vs published ${num(pub_cur, 'budget_sales'):,.0f}")
pub_ytd = sum(num(published[k], "actual_sales") for k in pub_ytd_months)
pub_ytd_b = sum(num(published[k], "budget_sales") for k in pub_ytd_months)
check("K3", "Calculation", "FAIL", "Year-to-date actual matches the published monthly figures",
      abs(ytd - pub_ytd) <= TOLERANCE, f"${ytd:,.0f} vs published ${pub_ytd:,.0f}")
check("K4", "Calculation", "FAIL", "Year-to-date budget matches the published monthly figures",
      abs(ytd_b - pub_ytd_b) <= TOLERANCE, f"${ytd_b:,.0f} vs published ${pub_ytd_b:,.0f}")
bad = [r["family"] for r in rows if abs(r["volume_effect"] + r["price_effect"] - r["variance"]) > TOLERANCE]
check("K5", "Calculation", "FAIL", "For every family, volume + price = actual − budget",
      not bad, "all 11 families add up" if not bad else "does not add up: " + ", ".join(bad))
check("K6", "Calculation", "FAIL", "Total bridge: volume + mix + price = actual − budget",
      abs(volume + mix + price - (act - bud)) <= TOLERANCE,
      f"{m(volume):+.2f} {m(mix):+.2f} {m(price):+.2f} = {m(volume + mix + price):+.2f}m; actual − budget = {m(act - bud):+.2f}m")
bad = [r["family"] for r in rows if abs(r["ytd_budget"] + r["budget_rest"] - r["budget_full_year"]) > TOLERANCE]
check("K7", "Calculation", "FAIL", "Full-year budget = year-to-date budget + rest-of-year budget, for every family",
      not bad, "all 11 families add up" if not bad else "does not add up: " + ", ".join(bad))

# ---------------------------------------------------------------- steps 4-5: forecast check and re-forecast
fc, fc_lo, fc_hi = num(fc_check, "forecast"), num(fc_check, "low_80"), num(fc_check, "high_80")
fc_err = act / fc - 1
rest_fc = sum(num(r, "forecast") for r in reforecast)
rest_lo = sum(num(r, "low_80") for r in reforecast)
rest_hi = sum(num(r, "high_80") for r in reforecast)
fy_budget, rest_budget = T("budget_full_year"), T("budget_rest")
landing_model = ytd + rest_fc
landing_trend = ytd + rest_budget * (ytd / ytd_b)   # the year-to-date shortfall continues
bad = [r["month"][:7] for r in reforecast if not num(r, "low_80") <= num(r, "forecast") <= num(r, "high_80")]
check("K8", "Calculation", "FAIL", "Every re-forecast month sits inside its own range",
      not bad, f"{len(reforecast)} months, all inside" if not bad else "outside: " + ", ".join(bad))
expected_months = 12 - int(CLOSE_MONTH[5:7])
check("K9", "Calculation", "FAIL", "Re-forecast covers exactly the rest of the year",
      len(reforecast) == expected_months and reforecast[0]["month"] > CLOSE_MONTH,
      f"{len(reforecast)} months from {reforecast[0]['month'][:7]} (expected {expected_months})")
check("F1", "Forecast", "WARN", "Last month's forecast for this month was inside its range",
      fc_lo <= act <= fc_hi, f"forecast ${m(fc)}m (range {m(fc_lo)}–{m(fc_hi)}), actual ${m(act)}m, error {fc_err:+.1%}")

# ---------------------------------------------------------------- step 6: commentary, by written rules
# Each sentence below is produced by a rule documented in README.md, from the numbers above.
pub_q = [k for k in pub_ytd_months if k < CLOSE_MONTH]
prior_ytd_pct = (sum(num(published[k], "actual_sales") for k in pub_q) /
                 sum(num(published[k], "budget_sales") for k in pub_q) - 1)
ytd_pct = ytd / ytd_b - 1
offset = price + mix
by_var = sorted(rows, key=lambda r: r["variance"])
timing = [r for r in rows if r["variance_pct"] <= -0.10 and r["ytd_variance"] >= 0]
growing = [r for r in rows if r["yoy_pct"] > 0 and r["liters_yoy_pct"] > 0]
price_only = [r for r in rows if r["variance"] > 0 and r["volume_effect"] < 0]

summary = []
if volume < 0 and abs(volume) > abs(offset):
    summary.append(["Volume explains the miss.",
                    f"Sales came in ${abs(m(act - bud))}m {'below' if act < bud else 'above'} budget ({act / bud - 1:+.1%}). Fewer litres cost "
                    f"${abs(m(volume))}m; price ({m(price):+.2f}m) and mix ({m(mix):+.2f}m) won back "
                    f"{offset / abs(volume):.0%} of that."])
else:
    summary.append(["Month vs budget.", f"{act / bud - 1:+.1%}: volume {m(volume):+.2f}m, mix {m(mix):+.2f}m, price {m(price):+.2f}m."])
trend_word = "stable" if abs(ytd_pct - prior_ytd_pct) <= 0.005 else ("widening" if ytd_pct < prior_ytd_pct else "narrowing")
summary.append([f"The year-to-date gap is {trend_word}.",
                f"Year to date is {ytd_pct:+.1%} against budget, vs {prior_ytd_pct:+.1%} one month earlier."])
for r in timing:
    summary.append([f"{r['family']}: likely timing, not a trend.",
                    f"{r['variance_pct']:+.0%} against budget this month, but ${abs(m(r['ytd_variance']))}m "
                    f"{'above' if r['ytd_variance'] >= 0 else 'below'} budget year to date."])
for r in growing:
    summary.append([f"{r['family']} is growing.",
                    f"{m(r['variance']):+.2f}m against budget and {r['yoy_pct']:+.1%} vs last year, with more litres sold "
                    f"({r['liters_yoy_pct']:+.1%})."])
for r in price_only:
    summary.append([f"{r['family']} beat budget on price only.",
                    f"Litres are {'down' if r['liters_yoy_pct'] < 0 else 'up'} {abs(r['liters_yoy_pct']):.0%} vs last year; higher prices hide the lost volume."])
summary.append(["The forecast model " + ("was accurate." if fc_lo <= act <= fc_hi else "missed."),
                f"With data to {PRIOR_MONTH[:7]} it expected ${m(fc)}m; the actual was {abs(fc_err):.1%} {'lower' if fc_err < 0 else 'higher'}"
                + (", inside its range." if fc_lo <= act <= fc_hi else ", outside its range.")])

actions = [[f"Plan on ${landing_trend / 1e6:.0f}m, not ${fy_budget / 1e6:.0f}m",
            f"Reset the rest-of-year targets to the trend view so plans for cash and stock stay realistic."]]
actions += [[f"Back {r['family']}", "The only family growing in both sales and litres."] for r in growing]
actions += [[f"Review {r['family']} pricing", "Volume is falling while prices rise. Test whether price is driving the loss."] for r in price_only]
actions += [[f"No action on {r['family']} yet", "Likely timing. Recheck at the next close."] for r in timing]

# ---------------------------------------------------------------- outputs
fails = [c for c in checks if c["status"] == "FAIL"]
warns = [c for c in checks if c["status"] == "WARN"]
GOV.mkdir(exist_ok=True)
icon = {"PASS": "✅ PASS", "WARN": "⚠️ WARN", "FAIL": "❌ FAIL", "INFO": "ℹ️ INFO"}
with open(GOV / "checks.md", "w", encoding="utf-8") as f:
    f.write(f"# Checks for the {CLOSE_MONTH[:7]} close\n\nGenerated by `scripts/close.py`. "
            f"FAIL checks stop the run; WARN checks are shown on the report.\n\n"
            f"**Result: {len(checks) - len(fails) - len(warns)} pass or info, {len(warns)} warnings, {len(fails)} failures.**\n\n"
            "| ID | Area | Rule | Result | Status |\n|---|---|---|---|---|\n")
    for c in checks:
        f.write(f"| {c['id']} | {c['area']} | {c['rule']} | {c['result']} | {icon[c['status']]} |\n")

fingerprints = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DATA.glob("*.csv"))
                if p.name != "close_by_family.csv"}
gb = sum(int(q["bytes_billed"]) for q in query_log) / 1e9
with open(GOV / "run_log.md", "w", encoding="utf-8") as f:
    f.write(f"# Run log: {CLOSE_MONTH[:7]} close\n\nEvery BigQuery query that ran for this close, in order. "
            f"SQL is in `sql/`, results are saved unchanged in `data/`.\n\n"
            "| Step | Purpose | SQL | Result file | GB billed | Rows | Date |\n|---|---|---|---|---|---|---|\n")
    for q in query_log:
        f.write(f"| {q['step']} | {q['purpose']} | {q['sql_file'] or '–'} | {q['output_file'] or '–'} | "
                f"{int(q['bytes_billed']) / 1e9:.2f} | {q['rows_returned']} | {q['run_on']} |\n")
    f.write(f"\n**Total: {gb:.2f} GB billed**, inside BigQuery's free 1 TB a month. All queries were read-only: "
            "nothing in BigQuery was created or changed.\n\n## Input fingerprints (SHA-256)\n\n"
            "If any input file is edited after the run, its fingerprint will no longer match.\n\n| File | SHA-256 |\n|---|---|\n")
    for k, v in fingerprints.items():
        f.write(f"| {k} | `{v}` |\n")
    f.write(f"\n## Outcome\n\n- Checks: {len(checks) - len(fails) - len(warns)} pass or info, {len(warns)} warnings, "
            f"{len(fails)} failures (see `checks.md`).\n- Report data: "
            + ("**not written** because a FAIL check failed.\n" if fails else "written to `dashboard/data.js`.\n")
            + "- Publishing: by pull request only; a person reviews and merges.\n")

if fails:
    print(f"STOPPED: {len(fails)} FAIL check(s): " + ", ".join(c["id"] for c in fails))
    sys.exit(1)

with open(DATA / "close_by_family.csv", "w", newline="", encoding="utf-8") as f:
    cols = ["family", "actual", "budget", "variance", "variance_pct", "volume_effect", "price_effect",
            "last_year", "yoy_pct", "liters", "liters_budget", "liters_yoy_pct", "ytd", "ytd_budget", "ytd_variance"]
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in by_var:
        w.writerow({k: (round(r[k], 4) if isinstance(r[k], float) else r[k]) for k in cols})

report = dict(
    month=CLOSE_MONTH[:7], generated=max(q["run_on"] for q in query_log), gb_billed=round(gb, 2),
    tiles=dict(actual=act, budget=bud, last_year=T("last_year"), ytd=ytd, ytd_budget=ytd_b, prior_ytd_pct=prior_ytd_pct,
               fy_budget=fy_budget, landing_trend=landing_trend, landing_model=landing_model,
               landing_lo=ytd + rest_lo, landing_hi=ytd + rest_hi),
    bridge=[["Budget", bud], ["Volume", volume], ["Mix", mix], ["Price", price], ["Actual", act]],
    families=[{k: r[k] for k in ("family", "variance", "variance_pct", "volume_effect", "price_effect", "yoy_pct", "ytd_variance")}
              for r in by_var],
    summary=summary, actions=actions, checks=checks,
    queries=[dict(q, gb=round(int(q["bytes_billed"]) / 1e9, 2)) for q in query_log],
)
with open(ROOT / "dashboard" / "data.js", "w", encoding="utf-8") as f:
    f.write("// Generated by scripts/close.py. Do not edit by hand.\nconst CLOSE = " + json.dumps(report, indent=1) + ";\n")
print(f"OK: {len(checks)} checks, {len(warns)} warnings, 0 failures. Report data written.")
