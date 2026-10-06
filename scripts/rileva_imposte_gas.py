"""Rileva dal Portale Offerte accise e addizionale regionale gas per regione.

    python scripts/rileva_imposte_gas.py

Il Portale non pubblica le imposte gas tra gli open data: il dettaglio di
un'offerta, però, ne riporta le aliquote unitarie per scaglione. Con un
consumo di 3000 Smc compaiono tutti gli scaglioni. Output:
data/processed/imposte_gas_portale.json  {regione: {"accisa": [[lim, €/Smc]],
"addizionale": [[lim, €/Smc]], "cap": ...}}
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
URL = "https://www.ilportaleofferte.it/portaleOfferte/it/confronto-tariffe-prezzi-luce-gas.page"
OUT = BASE / "data" / "processed" / "imposte_gas_portale.json"
CONSUMO = 3000
APERTO = 9_999_999

# Capoluogo di regione (più Latina e Frosinone: Lazio con territori ex Mezzogiorno)
CAP = {
    "Valle d'Aosta": "11100", "Piemonte": "10121", "Liguria": "16121",
    "Lombardia": "20121", "Trentino-Alto Adige": "38121", "Trentino-Alto Adige (BZ)": "39100",
    "Veneto": "30121", "Friuli-Venezia Giulia": "34121", "Emilia-Romagna": "40121",
    "Toscana": "50121", "Umbria": "06121", "Marche": "60121",
    "Lazio": "00185", "Lazio (LT)": "04100", "Lazio (FR)": "03100",
    "Abruzzo": "67100", "Molise": "86100", "Campania": "80121", "Puglia": "70121",
    "Basilicata": "85100", "Calabria": "88100", "Sicilia": "90121", "Sardegna": "09121",
}

def _limite(descr: str) -> int:
    m = re.search(r"(?:a|fino a)\s+([\d.]+)\s+Smc", descr)
    return int(m.group(1).replace(".", "")) if m else APERTO


def leggi_aliquote(cap: str) -> dict:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page(ignore_https_errors=True)
        pg.goto(URL, wait_until="networkidle", timeout=90000)
        pg.click("#gas", force=True)
        pg.fill("#capComune", cap)
        pg.locator(".ui-menu-item").first.wait_for(timeout=15000)
        comune = pg.locator(".ui-menu-item").first.inner_text().strip()
        pg.locator(".ui-menu-item").first.click()
        pg.locator("#casa").wait_for(state="visible", timeout=45000)
        pg.click("#casa", force=True)
        pg.click("#prezzoFisso", force=True)
        pg.locator("a:visible").filter(has_text="Avanti").first.click()
        pg.locator("#scegliClasse").wait_for(state="visible", timeout=20000)
        pg.select_option("#scegliClasse", "1")
        for uso in ("cottura", "acquaCalda", "riscaldamento"):
            pg.click(f"label[for={uso}]")
        pg.click("#consumoGasSI", force=True)
        pg.fill("#ConsumoAnnuoGas", str(CONSUMO))
        pg.locator("#ConsumoAnnuoGas").dispatch_event("keyup")
        pg.locator("input[name=confronta]:visible").click()
        pg.wait_for_url("**/confronta_offerte.page", timeout=120000)
        pg.wait_for_load_state("networkidle", timeout=180000)
        # la prima carta è il servizio di tutela: si apre la prima offerta di mercato
        pg.locator("div.boxRisultato_shadow").nth(1).get_by_text("Vai al dettaglio").first.click()
        pg.locator("#corr_unitari_imposte_gas").wait_for(state="attached", timeout=120000)
        righe = pg.eval_on_selector_all("#corr_unitari_imposte_gas tr", """rs => rs.map(r =>
            [...r.querySelectorAll('td')].map(td => td.textContent.trim()))""")
        b.close()

    out = {"cap": cap, "comune": comune, "accisa": [], "addizionale": []}
    for celle in righe:
        if len(celle) < 3 or not celle[2]:
            continue
        descr, valore = celle[1], float(celle[2].replace(".", "").replace(",", "."))
        voce = "accisa" if descr.lower().startswith("accisa") else "addizionale"
        out[voce].append([_limite(descr), valore])
    if not out["accisa"]:
        raise RuntimeError("aliquote non trovate nel dettaglio offerta")
    for voce in ("accisa", "addizionale"):
        if out[voce]:
            out[voce][-1][0] = APERTO  # ultimo scaglione aperto
    return out


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    risultati = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    for regione, cap in CAP.items():
        if regione in risultati:
            continue
        for tentativo in range(1, 4):
            try:
                risultati[regione] = leggi_aliquote(cap)
                break
            except Exception as e:  # pagina lenta o errore del portale: si riprova
                logging.warning("%s: %s (tentativo %d/3)", regione, str(e).splitlines()[0], tentativo)
        else:
            continue
        logging.info("%s: %s", regione, risultati[regione])
        OUT.write_text(json.dumps(risultati, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
