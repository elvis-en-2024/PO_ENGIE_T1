import os
import time
import requests
import logging
from duckduckgo_search import DDGS
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

COMPETITORS = {
    'A2A': 'a2aenergia.eu',
    'ACEA': 'acea.it',
    'E.ON': 'eon-energia.com',
    'EDISON': 'edisonenergia.it',
    'ENEL': 'enel.it',
    'ENGIE': 'casa.engie.it',
    'FASTWEB': 'fastweb.it',
    'HERA COMM': 'heracomm.gruppohera.it',
    'ILLUMIA': 'illumia.it',
    'IREN': 'irenlucegas.it',
    'NeN': 'nen.it',
    'OCTOPUS': 'octopusenergy.it',
    'PLENITUDE': 'eniplenitude.com',
    'POSTE ITALIANE': 'poste.it',
    'SORGENIA': 'sorgenia.it',
    'WIND': 'windtre.it'
}

OUTPUT_DIR = "data/raw/cte_competitors"

def search_pdfs(domain, query_term):
    query = f'site:{domain} filetype:pdf "{query_term}" ("luce" OR "gas" OR "energia")'
    results = []
    logging.info(f"Searching: {query}")
    try:
        with DDGS() as ddgs:
            # Get up to 5 results per competitor to avoid spam
            for r in ddgs.text(query, max_results=5):
                url = r.get('href')
                if url and url.lower().endswith('.pdf'):
                    results.append(url)
        return results
    except Exception as e:
        logging.error(f"Search failed for {domain}: {e}")
        return []

def download_pdf(url, output_path):
    try:
        # Add basic headers to prevent 403 Forbidden
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        logging.warning(f"Failed to download {url}: {e}")
        return False

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for comp_name, domain in COMPETITORS.items():
        comp_dir = os.path.join(OUTPUT_DIR, comp_name.replace(' ', '_'))
        os.makedirs(comp_dir, exist_ok=True)
        
        logging.info(f"--- Processing {comp_name} ({domain}) ---")
        
        # Searching for "Condizioni Tecnico Economiche"
        pdf_urls = search_pdfs(domain, "Condizioni Tecnico Economiche")
        
        if not pdf_urls:
            logging.info(f"No CTE PDFs found for {comp_name}. Trying alternative keywords...")
            # Try alternative keywords
            pdf_urls = search_pdfs(domain, "Condizioni Economiche")
            
        if not pdf_urls:
            logging.info(f"Still no PDFs found for {comp_name}.")
            continue
            
        logging.info(f"Found {len(pdf_urls)} PDFs for {comp_name}. Downloading...")
        
        for i, url in enumerate(pdf_urls):
            # Parse filename from URL
            filename = os.path.basename(urlparse(url).path)
            if not filename or not filename.endswith('.pdf'):
                filename = f"cte_document_{i+1}.pdf"
                
            output_path = os.path.join(comp_dir, filename)
            
            # Skip if already downloaded
            if os.path.exists(output_path):
                logging.info(f"Already exists: {filename}")
                continue
                
            logging.info(f"Downloading {filename}...")
            if download_pdf(url, output_path):
                logging.info("Success.")
            
            # Sleep to respect rate limits
            time.sleep(2)

if __name__ == "__main__":
    main()
