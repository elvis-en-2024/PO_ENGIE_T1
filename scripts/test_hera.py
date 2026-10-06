import requests
import re
requests.packages.urllib3.disable_warnings()
html = requests.get('https://heracomm.gruppohera.it/casa/offerte-luce-gas/hera-impronta-zero', verify=False).text
links = re.findall(r'/documents/[^\s"\'\\]+', html, re.IGNORECASE)
for l in set(links):
    if 'pdf' in l.lower() or 'zip' in l.lower():
        print(l)
