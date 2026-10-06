from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        def handle_response(response):
            # Print URLs that look like JSON APIs or PDFs
            if 'pdf' in response.url.lower() or '/api/' in response.url.lower() or 'offert' in response.url.lower():
                print(f"[{response.status}] {response.url}")
                
        page.on("response", handle_response)
        print("Navigating to A2A Click...")
        page.goto("https://www.a2a.it/casa/a2a-click", wait_until="networkidle")
        browser.close()

if __name__ == "__main__":
    run()
