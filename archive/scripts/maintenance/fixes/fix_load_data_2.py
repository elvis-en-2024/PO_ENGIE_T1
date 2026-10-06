with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Find where return df is
old_code = 'return df'
new_code = '''
    col_piva = 'PIVA_UTENTE' if 'PIVA_UTENTE' in df.columns else 'PIVA_VENDITORE'
    piva_map = {
        '09633951000': 'Enel Energia', '06655971007': 'Enel Energia', '11475730154': 'ENGIE',
        '11956540153': 'A2A Energia', '02863660359': 'E.ON', '02319210213': 'Iren',
        '04584980962': 'Fastweb', '12874490159': 'Plenitude', '02031070994': 'Acea',
        '04179130963': 'Octopus'
    }
    df['NOME_VENDITORE'] = df[col_piva].map(piva_map).fillna(df[col_piva])
    df['Player'] = df['NOME_VENDITORE']
    return df
'''

content = content.replace(old_code, new_code)
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
