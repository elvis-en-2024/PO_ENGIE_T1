import duckdb
import csv

print("Reading transcodifica...")
col_order = []
with open('data/spreadsheets/tabella_xml_v2.csv', 'r', encoding='latin1') as f:
    reader = csv.DictReader(f)
    for row in reader:
        c = row.get('DATI')
        if c and c.strip() and c not in col_order:
            col_order.append(c.strip())

print("Connecting to duckdb...")
con = duckdb.connect(database=':memory:')

print("Getting columns...")
cols_query = con.execute("DESCRIBE SELECT * FROM 'data/processed/storico_2026_full.parquet'").fetchall()
parquet_cols = [row[0] for row in cols_query]

final_cols = [c for c in col_order if c in parquet_cols]
remaining_cols = [c for c in parquet_cols if c not in final_cols]
final_cols.extend(remaining_cols)

print("Constructing query...")
cols_str = ", ".join([f'"{c}"' for c in final_cols])
query = f"""
COPY (
    SELECT {cols_str} 
    FROM 'data/processed/storico_2026_full.parquet'
) TO 'data/processed/storico_2026_ordered.parquet' (FORMAT PARQUET)
"""
print("Executing copy...")
con.execute(query)
print("Done! Saved to data/processed/storico_2026_ordered.parquet")
