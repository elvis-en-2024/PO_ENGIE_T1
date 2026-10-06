"""Storico partizionato delle offerte.

Layout: data/storage/storico/commodity={E|G|D}/anno={YYYY}/{YYYY-MM}.parquet

Un file per (commodity, mese), ordinato per offerta e data: la ripetizione
delle offerte giorno su giorno comprime circa 10 volte meglio dei file
giornalieri. Scrivere un giorno sostituisce le sue righe nel file del mese,
quindi rielaborare un giorno non crea duplicati e l'aggiornamento quotidiano
riscrive solo il mese corrente.
"""
from __future__ import annotations

import logging
import os
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import duckdb
import polars as pl

from parse.parser import OfferteParser

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[1]
STORICO_DIR = BASE_DIR / "data" / "storage" / "storico"
DASHBOARD_PATH = BASE_DIR / "data" / "processed" / "storico_2026_full.parquet"
MAPPING_PATH = BASE_DIR / "config" / "xpath_mapping.yaml"

CHIAVE_OFFERTA = ["PIVA_UTENTE", "COD_OFFERTA"]
_RE_DATA_FILE = re.compile(r"_(\d{8})\.xml(\.gz)?$")


def data_da_nome_file(path: Path) -> date | None:
    m = _RE_DATA_FILE.search(Path(path).name)
    return datetime.strptime(m.group(1), "%Y%m%d").date() if m else None


def path_mese(commodity: str, anno: int, mese: int, root: Path = STORICO_DIR) -> Path:
    return root / f"commodity={commodity}" / f"anno={anno}" / f"{anno}-{mese:02d}.parquet"


def glob_storico(root: Path = STORICO_DIR, commodity: str = "*") -> str:
    return (root / f"commodity={commodity}" / "anno=*" / "*.parquet").as_posix()


def parse_giorno(xml_path: Path, commodity: str, giorno: date,
                 parser: OfferteParser | None = None) -> pl.DataFrame:
    """Parsing di un file XML: tutte le colonne Utf8 tranne DATA_RILEVAZIONE
    (Date). Le offerte duplicate nel file sorgente vengono rimosse."""
    parser = parser or OfferteParser(MAPPING_PATH)
    records = [{k: (str(v) if v is not None else None) for k, v in r.items()}
               for r in parser.parse(Path(xml_path), commodity)]
    if not records:
        return pl.DataFrame()

    chiavi = {}
    for r in records:
        for k in r:
            chiavi.setdefault(k, None)   # ordine di prima apparizione
    df = pl.DataFrame(records, schema={k: pl.Utf8 for k in chiavi})
    df = df.with_columns(pl.lit(giorno).alias("DATA_RILEVAZIONE"))

    n = df.height
    df = df.unique(subset=CHIAVE_OFFERTA, keep="first", maintain_order=True)
    if df.height < n:
        logger.warning("%s %s: %d offerte duplicate nel file sorgente rimosse",
                       commodity, giorno, n - df.height)
    return df


def _scrivi_atomico(df: pl.DataFrame, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".parquet.tmp")
    df.write_parquet(tmp, compression="zstd")
    os.replace(tmp, out)


def scrivi_giorni(giorni: list[pl.DataFrame], commodity: str,
                  root: Path = STORICO_DIR) -> list[Path]:
    """Inserisce o sostituisce i giorni indicati nei rispettivi file mensili."""
    per_mese = defaultdict(list)
    for df in giorni:
        if df.is_empty():
            continue
        g = df["DATA_RILEVAZIONE"][0]
        per_mese[(g.year, g.month)].append(df)

    scritti = []
    for (anno, mese), nuovi in sorted(per_mese.items()):
        out = path_mese(commodity, anno, mese, root)
        nuovi_df = pl.concat(nuovi, how="diagonal")
        if out.exists():
            date_nuove = nuovi_df["DATA_RILEVAZIONE"].unique().implode()
            vecchio = pl.read_parquet(out).filter(
                ~pl.col("DATA_RILEVAZIONE").is_in(date_nuove))
            nuovi_df = pl.concat([vecchio, nuovi_df], how="diagonal")
        nuovi_df = nuovi_df.sort(CHIAVE_OFFERTA + ["DATA_RILEVAZIONE"])
        _scrivi_atomico(nuovi_df, out)
        scritti.append(out)
    return scritti


