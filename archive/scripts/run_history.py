import argparse
from datetime import date, timedelta
import logging
from scripts.run_pipeline import run_daily_pipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Esegui caricamento storico Portale Offerte")
    parser.add_argument("--start", type=str, required=True, help="Data inizio YYYY-MM-DD")
    parser.add_argument("--end", type=str, required=True, help="Data fine YYYY-MM-DD")
    args = parser.parse_args()
    
    start_date = date.fromisoformat(args.start)
    end_date = date.fromisoformat(args.end)
    
    current_date = start_date
    logger.info(f"Avvio elaborazione storica da {start_date} a {end_date}")
    
    while current_date <= end_date:
        logger.info(f"=== Elaborazione giorno: {current_date} ===")
        run_daily_pipeline(current_date)
        current_date += timedelta(days=1)
        
    logger.info("Elaborazione storica completata!")

if __name__ == "__main__":
    main()
