import glob
import os
import duckdb

os.makedirs("powerbi/source", exist_ok=True)
for db in sorted(glob.glob("data/processed/*.duckdb")):
    con = duckdb.connect(db, read_only=True)
    print("DB:", db)
    for (t,) in con.sql("SHOW TABLES").fetchall():
        cols = [r[0] for r in con.sql("DESCRIBE " + t).fetchall()]
        n = con.sql("SELECT COUNT(*) FROM " + t).fetchone()[0]
        sel = "SELECT * EXCLUDE (legal_name) FROM " if "legal_name" in cols else "SELECT * FROM "
        con.sql("COPY (" + sel + t + ") TO 'powerbi/source/" + t + ".csv' (HEADER)")
        print(" ", t, n, cols)
    con.close()
