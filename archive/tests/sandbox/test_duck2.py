import duckdb
import pandas as pd
import time

t0 = time.time()
data_rif = '2026-08-27'

query = f"""
WITH raw AS (
    SELECT 
        *
    FROM read_parquet('data/processed/storico_2026_full.parquet')
    WHERE DATA_RILEVAZIONE <= '{data_rif}'
),
ranked AS (
    SELECT *,
           ROW_NUMBER() OVER(PARTITION BY PIVA_UTENTE, COD_OFFERTA ORDER BY DATA_RILEVAZIONE DESC) as rn
    FROM raw
),
dedup AS (
    SELECT * FROM ranked WHERE rn = 1
),
max_date AS (
    SELECT MAX(DATA_RILEVAZIONE::DATE) as m_date FROM dedup
)
SELECT d.* EXCLUDE(rn)
FROM dedup d, max_date m
WHERE d.DATA_RILEVAZIONE::DATE >= (m.m_date - INTERVAL 7 DAY)
"""
print("Running DuckDB query...")
df = duckdb.query(query).df()
print("Rows:", len(df))
print("Time:", time.time() - t0)
