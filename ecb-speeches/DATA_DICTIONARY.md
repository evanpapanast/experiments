# Data dictionary: What the ECB says, and what it does

All files in `data/` are totals or counts. None contains speech text, titles or names.

## Speeches

| File | One row per | Main columns |
|---|---|---|
| `speech_topics.csv` | speech (2,657) | `speech_id` (anonymous number, in date order), `date`, `year`, `quarter`, `word_count`, `T01`…`T15` (matching words per subject), `total_hits`, `primary_topic` (subject with most matches), `n_tags` (subjects with enough matches to count) |
| `speech_tags.csv` | speech and subject | `speech_id`, `topic_id`: a subject counts for a speech when it has at least 3 matches and at least 1 per 1,000 words |
| `topic_share_year.csv`, `topic_share_quarter.csv` | period and subject | `share` (matches for the subject ÷ matches for all subjects), `hits`, `hits_per_10k_words`, `n_speeches`, `words` |
| `dim_topic.csv` | subject (15) | `topic_id`, `topic_name`, `description`, `keywords` |
| `term_frequency_year.csv` | year and word | `term` (word or two-word phrase, lower case), `count`, `per_10k_words` |
| `manifest.json` | – | source, download date, SHA-256 fingerprint of the raw file, rows kept and left out, rules used |

## Words vs actions

| File | One row per | Main columns |
|---|---|---|
| `speech_signal_month.csv` | month | `n_speeches`, `words`, `hawkish` (tough phrases), `dovish` (soft phrases), `policy_hits` (inflation + interest-rate matches), `all_hits` |
| `words_vs_actions_month.csv` | month | `tone` (tough − soft) ÷ (tough + soft) over 3 months, `tone_gap` (tone minus its average of the 2 years before), `rate_change`, `policy_rate` (end of month) |
| `policy_rate_decisions.csv` | rate change (63) | `effective_date`, `decision_month` (effective date − 7 days), `instrument` (MRO until May 2014, DFR from June 2014), `policy_rate`, `change`, `direction` (+1 rise, −1 cut), `turning_point`, `cycle` (first hike / first cut) |
| `decision_warnings.csv` | rate change | `tone_gap_before` (average of the 3 months before), `months_right_sign` (0–3), `warned` (at least 2 of 3 months pointed the right way) |
| `turning_point_profile.csv` | type of change and month | average `tone_gap` and `policy_talk` from 12 months before to 6 months after a change of direction |
| `words_vs_actions_results.json` | – | every number shown on the "Words vs actions" page |

## Rules (`playbook/`)

| File | What it is |
|---|---|
| `taxonomy.csv` | the 15 subjects and their words (version 2) |
| `CHANGELOG.md` | what changed between versions and why |
| `tone_lexicon.csv` | tough and soft phrases, fixed before the comparison with interest rates |
| `what_it_means.csv` | the notes on the "Now" page, one for "talked about more" and one for "talked about less" per subject |

## Quality (`data_quality/`)

| File | What it is |
|---|---|
| `manual_review.csv` | 40 speeches checked by hand: `speech_id`, `year`, `playbook_primary`, `verdict` (correct / defensible / wrong), `reviewer_note` (in my own words) |
| `dq_report.md` | result of the 22 automatic checks |
