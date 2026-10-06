import polars as pl
import pandas as pd
import os

print("Starting script...")
df_trans = pd.read_csv('data/spreadsheets/tabella_xml_v2.csv', encoding='latin1')
col_order_raw = df_trans['DATI'].dropna().tolist()
col_order = []
for c in col_order_raw:
    if c not in col_order:
        col_order.append(c)

print("Reading parquet...")
try:
    df_parquet = pl.read_parquet('data/processed/storico_2026_full.parquet')
except Exception as e:
    print("Error reading parquet:", e)
    exit(1)

print("Parquet read. Shape:", df_parquet.shape)

# Find date col
date_col = 'DATA_INIZIO' if 'DATA_INIZIO' in df_parquet.columns else 'valid_from'
if date_col in df_parquet.columns:
    print(f"Filtering by {date_col} == 2026")
    df_parquet = df_parquet.with_columns(pl.col(date_col).cast(pl.Utf8))
    df_parquet = df_parquet.filter(pl.col(date_col).str.starts_with("2026"))
else:
    print("No date column found among:", df_parquet.columns)

final_cols = [c for c in col_order if c in df_parquet.columns]
remaining_cols = [c for c in df_parquet.columns if c not in final_cols]
final_cols.extend(remaining_cols)

print("Reordering and saving...")
df_parquet = df_parquet.select(final_cols)
df_parquet.write_parquet('data/processed/storico_2026_ordered.parquet')
print("Done. Saved to data/processed/storico_2026_ordered.parquet")
