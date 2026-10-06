import duckdb
df = duckdb.query("SELECT DISTINCT PIVA_UTENTE, URL_SITO_VENDITORE FROM read_parquet('data/processed/storico_2026_full.parquet') LIMIT 20").df()
print(df)
