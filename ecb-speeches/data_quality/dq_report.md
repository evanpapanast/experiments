# Data quality report: What the ECB says, and what it does

Run on committed files. **22 PASS, 0 WARN, 0 FAIL.**

| ID | Area | Rule | Result | Problems | Detail |
|---|---|---|---|---|---|
| Q01 | Privacy | Data files contain only approved columns (no titles, speakers or text) | ✅ PASS | 0 |  |
| Q02 | Copyright | No text cell longer than 160 characters in the data files | ✅ PASS | 0 |  |
| Q03 | Copyright | No text in the report data longer than 700 characters | ✅ PASS | 0 |  |
| Q04 | Privacy | Word-search terms are lower-case words or two-word phrases only | ✅ PASS | 0 |  |
| C01 | Completeness | Every analysed speech is in the speech table (matches the manifest) | ✅ PASS | 0 |  |
| C02 | Completeness | Speech numbers run 1, 2, 3 ... without gaps or repeats | ✅ PASS | 0 |  |
| C03 | Completeness | Every year from 1999 has topic shares | ✅ PASS | 0 |  |
| C04 | Completeness | Monthly signal covers every analysed speech | ✅ PASS | 0 |  |
| V01 | Validity | Speeches have at least 200 words and dates from 1999 on | ✅ PASS | 0 |  |
| V02 | Validity | Topic codes are known (T01 to T15 or NONE) | ✅ PASS | 0 |  |
| V03 | Validity | Counts and shares are never negative | ✅ PASS | 0 |  |
| V04 | Validity | Manual review results are right, acceptable (defensible) or wrong | ✅ PASS | 0 |  |
| K01 | Consistency | Topic shares add up to 100% in every year | ✅ PASS | 0 |  |
| K02 | Consistency | Each speech's total equals the sum of its topic counts | ✅ PASS | 0 |  |
| K03 | Consistency | Each speech's main topic is the topic with the most matches | ✅ PASS | 0 |  |
| K04 | Consistency | Rate decisions are real changes and their direction matches the sign | ✅ PASS | 0 |  |
| K05 | Consistency | Changes of direction match the decision list, and totals match the results | ✅ PASS | 0 |  |
| K06 | Consistency | The report uses the same results as the analysis files | ✅ PASS | 0 |  |
| K07 | Consistency | Now and usual shares on the 'Now' page each add up to 100% | ✅ PASS | 0 |  |
| A01 | Accuracy | At least 80% of hand-checked labels are right or acceptable | ✅ PASS | 0 | 85% right or acceptable, 68% clearly right |
| F01 | Freshness | Latest speech is less than 90 days old (the ECB updates the file monthly) | ✅ PASS | 0 | latest speech 2026-10-30, 9 days ago |
| A02 | Accuracy | Fewer than 2% of speeches get no topic label | ✅ PASS | 0 | 25 speeches without a label |
