import duckdb
import yaml

cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
con = duckdb.connect("data/processed/onboarding.duckdb")
con.sql("DROP TABLE IF EXISTS sim_clock")
con.sql("CREATE TABLE sim_clock AS SELECT MAX(received_ts) AS last_arrival_ts FROM fact_request")
# The as-of time is the end of the last business day in the request window.
con.sql("""
CREATE OR REPLACE TABLE sim_clock AS
SELECT (CAST(MAX(received_ts) AS DATE) + INTERVAL 18 HOUR) AS asof_ts FROM fact_request
""")
print("sim_clock:", con.sql("SELECT * FROM sim_clock").fetchall())
