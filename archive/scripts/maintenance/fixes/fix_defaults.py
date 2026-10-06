with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Change escludi_false_multi to default False
content = content.replace(
    'escludi_false_multi = st.sidebar.checkbox("Escludi false multiorarie (F1=F2=F3)", value=True)',
    'escludi_false_multi = st.sidebar.checkbox("Escludi false multiorarie (F1=F2=F3)", value=False)'
)

# Change default region to Piemonte
content = content.replace(
    'st.session_state.regione = st.selectbox("Ambito Territoriale (Regione)", ["Lombardia", "Lazio", "Campania", "Sicilia", "Piemonte", "Veneto"])',
    'st.session_state.regione = st.selectbox("Ambito Territoriale (Regione)", ["Piemonte", "Lombardia", "Lazio", "Campania", "Sicilia", "Veneto"])'
)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
