import pandas as pd
from engine.sas_calculator_fast import FastSASCalculator
from app import load_data

df = load_data('2026-08-24')
calc = FastSASCalculator(df)
filtered = calc.filter_offers(commodity='E', fasce='Biorario', tipo_offerta='Fisso', regione='Lombardia')
res = calc.calculate_sas(filtered, {'F1': 891, 'F2': 837, 'F3': 972}, potenza=3.0, residente=True, is_domiciliazione=True)

print(res[['PIVA_VENDITORE', 'NOME_OFFERTA', 'SAS', 'QUOTA_FISSA', 'PREZZO_UNITARIO']].head(10))
