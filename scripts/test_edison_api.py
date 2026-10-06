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
            url = response.url.lower()
            if 'pdf' in url or 'api' in url or 'json' in url:
                urls_found.append(response.url)
                
        page.on("response", handle_response)
        
        print("Navigating to EDISON Luce...")
        page.goto("https://www.edisonenergia.it/edison/casa/luce", wait_until="networkidle")
        
        # Take a screenshot to see what it looks like
        page.screenshot(path="edison_screenshot.png", full_page=True)
        
        with open("edison_links.txt", "w") as f:
            for u in set(urls_found):
                f.write(u + "\n")
                
        print("Done. Saved to edison_links.txt")
        browser.close()

if __name__ == "__main__":
    run()
