"""Do ECB words predict ECB actions? Compare speech tone with later interest rate decisions.

Rules fixed before looking at results:
  * policy rate = main refinancing rate until May 2014, deposit facility rate from June 2014
    (the deposit rate steers policy since rates went negative); this drops purely technical
    corridor changes (Jan 1999, Oct 2008, Sep 2024);
  * decision month = effective date minus 7 days (rates take effect about a week after the meeting);
  * tone = (hawkish - dovish) / (hawkish + dovish) over the last 3 months of speeches,
    expressed as the gap to its own average of the previous 24 months;
  * a turning point is a rate change in the opposite direction to the previous change;
  * a warning is "on time" if the tone gap has the right sign in at least 2 of the 3 months
    before the decision month.

Usage: python 04_words_vs_actions.py --rates-dir ../raw
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SWITCH = pd.Timestamp("2014-06-01")


def load_rates(raw_dir):
    def one(code):
        d = pd.read_csv(Path(raw_dir) / f"rate_{code}.csv", usecols=["TIME_PERIOD", "OBS_VALUE"]).dropna()
        d["TIME_PERIOD"] = pd.to_datetime(d.TIME_PERIOD)
        return d.set_index("TIME_PERIOD").OBS_VALUE.rename(code)
    r = pd.concat([one("DFR"), one("MRR_FR"), one("MRR_MBR")], axis=1).sort_index()
    r["MRO"] = r.MRR_FR.where(r.MRR_FR.notna(), r.MRR_MBR)
    r = r[["DFR", "MRO"]].ffill()
    r["policy_rate"] = np.where(r.index < SWITCH, r.MRO, r.DFR)
    r["instrument"] = np.where(r.index < SWITCH, "MRO", "DFR")
    ch = r.policy_rate.diff()
    # the switch itself is not a decision
    dec = r[(ch.abs() > 1e-9) & ~((r.index == r.index[r.index >= SWITCH][0]))].copy()
    dec["change"] = ch.loc[dec.index].round(4)
    dec = dec[dec.index > r.index.min()]
    dec["effective_date"] = dec.index.strftime("%Y-%m-%d")
    dec["decision_month"] = (dec.index - pd.Timedelta(days=7)).strftime("%Y-%m")
    dec["direction"] = np.sign(dec.change).astype(int)
    prev = dec.direction.shift(1)
    dec["turning_point"] = (prev.notna() & (dec.direction != prev))
    dec["cycle"] = np.where(dec.turning_point & (dec.direction > 0), "first hike",
                   np.where(dec.turning_point & (dec.direction < 0), "first cut", ""))
    return r, dec[["effective_date", "decision_month", "instrument", "policy_rate", "change", "direction",
                   "turning_point", "cycle"]].reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rates-dir", required=True)
    args = ap.parse_args()
    rates, dec = load_rates(args.rates_dir)
    dec.to_csv(ROOT / "data" / "policy_rate_decisions.csv", index=False)

    m = pd.read_csv(ROOT / "data" / "speech_signal_month.csv")
    m = m.set_index("month")
    h3, d3 = m.hawkish.rolling(3).sum(), m.dovish.rolling(3).sum()
    m["tone"] = ((h3 - d3) / (h3 + d3)).where(h3 + d3 >= 10)
    m["tone_gap"] = m.tone - m.tone.shift(1).rolling(24, min_periods=18).mean()
    m["policy_talk"] = m.policy_hits.rolling(3).sum() / m.all_hits.rolling(3).sum()
    chg = dec.groupby("decision_month").change.sum()
    m["rate_change"] = chg.reindex(m.index).fillna(0)
    # policy rate at month end
    pr = rates.policy_rate.resample("ME").last()
    pr.index = pr.index.strftime("%Y-%m")
    m["policy_rate"] = pr.reindex(m.index).ffill()
    m["next3_change"] = sum(m.rate_change.shift(-k) for k in (1, 2, 3))
    m["past3_change"] = sum(m.rate_change.shift(k) for k in (0, 1, 2))

    # 1. lead/lag profile: correlation of tone gap with the rate change in a 3-month window k months ahead
    prof = []
    for k in range(-12, 13):
        fut = sum(m.rate_change.shift(-(k + j)) for j in (1, 2, 3))
        ok = m.tone_gap.notna() & fut.notna()
        prof.append({"lead_months": k, "corr": round(float(np.corrcoef(m.tone_gap[ok], fut[ok])[0, 1]), 3)})

    # 2. regression: does tone add information beyond the most recent moves?
    ok = m[["tone_gap", "next3_change", "past3_change"]].notna().all(axis=1)
    y = m.next3_change[ok].values
    X0 = np.column_stack([np.ones(ok.sum()), m.past3_change[ok]])
    X1 = np.column_stack([X0, m.tone_gap[ok]])
    def r2(X):
        b = np.linalg.lstsq(X, y, rcond=None)[0]
        return 1 - ((y - X @ b) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    r2_base, r2_tone = r2(X0), r2(X1)

    # 3. warnings before each decision
    rows = []
    for r in dec.itertuples():
        months = pd.period_range(end=pd.Period(r.decision_month, "M") - 1, periods=3, freq="M").astype(str)
        g = m.tone_gap.reindex(months)
        right = int(((np.sign(g) == r.direction) & g.notna()).sum())
        rows.append({"decision_month": r.decision_month, "change": r.change, "direction": r.direction,
                     "cycle": r.cycle, "tone_gap_before": round(float(g.mean()), 3) if g.notna().any() else None,
                     "months_right_sign": right, "warned": right >= 2 if g.notna().sum() >= 2 else None})
    w = pd.DataFrame(rows)
    w.to_csv(ROOT / "data" / "decision_warnings.csv", index=False)
    tp = w[w.cycle != ""]
    allw = w[w.warned.notna()]
    prev_dir = dec.direction.shift(1)
    momentum_hits = int((prev_dir == dec.direction).sum())

    # 4. false alarms: clearly hawkish months (top 15% of tone gap) with no hike in the next 6 months
    thr = m.tone_gap.quantile(0.85)
    nxt6 = sum(m.rate_change.shift(-k).clip(lower=0) for k in range(1, 7))
    hawk_months = m[(m.tone_gap >= thr) & nxt6.notna()]
    false_alarm = hawk_months[nxt6.reindex(hawk_months.index) == 0]
    thr_d = m.tone_gap.quantile(0.15)
    nxt6c = sum(m.rate_change.shift(-k).clip(upper=0) for k in range(1, 7))
    dove_months = m[(m.tone_gap <= thr_d) & nxt6c.notna()]
    false_alarm_d = dove_months[nxt6c.reindex(dove_months.index) == 0]

    # chance benchmark for turning-point warnings: share of all 3-month windows meeting the rule
    sg = np.sign(m.tone_gap)
    def chance(direction):
        ok = [((sg.iloc[i - 3:i] == direction).sum() >= 2) for i in range(3, len(sg)) if sg.iloc[i - 3:i].notna().sum() >= 2]
        return float(np.mean(ok))
    tpa = tp[tp.warned.notna()]
    pc = [chance(d) for d in tpa.direction]
    n_tp, k_tp, p_avg = len(tpa), int(tpa.warned.sum()), float(np.mean(pc))
    from math import comb
    p_value = sum(comb(n_tp, j) * p_avg ** j * (1 - p_avg) ** (n_tp - j) for j in range(k_tp, n_tp + 1))
    base_hike = float((nxt6 > 0).mean()); after_hawk = float((nxt6[m.tone_gap >= thr] > 0).mean())
    base_cut = float((nxt6c < 0).mean()); after_dove = float((nxt6c[m.tone_gap <= thr_d] < 0).mean())

    # 5. event study around turning points
    ev = []
    for r in dec[dec.turning_point].itertuples():
        base = pd.Period(r.decision_month, "M")
        for k in range(-12, 7):
            mm = str(base + k)
            if mm in m.index and pd.notna(m.at[mm, "tone_gap"]):
                ev.append({"cycle": r.cycle, "decision_month": r.decision_month, "k": k,
                           "tone_gap": m.at[mm, "tone_gap"], "policy_talk": m.at[mm, "policy_talk"]})
    ev = pd.DataFrame(ev)
    ev_avg = ev.groupby(["cycle", "k"])[["tone_gap", "policy_talk"]].mean().reset_index()
    ev_avg.to_csv(ROOT / "data" / "turning_point_profile.csv", index=False, float_format="%.4f")

    m.reset_index()[["month", "n_speeches", "hawkish", "dovish", "tone", "tone_gap", "policy_talk", "rate_change",
                     "policy_rate"]].to_csv(ROOT / "data" / "words_vs_actions_month.csv", index=False, float_format="%.4f")
    best = max(prof, key=lambda p: p["corr"])
    res = {
        "decisions": int(len(dec)), "hikes": int((dec.direction > 0).sum()), "cuts": int((dec.direction < 0).sum()),
        "turning_points": int(len(tp)),
        "turning_points_warned": int(tp.warned.fillna(False).sum()),
        "turning_points_assessable": int(tp.warned.notna().sum()),
        "all_decisions_warned": int(allw.warned.sum()), "all_decisions_assessable": int(len(allw)),
        "momentum_baseline_hits": momentum_hits, "momentum_baseline_n": int(prev_dir.notna().sum()),
        "corr_tone_next3": next(p["corr"] for p in prof if p["lead_months"] == 0),
        "corr_tone_past3": next(p["corr"] for p in prof if p["lead_months"] == -3),
        "best_lead": best,
        "lead_lag_profile": prof,
        "r2_past_moves_only": round(float(r2_base), 3), "r2_with_tone": round(float(r2_tone), 3),
        "hawkish_months": int(len(hawk_months)), "hawkish_false_alarms": int(len(false_alarm)),
        "dovish_months": int(len(dove_months)), "dovish_false_alarms": int(len(false_alarm_d)),
        "tone_gap_thresholds": [round(float(thr_d), 3), round(float(thr), 3)],
        "turning_points_expected_by_chance": round(p_avg * n_tp, 1),
        "turning_points_p_value": round(float(p_value), 3),
        "base_rate_hike_6m": round(base_hike, 3), "hike_6m_after_hawkish": round(after_hawk, 3),
        "base_rate_cut_6m": round(base_cut, 3), "cut_6m_after_dovish": round(after_dove, 3),
        "latest_month": m.index[-1], "latest_tone_gap": round(float(m.tone_gap.iloc[-1]), 3),
        "latest_policy_rate": float(m.policy_rate.iloc[-1]),
    }
    (ROOT / "data" / "words_vs_actions_results.json").write_text(json.dumps(res, indent=2))
    print(json.dumps({k: v for k, v in res.items() if k != "lead_lag_profile"}, indent=2))
    print("lead/lag:", [(p["lead_months"], p["corr"]) for p in prof])
    print(tp.to_string())


if __name__ == "__main__":
    main()
