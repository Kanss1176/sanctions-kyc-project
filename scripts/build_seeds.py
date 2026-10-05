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

N = 20
wanted = ["fifo_5_3", "fifo_4_2", "priority_4_2"]
rows = []
for s in cfg["scenarios"]:
    if s["name"] not in wanted:
        continue
    for k in range(N):
        c = dict(cfg)
        c["seed"] = cfg["seed"] + k
        df = run(c, leis, severe, s["policy"], s["makers"], s["checkers"])
        d = df[df.completed]
        rows.append({
            "scenario": s["name"], "seed": c["seed"],
            "completed": len(d), "open_requests": len(df) - len(d),
            "median_tat_h": float(d.tat_h.median()),
            "breach_rate": float(d.breached.mean()),
        })

res = pd.DataFrame(rows)
con.sql("DROP TABLE IF EXISTS scenario_seeds")
con.register("tmp_df", res)
con.sql("CREATE TABLE scenario_seeds AS SELECT * FROM tmp_df")
con.unregister("tmp_df")

g = res.groupby("scenario")
print(g.agg(
    seeds=("seed", "count"),
    breach_mean=("breach_rate", "mean"), breach_min=("breach_rate", "min"), breach_max=("breach_rate", "max"),
    open_mean=("open_requests", "mean"), median_tat_mean=("median_tat_h", "mean"),
).round(3).to_string())

a = res[res.scenario == "fifo_4_2"].sort_values("seed").breach_rate.values
b = res[res.scenario == "priority_4_2"].sort_values("seed").breach_rate.values
diff = b - a
print("priority minus fifo breach rate at 4/2, per seed: mean %.4f, min %.4f, max %.4f" % (diff.mean(), diff.min(), diff.max()))
print("seeds where priority had fewer breaches:", int((diff < 0).sum()), "of", len(diff))
