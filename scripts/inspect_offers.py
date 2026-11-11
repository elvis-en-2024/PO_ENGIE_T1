import duckdb
con = duckdb.connect()
cols = [c[0] for c in con.execute("DESCRIBE SELECT * FROM read_parquet('data/storage/dim_offerta.parquet')").fetchall()]
print("Columns count:", len(cols))
print("First 30 columns:", cols[:30])

res = con.execute("SELECT COD_OFFERTA, NOME_OFFERTA, TIPO_MERCATO, TIPO_OFFERTA, TIPOLOGIA_FASCE FROM read_parquet('data/storage/dim_offerta.parquet') WHERE COD_OFFERTA LIKE '001714%' LIMIT 10").fetchall()
print("\nEngie sample offers:")
for r in res:
    print(r)
