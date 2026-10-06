with open('engine/sas_calculator_fast.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace("* 1.10, 0)", ", 0)")

with open('engine/sas_calculator_fast.py', 'w', encoding='utf-8') as f:
    f.write(code)
