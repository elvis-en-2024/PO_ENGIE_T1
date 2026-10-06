import os
import glob
import fitz  # PyMuPDF
import json
import logging
import pandas as pd
from google import genai
from google.genai import types
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

INPUT_DIR = "data/raw/cte_competitors"
OUTPUT_FILE = "data/storage/competitors_live.parquet"

# Pydantic schema for structured extraction
class Sconto(BaseModel):
    nome: str
    valore: float
    unita: str
    condizione: str

class OffertaCTE(BaseModel):
    fornitore: str
    nome_offerta: str
    commodity: str
    quota_fissa_annua: float
    quota_energia_kwh_smc: float
    sconti: list[Sconto]

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
    except Exception as e:
        logging.error(f"Error reading {pdf_path}: {e}")
    return text

def parse_with_gemini(text, competitor_name):
    # Retrieve API key from environment
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logging.error("GEMINI_API_KEY environment variable not set.")
        return None
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Sei un assistente specializzato nell'analisi di bollette e contratti luce/gas (CTE).
    Leggi il seguente testo estratto dalle Condizioni Tecnico Economiche del fornitore {competitor_name}.
    Estrai i seguenti dati:
    - Nome dell'offerta
    - Commodity (Luce o Gas)
    - La "Quota Fissa" o "Corrispettivo fisso" o "CCV" in Euro/Anno.
    - Il prezzo dell'energia "Quota Energia" o "Materia Prima" (fissa o variabile) in Euro/kWh o Euro/Smc.
    - Eventuali sconti (es. Sconto Domiciliazione, Sconto Web, Bonus).
    
    Testo del PDF:
    {text[:8000]} # Limit to 8000 chars to save tokens if it's very long
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=OffertaCTE,
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        logging.error(f"Gemini API error for {competitor_name}: {e}")
        return None

def main():
    if not os.environ.get("GEMINI_API_KEY"):
        logging.error("🚨 ERRORE: Imposta la variabile d'ambiente GEMINI_API_KEY prima di eseguire lo script.")
        logging.error("Esempio: $env:GEMINI_API_KEY='la-tua-chiave-api'")
        return

    all_offers = []
    
    pdf_files = glob.glob(f"{INPUT_DIR}/**/*.pdf", recursive=True)
    if not pdf_files:
        logging.warning(f"Nessun file PDF trovato in {INPUT_DIR}.")
        return
        
    logging.info(f"Trovati {len(pdf_files)} PDF da processare.")
    
    for pdf_path in pdf_files:
        competitor = os.path.basename(os.path.dirname(pdf_path))
        logging.info(f"Elaborazione PDF per {competitor}: {os.path.basename(pdf_path)}")
        
        testo = extract_text_from_pdf(pdf_path)
        if not testo.strip():
            continue
            
        dati_estratti = parse_with_gemini(testo, competitor)
        
        if dati_estratti:
            # Flatten per il dataframe
            flat_offer = {
                'FORNITORE': competitor,
                'NOME_OFFERTA': dati_estratti.get('nome_offerta'),
                'COMMODITY': dati_estratti.get('commodity'),
                'QUOTA_FISSA': dati_estratti.get('quota_fissa_annua', 0.0),
                'QUOTA_ENERGIA': dati_estratti.get('quota_energia_kwh_smc', 0.0),
                'FILE_SORGENTE': os.path.basename(pdf_path)
            }
            
            # Appiattisci fino a 3 sconti
            sconti = dati_estratti.get('sconti', [])
            for i in range(min(3, len(sconti))):
                flat_offer[f'SCONTO_{i+1}_NOME'] = sconti[i].get('nome')
                flat_offer[f'SCONTO_{i+1}_VALORE'] = sconti[i].get('valore')
                
            all_offers.append(flat_offer)
            logging.info(f"Offerta estratta: {flat_offer['NOME_OFFERTA']} ({flat_offer['QUOTA_FISSA']} €/anno)")

    if all_offers:
        df = pd.DataFrame(all_offers)
        df.to_parquet(OUTPUT_FILE, index=False)
        logging.info(f"Salvato {len(df)} offerte strutturate in {OUTPUT_FILE}")
    else:
        logging.info("Nessuna offerta valida estratta.")

if __name__ == "__main__":
    main()
