import re
with open('engine/sas_calculator_fast.py', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r"acc_g_4 = 0\.186 \* np\.maximum\(0, TOT_CONS - 1560\)\n\s+accisa_gas = acc_g_1 \+ acc_g_2 \+ acc_g_3 \+ acc_g_4"
replacement = """acc_g_4 = 0.186 * np.maximum(0, TOT_CONS - 1560)
        accisa_gas = acc_g_1 + acc_g_2 + acc_g_3 + acc_g_4
        
        # Addizionale Regionale (circa 0.019 - 0.022 a seconda della regione)
        addiz_rate = self.arera.GAS_ADDIZIONALE.get(regione, self.arera.GAS_ADDIZIONALE.get('DEFAULT', 0.019))
        addiz_gas = addiz_rate * TOT_CONS
        
        accisa_gas += addiz_gas"""

content = re.sub(pattern, replacement, content)

with open('engine/sas_calculator_fast.py', 'w', encoding='utf-8') as f:
    f.write(content)
