with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove the incorrectly placed lines
new_lines = []
for line in lines:
    if 'escludi_false_multi = st.sidebar.checkbox' in line:
        continue
    if 'escludi_dual_fuel = st.sidebar.checkbox' in line:
        continue
    new_lines.append(line)

# Add them in the right place (around line 170 where sidebar is defined)
for i, line in enumerate(new_lines):
    if 'data_rif_str = filtro_data.strftime("%Y-%m-%d")' in line:
        new_lines.insert(i+1, 'escludi_false_multi = st.sidebar.checkbox("Escludi false multiorarie (F1=F2=F3)", value=True)\n')
        new_lines.insert(i+2, 'escludi_dual_fuel = st.sidebar.checkbox("Escludi offerte solo Dual Fuel", value=True)\n')
        break

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
