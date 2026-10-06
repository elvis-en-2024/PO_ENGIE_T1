import re
import httpx
xml = httpx.get('https://ilportaleofferte.it/portaleOfferte/resources/opendata/csv/offerteML/2026_8/PO_Offerte_E_MLIBERO_20260825.xml', verify=False).content.decode('utf-8')
m = re.search(r'<[^>]*?offerta[^>]*>.*?000362ESFFL01XXL626U0D000000A000.*?</[^>]*?offerta>', xml, re.I | re.S)
if m: print(m.group(0))

