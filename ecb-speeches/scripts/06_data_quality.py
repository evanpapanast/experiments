"""Data quality, privacy and copyright gate for the ECB speeches experiment.

Runs on the committed files only (no raw data needed), so it also runs in GitHub Actions.
FAIL checks stop the pipeline (exit code 1); WARN checks are reported but do not stop it.
Writes data_quality/dq_report.md.

Usage: python 06_data_quality.py
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"
TOL = 1e-4   # shares are stored with 6 decimals, so 15 topics can round to a few millionths off 100%

# every column allowed in a published data file; anything else (e.g. a title or speaker column) fails Q01
APPROVED = {
    "speech_topics.csv": {"speech_id", "date", "year", "quarter", "word_count", "total_hits", "primary_topic", "n_tags",
                          *[f"T{i:02d}" for i in range(1, 16)]},
    "speech_tags.csv": {"speech_id", "topic_id"},
    "topic_share_year.csv": {"year", "topic_id", "share", "hits", "n_speeches", "words", "hits_per_10k_words"},
    "topic_share_quarter.csv": {"quarter", "topic_id", "share", "hits", "n_speeches", "words", "hits_per_10k_words"},
    "dim_topic.csv": {"topic_id", "topic_name", "description", "keywords"},
    "term_frequency_year.csv": {"year", "term", "per_10k_words", "count"},
    "speech_signal_month.csv": {"month", "n_speeches", "words", "hawkish", "dovish", "policy_hits", "all_hits"},
    "words_vs_actions_month.csv": {"month", "n_speeches", "hawkish", "dovish", "tone", "tone_gap", "policy_talk",
                                   "rate_change", "policy_rate"},
    "policy_rate_decisions.csv": {"effective_date", "decision_month", "instrument", "policy_rate", "change", "direction",
                                  "turning_point", "cycle"},
    "decision_warnings.csv": {"decision_month", "change", "direction", "cycle", "tone_gap_before", "months_right_sign",
                              "warned"},
    "turning_point_profile.csv": {"cycle", "k", "tone_gap", "policy_talk"},
}
FORBIDDEN = re.compile(r"\b(title|subtitle|speaker|speakers|contents|text|name_of|author)\b")
MAX_CELL = 160          # longest text cell allowed in data files (speech text would be far longer)
MAX_JS_STRING = 700     # longest string allowed in the report data


def main():
    res = []

    def check(cid, cat, sev, rule, bad, detail=""):
        res.append({"id": cid, "category": cat, "severity": sev, "rule": rule,
                    "status": "PASS" if bad == 0 else sev, "failures": int(bad), "detail": detail})

    files = {f.name: pd.read_csv(f) for f in sorted(D.glob("*.csv"))}
    man = json.loads((D / "manifest.json").read_text())
    st, ys = files["speech_topics.csv"], files["topic_share_year.csv"]
    ids = [f"T{i:02d}" for i in range(1, 16)]

    # ---- privacy & copyright ----
    unknown = [f"{n}: {c}" for n, df in files.items() for c in df.columns
               if n not in APPROVED or c not in APPROVED[n] or FORBIDDEN.search(c.lower())]
    check("Q01", "Privacy", "FAIL", "Data files contain only approved columns (no titles, speakers or text)", len(unknown), "; ".join(unknown[:5]))
    long_cells = []
    for n, df in files.items():
        for c in df.columns[df.dtypes.astype(str).isin(["object", "str", "string"])]:
            if n == "dim_topic.csv" and c == "keywords":
                continue
            L = df[c].astype(str).str.len()
            if (L > MAX_CELL).any():
                long_cells.append(f"{n}.{c} ({int(L.max())} chars)")
    check("Q02", "Copyright", "FAIL", f"No text cell longer than {MAX_CELL} characters in the data files", len(long_cells), "; ".join(long_cells))
    js = (ROOT / "dashboard" / "data.js").read_text(encoding="utf-8")
    data = json.loads(js[js.index("=") + 1:].strip().rstrip(";"))
    strings = []
    def walk(o):
        if isinstance(o, dict):
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
        elif isinstance(o, str):
            strings.append(o)
    walk(data)
    too_long = [s_ for s_ in strings if len(s_) > MAX_JS_STRING]
    check("Q03", "Copyright", "FAIL", f"No text in the report data longer than {MAX_JS_STRING} characters", len(too_long))
    bad_terms = [t for t in files["term_frequency_year.csv"].term.unique()
                 if not re.fullmatch(r"[a-z][a-z\-]*( [a-z][a-z\-]*)?", str(t))]
    check("Q04", "Privacy", "FAIL", "Word-search terms are lower-case words or two-word phrases only", len(bad_terms), ", ".join(bad_terms[:5]))

    # ---- completeness ----
    check("C01", "Completeness", "FAIL", "Every analysed speech is in the speech table (matches the manifest)",
          abs(len(st) - man["analysed_speeches"]))
    gaps = int((st.speech_id.diff().dropna() != 1).sum()) + int(st.speech_id.iloc[0] != 1)
    check("C02", "Completeness", "FAIL", "Speech numbers run 1, 2, 3 ... without gaps or repeats", gaps)
    exp = set(range(1999, int(st.year.max()) + 1))
    check("C03", "Completeness", "FAIL", "Every year from 1999 has topic shares", len(exp - set(ys.year)))
    sm = files["speech_signal_month.csv"]
    check("C04", "Completeness", "FAIL", "Monthly signal covers every analysed speech", abs(int(sm.n_speeches.sum()) - len(st)))

    # ---- validity ----
    check("V01", "Validity", "FAIL", "Speeches have at least 200 words and dates from 1999 on",
          int(((st.word_count < man["rules"]["min_words"]) | (st.year < 1999)).sum()))
    check("V02", "Validity", "FAIL", "Topic codes are known (T01 to T15 or NONE)", int((~st.primary_topic.isin(ids + ["NONE"])).sum()))
    neg = sum(int((files[n].select_dtypes("number") < 0).sum().sum()) for n in
              ("speech_topics.csv", "topic_share_year.csv", "term_frequency_year.csv", "speech_signal_month.csv"))
    check("V03", "Validity", "FAIL", "Counts and shares are never negative", neg)
    rv = pd.read_csv(ROOT / "data_quality" / "manual_review.csv")
    check("V04", "Validity", "FAIL", "Manual review results are right, acceptable (defensible) or wrong",
          int((~rv.verdict.isin(["correct", "defensible", "wrong"])).sum()))

    # ---- consistency ----
    s_sum = ys.groupby("year").share.sum()
    check("K01", "Consistency", "FAIL", "Topic shares add up to 100% in every year", int(((s_sum - 1).abs() > TOL).sum()))
    check("K02", "Consistency", "FAIL", "Each speech's total equals the sum of its topic counts",
          int((st[ids].sum(axis=1) != st.total_hits).sum()))
    argmax = st[ids].idxmax(axis=1).where(st.total_hits > 0, "NONE")
    check("K03", "Consistency", "FAIL", "Each speech's main topic is the topic with the most matches", int((argmax != st.primary_topic).sum()))
    dec = files["policy_rate_decisions.csv"]
    wr = json.loads((D / "words_vs_actions_results.json").read_text())
    bad_dec = int((dec.change == 0).sum() + (pd.Series(dec.change).apply(lambda x: (x > 0) - (x < 0)) != dec.direction).sum())
    flips = int((dec.direction != dec.direction.shift()).iloc[1:].sum())
    check("K04", "Consistency", "FAIL", "Rate decisions are real changes and their direction matches the sign", bad_dec)
    check("K05", "Consistency", "FAIL", "Changes of direction match the decision list, and totals match the results",
          abs(flips - int(dec.turning_point.sum())) + abs(len(dec) - wr["decisions"]) + abs(flips - wr["turning_points"]))
    check("K06", "Consistency", "FAIL", "The report uses the same results as the analysis files",
          int(data["wa"]["results"] != wr) + int(data["meta"] != man))
    ag = data["agenda"]["rows"]
    check("K07", "Consistency", "FAIL", "Now and usual shares on the 'Now' page each add up to 100%",
          int(abs(sum(r["now"] for r in ag) - 1) > 1e-3) + int(abs(sum(r["usual"] for r in ag) - 1) > 1e-3))

    # ---- accuracy and freshness (warnings) ----
    ok_share = (rv.verdict != "wrong").mean()
    check("A01", "Accuracy", "WARN", "At least 80% of hand-checked labels are right or acceptable",
          int(ok_share < 0.8), f"{ok_share:.0%} right or acceptable, {(rv.verdict == 'correct').mean():.0%} clearly right")
    days = (pd.Timestamp.today().normalize() - pd.Timestamp(man["raw_last_speech_date"])).days
    check("F01", "Freshness", "WARN", "Latest speech is less than 90 days old (the ECB updates the file monthly)",
          int(days > 90), f"latest speech {man['raw_last_speech_date']}, {days} days ago")
    untag = int((st.n_tags == 0).sum())
    check("A02", "Accuracy", "WARN", "Fewer than 2% of speeches get no topic label", int(untag / len(st) > 0.02),
          f"{untag} speeches without a label")

    r = pd.DataFrame(res)
    n = r.status.value_counts()
    icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}
    lines = ["# Data quality report: What the ECB says, and what it does", "",
             f"Run on committed files. **{n.get('PASS', 0)} PASS, {n.get('WARN', 0)} WARN, {n.get('FAIL', 0)} FAIL.**", "",
             "| ID | Area | Rule | Result | Problems | Detail |", "|---|---|---|---|---|---|"]
    for x in res:
        lines.append(f"| {x['id']} | {x['category']} | {x['rule']} | {icon[x['status']]} {x['status']} | {x['failures']} | {x['detail']} |")
    (ROOT / "data_quality" / "dq_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(r[["id", "category", "status", "failures", "detail"]].to_string(index=False))
    print(f"\n{n.get('PASS', 0)} PASS, {n.get('WARN', 0)} WARN, {n.get('FAIL', 0)} FAIL  ->  data_quality/dq_report.md")
    sys.exit(1 if n.get("FAIL", 0) else 0)


if __name__ == "__main__":
    main()
