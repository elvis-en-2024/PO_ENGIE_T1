import sys
import pandas as pd

def load_data(data_rif_str):
    path = 'data/processed/storico_2026_full.parquet'
    columns = ['PIVA_UTENTE', 'PIVA_VENDITORE', 'CODICE_OFFERTA', 'COD_OFFERTA', 'DATA_RILEVAZIONE', 'DATA_INIZIO', 'NOME_OFFERTA']
    table = __import__('pyarrow.parquet').parquet.read_table(path, columns=columns)
    df = table.to_pandas()
    
    col_piva = 'PIVA_UTENTE' if 'PIVA_UTENTE' in df.columns else 'PIVA_VENDITORE'
    col_cod = 'CODICE_OFFERTA' if 'CODICE_OFFERTA' in df.columns else 'COD_OFFERTA'
    
    data_rif = pd.to_datetime(data_rif_str, format='%Y-%m-%d')
    if 'DATA_RILEVAZIONE' in df.columns:
        df['DATA_RILEVAZIONE_DT'] = pd.to_datetime(df['DATA_RILEVAZIONE'], errors='coerce')
        df = df[df['DATA_RILEVAZIONE_DT'] <= data_rif]
        df = df.sort_values(['DATA_RILEVAZIONE_DT', col_cod], ascending=[False, True])
        
    if 'DATA_INIZIO' in df.columns:
        dt_inizio = df['DATA_INIZIO'].astype(str).str.split('_').str[0]
        dt_inizio = pd.to_datetime(dt_inizio, format='%d/%m/%Y', errors='coerce')
        df = df[dt_inizio <= data_rif]
        
    subset = [col_piva, col_cod]
    if 'commodity' in df.columns:
        subset.append('commodity')
        
    df = df.drop_duplicates(subset=subset)
    
    if 'DATA_RILEVAZIONE_DT' in df.columns and not df.empty:
        max_ril = df['DATA_RILEVAZIONE_DT'].max()
        if pd.notna(max_ril):
            df = df[df['DATA_RILEVAZIONE_DT'] >= max_ril - pd.Timedelta(days=7)]
    
    return df

df = load_data('2026-08-27')
print("Total rows returned:", len(df))
