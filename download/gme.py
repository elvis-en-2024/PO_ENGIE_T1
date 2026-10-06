"""Quotazioni forward del GME (mercati a termine MTE luce e MT-GAS).

Il Portale Offerte stima le offerte variabili con la media delle quotazioni
forward dell'indice nel mese precedente la consultazione (ARERA, delibera
289/2022). Qui si scaricano gli esiti giornalieri dei mercati a termine GME:
data/raw/gme/{mte,mtgas}/YYYY/YYYYMMDD.json  {prodotto: €/MWh}
(prezzo di riferimento se ci sono stati scambi, altrimenti prezzo di controllo).

Le API del sito rispondono solo dentro una sessione di navigazione (token
generato dalla pagina), quindi si passa da Playwright.
"""
from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

GME_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "gme"
_SITO = "https://www.mercatoelettrico.org"
_PAGINE = {
    "mte": f"{_SITO}/it-it/Home/Esiti/Elettricita/MTE/Esiti/Baseload/MTE",
    "mtgas": f"{_SITO}/it-it/Home/Esiti/Gas/MT-GAS/Esiti/MT-GAS",
}
_API = {
    "mte": f"{_SITO}/DesktopModules/GmeEsitiMTE/API/GmeEsitiMTE/GetMEESitiMTE?data={{g}}",
    "mtgas": f"{_SITO}/DesktopModules/GmeEsitiMGAS/API/item/GetGasEsitiMGAS?DataSessione={{g}}&Mercato=MT",
}
_HEADER = ("moduleid", "tabid", "requestverificationtoken")


def path_sessione(mercato: str, giorno: date, root: Path = GME_DIR) -> Path:
    return root / mercato / str(giorno.year) / f"{giorno:%Y%m%d}.json"


def _prezzi(mercato: str, righe: list[dict]) -> dict[str, float]:
    out = {}
    for r in righe:
        if mercato == "mte":
            prod, rif, ctrl = r["Prodotto"], r["PrezzoRiferimento"], r["PrezzoControllo"]
        else:
            prod, rif, ctrl = r["prodotto"], r["prezzoRiferimento"], r["prezzoControllo"]
        p = rif or ctrl
        if p:
            out[prod] = float(p)
    return out


def scarica(giorni: list[date], root: Path = GME_DIR) -> int:
    """Scarica le sessioni mancanti dei giorni indicati. Ritorna quante ne ha scritte."""
    mancanti = [(m, g) for g in giorni for m in _API
                if g.weekday() < 5 and not path_sessione(m, g, root).exists()]
    if not mancanti:
        return 0
    from playwright.sync_api import sync_playwright

    scritte = 0
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page(ignore_https_errors=True)
        header = {}
        pg.on("request", lambda r: header.setdefault(
            next((m for m, u in _API.items() if r.url.startswith(u.split("?")[0])), None),
            {k: v for k, v in r.headers.items() if k in _HEADER}))
        for url in _PAGINE.values():
            pg.goto(url, wait_until="networkidle", timeout=90000)
        for mercato, g in mancanti:
            if mercato not in header:
                raise RuntimeError(f"GME: token API {mercato} non intercettato")
            r = pg.request.get(_API[mercato].format(g=f"{g:%Y%m%d}"), headers=header[mercato])
            if not r.ok:
                logger.warning("GME %s %s: HTTP %s", mercato, g, r.status)
                continue
            prezzi = _prezzi(mercato, r.json())
            if not prezzi:  # festivo o sessione non ancora pubblicata
                continue
            out = path_sessione(mercato, g, root)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(prezzi, indent=1), encoding="utf-8")
            scritte += 1
        b.close()
    return scritte


def aggiorna(oggi: date | None = None, root: Path = GME_DIR) -> int:
    """Sessioni del mese precedente e del mese in corso fino a ieri."""
    oggi = oggi or date.today()
    inizio = (oggi.replace(day=1) - timedelta(days=1)).replace(day=1)
    giorni = [inizio + timedelta(n) for n in range((oggi - inizio).days)]
    return scarica(giorni, root)


def sessioni(mercato: str, anno: int, mese: int, root: Path = GME_DIR) -> list[dict[str, float]]:
    """Prezzi delle sessioni di un mese, in ordine di data."""
    cartella = root / mercato / str(anno)
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(cartella.glob(f"{anno}{mese:02d}*.json"))]
