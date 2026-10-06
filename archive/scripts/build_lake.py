import polars as pl
from pathlib import Path
import logging
from datetime import datetime

from parse.parser import OfferteParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
LAKE_DIR = BASE_DIR / "data" / "lake"

def main():
    MAPPING_PATH = BASE_DIR / "config" / "xpath_mapping.yaml"
    parser = OfferteParser(MAPPING_PATH)
    
    LAKE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Cerchiamo tutti i file .gz estratti in precedenza
    files = list(RAW_DIR.rglob("*.gz"))
    logger.info(f"Trovati {len(files)} file compressi da processare.")
    
    batch_records = []
    
    for idx, xml_file in enumerate(files):
        # Esempio percorso: data/raw/E/2023/01/PO_Offerte_E_MLIBERO_20230101.xml.gz
        commodity = xml_file.parent.parent.parent.name
        
        # Estrai data dal nome file
        filename = xml_file.name
        date_str = filename.split('_')[-1].split('.')[0]
        try:
            process_date = datetime.strptime(date_str, "%Y%m%d").date()
        except ValueError:
            continue
            
        logger.info(f"[{idx+1}/{len(files)}] Parsing {commodity} - {process_date}")
        
        try:
            records = list(parser.parse(xml_file, commodity))
            # Aggiungiamo data rilevazione
            for r in records:
                r["DATA_RILEVAZIONE"] = process_date
                
            # Convertiamo tutto in stringa (tranne data) per sicurezza type-inference
            for r in records:
                for k, v in r.items():
                    if k != "DATA_RILEVAZIONE":
                        r[k] = str(v) if v is not None else None
                        
            batch_records.extend(records)
            
        except Exception as e:
            logger.error(f"Errore parsing {xml_file}: {e}")
            
        # Ogni 300 file (~1 mese), scarichiamo su parquet per non saturare la RAM
        if (idx + 1) % 100 == 0 or (idx + 1) == len(files):
            if batch_records:
                # Inferiamo lo schema in modo sicuro assegnando Utf8 a tutto tranne la data
                all_keys = set()
                for r in batch_records:
                    all_keys.update(r.keys())
                    
                safe_schema = {k: pl.Utf8 for k in all_keys}
                if "DATA_RILEVAZIONE" in safe_schema:
                    safe_schema["DATA_RILEVAZIONE"] = pl.Date
                    
                df = pl.DataFrame(batch_records, schema=safe_schema)
                # Salva partizionato
                df.write_parquet(
                    LAKE_DIR / f"batch_{idx}.parquet",
                )
                logger.info(f"Salvato batch {idx} con {df.height} righe.")
                batch_records.clear()

if __name__ == "__main__":
    main()
