import requests
import re
requests.packages.urllib3.disable_warnings()
html = requests.get('https://postepay.poste.it/poste-energia-luce-gas', verify=False).text
links = re.findall(r'href="([^"]*\.pdf[^"]*)"', html, re.IGNORECASE)
for l in set(links): print(l)
