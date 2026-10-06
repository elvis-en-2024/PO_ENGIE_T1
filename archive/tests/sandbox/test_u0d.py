import duckdb
import pandas as pd
import sys
sys.path.append('.')
from engine.sas_calculator_fast import FastSASCalculator

conn = duckdb.connect()
df = conn.execute("SELECT * FROM 'data/processed/storico_2026_full.parquet' WHERE COD_OFFERTA = '000362ESFFL01XXL626U0D000000A000'").df()

calc = FastSASCalculator(df)
res = calc.calculate_sas(df, {'F1': 891, 'F2': 837, 'F3': 972}, 3.0)
for col in ['PREZZO_COMPRENSIVO_PERDITE_RETE', 'DISP_CdispD', 'DISP_CdispD_VALORE', 'COMP_IMP_1_INT_1_PREZZO']:
    print(f"{col}: {df[col].iloc[0]}")
    
print(f"SAS Engine: {res['SAS'].iloc[0]}")
