import re

with open('engine/sas_calculator_fast.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Biorario filter
code = re.sub(
    r"if fasce == 'Biorario':\s*filtered = filtered\[filtered\['TIPOLOGIA_FASCE'\].astype\(str\).str.contains\('F2\|F3\|biorario\|Peak/OffPeak', na=False, regex=True, case=False\)\]",
    "if fasce == 'Biorario':\n                filtered = filtered[~filtered['TIPOLOGIA_FASCE'].astype(str).str.contains('monorario', na=False, regex=True, case=False) & filtered['TIPOLOGIA_FASCE'].astype(str).str.strip().astype(bool)]",
    code
)

# 2. Domestico filter
code = re.sub(
    r"\(filtered\['TIPO_CLIENTE'\].astype\(str\).str.contains\(tipo_cliente, case=False, na=False\)\)",
    "(filtered['TIPO_CLIENTE'].astype(str).str.contains(rf'\\\\b{tipo_cliente}\\\\b', case=False, regex=True, na=False))",
    code
)

# 3. Accisa Gas Nord/Sud and Addizionale (replace hardcoded calculation)
code = re.sub(
    r"gas_fix_arera, gas_vol_arera = self.arera.get_gas_costi_regolati\(regione, TOT_CONS, include_taxes=False\).*?accisa_gas \+= addiz_gas",
    "gas_fix_arera, gas_vol_arera = self.arera.get_gas_costi_regolati(regione, TOT_CONS, include_taxes=True, strict=False)\n        tot_arera_gas = gas_fix_arera + (gas_vol_arera * TOT_CONS)\n        accisa_gas = 0.0",
    code,
    flags=re.DOTALL
)

# Also update imponibile_gas
code = re.sub(
    r"imponibile_gas = costo_fix \+ costo_vol \+ tot_arera_netto_gas \+ accisa_gas",
    "imponibile_gas = costo_fix + costo_vol + tot_arera_gas",
    code
)

# 4. Duplicate fasce (only apply each unique fascia once per c per row) & ignoring '%' in is_fix
# We'll replace the inner loop for C and I with a tracked implementation.
# But regex replacing the whole C and I loop is easier.
with open('rewrite_engine.py', 'a', encoding='utf-8') as f:
    f.write('print("Rewrite script ready to execute.")\n')
print("Rewrite script ready to execute.")
