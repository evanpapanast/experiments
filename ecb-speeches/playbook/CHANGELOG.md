# Playbook changelog

## v2 (8 November 2026)
Changes after reviewing a random sample of 40 speeches (seed 7) against the v1 tags:
- **T10 Climate:** removed `sustainable` and `sustainability`. They are mostly used generically ("sustainable growth",
  "debt sustainability") and tagged unrelated speeches as climate. Added `sustainable finance`, `climate-related`.
- **T04 Banking supervision:** added `bank capital`, `banking sector`; banking-resilience speeches were drifting to T05.
- **T15 Statistics & data (new):** speeches on euro area statistics had no home and were mis-tagged as supervision
  or communication.

Accuracy is measured on a **second, fresh** random sample (seed 11), not on the sample used to tune v2.

## v1 (8 November 2026)
First version: 14 topics, keyword rules, longest phrase counted first.
