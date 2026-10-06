import pyarrow.parquet as pq
import pandas as pd
from engine.sas_calculator import SASCalculator
import time

start = time.time()
parquet_file = pq.ParquetFile('data/storage/storico_completo.parquet')
valid_rows = []

# Instantiate calculator without df to access filter logic
calc = SASCalculator(pd.DataFrame())
oggi = pd.to_datetime('2026-08-24')

print("Filtro in chunking...")
count = 0
for batch in parquet_file.iter_batches(batch_size=50000):
    df_chunk = batch.to_pandas()
    
    # Fill NaN to allow string operations
    df_chunk['commodity'] = df_chunk['commodity'].fillna('')
    df_chunk['TIPO_OFFERTA'] = df_chunk['TIPO_OFFERTA'].fillna('')
    df_chunk['TIPO_CLIENTE'] = df_chunk['TIPO_CLIENTE'].fillna('')
    df_chunk['TIPOLOGIA_FASCE'] = df_chunk['TIPOLOGIA_FASCE'].fillna('')
    
    # Applica filtro grezzo
    filtered = df_chunk[
        (df_chunk['commodity'] == 'E') & 
        (df_chunk['TIPO_OFFERTA'].str.contains('Fiss', case=False, na=False)) &
        (df_chunk['TIPO_CLIENTE'].str.contains('Domestico', case=False, na=False)) &
        (df_chunk['TIPOLOGIA_FASCE'].str.contains('F2|F3|biorario', case=False, na=False, regex=True))
    ]
    
    if len(filtered) > 0:
        if 'DATA_INIZIO' in filtered.columns:
            filtered['DATA_INIZIO'] = pd.to_datetime(filtered['DATA_INIZIO'], errors='coerce')
            filtered = filtered[filtered['DATA_INIZIO'] <= oggi]

        if 'COMP_IMP_1_INT_1_VALIDO_FINO' in filtered.columns:
            filtered['VALIDO_FINO'] = pd.to_datetime(filtered['COMP_IMP_1_INT_1_VALIDO_FINO'], errors='coerce')
            filtered = filtered[(filtered['VALIDO_FINO'].isna()) | (filtered['VALIDO_FINO'] >= oggi)]

        if len(filtered) > 0:
            valid_rows.append(filtered)
            
    count += len(df_chunk)
    if count % 200000 == 0:
        print(f"Elaborate {count} righe...")

print(f"Lette {count} righe totali. Trovate {sum(len(x) for x in valid_rows) if valid_rows else 0} offerte valide.")

if not valid_rows:
    print("Nessuna offerta trovata.")
else:
    df_final = pd.concat(valid_rows, ignore_index=True)
    
    # Rimuoviamo Sottocosto e FIXDOM
    df_final = df_final[~df_final['NOME_OFFERTA'].astype(str).str.contains('Sottocosto', case=False, na=False)]
    if 'CODICE_OFFERTA' in df_final.columns:
        df_final = df_final[~df_final['CODICE_OFFERTA'].astype(str).str.contains('FIXDOM', na=False)]
    elif 'COD_OFFERTA' in df_final.columns:
        df_final = df_final[~df_final['COD_OFFERTA'].astype(str).str.contains('FIXDOM', na=False)]
        
    consumi = {'F1': 891, 'F2': 837, 'F3': 972}
    potenza = 3.0

    print("Calcolo SAS sulle offerte valide...")
    res = calc.calculate_sas(
        filtered_df=df_final,
        consumi=consumi,
        potenza=potenza,
        is_dual_fuel=False,
        is_domiciliazione=False,
        regione='Lombardia',
        residente=True
    )
    
    print("\\n=== TOP 10 OFFERTE: ELE, DOMESTICO RESIDENTE MILANO, FISSO, BIORARIO, 2700 kWh, 3kW ===")
    print(res.head(10).to_string())

print(f"Tempo: {time.time() - start:.2f} s")
