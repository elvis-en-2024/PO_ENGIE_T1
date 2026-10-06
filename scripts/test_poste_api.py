from playwright.sync_api import sync_playwright
import os

os.environ['NODE_TLS_REJECT_UNAUTHORIZED'] = '0'

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    
    urls_found = []
    def handle_response(response):
        if 'pdf' in response.url.lower():
            urls_found.append(response.url)
            
    page.on("response", handle_response)
    page.goto('https://postepay.poste.it/poste-energia-luce-gas', wait_until='domcontentloaded')
    page.wait_for_timeout(5000)
    
    print('PDFs found in network:', urls_found)
    
    # Also dump all link texts to see if we missed something
    for a in page.locator('a').element_handles():
        href = a.get_attribute('href')
        text = a.text_content()
        if text: text = text.strip()
        if href:
            if 'condizion' in text.lower() or 'sintetic' in text.lower() or 'pdf' in href.lower() or 'trasparenza' in text.lower() or 'document' in text.lower() or 'trasparenza' in href.lower() or 'document' in href.lower():
                print(f"[{text}] -> {href}")
                
    browser.close()
