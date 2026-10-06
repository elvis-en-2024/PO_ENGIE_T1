import pyarrow.parquet as pq
import pandas as pd
from engine.sas_calculator import SASCalculator

print("Lettura del parquet test in corso...", flush=True)
df = pd.read_parquet('data/storage/test.parquet')
print(f"Righe lette: {len(df)}", flush=True)

calc = SASCalculator(df)

filtered = calc.filter_offers(
    commodity='E',
    tipo_offerta='Fiss',
    tipo_cliente='Domestico',
    fasce='Biorario',
    regione='Lombardia'
)
print(f"Offerte dopo il filtraggio base: {len(filtered)}", flush=True)

oggi = pd.to_datetime('2026-08-24')

if 'DATA_INIZIO' in filtered.columns:
    filtered['DATA_INIZIO'] = pd.to_datetime(filtered['DATA_INIZIO'], errors='coerce')
    filtered = filtered[filtered['DATA_INIZIO'] <= oggi]

if 'COMP_IMP_1_INT_1_VALIDO_FINO' in filtered.columns:
    filtered['VALIDO_FINO'] = pd.to_datetime(filtered['COMP_IMP_1_INT_1_VALIDO_FINO'], errors='coerce')
    filtered = filtered[(filtered['VALIDO_FINO'].isna()) | (filtered['VALIDO_FINO'] >= oggi)]

print(f"Offerte valide ad oggi: {len(filtered)}", flush=True)

consumi = {'F1': 891, 'F2': 837, 'F3': 972}
potenza = 3.0

res = calc.calculate_sas(
    filtered_df=filtered,
    consumi=consumi,
    potenza=potenza,
    is_dual_fuel=False,
    is_domiciliazione=False,
    regione='Lombardia',
    residente=True
)

if len(res) > 0:
    print(res.head(10).to_json(orient='records'))
else:
    print("[]")
