"""Run sql/02_marts.sql locally (SQLite) on the CSVs in data/ and export the
dashboard dataset to dashboard/data.js (loaded by dashboard/index.html).

The same SQL file is deployed to BigQuery unchanged; this script only strips the
`project.dataset.` prefix so SQLite can run it. That keeps one source of truth
for the business logic.

Usage:  python scripts/02_build_marts.py
"""
import json

import pandas as pd

from sqlrun import ROOT, connect_with_data, run_file


def main() -> None:
    con = connect_with_data()
    run_file(con, "02_marts.sql")

    def q(sql: str) -> list[dict]:
        df = pd.read_sql(sql, con)
        return json.loads(df.to_json(orient="records"))

    data = {
        "source": "Eurostat, ICT usage and e-commerce in enterprises (isoc_eb_ai, isoc_eb_ain2)",
        "built": pd.Timestamp.today().strftime("%Y-%m-%d"),
        "countries": q("SELECT geo, country, is_eu_member, year, pct_enterprises_using_ai AS v, flag, "
                       "eu_rank, change_pp_vs_previous AS chg FROM mart_country_adoption ORDER BY geo, year"),
        "size": q("SELECT geo, year, pct_small AS s, pct_medium AS m, pct_large AS l, gap_large_vs_small_pp AS gap "
                  "FROM mart_size_gap ORDER BY geo, year"),
        "profile": q("SELECT geo, year, indicator_group AS grp, short_label AS label, unit, value AS v "
                     "FROM mart_ai_profile ORDER BY geo, year"),
        "sectors": q("SELECT geo, year, sector, value AS v, flag FROM mart_sector_adoption "
                     "WHERE indicator = 'E_AI_TANY' ORDER BY geo, year"),
    }
    out = ROOT / "dashboard" / "data.js"
    out.parent.mkdir(exist_ok=True)
    out.write_text("window.AI_DATA = " + json.dumps(data, separators=(",", ":"), ensure_ascii=False) + ";\n")
    print(f"{out.relative_to(ROOT)}  {out.stat().st_size / 1e3:.0f} KB  " +
          ", ".join(f"{k}={len(v)}" for k, v in data.items() if isinstance(v, list)))



if __name__ == "__main__":
    main()