def giorni_presenti(commodity: str, root: Path = STORICO_DIR) -> set[date]:
    # file per file: lo schema cambia tra i mesi (numero di componenti variabile)
    giorni: set[date] = set()
    for f in (root / f"commodity={commodity}").glob("anno=*/*.parquet"):
        giorni.update(pl.read_parquet(f, columns=["DATA_RILEVAZIONE"])
                      ["DATA_RILEVAZIONE"].unique().to_list())
    return giorni


def ultima_rilevazione(root: Path = STORICO_DIR) -> date | None:
    date_ = [max(g) for c in ("E", "G", "D") if (g := giorni_presenti(c, root))]
    return max(date_) if date_ else None


def pulisci_tmp(root: Path = STORICO_DIR) -> int:
    """Rimuove i .tmp lasciati da scritture interrotte."""
    n = 0
    for p in root.rglob("*.tmp"):
        p.unlink()
        n += 1
    if n:
        logger.warning("Rimossi %d file temporanei orfani in %s", n, root)
    return n


def leggi_finestra(fino_a: date, giorni: int = 8, root: Path = STORICO_DIR,
                   margine_giorni: int = 45):
    """Offerte attive nella finestra di `giorni` che termina all'ultima
    rilevazione <= fino_a: per ogni offerta l'ultima versione rilevata.
    Legge solo i file mensili degli ultimi `margine_giorni` (tollera buchi
    nei dati). Restituisce un DataFrame pandas, vuoto se non ci sono dati."""
    inizio = fino_a - timedelta(days=margine_giorni)
    mesi, g = set(), inizio.replace(day=1)
    while g <= fino_a:
        mesi.add((g.year, g.month))
        g = (g + timedelta(days=32)).replace(day=1)
    files = [p.as_posix() for c in ("E", "G", "D") for a, m in sorted(mesi)
             if (p := path_mese(c, a, m, root)).exists()]
    if not files:
        import pandas as pd
        return pd.DataFrame()

    lista = ", ".join(f"'{f}'" for f in files)
    con = duckdb.connect()
    df = con.execute(f"""
        WITH raw AS (
            SELECT * FROM read_parquet([{lista}], union_by_name = true,
                                       hive_partitioning = false)
            WHERE DATA_RILEVAZIONE <= DATE '{fino_a.isoformat()}'
        ),
        ultima AS (
            SELECT * FROM raw
            QUALIFY ROW_NUMBER() OVER (PARTITION BY PIVA_UTENTE, COD_OFFERTA
                                       ORDER BY DATA_RILEVAZIONE DESC) = 1
        )
        SELECT * FROM ultima
        WHERE DATA_RILEVAZIONE > (SELECT max(DATA_RILEVAZIONE) FROM ultima)
                                 - INTERVAL {int(giorni)} DAY
    """).df()
    con.close()
    return df


def genera_dashboard(out_path: Path = DASHBOARD_PATH, anni_inizio=None,
                     root: Path = STORICO_DIR) -> int:
    """Rigenera il parquet di compatibilità storico_2026_full: offerte con
    DATA_INIZIO negli anni indicati, di default l'anno corrente e il
    precedente (data parsata, non LIKE sul testo)."""
    if anni_inizio is None:
        anni_inizio = (date.today().year - 1, date.today().year)
    anni = ", ".join(str(int(a)) for a in anni_inizio)
    tmp = Path(out_path).with_suffix(".tmp.parquet")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(f"""
        COPY (
            SELECT *
            FROM read_parquet('{glob_storico(root)}', union_by_name = true,
                              hive_partitioning = false)
            WHERE year(try_strptime(split_part(DATA_INIZIO, '_', 1), '%d/%m/%Y')) IN ({anni})
        ) TO '{tmp.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)
    n = con.execute(f"SELECT count(*) FROM read_parquet('{tmp.as_posix()}')").fetchone()[0]
    con.close()
    os.replace(tmp, out_path)
    logger.info("Parquet dashboard rigenerato: %s (%d righe)", out_path, n)
    return n
