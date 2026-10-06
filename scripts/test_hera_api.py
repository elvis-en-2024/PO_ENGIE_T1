from playwright.sync_api import sync_playwright
import os

os.environ['NODE_TLS_REJECT_UNAUTHORIZED'] = '0'

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    
    urls_found = []
    def handle_response(response):
        url = response.url.lower()
        if 'pdf' in url or 'zip' in url or 'api' in url or 'document' in url:
            urls_found.append(response.url)
            
    page.on("response", handle_response)
    page.goto('https://heracomm.gruppohera.it/casa/offerte-luce-gas/hera-impronta-zero', wait_until='networkidle')
    page.wait_for_timeout(5000)
    
    with open("hera_links.txt", "w") as f:
        for u in set(urls_found):
            f.write(u + "\n")
            
    browser.close()
