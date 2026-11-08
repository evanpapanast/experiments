"""Download Eurostat AI-adoption datasets and turn them into tidy, labelled CSVs.

Sources (Eurostat, ICT usage in enterprises survey, enterprises with 10+ employees):
  - isoc_eb_ai   : Artificial intelligence by size class of enterprise
  - isoc_eb_ain2 : Artificial intelligence by NACE Rev. 2 activity

Usage:  python scripts/01_extract_transform.py [--raw-dir RAW] [--out-dir data]
"""
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import urllib.request

import pandas as pd

API = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1"
DATASETS = ["isoc_eb_ai", "isoc_eb_ain2"]
CODELISTS = ["INDIC_IS", "GEO", "NACE_R2", "SIZE_EMP"]

# AI technologies, purposes and barriers kept for the dashboard (short labels for charts)
INDICATORS = {
    "E_AI_TANY": ("Uses any AI technology", "headline"),
    "E_AI_TTM": ("Text mining", "technology"),
    "E_AI_TSR": ("Speech recognition", "technology"),
    "E_AI_TNLG": ("Generating text, speech or code", "technology"),
    "E_AI_TIR": ("Image recognition", "technology"),
    "E_AI_TML": ("Machine learning for data analysis", "technology"),
    "E_AI_TPA": ("Workflow automation / decision support", "technology"),
    "E_AI_TAR": ("Autonomous machines / robots", "technology"),
    "E_AI_TPVSG": ("Generating images, video or audio", "technology"),
    "E_AI_PMS": ("Marketing or sales", "purpose"),
    "E_AI_PPP": ("Production processes", "purpose"),
    "E_AI_PBA": ("Business administration", "purpose"),
    "E_AI_PME": ("Management of the enterprise", "purpose"),
    "E_AI_PLOG": ("Logistics", "purpose"),
    "E_AI_PITS": ("ICT security", "purpose"),
    "E_AI_PFIN": ("Accounting, controlling or finance", "purpose"),
    "E_AI_PRDI": ("R&D or innovation", "purpose"),
    "E_AI_PHR": ("HR or recruiting", "purpose"),
    "E_AI_BLE": ("Lack of expertise", "barrier"),
    "E_AI_BLEG": ("Unclear legal consequences", "barrier"),
    "E_AI_BCDP": ("Data protection / privacy concerns", "barrier"),
    "E_AI_BDDT": ("Data availability or quality", "barrier"),
    "E_AI_BCST": ("Costs seem too high", "barrier"),
    "E_AI_BINC": ("Incompatible with existing systems", "barrier"),
    "E_AI_BEC": ("Ethical considerations", "barrier"),
    "E_AI_BNU": ("AI not useful for the business", "barrier"),
    "E_AI_ARDY": ("Ready-to-use commercial software", "sourcing"),
    "E_AI_AMOWN": ("Commercial software modified in-house", "sourcing"),
    "E_AI_AOS": ("Open-source modified in-house", "sourcing"),
    "E_AI_ADOWN": ("Developed by own employees", "sourcing"),
    "E_AI_AEXT": ("Developed by external providers", "sourcing"),
}
# unit: PC_ENT = % of all enterprises; PC_ENT_AI_TANY = % of AI users; PC_ENT_AI_EC = % of those who considered AI
UNITS = ["PC_ENT", "PC_ENT_AI_TANY", "PC_ENT_AI_EC"]
# Eurostat's announced next release of this survey (Statistics Explained: "planned article update December 2026")
NEXT_EXPECTED_UPDATE = "2026-12-31"
BQ = "`project-57338774-2b06-4ac1-ba9.ai_adoption"


