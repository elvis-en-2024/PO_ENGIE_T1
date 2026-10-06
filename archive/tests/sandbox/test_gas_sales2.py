import duckdb
import pandas as pd
conn = duckdb.connect()
df = conn.execute("SELECT COD_OFFERTA, NOME_OFFERTA, COMP_IMP_1_INT_1_PREZZO, COMP_IMP_1_INT_1_UNITA, COMP_IMP_2_INT_1_PREZZO, COMP_IMP_2_INT_1_UNITA FROM 'data/processed/storico_2026_full.parquet' WHERE COD_OFFERTA = '000788ESFFL01XXFWEBE06326X3X0000'").df()
df = df.drop_duplicates(subset=['COD_OFFERTA'])
print(df.to_string())
