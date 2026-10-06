import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
from engine.sas_calculator_fast import FastSASCalculator

df = pd.read_parquet('data/processed/storico_2026_full.parquet')
df = df[df['DATA_RIFERIMENTO'] == df['DATA_RIFERIMENTO'].max()]

calc = FastSASCalculator(df)
filtered = calc.filter_offers(commodity='G', tipo_offerta='Fisso', regione='Lombardia')

res = calc.calculate_sas(filtered, {'F1': 600}, potenza=None, residente=True, is_domiciliazione=True)
res = res.sort_values('SAS')
print(res[['PIVA_VENDITORE', 'NOME_OFFERTA', 'SAS', 'QUOTA_FISSA', 'PREZZO_UNITARIO']].head(15))
