with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("provincia='015'", "provincia=None")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
