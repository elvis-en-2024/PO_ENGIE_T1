import argparse
import logging
from datetime import date, timedelta
from pathlib import Path
import sys
import json

from download.downloader import PortaleOfferteDownloader
from parse.parser import OfferteParser
from storage.scd2_manager import SCD2Manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("po_etl")

BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
STORAGE_DIR = BASE_DIR / "data" / "storage"
MAPPING_PATH = BASE_DIR / "config" / "xpath_mapping.yaml"

def run_pipeline_for_date(target_date: date, commodity: str, downloader: PortaleOfferteDownloader, parser: OfferteParser, scd2: SCD2Manager):
    logger.info(f"--- Inizio pipeline per {target_date} Commodity {commodity} ---")
    
    xml_file = downloader.fetch_file(target_date, commodity)
    if not xml_file:
        logger.info("Nessun file scaricato, skip elaborazione SCD2.")
        return
        
    logger.info("Estrazione in streaming...")
    records = list(parser.parse(xml_file, commodity))
    logger.info(f"Estratte {len(records)} offerte dal file.")
    
    stats = scd2.process_daily_batch(records, target_date, commodity)
    
    manifest_path = STORAGE_DIR / f"manifest_{commodity}_{target_date.strftime('%Y%m%d')}.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Statistiche SCD2: {stats}. Manifest salvato.")

def cmd_daily():
    target_date = date.today()
    logger.info(f"Avvio job giornaliero per il {target_date}")
    
    parser = OfferteParser(MAPPING_PATH)
    scd2 = SCD2Manager(STORAGE_DIR)
    
    with PortaleOfferteDownloader(RAW_DIR) as downloader:
        for commodity in ["E", "G", "D"]:
            run_pipeline_for_date(target_date, commodity, downloader, parser, scd2)

def cmd_backfill(start_date: str, end_date: str, commodity: str):
    start_d = date.fromisoformat(start_date)
    end_d = date.fromisoformat(end_date)
    logger.info(f"Avvio backfill dal {start_d} al {end_d} per commodity {commodity}")
    
    parser = OfferteParser(MAPPING_PATH)
    scd2 = SCD2Manager(STORAGE_DIR)
    
    with PortaleOfferteDownloader(RAW_DIR) as downloader:
        current_d = start_d
        while current_d <= end_d:
            run_pipeline_for_date(current_d, commodity, downloader, parser, scd2)
            current_d += timedelta(days=1)

def cmd_simula():
    logger.info("Funzione simulazione (Fase 2) non ancora implementata a causa di documenti PDF mancanti.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ETL e Pricing Engine per Portale Offerte")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    parser_daily = subparsers.add_parser("daily", help="Job giornaliero")
    
    parser_backfill = subparsers.add_parser("backfill", help="Backfill storico")
    parser_backfill.add_argument("--start", required=True, help="Data inizio (YYYY-MM-DD)")
    parser_backfill.add_argument("--end", required=True, help="Data fine (YYYY-MM-DD)")
    parser_backfill.add_argument("--commodity", choices=["E", "G", "D"], default="E")
    
    parser_simula = subparsers.add_parser("simula", help="Simula ranking offerta")
    
    args = parser.parse_args()
    
    if args.command == "daily":
        cmd_daily()
    elif args.command == "backfill":
        cmd_backfill(args.start, args.end, args.commodity)
    elif args.command == "simula":
        cmd_simula()
