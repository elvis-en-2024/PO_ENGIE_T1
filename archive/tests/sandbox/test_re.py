import re
with open('ELE_2700.html', 'r', encoding='utf-8') as f:
    text = f.read()

offers = re.findall(r'<p class="nome_offerta">(.*?)</p>', text, re.DOTALL)
prices = re.findall(r'(\d+,\d{2})&nbsp;&euro;', text)
print("Top 5:")
for o, p in zip(offers[:5], prices[:5]):
    print(o.strip(), p)
