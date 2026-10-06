import duckdb
conn = duckdb.connect()
df = conn.execute("SELECT * FROM 'data/processed/storico_2026_full.parquet' WHERE COD_OFFERTA = '000788ESFFL01XXFWEBE06326X3X0000'").df()
row = df.iloc[0]
for c in range(1, 3):
    for i in range(1, 6):
        prezzo_col = f'COMP_IMP_{c}_INT_{i}_PREZZO'
        fascia_col = f'COMP_IMP_{c}_INT_{i}_FASCIA'
        if row.get(prezzo_col):
            print(f"C{c} I{i}: {row.get(fascia_col)} -> {row.get(prezzo_col)}")
