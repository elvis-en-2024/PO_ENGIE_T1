import os
import glob
import fitz  # PyMuPDF
import re
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

INPUT_DIR = "data/raw/ctes"
OUTPUT_FILE = "data/storage/competitors_extracted.parquet"

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
    except Exception as e:
        logging.error(f"Error reading {pdf_path}: {e}")
    return text

def parse_scheda_sintetica(text, competitor):
    """
    Usa RegEx per estrarre le info chiave dalle Schede Sintetiche ARERA.
    """
    dati = {
        'FORNITORE': competitor,
        'NOME_OFFERTA': 'Non Trovato',
        'COMMODITY': 'Sconosciuta',
        'QUOTA_FISSA': 0.0,
        'QUOTA_ENERGIA': 0.0
    }
    
    # Rilevamento Commodity
    text_lower = text.lower()
    if 'smc' in text_lower or 'gas' in text_lower:
        dati['COMMODITY'] = 'G'
    elif 'kwh' in text_lower or 'luce' in text_lower or 'energia elettrica' in text_lower:
        dati['COMMODITY'] = 'E'
        
    # Pattern RegEx tipici per Scheda Sintetica ARERA
    # 1. Nome Offerta
    nome_match = re.search(r'(?:Nome|Denominazione)\s*(?:dell\')?offerta\s*:?\s*([A-Za-z0-9\s\-]+)', text, re.IGNORECASE)
    if nome_match:
        dati['NOME_OFFERTA'] = nome_match.group(1).strip()
        
    # 2. Quota Fissa (es. "Quota fissa: 120 €/anno" o "Corrispettivo fisso annuo... 144")
    # Cerca numeri vicini a "fisso" o "commercializzazione"
    q_fissa_match = re.search(r'(?:quota\s*fissa|commercializzazione|corrispettivo\s*fisso)[\s\S]{0,50}?(\d+[\,\.]?\d*)\s*€\s*/\s*(?:anno|mese)', text, re.IGNORECASE)
    if q_fissa_match:
        val_str = q_fissa_match.group(1).replace(',', '.')
        try:
            val = float(val_str)
            # Se è al mese, moltiplica per 12
            if 'mese' in q_fissa_match.group(0).lower():
                val *= 12
            dati['QUOTA_FISSA'] = round(val, 2)
        except ValueError:
            pass

    # 3. Quota Energia (es. "Quota energia: 0,15 €/kWh")
    q_energia_match = re.search(r'(?:quota\s*energia|corrispettivo\s*energia|materia\s*energia)[\s\S]{0,50}?(\d+[\,\.]?\d+)\s*€\s*/\s*(?:kWh|Smc)', text, re.IGNORECASE)
    if q_energia_match:
        val_str = q_energia_match.group(1).replace(',', '.')
        try:
            dati['QUOTA_ENERGIA'] = round(float(val_str), 5)
        except ValueError:
            pass
            
    return dati

def main():
    pdf_files = glob.glob(f"{INPUT_DIR}/**/*.pdf", recursive=True)
    if not pdf_files:
        logging.warning(f"Nessun PDF trovato in {INPUT_DIR}.")
        return
        
    logging.info(f"Trovati {len(pdf_files)} PDF. Inizio estrazione...")
    
    all_offers = []
    
    for pdf_path in pdf_files:
        competitor = os.path.basename(os.path.dirname(pdf_path))
        text = extract_text_from_pdf(pdf_path)
        
        if not text.strip():
            continue
            
        dati = parse_scheda_sintetica(text, competitor)
        dati['FILE_SORGENTE'] = os.path.basename(pdf_path)
        
        # Filtriamo le estrazioni "vuote" o fallite
        if dati['QUOTA_FISSA'] > 0 or dati['QUOTA_ENERGIA'] > 0:
            all_offers.append(dati)
            logging.info(f"[{competitor}] Estratta: {dati['NOME_OFFERTA']} (Fisso: {dati['QUOTA_FISSA']}, Var: {dati['QUOTA_ENERGIA']})")
        else:
            logging.debug(f"[{competitor}] Skipped (prezzi non trovati): {os.path.basename(pdf_path)}")
            
    if all_offers:
        df = pd.DataFrame(all_offers)
        # Salva in parquet per la Fase 3
        df.to_parquet(OUTPUT_FILE, index=False)
        logging.info(f"Successo! {len(df)} offerte strutturate e salvate in {OUTPUT_FILE}")
    else:
        logging.warning("Nessuna offerta estratta con successo dai PDF forniti.")

if __name__ == "__main__":
    main()
