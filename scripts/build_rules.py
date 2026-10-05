import duckdb

DB = "data/processed/onboarding.duckdb"
AS_OF = "2026-10-04 16:00:00"

con = duckdb.connect(DB)
con.sql("DROP TABLE IF EXISTS fact_rule_hit")

RULES = {
    "R01": "e.registration_status NOT IN ('ISSUED','ANNULLED','DUPLICATE')",
    "R02": "e.registration_status = 'ISSUED' AND e.next_renewal_ts < TIMESTAMP '" + AS_OF + "'",
    "R03": "e.entity_status = 'INACTIVE'",
    "R04": "e.legal_country <> e.hq_country",
    "R05": "p.missing_parent_unexplained = 1",
}

parts = []
for rid, cond in RULES.items():
    parts.append(
        "SELECT '" + rid + "' AS rule_id, e.lei, e.registration_status "
        "FROM dim_entity e JOIN fact_parent p ON p.lei = e.lei WHERE " + cond
    )
con.sql("CREATE TABLE fact_rule_hit AS " + " UNION ALL ".join(parts))

print("rule hits (unweighted, in sample):")
for r in con.sql("SELECT rule_id, COUNT(*) AS hits, COUNT(DISTINCT lei) AS entities FROM fact_rule_hit GROUP BY 1 ORDER BY 1").fetchall():
    print(r)
print("entities with at least one hit:", con.sql("SELECT COUNT(DISTINCT lei) FROM fact_rule_hit").fetchone()[0])
