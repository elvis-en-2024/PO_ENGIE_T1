"""Confronto diretto con il Portale Offerte online, a parità di parametri.

    python scripts/verifica_portale.py                 # tutti gli scenari
    python scripts/verifica_portale.py E_mono_fisso_Milano

Per ogni scenario compila il form di ilportaleofferte.it (Playwright, headless),
legge l'elenco offerte con la spesa annua, poi calcola la SAS con il motore
locale sull'ultima rilevazione dello storico e confronta per codice offerta.
Output: data/processed/verifica_portale_<scenario>.csv + riepilogo a video.
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

URL = "https://www.ilportaleofferte.it/portaleOfferte/it/confronto-tariffe-prezzi-luce-gas.page"

# Comune di prova -> (CAP, regione, provincia ISTAT, comune ISTAT)
COMUNI = {
    "Milano": ("20121", "Lombardia", "015", "015146"),
    "Palermo": ("90121", "Sicilia", "082", "082053"),
    "Roma": ("00185", "Lazio", "058", "058091"),
}

SCENARI = {
    "E_mono_fisso_Milano": dict(commodity="E", comune="Milano", tipo="Fisso", fasce="Monorario",
                                consumi={"F1": 2700}, potenza=3, residente=True),
    # stesse offerte a consumi/potenze diverse: separano le componenti fisse, per kWh e per kW
    "E_mono_fisso_Milano_1500": dict(commodity="E", comune="Milano", tipo="Fisso", fasce="Monorario",
                                     consumi={"F1": 1500}, potenza=3, residente=True),
    "E_mono_fisso_Milano_4500": dict(commodity="E", comune="Milano", tipo="Fisso", fasce="Monorario",
                                     consumi={"F1": 4500}, potenza=3, residente=True),
    "E_mono_fisso_Milano_6kW": dict(commodity="E", comune="Milano", tipo="Fisso", fasce="Monorario",
                                    consumi={"F1": 2700}, potenza=6, residente=True),
    "E_fasce_fisso_Milano": dict(commodity="E", comune="Milano", tipo="Fisso", fasce="A Fasce",
                                 consumi={"F1": 891, "F2": 837, "F3": 972}, potenza=3, residente=True),
    "E_mono_variabile_Palermo": dict(commodity="E", comune="Palermo", tipo="Variabile", fasce="Monorario",
                                     consumi={"F1": 2700}, potenza=3, residente=True),
    "G_fisso_Milano": dict(commodity="G", comune="Milano", tipo="Fisso", consumi={"F1": 1400}),
    "G_variabile_Roma": dict(commodity="G", comune="Roma", tipo="Variabile", consumi={"F1": 1400}),
}


def _euro(s: str) -> float | None:
    m = re.search(r"(-?)\s*€\s*(-?[\d.]+,\d+)", s.replace("\xa0", " "))
    if not m:
        return None
    v = float(m.group(2).replace(".", "").replace(",", "."))
    return -abs(v) if m.group(1) or v < 0 else v


def cerca_portale(sc: dict, screenshot: Path | None = None, tentativi: int = 3) -> pd.DataFrame:
    # il portale a volte risponde "Si è verificato un errore inaspettato": si riprova
    for n in range(1, tentativi + 1):
        try:
            df = _cerca_portale(sc, screenshot)
            if len(df):
                return df
            logging.warning("Portale senza risultati (tentativo %d/%d)", n, tentativi)
        except Exception as e:  # timeout di Playwright su pagina lenta
            logging.warning("Portale: %s (tentativo %d/%d)", str(e).splitlines()[0], n, tentativi)
    raise RuntimeError("Il portale non ha restituito offerte: vedi lo screenshot")


def dettaglio_portale(sc: dict, codici: list[str]) -> dict[str, list[tuple[str, str]]]:
    """Composizione della spesa (voce, valore) dal dettaglio delle offerte indicate."""
    from playwright.sync_api import sync_playwright

    out = {}
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page(ignore_https_errors=True)
        for codice in codici:
            _compila_form(pg, sc)
            trovata = pg.evaluate("""cod => {
                const c = [...document.querySelectorAll('div.boxRisultato_shadow')]
                    .find(c => c.textContent.includes(cod));
                if (!c) return false;
                c.querySelector('a.linkDettaglio').click(); return true; }""", codice)
            if not trovata:
                out[codice] = []
                continue
            pg.wait_for_url("**/dettaglio_offerta_ml.page", timeout=120000)
            pg.wait_for_load_state("networkidle", timeout=120000)
            out[codice] = pg.eval_on_selector_all(
                "tr", """rs => rs.map(r => [...r.children].map(c => c.textContent.trim())
                    .filter(Boolean)).filter(c => c.length >= 2).map(c => [c[0], c[c.length-1]])""")
        b.close()
    return out


def _cerca_portale(sc: dict, screenshot: Path | None = None) -> pd.DataFrame:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page(ignore_https_errors=True)
        _compila_form(pg, sc)
        if screenshot:
            pg.screenshot(path=str(screenshot))
        carte = pg.eval_on_selector_all("div.boxRisultato_shadow", """cs => cs.map(c => {
            const t = s => (c.querySelector(s) || {}).innerText || '';
            return {venditore: t('.nome_venditore').trim(), nome: t('.nome_offerta').trim(),
                    codice: t('.codice_offerta').replace('cod.', '').trim(),
                    validita: t('.valid_date').trim(), prezzo: t('.prezzoOffertaValore').trim()};
        })""")
        trovate = pg.locator("text=SONO STATE TROVATE").first.inner_text() if pg.locator(
            "text=SONO STATE TROVATE").count() else ""
        b.close()

    df = pd.DataFrame(carte, columns=["venditore", "nome", "codice", "validita", "prezzo"])
    df["SAS_PO"] = df["prezzo"].map(_euro)
    df["rank_PO"] = range(1, len(df) + 1)
    logging.info("Portale: %s carte lette (%s)", len(df), trovate.strip())
    return df


def _compila_form(pg, sc: dict) -> None:
    """Compila il form di ricerca e attende la pagina dei risultati."""
    cap = COMUNI[sc["comune"]][0]
    pg.goto(URL, wait_until="networkidle", timeout=90000)
    pg.click("#energiaElettrica" if sc["commodity"] == "E" else "#gas", force=True)
    pg.fill("#capComune", cap)
    pg.locator(".ui-menu-item").first.wait_for(timeout=15000)
    pg.locator(".ui-menu-item").first.click()
    pg.locator("#casa").wait_for(state="visible", timeout=45000)
    pg.click("#casa", force=True)
    pg.click("#prezzoFisso" if sc["tipo"] == "Fisso" else "#prezzoVariabile", force=True)
    if sc["commodity"] == "E":
        pg.click("#residenteSI" if sc["residente"] else "#residenteNO", force=True)
    pg.locator("a:visible").filter(has_text="Avanti").first.click()
    pg.wait_for_timeout(1500)

    if sc["commodity"] == "E":
        pg.select_option("#scegliPotenza", str(sc["potenza"]).rstrip("0").rstrip(".")
                         if isinstance(sc["potenza"], float) else str(sc["potenza"]))
        mono = sc["fasce"] == "Monorario"
        pg.select_option("#tipoTariffa", "monoraria" if mono else "fasce")
        pg.click("#ferNO", force=True)
        pg.click("#consumoSI", force=True)
        pg.wait_for_timeout(800)
        if mono:
            pg.fill("#ConsumoAnnuo", str(sum(sc["consumi"].values())))
        else:
            # il primo campo del riquadro è il totale: si compilano le fasce per id
            for i, banda in enumerate(("F1", "F2", "F3"), start=1):
                campo = pg.locator(f"#fascia{i}")
                campo.fill(str(sc["consumi"][banda]))
                campo.dispatch_event("keyup")
    else:
        pg.locator("#scegliClasse").wait_for(state="visible", timeout=20000)
        pg.select_option("#scegliClasse", "1")
        # categorie d'uso: checkbox nascoste, si clicca l'etichetta
        for uso in ("cottura", "acquaCalda", "riscaldamento"):
            pg.click(f"label[for={uso}]")
        pg.click("#consumoGasSI", force=True)
        campo = pg.locator("#ConsumoAnnuoGas")
        campo.wait_for(state="visible", timeout=10000)
        campo.fill(str(sum(sc["consumi"].values())))
        campo.dispatch_event("keyup")

    pg.locator("input[name=confronta]:visible").click()
    pg.wait_for_url("**/confronta_offerte.page", timeout=120000)
    pg.wait_for_load_state("networkidle", timeout=180000)


def calcola_locale(sc: dict, rif: date | None) -> tuple[pd.DataFrame, date]:
    from engine.sas_calculator_fast import FastSASCalculator
    from storage import daily_store as ds

    rif = rif or ds.ultima_rilevazione()
    _, regione, provincia, comune = COMUNI[sc["comune"]]
    # il Portale mostra solo le offerte del file del giorno
    calc = FastSASCalculator(ds.leggi_finestra(rif, giorni=1))
    cons = sc["consumi"]
    if sc["commodity"] == "E":
        f = calc.filter_offers(commodity="E", tipo_offerta=sc["tipo"], tipo_cliente="Domestico",
                               fasce=sc["fasce"], regione=regione, provincia=provincia,
                               comune=comune, consumo_annuo=sum(cons.values()),
                               falsa_multioraria="mantieni", potenza=sc["potenza"],
                               residente=sc["residente"])
        res = calc.calculate_sas(f, cons, potenza=sc["potenza"], regione=regione,
                                 residente=sc["residente"])
    else:
        f = calc.filter_offers(commodity="G", tipo_offerta=sc["tipo"], regione=regione,
                               provincia=provincia, comune=comune,
                               consumo_annuo=sum(cons.values()))
        res = calc.calculate_sas(f, cons, potenza=0, regione=regione, residente=True)
    if sc["tipo"] == "Variabile":
        # sensibilità della SAS alla stima dell'indice: serve a ricavare quella del Portale
        kw = dict(potenza=sc.get("potenza", 0), regione=regione, residente=sc.get("residente", True))
        if calc.forward:
            # forward GME: si sposta di 0,01 €/unità l'intera curva dell'indice
            import copy
            from engine import forward
            originale = calc.forward
            if sc["commodity"] == "E":
                chiave, base = "forward PUN F0 (netto perdite)", originale["ee"]["F0"]
            else:
                quote = forward.profilo_gas(regione, calc.oggi)
                chiave = "forward PSV pesato sul profilo"
                base = sum(w * p for w, p in zip(quote, originale["gas_mesi"]))
            spostato = copy.deepcopy(originale)
            spostato["ee"] = {k: v + 0.01 for k, v in spostato["ee"].items()}
            spostato["gas_mesi"] = [v + 0.01 for v in spostato["gas_mesi"]]
            calc.forward = spostato
            bump = calc.calculate_sas(f, cons, **kw).set_index("COD_OFFERTA")["SAS"]
            calc.forward = originale
        else:
            chiave = "pun_stima" if sc["commodity"] == "E" else "psv_stima"
            base = calc.arera.PARAMETRI[chiave]
            calc.arera.PARAMETRI[chiave] = base + 0.01
            bump = calc.calculate_sas(f, cons, **kw).set_index("COD_OFFERTA")["SAS"]
            calc.arera.PARAMETRI[chiave] = base
        res["dSAS_indice"] = (res["COD_OFFERTA"].map(bump[~bump.index.duplicated()]) - res["SAS"]) / 0.01
        res.attrs["indice"] = (chiave, base)
    res = res.reset_index(drop=True)
    res["rank_locale"] = res.index + 1
    zone = f.set_index("COD_OFFERTA")[["REGIONE", "PROVINCIA", "COMUNE"]]
    attrs = res.attrs
    res = res.join(zone[~zone.index.duplicated()], on="COD_OFFERTA")
    cols = ["COD_OFFERTA", "NOME_OFFERTA", "SAS", "rank_locale", "REGIONE", "PROVINCIA", "COMUNE"]
    out = res[cols + (["dSAS_indice"] if "dSAS_indice" in res else [])]
    out.attrs = attrs
    return out, rif


def confronta(nome: str, sc: dict, rif: date | None) -> pd.DataFrame:
    po = cerca_portale(sc, screenshot=BASE / ".tmp" / f"po_{nome}.png")
    loc, rif = calcola_locale(sc, rif)
    po_ml = po[po["codice"] != ""]  # la prima carta è il servizio di tutela, senza codice
    d = po_ml.merge(loc, left_on="codice", right_on="COD_OFFERTA", how="outer", indicator=True)
    d["codice"] = d["codice"].fillna(d["COD_OFFERTA"])
    d["delta"] = (d["SAS"] - d["SAS_PO"]).round(2)
    d["delta_pct"] = (100 * d["delta"] / d["SAS_PO"]).round(2)
    d["esito"] = d["_merge"].map({"both": "entrambi", "left_only": "solo portale",
                                  "right_only": "solo locale"})
    d = d.drop(columns=["_merge", "COD_OFFERTA", "prezzo"]).sort_values(["rank_PO", "rank_locale"])
    d.to_csv(BASE / "data" / "processed" / f"verifica_portale_{nome}.csv", index=False)

    tutela = po[po["codice"] == ""]["SAS_PO"].tolist()
    e = d[d.esito == "entrambi"]
    print(f"\n=== {nome}  (dati locali al {rif}, portale oggi {date.today()}) ===")
    print(f"offerte portale: {len(po_ml)}  locale: {len(loc)}  in comune: {len(e)}  "
          f"solo portale: {(d.esito == 'solo portale').sum()}  solo locale: {(d.esito == 'solo locale').sum()}")
    if tutela:
        print(f"servizio di tutela sul portale: € {tutela[0]:.2f}")
    if len(e):
        print(f"SAS uguale (±1 €): {(e.delta.abs() <= 1).sum()}  entro ±1%: {(e.delta_pct.abs() <= 1).sum()}  "
              f"delta mediano: {e.delta.median():.2f} €  max |delta|: {e.delta.abs().max():.2f} €")
        if "indice" in loc.attrs:
            # stima dell'indice che annulla lo scarto (mediana sulle offerte in comune)
            chiave, base = loc.attrs["indice"]
            implicita = (base - e["delta"] / e["dSAS_indice"]).median()
            print(f"{chiave}: locale {base:.6f}  implicita nel Portale {implicita:.6f} €/unità")
        top = e.nsmallest(10, "rank_PO")[["rank_PO", "rank_locale", "nome", "SAS_PO", "SAS", "delta"]]
        print(top.to_string(index=False))
    return d


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenari", nargs="*", default=list(SCENARI))
    ap.add_argument("--rif", type=date.fromisoformat, help="data rilevazione locale (default: ultima)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    for nome in args.scenari:
        confronta(nome, SCENARI[nome], args.rif)


if __name__ == "__main__":
    main()
