import duckdb

P = "data/processed/entity_sample.parquet"
cols = [
    "LEI",
    "Entity.LegalName",
    "Entity.LegalAddress.Country",
    "Entity.HeadquartersAddress.Country",
    "Entity.EntityCategory",
    "Entity.LegalForm.EntityLegalFormCode",
    "Entity.EntityStatus",
    "Entity.SuccessorEntity.1.SuccessorLEI",
    "Registration.InitialRegistrationDate",
    "Registration.LastUpdateDate",
    "Registration.RegistrationStatus",
    "Registration.NextRenewalDate",
    "Registration.ManagingLOU",
]
con = duckdb.connect()
for c in cols:
    r = con.sql('SELECT "' + c + '" FROM read_parquet(\'' + P + '\') WHERE "' + c + '" IS NOT NULL LIMIT 1').fetchone()
    print(c, "=>", r[0] if r else None)