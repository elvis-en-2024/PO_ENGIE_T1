import duckdb
import pandas as pd
import numpy as np
import sys
sys.path.append('.')
from engine.sas_calculator_fast import FastSASCalculator

conn = duckdb.connect()
df = conn.execute("SELECT * FROM 'data/processed/storico_2026_full.parquet' WHERE COD_OFFERTA = '000788ESFFL01XXFWEBE06326X3X0000'").df()

df = df.head(1)
calc = FastSASCalculator(df)

F1, F2, F3 = 891, 837, 972
TOT_CONS = F1 + F2 + F3

costo_fix = 0
costo_vol = 0

for c in range(1, 6):
    for i in range(1, 6):
        prezzo_col = f'COMP_IMP_{c}_INT_{i}_PREZZO'
        unita_col = f'COMP_IMP_{c}_INT_{i}_UNITA'
        fascia_col = f'COMP_IMP_{c}_INT_{i}_FASCIA'
        
        if prezzo_col not in df.columns or df[prezzo_col].isna().all():
            continue
            
        prezzo_str = str(df[prezzo_col].iloc[0]).replace(',', '.')
        prezzo = float(prezzo_str) if prezzo_str and prezzo_str != 'nan' else 0
        unita = str(df.get(unita_col, [''])[0])
        fascia = str(df.get(fascia_col, [''])[0])
        
        is_kwh = 'kWh' in unita
        is_smc = 'Smc' in unita
        is_kw = 'kW' in unita and not is_kwh
        
        if is_kwh:
            prezzo_netto = prezzo * 1.10
            costo_vol += prezzo_netto * TOT_CONS
            print(f"Volumetric: {prezzo} -> {prezzo_netto} * {TOT_CONS} = {prezzo_netto*TOT_CONS}")
        elif 'Anno' in unita or (not is_kwh and not is_smc and not is_kw and unita and unita != 'nan' and unita != 'None'):
            costo_fix += prezzo
            print(f"Fixed: {prezzo}")

print(f"costo_fix: {costo_fix}, costo_vol: {costo_vol}")
