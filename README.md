# experiments

End-to-end data projects on public data: source → cloud warehouse → SQL → interactive report.
Each one tests a newer tool or way of working (Google BigQuery, AI-assisted development with Claude,
reports as code) on a question I find interesting.

**Live reports:** [evanpapanast.github.io/experiments](https://evanpapanast.github.io/experiments/)

| Experiment | Question | Data | Stack | Report |
|---|---|---|---|---|
| [AI adoption in EU enterprises](ai-adoption-eu/) | Who uses AI in Europe, for what, and what holds the rest back? | Eurostat `isoc_eb_ai`, `isoc_eb_ain2` | Python, BigQuery, SQL, HTML/SVG | [Open](https://evanpapanast.github.io/experiments/ai-adoption-eu/dashboard/) |
| [What the ECB says, and what it does](ecb-speeches/) | Do ECB speeches predict interest rate decisions, and what is the ECB talking about now? | ECB speeches dataset, ECB statistics (interest rates) | Python, text analysis, HTML/SVG | [Open](https://evanpapanast.github.io/experiments/ecb-speeches/dashboard/) |
| [Iowa spirits market: price, volume, forecast and budget](liquor-market/) | Is growth coming from price or volume, how good was the budget, and what should we plan for next year? | Iowa Liquor Sales (CC BY 4.0) via BigQuery public datasets | BigQuery, SQL, AI.FORECAST, Python, HTML/SVG | [Open](https://evanpapanast.github.io/experiments/liquor-market/dashboard/) |
| [Automated monthly close (concept)](monthly-close/) | Can a governed month-end close run by itself, with checks a person can audit? | Iowa Liquor Sales (CC BY 4.0) via BigQuery public datasets | BigQuery, SQL, AI.FORECAST, Python, GitHub Actions, HTML/SVG | [Open](https://evanpapanast.github.io/experiments/monthly-close/dashboard/) |

## Conventions

Every experiment folder follows the same layout:

```
<experiment>/
├── README.md        question, key findings, pipeline, how to rerun
├── scripts/         Python: extract, transform, build report data
├── sql/             BigQuery DDL, loads, reporting views (when a warehouse is used)
├── data/            tidy, small CSVs (raw downloads are not committed)
└── dashboard/       self-contained interactive report (opens in any browser)
```

Cost: all work runs on BigQuery's free tier; nothing here requires a paid account.

## Data protection and reuse

- **No personal data.** Experiments publish aggregated figures only: no names and no personal data (GDPR data minimisation and privacy by design).
- **Open, official sources only, used under their licences:**
  - EU data © European Union, reused under Commission Decision 2011/833/EU with the source acknowledged.
  - ECB speeches and statistics, reused under the ECB copyright terms and the ESCB statistics reuse policy; no speech text is reproduced.
  - Iowa Liquor Sales © State of Iowa (Iowa Department of Revenue), reused under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) with the source credited.
- These are independent analyses, not endorsed by any of the publishers.

---
[Evangelos Papanastasis](https://evanpapanast.github.io/portfolio/) · BI & FP&A analyst, Vienna
