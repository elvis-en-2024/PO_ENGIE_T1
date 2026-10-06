import polars as pl
from datetime import date
from pathlib import Path
import sys

from download.downloader import PortaleOfferteDownloader
from parse.parser import OfferteParser

BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
STORAGE_DIR = BASE_DIR / "data" / "storage"
MAPPING_PATH = BASE_DIR / "config" / "xpath_mapping.yaml"

def main():
    target_date = date(2026, 8, 20)
    commodities = ["E", "G", "D"]
    all_records = []
    
    print(f"Inizio procedura di verifica per {target_date}...")
    
    parser = OfferteParser(MAPPING_PATH)
    
    with PortaleOfferteDownloader(RAW_DIR) as downloader:
        for comm in commodities:
            print(f"\n--- Scaricamento ed estrazione Commodity {comm} ---")
            xml_file = downloader.fetch_file(target_date, comm)
            if not xml_file:
                print(f"File per commodity {comm} non trovato.")
                continue
                
            print(f"File scaricato: {xml_file}")
            print("Avvio parsing...")
            records = list(parser.parse(xml_file, comm))
            print(f"Estratte {len(records)} offerte.")
            all_records.extend(records)
            
    if not all_records:
        print("Nessun record estratto. Esco.")
        return
        
    print(f"\nGenerazione CSV di verifica totale: {len(all_records)} righe.")
    
    # Mappiamo su Polars con type inference estesa
    df = pl.DataFrame(all_records, infer_schema_length=10000)
    
    csv_path = STORAGE_DIR / f"verifica_piatta_{target_date.strftime('%Y%m%d')}.csv"
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    df.write_csv(csv_path)
    
    print(f"\nFatto! Il file è disponibile in: {csv_path}")

if __name__ == "__main__":
    main()
