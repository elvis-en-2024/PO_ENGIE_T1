import sys
import pandas as pd

sys.path.append('.')
from engine.sas_calculator_fast import FastSASCalculator

print("Loading parquet...")
df = pd.read_parquet('data/processed/storico_2026_full.parquet')

# Escludi limitanti
df = df[df['COND_Attivazione_LIMITANTE'].isna() | (df['COND_Attivazione_LIMITANTE'] == '') | (df['COND_Attivazione_LIMITANTE'] == 'None')]
# Escludi pluriennali se serve, ma non lo faccio per ora

print("=========================================")
print("  RANKING GAS: 1400 Smc, Residente, Fisso")
print("=========================================")
df_gas = df[(df['commodity'] == 'G') & (df['TIPO_OFFERTA'].astype(str).str.contains('Fisso', case=False, na=False))].copy()

calc = FastSASCalculator(df_gas)
filtered_gas = calc.filter_offers(commodity='G', tipo_offerta='Fisso', tipo_cliente='Domestico', regione='Lombardia', provincia='015', comune='F205')
res_gas = calc.calculate_sas(filtered_gas, {'F1': 1400}, 3.0, is_dual_fuel=False, is_domiciliazione=False, regione='Lombardia', residente=True)
res_gas = res_gas.sort_values(by='SAS', ascending=True).drop_duplicates(subset=['COD_OFFERTA']).head(20)
print(res_gas[['NOME_OFFERTA', 'COD_OFFERTA', 'SAS']].to_string(index=False))


print("\n=========================================")
print("  RANKING ELE: 2700 kWh, Biorario, Residente")
print("=========================================")
df_ele = df[(df['commodity'] == 'E') & (df['TIPO_OFFERTA'].astype(str).str.contains('Fisso', case=False, na=False))].copy()

calc_ele = FastSASCalculator(df_ele)
filtered_ele = calc_ele.filter_offers(commodity='E', tipo_offerta='Fisso', tipo_cliente='Domestico', fasce='Biorario', regione='Lombardia', provincia='015', comune='F205')
res_ele = calc_ele.calculate_sas(filtered_ele, {'F1': 891, 'F2': 837, 'F3': 972}, 3.0, is_dual_fuel=False, is_domiciliazione=False, regione='Lombardia', residente=True)
res_ele = res_ele.sort_values(by='SAS', ascending=True).drop_duplicates(subset=['COD_OFFERTA']).head(20)
print(res_ele[['NOME_OFFERTA', 'COD_OFFERTA', 'SAS']].to_string(index=False))
