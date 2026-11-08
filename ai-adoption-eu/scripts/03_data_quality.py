"""Data quality gate.

Runs the rule book in sql/04_data_quality_checks.sql locally (the same SQL that runs in
BigQuery), adds file-level lineage checks that only make sense outside the warehouse,
and writes:
  data_quality/dq_report.md   human-readable report (committed, so every change is reviewable)
  dashboard/dq.js             results shown on the report's "About the data" page

Exit code 1 if any FAIL-severity check fails, so it can block a publish (CI gate).

Usage:  python scripts/03_data_quality.py
"""
import datetime as dt
import hashlib
import json
import sys

import pandas as pd

from sqlrun import ROOT, connect_with_data, to_sqlite

LINEAGE_CHECKS = [
    ("L01", "Lineage", "FAIL", "Every raw source row is accounted for: kept + out of scope + not published = raw"),
    ("L02", "Lineage", "FAIL", "Committed data files are byte-identical to the extract (SHA-256 fingerprint)"),
    ("L03", "Lineage", "FAIL", "Figures in the published report reconcile to the warehouse tables"),
]


def sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lineage_failures(manifest: dict, con) -> list[tuple[str, str]]:
    fails = []
    for name, m in manifest["tables"].items():
        lin = m.get("lineage")
        if lin:
            total = lin["kept_rows"] + lin["excluded_out_of_scope"] + lin["excluded_not_published"]
            if total != lin["raw_rows"] or lin["kept_rows"] != lin["written_rows"]:
                fails.append(("L01", f"{name}: {total:,} accounted vs {lin['raw_rows']:,} raw rows"))
        f = ROOT / "data" / f"{name}.csv"
        if not f.exists() or sha256(f) != m["output_sha256"]:
            fails.append(("L02", f"{name}.csv differs from the extract fingerprint"))

    # L03: the report's data file must match a fresh query of the warehouse tables
    js = (ROOT / "dashboard" / "data.js").read_text()
    report = json.loads(js[js.index("=") + 1: js.rindex(";")])
    rep = {(r["geo"], r["year"]): r["v"] for r in report["countries"]}
    wh = pd.read_sql("SELECT geo, year, value FROM fact_ai_by_size "
                     "WHERE indicator = 'E_AI_TANY' AND unit = 'PC_ENT' AND size_class = 'GE10'", con)
    for r in wh.itertuples():
        if abs(rep.get((r.geo, r.year), -1) - r.value) > 1e-9:
            fails.append(("L03", f"report shows {rep.get((r.geo, r.year))} for {r.geo} {r.year}, warehouse has {r.value}"))
    if len(rep) != len(wh):
        fails.append(("L03", f"report has {len(rep)} headline rows, warehouse {len(wh)}"))
    return fails


def main() -> int:
    manifest = json.loads((ROOT / "data" / "manifest.json").read_text())
    con = connect_with_data()
    pd.DataFrame([{"table_name": t, "expected_rows": m["expected_rows"], "expected_value_sum": m["expected_value_sum"],
                   "source_dataset": m["source_dataset"], "source_last_update": m["source_last_update"],
                   "next_expected_update": manifest["next_expected_update"], "output_sha256": m["output_sha256"]}
                  for t, m in manifest["tables"].items() if "source_dataset" in m]
                 ).to_sql("load_control_totals", con, index=False)

    sql = (ROOT / "sql" / "04_data_quality_checks.sql").read_text().replace("'bigquery'", "'local'")
    for stmt in to_sqlite(sql):
        con.execute(stmt)

    results = pd.read_sql("SELECT * FROM dq_results ORDER BY check_id", con)
    failures = pd.read_sql("SELECT * FROM dq_failures ORDER BY check_id, detail", con)

    extra = lineage_failures(manifest, con)
    for cid, dim, sev, text in LINEAGE_CHECKS:
        n = sum(1 for c, _ in extra if c == cid)
        results.loc[len(results)] = [cid, dim, sev, text, n, "PASS" if n == 0 else sev]
    if extra:
        failures = pd.concat([failures, pd.DataFrame(extra, columns=["check_id", "detail"])], ignore_index=True)

    order = ["Completeness", "Uniqueness", "Validity", "Referential integrity", "Consistency",
             "Plausibility", "Accuracy", "Timeliness", "Lineage"]
    results["o"] = results.dimension.map(order.index)
    results = results.sort_values(["o", "check_id"]).drop(columns="o").reset_index(drop=True)

    run_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    counts = results.status.value_counts().to_dict()
    n_fail, n_warn, n_pass = counts.get("FAIL", 0), counts.get("WARN", 0), counts.get("PASS", 0)

    # Markdown report
    out = ROOT / "data_quality"
    out.mkdir(exist_ok=True)
    icon = {"PASS": "✅ PASS", "WARN": "⚠️ WARN", "FAIL": "❌ FAIL"}
    lines = [
        "# Data quality report: AI adoption in EU enterprises", "",
        f"Run: {run_at} · Source extract: {manifest['extracted_at']} · "
        f"Eurostat last update: {next(iter(manifest['tables'].values()))['source_last_update']}", "",
        f"**{n_pass} passed · {n_warn} warnings · {n_fail} failed** out of {len(results)} checks.", "",
        "| Check | Dimension | Rule | Result | Records |", "|---|---|---|---|---:|",
        *[f"| {r.check_id} | {r.dimension} | {r.rule_text} | {icon[r.status]} | {r.failed_rows} |" for r in results.itertuples()],
        "", "## Findings to review", "",
    ]
    if failures.empty:
        lines.append("None.")
    for cid, grp in failures.groupby("check_id", sort=True):
        lines.append(f"**{cid}** ({len(grp)} record{'s' if len(grp) != 1 else ''})")
        lines += [f"- {d}" for d in grp.detail.head(15)]
        if len(grp) > 15:
            lines.append(f"- … and {len(grp) - 15} more")
        lines.append("")
    lines += ["## Lineage", "", "| Table | Raw rows | Kept | Out of scope | Not published (of which confidential) | Source SHA-256 |",
              "|---|---:|---:|---:|---:|---|"]
    for t, m in manifest["tables"].items():
        if "lineage" in m:
            l = m["lineage"]
            lines.append(f"| {t} | {l['raw_rows']:,} | {l['kept_rows']:,} | {l['excluded_out_of_scope']:,} | "
                         f"{l['excluded_not_published']:,} ({l['of_which_confidential']:,}) | `{m['source_sha256'][:16]}…` |")
    (out / "dq_report.md").write_text("\n".join(lines) + "\n")

    # Data for the report page
    payload = {"run_at": run_at, "pass": n_pass, "warn": n_warn, "fail": n_fail,
               "results": results.to_dict(orient="records"),
               "findings": failures.groupby("check_id").detail.apply(lambda s: s.head(6).tolist()).to_dict(),
               "lineage": {t: m["lineage"] for t, m in manifest["tables"].items() if "lineage" in m}}
    (ROOT / "dashboard" / "dq.js").write_text("window.DQ_RESULTS = " + json.dumps(payload, ensure_ascii=False) + ";\n")

    print(results[["check_id", "dimension", "status", "failed_rows"]].to_string(index=False))
    print(f"\n{n_pass} PASS, {n_warn} WARN, {n_fail} FAIL  ->  data_quality/dq_report.md")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
