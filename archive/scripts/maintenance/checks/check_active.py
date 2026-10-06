import duckdb
import pandas as pd

conn = duckdb.connect()
df = conn.execute("SELECT COD_OFFERTA, NOME_OFFERTA, DATA_FINE FROM 'data/processed/storico_2026_full.parquet' WHERE COD_OFFERTA LIKE '%000362ESFFL01XXL626%' AND (DATA_FINE IS NULL OR DATA_FINE == '' OR CAST(SUBSTRING(DATA_FINE, 7, 4) || '-' || SUBSTRING(DATA_FINE, 4, 2) || '-' || SUBSTRING(DATA_FINE, 1, 2) AS DATE) >= CURRENT_DATE)").df()
print(df)
