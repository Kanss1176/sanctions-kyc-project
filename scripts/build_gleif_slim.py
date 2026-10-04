import duckdb, glob, os

src = glob.glob("data/raw/*-lei2-golden-copy*.csv")[0].replace("\\", "/")
con = duckdb.connect()
all_cols = [r[0] for r in con.sql(
    f"DESCRIBE SELECT * FROM read_csv('{src}', all_varchar=true)").fetchall()]

wanted = [
    "LEI", "Entity.LegalName",
    "Entity.LegalAddress.FirstAddressLine", "Entity.LegalAddress.City",
    "Entity.LegalAddress.Region", "Entity.LegalAddress.Country",
    "Entity.LegalAddress.PostalCode",
    "Entity.HeadquartersAddress.City", "Entity.HeadquartersAddress.Country",
    "Entity.RegistrationAuthority.RegistrationAuthorityID",
    "Entity.RegistrationAuthority.RegistrationAuthorityEntityID",
    "Entity.EntityCategory", "Entity.EntitySubCategory",
    "Entity.LegalForm.EntityLegalFormCode", "Entity.EntityStatus",
    "Entity.AssociatedEntity.AssociatedLEI", "Entity.SuccessorEntity.1.SuccessorLEI",
    "Registration.InitialRegistrationDate", "Registration.LastUpdateDate",
    "Registration.RegistrationStatus", "Registration.NextRenewalDate",
    "Registration.ManagingLOU",
]
use = [c for c in wanted if c in all_cols]
missing = [c for c in wanted if c not in all_cols]
print("using", len(use), "columns")
print("not found (skipped):", missing)

select_list = ", ".join(f'"{c}"' for c in use)
out = "data/processed/gleif_lei_slim.parquet"
os.makedirs("data/processed", exist_ok=True)
con.sql(f"COPY (SELECT {select_list} FROM read_csv('{src}', all_varchar=true)) "
        f"TO '{out}' (FORMAT PARQUET)")
n = con.sql(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
print("rows written:", n)