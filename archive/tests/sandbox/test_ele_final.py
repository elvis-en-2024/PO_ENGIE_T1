import sys
sys.path.append('.')
from engine.sas_calculator_fast import FastSASCalculator
import pandas as pd
import duckdb

conn = duckdb.connect()
df = conn.execute("SELECT * FROM 'data/processed/storico_2026_full.parquet' WHERE commodity='E' AND TIPO_OFFERTA='01'").df()

calc = FastSASCalculator(df)
filtered = calc.filter_offers(commodity='E', fasce='Biorario', tipo_offerta='Fisso', regione='Lombardia', provincia='015', comune='F205')
res = calc.calculate_sas(filtered, 2700, {'F1': 891, 'F2': 837, 'F3': 972}, False, True)
res = res.sort_values(by='SAS', ascending=True)
print(res[['NOME_OFFERTA', 'COD_OFFERTA', 'SAS']].head(10).to_string())
