import duckdb, glob

con = duckdb.connect()
expected = {"lei2": 3451551, "rr": 489935, "repex": 6396820}
keywords = ["LEI", "LegalName", "Status", "Country", "Renewal", "Category",
            "LegalForm", "Registration", "LastUpdate", "Relationship", "Exception"]

for key, exp in expected.items():
    paths = glob.glob(f"data/raw/*-{key}-golden-copy*.csv")
    if not paths:
        print(key, "-> FILE NOT FOUND")
        continue
    f = paths[0].replace("\\", "/")
    cols = [r[0] for r in con.sql(
        f"DESCRIBE SELECT * FROM read_csv('{f}', all_varchar=true)").fetchall()]
    n = con.sql(f"SELECT COUNT(*) FROM read_csv('{f}', all_varchar=true)").fetchone()[0]
    print("=" * 70)
    print(key, "| file:", f)
    print("rows loaded:", n, "| GLEIF page said:", exp, "| match:", n == exp)
    print("total columns:", len(cols))
    with open(f"docs/gleif_columns_{key}.txt", "w", encoding="utf-8") as out:
        out.write("\n".join(cols))
    hits = [c for c in cols if any(k.lower() in c.lower() for k in keywords)]
    print("columns matching onboarding keywords:")
    for c in hits[:60]:
        print("  ", c)