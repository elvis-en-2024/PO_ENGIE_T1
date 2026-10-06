import urllib.request
import re
req = urllib.request.Request('https://html.duckduckgo.com/html/?q=site:poste.it+energia', headers={'User-Agent': 'Mozilla/5.0'})
try:
    html = urllib.request.urlopen(req).read().decode('utf-8')
    for url in set(re.findall(r'href="([^"]+)"', html)):
        if 'poste.it' in url and 'energia' in url:
            print(url)
except Exception as e: print(e)
