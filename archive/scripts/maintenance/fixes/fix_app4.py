with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

missing_code = '''
st.sidebar.markdown("### Impostazioni")
filtro_data = st.sidebar.date_input("Data di validita offerte", dt.date.today())
data_rif_str = filtro_data.strftime("%Y-%m-%d")

with st.spinner("Caricamento offerte in corso..."):
    df_attive = load_data(data_rif_str)

if 'step' not in st.session_state:
'''

code = code.replace("if 'step' not in st.session_state:", missing_code)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
