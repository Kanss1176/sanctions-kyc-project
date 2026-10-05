import os
import sys

import duckdb
import pandas as pd
from rapidfuzz import fuzz, process

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import match

con = duckdb.connect("data/processed/onboarding.duckdb")
ent = pd.read_csv(match.ENT, dtype=str, low_memory=False)
ent["m"] = ent["name"].map(match.prep)
ent = ent[ent["m"] != ""].reset_index(drop=True)
choices = ent["m"].tolist()
src = ent["source"].tolist()
sid = ent["source_id"].tolist()
print("list records:", len(choices))

people = con.sql("SELECT lei, legal_name FROM dim_entity").fetchall()
rows = []
for i, (lei, name) in enumerate(people, 1):
    q = match.prep(name)
    best, bi = 0.0, -1
    if q:
        hits = process.extract(q, choices, scorer=fuzz.token_sort_ratio, limit=match.TOP_K, score_cutoff=40)
        for cand, ts, idx in hits:
            s = match.combined(q, cand, ts)
            if s > best:
                best, bi = s, idx
    rows.append((lei, round(best, 1), src[bi] if bi >= 0 else None, sid[bi] if bi >= 0 else None))
    if i % 500 == 0:
        print("screened", i, "/", len(people))

df = pd.DataFrame(rows, columns=["lei", "best_score", "list_source", "list_id"])
con.sql("DROP TABLE IF EXISTS fact_screen")
con.sql("CREATE TABLE fact_screen AS SELECT * FROM df")
print("fact_screen rows:", con.sql("SELECT COUNT(*) FROM fact_screen").fetchone()[0])
print("score bands (counts only):")
print(con.sql("SELECT CASE WHEN best_score >= 95 THEN '95+' WHEN best_score >= 90 THEN '90-95' WHEN best_score >= 85 THEN '85-90' WHEN best_score >= 80 THEN '80-85' WHEN best_score >= 70 THEN '70-80' ELSE 'under 70' END AS band, COUNT(*) AS n FROM fact_screen GROUP BY 1 ORDER BY MIN(best_score) DESC").fetchall())
