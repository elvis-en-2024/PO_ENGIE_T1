import sys
sys.path.append('.')
from engine.sas_calculator_fast import FastSASCalculator
import pandas as pd
import duckdb

conn = duckdb.connect()
df = conn.execute("SELECT * FROM 'data/processed/storico_2026_full.parquet' WHERE commodity='G' AND TIPO_OFFERTA='01'").df()

calc = FastSASCalculator(df)
filtered = calc.filter_offers(commodity='G', tipo_offerta='Fisso', regione='Lombardia', provincia='015', comune='F205')
res = calc.calculate_sas(filtered, {'F1': 1400}, 3.0, residente=True)
print(res.columns)
if 'SAS' in res.columns:
    res = res.sort_values(by='SAS', ascending=True)
    print(res[['NOME_OFFERTA', 'COD_OFFERTA', 'SAS']].head(10).to_string())
else:
    print(res)
