import pandas as pd
import pyarrow.parquet as pq
from engine.sas_calculator import SASCalculator
from datetime import datetime

print("Lettura del parquet in corso...")
df = pd.read_parquet('data/storage/storico_completo.parquet')
print(f"Parquet caricato, righe totali: {len(df)}")

# Creiamo l'istanza
calc = SASCalculator(df)

# Filtriamo per i criteri dell'utente:
# ELE (commodity='E' o 'EE', il sistema mappa 'E'), Fisso, Domestico, a fasce (Biorario), Milano (Lombardia)
print("Filtraggio delle offerte...")
filtered = calc.filter_offers(
    commodity='E',
    tipo_offerta='Fiss',
    tipo_cliente='Domestico',
    fasce='Biorario',
    regione='Lombardia'
)
print(f"Offerte dopo il filtraggio base: {len(filtered)}")

# Ulteriore filtro: valide ad oggi 24/08/2026 (assumiamo oggi)
oggi = pd.to_datetime('2026-08-24')

# DATA_INIZIO_VALIDITA o DATA_INIZIO
if 'DATA_INIZIO' in filtered.columns:
    filtered['DATA_INIZIO'] = pd.to_datetime(filtered['DATA_INIZIO'], errors='coerce')
    filtered = filtered[filtered['DATA_INIZIO'] <= oggi]

if 'COMP_IMP_1_INT_1_VALIDO_FINO' in filtered.columns:
    filtered['VALIDO_FINO'] = pd.to_datetime(filtered['COMP_IMP_1_INT_1_VALIDO_FINO'], errors='coerce')
    filtered = filtered[(filtered['VALIDO_FINO'].isna()) | (filtered['VALIDO_FINO'] >= oggi)]

print(f"Offerte valide in data 24/08/2026: {len(filtered)}")

# Calcoliamo la graduatoria
consumi = {'F1': 891, 'F2': 837, 'F3': 972} # 2700 kWh total
potenza = 3.0

print("Calcolo della Spesa Annua Stimata...")
res = calc.calculate_sas(
    filtered_df=filtered,
    consumi=consumi,
    potenza=potenza,
    is_dual_fuel=False,
    is_domiciliazione=False,
    regione='Lombardia',
    residente=True
)

print("\\n=== TOP 10 OFFERTE: ELE, DOMESTICO RESIDENTE MILANO, FISSO, BIORARIO, 2700 kWh, 3kW ===")
print(res.head(10).to_string())
