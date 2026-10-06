"""Rileva dal Portale Offerte le componenti regolate non pubblicate negli open data.

    python scripts/rileva_componenti_portale.py

PPE (luce, €/kWh) e CCR (gas, €/Smc per trimestre) sono parametri del Portale
(Regole per il calcolo della spesa, appendice: ppe, ccr_gj_1..4) ma mancano
dal file Parametri degli open data. Il dettaglio di un'offerta che le dichiara
ne riporta il valore: si apre il dettaglio di una di queste offerte, scelta
dall'ultima rilevazione locale. Output: data/processed/componenti_portale.json
{"ppe": float, "ccr": {"2026-Q4": float, ...}, "rilevato": "YYYY-MM-DD", ...}
"""
from __future__ import annotations

import json
import logging
import re
import sys
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "scripts"))

from engine.forward import COMPONENTI_PORTALE  # noqa: E402

_ROMANI = {"I": 1, "II": 2, "III": 3, "IV": 4}
_RE_CCR = re.compile(r"^CCR\s+(I{1,3}|IV)\s+trimestre\s+(\d{4})$")


def _numero(s: str) -> float:
    return float(s.replace(".", "").replace(",", "."))


def candidati(df, colonna: str, commodity: str) -> list[str]:
    """Offerte a prezzo fisso, domestiche, che dichiarano la componente."""
    f = df[(df["commodity"] == commodity)
           & (df[colonna].astype(str).str.lower() == "true")
           & df["TIPO_OFFERTA"].astype(str).str.contains("isso")
           & df["TIPO_CLIENTE"].astype(str).str.contains("omestico")]
    if commodity == "E":
        f = f[f["TIPOLOGIA_FASCE"].astype(str).str.contains("onorari")]
    return f["COD_OFFERTA"].drop_duplicates().tolist()


def dettaglio_primo(sc: dict, codici: list[str]) -> tuple[str, list] | None:
    """Righe del dettaglio della prima offerta dei risultati tra quelle indicate."""
    from playwright.sync_api import sync_playwright
    import verifica_portale as vp

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page(ignore_https_errors=True)
        vp._compila_form(pg, sc)
        codice = pg.evaluate("""cods => {
            for (const c of document.querySelectorAll('div.boxRisultato_shadow')) {
                const cod = cods.find(x => c.textContent.includes(x));
                if (cod) { c.querySelector('a.linkDettaglio').click(); return cod; }
            }
            return null; }""", codici)
        if not codice:
            b.close()
            return None
        pg.wait_for_url("**/dettaglio_offerta_ml.page", timeout=120000)
        pg.wait_for_load_state("networkidle", timeout=120000)
        righe = pg.eval_on_selector_all(
            "tr", """rs => rs.map(r => [...r.children].map(c => c.textContent.trim())
                .filter(Boolean)).filter(c => c.length >= 2).map(c => [c[0], c[c.length-1]])""")
        b.close()
    return codice, righe


def leggi_ppe(righe: list) -> float | None:
    return next((_numero(v) for voce, v in righe if voce.strip() == "PPE"), None)


def leggi_ccr(righe: list) -> dict[str, float]:
    out = {}
    for voce, v in righe:
        if m := _RE_CCR.match(voce.strip()):
            out[f"{m.group(2)}-Q{_ROMANI[m.group(1)]}"] = _numero(v)
    return dict(sorted(out.items()))


def rileva(rif: date | None = None) -> dict:
    import verifica_portale as vp
    from storage import daily_store as ds

    rif = rif or ds.ultima_rilevazione()
    df = ds.leggi_finestra(rif, giorni=1)
    out = carica()
    for nome, colonna, comm, leggi, chiave in (
            ("E_mono_fisso_Milano", "REGOLATA_PPE", "E", leggi_ppe, "ppe"),
            ("G_fisso_Milano", "REGOLATA_CCR", "G", leggi_ccr, "ccr")):
        cod = candidati(df, colonna, comm)
        if not cod:
            logging.warning("%s: nessuna offerta locale la dichiara", chiave)
            continue
        trovato = None
        for tentativo in range(1, 4):
            try:
                trovato = dettaglio_primo(vp.SCENARI[nome], cod)
                break
            except Exception as e:  # pagina lenta o errore del portale: si riprova
                logging.warning("%s: %s (tentativo %d/3)", chiave, str(e).splitlines()[0], tentativo)
        if not trovato:
            logging.warning("%s: nessuna offerta che la dichiara tra i risultati del Portale", chiave)
            continue
        codice, righe = trovato
        valore = leggi(righe)
        if valore is None or valore == {}:
            logging.warning("%s: voce assente nel dettaglio di %s", chiave, codice)
            continue
        out[chiave] = valore
        out[f"{chiave}_offerta"] = codice
        logging.info("%s = %s (offerta %s)", chiave, valore, codice)
    out["rilevato"] = date.today().isoformat()
    COMPONENTI_PORTALE.write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


def carica() -> dict:
    if COMPONENTI_PORTALE.exists():
        return json.loads(COMPONENTI_PORTALE.read_text(encoding="utf-8"))
    return {}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    print(json.dumps(rileva(), indent=1))
