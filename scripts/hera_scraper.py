import os
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
import hashlib
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
requests.packages.urllib3.disable_warnings()

def get_file_hash(content):
    return hashlib.sha256(content).hexdigest()

def get_hera_offer_links():
    html = requests.get('https://heracomm.gruppohera.it/casa/offerte-luce-gas', verify=False).text
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    for a in soup.find_all(href=True):
        href = a['href']
        if 'offerte-luce-gas/' in href and not href.endswith('.pdf') and 'business' not in href:
            links.add(urljoin('https://heracomm.gruppohera.it', href))
    return list(links)

def is_ss(text, href):
    text = text.lower()
    href = href.lower()
    return 'sintetic' in text or 'sintetic' in href or 'confrontabilit' in text or 'confrontabilit' in href

def run():
    logging.info("Recupero link offerte HERA COMM...")
    offer_links = get_hera_offer_links()
    logging.info(f"Trovate {len(offer_links)} offerte.")
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    base_dir = os.path.join("data", "raw", "ctes", "HERA_COMM")
    
    os.environ['NODE_TLS_REJECT_UNAUTHORIZED'] = '0'
    
    pdf_links = set()
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        for url in offer_links:
            try:
                logging.info(f"Analizzo pagina offerta: {url}")
                page.goto(url, wait_until='networkidle')
                page.wait_for_timeout(3000) # Give Liferay time to render fragments
                html = page.content()
                soup = BeautifulSoup(html, 'html.parser')
                
                for a in soup.find_all(href=True):
                    href = a['href']
                    if '/documents/' in href and ('.pdf' in href.lower() or '.zip' in href.lower()):
                        full_url = urljoin(url, href)
                        doc_type = "SS" if is_ss(a.text, href) else "CTE"
                        pdf_links.add((full_url, doc_type))
            except Exception as e:
                logging.error(f"Errore su {url}: {e}")
                
        browser.close()
        
    logging.info(f"Trovati {len(pdf_links)} documenti (PDF/ZIP). Inizio download...")
    
    downloaded = 0
    for pdf_url, doc_type in pdf_links:
        try:
            r = requests.get(pdf_url, verify=False, timeout=20)
            if r.status_code == 200 and len(r.content) > 5000:
                file_hash = get_file_hash(r.content)
                ext = ".zip" if ".zip" in pdf_url.lower() else ".pdf"
                filename = f"{today_str}_{file_hash[:8]}{ext}"
                subfolder = os.path.join(base_dir, doc_type)
                os.makedirs(subfolder, exist_ok=True)
                
                filepath = os.path.join(subfolder, filename)
                if not os.path.exists(filepath):
                    with open(filepath, 'wb') as f:
                        f.write(r.content)
                    downloaded += 1
        except Exception as e:
            logging.error(f"Errore download {pdf_url}: {e}")
            
    logging.info(f"Finito. Scaricati {downloaded} documenti per HERA COMM.")

if __name__ == "__main__":
    run()
