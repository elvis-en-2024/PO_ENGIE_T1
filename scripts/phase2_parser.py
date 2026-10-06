import os
import glob
import re
import pandas as pd
from markitdown import MarkItDown
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_competitor_rules():
    """
    Ritorna un dizionario con le regex specifiche per ogni competitor.
    Per ogni competitor abbiamo:
    - 'luce_fissa': regex per il prezzo fisso energia
    - 'luce_variabile_spread': regex per lo spread sul PUN
    - 'luce_ccv': regex per la quota fissa annua (CCV)
    - 'gas_fissa': regex per il prezzo fisso gas
    - 'gas_variabile_spread': regex per lo spread sul PSV
    - 'gas_ccv': regex per la quota fissa annua gas
    """
    return {
        'E.ON': {
            'luce_variabile_spread': r'PUN GME \+\s*([\d,]+)\s*(?:€|euro)/kWh',
            'luce_ccv': r'Corrispettivo Annuo[\s\S]{1,100}?([\d,]+)\s*(?:€|euro)/POD/anno',
        },
        'ENEL': {
            'luce_fissa': r'componente energia comprensiva delle perdite di rete pari a\s*([\d,]+)\s*(?:€|euro)/KWh',
            'luce_ccv': r'CCV luce\)? pari a\s*([\d,]+)\s*(?:€|euro)/POD/anno',
            'gas_fissa': r'componente materia prima gas pari a\s*([\d,]+)\s*(?:€|euro)/Smc',
            'gas_ccv': r'CCV gas\)? pari a\s*([\d,]+)\s*(?:€|euro)/PDR/anno'
        },
        'IREN': {
            'luce_fissa': r'Prezzo\s*Energia[\s\S]{1,50}?([\d,]+)\s*(?:€|euro)/kWh',
            'luce_variabile_spread': r'PUN\s*\+\s*([\d,]+)\s*(?:€|euro)/kWh',
            'luce_ccv': r'Corrispettivo di commercializzazione[\s\S]{1,50}?([\d,]+)\s*(?:€|euro)/POD',
        },
        'A2A': {
            'luce_ccv': r'Commercializzazione[\s\S]{1,100}?([\d,.]+)\s*(?:€|euro|\'|)/anno',
            'luce_variabile_spread': r'PUN[\s\S]{1,100}?\+\s*([\d,.]+)\s*(?:€|euro|\'|)/kWh',
        },
        'POSTE_ITALIANE': {
            'luce_ccv': r'commercializzazione[\s\S]{1,100}?([\d,.]+)\s*(?:€|euro|\'|)/PoD',
            'luce_fissa': r'Componente Energia[\s\S]{1,100}?([\d,.]+)\s*(?:€|euro|\'|)/kWh'
        },
        'NeN': {
            'luce_ccv': r'quota fissa.*?([\d,.]+)\s*(?:€|euro|\'|)',
            'luce_fissa': r'([\d,.]+)\s*(?:€|euro|\'|)/kWh'
        },
        'OCTOPUS': {
            'luce_ccv': r'commercializzazione[\s\S]{1,100}?([\d,.]+)\s*(?:€|euro|\'|)/anno',
            'luce_fissa': r'([\d,.]+)\s*(?:€|euro|\'|)/kWh'
        },
        'ILLUMIA': {
            'luce_ccv': r'commercializzazione[\s\S]{1,100}?([\d,.]+)\s*(?:€|euro|\'|)',
            'luce_variabile_spread': r'PUN[\s\S]{1,100}?\+\s*([\d,.]+)\s*(?:€|euro|\'|)'
        },
        'SORGENIA': {
            'luce_ccv': r'commercializzazione[\s\S]{1,100}?([\d,.]+)\s*(?:€|euro|\'|)',
            'luce_variabile_spread': r'PUN[\s\S]{1,100}?\+\s*([\d,.]+)\s*(?:€|euro|\'|)'
        },
        'WIND': {
            'luce_ccv': r'commercializzazione[\s\S]{1,100}?([\d,.]+)\s*(?:€|euro|\'|)',
            'luce_variabile_spread': r'PUN[\s\S]{1,100}?\+\s*([\d,.]+)\s*(?:€|euro|\'|)'
        },
        'FASTWEB': {
            'luce_ccv': r'commercializzazione[\s\S]{1,100}?([\d,.]+)\s*(?:€|euro|\'|)',
            'luce_variabile_spread': r'PUN[\s\S]{1,100}?\+\s*([\d,.]+)\s*(?:€|euro|\'|)'
        },
        'EDISON': {
            'luce_ccv': r'commercializzazione[\s\S]{1,100}?([\d,.]+)\s*(?:€|euro|\'|)',
            'luce_variabile_spread': r'PUN[\s\S]{1,100}?\+\s*([\d,.]+)\s*(?:€|euro|\'|)'
        },
        'ACEA': {
            'luce_ccv': r'QVD[\s\S]{1,100}?([\d,.]+)',
            'luce_variabile_spread': r'PUN[\s\S]{1,100}?\+\s*([\d,.]+)\s*(?:€|euro|\'|)'
        },
        'HERA_COMM': {
            'luce_ccv': r'commercializzazione[\s\S]{1,100}?([\d,.]+)\s*(?:€|euro|\'|)',
            'luce_variabile_spread': r'PUN[\s\S]{1,100}?\+\s*([\d,.]+)\s*(?:€|euro|\'|)'
        },
        'PLENITUDE': {
            'luce_ccv': r'commercializzazione[\s\S]{1,100}?([\d,.]+)\s*(?:€|euro|\'|)',
            'luce_variabile_spread': r'PUN[\s\S]{1,100}?\+\s*([\d,.]+)\s*(?:€|euro|\'|)'
        }
    }

