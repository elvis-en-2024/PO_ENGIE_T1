from playwright.sync_api import sync_playwright
import os

os.environ['NODE_TLS_REJECT_UNAUTHORIZED'] = '0'

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('https://heracomm.gruppohera.it/casa/offerte-luce-gas/hera-impronta-zero', wait_until='networkidle')
    page.wait_for_timeout(5000)
    page.screenshot(path="hera_impronta_zero.png", full_page=True)
    browser.close()
