import duckdb
res = duckdb.query("SELECT NOME_OFFERTA, TIPOLOGIA_FASCE, DISP_Cod_04_VALORE, DISP_Cod_05_VALORE FROM read_parquet('data/processed/storico_2026_full.parquet') WHERE NOME_OFFERTA LIKE 'CASA SERENA%' LIMIT 1").df()
print(res)
