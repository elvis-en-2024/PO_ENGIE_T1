from playwright.sync_api import sync_playwright
import os

os.environ['NODE_TLS_REJECT_UNAUTHORIZED'] = '0'

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://www.edisonenergia.it/edison/casa/luce/edison-sweet-luce")
    page.wait_for_timeout(5000)
    page.screenshot(path="edison_sweet_luce.png", full_page=True)
    browser.close()
