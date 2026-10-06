import duckdb
res = duckdb.query("DESCRIBE SELECT * FROM read_parquet('data/processed/storico_2026_full.parquet') LIMIT 1").df()
print([c for c in res['column_name'] if 'VENDITORE' in c or 'NOME' in c])
