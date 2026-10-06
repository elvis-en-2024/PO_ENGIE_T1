import re

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_func = False
new_lines = []
for line in lines:
    if line.startswith('def load_data(data_rif_str):'):
        in_func = True
        new_lines.append('''def load_data(data_rif_str):
    import pandas as pd
    import datetime as dt
    path = 'data/processed/storico_2026_full.parquet'
    
    df = pd.read_parquet(path)
    
    col_piva = 'PIVA_UTENTE' if 'PIVA_UTENTE' in df.columns else 'PIVA_VENDITORE'
    col_cod = 'CODICE_OFFERTA' if 'CODICE_OFFERTA' in df.columns else 'COD_OFFERTA'
    
    # Filter by date
    if 'DATA_FINE' in df.columns:
        df['DATA_FINE'] = pd.to_datetime(df['DATA_FINE'], errors='coerce', dayfirst=True)
        df = df[df['DATA_FINE'] >= pd.Timestamp.today()]
        
    # Convert data_rif_str to datetime
    data_rif = pd.to_datetime(data_rif_str, format='%Y-%m-%d')
    if 'DATA_INIZIO' in df.columns:
        # Extract first part of DATA_INIZIO
        dt_inizio = df['DATA_INIZIO'].astype(str).str.split('_').str[0]
        dt_inizio = pd.to_datetime(dt_inizio, format='%d/%m/%Y', errors='coerce')
        df = df[dt_inizio <= data_rif]
        
    # Deduplicate
    subset = [col_piva, col_cod]
    if 'commodity' in df.columns:
        subset.append('commodity')
        
    if 'DATA_RILEVAZIONE' in df.columns:
        df = df.sort_values(['DATA_RILEVAZIONE', col_cod], ascending=[False, True])
        
    df = df.drop_duplicates(subset=subset)
    
    piva_map = {
        '09633951000': 'Enel Energia', '06655971007': 'Enel Energia', '11475730154': 'ENGIE',
        '11956540153': 'A2A Energia', '02863660359': 'E.ON', '02319210213': 'Iren',
        '04584980962': 'Fastweb', '12874490159': 'Plenitude', '02031070994': 'Acea',
        '04179130963': 'Octopus'
    }
    
    df['NOME_VENDITORE'] = df[col_piva].map(piva_map).fillna(df[col_piva])
    df['Player'] = df['NOME_VENDITORE']
    return df
''')
    elif in_func and line.startswith('def '):
        in_func = False
        new_lines.append(line)
    elif not in_func:
        new_lines.append(line)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
