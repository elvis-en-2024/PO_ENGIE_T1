import polars as pl
from pathlib import Path
from datetime import date, timedelta
import logging

from download.downloader import PortaleOfferteDownloader
from parse.parser import OfferteParser
from storage.scd2_manager import SCD2Manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
STORAGE_DIR = BASE_DIR / "data" / "storage"

def run_daily_pipeline(process_date: date):
    MAPPING_PATH = BASE_DIR / "config" / "xpath_mapping.yaml"
    parser = OfferteParser(MAPPING_PATH)
    scd2 = SCD2Manager(STORAGE_DIR)
    
    commodities = ["E", "G", "D"]
    with PortaleOfferteDownloader(RAW_DIR) as downloader:
        for comm in commodities:
            try:
                xml_file = downloader.fetch_file(process_date, comm)
                if not xml_file:
                    logger.warning(f"File per commodity {comm} in {process_date} non trovato.")
                    continue
                    
                # Parsa tutti gli XML in un array di dicts
                records = list(parser.parse(xml_file, comm))
                    
                if not records:
                    logger.warning(f"Nessun record estratto per {comm} in {process_date}")
                    continue
                    
                # Esegue il merge SCD2
                stats = scd2.process_daily_batch(records, process_date, comm)
                logger.info(f"Statistiche {comm} per {process_date}: {stats}")
                
            except Exception as e:
                logger.error(f"Errore elaborazione {comm} in {process_date}: {e}")

if __name__ == "__main__":
    # Il portale tipicamente espone i dati di "ieri" o degli ultimi giorni.
    # L'utente ha chiesto di processare lo storico di "tutti i 3 file per ciascun giorno".
    # Ipotizziamo di simulare gli ultimi 3 giorni (dal 18 al 20 agosto 2026).
    start_date = date(2026, 8, 18)
    end_date = date(2026, 8, 20)
    
    current_date = start_date
    while current_date <= end_date:
        run_daily_pipeline(current_date)
        current_date += timedelta(days=1)
