import duckdb
res = duckdb.query("SELECT PREZZO_UNITARIO, PREZZO_UNITARIO_F2, PREZZO_UNITARIO_F3 FROM read_parquet('data/processed/storico_2026_full.parquet') WHERE COD_OFFERTA = '000155ESFFL07XXZZ03839Z260805E03' LIMIT 1").df()
print(res)
