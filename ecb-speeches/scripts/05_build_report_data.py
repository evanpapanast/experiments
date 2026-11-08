"""Build dashboard/data.js (window.SPEECH_DATA) from the aggregate tables in data/.

Reads only the derived, aggregate CSVs: no raw speech data is needed or touched here.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"

EVENTS = [  # well-documented milestones, shown as markers on the timelines
    {"date": "1999-01-01", "label": "Euro launched"},
    {"date": "2002-01-01", "label": "Euro cash"},
    {"date": "2008-09-15", "label": "Global financial crisis"},
    {"date": "2010-05-02", "label": "Sovereign debt crisis"},
    {"date": "2012-07-26", "label": "“Whatever it takes”"},
    {"date": "2014-11-04", "label": "ECB banking supervision starts"},
    {"date": "2015-01-22", "label": "QE announced"},
    {"date": "2020-03-11", "label": "Pandemic"},
    {"date": "2021-07-08", "label": "Strategy review"},
    {"date": "2022-07-21", "label": "First rate hike since 2011"},
    {"date": "2023-10-18", "label": "Digital euro preparation phase"},
]


def main():
    man = json.loads((D / "manifest.json").read_text())
    topics = pd.read_csv(D / "dim_topic.csv")
    ys = pd.read_csv(D / "topic_share_year.csv")
    qs = pd.read_csv(D / "topic_share_quarter.csv")
    st = pd.read_csv(D / "speech_topics.csv")
    tf = pd.read_csv(D / "term_frequency_year.csv")
    rv = pd.read_csv(ROOT / "data_quality" / "manual_review.csv")

    tids = topics.topic_id.tolist()
    years = sorted(ys.year.unique().tolist())
    share = ys.pivot(index="topic_id", columns="year", values="share").loc[tids, years]
    per10k = ys.pivot(index="topic_id", columns="year", values="hits_per_10k_words").loc[tids, years]
    quarters = sorted(qs.quarter.unique().tolist())
    qshare = qs.pivot(index="topic_id", columns="quarter", values="share").loc[tids, quarters].fillna(0)
    qn = qs.drop_duplicates("quarter").set_index("quarter").loc[quarters, "n_speeches"]
    yn = ys.drop_duplicates("year").set_index("year").loc[years]
    prim = st.primary_topic.value_counts()

    terms = tf.pivot(index="term", columns="year", values="per_10k_words").reindex(columns=years).fillna(0)
    term_tot = tf.groupby("term")["count"].sum()
    terms = terms.loc[term_tot.sort_values(ascending=False).index]

    # computed insights (all numbers from the tables above)
    last_full = years[-2]
    def pct(t, y):
        return share.loc[t, y] * 100
    infl_min_year = int(share.loc["T01"].idxmin())
    fs_peak_year = int(share.loc["T05"].idxmax())
    pay_peak_year = int(share.loc["T09"].idxmax())
    insights = [
        f"Inflation is the ECB's main subject. It took {pct('T01', years[0]):.0f}% of the ECB's attention in {years[0]}, "
        f"fell to {pct('T01', infl_min_year):.0f}% in {infl_min_year} when crises took over, and rose again to "
        f"{share.loc['T01'].loc[2022:2024].max() * 100:.0f}% when prices jumped in 2022\u201324.",
        f"Crisis talk was highest in {fs_peak_year}: {pct('T05', fs_peak_year):.0f}% of attention went to financial stability. "
        f"Government debt came next ({share.loc['T06'].max() * 100:.0f}% in {int(share.loc['T06'].idxmax())}), "
        f"then bank supervision ({share.loc['T04'].max() * 100:.0f}% in {int(share.loc['T04'].idxmax())}).",
        f"Climate was almost never mentioned before 2019 (never more than {share.loc['T10'].loc[:2018].max() * 100:.1f}% a year). "
        f"It jumped to {share.loc['T10'].max() * 100:.0f}% in {int(share.loc['T10'].idxmax())}, the year the ECB reviewed its strategy.",
        f"Payments and the digital euro reached {pct('T09', pay_peak_year):.0f}% of attention in {pay_peak_year}, the highest since 1999.",
        f"In {years[-1]} so far, technology and AI are the top subject with {pct('T11', years[-1]):.0f}% of attention, "
        f"up from {pct('T11', last_full):.0f}% in {last_full}.",
    ]

    # ---- agenda radar: last 12 months vs the 10 years before ----
    st["month"] = st.date.str[:7]
    end_m = pd.Period(st.month.max(), "M")
    now0, base0 = end_m - 11, end_m - 11 - 120
    now_s = st[(st.month >= str(now0)) & (st.month <= str(end_m))]
    base_s = st[(st.month >= str(base0)) & (st.month < str(now0))]
    now_sh = now_s[tids].sum() / now_s[tids].sum().sum()
    base_sh = base_s[tids].sum() / base_s[tids].sum().sum()
    means = pd.read_csv(ROOT / "playbook" / "what_it_means.csv", sep="|").set_index("topic_id")
    radar = []
    for t in tids:
        n_, b_ = float(now_sh[t]), float(base_sh[t])
        ratio, diff = n_ / b_, (n_ - b_) * 100
        status = "more" if ratio >= 1.3 and diff >= 1 else ("less" if ratio <= 0.75 and diff <= -1 else "usual")
        radar.append({"id": t, "now": round(n_, 5), "usual": round(b_, 5), "ratio": round(ratio, 3), "diff_pts": round(diff, 2),
                      "status": status, "means": means.loc[t, "when_more"] if status == "more" else
                      (means.loc[t, "when_less"] if status == "less" else "")})
    radar.sort(key=lambda r: -r["diff_pts"])
    agenda = {"from": str(now0), "to": str(end_m), "base_from": str(base0), "base_to": str(now0 - 1),
              "n_now": int(len(now_s)), "n_base": int(len(base_s)), "rows": radar}

    # ---- words vs actions ----
    wr = json.loads((D / "words_vs_actions_results.json").read_text())
    wm = pd.read_csv(D / "words_vs_actions_month.csv")
    dec = pd.read_csv(D / "policy_rate_decisions.csv")
    warn = pd.read_csv(D / "decision_warnings.csv")
    bl = wr["best_lead"]["lead_months"]
    win = (bl + 1, bl + 3)
    def when(a, b):
        return f"{-b}\u2013{-a} months before" if b < 0 else (f"{a}\u2013{b} months after" if a > 0 else "around the time of")
    tp = warn[warn.cycle.notna()]
    missed = tp[tp.warned == False]
    last_hikes = dec[(dec.direction > 0) & (dec.decision_month >= str(int(wr["latest_month"][:4]) - 1))]
    wa_takeaways = [
        {"h": "Speeches mostly explain decisions the ECB has already made.",
         "t": f"The link between what the ECB says and what it does is strongest for decisions made {when(*win)} the speeches. "
              f"The link with the next 3 months is much weaker. If you already know the ECB's last few decisions, "
              f"the speeches do not help you guess the next one."},
        {"h": "When the ECB starts to sound worried about the economy, a rate cut often follows.",
         "t": f"After a month with a clearly soft tone, the ECB cut rates within 6 months in {wr['cut_6m_after_dovish'] * 100:.0f}% of cases. "
              f"In a normal month, the figure is {wr['base_rate_cut_6m'] * 100:.0f}%."},
        {"h": "Tough talk about inflation usually does not lead to a rate rise.",
         "t": f"In {wr['hawkish_false_alarms']} out of {wr['hawkish_months']} months with a clearly tough tone, no rate rise came in the next 6 months. "
              f"A rise followed in {wr['hike_6m_after_hawkish'] * 100:.0f}% of cases, close to the {wr['base_rate_hike_6m'] * 100:.0f}% of a normal month."},
        {"h": "Before a change of direction, the speeches often gave a hint, but there are too few cases to be sure.",
         "t": f"Before {wr['turning_points_warned']} of the {wr['turning_points_assessable']} changes of direction, the tone already pointed the right way. "
              f"Pure luck would give about {wr['turning_points_expected_by_chance']:.0f}. "
              f"The two misses were {' and '.join(pd.to_datetime(missed.decision_month).dt.strftime('%B %Y'))}: "
              f"the tone was still tough just before the first cut."},
    ]
    wa_now = (f"Today ({pd.to_datetime(wr['latest_month']).strftime('%B %Y')}): the tone is "
              f"{'tougher' if wr['latest_tone_gap'] > 0 else 'softer'} than usual"
              + (f", after rate rises in {' and '.join(pd.to_datetime(last_hikes.decision_month).dt.strftime('%B %Y'))}" if len(last_hikes) else "")
              + ". Based on the past, this tough tone most likely explains the recent rises. It is not a reliable sign of another one.")
    words_vs_actions = {
        "results": wr, "takeaways": wa_takeaways, "now": wa_now,
        "lexicon": pd.read_csv(ROOT / "playbook" / "tone_lexicon.csv", sep="|").to_dict(orient="records"),
        "months": wm.month.tolist(),
        "rate": wm.policy_rate.round(2).tolist(),
        "tone_gap": [None if pd.isna(v) else round(float(v), 3) for v in wm.tone_gap],
        "n_speeches": wm.n_speeches.astype(int).tolist(),
        "decisions": dec[["decision_month", "effective_date", "change", "direction", "cycle", "instrument"]].fillna("").to_dict(orient="records"),
        "turning_points": tp[["decision_month", "change", "direction", "cycle", "tone_gap_before", "months_right_sign", "warned"]]
                            .astype(object).where(tp[["decision_month", "change", "direction", "cycle", "tone_gap_before", "months_right_sign", "warned"]].notna(), None)
                            .to_dict(orient="records"),
    }

    data = {
        "meta": man,
        "years": years,
        "topics": [{"id": r.topic_id, "name": r.topic_name, "description": r.description,
                    "keywords": r.keywords.split("|"), "primary_speeches": int(prim.get(r.topic_id, 0))}
                   for r in topics.itertuples()],
        "share": share.round(5).values.tolist(),
        "per10k": per10k.round(2).values.tolist(),
        "quarters": quarters,
        "qshare": qshare.round(5).values.tolist(),
        "q_speeches": [int(x) for x in qn.values],
        "y_speeches": [int(x) for x in yn.n_speeches.values],
        "y_words": [int(x) for x in yn.words.values],
        "events": EVENTS,
        "insights": insights,
        "review": {
            "sample_size": int(len(rv)), "seed": int(rv.sample_seed.iloc[0]), "version": rv.playbook_version.iloc[0],
            "counts": rv.verdict.value_counts().to_dict(),
            "rows": rv.fillna("").to_dict(orient="records"),
        },
        "wa": words_vs_actions,
        "agenda": agenda,
        "terms": {t: [round(float(v), 2) for v in row] for t, row in zip(terms.index, terms.values)},
    }
    js = "// Generated by scripts/05_build_report_data.py. Aggregate statistics only: no speech text, no names.\n"
    js += "window.SPEECH_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
    (ROOT / "dashboard" / "data.js").write_text(js, encoding="utf-8")
    print(f"data.js {len(js) / 1024:.0f} KB")
    print("\n".join(insights))


if __name__ == "__main__":
    main()
