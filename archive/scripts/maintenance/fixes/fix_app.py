import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace the duckdb part
new_load_data = '''def load_data(data_rif_str):
    import pandas as pd
    path = 'data/processed/storico_2026_full.parquet'
    
    # Use pandas directly which is memory efficient for this
    df = pd.read_parquet(path)
    
    col_piva = 'PIVA_UTENTE' if 'PIVA_UTENTE' in df.columns else 'PIVA_VENDITORE'
    col_cod = 'CODICE_OFFERTA' if 'CODICE_OFFERTA' in df.columns else 'COD_OFFERTA'
    
    # Filter by date
    if 'DATA_FINE' in df.columns:
        df['DATA_FINE'] = pd.to_datetime(df['DATA_FINE'], errors='coerce')
        df = df[df['DATA_FINE'] >= pd.Timestamp.today()]
        
    # Deduplicate
    subset = [col_piva, col_cod]
    if 'commodity' in df.columns:
        subset.append('commodity')
        
    if 'DATA_RILEVAZIONE' in df.columns:
        df = df.sort_values(['DATA_RILEVAZIONE', col_cod], ascending=[False, True])
        
    df = df.drop_duplicates(subset=subset)
    return df
'''

code = re.sub(r'def load_data\(data_rif_str\):.*?return duckdb\.query\(query\)\.df\(\)', new_load_data, code, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
