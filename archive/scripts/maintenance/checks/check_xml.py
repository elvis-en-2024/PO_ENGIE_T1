import duckdb
conn = duckdb.connect()
df = conn.execute("SELECT OFFERTA_SINGOLA FROM 'data/processed/storico_2026_full.parquet' WHERE COD_OFFERTA='000362ESFFL01XXL626N0DV20000A000' LIMIT 1").df()
print(df.to_dict('records'))
