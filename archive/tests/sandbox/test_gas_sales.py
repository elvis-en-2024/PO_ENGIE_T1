import duckdb
import pandas as pd
import sys
sys.path.append('.')
from engine.sas_calculator_fast import FastSASCalculator

conn = duckdb.connect()
df = conn.execute("SELECT * FROM 'data/processed/storico_2026_full.parquet' WHERE COD_OFFERTA IN ('000362ESFFL01XXL626U0D000000A000', '000788ESFFL01XXFWEBE06326X3X0000')").df()

calc = FastSASCalculator(df)
res = calc.calculate_sas(df, {'F1': 891, 'F2': 837, 'F3': 972}, 3.0)
print(res[['NOME_OFFERTA', 'SAS']])
