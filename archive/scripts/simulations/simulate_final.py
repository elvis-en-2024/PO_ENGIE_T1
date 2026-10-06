import sys
import os
sys.path.append('.')
from engine.sas_calculator_fast import FastSASCalculator
import pandas as pd
import duckdb

conn = duckdb.connect()
print('--- SIMULAZIONE GAS (1400 Smc) ---')
df_gas = conn.execute("SELECT * FROM 'data/processed/storico_2026_full.parquet' WHERE commodity='G' AND TIPO_OFFERTA LIKE '%Fisso%'").df()
calc = FastSASCalculator(df_gas)
filtered_gas = calc.filter_offers(commodity='G', tipo_offerta='Fisso', tipo_cliente='Domestico', regione='Lombardia', provincia='015', comune='F205')
filtered_gas = calc.calculate_sas(filtered_gas, {'F1': 1400}, 3.0, residente=True)
res_gas = filtered_gas[['NOME_OFFERTA', 'COD_OFFERTA', 'SAS']].head(10)
print(res_gas.to_string(index=False))

print('\n--- SIMULAZIONE ELE (2700 kWh, Biorario) ---')
df_ele = conn.execute("SELECT * FROM 'data/processed/storico_2026_full.parquet' WHERE commodity='E' AND TIPO_OFFERTA LIKE '%Fisso%'").df()
calc_ele = FastSASCalculator(df_ele)
filtered_ele = calc_ele.filter_offers(commodity='E', tipo_offerta='Fisso', tipo_cliente='Domestico', fasce='Biorario', regione='Lombardia', provincia='015', comune='F205')
filtered_ele = calc_ele.calculate_sas(filtered_ele, {'F1': 891, 'F2': 837, 'F3': 972}, 3.0, residente=True)
res_ele = filtered_ele[['NOME_OFFERTA', 'COD_OFFERTA', 'SAS']].head(10)
print(res_ele.to_string(index=False))
