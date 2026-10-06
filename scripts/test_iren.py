import requests
import re
requests.packages.urllib3.disable_warnings()
html = requests.get('https://www.irenlucegas.it/casa/offerte-luce/iren-web-self-prezzo-fisso-luce', verify=False).text
links = re.findall(r'href="([^"]*pdf[^"]*)"', html, re.IGNORECASE)
for l in set(links): print(l)
