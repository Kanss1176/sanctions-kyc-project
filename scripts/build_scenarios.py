import os
import sys

import duckdb
import pandas as pd
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.scenarios import run

cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
con = duckdb.connect("data/processed/onboarding.duckdb")
leis = [r[0] for r in con.sql("SELECT lei FROM dim_entity ORDER BY lei").fetchall()]
severe = {r[0] for r in con.sql(
    "SELECT DISTINCT h.lei FROM fact_rule_hit h JOIN dim_rule r ON r.rule_id = h.rule_id WHERE r.severity >= 3"
).fetchall()}

rows, errs = [], []
for s in cfg["scenarios"]:
    df = run(cfg, leis, severe, s["policy"], s["makers"], s["checkers"])
    groups = [("ALL", df)] + [(t, g) for t, g in df.groupby("request_type")]
    for label, g in groups:
        c = g[g.completed]
        rows.append({
            "scenario": s["name"], "policy": s["policy"], "makers": s["makers"], "checkers": s["checkers"],
            "request_type": label, "received": len(g), "completed": len(c),
            "open_requests": len(g) - len(c),
            "median_tat_h": round(float(c.tat_h.median()), 2),
            "p90_tat_h": round(float(c.tat_h.quantile(0.9)), 2),
            "breach_rate": round(float(c.breached.mean()), 4),
        })
    errs.append({
        "scenario": s["name"], "injected": int(df.error.sum()),
        "caught": int(df.detected.sum()), "escaped": int((df.error & ~df.detected).sum()),
    })

res, er = pd.DataFrame(rows), pd.DataFrame(errs)
for name, d in [("scenario_results", res), ("scenario_errors", er)]:
    con.sql("DROP TABLE IF EXISTS " + name)
    con.register("tmp_df", d)
    con.sql("CREATE TABLE " + name + " AS SELECT * FROM tmp_df")
    con.unregister("tmp_df")

cols = ["scenario", "request_type", "completed", "open_requests", "median_tat_h", "p90_tat_h", "breach_rate"]
print(res[cols].to_string(index=False))
print(er.to_string(index=False))
