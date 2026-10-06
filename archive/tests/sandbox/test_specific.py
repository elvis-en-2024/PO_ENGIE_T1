import sys
import pandas as pd
import duckdb

sys.path.append('.')
from engine.sas_calculator_fast import FastSASCalculator

conn = duckdb.connect()

print("--- GAS (GAS GALATTICA e E.ON) ---")
df_gas = conn.execute("SELECT * FROM 'data/processed/storico_2026_full.parquet' WHERE commodity='G' AND COD_OFFERTA IN ('038693GSFML01XX00000000000032463', '000362GSFML01XXMP06U0DA00000A000')").df()
calc = FastSASCalculator(df_gas)
res_gas = calc.calculate_sas(df_gas, {'F1': 1400}, 3.0, is_dual_fuel=False, is_domiciliazione=False, regione='Lombardia', residente=True)
print(res_gas[['NOME_OFFERTA', 'SAS']])

print("\n--- ELE (E.ON LuceClick BiorariaVerde) ---")
df_ele = conn.execute("SELECT * FROM 'data/processed/storico_2026_full.parquet' WHERE commodity='E' AND COD_OFFERTA = '000362ESFFL01XXL626U0D000000A000'").df()
calc_ele = FastSASCalculator(df_ele)
res_ele = calc_ele.calculate_sas(df_ele, {'F1': 891, 'F2': 837, 'F3': 972}, 3.0, is_dual_fuel=False, is_domiciliazione=False, regione='Lombardia', residente=True)
print(res_ele[['NOME_OFFERTA', 'SAS']])
