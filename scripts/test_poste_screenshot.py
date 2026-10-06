from playwright.sync_api import sync_playwright
import os

os.environ['NODE_TLS_REJECT_UNAUTHORIZED'] = '0'

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('https://postepay.poste.it/poste-energia-luce-gas', wait_until='networkidle')
    page.wait_for_timeout(5000)
    page.screenshot(path="postepay.png", full_page=True)
    browser.close()
