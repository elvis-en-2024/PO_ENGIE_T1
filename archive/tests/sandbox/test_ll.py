import duckdb
res = duckdb.query("SELECT TIPOLOGIA_FASCE FROM read_parquet('data/processed/storico_2026_full.parquet') WHERE NOME_OFFERTA = 'Energia Lunga Luce' LIMIT 1").df()
print(res.iloc[0]['TIPOLOGIA_FASCE'])
