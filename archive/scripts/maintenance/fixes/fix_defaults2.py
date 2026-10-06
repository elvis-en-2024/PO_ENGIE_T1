with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "regione = st.session_state.get('regione', 'Lombardia')",
    "regione = st.session_state.get('regione', 'Piemonte')"
)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
