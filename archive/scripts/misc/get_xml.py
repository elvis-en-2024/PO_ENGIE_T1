import urllib.request
from bs4 import BeautifulSoup
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://www.ilportaleofferte.it/portaleOfferte/it/opendata.page', headers={'User-Agent': 'Mozilla/5.0'})
try:
    html = urllib.request.urlopen(req, context=ctx).read()
    soup = BeautifulSoup(html, 'html.parser')
    for a in soup.find_all('a', href=True):
        if 'zip' in a['href'].lower() or 'xml' in a['href'].lower():
            print(a['href'])
except Exception as e:
    print('Error:', e)

