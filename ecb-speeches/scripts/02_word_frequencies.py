"""Yearly frequency of the most used terms, for the word explorer.

Writes only term counts per year (no text). To keep personal names out, a term is dropped when it is
mostly written with a capital letter in the speeches (a proper noun), unless it is an all-caps acronym
or on the allow-list of places and institutions below.

Usage: python 02_word_frequencies.py --raw ../raw/all_ECB_speeches.csv
"""
import argparse
import re
from collections import Counter
from pathlib import Path

import importlib.util
import pandas as pd
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, CountVectorizer

ROOT = Path(__file__).resolve().parent.parent
N_TERMS = 3000
MIN_DOCS = 15
ALLOW = {  # places and institutions (not persons) that are written with capitals
    "europe", "european", "germany", "france", "italy", "spain", "greece", "portugal", "ireland", "netherlands",
    "belgium", "austria", "finland", "slovakia", "slovenia", "estonia", "latvia", "lithuania", "croatia",
    "bulgaria", "cyprus", "malta", "luxembourg", "poland", "hungary", "romania", "sweden", "denmark",
    "china", "japan", "russia", "ukraine", "india", "brazil", "america", "american", "asia", "asian", "africa",
    "british", "britain", "kingdom", "united", "states", "london", "frankfurt", "brussels", "washington",
    "german", "french", "italian", "spanish", "greek", "chinese", "japanese", "russian",
    "eurosystem", "eurogroup", "eurostat", "treaty", "maastricht", "lisbon", "parliament", "commission",
    "council", "federal", "reserve", "basel", "brexit", "euro", "union", "governing", "fed", "english",
    "member", "states", "economics", "artificial", "intelligence", "internet", "covid",
}
MUST_HAVE = ["ai", "artificial intelligence", "digital euro", "climate change", "stablecoins", "crypto",
             "tariffs", "pandemic", "energy", "war", "deflation", "inflation", "negative interest", "forward guidance",
             "quantitative easing", "asset purchases", "banking union", "brexit", "fragmentation", "geopolitical",
             "cyber", "fintech", "cash", "nature", "biodiversity", "demographics", "productivity", "trust",
             "wages", "housing", "uncertainty", "resilience", "sovereign debt", "whatever it takes", "member states"]
STOP = set(ENGLISH_STOP_WORDS) | {"mr", "ms", "dr", "prof", "et", "al", "pp", "ibid", "vol", "www", "http", "https",
                                  "html", "en", "pdf", "op", "cit"}


def load_selection(raw):
    spec = importlib.util.spec_from_file_location("tagger", Path(__file__).with_name("01_tag_speeches.py"))
    tagger = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tagger)
    d = pd.read_csv(raw, sep="|", quoting=3, dtype=str, encoding="utf-8", keep_default_na=False)
    d = d.reset_index().rename(columns={"index": "source_row"})
    d["word_count"] = d.contents.str.split().str.len()
    d["year"] = d.date.str[:4].astype(int)
    d["en_share"] = d.contents.map(tagger.english_share)
    d = d[(d.year >= tagger.FIRST_YEAR) & (d.word_count >= tagger.MIN_WORDS) & (d.en_share >= tagger.EN_SHARE_MIN)]
    return d.sort_values(["date", "source_row"], kind="mergesort").reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    args = ap.parse_args()
    d = load_selection(args.raw)

    # capitalisation profile of every word (mid-sentence occurrences only)
    total, capital, allcaps = Counter(), Counter(), Counter()
    for text in d.contents:
        for m in re.finditer(r"(?<=[a-z,;:] )([A-Za-z][A-Za-z\-]+)", text):
            w = m.group(1)
            lw = w.lower()
            total[lw] += 1
            if w[0].isupper():
                capital[lw] += 1
            if w.isupper() and len(w) >= 2:
                allcaps[lw] += 1

    def is_proper(word):
        n = total.get(word, 0)
        if n == 0 or word in ALLOW:
            return False
        if allcaps[word] / n > 0.6:      # acronym such as ECB, SSM, AI
            return False
        return capital[word] / n > 0.7

    vec = CountVectorizer(lowercase=True, ngram_range=(1, 2), min_df=MIN_DOCS,
                          token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z\-]*[a-zA-Z]\b", stop_words=list(STOP))
    X = vec.fit_transform(d.contents)
    terms = vec.get_feature_names_out()
    counts = pd.Series(X.sum(axis=0).A1, index=terms)
    keep = [t for t in counts.index if not any(is_proper(w) for w in t.split())]
    dropped = sorted(set(counts.index) - set(keep), key=lambda t: -counts[t])
    top = counts[keep].sort_values(ascending=False).head(N_TERMS)
    # terms the explorer suggests are always included (if they occur and pass the name filter)
    must = [t for t in MUST_HAVE if t in counts.index and t in keep and t not in top.index]
    top = pd.concat([top, counts[must]])

    idx = [vec.vocabulary_[t] for t in top.index]
    sub = pd.DataFrame(X[:, idx].toarray(), columns=top.index)
    sub["year"] = d.year.values
    by_year = sub.groupby("year").sum()
    words = d.groupby("year").word_count.sum()
    rate = by_year.div(words, axis=0) * 10000
    long = rate.stack().rename("per_10k_words").reset_index().rename(columns={"level_1": "term"})
    long["count"] = by_year.stack().values
    long.to_csv(ROOT / "data" / "term_frequency_year.csv", index=False, float_format="%.3f")
    print(f"{len(top)} terms kept, {len(dropped)} candidate terms dropped as proper nouns")
    print("examples dropped:", dropped[:25])
    print("examples kept:", list(top.index[:40]))


if __name__ == "__main__":
    main()
