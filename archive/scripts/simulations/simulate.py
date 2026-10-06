import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Navigazione in corso...")
        await page.goto("https://ilportaleofferte.it/portaleOfferte/it/confronto-tariffe-prezzi-luce-gas.page", wait_until="networkidle")

        html = await page.content()
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Salvato page_source.html")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
