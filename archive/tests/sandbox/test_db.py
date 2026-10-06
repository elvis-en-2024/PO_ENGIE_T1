import pandas as pd
import duckdb
conn = duckdb.connect()
df = conn.execute("SELECT TIPO_OFFERTA, count(*) FROM 'data/processed/storico_2026_full.parquet' WHERE commodity='G' GROUP BY TIPO_OFFERTA LIMIT 5").df()
print(df)
