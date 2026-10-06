import duckdb
import pandas as pd
data_rif = '2026-08-27'
print("Querying DuckDB...")
query = f"""
    SELECT *
    FROM 'data/processed/storico_2026_full.parquet'
"""
df = duckdb.query(query).df()
print("Done. Rows:", len(df))
