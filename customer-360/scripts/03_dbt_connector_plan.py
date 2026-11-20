"""Turn the compiled dbt project into run-ready BigQuery SQL, for environments without Google credentials.

Why: this experiment is run by Claude through the BigQuery connector, which has no local Google login.
dbt compiles the project offline (target "offline"); this script then
  1. wraps each compiled model in the same CREATE OR REPLACE TABLE ... AS statement that dbt's
     table materialisation would run, in dependency order, with the project's labels;
  2. combines every compiled dbt test into one query that returns the number of failing rows per test
     (one query instead of 42 keeps the bytes billed low: BigQuery bills at least 10 MB per table per query).
With your own Google login, `dbt build` runs the same project directly and this script is not needed.

Usage (from customer-360/dbt):
  DBT_PROFILES_DIR=. dbt compile --target offline --no-populate-cache --no-introspect
  python ../scripts/03_dbt_connector_plan.py
Writes target/connector/run_models.sql, target/connector/run_tests.sql and target/connector/plan.json.
"""
import json
from graphlib import TopologicalSorter
from pathlib import Path

DBT = Path(__file__).resolve().parent.parent / "dbt"
OUT = DBT / "target" / "connector"


def main():
    m = json.loads((DBT / "target" / "manifest.json").read_text(encoding="utf-8"))
    models = {k: v for k, v in m["nodes"].items() if v["resource_type"] == "model"}
    graph = {k: [d for d in v["depends_on"]["nodes"] if d in models] for k, v in models.items()}
    # Stable order: layer by layer (all dependencies first), alphabetical within a layer.
    ts = TopologicalSorter(graph)
    ts.prepare()
    order = []
    while ts.is_active():
        ready = sorted(ts.get_ready(), key=lambda k: models[k]["name"])
        order += ready
        ts.done(*ready)

    OUT.mkdir(parents=True, exist_ok=True)
    stmts, plan = [], []
    for uid in order:
        n = models[uid]
        sql = (DBT / n["compiled_path"]).read_text(encoding="utf-8").strip().rstrip(";")
        labels = n["config"].get("labels", {})
        opts = ", ".join([f"labels=[{', '.join(repr((k, v)).replace(chr(39), chr(34)) for k, v in labels.items())}]"] if labels else [])
        desc = (n.get("description") or "").replace('"', "'")
        if desc:
            opts = (opts + ", " if opts else "") + f'description="{desc}"'
        target = f"`{n['database']}.{n['schema']}.{n['alias']}`"
        stmts.append(f"-- {n['name']}\nCREATE OR REPLACE TABLE {target}\nOPTIONS ({opts})\nAS\n{sql};")
        plan.append({"model": n["name"], "layer": n["fqn"][1], "table": target.strip("`"),
                     "depends_on": [models[d]["name"] for d in graph[uid]]})

    tests = [v for v in m["nodes"].values() if v["resource_type"] == "test"]
    parts = []
    for t in sorted(tests, key=lambda t: t["name"]):
        sql = (DBT / t["compiled_path"]).read_text(encoding="utf-8").strip().rstrip(";")
        parts.append(f"select '{t['name']}' as test_name, (select count(*) from (\n{sql}\n)) as failures")
    schema = f"{plan[0]['table'].rsplit('.', 1)[0]}"
    (OUT / "run_models.sql").write_text(f"CREATE SCHEMA IF NOT EXISTS `{schema}` OPTIONS (location = 'US');\n\n" + "\n\n".join(stmts) + "\n", encoding="utf-8")
    (OUT / "run_tests.sql").write_text("\nunion all\n".join(parts) + "\norder by failures desc, test_name\n", encoding="utf-8")
    (OUT / "plan.json").write_text(json.dumps({"models": plan, "tests": len(parts)}, indent=2), encoding="utf-8")
    print(f"{len(plan)} models in order: " + " -> ".join(p["model"] for p in plan))
    print(f"{len(parts)} tests combined into one query")


if __name__ == "__main__":
    main()
