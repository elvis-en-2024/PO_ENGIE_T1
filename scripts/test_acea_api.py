from playwright.sync_api import sync_playwright
import os

os.environ['NODE_TLS_REJECT_UNAUTHORIZED'] = '0'

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        urls_found = []
        
        def handle_response(response):
            if 'pdf' in response.url.lower() or 'doc' in response.url.lower() or 'cte' in response.url.lower():
                urls_found.append(response.url)
                
        page.on("response", handle_response)
        
        print("Navigating to ACEA Fix...")
        page.goto("https://www.aceaenergia.it/offerte-casa/acea-energia-fix", wait_until="networkidle")
        
        # Click Documentazione
        try:
            page.locator("text=Documentazione").click(timeout=3000)
            page.wait_for_timeout(2000)
        except Exception as e:
            pass
            
        # Click all accordion buttons
        try:
            buttons = page.locator("button, a").all()
            for b in buttons:
                if 'document' in b.inner_text().lower() or 'condizion' in b.inner_text().lower():
                    b.click(timeout=1000)
                    page.wait_for_timeout(1000)
        except Exception as e:
            pass
            
        with open("acea_links.txt", "w") as f:
            for u in set(urls_found):
                f.write(u + "\n")
                
        print("Done. Saved to acea_links.txt")
        browser.close()

if __name__ == "__main__":
    run()
