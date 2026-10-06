import duckdb
res = duckdb.query("SELECT DISTINCT REGIONE FROM read_parquet('data/processed/storico_2026_full.parquet') WHERE NOME_OFFERTA = 'DOLOMITI FISSO LUCE 36 BIORARIA WEB'").df()
print(res)
