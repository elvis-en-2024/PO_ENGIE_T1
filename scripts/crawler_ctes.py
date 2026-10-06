import os
import json
import hashlib
import requests
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, urlparse
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CONFIG_FILE = "data/config/config_competitors.json"
OUTPUT_DIR = "data/raw/ctes"
HISTORY_FILE = "data/crawling_history/crawling_report_"

def get_file_hash(content):
    return hashlib.sha256(content).hexdigest()

def is_valid_offer_link(href, base_url):
    if not href: return False
    parsed_href = urlparse(href)
    parsed_base = urlparse(base_url)
    if parsed_href.netloc and parsed_href.netloc != parsed_base.netloc:
        return False
    href_lower = href.lower()
    blacklisted = ['login', 'privacy', 'assistenza', 'chi-siamo', 'faq', 'cookie', 
                   'supporto', 'contatti', 'lavora-con-noi', 'investitori', 'media',
                   'condizioni-generali', 'sostenibilita']
    for bad_word in blacklisted:
        if bad_word in href_lower:
            return False
    if href_lower.endswith(('.pdf', '.jpg', '.png', '.css', '.js')):
        return False
    if len(href_lower) < 5 or href_lower == '/':
        return False
    return True

def is_valid_cte_pdf(href, text=""):
    if not href: return False, ""
    href_lower = href.lower()
    text_lower = text.lower() if text else ""
    
    is_salesforce = 'salesforce.com/sfc/p/' in href_lower
    is_acea = 'visualizzadocumento' in href_lower
    is_edison = 'getbusinessdoc.ashx' in href_lower
    
    if not href_lower.endswith('.pdf') and '.pdf?' not in href_lower and not is_salesforce and not is_acea and not is_edison:
        return False, ""
        
    is_ss = 'sintetic' in href_lower or 'sintetic' in text_lower or 'confrontabilit' in href_lower or 'confrontabilit' in text_lower or 'schede_' in href_lower
    is_cte = 'cte' in href_lower or 'tecnico' in href_lower or 'economich' in href_lower or 'condizion' in href_lower or \
             'cte' in text_lower or 'tecnico' in text_lower or 'economich' in text_lower or 'condizion' in text_lower or 'condeco_' in href_lower
             
    is_iren = 'iren' in href_lower and ('visualizza' in text_lower or 'scarica' in text_lower)
             
    if is_salesforce or is_acea or is_edison or is_iren:
        # If it's an obfuscated link, assume it's valid, and try to guess type. If neither, default to CTE.
        if not is_ss and not is_cte:
            is_cte = True
            
    is_valid = is_ss or is_cte
    
    bad_keywords = ['generali', 'cgv', 'privacy', 'assicurazione', 'domiciliazione', 'modul']
    is_bad = any(k in href_lower or k in text_lower for k in bad_keywords)
    
    if not is_valid or is_bad:
        return False, ""
        
    doc_type = "SS" if is_ss else "CTE"
    return True, doc_type

def run_crawler():
    requests.packages.urllib3.disable_warnings()
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
        
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs("data/crawling_history", exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")
    report = {}
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for comp_name, urls in config.items():
        logging.info(f"=== {comp_name} ===")
        comp_dir = os.path.join(OUTPUT_DIR, comp_name.replace(' ', '_'))
        os.makedirs(comp_dir, exist_ok=True)
        
        comp_report = {'unique_offer_links_found': [], 'cte_pdfs_found': [], 'cte_pdfs_downloaded': 0}
        
        all_offer_links = set()
        for index_url in urls:
            try:
                response = requests.get(index_url, headers=headers, timeout=15, verify=False)
                soup = BeautifulSoup(response.text, 'html.parser')
                for a in soup.find_all(href=True):
                    href = a['href']
                    if is_valid_offer_link(href, index_url):
                        full_url = urljoin(index_url, href).split('#')[0]
                        all_offer_links.add(full_url)
            except Exception as e:
                logging.error(f"Errore LEVEL 1 per {index_url}: {e}")
                
        comp_report['unique_offer_links_found'] = list(all_offer_links)
        logging.info(f"Trovate {len(all_offer_links)} potenziali pagine offerta.")
        
        all_pdf_links = set()
        for offer_url in list(all_offer_links):
            try:
                response = requests.get(offer_url, headers=headers, timeout=15, verify=False)
                html_text = response.text
                soup = BeautifulSoup(html_text, 'html.parser')
                
                # 1. Cerca link standard HTML
                for a in soup.find_all(href=True):
                    href = a['href']
                    valid, doc_type = is_valid_cte_pdf(href, a.text)
                    if valid:
                        all_pdf_links.add((urljoin(offer_url, href), doc_type))
                        
                # 2. Cerca link JSON embedded (HACK per A2A, EDISON e altri)
                json_links = re.findall(r'"(?:url_scheda_sintetica|url|DocumentLink)"\s*:\s*"([^"]+)"', html_text, re.IGNORECASE)
                for jl in json_links:
                    clean_url = jl.replace('\\/', '/')
                    valid, doc_type = is_valid_cte_pdf(clean_url, "scheda sintetica json")
                    if valid:
                        all_pdf_links.add((clean_url, doc_type))
                        
            except Exception as e:
                logging.debug(f"Errore LEVEL 2 per {offer_url}: {e}")
                
        comp_report['cte_pdfs_found'] = [u for u, t in all_pdf_links]
        logging.info(f"Trovati {len(all_pdf_links)} potenziali PDF (CTE/Sintetiche).")
        
        for pdf_url, doc_type in list(all_pdf_links):
            try:
                r = requests.get(pdf_url, headers=headers, timeout=15, verify=False)
                if r.status_code == 200 and len(r.content) > 10000:
                    file_hash = get_file_hash(r.content)
                    filename = f"{today_str}_{file_hash[:8]}.pdf"
                    
                    # Create subfolder based on doc_type (CTE or SS)
                    subfolder = os.path.join(comp_dir, doc_type)
                    os.makedirs(subfolder, exist_ok=True)
                    filepath = os.path.join(subfolder, filename)
                    
                    if not os.path.exists(filepath):
                        with open(filepath, 'wb') as f:
                            f.write(r.content)
                        comp_report['cte_pdfs_downloaded'] += 1
            except Exception as e:
                logging.error(f"Errore download PDF {pdf_url}: {e}")
                
        logging.info(f"Scaricati {comp_report['cte_pdfs_downloaded']} PDF per {comp_name}.")
        report[comp_name] = comp_report

    with open(f"{HISTORY_FILE}{today_str}.json", 'w') as f:
        json.dump(report, f, indent=4)

if __name__ == "__main__":
    run_crawler()
