import polars as pl
from pathlib import Path
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
LAKE_DIR = BASE_DIR / "data" / "lake"
STORAGE_DIR = BASE_DIR / "data" / "storage"

def main():
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Raccogliamo tutti i batch
    batch_files = list(LAKE_DIR.glob("batch_*.parquet"))
    logger.info(f"Trovati {len(batch_files)} file batch da unificare.")
    
    if not batch_files:
        logger.warning("Nessun file batch trovato!")
        return

    # Usiamo LazyFrame e sink_parquet per elaborare in streaming senza esplodere la RAM
    lazy_frames = [pl.scan_parquet(f) for f in batch_files]
    
    final_path = STORAGE_DIR / "storico_completo.parquet"
    logger.info("Avvio unificazione in streaming (Basso consumo RAM)...")
    
    # Concateniamo diagonalmente per coprire tutte le colonne possibili
    pl.concat(lazy_frames, how="diagonal").sink_parquet(final_path)
    
    logger.info(f"Salvataggio completato con successo in {final_path}")
    
    # Pulizia opzionale dei batch
    for f in batch_files:
        os.remove(f)
    logger.info("File batch temporanei eliminati.")

if __name__ == "__main__":
    main()
