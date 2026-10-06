import duckdb
conn = duckdb.connect()
df = conn.execute("SELECT COD_OFFERTA, NOME_OFFERTA, DISP_DispBT FROM 'data/processed/storico_2026_full.parquet' WHERE COD_OFFERTA IN ('000362ESFFL01XXL626U0D000000A000', '000788ESFFL01XXFWEBE06326X3X0000', '000155ESFFL07XXZZ03839Z260805E03', '026160ESFFL51XXLFIXA24VSMA130726')").df()
df = df.drop_duplicates(subset=['COD_OFFERTA'])
print(df.to_string())
