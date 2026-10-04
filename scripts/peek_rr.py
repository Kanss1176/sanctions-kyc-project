import glob
import duckdb

files = glob.glob("data/raw/*rr-golden-copy*.csv")
print("files found:", files)
f = files[0].replace("\\", "/")
con = duckdb.connect()
T = "read_csv_auto('" + f + "', sample_size=20000)"
for col in ["Relationship.RelationshipType", "Relationship.RelationshipStatus",
            "Relationship.StartNode.NodeIDType", "Relationship.EndNode.NodeIDType"]:
    print("\n==", col)
    for r in con.sql('SELECT "' + col + '", COUNT(*) FROM ' + T + ' GROUP BY 1 ORDER BY 2 DESC').fetchall():
        print(r)
print("\nrows:", con.sql("SELECT COUNT(*) FROM " + T).fetchone()[0])