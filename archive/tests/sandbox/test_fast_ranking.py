# -*- coding: utf-8 -*-
import sys
import duckdb
import pandas as pd
sys.path.append('.')
from engine.sas_calculator_fast import FastSASCalculator

conn = duckdb.connect()
df_ele = conn.execute("SELECT * FROM 'data/processed/storico_2026_full.parquet' WHERE commodity='E' AND TIPO_OFFERTA LIKE '%Fisso%'").df()

df_ele = df_ele[df_ele['COND_Attivazione_LIMITANTE'].isna() | 
                (df_ele['COND_Attivazione_LIMITANTE'] == '') | 
                (df_ele['COND_Attivazione_LIMITANTE'] == 'None') |
                df_ele['COND_Attivazione_LIMITANTE'].astype(str).str.contains('non', case=False, na=False)]

calc_ele = FastSASCalculator(df_ele)
filtered_ele = calc_ele.filter_offers(commodity='E', tipo_offerta='Fisso', tipo_cliente='Domestico', fasce='Biorario', regione='Lombardia', provincia='015', comune='F205')

res_ele = calc_ele.calculate_sas(filtered_ele, {'F1': 891, 'F2': 837, 'F3': 972}, 3.0, is_dual_fuel=False, is_domiciliazione=False, regione='Lombardia', residente=True)
res_ele = res_ele.sort_values(by='SAS', ascending=True).drop_duplicates(subset=['COD_OFFERTA']).head(20)
print(res_ele[['NOME_OFFERTA', 'COD_OFFERTA', 'SAS']].to_string(index=False))
