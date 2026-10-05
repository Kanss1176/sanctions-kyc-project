import os
import sys

import duckdb
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.workflow_v2 import simulate_queue as simulate

cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
con = duckdb.connect("data/processed/onboarding.duckdb")
leis = [r[0] for r in con.sql("SELECT lei FROM dim_entity ORDER BY lei").fetchall()]
severe = {r[0] for r in con.sql(
    "SELECT DISTINCT h.lei FROM fact_rule_hit h JOIN dim_rule r ON r.rule_id = h.rule_id WHERE r.severity >= 3"
).fetchall()}
out = simulate(cfg, leis, severe)
for name, df in out.items():
    con.sql("DROP TABLE IF EXISTS " + name)
    con.register("tmp_df", df)
    con.sql("CREATE TABLE " + name + " AS SELECT * FROM tmp_df")
    con.unregister("tmp_df")
    print(name, len(df))

print("requests, completed, open:", con.sql(
    "SELECT COUNT(*), SUM((status='Completed')::INT), SUM((status='Open')::INT) FROM fact_request").fetchall())
print("median TAT h, P90 TAT h, SLA breach rate, first-time-right (completed only):", con.sql(
    "SELECT ROUND(MEDIAN(tat_hours),2), ROUND(quantile_cont(tat_hours,0.9),2), "
    "ROUND(AVG(sla_breached::INT),3), ROUND(AVG(first_time_right::INT),3) "
    "FROM fact_request WHERE status='Completed'").fetchall())
print("injected errors, caught by checker:", con.sql(
    "SELECT COUNT(*), SUM(detected_by_checker::INT) FROM sim_error_truth").fetchall())
