from playwright.sync_api import sync_playwright
import os

os.environ['NODE_TLS_REJECT_UNAUTHORIZED'] = '0'

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('https://html.duckduckgo.com/html/?q=site:poste.it+trasparenza+energia')
    
    links = page.locator('.result__url').element_handles()
    for link in links:
        print(link.text_content().strip())
    browser.close()
