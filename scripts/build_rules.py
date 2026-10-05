import os
import sys

import duckdb

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.onboarding_rules import RULES, hit_query

DB = "data/processed/onboarding.duckdb"

con = duckdb.connect(DB)
con.sql("DROP TABLE IF EXISTS fact_rule_hit")
parts = [hit_query(rid) for rid in RULES]
con.sql("CREATE TABLE fact_rule_hit AS " + " UNION ALL ".join(parts))

print("rule hits (unweighted, in sample):")
for r in con.sql("SELECT rule_id, COUNT(*) AS hits, COUNT(DISTINCT lei) AS entities FROM fact_rule_hit GROUP BY 1 ORDER BY 1").fetchall():
    print(r)
print("entities with at least one hit:", con.sql("SELECT COUNT(DISTINCT lei) FROM fact_rule_hit").fetchone()[0])
