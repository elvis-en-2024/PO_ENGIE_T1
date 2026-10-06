import os
import requests
import re
from playwright.sync_api import sync_playwright
import hashlib
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
requests.packages.urllib3.disable_warnings()

def get_file_hash(content):
    return hashlib.sha256(content).hexdigest()

def is_ss(text):
    text = text.lower()
    return 'sintetic' in text or 'confrontabilit' in text

def run():
    logging.info("Recupero documenti per POSTE ITALIANE (Energia)...")
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    base_dir = os.path.join("data", "raw", "ctes", "POSTE_ITALIANE")
    
    os.environ['NODE_TLS_REJECT_UNAUTHORIZED'] = '0'
    
    pdf_links = set()
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        url = 'https://postepay.poste.it/poste-energia-luce-gas'
        logging.info(f"Analizzo pagina offerta: {url}")
        
        page.goto(url, wait_until='domcontentloaded')
        page.wait_for_timeout(5000)
        
        links = page.locator('a').element_handles()
        for link in links:
            href = link.get_attribute('href')
            text = link.text_content()
            if text: text = text.strip()
            
            if href and 'media.poste.it' in href:
                if 'condizion' in text.lower() or 'sintetic' in text.lower() or 'tecnico' in text.lower() or 'economich' in text.lower():
                    # Check for bad keywords
                    bad_keywords = ['generali', 'cgv', 'privacy']
                    if not any(k in text.lower() for k in bad_keywords):
                        doc_type = "SS" if is_ss(text) else "CTE"
                        pdf_links.add((href, doc_type))
                        
        browser.close()
        
    logging.info(f"Trovati {len(pdf_links)} documenti. Inizio download...")
    
    downloaded = 0
    for pdf_url, doc_type in pdf_links:
        try:
            r = requests.get(pdf_url, verify=False, timeout=20)
            if r.status_code == 200 and len(r.content) > 5000:
                file_hash = get_file_hash(r.content)
                ext = ".pdf"
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
            
    logging.info(f"Finito. Scaricati {downloaded} documenti per POSTE ITALIANE.")

if __name__ == "__main__":
    run()
