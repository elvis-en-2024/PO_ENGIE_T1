import duckdb
import pandas as pd

conn = duckdb.connect()
df = conn.execute("SELECT * FROM 'data/processed/storico_2026_full.parquet' WHERE COD_OFFERTA IN ('000362ESFFL01XXL626N0DV20000A000', '000362ESFFL01XXL626U0D000000A000')").df()

# Print differences
if len(df) >= 2:
    row1 = df.iloc[0]
    row2 = df.iloc[len(df)-1]
    for col in df.columns:
        val1 = str(row1[col])
        val2 = str(row2[col])
        if val1 != val2 and 'nan' not in val1 and 'nan' not in val2:
            print(f"{col}: {val1} vs {val2}")
        elif (('nan' in val1) ^ ('nan' in val2)) and val1 != val2:
            print(f"{col}: {val1} vs {val2}")
