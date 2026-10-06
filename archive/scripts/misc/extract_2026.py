import duckdb

query = """
COPY (
    SELECT *
    FROM read_parquet('data/storage/storico_completo.parquet')
    WHERE DATA_INIZIO LIKE '%2026%' OR DATA_INIZIO LIKE '%2025%'
) TO 'data/processed/storico_2026_full.parquet' (FORMAT PARQUET);
"""
duckdb.execute(query)
print("Data extracted successfully!")
