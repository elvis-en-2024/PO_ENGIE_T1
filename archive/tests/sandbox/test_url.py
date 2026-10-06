import duckdb
df = duckdb.query("SELECT URL_SITO_VENDITORE FROM read_parquet('data/processed/storico_2026_full.parquet') LIMIT 10").df()
print(df)
