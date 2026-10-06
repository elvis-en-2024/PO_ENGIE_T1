from playwright.sync_api import sync_playwright
import os

os.environ['NODE_TLS_REJECT_UNAUTHORIZED'] = '0'

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://www.aceaenergia.it/offerte-casa/acea-energia-fix")
    page.wait_for_timeout(5000)
    page.screenshot(path="acea_screenshot.png", full_page=True)
    browser.close()
