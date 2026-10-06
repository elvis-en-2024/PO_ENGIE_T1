import duckdb
res = duckdb.query("SELECT NOME_OFFERTA, TIPO_OFFERTA, TIPO_CLIENTE, TIPOLOGIA_FASCE, REGIONE, PROVINCIA FROM read_parquet('data/processed/storico_2026_full.parquet') WHERE NOME_OFFERTA LIKE '%DOLOMITI FISSO LUCE 36%' LIMIT 5").df()
print(res)
