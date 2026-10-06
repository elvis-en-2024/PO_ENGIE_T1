import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        requests_data = []

        async def handle_response(response):
            # Intercept API calls returning JSON
            if "application/json" in response.headers.get("content-type", ""):
                try:
                    data = await response.json()
                    requests_data.append({"url": response.url, "response": data})
                except:
                    pass

        page.on("response", handle_response)

        print("Navigazione...")
        await page.goto("https://ilportaleofferte.it/portaleOfferte/it/confronto-tariffe-prezzi-luce-gas.page", wait_until="networkidle")

        try:
            # Click the accept cookie button if there is one
            await page.click("text=Accetta tutti", timeout=2000)
            print("Cookie accettati")
        except:
            pass

        try:
            # Wait for CAP input
            await page.fill("input[name='cap']", "00100")
            print("CAP inserito")
            # The UI might have a button to proceed
            await page.click("button:has-text('Inizia')", timeout=2000) # example
        except Exception as e:
            print("Errore fill cap:", e)
        
        await page.wait_for_timeout(3000)
        
        # We can dump the HTML to see the current state
        html = await page.content()
        with open("page_source2.html", "w", encoding="utf-8") as f:
            f.write(html)
        
        with open("network_data.json", "w", encoding="utf-8") as f:
            json.dump(requests_data, f, indent=2)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
