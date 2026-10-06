import requests
import re
requests.packages.urllib3.disable_warnings()
html = requests.get('https://www.edisonenergia.it/edison/casa/luce/edison-sweet-luce', verify=False).text
links = re.findall(r'documenti\.edisonenergia\.it/[^\"]*id=[^\"]+', html, re.IGNORECASE)
print(f"Found {len(links)} links")
for l in set(links): print(l)
