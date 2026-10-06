with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re
old_code = '''    df['NOME_VENDITORE'] = df[col_piva].map(piva_map).fillna(df[col_piva])'''

new_code = '''
    def extract_name(url):
        import re, pandas as pd
        if pd.isna(url) or not str(url).strip(): return None
        s = str(url).lower().strip()
        s = re.sub(r'^https?://', '', s)
        s = re.sub(r'^www\.', '', s)
        s = s.split('/')[0]
        s = s.split('.')[0]
        if s == 'estenergy': return 'EstEnergy'
        return s.title()
        
    df['NOME_URL'] = df['URL_SITO_VENDITORE'] if 'URL_SITO_VENDITORE' in df.columns else None
    if df['NOME_URL'].notna().any():
        df['NOME_URL'] = df['NOME_URL'].apply(extract_name)
    else:
        df['NOME_URL'] = None
        
    df['NOME_VENDITORE'] = df[col_piva].map(piva_map).fillna(df['NOME_URL']).fillna(df[col_piva])
'''

content = content.replace(old_code, new_code)
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
