with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "res['PIVA_VENDITORE'].map",
    "res.get('PIVA_VENDITORE', res.get('PIVA_UTENTE')).map"
)
content = content.replace(
    "fillna(res['PIVA_VENDITORE'])",
    "fillna(res.get('PIVA_VENDITORE', res.get('PIVA_UTENTE')))"
)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
