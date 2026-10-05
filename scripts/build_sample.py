import csv
import os
import duckdb

SEED = "gleif-sample-2026-v1"
P = "data/processed/gleif_lei_slim.parquet"
OUT = "data/processed/entity_sample.parquet"
T = "read_parquet('" + P + "')"

LEI = "LEI"
REG = "Registration.RegistrationStatus"
CTRY = "Entity.LegalAddress.Country"

COUNTRIES = ["IN", "US", "GB", "DE", "FR", "NL", "LU", "CH", "IE", "CA", "AU", "KY"]
QUOTA = {"ISSUED": 2500, "LAPSED": 1500, "OTHER_NON_ACTIVE": 1000}

os.makedirs("docs", exist_ok=True)
con = duckdb.connect()
cols = [r[0] for r in con.sql("DESCRIBE SELECT * FROM " + T).fetchall()]
for need in (LEI, REG, CTRY):
    if need not in cols:
        print("Missing column:", need)
        print("Columns available:", cols)
        raise SystemExit(1)

in_list = ", ".join("'" + c + "'" for c in COUNTRIES)
base = (
    'SELECT *, CASE WHEN "' + REG + '" = \'ISSUED\' THEN \'ISSUED\' '
    'WHEN "' + REG + '" = \'LAPSED\' THEN \'LAPSED\' '
    "ELSE 'OTHER_NON_ACTIVE' END AS stratum "
    "FROM " + T + ' WHERE "' + CTRY + '" IN (' + in_list + ")"
)
quota_case = "CASE stratum " + " ".join(
    "WHEN '" + k + "' THEN " + str(v) for k, v in QUOTA.items()
) + " ELSE 0 END"

sql = (
    "CREATE TABLE s AS "
    "WITH base AS (" + base + "), "
    "ranked AS (SELECT *, "
    'ROW_NUMBER() OVER (PARTITION BY stratum ORDER BY hash("' + LEI + "\" || '" + SEED + "')) AS rn, "
    "COUNT(*) OVER (PARTITION BY stratum) AS stratum_population "
    "FROM base) "
    "SELECT * EXCLUDE (rn), "
    "stratum_population * 1.0 / LEAST(" + quota_case + ", stratum_population) AS sampling_weight "
    "FROM ranked WHERE rn <= " + quota_case
)
con.sql(sql)
con.sql("COPY s TO '" + OUT + "' (FORMAT PARQUET)")

n, n_unique = con.sql('SELECT COUNT(*), COUNT(DISTINCT "' + LEI + '") FROM s').fetchone()
print("sample rows:", n, "| unique LEIs:", n_unique)

res = con.sql(
    "SELECT stratum, MIN(stratum_population) AS population, COUNT(*) AS sampled, "
    "ROUND(MIN(sampling_weight), 2) AS weight FROM s GROUP BY 1 ORDER BY 1"
)
rows = res.fetchall()
header = res.columns
print(header)
for r in rows:
    print(r)
with open("docs/sample_design_summary.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(header)
    w.writerows(rows)

print("\nBy country:")
for r in con.sql('SELECT "' + CTRY + '", COUNT(*) FROM s GROUP BY 1 ORDER BY 2 DESC').fetchall():
    print(r)
print("\nSaved:", OUT)