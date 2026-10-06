import duckdb
import csv

print("1. Lettura colonne dalla transcodifica...")
col_order = []
with open('data/spreadsheets/tabella_xml_v2.csv', 'r', encoding='latin1') as f:
    reader = csv.DictReader(f)
    for row in reader:
        c = row.get('DATI')
        if c and c.strip() and c not in col_order:
            col_order.append(c.strip())

print("2. Connessione a DuckDB e analisi del Parquet...")
con = duckdb.connect(database=':memory:')

# Trova le colonne disponibili
cols_query = con.execute("DESCRIBE SELECT * FROM 'data/storage/storico_completo.parquet'").fetchall()
parquet_cols = [row[0] for row in cols_query]

# Determina la colonna della data per il filtro 2026
date_col = 'DATA_INIZIO' if 'DATA_INIZIO' in parquet_cols else ('valid_from' if 'valid_from' in parquet_cols else None)

# Riordino colonne
final_cols = [c for c in col_order if c in parquet_cols]
remaining_cols = [c for c in parquet_cols if c not in final_cols]
final_cols.extend(remaining_cols)

cols_str = ", ".join([f'"{c}"' for c in final_cols])

print("3. Esecuzione query di estrazione, filtro e salvataggio (formato Parquet)...")
if date_col:
    print(f"Filtro applicato: {date_col} nell'anno 2026")
    query = f"""
    COPY (
        SELECT {cols_str} 
        FROM 'data/storage/storico_completo.parquet'
        WHERE CAST({date_col} AS VARCHAR) LIKE '2026%'
    ) TO 'data/processed/storico_completo_2026_ordered.parquet' (FORMAT PARQUET)
    """
else:
    print("Nessuna colonna data trovata (DATA_INIZIO o valid_from). Procedo senza filtro anno.")
    query = f"""
    COPY (
        SELECT {cols_str} 
        FROM 'data/storage/storico_completo.parquet'
    ) TO 'data/processed/storico_completo_2026_ordered.parquet' (FORMAT PARQUET)
    """

con.execute(query)
print("Fatto! File salvato in: data/processed/storico_completo_2026_ordered.parquet")
