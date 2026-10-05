import csv
import os
import duckdb

P = "data/processed/gleif_lei_slim.parquet"
T = "read_parquet('" + P + "')"
os.makedirs("docs", exist_ok=True)

con = duckdb.connect()
cols = [r[0] for r in con.sql("DESCRIBE SELECT * FROM " + T).fetchall()]
total = con.sql("SELECT COUNT(*) FROM " + T).fetchone()[0]
print("rows:", total)
print("columns:", len(cols))

# 1. Fill rate for every column
counts_sql = ", ".join('COUNT("' + c + '")' for c in cols)
counts = con.sql("SELECT " + counts_sql + " FROM " + T).fetchone()
with open("docs/gleif_profile_fill_rate.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["column", "non_null_rows", "fill_pct"])
    for c, n in zip(cols, counts):
        pct = round(100.0 * n / total, 2)
        w.writerow([c, n, pct])
        print(c.ljust(60), str(pct) + "%")


def save(name, sql, needs):
    missing = [c for c in needs if c not in cols]
    if missing:
        print("\n==", name, ": SKIPPED, missing columns:", missing)
        return
    res = con.sql(sql)
    header = res.columns
    rows = res.fetchall()
    with open("docs/gleif_profile_" + name + ".csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print("\n==", name)
    print(header)
    for r in rows[:25]:
        print(r)


REG = "Registration.RegistrationStatus"
ENT = "Entity.EntityStatus"
CAT = "Entity.EntityCategory"
CTRY = "Entity.LegalAddress.Country"
REN = "Registration.NextRenewalDate"

save("registration_status",
     'SELECT "' + REG + '" AS reg_status, COUNT(*) AS n FROM ' + T + ' GROUP BY 1 ORDER BY n DESC',
     [REG])

save("entity_status",
     'SELECT "' + ENT + '" AS entity_status, COUNT(*) AS n FROM ' + T + ' GROUP BY 1 ORDER BY n DESC',
     [ENT])

save("category",
     'SELECT "' + CAT + '" AS category, COUNT(*) AS n FROM ' + T + ' GROUP BY 1 ORDER BY n DESC',
     [CAT])

save("country_top25",
     'SELECT "' + CTRY + '" AS country, COUNT(*) AS n FROM ' + T + ' GROUP BY 1 ORDER BY n DESC LIMIT 25',
     [CTRY])

renewal_sql = (
    'SELECT "' + REG + '" AS reg_status, COUNT(*) AS n, '
    'COUNT(*) FILTER (WHERE TRY_CAST(LEFT("' + REN + '", 19) AS TIMESTAMP) '
    "< TIMESTAMP '2026-10-04 16:00:00') AS renewal_date_passed, "
    'COUNT(*) FILTER (WHERE "' + REN + '" IS NULL) AS no_renewal_date '
    'FROM ' + T + ' GROUP BY 1 ORDER BY n DESC'
)
save("renewal_check", renewal_sql, [REG, REN])

save("reg_by_entity_status",
     'SELECT "' + REG + '" AS reg_status, "' + ENT + '" AS entity_status, COUNT(*) AS n FROM ' + T + ' GROUP BY 1, 2 ORDER BY n DESC',
     [REG, ENT])

print("\nDone. CSVs saved in docs/")