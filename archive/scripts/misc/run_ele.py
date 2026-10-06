import sys
sys.path.append('.')
from engine.sas_calculator_fast import FastSASCalculator
import pandas as pd
import duckdb

conn = duckdb.connect()
df = conn.execute("SELECT * FROM 'data/processed/storico_2026_full.parquet' WHERE commodity='E' AND TIPO_OFFERTA LIKE '%Fisso%'").df()

calc = FastSASCalculator(df)
filtered = calc.filter_offers(commodity='E', tipo_offerta='Fisso', tipo_cliente='Domestico', fasce='Biorario', regione='Lombardia')

res = calc.calculate_sas(filtered, 2700, {'F1': 891, 'F2': 837, 'F3': 972}, False, True)
res = res.sort_values(by='SAS', ascending=True)
print(res[['NOME_OFFERTA', 'COD_OFFERTA', 'SAS']].head(10).to_string())
