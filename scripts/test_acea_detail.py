import requests
import re
requests.packages.urllib3.disable_warnings()
url = 'https://www.aceaenergia.it/offerte-casa/acea-energia-fix'
html = requests.get(url, verify=False).text
pdfs = re.findall(r'/content/dam/[a-zA-Z0-9_\-\/]+\.pdf', html, re.IGNORECASE)
for p in set(pdfs): print(p)
