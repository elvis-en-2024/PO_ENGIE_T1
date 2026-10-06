import os
from playwright.sync_api import sync_playwright

os.environ['NODE_TLS_REJECT_UNAUTHORIZED'] = '0'

def download_salesforce_pdf():
    url = "https://a2aenergia.my.salesforce.com/sfc/p/1t000000D4H8/a/SX00000NaL8l/3rq7ktf0XpcUSWW4MNH0O1wBimZtHx7_I1TGn3rUGhU"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        print("Navigating to Salesforce viewer...")
        page.goto(url, wait_until="networkidle")
        
        print("Clicking download button...")
        try:
            # Try to click the download button (usually has an id like 'download' or class 'downloadIcon')
            with page.expect_download() as download_info:
                # We can try to click any button that has title Download or id download
                page.locator("[id*='download'], [title*='Download'], [title*='Scarica']").first.click()
                
            download = download_info.value
            filepath = os.path.join("data/raw/ctes", "a2a_downloaded.pdf")
            download.save_as(filepath)
            print(f"Downloaded to {filepath}")
            
        except Exception as e:
            print("Failed to click download:", e)
            print(page.content()[:1000])
            
        browser.close()

if __name__ == "__main__":
    download_salesforce_pdf()
