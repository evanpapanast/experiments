"""Monthly speech signals: policy-talk share and hawk/dove tone.

The tone word list (playbook/tone_lexicon.csv) was fixed before any comparison with interest rates.
Writes monthly aggregates only (no text, no names).

Usage: python 03_monthly_signal.py --raw ../raw/all_ECB_speeches.csv
"""
import argparse
import importlib.util
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    args = ap.parse_args()
    spec = importlib.util.spec_from_file_location("tagger", Path(__file__).with_name("01_tag_speeches.py"))
    tagger = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tagger)

    d = pd.read_csv(args.raw, sep="|", quoting=3, dtype=str, encoding="utf-8", keep_default_na=False)
    d = d.reset_index().rename(columns={"index": "source_row"})
    d["word_count"] = d.contents.str.split().str.len()
    d["year"] = d.date.str[:4].astype(int)
    d["en_share"] = d.contents.map(tagger.english_share)
    d = d[(d.year >= tagger.FIRST_YEAR) & (d.word_count >= tagger.MIN_WORDS) & (d.en_share >= tagger.EN_SHARE_MIN)]
    d = d.sort_values(["date", "source_row"], kind="mergesort").reset_index(drop=True)
    d["speech_id"] = range(1, len(d) + 1)

    lex = pd.read_csv(ROOT / "playbook" / "tone_lexicon.csv", sep="|")
    low = d.contents.str.lower()
    for tone in ("hawkish", "dovish"):
        kws = sorted(lex[lex.tone == tone].phrase.str.lower(), key=len, reverse=True)
        rx = re.compile(r"(?<![a-z0-9-])(?:" + "|".join(re.escape(k) for k in kws) + r")(?![a-z0-9-])")
        d[tone] = low.map(lambda s: len(rx.findall(s)))

    tags = pd.read_csv(ROOT / "data" / "speech_topics.csv")
    assert (tags.speech_id.values == d.speech_id.values).all()
    d["policy_hits"] = tags.T01.values + tags.T02.values
    d["all_hits"] = tags.total_hits.values
    d["month"] = d.date.str[:7]
    m = d.groupby("month").agg(n_speeches=("speech_id", "size"), words=("word_count", "sum"),
                               hawkish=("hawkish", "sum"), dovish=("dovish", "sum"),
                               policy_hits=("policy_hits", "sum"), all_hits=("all_hits", "sum")).reset_index()
    # fill months without speeches so that rolling windows are calendar-based
    allm = pd.period_range(m.month.min(), m.month.max(), freq="M").astype(str)
    m = m.set_index("month").reindex(allm, fill_value=0).rename_axis("month").reset_index()
    m.to_csv(ROOT / "data" / "speech_signal_month.csv", index=False)
    print(m.tail(6).to_string())
    print("months:", len(m), " months without speeches:", int((m.n_speeches == 0).sum()))
    print("total hawkish hits:", int(m.hawkish.sum()), " dovish hits:", int(m.dovish.sum()))


if __name__ == "__main__":
    main()
