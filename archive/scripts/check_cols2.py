import duckdb
res = duckdb.connect().execute("DESCRIBE SELECT * FROM 'data/processed/storico_2026_ordered.parquet'").fetchall()
cols = [r[0] for r in res]
print(cols[:15])
print([c for c in cols if 'COMP' in c][:10])
print([c for c in cols if 'SCONTO' in c][:10])
print([c for c in cols if 'COND' in c][:10])
