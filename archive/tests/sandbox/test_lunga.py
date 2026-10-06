import duckdb
res = duckdb.query("SELECT NOME_OFFERTA, TIPOLOGIA_FASCE, DISP_Cod_04_VALORE, DISP_Cod_05_VALORE FROM read_parquet('data/processed/storico_2026_full.parquet') WHERE NOME_OFFERTA LIKE 'Energia Lunga Luce%' LIMIT 2").df()
print(res)
