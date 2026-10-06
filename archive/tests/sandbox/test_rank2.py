import pandas as pd
from engine.sas_calculator_fast import FastSASCalculator
import duckdb

query = """SELECT * EXCLUDE(rn) FROM (SELECT *, ROW_NUMBER() OVER(PARTITION BY COD_OFFERTA ORDER BY try_strptime(split_part(DATA_INIZIO, '_', 1), '%d/%m/%Y') DESC NULLS LAST) as rn FROM read_parquet('data/processed/storico_2026_full.parquet') WHERE try_strptime(split_part(DATA_INIZIO, '_', 1), '%d/%m/%Y') <= '2026-08-24'::DATE) WHERE rn = 1"""
df = duckdb.query(query).df()
calc = FastSASCalculator(df)
filtered = calc.filter_offers(commodity='E', fasce='Biorario', tipo_offerta='Fisso', regione='Lombardia')
res = calc.calculate_sas(filtered, {'F1': 2700*0.334, 'F2': 2700*0.333, 'F3': 2700*0.333}, potenza=3.0, residente=True, is_domiciliazione=True)

print(res[res['COD_OFFERTA'] == '000362ESFFL01XXL626U0D000000A000'][['COD_OFFERTA', 'SAS', 'QUOTA_FISSA', 'PREZZO_UNITARIO']])
