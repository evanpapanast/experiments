"""Shared helper: run the BigQuery SQL files locally on SQLite.

The SQL in sql/ is written in a portable subset of GoogleSQL. To run it locally we only
strip the `project.dataset.` prefix and turn CREATE OR REPLACE VIEW into DROP + CREATE.
"""
import pathlib
import re
import sqlite3

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
PREFIX = "`project-57338774-2b06-4ac1-ba9.ai_adoption."


def to_sqlite(sql: str) -> list[str]:
    sql = re.sub(r"--[^\n]*", "", sql)
    sql = re.sub(re.escape(PREFIX) + r"(\w+)`", r"\1", sql)
    out = []
    for s in (s.strip() for s in sql.split(";")):
        if not s:
            continue
        m = re.match(r"CREATE OR REPLACE VIEW (\w+)", s)
        if m:
            out.append(f"DROP VIEW IF EXISTS {m.group(1)}")
            s = s.replace("CREATE OR REPLACE VIEW", "CREATE VIEW", 1)
        out.append(s)
    return out


def connect_with_data() -> sqlite3.Connection:
    """In-memory warehouse with every CSV in data/ loaded as a table."""
    con = sqlite3.connect(":memory:")
    for f in sorted((ROOT / "data").glob("*.csv")):
        pd.read_csv(f, keep_default_na=False, na_values=[""]).to_sql(f.stem, con, index=False)
    return con


def run_file(con: sqlite3.Connection, name: str) -> None:
    for stmt in to_sqlite((ROOT / "sql" / name).read_text()):
        con.execute(stmt)