def is_valid_energy_doc(text):
    text_lower = text.lower()
    keywords = ['pun', 'psv', 'corrispettivo', 'commercializzazione', 'dispbt', 'materia energia', 'quota fissa', 'smc', 'kwh']
    matches = sum(1 for k in keywords if k in text_lower)
    # Se contiene almeno 2 parole chiave, è molto probabile che sia un CTE luce/gas e non un contratto fibra/caldaia
    return matches >= 2

def extract_data(text, rules):
    results = {}
    for key, pattern in rules.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            results[key] = match.group(1)
    return results

def run_parser():
    md = MarkItDown()
    base_dir = r'data\raw\ctes'
    
    rules_dict = get_competitor_rules()
    
    all_data = []
    
    for competitor in os.listdir(base_dir):
        comp_dir = os.path.join(base_dir, competitor)
        if not os.path.isdir(comp_dir): continue
        
        # Cerca PDF
        pdfs = glob.glob(os.path.join(comp_dir, '**', '*.pdf'), recursive=True)
        if not pdfs:
            continue
            
        logging.info(f"Analizzo {competitor} ({len(pdfs)} PDF trovati)")
        
        rules = rules_dict.get(competitor, {})
        
        valid_pdfs_found = 0
        for pdf in pdfs:
            if valid_pdfs_found >= 1: # Analizziamo solo il primo PDF valido per competitor come test
                break
                
            try:
                res = md.convert(pdf)
                text = res.text_content
                
                if not is_valid_energy_doc(text):
                    continue
                    
                valid_pdfs_found += 1
                logging.info(f"  [+] Documento Valido Trovato: {os.path.basename(pdf)}")
                
                if rules:
                    extracted = extract_data(text, rules)
                    if extracted:
                        logging.info(f"      Estratti: {extracted}")
                        extracted['competitor'] = competitor
                        extracted['file'] = os.path.basename(pdf)
                        all_data.append(extracted)
                    else:
                        logging.info(f"      Nessun dato estratto con le regole attuali. Necessario raffinare la regex.")
                        lines = text.split('\n')
                        printed = 0
                        for i, line in enumerate(lines):
                            if printed >= 2: break
                            if 'pun ' in line.lower() or 'quota fissa' in line.lower() or 'commercializzazione' in line.lower() or '€/kwh' in line.lower():
                                snippet = " ".join(lines[max(0, i-1):i+2]).strip()
                                logging.info(f"        Snippet: {snippet[:150]}")
                                printed += 1
                else:
                    logging.info(f"      Nessuna regola definita per {competitor}. Stampo contesto PUN/Fissa per creare la regola:")
                    # Snippet extraction per aiutare a creare la regola
                    lines = text.split('\n')
                    for i, line in enumerate(lines):
                        if 'PUN' in line or 'commercializzazione' in line.lower() or 'quota fissa' in line.lower():
                            snippet = " ".join(lines[max(0, i-1):i+2]).strip()
                            if len(snippet) > 10:
                                logging.info(f"        Snippet: {snippet[:150]}")
                                break # Solo uno per non inondare
                                
            except Exception as e:
                logging.error(f"  Errore parsing {pdf}: {e}")
                
    if all_data:
        df = pd.DataFrame(all_data)
        os.makedirs('data/processed', exist_ok=True)
        df.to_csv('data/processed/estratti_fase2_test.csv', index=False)
        logging.info("\nRisultati estratti:\n" + str(df))

if __name__ == "__main__":
    run_parser()
