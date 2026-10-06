"""Aggiornamento quotidiano dello storico offerte.

    python -m scripts.update_daily                  # giorni mancanti negli ultimi 30
    python -m scripts.update_daily --date 2026-09-24
    python -m scripts.update_daily --giorni 90      # recupero buchi più vecchi

Per ogni commodity scarica e parsa i giorni assenti dallo storico partizionato
(data/storage/storico), li scrive nel file del mese (rielaborare un giorno ne
sostituisce le righe, non le duplica) e rigenera il parquet della dashboard.
Scarica anche i parametri di calcolo del Portale (data/raw/parametri), letti
da engine.parametri_po per la parte regolata della SAS, le quotazioni forward
GME per le offerte variabili (data/raw/gme) e, una volta al giorno, PPE e CCR
dal dettaglio offerta del Portale (data/processed/componenti_portale.json).
"""
import argparse
import logging
from datetime import date, timedelta

from download import gme
from download.downloader import PortaleOfferteDownloader
from engine import forward
from parse.parser import OfferteParser
from storage import daily_store as ds

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RAW_DIR = ds.BASE_DIR / "data" / "raw"
COMMODITIES = ["E", "G", "D"]


def giorni_da_elaborare(commodity: str, fino_a: date, giorni: int) -> list[date]:
    presenti = ds.giorni_presenti(commodity)
    finestra = (fino_a - timedelta(days=n) for n in range(giorni))
    return sorted(g for g in finestra if g not in presenti)


def aggiorna_stime(oggi: date) -> None:
    """Forward GME e componenti del Portale. Un errore non blocca l'aggiornamento
    delle offerte: il motore usa gli ultimi valori disponibili."""
    try:
        n = gme.aggiorna(oggi)
        stima = forward.stima(oggi)
        logger.info(f"Forward GME: {n} sessioni nuove; stima {stima and stima['ee']} "
                    f"(rilevazione {stima and stima['rilevazione']})")
    except Exception as e:
        logger.error(f"Errore forward GME: {e}")
    if forward.carica_componenti().get("rilevato") == oggi.isoformat():
        return
    try:
        from scripts.rileva_componenti_portale import rileva
        rileva()
    except Exception as e:
        logger.error(f"Errore rilevazione PPE/CCR dal Portale: {e}")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--date", type=str, help="Forza (rielabora) una data YYYY-MM-DD", default=None)
    parser.add_argument("--giorni", type=int, default=30,
                        help="Ampiezza della finestra in cui cercare giorni mancanti")
    args = parser.parse_args()

    ds.pulisci_tmp()
    # il file del giorno è pubblicato in mattinata: se manca ancora è solo un warning
    oggi = date.today()
    aggiorna_stime(oggi)
    if args.date:
        piano = {c: [date.fromisoformat(args.date)] for c in COMMODITIES}
    else:
        piano = {c: giorni_da_elaborare(c, oggi, args.giorni) for c in COMMODITIES}

    if not any(piano.values()):
        logger.info("Nessun giorno mancante. Lo storico e' gia' aggiornato.")
        return

    parser_obj = OfferteParser(ds.MAPPING_PATH)
    n_righe, non_pubblicati = 0, []
    with PortaleOfferteDownloader(RAW_DIR) as downloader:
        for comm, giorni in piano.items():
            if giorni:
                logger.info(f"{comm}: giorni da elaborare {[g.isoformat() for g in giorni]}")
            nuovi = []
            for g in giorni:
                try:
                    xml_file = downloader.fetch_file(g, comm)
                    if not xml_file:
                        non_pubblicati.append((comm, g))
                        continue
                    df = ds.parse_giorno(xml_file, comm, g, parser_obj)
                    nuovi.append(df)
                    logger.info(f"Estratte {df.height} offerte per {comm} in {g}.")
                except Exception as e:
                    logger.error(f"Errore elaborazione di {comm} per {g}: {e}")
            ds.scrivi_giorni(nuovi, comm)
            n_righe += sum(df.height for df in nuovi)
            if comm in ("E", "G"):
                for g in giorni:
                    try:
                        downloader.fetch_parametri(g, comm)
                    except Exception as e:
                        logger.error(f"Errore download parametri {comm} per {g}: {e}")

    if non_pubblicati:
        logger.warning("File non pubblicati sul portale: "
                       + ", ".join(f"{c} {g}" for c, g in non_pubblicati))
    if n_righe:
        ds.genera_dashboard()
    logger.info(f"Aggiornamento completato: {n_righe} righe scritte. "
                f"Ultima rilevazione: {ds.ultima_rilevazione()}")


if __name__ == "__main__":
    main()
