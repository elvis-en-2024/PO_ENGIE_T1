import sys
import pandas as pd
import duckdb

sys.path.append('.')
from engine.sas_calculator_fast import FastSASCalculator

conn = duckdb.connect()

print("=========================================")
print("  SIMULAZIONE GAS: 1400 Smc, Residente, Fisso")
print("=========================================")
df_gas = conn.execute("SELECT * FROM 'data/processed/storico_2026_full.parquet' WHERE commodity='G' AND TIPO_OFFERTA LIKE '%Fisso%'").df()

calc = FastSASCalculator(df_gas)
filtered_gas = calc.filter_offers(commodity='G', tipo_offerta='Fisso', tipo_cliente='Domestico', regione='Lombardia', provincia='015', comune='F205')
res_gas = calc.calculate_sas(filtered_gas, {'F1': 1400}, 3.0, is_dual_fuel=False, is_domiciliazione=False, regione='Lombardia', residente=True)
if len(res_gas) > 0:
    print(res_gas[['NOME_OFFERTA', 'COD_OFFERTA', 'SAS']].head(10).to_string(index=False))


print("\n=========================================")
print("  SIMULAZIONE ELE: 2700 kWh, Biorario, Residente")
print("=========================================")
df_ele = conn.execute("SELECT * FROM 'data/processed/storico_2026_full.parquet' WHERE commodity='E' AND TIPO_OFFERTA LIKE '%Fisso%'").df()

calc_ele = FastSASCalculator(df_ele)
filtered_ele = calc_ele.filter_offers(commodity='E', tipo_offerta='Fisso', tipo_cliente='Domestico', fasce='Biorario', regione='Lombardia', provincia='015', comune='F205')
res_ele = calc_ele.calculate_sas(filtered_ele, {'F1': 891, 'F2': 837, 'F3': 972}, 3.0, is_dual_fuel=False, is_domiciliazione=False, regione='Lombardia', residente=True)
if len(res_ele) > 0:
    print(res_ele[['NOME_OFFERTA', 'COD_OFFERTA', 'SAS']].head(10).to_string(index=False))
