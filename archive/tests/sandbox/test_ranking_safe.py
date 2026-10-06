import sys
import pandas as pd

sys.path.append('.')
from engine.sas_calculator_fast import FastSASCalculator

df = pd.read_parquet('data/processed/storico_2026_full.parquet')

# Filtra le offerte limitanti per simulare il comportamento di default del PO
df = df[df['COND_Attivazione_LIMITANTE'].isna() | (df['COND_Attivazione_LIMITANTE'] == '') | (df['COND_Attivazione_LIMITANTE'] == 'None')]
df = df[~df['NOME_OFFERTA'].astype(str).str.contains('Sottocosto', case=False, na=False)]

calc = FastSASCalculator(df)

print("--- GAS (1400 Smc) ---")
df_gas = df[(df['commodity'] == 'G') & (df['TIPO_OFFERTA'].astype(str).str.contains('Fisso', case=False, na=False))].copy()
filtered_gas = calc.filter_offers(commodity='G', tipo_offerta='Fisso', tipo_cliente='Domestico', regione='Lombardia', provincia='015', comune='F205')
# Filtra manually il dataframe
filtered_gas = filtered_gas[(filtered_gas['commodity'] == 'G') & (filtered_gas['TIPO_OFFERTA'].astype(str).str.contains('Fisso', case=False, na=False))]

res_gas = calc.calculate_sas(filtered_gas, {'F1': 1400}, 3.0, is_dual_fuel=False, is_domiciliazione=False, regione='Lombardia', residente=True)
res_gas = res_gas.sort_values(by='SAS', ascending=True).drop_duplicates(subset=['COD_OFFERTA']).head(10)
print(res_gas[['NOME_OFFERTA', 'COD_OFFERTA', 'SAS']].to_string(index=False))

print("\n--- ELE (2700 kWh) ---")
df_ele = df[(df['commodity'] == 'E') & (df['TIPO_OFFERTA'].astype(str).str.contains('Fisso', case=False, na=False))].copy()
filtered_ele = calc.filter_offers(commodity='E', tipo_offerta='Fisso', tipo_cliente='Domestico', fasce='Biorario', regione='Lombardia', provincia='015', comune='F205')
filtered_ele = filtered_ele[(filtered_ele['commodity'] == 'E') & (filtered_ele['TIPO_OFFERTA'].astype(str).str.contains('Fisso', case=False, na=False))]

res_ele = calc.calculate_sas(filtered_ele, {'F1': 891, 'F2': 837, 'F3': 972}, 3.0, is_dual_fuel=False, is_domiciliazione=False, regione='Lombardia', residente=True)
res_ele = res_ele.sort_values(by='SAS', ascending=True).drop_duplicates(subset=['COD_OFFERTA']).head(10)
print(res_ele[['NOME_OFFERTA', 'COD_OFFERTA', 'SAS']].to_string(index=False))
