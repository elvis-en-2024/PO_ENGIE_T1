import pandas as pd
import time
from engine.sas_calculator_fast import FastSASCalculator

df = pd.read_csv('data/storage/verifica_piatta_20260820.csv', dtype=str)

calc = FastSASCalculator(df)

t0 = time.time()
filtered = calc.filter_offers(commodity='E', tipo_offerta='Fisso', tipo_cliente='Domestico', fasce='Biorario')

oggi = pd.to_datetime('2026-08-24')
if 'DATA_INIZIO' in filtered.columns:
    filtered['DATA_INIZIO'] = pd.to_datetime(filtered['DATA_INIZIO'], errors='coerce')
    filtered = filtered[(filtered['DATA_INIZIO'].isna()) | (filtered['DATA_INIZIO'] <= oggi)]

if 'COMP_IMP_1_INT_1_VALIDO_FINO' in filtered.columns:
    filtered['VALIDO_FINO'] = pd.to_datetime(filtered['COMP_IMP_1_INT_1_VALIDO_FINO'], errors='coerce')
    filtered = filtered[(filtered['VALIDO_FINO'].isna()) | (filtered['VALIDO_FINO'] >= oggi)]

consumi = {'F1': 891, 'F2': 837, 'F3': 972}
res = calc.calculate_sas(filtered, consumi=consumi, potenza=3.0)
t1 = time.time()

print(f"Elapsed: {t1-t0:.4f}s")
print(res[['COD_OFFERTA', 'NOME_OFFERTA', 'SPESA_MATERIA_PRIMA', 'SAS']].head())
