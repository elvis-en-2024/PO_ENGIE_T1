import duckdb
import pandas as pd

df = duckdb.execute("SELECT * FROM read_parquet('data/storage/storico_completo.parquet') LIMIT 0").df()
cols = df.columns.tolist()

targets = ['VEND', 'RAGIONE', 'NOME', 'PIVA', 'COMP']
print([c for c in cols if any(t in c.upper() for t in targets)])
