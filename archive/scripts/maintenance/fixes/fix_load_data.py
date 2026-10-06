with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Find the load_data block up to the return df
match = re.search(r'(def load_data\(data_rif_str\):.*?return df\n)', content, re.DOTALL)
if match:
    old_code = match.group(1)
    new_code = '''def load_data(data_rif_str):
    import duckdb
    import pandas as pd
    path = 'data/processed/storico_2026_full.parquet'
    
    query = f"""
    WITH raw AS (
        SELECT *
        FROM read_parquet('{path}')
        WHERE DATA_RILEVAZIONE <= '{data_rif_str}'
    ),
    ranked AS (
        SELECT *,
               ROW_NUMBER() OVER(PARTITION BY COALESCE(PIVA_UTENTE, PIVA_VENDITORE), COD_OFFERTA ORDER BY DATA_RILEVAZIONE DESC) as rn
        FROM raw
    ),
    dedup AS (
        SELECT * FROM ranked WHERE rn = 1
    ),
    max_date AS (
        SELECT MAX(DATA_RILEVAZIONE::DATE) as m_date FROM dedup
    )
    SELECT d.* EXCLUDE(rn)
    FROM dedup d, max_date m
    WHERE d.DATA_RILEVAZIONE::DATE >= (m.m_date - INTERVAL 7 DAY)
    """
    
    df = duckdb.query(query).df()
    
    # Extract first part of DATA_INIZIO if present
    if 'DATA_INIZIO' in df.columns:
        dt_inizio = df['DATA_INIZIO'].astype(str).str.split('_').str[0]
        dt_inizio = pd.to_datetime(dt_inizio, format='%d/%m/%Y', errors='coerce')
        data_rif = pd.to_datetime(data_rif_str, format='%Y-%m-%d')
        df = df[dt_inizio <= data_rif]
        
    return df
'''
    new_content = content.replace(old_code, new_code)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
