import pyarrow.parquet as pq
from engine.sas_calculator import SASCalculator
import pandas as pd

# Leggiamo solo un sottoinsieme del file per evitare freeze su Windows VM con file di rete
parquet_file = pq.ParquetFile('data/storage/storico_completo.parquet')
df = next(parquet_file.iter_batches(batch_size=10000)).to_pandas()
print(f"Lette le prime {len(df)} righe")

calc = SASCalculator(df)

filtered = calc.filter_offers(
    commodity='E',
    tipo_offerta='Fiss',
    tipo_cliente='Domestico',
    fasce='Biorario',
    regione='Lombardia'
)
print(f"Offerte dopo il filtraggio base: {len(filtered)}")

oggi = pd.to_datetime('2026-08-24')
if 'DATA_INIZIO' in filtered.columns:
    filtered['DATA_INIZIO'] = pd.to_datetime(filtered['DATA_INIZIO'], errors='coerce')
    filtered = filtered[filtered['DATA_INIZIO'] <= oggi]

if 'COMP_IMP_1_INT_1_VALIDO_FINO' in filtered.columns:
    filtered['VALIDO_FINO'] = pd.to_datetime(filtered['COMP_IMP_1_INT_1_VALIDO_FINO'], errors='coerce')
    filtered = filtered[(filtered['VALIDO_FINO'].isna()) | (filtered['VALIDO_FINO'] >= oggi)]

print(f"Offerte valide ad oggi: {len(filtered)}")

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

print("\\n=== TOP 5 OFFERTE (campione): ELE, DOM. RES. MILANO, FISSO, BIORARIO, 2700 kWh, 3kW ===")
if len(res) > 0:
    print(res.head(5).to_string())
else:
    print("Nessuna offerta trovata nel batch.")
