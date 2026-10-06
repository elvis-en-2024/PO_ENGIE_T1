"""Ricostruisce lo storico partizionato dai file raw e rigenera il parquet
di compatibilità storico_2026_full.

    python scripts/rebuild_storico.py --anni 2025 2026 [--workers 6] [--force]

Senza --force i giorni già presenti nello storico vengono saltati: lo script
si può interrompere e rilanciare.
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from storage import daily_store as ds  # noqa: E402

RAW_DIR = ds.BASE_DIR / "data" / "raw"
COMMODITIES = ("E", "G", "D")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("rebuild_storico")


def _elabora_mese(commodity: str, files: list[str]):
    """Un worker per (commodity, mese): nessun file scritto da due processi."""
    from parse.parser import OfferteParser
    logging.getLogger("parse.flattener").setLevel(logging.ERROR)
    parser = OfferteParser(ds.MAPPING_PATH)
    giorni, errori = [], []
    for f in files:
        try:
            giorni.append(ds.parse_giorno(Path(f), commodity, ds.data_da_nome_file(Path(f)), parser))
        except Exception as e:  # un file corrotto non blocca il mese
            errori.append((f, repr(e)))
    ds.scrivi_giorni(giorni, commodity)
    return len(files), sum(g.height for g in giorni), errori


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--anni", nargs="+", type=int, default=[2025, 2026])
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--force", action="store_true", help="rielabora anche i giorni già presenti")
    ap.add_argument("--solo-dashboard", action="store_true")
    args = ap.parse_args()

    if not args.solo_dashboard:
        ds.pulisci_tmp()
        mesi = defaultdict(list)
        for c in COMMODITIES:
            presenti = set() if args.force else ds.giorni_presenti(c)
            for anno in args.anni:
                for f in sorted((RAW_DIR / c / str(anno)).rglob("*.xml*")):
                    g = ds.data_da_nome_file(f)
                    if g and g not in presenti:
                        mesi[(c, g.year, g.month)].append(str(f))
        n_file = sum(len(v) for v in mesi.values())
        logger.info("Da elaborare: %d file in %d mesi", n_file, len(mesi))

        t0, fatti, errori = time.time(), 0, []
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(_elabora_mese, c, files): (c, a, m)
                    for (c, a, m), files in mesi.items()}
            for fut in as_completed(futs):
                c, a, m = futs[fut]
                try:
                    nf, nr, err = fut.result()
                    fatti += nf
                    errori += err
                    el = time.time() - t0
                    logger.info("%s %d-%02d: %d file, %d righe | %d/%d (ETA %.0fs)",
                                c, a, m, nf, nr, fatti, n_file,
                                el / fatti * (n_file - fatti))
                except Exception as e:
                    logger.error("Errore su %s %d-%02d: %s", c, a, m, e)
        for f, e in errori:
            logger.error("File in errore: %s (%s)", f, e)

    ds.genera_dashboard(anni_inizio=args.anni)


if __name__ == "__main__":
    main()
