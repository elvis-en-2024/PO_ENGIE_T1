import requests
import re
requests.packages.urllib3.disable_warnings()
html = requests.get('https://www.aceaenergia.it/offerte-per-casa', verify=False).text
pdfs = re.findall(r'"([^"]*\.pdf)"', html, re.IGNORECASE)
for p in set(pdfs):
    print(p)
