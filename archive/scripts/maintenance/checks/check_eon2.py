import httpx
import re

url = 'https://ilportaleofferte.it/portaleOfferte/resources/opendata/csv/offerteML/2026_8/PO_Offerte_E_MLIBERO_20260825.xml'
resp = httpx.get(url, verify=False)
content = resp.content.decode('utf-8', errors='ignore')

match = re.search(r'(<[\w:]+offerta[^>]*>.*?luceclick.*?</[\w:]+offerta>)', content, re.DOTALL | re.IGNORECASE)
if match:
    block = match.group(1)
    ident = re.search(r'<[^>]*Identificativo[^>]*>(.*?)</[^>]*Identificativo>', block, re.IGNORECASE)
    print('ID in XML:', ident.group(1) if ident else 'None')

