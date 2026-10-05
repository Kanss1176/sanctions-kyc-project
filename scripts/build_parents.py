import glob
import duckdb

DB = "data/processed/onboarding.duckdb"
rr = glob.glob("data/raw/*rr-golden-copy*.csv")[0].replace("\\", "/")
rx = glob.glob("data/raw/*repex-golden-copy*.csv")[0].replace("\\", "/")

con = duckdb.connect(DB)

con.sql("DROP TABLE IF EXISTS fact_parent")
con.sql("DROP TABLE IF EXISTS dq_parent_summary")

con.sql("""
CREATE TEMP TABLE rel AS
SELECT
  "Relationship.StartNode.NodeID" AS child_lei,
  "Relationship.EndNode.NodeID" AS parent_lei,
  "Relationship.RelationshipType" AS rel_type,
  "Relationship.RelationshipStatus" AS rel_status
FROM read_csv_auto('""" + rr + """', sample_size=-1)
WHERE "Relationship.StartNode.NodeID" IN (SELECT lei FROM dim_entity)
""")

con.sql("""
CREATE TEMP TABLE rx AS
SELECT "LEI" AS lei,
       "Exception.Category" AS exc_category,
       "Exception.Reason.1" AS exc_reason
FROM read_csv_auto('""" + rx + """', sample_size=-1)
WHERE "LEI" IN (SELECT lei FROM dim_entity)
""")

con.sql("""
CREATE TABLE fact_parent AS
SELECT
  e.lei,
  e.registration_status,
  d.parent_lei AS direct_parent_lei,
  u.parent_lei AS ultimate_parent_lei,
  CASE WHEN d.parent_lei IS NOT NULL THEN 1 ELSE 0 END AS has_direct_parent,
  CASE WHEN u.parent_lei IS NOT NULL THEN 1 ELSE 0 END AS has_ultimate_parent,
  (SELECT string_agg(DISTINCT exc_category || ':' || COALESCE(exc_reason, ''), '; ')
     FROM rx WHERE rx.lei = e.lei) AS exception_info,
  CASE WHEN d.parent_lei IS NULL AND u.parent_lei IS NULL
       AND EXISTS (SELECT 1 FROM rx WHERE rx.lei = e.lei) THEN 1 ELSE 0 END AS missing_parent_explained,
  CASE WHEN d.parent_lei IS NULL AND u.parent_lei IS NULL
       AND NOT EXISTS (SELECT 1 FROM rx WHERE rx.lei = e.lei) THEN 1 ELSE 0 END AS missing_parent_unexplained
FROM dim_entity e
LEFT JOIN (SELECT child_lei, ANY_VALUE(parent_lei) AS parent_lei FROM rel
           WHERE rel_type = 'IS_DIRECTLY_CONSOLIDATED_BY' AND rel_status = 'ACTIVE'
           GROUP BY child_lei) d ON d.child_lei = e.lei
LEFT JOIN (SELECT child_lei, ANY_VALUE(parent_lei) AS parent_lei FROM rel
           WHERE rel_type = 'IS_ULTIMATELY_CONSOLIDATED_BY' AND rel_status = 'ACTIVE'
           GROUP BY child_lei) u ON u.child_lei = e.lei
""")

print("fact_parent rows:", con.sql("SELECT COUNT(*) FROM fact_parent").fetchone()[0])
print("\nstatus counts for sampled children in relationship file:")
for r in con.sql("SELECT rel_type, rel_status, COUNT(*) FROM rel GROUP BY 1,2 ORDER BY 3 DESC").fetchall():
    print(r)
print("\nsummary (unweighted, in sample):")
print(con.sql("""SELECT COUNT(*) AS n,
  SUM(has_direct_parent) AS with_direct,
  SUM(has_ultimate_parent) AS with_ultimate,
  SUM(missing_parent_explained) AS missing_explained,
  SUM(missing_parent_unexplained) AS missing_unexplained
  FROM fact_parent""").fetchall())
print("\nexception categories in sample:")
for r in con.sql("SELECT exc_category, exc_reason, COUNT(*) FROM rx GROUP BY 1,2 ORDER BY 3 DESC LIMIT 10").fetchall():
    print(r)
print("\nmulti-parent check (children with >1 active direct parent):")
print(con.sql("""SELECT COUNT(*) FROM (SELECT child_lei FROM rel
  WHERE rel_type='IS_DIRECTLY_CONSOLIDATED_BY' AND rel_status='ACTIVE'
  GROUP BY 1 HAVING COUNT(*) > 1)""").fetchone()[0])