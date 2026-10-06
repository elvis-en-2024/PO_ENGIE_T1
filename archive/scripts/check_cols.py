import duckdb
res = duckdb.connect().execute("DESCRIBE SELECT * FROM 'data/processed/storico_2026_ordered.parquet'").fetchall()
cols = [r[0] for r in res]
print("Number of columns:", len(cols))
print("First 20 columns:", cols[:20])
