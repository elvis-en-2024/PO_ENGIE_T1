import requests
import re
requests.packages.urllib3.disable_warnings()
url = 'https://www.a2a.it/casa/a2a-click'
headers = {'User-Agent': 'Mozilla/5.0'}
html = requests.get(url, headers=headers, verify=False).text
pdfs = re.findall(r'"([^"]+\.pdf[^"]*)"', html, re.IGNORECASE)
for p in set(pdfs): print(p)
