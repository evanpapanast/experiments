"""Build the report data for "Iowa spirits market: price, volume, forecast and budget".

Input : data/bigquery_extract.txt (results of sql/05_extract.sql, copied from BigQuery)
Output: data/*.csv (one tidy file per block) and dashboard/data.js (window.LIQ)

Every number and sentence in the report is computed here; nothing is typed by hand.
"""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"
MARGIN_NOTE = "Iowa adds a fixed 50% markup to what it pays suppliers, so gross margin is about one third of sales."


def read_extract():
    blocks, cur = {}, None
    for line in (D / "bigquery_extract.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("["):
            cur = line[1:line.index("]")]
            blocks[cur] = {"cols": line.split("] ", 1)[1].split("|"), "rows": []}
        elif cur and line.strip() and not line.startswith("#"):
            blocks[cur]["rows"] += [r.split("|") for r in line.split(";")]
    out = {}
    for k, b in blocks.items():
        df = pd.DataFrame(b["rows"], columns=b["cols"])
        for c in df.columns:
            if df[c].str.fullmatch(r"-?[\d.]+").all() and c not in ("month",):
                df[c] = pd.to_numeric(df[c])
        out[k] = df
        df.to_csv(D / f"{k}.csv", index=False)
    return out


def status_of(sales_pct, vol_pct, price_pct):
    if sales_pct >= -1:
        return "steady"
    if vol_pct <= -3 and price_pct >= 2:
        return "price"
    return "losing"


STATUS = {
    "steady": {"label": "Holding steady", "action": "Protect and grow: keep stock and shelf space. These are the safest bets."},
    "price": {"label": "Price hides falling volume", "action": "Check pricing: buyers take fewer litres. Test whether price rises push them away before raising prices again."},
    "losing": {"label": "Losing ground", "action": "Find the cause. Defend the big sellers with promotions; in small families, trim slow products to free up stock and cash."},
}


def main():
    x = read_extract()
    yf, mt, se = x["year_family"], x["month_total"], x["seasonality"]
    pf, bvm, bvf = x["pvm_family"], x["budget_vs_actual_month"], x["budget_vs_actual_family"]
    b26, of, oms, ft = x["budget_2026_family"], x["outlook_family"], x["outlook_month_sum"], x["forecast_total"]

    mt["month"] = mt.month.str[:7]
    last_month = mt.month.max()
    last_year, n_ytd = int(last_month[:4]), int(last_month[5:7])
    fy = last_year - 1                           # last full year
    yt = yf.groupby("year")[["sales_usd", "cost_usd", "liters"]].sum()

    # ---------- price / volume / mix bridges ----------
    def bridge(comp):
        d = pf[pf.comparison == comp].copy()
        s0, s1, l0, l1 = d.sales_before.sum(), d.sales_after.sum(), d.liters_before.sum(), d.liters_after.sum()
        p0 = s0 / l0
        s1_at_p0 = (d.liters_after * d.sales_before / d.liters_before).sum()
        vol, mix, price = (l1 - l0) * p0, s1_at_p0 - l1 * p0, s1 - s1_at_p0
        assert abs(vol + mix + price - (s1 - s0)) < 1
        d["sales_pct"] = (d.sales_after / d.sales_before - 1) * 100
        d["vol_pct"] = (d.liters_after / d.liters_before - 1) * 100
        d["price_pct"] = ((d.sales_after / d.liters_after) / (d.sales_before / d.liters_before) - 1) * 100
        return {"before": s0, "after": s1, "volume": vol, "mix": mix, "price": price,
                "like_price_pct": price / s1_at_p0 * 100,
                "sales_pct": (s1 / s0 - 1) * 100, "vol_pct": (l1 / l0 - 1) * 100,
                "price_pct": ((s1 / l1) / (s0 / l0) - 1) * 100}, d

    br_fy, fam_fy = bridge(f"FY{fy} vs FY{fy - 1}")
    br_ytd, fam_ytd = bridge(f"YTD{last_year} vs YTD{fy}")

    # ---------- families: status and action from the latest months ----------
    fam = fam_ytd[["family", "sales_after", "sales_pct", "vol_pct", "price_pct"]].rename(
        columns={"sales_after": "ytd_sales", "sales_pct": "ytd_sales_pct", "vol_pct": "ytd_vol_pct", "price_pct": "ytd_price_pct"})
    fam = fam.merge(fam_fy[["family", "sales_after", "sales_pct", "vol_pct", "price_pct"]].rename(
        columns={"sales_after": "fy_sales", "sales_pct": "fy_sales_pct", "vol_pct": "fy_vol_pct", "price_pct": "fy_price_pct"}), on="family")
    fam["status"] = [status_of(a, b, c) for a, b, c in zip(fam.ytd_sales_pct, fam.ytd_vol_pct, fam.ytd_price_pct)]
    fam = fam.sort_values("fy_sales", ascending=False).reset_index(drop=True)
    fam["share_fy"] = fam.fy_sales / fam.fy_sales.sum()

    # ---------- budget vs actual (forecast made with data to December of the last full year) ----------
    bvf["budget_price"] = bvf.budget_sales / bvf.budget_liters
    bvf["actual_price"] = bvf.actual_sales / bvf.actual_liters
    bvf["var_total"] = bvf.actual_sales - bvf.budget_sales
    bvf["var_volume"] = (bvf.actual_liters - bvf.budget_liters) * bvf.budget_price
    bvf["var_price"] = (bvf.actual_price - bvf.budget_price) * bvf.actual_liters
    assert (abs(bvf.var_volume + bvf.var_price - bvf.var_total) < 1).all()
    bva_tot = {k: float(bvf[k].sum()) for k in ("budget_sales", "actual_sales", "budget_liters", "actual_liters", "var_volume", "var_price", "var_total")}
    budget_fy_total = float(b26.budget_sales.sum())

    # ---------- outlook: family forecasts summed; band from the total-market model's 80% range ----------
    oms["month"] = oms.month.str[:7]
    ft["month"] = ft.month.str[:7]
    out_s = oms[oms.measure == "sales_usd"].set_index("month")
    band = ft[ft.version == "outlook"].set_index("month")
    out_s["lo"] = out_s.forecast * band.lower_80 / band.forecast
    out_s["hi"] = out_s.forecast * band.upper_80 / band.forecast
    bud_m = ft[ft.version == f"budget_{last_year}"].set_index("month")
    ytd_actual = float(mt[mt.month.str[:4] == str(last_year)].sales_usd.sum())
    rest_fy_prev = float(mt[(mt.month.str[:4] == str(fy)) & (mt.month.str[5:7].astype(int) > n_ytd)].sales_usd.sum())
    model_cur = ytd_actual + float(out_s[out_s.index.str[:4] == str(last_year)].forecast.sum())
    model_next = float(out_s[out_s.index.str[:4] == str(last_year + 1)].forecast.sum())
    trend_v, trend_p = br_ytd["vol_pct"] / 100, br_ytd["price_pct"] / 100
    trend_cur = ytd_actual + rest_fy_prev * (1 + trend_v) * (1 + trend_p)
    trend_next = trend_cur * (1 + trend_v) * (1 + trend_p)

    # family 2027 budget: model vs current trend
    ofp = of.pivot(index="family", columns="year", values="sales_usd")
    yfp = yf.pivot(index="family", columns="year", values="sales_usd")
    ytd_prev_fam = fam_ytd.set_index("family").sales_before
    fam["fy_prev_rest"] = fam.family.map(lambda f: yfp.loc[f, fy] - ytd_prev_fam[f])
    fam["trend_cur"] = fam.family.map(lambda f: yfp.loc[f, last_year]) + fam.fy_prev_rest * (1 + fam.ytd_vol_pct / 100) * (1 + fam.ytd_price_pct / 100)
    fam["trend_next"] = fam.trend_cur * (1 + fam.ytd_vol_pct / 100) * (1 + fam.ytd_price_pct / 100)
    fam["model_cur"] = fam.family.map(ofp[last_year])
    fam["model_next"] = fam.family.map(ofp[last_year + 1])
    fam["budget_cur"] = fam.family.map(b26.set_index("family").budget_sales)

    # ---------- seasonality ----------
    se = se.sort_values("month_of_year")
    top2 = se.nlargest(2, "avg_share")
    low = se.nsmallest(1, "avg_share").iloc[0]
    mname = lambda m: pd.Timestamp(2000, int(m), 1).strftime("%B")

    # ---------- headline numbers and plain-language insights ----------
    sales_fy, sales_prev = float(yt.loc[fy, "sales_usd"]), float(yt.loc[fy - 1, "sales_usd"])
    peak_year = int(yt.loc[:fy, "sales_usd"].idxmax())
    vol_peak_year = int(yt.loc[:fy, "liters"].idxmax())
    margin_fy = 1 - float(yt.loc[fy, "cost_usd"]) / sales_fy
    big3 = fam.head(3)
    m = lambda v: f"${v / 1e6:,.1f}m"
    pc = lambda v: f"{v:+.1f}%"
    steady = fam[fam.status == "steady"].family.tolist()
    pricey = fam[fam.status == "price"].family.tolist()
    losing = fam[fam.status == "losing"].family.tolist()
    lst = lambda a: ", ".join(a[:-1]) + " and " + a[-1] if len(a) > 1 else (a[0] if a else "none")
    ytd_label = f"Jan–{pd.Timestamp(last_month + '-01').strftime('%b')} {last_year}"

    what_happened = [
        f"Sales peaked in {peak_year} at {m(yt.loc[peak_year, 'sales_usd'])}. In {fy} they fell to {m(sales_fy)} ({pc((sales_fy / sales_prev - 1) * 100)}).",
        f"The drop is about volume, not price: fewer litres cost {m(-br_fy['volume'])}, while price added only {m(br_fy['price'])}. "
        f"Litres sold in {fy} were {abs((yt.loc[fy, 'liters'] / yt.loc[vol_peak_year, 'liters'] - 1) * 100):.0f}% below their peak in {vol_peak_year}.",
        f"{ytd_label} continues the trend: sales {pc(br_ytd['sales_pct'])}, litres {pc(br_ytd['vol_pct'])}, price per litre {pc(br_ytd['price_pct'])} against the same months of {fy}.",
        f"Actual sales were {pc((bva_tot['actual_sales'] / bva_tot['budget_sales'] - 1) * 100)} against the forecast-based budget for {ytd_label}. "
        f"Lower volume explains {m(-bva_tot['var_volume'])} of the gap; price was {m(bva_tot['var_price'])} better.",
    ]
    actions = [
        {"h": f"Plan {last_year + 1} on a range, not one number.",
         "t": f"Plan for {m(trend_next)} (current trend continues) up to {m(model_next)} (forecast model). "
              f"The model was {abs(bva_tot['actual_sales'] / bva_tot['budget_sales'] - 1) * 100:.0f}% too high this year, so use the lower end as the base case."},
        {"h": "Fix volume, not price.",
         "t": f"Price rises of about {br_ytd['price_pct']:.1f}% do not make up for {abs(br_ytd['vol_pct']):.1f}% fewer litres. "
              f"Focus on getting more buyers and more outlets, for example promotions in the biggest families: {lst(big3.family.tolist())} ({big3.share_fy.sum() * 100:.0f}% of sales)."},
        {"h": "Back what is holding steady.", "t": f"{lst(steady)}: keep stock and shelf space here first."},
        {"h": "Check pricing where volume is falling fast.", "t": f"{lst(pricey)}: price rises hide part of the fall, but buyers are taking clearly fewer litres."},
        {"h": "Act where sales are shrinking.", "t": f"{lst(losing)}: defend the big sellers with promotions; in the small families, trim slow products to free up stock and cash."},
        {"h": "Plan stock and cash around the calendar.",
         "t": f"{mname(top2.iloc[0].month_of_year)} and {mname(top2.iloc[1].month_of_year)} are the strongest months "
              f"({(top2.avg_share.sum()) * 100:.0f}% of the year together); {mname(low.month_of_year)} is the weakest ({low.avg_share * 100:.1f}%). "
              f"Split the yearly budget by month with these shares, not by twelve."},
    ]

    data = {
        "meta": {"last_month": last_month, "last_year": last_year, "fy": fy, "n_ytd": n_ytd, "ytd_label": ytd_label,
                 "margin_note": MARGIN_NOTE, "source": "Iowa Department of Revenue, Alcohol Operations Bureau: Iowa Liquor Sales (CC BY 4.0), via BigQuery public datasets",
                 "built": pd.Timestamp.today().strftime("%Y-%m-%d")},
        "kpi": {"sales_fy": sales_fy, "sales_prev": sales_prev, "margin_fy": margin_fy,
                "liters_fy": float(yt.loc[fy, "liters"]), "liters_prev": float(yt.loc[fy - 1, "liters"]),
                "ytd_sales": ytd_actual, "ytd_sales_pct": br_ytd["sales_pct"], "bva_pct": (bva_tot["actual_sales"] / bva_tot["budget_sales"] - 1) * 100,
                "budget_fy_total": budget_fy_total},
        "years": [int(y) for y in yt.index],
        "year_sales": [float(v) for v in yt.sales_usd], "year_liters": [float(v) for v in yt.liters],
        "year_price": [float(s / l) for s, l in zip(yt.sales_usd, yt.liters)],
        "bridge_fy": br_fy, "bridge_ytd": br_ytd,
        "families": json.loads(fam.round(4).to_json(orient="records")),
        "status": STATUS,
        "bva_month": json.loads(bvm.assign(month=bvm.month.str[:7]).to_json(orient="records")),
        "bva_family": json.loads(bvf.round(2).to_json(orient="records")), "bva_total": bva_tot,
        "months": mt.month.tolist(), "month_sales": [float(v) for v in mt.sales_usd],
        "outlook": {"months": out_s.index.tolist(), "f": out_s.forecast.round(0).tolist(), "lo": out_s.lo.round(0).tolist(), "hi": out_s.hi.round(0).tolist()},
        "budget_months": {"months": bud_m.index.tolist(), "f": bud_m.forecast.tolist()},
        "scenarios": {"model_cur": model_cur, "model_next": model_next, "trend_cur": trend_cur, "trend_next": trend_next,
                      "trend_v": trend_v, "trend_p": trend_p, "ytd_actual": ytd_actual, "rest_fy_prev": rest_fy_prev},
        "seasonality": json.loads(se.to_json(orient="records")),
        "what_happened": what_happened, "actions": actions,
    }
    js = "// Generated by scripts/01_build_report_data.py from BigQuery results. Totals only: no store, supplier or product names.\n"
    js += "window.LIQ = " + json.dumps(data, separators=(",", ":"), default=lambda o: o.item() if hasattr(o, "item") else str(o)) + ";\n"
    (ROOT / "dashboard").mkdir(exist_ok=True)
    (ROOT / "dashboard" / "data.js").write_text(js, encoding="utf-8")
    print("\n".join(what_happened)); print()
    for a in actions:
        print("-", a["h"], a["t"])
    print(fam[["family", "status", "ytd_sales_pct", "ytd_vol_pct", "ytd_price_pct", "trend_next", "model_next"]].round(1).to_string())
    print({k: round(v / 1e6, 1) for k, v in data["scenarios"].items() if abs(v) > 1000})


if __name__ == "__main__":
    main()
