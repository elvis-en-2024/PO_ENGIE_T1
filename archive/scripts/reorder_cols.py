import pandas as pd
import pyarrow.parquet as pq

# Load transcodifica
df_trans = pd.read_csv('data/spreadsheets/tabella_xml_v2.csv', encoding='latin1')
col_order_raw = df_trans['DATI'].dropna().tolist()
col_order = []
for c in col_order_raw:
    if c not in col_order:
        col_order.append(c)

# Load parquet
table = pq.read_table('data/processed/storico_2026_full.parquet')
df_parquet = table.to_pandas()

# Filter for 2026 if necessary, assuming valid_from or DATA_INIZIO is present
date_col = 'DATA_INIZIO' if 'DATA_INIZIO' in df_parquet.columns else 'valid_from'
if date_col in df_parquet.columns:
    df_parquet[date_col] = pd.to_datetime(df_parquet[date_col], errors='coerce')
    df_parquet = df_parquet[df_parquet[date_col].dt.year == 2026]
else:
    print("Could not find date column. Columns:", df_parquet.columns)

# Reorder columns
final_cols = [c for c in col_order if c in df_parquet.columns]
# Add remaining columns not in transcodifica at the end
remaining_cols = [c for c in df_parquet.columns if c not in final_cols]
final_cols.extend(remaining_cols)

df_parquet = df_parquet[final_cols]

# Save to new parquet
df_parquet.to_parquet('data/processed/storico_2026_ordered.parquet')
print("Saved to data/processed/storico_2026_ordered.parquet")
print(f"Columns: {final_cols[:20]}")
