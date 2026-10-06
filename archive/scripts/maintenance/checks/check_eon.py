import pandas as pd
import duckdb
conn = duckdb.connect()
df = conn.execute("SELECT NOME_OFFERTA, TIPOLOGIA_FASCE FROM 'data/processed/storico_2026_full.parquet' WHERE COD_OFFERTA='000362ESFFL01XXL626U0D000000A000' LIMIT 5").df()
print(df)
