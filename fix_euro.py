with open('engine/component_matrix.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'return KIND_PCT' in line:
        lines[i+1] = '    if "euro" in n or "anno" in n:\n'
        break

with open('engine/component_matrix.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
