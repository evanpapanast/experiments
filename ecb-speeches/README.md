# What the ECB says, and what it does

**[Open the interactive report →](https://evanpapanast.github.io/experiments/ecb-speeches/dashboard/)**

27 years of speeches by the European Central Bank (ECB), turned into numbers. Two questions:

1. **Can the ECB's words tell you what it will do next with interest rates?**
2. **What is the ECB talking about now, and what can that mean for you?**

## What we found

| | |
|---|---|
| **Words vs actions** | Mostly no. Speeches mostly explain decisions already made. But when the ECB starts to sound worried about the economy, a rate cut often follows (53% of cases within 6 months, against 32% normally). Tough talk about inflation usually does not lead to a rate rise (no rise in 27 of 42 such months). Before 6 of 8 changes of direction, the tone gave a hint (luck alone would give about 4). |
| **Now** | In the last 12 months the ECB talked 4 times more than usual about technology and AI, and almost twice as much about payments and the digital euro. It talked about 3 times less about interest rates and bond buying, even in a year with two rate rises. |
| **Over time** | The agenda follows history: crises in 2009–2012, bank supervision in 2013, climate in 2021, inflation in 2022–2024, the digital euro in 2025, AI in 2026. |

This is an analysis of public data. It is not investment advice.

## How it works

```
ECB speeches file ──► Python: clean, label each speech by subject ──┐
                                                                     ├──► totals only ──► interactive report
ECB interest rates ──► Python: one rate line, list of decisions ────┘         │
                                                                               └──► automatic quality checks
```

| Step | What happens | Files |
|---|---|---|
| Rules | 15 subjects and the words that belong to each one, written like a tagging playbook and versioned | `playbook/taxonomy.csv`, `playbook/CHANGELOG.md` |
| Label speeches | Count the words of each subject in every speech; keep only the counts | `scripts/01_tag_speeches.py` |
| Word search | Yearly use of the 3,000 most common words and two-word phrases; people's names removed | `scripts/02_word_frequencies.py` |
| Tone | Count "tough" phrases (prices rising too fast) and "soft" phrases (weak economy) per month. The word lists were fixed **before** looking at interest rates | `playbook/tone_lexicon.csv`, `scripts/03_monthly_signal.py` |
| Words vs actions | Compare tone with 63 rate changes; check against luck and against "same as last time" | `scripts/04_words_vs_actions.py` |
| Report data | Build the numbers and sentences the report shows; nothing typed by hand | `scripts/05_build_report_data.py`, `playbook/what_it_means.csv` |
| Quality gate | 22 checks on privacy, copyright, completeness and consistency; stops on any serious problem | `scripts/06_data_quality.py`, `data_quality/dq_report.md` |

## Quality

- **Hand check:** 40 speeches picked at random were read and their main subject checked: 27 right, 7 acceptable, 6 wrong
  (`data_quality/manual_review.csv`). The rules were improved on a different sample, so the check is fair.
- **Automatic checks:** 22 of 22 pass ([report](data_quality/dq_report.md)). They run on every change in GitHub Actions.
- **Reproducible:** running the scripts from scratch gives byte-for-byte the same data files.

## Privacy and copyright

- **No speech text.** The ECB does not allow copying signed speeches without permission, so only counts and percentages are published. A check (Q02, Q03) fails if long text ever appears.
- **No names.** Speaker names and speech titles are never saved; each speech only has a number. A check (Q01) fails if a name, title or text column appears.
- **Sources named.** Speeches: © European Central Bank, used under the [ECB copyright terms](https://www.ecb.europa.eu/home/disclaimer/html/index.en.html). Interest rates: Source: ECB statistics, reused under the [ESCB statistics reuse policy](https://www.ecb.europa.eu/stats/ecb_statistics/governance_and_quality_framework/html/usage_policy.en.html), used exactly as published. Joining the two official rates into one line is our own step. All other figures are my own calculations. Independent work, not approved by the ECB.

## Run it yourself

The raw files are not in this repository. Download them into a `raw/` folder (it is ignored by Git):

```bash
mkdir -p raw
curl -L -o raw/all_ECB_speeches.csv https://www.ecb.europa.eu/press/key/shared/data/all_ECB_speeches.csv
for r in DFR MRR_FR MRR_MBR; do
  curl -o raw/rate_$r.csv "https://data-api.ecb.europa.eu/service/data/FM/D.U2.EUR.4F.KR.$r.LEV?format=csvdata"
done

pip install -r requirements.txt
cd scripts
python 01_tag_speeches.py    --raw ../raw/all_ECB_speeches.csv
python 02_word_frequencies.py --raw ../raw/all_ECB_speeches.csv
python 03_monthly_signal.py   --raw ../raw/all_ECB_speeches.csv
python 04_words_vs_actions.py --rates-dir ../raw
python 05_build_report_data.py
python 06_data_quality.py
```

Then open `dashboard/index.html` in a browser. See [DATA_DICTIONARY.md](DATA_DICTIONARY.md) for every file and column.

## Sources

- European Central Bank, [Speeches dataset](https://www.ecb.europa.eu/press/key/html/downloads.en.html), speeches up to 30 October 2026.
- European Central Bank, [ECB Data Portal](https://data.ecb.europa.eu/): deposit facility rate and main refinancing operations rate (series `FM.D.U2.EUR.4F.KR.*`).

---
Part of [experiments](../README.md) by [Evangelos Papanastasis](https://evanpapanast.github.io/portfolio/).
