import os
import time
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

def get_a2a_pdf():
    # Setup environment to ignore SSL errors for Playwright
    os.environ['NODE_TLS_REJECT_UNAUTHORIZED'] = '0'
    
    with sync_playwright() as p:
        # Launch Chromium (ignore https errors)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        pdf_urls = set()
        
        # Intercept network requests to catch hidden PDFs
        def handle_response(response):
            try:
                url = response.url.lower()
                if '.pdf' in url or 'condizioni' in url:
                    pdf_urls.add(response.url)
            except:
                pass
                
        page.on("response", handle_response)
        
        print("Navigating to A2A Click...")
        page.goto("https://www.a2a.it/casa/a2a-click", wait_until="networkidle")
        
        # Wait a bit for JS to render
        page.wait_for_timeout(3000)
        
        # Scroll to bottom to trigger lazy loading
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        
        # Extract all a hrefs from the rendered DOM
        print("Evaluating DOM links...")
        links = page.eval_on_selector_all("a", "elements => elements.map(e => e.href)")
        
        for link in links:
            if not link: continue
            if '.pdf' in link.lower() or 'condizioni' in link.lower() or 'cte' in link.lower():
                pdf_urls.add(link)
                
        # Try to click on any button that says "Documenti" or "Condizioni"
        print("Trying to click document tabs...")
        try:
            buttons = page.locator("button:has-text('Documenti'), button:has-text('Condizioni'), a:has-text('Documenti')").all()
            for b in buttons:
                b.click(timeout=1000)
                page.wait_for_timeout(1000)
        except Exception as e:
            pass
            
        print("--- Risultati ---")
        for p_url in pdf_urls:
            print("Found:", p_url)
            
        browser.close()

if __name__ == "__main__":
    get_a2a_pdf()
