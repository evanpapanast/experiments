# experiments

End-to-end data projects on public data: source → cloud warehouse → SQL → interactive report.
Each one tests a newer tool or way of working (Google BigQuery, AI-assisted development with Claude,
reports as code) on a question I find interesting.

**Live reports:** [evanpapanast.github.io/experiments](https://evanpapanast.github.io/experiments/)

| Experiment | Question | Data | Stack | Report |
|---|---|---|---|---|
| [AI adoption in EU enterprises](ai-adoption-eu/) | Who uses AI in Europe, for what, and what holds the rest back? | Eurostat `isoc_eb_ai`, `isoc_eb_ain2` | Python, BigQuery, SQL, HTML/SVG | [Open](https://evanpapanast.github.io/experiments/ai-adoption-eu/dashboard/) |
| [What the ECB says, and what it does](ecb-speeches/) | Do ECB speeches predict interest rate decisions, and what is the ECB talking about now? | ECB speeches dataset, ECB statistics (interest rates) | Python, text analysis, HTML/SVG | [Open](https://evanpapanast.github.io/experiments/ecb-speeches/dashboard/) |

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
- **Open, official sources only.** EU data © European Union, reused under Commission Decision 2011/833/EU with the
  source acknowledged. These are independent analyses, not endorsed by the European Commission.

---
[Evangelos Papanastasis](https://evanpapanast.github.io/portfolio/) · BI & FP&A analyst, Vienna
