import duckdb
res = duckdb.query("SELECT NOME_OFFERTA, TIPOLOGIA_FASCE FROM read_parquet('data/processed/storico_2026_full.parquet') WHERE NOME_OFFERTA = 'CasaFix1206260300' LIMIT 1").df()
print(res)
