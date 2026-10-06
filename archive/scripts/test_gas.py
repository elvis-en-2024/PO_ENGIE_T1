import polars as pl
from engine.sas_calculator import SASCalculator
import pandas as pd

df = pl.scan_parquet("data/storage/storico_completo.parquet")
max_date = df.select(pl.max("DATA_RILEVAZIONE")).collect().item()
df_latest_dicts = df.filter(pl.col("DATA_RILEVAZIONE") == max_date).collect().to_dicts()
df_latest = pd.DataFrame(df_latest_dicts)

calc = SASCalculator(df_latest)

filtered_gas = calc.filter_offers(commodity='G', tipo_offerta='Fisso')
consumi_gas = {'F1': 300, 'F2': 0, 'F3': 0}

for regione in ['Lombardia', 'Lazio', 'Campania', 'Sicilia']:
    res_gas = calc.calculate_sas(filtered_gas, consumi_gas, potenza=0, is_dual_fuel=False, is_domiciliazione=False, regione=regione)
    print(f'=== TOP 5 OFFERTE GAS ({regione.upper()}, 300 Smc) ===')
    print(res_gas[['NOME_OFFERTA', 'SPESA_MATERIA_PRIMA', 'SAS']].head(5).to_string())
    print()
