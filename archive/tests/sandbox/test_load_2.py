import pandas as pd
print("Loading...")
df = pd.read_parquet('data/processed/storico_2026_full.parquet', columns=['PIVA_VENDITORE', 'COD_OFFERTA', 'DATA_RILEVAZIONE', 'DATA_INIZIO', 'NOME_OFFERTA'])
print("Loaded. Rows:", len(df))
data_rif = pd.to_datetime('2026-08-27', format='%Y-%m-%d')
df['DATA_RILEVAZIONE_DT'] = pd.to_datetime(df['DATA_RILEVAZIONE'], errors='coerce')
df = df[df['DATA_RILEVAZIONE_DT'] <= data_rif]
df = df.sort_values(['DATA_RILEVAZIONE_DT', 'COD_OFFERTA'], ascending=[False, True])
df = df.drop_duplicates(subset=['PIVA_VENDITORE', 'COD_OFFERTA'])
max_ril = df['DATA_RILEVAZIONE_DT'].max()
print("Max ril:", max_ril)
df = df[df['DATA_RILEVAZIONE_DT'] >= max_ril - pd.Timedelta(days=7)]
print("Final rows:", len(df))
