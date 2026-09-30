"""Run every query in sql/ against the processed CSVs and save the results."""
from pathlib import Path

import duckdb

OUT = Path("docs/sql_results")
OUT.mkdir(parents=True, exist_ok=True)
con = duckdb.connect()

for f in sorted(Path("sql").glob("*.sql")):
    df = con.execute(f.read_text(encoding="utf-8-sig")).df()
    df.to_csv(OUT / f"{f.stem}.csv", index=False)
    print(f"\n=== {f.name} ({len(df)} rows) ===")
    print(df.to_string(index=False))