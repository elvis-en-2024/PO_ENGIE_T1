with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'data_rif_str =' in line:
        lines.insert(i+1, 'escludi_false_multi = st.sidebar.checkbox("Escludi false multiorarie (F1=F2=F3)", value=True)\n')
        lines.insert(i+2, 'escludi_dual_fuel = st.sidebar.checkbox("Escludi offerte solo Dual Fuel", value=True)\n')
        break
with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
