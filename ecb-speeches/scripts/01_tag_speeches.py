"""Tag ECB speeches with the topic playbook and write aggregate tables.

Input : the ECB speeches dataset (CSV, '|' separated), kept outside the repository.
Output: speech-level topic counts and yearly/quarterly topic shares.

Privacy and copyright by design:
  * speech text, titles, subtitles and speaker names are read in memory only and never written out;
  * each speech gets an anonymous sequential id (order of date, then original row order).

Usage: python 01_tag_speeches.py --raw ../raw/all_ECB_speeches.csv
"""
import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FIRST_YEAR = 1999          # first full year of the ECB and the euro
MIN_WORDS = 200            # shorter items are slides, notes or greetings
EN_SHARE_MIN = 0.08        # share of the five most common English words; below = not English
TAG_MIN_HITS = 3           # a speech carries a topic tag if the topic has >= 3 hits ...
TAG_MIN_DENSITY = 1.0      # ... and >= 1 hit per 1,000 words


def load_playbook():
    topics = []
    for line in (ROOT / "playbook" / "taxonomy.csv").read_text(encoding="utf-8").splitlines()[1:]:
        if not line.strip():
            continue
        parts = line.split("|")
        kws = sorted({k.strip().lower() for k in parts[3:] if k.strip()}, key=len, reverse=True)
        # longest phrase first so that "climate change" is one hit, not "climate" + "climate change"
        pattern = re.compile(r"(?<![a-z0-9-])(?:" + "|".join(re.escape(k) for k in kws) + r")(?![a-z0-9-])")
        topics.append({"id": parts[0], "name": parts[1], "description": parts[2], "keywords": kws, "re": pattern})
    return topics


def english_share(text):
    words = re.findall(r"[a-z]+", text.lower()[:6000])
    return sum(w in ("the", "and", "of", "to", "in") for w in words) / max(len(words), 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    args = ap.parse_args()
    raw = Path(args.raw)
    raw_sha = hashlib.sha256(raw.read_bytes()).hexdigest()

    d = pd.read_csv(raw, sep="|", quoting=3, dtype=str, encoding="utf-8", keep_default_na=False)
    n_raw = len(d)
    d = d.reset_index().rename(columns={"index": "source_row"})
    d["word_count"] = d.contents.str.split().str.len()
    d["year"] = d.date.str[:4].astype(int)
    d["en_share"] = d.contents.map(english_share)

    excl = {
        "before_1999": int((d.year < FIRST_YEAR).sum()),
        "too_short_or_slides": int(((d.year >= FIRST_YEAR) & (d.word_count < MIN_WORDS)).sum()),
        "not_english": int(((d.year >= FIRST_YEAR) & (d.word_count >= MIN_WORDS) & (d.en_share < EN_SHARE_MIN)).sum()),
    }
    d = d[(d.year >= FIRST_YEAR) & (d.word_count >= MIN_WORDS) & (d.en_share >= EN_SHARE_MIN)].copy()
    d = d.sort_values(["date", "source_row"], kind="mergesort").reset_index(drop=True)
    d["speech_id"] = range(1, len(d) + 1)

    topics = load_playbook()
    low = d.contents.str.lower()
    for t in topics:
        d[t["id"]] = low.map(lambda s, r=t["re"]: len(r.findall(s)))
    ids = [t["id"] for t in topics]
    d["total_hits"] = d[ids].sum(axis=1)
    d["primary_topic"] = d[ids].idxmax(axis=1).where(d.total_hits > 0, "NONE")
    dens = d[ids].div(d.word_count, axis=0) * 1000
    tagged = (d[ids] >= TAG_MIN_HITS) & (dens >= TAG_MIN_DENSITY)
    d["n_tags"] = tagged.sum(axis=1)
    d["quarter"] = d.date.str[:4] + "-Q" + ((d.date.str[5:7].astype(int) - 1) // 3 + 1).astype(str)

    out = d[["speech_id", "date", "year", "quarter", "word_count", *ids, "total_hits", "primary_topic", "n_tags"]]
    out.to_csv(ROOT / "data" / "speech_topics.csv", index=False)
    for t in topics:
        out_t = tagged[t["id"]]
        d[t["id"] + "_tag"] = out_t
    tags_long = (tagged.stack().rename("is_tagged").reset_index()
                 .rename(columns={"level_0": "row", "level_1": "topic_id"}))
    tags_long["speech_id"] = d.speech_id.values[tags_long.row]
    tags_long[tags_long.is_tagged][["speech_id", "topic_id"]].to_csv(ROOT / "data" / "speech_tags.csv", index=False)

    # share of voice: topic hits / all topic hits, per period
    def share(period):
        g = d.groupby(period)[ids].sum()
        s = g.div(g.sum(axis=1), axis=0).stack().rename("share").reset_index().rename(columns={"level_1": "topic_id"})
        h = g.stack().rename("hits").reset_index().rename(columns={"level_1": "topic_id"})
        n = d.groupby(period).agg(n_speeches=("speech_id", "size"), words=("word_count", "sum")).reset_index()
        m = s.merge(h, on=[period, "topic_id"]).merge(n, on=period)
        m["hits_per_10k_words"] = m.hits / m.words * 10000
        return m

    share("year").to_csv(ROOT / "data" / "topic_share_year.csv", index=False, float_format="%.6f")
    share("quarter").to_csv(ROOT / "data" / "topic_share_quarter.csv", index=False, float_format="%.6f")
    pd.DataFrame([{k: t[k] for k in ("id", "name", "description")} | {"keywords": "|".join(sorted(t["keywords"]))}
                  for t in topics]).rename(columns={"id": "topic_id", "name": "topic_name"}).to_csv(
        ROOT / "data" / "dim_topic.csv", index=False)

    manifest = {
        "source": "European Central Bank, Speeches dataset, https://www.ecb.europa.eu/press/key/html/downloads.en.html",
        "retrieved": date.today().isoformat(),
        "raw_file_sha256": raw_sha,
        "raw_rows": n_raw,
        "raw_last_speech_date": d.date.max(),
        "excluded": excl,
        "analysed_speeches": int(len(d)),
        "analysed_words": int(d.word_count.sum()),
        "rules": {"first_year": FIRST_YEAR, "min_words": MIN_WORDS, "english_share_min": EN_SHARE_MIN,
                  "tag_min_hits": TAG_MIN_HITS, "tag_min_density_per_1000_words": TAG_MIN_DENSITY},
        "published_fields_note": "No speech text, titles, subtitles or speaker names are written to any output.",
    }
    (ROOT / "data" / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))
    print(d.primary_topic.value_counts().to_string())
    print("untagged speeches:", int((d.n_tags == 0).sum()))


if __name__ == "__main__":
    main()
