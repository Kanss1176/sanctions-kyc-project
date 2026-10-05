import duckdb

con = duckdb.connect("data/processed/onboarding.duckdb", read_only=True)
rows = con.sql(
    "SELECT lei, registration_status, initial_reg_ts, next_renewal_ts, last_update_ts "
    "FROM dim_entity WHERE next_renewal_ts < initial_reg_ts"
).fetchall()
for r in rows:
    print(r)
print("rows:", len(rows))