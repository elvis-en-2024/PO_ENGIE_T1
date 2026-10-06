from playwright.sync_api import sync_playwright
import os
import re
from urllib.parse import urljoin

os.environ['NODE_TLS_REJECT_UNAUTHORIZED'] = '0'

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('https://postepay.poste.it/poste-energia-luce-gas', wait_until='domcontentloaded')
    page.wait_for_timeout(5000)
    
    html = page.content()
    links = re.findall(r'href="([^"]*pdf[^"]*)"', html, re.IGNORECASE)
    print('Found PDFs:', len(set(links)))
    for l in set(links):
        print(urljoin('https://postepay.poste.it', l))
        
    browser.close()