def download(url: str, path: pathlib.Path) -> None:
    if not path.exists():
        urllib.request.urlretrieve(url, path)


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def lineage(raw_df: pd.DataFrame, in_scope: pd.Series, out_rows: int) -> dict:
    """Row-level reconciliation: every raw row is either kept, out of scope, or not published."""
    published = raw_df.OBS_VALUE.notna()
    return {
        "raw_rows": int(len(raw_df)),
        "kept_rows": int((in_scope & published).sum()),
        "excluded_out_of_scope": int((~in_scope).sum()),
        "excluded_not_published": int((in_scope & ~published).sum()),
        "of_which_confidential": int((in_scope & ~published & (raw_df.CONF_STATUS == "C")).sum()),
        "written_rows": out_rows,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", default="raw")
    ap.add_argument("--out-dir", default="data")
    a = ap.parse_args()
    raw, out = pathlib.Path(a.raw_dir), pathlib.Path(a.out_dir)
    raw.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)

    for d in DATASETS:
        download(f"{API}/data/{d}?format=SDMX-CSV&compressed=false", raw / f"{d}.csv")
    for c in CODELISTS:
        download(f"{API}/codelist/ESTAT/{c}?format=TSV&lang=en", raw / f"{c}.tsv")

    cols = {"geo": "geo", "TIME_PERIOD": "year", "indic_is": "indicator",
            "unit": "unit", "OBS_VALUE": "value", "OBS_FLAG": "flag"}

    # Fact 1: by size class (all countries, all years)
    ai_raw = pd.read_csv(raw / "isoc_eb_ai.csv")
    ai_scope = ai_raw.indic_is.isin(INDICATORS) & ai_raw.unit.isin(UNITS)
    ai = ai_raw[ai_scope & ai_raw.OBS_VALUE.notna()]
    ai = ai.rename(columns={**cols, "size_emp": "size_class"})
    ai[["geo", "year", "size_class", "indicator", "unit", "value", "flag"]] \
        .sort_values(["indicator", "geo", "year", "size_class"]) \
        .to_csv(out / "fact_ai_by_size.csv", index=False)

    # Fact 2: by economic activity (enterprises with 10+ employees)
    n2_raw = pd.read_csv(raw / "isoc_eb_ain2.csv")
    keep = [k for k, (_, g) in INDICATORS.items() if g in ("headline", "technology")]
    n2_scope = (n2_raw.unit == "PC_ENT") & n2_raw.indic_is.isin(keep) & (n2_raw.size_emp == "GE10")
    n2 = n2_raw[n2_scope & n2_raw.OBS_VALUE.notna()]
    n2 = n2.rename(columns={**cols, "nace_r2": "nace"})
    n2[["geo", "year", "nace", "indicator", "value", "flag"]] \
        .sort_values(["indicator", "geo", "year", "nace"]) \
        .to_csv(out / "fact_ai_by_sector.csv", index=False)

    # Dimensions
    def codelist(name, used, key):
        cl = pd.read_csv(raw / f"{name}.tsv", sep="\t", header=None, names=[key, "label"])
        return cl[cl[key].isin(used)]

    ind = codelist("INDIC_IS", INDICATORS, "indicator")
    ind["short_label"] = ind.indicator.map(lambda k: INDICATORS[k][0])
    ind["indicator_group"] = ind.indicator.map(lambda k: INDICATORS[k][1])
    ind.to_csv(out / "dim_indicator.csv", index=False)
    codelist("GEO", set(ai.geo) | set(n2.geo), "geo").to_csv(out / "dim_geo.csv", index=False)
    codelist("NACE_R2", set(n2.nace), "nace").to_csv(out / "dim_sector.csv", index=False)
    codelist("SIZE_EMP", set(ai.size_class), "size_class").to_csv(out / "dim_size_class.csv", index=False)

    # Lineage manifest: provenance, fingerprints and control totals for every output table
    def last_update(df):  # Eurostat stamps each row with "dd/mm/yy hh:mm:ss"
        return dt.datetime.strptime(df["LAST UPDATE"].max(), "%d/%m/%y %H:%M:%S").date().isoformat()

    manifest = {
        "extracted_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "source": "Eurostat dissemination API (SDMX 2.1)",
        "licence": "Eurostat: free re-use with attribution (Commission Decision 2011/833/EU)",
        "next_expected_update": NEXT_EXPECTED_UPDATE,
        "tables": {},
    }
    for name, raw_df, scope, df, dataset in [
        ("fact_ai_by_size", ai_raw, ai_scope, ai, "isoc_eb_ai"),
        ("fact_ai_by_sector", n2_raw, n2_scope, n2, "isoc_eb_ain2"),
    ]:
        f = out / f"{name}.csv"
        manifest["tables"][name] = {
            "source_dataset": dataset,
            "source_url": f"{API}/data/{dataset}?format=SDMX-CSV&compressed=false",
            "source_last_update": last_update(raw_df),
            "source_sha256": sha256(raw / f"{dataset}.csv"),
            "output_sha256": sha256(f),
            "expected_rows": int(len(df)),
            "expected_value_sum": round(float(df.value.sum()), 2),
            "lineage": lineage(raw_df, scope, len(df)),
        }
    for f in sorted(out.glob("dim_*.csv")):
        manifest["tables"][f.stem] = {"output_sha256": sha256(f), "expected_rows": sum(1 for _ in open(f)) - 1}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    # Control totals for BigQuery (sql/03_load_control_totals.sql), generated from the manifest
    sql_dir = pathlib.Path(__file__).resolve().parents[1] / "sql"
    rows = ",\n  ".join(
        f"('{t}', {m['expected_rows']}, {m['expected_value_sum']}, '{m['source_dataset']}', "
        f"DATE '{m['source_last_update']}', DATE '{NEXT_EXPECTED_UPDATE}', '{m['output_sha256']}')"
        for t, m in manifest["tables"].items() if "source_dataset" in m)
    (sql_dir / "03_load_control_totals.sql").write_text(
        "-- Control totals for the load, generated by scripts/01_extract_transform.py from data/manifest.json.\n"
        "-- The data quality checks (04) compare what is in BigQuery against these numbers.\n"
        f"CREATE OR REPLACE TABLE {BQ}.load_control_totals` AS\n"
        "SELECT * FROM UNNEST(ARRAY<STRUCT<table_name STRING, expected_rows INT64, expected_value_sum FLOAT64,\n"
        "  source_dataset STRING, source_last_update DATE, next_expected_update DATE, output_sha256 STRING>>[\n"
        f"  {rows}]);\n")

    for f in sorted(out.glob("*.csv")):
        print(f"{f.name:28s} {sum(1 for _ in open(f)) - 1:>7,} rows  {f.stat().st_size/1e6:5.2f} MB")
    for t, m in manifest["tables"].items():
        if "lineage" in m:
            print(t, m["lineage"])


if __name__ == "__main__":
    main()
