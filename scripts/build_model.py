import os
import duckdb

DB = "data/processed/onboarding.duckdb"
SAMPLE = "data/processed/entity_sample.parquet"
AS_OF = "2026-10-04 16:00:00"

os.makedirs("data/processed", exist_ok=True)
if os.path.exists(DB):
    os.remove(DB)
con = duckdb.connect(DB)

con.sql("""
CREATE TABLE dim_entity AS
SELECT
  "LEI" AS lei,
  "Entity.LegalName" AS legal_name,
  "Entity.LegalAddress.Country" AS legal_country,
  "Entity.HeadquartersAddress.Country" AS hq_country,
  "Entity.EntityCategory" AS entity_category,
  "Entity.LegalForm.EntityLegalFormCode" AS legal_form_code,
  "Entity.EntityStatus" AS entity_status,
  "Registration.RegistrationStatus" AS registration_status,
  TRY_CAST(LEFT("Registration.InitialRegistrationDate", 19) AS TIMESTAMP) AS initial_reg_ts,
  TRY_CAST(LEFT("Registration.LastUpdateDate", 19) AS TIMESTAMP) AS last_update_ts,
  TRY_CAST(LEFT("Registration.NextRenewalDate", 19) AS TIMESTAMP) AS next_renewal_ts,
  "Registration.ManagingLOU" AS managing_lou,
  stratum,
  sampling_weight
FROM read_parquet('data/processed/entity_sample.parquet')
""")

con.sql("""
CREATE TABLE dim_country AS
SELECT DISTINCT legal_country AS country_code FROM dim_entity
""")

con.sql("""
CREATE TABLE dim_rule (
  rule_id VARCHAR, description VARCHAR, source VARCHAR,
  severity INTEGER, action VARCHAR, sla_hours INTEGER
)
""")
con.sql("""
INSERT INTO dim_rule VALUES
('R01','Registration status is not ISSUED','observed',3,'escalate',48),
('R02','Renewal date passed at snapshot time','observed',3,'escalate',48),
('R03','Entity status inactive or successor exists','observed',2,'fix',72),
('R04','Legal and headquarters countries differ','observed',2,'fix',72)
""")

con.sql("CREATE TABLE model_build_log (built_at TIMESTAMP, as_of TIMESTAMP)")
con.sql("INSERT INTO model_build_log VALUES (now(), TIMESTAMP '" + AS_OF + "')")

con.sql("""
CREATE TABLE dq_finding AS
SELECT
  'DQ01' AS check_id,
  'Renewal date earlier than initial registration' AS check_name,
  lei,
  registration_status,
  'initial=' || CAST(initial_reg_ts AS VARCHAR) || ' renewal=' || CAST(next_renewal_ts AS VARCHAR) AS detail,
  CASE WHEN registration_status = 'ANNULLED'
       THEN 'Expected for annulled records; exclude ANNULLED from renewal-date rules'
       ELSE 'Unexpected; escalate to data owner' END AS disposition
FROM dim_entity
WHERE next_renewal_ts < initial_reg_ts
""")

for t in ["dim_entity", "dim_country", "dim_rule", "dq_finding"]:
    print(t, con.sql("SELECT COUNT(*) FROM " + t).fetchone()[0])
print("Saved:", DB)