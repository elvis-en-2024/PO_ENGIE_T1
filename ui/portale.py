"""Elementi grafici in stile Portale Offerte e descrizioni leggibili delle offerte."""
from __future__ import annotations

import html
import math

import pandas as pd

MAGENTA = "#B5008C"
VIOLA = "#520C7A"
VIOLA_CHIARO = "#F3E6F1"
GRIGIO = "#C8C8C8"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Raleway:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stMarkdown, .stButton button, input, select, textarea, label {{
    font-family: 'Raleway', 'Segoe UI', sans-serif !important;
}}
#MainMenu, footer, header[data-testid="stHeader"] {{ visibility: hidden; height: 0; }}
.block-container {{ padding-top: 0 !important; max-width: 1180px; }}

/* testata */
.po-top {{ background: {MAGENTA}; color: #fff; margin: 0 -100vw; padding: 18px 100vw 14px; }}
.po-top .po-ente {{ font-weight: 700; letter-spacing: .5px; font-size: 15px; opacity: .95; }}
.po-brand {{ display: flex; align-items: center; justify-content: space-between; padding: 16px 0 8px;
             border-bottom: 4px solid {VIOLA}; margin-bottom: 6px; }}
.po-logo {{ line-height: 1; }}
.po-logo .l1 {{ color: {VIOLA}; font-weight: 800; font-size: 30px; }}
.po-logo .l2 {{ color: {MAGENTA}; font-weight: 700; font-size: 17px; margin-left: 118px; }}
.po-badge {{ background: {VIOLA}; color: #fff; padding: 8px 18px; font-weight: 700; letter-spacing: 1px;
             font-size: 14px; text-transform: uppercase; }}
.po-crumb {{ font-size: 13px; color: #555; margin: 4px 0 10px; text-transform: uppercase; }}
.po-crumb b {{ color: {VIOLA}; font-weight: 600; }}
.po-title {{ color: {VIOLA}; font-weight: 800; font-size: 34px; margin: 6px 0 18px; }}

/* stepper */
.po-stepper {{ display: flex; align-items: flex-start; margin: 4px 0 26px; }}
.po-step {{ text-align: center; width: 170px; color: #666; font-size: 17px; }}
.po-step .n {{ display: inline-block; width: 30px; height: 30px; line-height: 30px; background: {GRIGIO};
               color: #333; font-size: 13px; font-weight: 700; margin-bottom: 8px; }}
.po-step.on {{ color: {VIOLA}; }}
.po-step.on .n {{ background: {MAGENTA}; color: #fff; }}
.po-line {{ flex: 0 0 140px; height: 3px; background: {GRIGIO}; margin: 14px -55px 0; }}

/* riquadri */
.po-banner {{ background: {MAGENTA}; color: #fff; padding: 18px 26px; font-size: 15px; margin-bottom: 0; }}
.po-banner b {{ font-weight: 700; }}
.po-q {{ color: #444; font-size: 17px; padding-top: 6px; }}
.po-sep {{ border-top: 1px solid #ddd; margin: 14px 0; }}
.po-box {{ border: 2px solid {VIOLA}; padding: 14px 18px; margin-bottom: 16px; background: #fff; }}
.po-box h4 {{ color: {VIOLA}; font-size: 15px; text-transform: uppercase; margin: 0 0 10px; font-weight: 600; }}
.po-kv {{ font-size: 14px; color: #333; margin-right: 18px; display: inline-block; }}
.po-kv b {{ font-weight: 600; }}
.po-found {{ font-size: 17px; color: {VIOLA}; text-transform: uppercase; margin: 6px 0 12px; }}
.po-found span {{ background: {VIOLA}; color: #fff; border-radius: 12px; padding: 1px 10px; font-weight: 700; }}
.po-note {{ border: 2px solid {VIOLA}; padding: 12px 14px; font-size: 13px; color: #444; margin-bottom: 14px; }}
.po-filtri {{ color: {MAGENTA}; font-size: 18px; text-transform: uppercase; border-bottom: 2px solid #ddd;
              padding-bottom: 6px; margin-bottom: 8px; }}

/* schede offerta */
[class*="st-key-card_"] {{ background: #fff; border: 1px solid #e3e3e3 !important; border-radius: 0 !important;
    box-shadow: 0 3px 8px rgba(0,0,0,.10); padding: 14px 18px !important; margin-bottom: 4px; }}
[class*="st-key-card_engie"] {{ border-left: 6px solid #00AAFF !important; }}
[class*="st-key-card_sim"] {{ border: 3px solid {MAGENTA} !important; background: {VIOLA_CHIARO}; }}
.po-pos {{ color: {VIOLA}; font-size: 26px; font-weight: 800; text-align: center; padding-top: 8px; }}
.po-vend {{ color: {MAGENTA}; font-size: 18px; font-weight: 600; text-transform: uppercase; }}
.po-off {{ color: {VIOLA}; font-size: 16px; font-weight: 600; }}
.po-cod {{ color: #888; font-size: 12px; }}
.po-tag {{ display: inline-block; font-size: 11px; color: {VIOLA}; border: 1px solid {VIOLA}; padding: 0 6px;
           margin: 4px 4px 0 0; border-radius: 2px; }}
.po-price {{ text-align: right; }}
.po-price span {{ background: {MAGENTA}; color: #fff; border-radius: 22px; padding: 6px 14px; font-size: 19px;
                  font-weight: 700; white-space: nowrap; }}
.po-price small {{ display: block; color: #777; margin-top: 8px; font-size: 12px; }}

/* composizione della spesa */
.po-voce {{ background: {MAGENTA}; color: #fff; font-weight: 600; padding: 5px 8px; display: flex;
            justify-content: space-between; margin-top: 12px; }}
.po-voce.tot {{ background: {VIOLA}; }}
.po-sub {{ display: flex; justify-content: space-between; border-bottom: 1px solid {VIOLA}; padding: 4px 8px;
           font-size: 14px; color: #333; }}
.po-sub i {{ color: #777; font-style: normal; font-size: 12px; }}
.po-info {{ display: grid; grid-template-columns: 44% 56%; gap: 6px 12px; font-size: 14px; }}
.po-info .k {{ text-align: right; color: #333; font-weight: 500; }}
.po-info .v {{ color: #555; }}

/* pulsanti */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
    border-radius: 0 !important; border: 2px solid {VIOLA} !important; color: {VIOLA} !important;
    background: #fff !important; font-weight: 700 !important; text-transform: uppercase; letter-spacing: .4px; }}
.stButton > button:hover {{ background: {VIOLA_CHIARO} !important; }}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{
    background: {VIOLA} !important; color: #fff !important; }}
.stButton > button[kind="primary"]:hover {{ background: {MAGENTA} !important; border-color: {MAGENTA} !important; }}
[data-testid="stSegmentedControl"] button[aria-checked="true"],
[data-testid="stButtonGroup"] button[aria-checked="true"] {{ background: {VIOLA} !important; color: #fff !important; }}
.po-footer {{ background: {VIOLA}; color: #fff; margin: 40px -100vw 0; padding: 22px 100vw; font-size: 13px; }}
</style>
"""


def esc(v) -> str:
    return html.escape("" if v is None or (isinstance(v, float) and math.isnan(v)) else str(v))


def euro(v, dec: int = 2) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "-"
    s = f"{v:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def testata(pagina: str) -> str:
    return (f'<div class="po-top"><span class="po-ente">SIMULATORE · REGOLE DEL PORTALE OFFERTE ARERA</span></div>'
            f'<div class="po-brand"><div class="po-logo"><div class="l1">portale offerte</div>'
            f'<div class="l2">luce e gas</div></div><div class="po-badge">ENGIE · competitive intelligence</div></div>'
            f'<div class="po-crumb"><b>Home</b> &gt; {esc(pagina)}</div>')


def stepper(attivo: int) -> str:
    voci = ["Tipo di offerta", "Caratteristiche<br>dell'offerta", "Elenco delle<br>offerte"]
    parti = []
    for i, v in enumerate(voci, start=1):
        if i > 1:
            parti.append('<div class="po-line"></div>')
        parti.append(f'<div class="po-step {"on" if i == attivo else ""}"><div class="n">{i}</div><div>{v}</div></div>')
    return f'<div class="po-stepper">{"".join(parti)}</div>'


def domanda(testo: str) -> str:
    return f'<div class="po-q">{esc(testo)}</div>'


def riepilogo_ricerca(r: dict) -> str:
    kv = "".join(f'<span class="po-kv"><b>{esc(k)}:</b> {esc(v)}</span>' for k, v in r.items())
    return f'<div class="po-box"><h4>Caratteristiche della ricerca</h4>{kv}</div>'


def scheda(pos, venditore, offerta, codice, sas, sotto: str = "", tag: list | None = None) -> tuple[str, str, str]:
    """Tre blocchi HTML della scheda risultato: posizione, testo, prezzo."""
    tags = "".join(f'<span class="po-tag">{esc(t)}</span>' for t in (tag or []))
    return (f'<div class="po-pos">#{pos}</div>',
            f'<div class="po-vend">{esc(venditore)}</div><div class="po-off">{esc(offerta)}</div>'
            f'<div class="po-cod">cod. {esc(codice)}</div>{tags}',
            f'<div class="po-price"><span>€ {euro(sas)} annui</span><small>circa € {euro(sas / 12)} al mese'
            f'{"<br>" + sotto if sotto else ""}</small></div>')


def voce(nome: str, valore, totale: bool = False) -> str:
    return f'<div class="po-voce {"tot" if totale else ""}"><span>{esc(nome)}</span><span>{euro(valore)} €</span></div>'


def sottovoce(nome: str, valore: str, nota: str = "") -> str:
    return (f'<div class="po-sub"><span>{esc(nome)} {f"<i>{esc(nota)}</i>" if nota else ""}</span>'
            f'<span>{esc(valore)}</span></div>')


def griglia_info(coppie: list[tuple[str, str]]) -> str:
    righe = "".join(f'<div class="k">{esc(k)}:</div><div class="v">{esc(v)}</div>' for k, v in coppie if v)
    return f'<div class="po-info">{righe}</div>'


# ---------------------------------------------------------------- descrizioni offerta

def _vero(v) -> bool:
    return str(v).strip().lower() in ("true", "1", "si", "sì")


def _num(v) -> float | None:
    try:
        x = float(str(v).replace(",", "."))
        return None if math.isnan(x) else x
    except (TypeError, ValueError):
        return None


def _pieno(v) -> bool:
    return v is not None and str(v).strip().lower() not in ("", "nan", "none", "<na>", "null")


def _prezzo(v: float, unita: str) -> str:
    dec = 2 if unita in ("€/Anno", "€", "€/kW") else 6
    return f"{euro(v, dec)} {unita}"


def componenti(row: pd.Series) -> list[dict]:
    """Componenti impresa dell'offerta: nome, macroarea, prezzo, fascia, scaglione."""
    out = []
    # schema dinamico: le colonne esistono fino al massimo del file, vuote se assenti
    for c in range(1, 61):
        if f"COMP_IMP_{c}_INT_1_PREZZO" not in row.index:
            break
        for i in range(1, 11):
            p = _num(row.get(f"COMP_IMP_{c}_INT_{i}_PREZZO"))
            if p is None:
                continue
            da, a = _num(row.get(f"COMP_IMP_{c}_INT_{i}_CONSUMO_DA")), _num(row.get(f"COMP_IMP_{c}_INT_{i}_CONSUMO_A"))
            unita = str(row.get(f"COMP_IMP_{c}_INT_{i}_UNITA") or "")
            fascia = row.get(f"COMP_IMP_{c}_INT_{i}_FASCIA")
            out.append({
                "nome": str(row.get(f"COMP_IMP_{c}_NOME") or f"Componente {c}"),
                "macroarea": str(row.get(f"COMP_IMP_{c}_MACROAREA") or ""),
                "prezzo": _prezzo(p, unita),
                "fascia": str(fascia) if _pieno(fascia) else "",
                "scaglione": f"{euro(da or 0, 0)}-{euro(a, 0) if a else 'oltre'}" if (da or a) else "",
                "opzionale": str(row.get(f"COMP_IMP_{c}_TIPOLOGIA") or "") == "OPZIONALE",
            })
    return out


def sconti(row: pd.Series) -> list[str]:
    """Sconti dichiarati, in chiaro, con condizioni e validità."""
    out = []
    for s in range(1, 16):
        nome = row.get(f"SCONTO_{s}_NOME")
        if not _pieno(nome):
            if f"SCONTO_{s}_NOME" not in row.index:
                break
            continue
        valori = []
        for p in range(1, 6):
            v = _num(row.get(f"SCONTO_{s}_PREZZO_{p}_VAL"))
            if v is None:
                continue
            unita = str(row.get(f"SCONTO_{s}_PREZZO_{p}_UNITA") or "")
            txt = f"{euro(v, 2)}%" if unita == "Percentuale" else _prezzo(v, unita)
            da, fino = _num(row.get(f"SCONTO_{s}_PREZZO_{p}_DA")), _num(row.get(f"SCONTO_{s}_PREZZO_{p}_FINO"))
            if fino:
                txt += f" ({euro(da or 0, 0)}-{euro(fino, 0)})"
            valori.append(txt)
        dettagli = [x for x in (
            str(row.get(f"SCONTO_{s}_VALIDITA") or "") if _pieno(row.get(f"SCONTO_{s}_VALIDITA")) else "",
            str(row.get(f"SCONTO_{s}_COND_APP") or "") if _pieno(row.get(f"SCONTO_{s}_COND_APP")) else "",
            f"su {row.get(f'SCONTO_{s}_CODICE_COMP')}" if _pieno(row.get(f"SCONTO_{s}_CODICE_COMP")) else "",
            f"per {int(_num(row.get(f'SCONTO_{s}_DURATA')))} mesi" if _num(row.get(f"SCONTO_{s}_DURATA")) else "",
            "non soggetto a IVA" if str(row.get(f"SCONTO_{s}_IVA")) == "NO" else "",
        ) if x]
        out.append(f"{nome}: −{' / '.join(valori) or '?'}" + (f" [{'; '.join(dettagli)}]" if dettagli else ""))
    return out


_IDX = {"PUN": "PUN", "PSV": "PSV", "TTF": "TTF", "Psbil": "PSbil", "PE": "PE", "Cmem": "Cmem", "Pfor": "Pfor"}


def note(row: pd.Series) -> list[str]:
    """Informazioni utili per capire l'offerta."""
    out = []
    durata = _num(row.get("DURATA"))
    if durata is not None:
        out.append("Condizioni economiche a durata indeterminata" if durata < 0 or durata >= 99
                   else f"Prezzo valido {int(durata)} mesi")
    if "ariabil" in str(row.get("TIPO_OFFERTA")):
        idx = []
        for col in row.index:
            if col.startswith("IDX_") and not col.endswith("_COEFF") and _vero(row[col]):
                nome = col[4:]
                base, _, per = nome.partition("_")
                coeff = _num(row.get(f"{col}_COEFF"))
                idx.append(f"{_IDX.get(base, base)} {dict(Trim='trimestrale', Bim='bimestrale', Men='mensile').get(per, per)}"
                           + (f" × {euro(coeff, 2)}" if coeff not in (None, 1.0) else ""))
        out.append("Indicizzata a " + (", ".join(idx) if idx else "indice non dichiarato"))
    reg = [c[9:] for c in row.index if c.startswith("REGOLATA_") and _vero(row[c])]
    if reg:
        out.append("Componenti regolate: " + ", ".join(r.replace("_", " ") for r in reg))
    comp = componenti(row)
    if any("FER" in c["macroarea"] for c in comp):
        out.append("Energia verde (componente FER)")
    if any(c["scaglione"] for c in comp):
        out.append("Prezzi a scaglioni di consumo")
    if any(c["opzionale"] for c in comp):
        out.append("Ha componenti opzionali")
    if _vero(row.get("MOD_ATTIVAZIONE_Solo web")):
        out.append("Attivabile solo da web")
    pag = [n.replace("PAGAMENTO_", "").replace("_", " ") for n in row.index
           if n.startswith("PAGAMENTO_") and not n.endswith("_DESC") and _vero(row[n])]
    if pag:
        out.append("Pagamento: " + ", ".join(pag))
    serv = [n.replace("SERVIZIO_", "") for n in row.index if n.startswith("SERVIZIO_") and _vero(row[n])]
    if serv:
        out.append("Servizi aggiuntivi: " + ", ".join(serv))
    lim = [n[5:-11].replace("_", " ") for n in row.index
           if n.startswith("COND_") and n.endswith("_LIMITANTE") and str(row[n]).startswith("Si")]
    if lim:
        out.append("Condizioni limitanti: " + ", ".join(lim))
    if str(row.get("OFFERTA_SINGOLA")).upper() == "NO":
        out.append("Sottoscrivibile solo in dual fuel")
    cmin, cmax = _num(row.get("CONSUMO_MIN")), _num(row.get("CONSUMO_MAX"))
    if cmin or cmax:
        out.append(f"Consumi ammessi {euro(cmin or 0, 0)}-{euro(cmax, 0) if cmax else 'oltre'}")
    if _pieno(row.get("DATA_FINE")):
        out.append("Offerta valida fino al " + str(row.get("DATA_FINE")).split("_")[0])
    return out
