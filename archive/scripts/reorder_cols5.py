import pyarrow.parquet as pq
import pyarrow as pa
import csv

print("Reading transcodifica...")
col_order = []
with open('data/spreadsheets/tabella_xml_v2.csv', 'r', encoding='latin1') as f:
    reader = csv.DictReader(f)
    for row in reader:
        c = row.get('DATI')
        if c and c.strip() and c not in col_order:
            col_order.append(c.strip())

print("Reading parquet file table...")
table = pq.read_table('data/processed/storico_2026_full.parquet')
print("Original columns:", len(table.column_names))

final_cols = [c for c in col_order if c in table.column_names]
remaining_cols = [c for c in table.column_names if c not in final_cols]
final_cols.extend(remaining_cols)

print("Selecting columns...")
table_out = table.select(final_cols)

print("Writing output...")
pq.write_table(table_out, 'data/processed/storico_2026_ordered.parquet')
print("Done! Saved to data/processed/storico_2026_ordered.parquet")
