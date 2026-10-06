import logging
from pathlib import Path
from datetime import date, timedelta
from download.downloader import PortaleOfferteDownloader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"

def main():
    start_date = date(2025, 4, 1)
    end_date = date(2026, 7, 31)
    
    current_date = start_date
    commodities = ["E", "G", "D"]
    
    with PortaleOfferteDownloader(RAW_DIR) as downloader:
        while current_date <= end_date:
            logger.info(f"Scarico data: {current_date}")
            for comm in commodities:
                try:
                    downloader.fetch_file(current_date, comm)
                except Exception as e:
                    logger.error(f"Errore download {comm} per {current_date}: {e}")
                    
            current_date += timedelta(days=1)
            
    logger.info("Download completato!")

if __name__ == "__main__":
    main()
