Prima del codice, la diagnosi — perché entrambe le anomalie hanno la stessa radice e una delle due potrebbe non essere un problema di filtro.

La radice comune
Il flattener appiattisce di ogni ComponenteImpresa solo PREZZO, UNITA, FASCIA, VALIDITA. Lascia cadere:

Campo AU	Dove sta	Cosa perdete
MACROAREA	ComponenteImpresa	distinguere "Prezzo Energia" da "Sbilanciamento" → Anomalia 1
TIPOLOGIA	ComponenteImpresa	componenti STANDARD vs OPZIONALE (le opzionali non vanno in SAS)
NOME / DESCRIZIONE	ComponenteImpresa	diagnostica leggibile
CONSUMO_DA / CONSUMO_A	IntervalloPrezzi	selezionare lo scaglione giusto → il vostro seen_fasce prende il primo
Il filtro "elegante" che chiedete non è scrivibile sul parquet attuale: il campo che discrimina è stato scartato in fase di parsing. Tutto il resto è inferenza dalla posizione nell'array, ed è esattamente il motivo per cui is_fake è fragile.

Anomalia 1: quasi certamente non è un'offerta da escludere
MONO2026DOME129EE. Il nome si legge: MONOrario 2026 DOMEstico 0.129 €/kWh EE. Il prezzo energia esiste nell'XML — non è arrivato nel parquet.

Se costruite un filtro che esclude le offerte senza prezzo energia, non state replicando il Portale: state nascondendo un bug di parsing, e con esso tutta la classe di offerte caricate nello stesso modo. In un tool di competitive intelligence è il tipo di errore che vi fa perdere un concorrente dal radar.

Verifica decisiva, 2 minuti:

python
Copy
# scripts/dump_offerta_xml.py
"""Estrae il nodo <offerta> grezzo per un COD_OFFERTA. Serve a capire DOVE sta
il prezzo che il flattener non vede.

    python scripts/dump_offerta_xml.py --cod MONO2026DOME129EE
    python scripts/dump_offerta_xml.py --cod CasaFix1206260300 --commodity E
"""
from __future__ import annotations

import argparse
import gzip
from pathlib import Path

from lxml import etree

NS = "{http://www.acquirenteunico.it/schemas/SII_AU/OffertaRetail/01}"


def iter_raw_files(root: Path, commodity: str | None, date_hint: str | None):
    pattern = f"**/PO_Offerte_{commodity or '*'}_MLIBERO_*.xml*"
    files = sorted(root.glob(pattern), reverse=True)
    if date_hint:
        d = date_hint.replace("-", "")
        files = [f for f in files if d in f.name] or files
    return files


def open_maybe_gz(path: Path):
    return gzip.open(path, "rb") if path.suffix == ".gz" else path.open("rb")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cod", required=True)
    ap.add_argument("--commodity", default=None, choices=["E", "G", "D"])
    ap.add_argument("--date", default=None, help="YYYY-MM-DD, filtro sul nome file")
    ap.add_argument("--raw", default="data/raw")
    args = ap.parse_args()

    files = iter_raw_files(Path(args.raw), args.commodity, args.date)
    if not files:
        raise SystemExit(f"Nessun XML in {args.raw}")

    for path in files:
        with open_maybe_gz(path) as fh:
            for _, node in etree.iterparse(fh, tag=f"{NS}offerta"):
                cod = node.findtext(f".//{NS}COD_OFFERTA")
                if cod and cod.strip() == args.cod:
                    print(f"=== {path} ===\n")
                    print(etree.tostring(node, pretty_print=True,
                                         encoding="unicode"))
                    # Riepilogo delle componenti, per confronto col parquet
                    print("--- ComponenteImpresa presenti nell'XML ---")
                    for k, comp in enumerate(node.findall(f".//{NS}ComponenteImpresa"), 1):
                        print(f"[{k}] NOME={comp.findtext(f'{NS}NOME')!r} "
                              f"MACROAREA={comp.findtext(f'{NS}MACROAREA')!r} "
                              f"TIPOLOGIA={comp.findtext(f'{NS}TIPOLOGIA')!r}")
                        for j, iv in enumerate(comp.findall(f"{NS}IntervalloPrezzi"), 1):
                            print(f"    INT_{j}: PREZZO={iv.findtext(f'{NS}PREZZO')!r} "
                                  f"UM={iv.findtext(f'{NS}UNITA_MISURA')!r} "
                                  f"FASCIA={iv.findtext(f'{NS}FASCIA_COMPONENTE')!r} "
                                  f"DA={iv.findtext(f'{NS}CONSUMO_DA')!r} "
                                  f"A={iv.findtext(f'{NS}CONSUMO_A')!r}")
                    # Elementi fratelli che il flattener potrebbe ignorare
                    print("\n--- Altri figli diretti di <offerta> ---")
                    for child in node:
                        print(" ", etree.QName(child).localname)
                    return
                node.clear()
    raise SystemExit(f"COD_OFFERTA '{args.cod}' non trovato.")


if __name__ == "__main__":
    main()
Se 0.129 compare in un ComponenteImpresa oltre il quinto, o in un IntervalloPrezzi oltre il quinto, o in un elemento fratello che il flattener non legge, il fix è nel flattener e il filtro serve solo come rete di sicurezza.

Anomalia 2: due ipotesi, conseguenze diverse
L'osservazione su F1=F2=F3 è solida, ma "il PO le scarta" e "il PO le riclassifica come monorarie" producono lo stesso effetto sulla lista A Fasce e effetti opposti su quella Monorario.

Test: cercate CasaFix1206260300 nel ranking Monorario del Portale a 2700 kWh. Se c'è → riclassifica. Se non c'è da nessuna parte → esclusione (o l'offerta non è pubblicata affatto, terza ipotesi).

Nel codice qui sotto la scelta è un parametro, non un assunto.

Terza ipotesi da escludere prima: comune='F205' con provincia='015'. 015 è ISTAT Milano, F205 è il codice Belfiore. Se nel parquet COMUNE contiene ISTAT (015146, come scrivete nel testo), il filtro comune non matcha mai e sopravvivono solo le offerte a copertura nazionale — le offerte comunali spariscono. Verificate con:

python
Copy
df.loc[df['COMUNE'].notna() & (df['COMUNE'].astype(str) != ''), 'COMUNE'].value_counts().head(20)
1. parse/flattener.py — emettere i campi scartati
python
Copy
# ==============================================================================
# In flatten_offer(), nel loop sui ComponenteImpresa
# ==============================================================================
# NS = "{http://www.acquirenteunico.it/schemas/SII_AU/OffertaRetail/01}"

for c, comp in enumerate(offerta.findall(f"{NS}ComponenteImpresa")[:5], start=1):
    # NUOVI: livello componente. Senza questi non è possibile distinguere
    # il Prezzo Energia dallo Sbilanciamento, né STANDARD da OPZIONALE.
    macro = (comp.findtext(f"{NS}MACROAREA") or "").strip()
    tipol = (comp.findtext(f"{NS}TIPOLOGIA") or "").strip()
    record[f"COMP_IMP_{c}_MACROAREA_COD"] = macro or None
    record[f"COMP_IMP_{c}_MACROAREA"] = DECODE_MAPS["MACROAREA_COMP"].get(macro, macro) or None
    record[f"COMP_IMP_{c}_TIPOLOGIA_COD"] = tipol or None
    record[f"COMP_IMP_{c}_NOME"] = (comp.findtext(f"{NS}NOME") or "").strip() or None
    record[f"COMP_IMP_{c}_DESCRIZIONE"] = (comp.findtext(f"{NS}DESCRIZIONE") or "").strip() or None

    intervalli = comp.findall(f"{NS}IntervalloPrezzi")
    record[f"COMP_IMP_{c}_N_INTERVALLI"] = len(intervalli)   # rileva il troncamento a 5
    if len(intervalli) > 5:
        record.setdefault("PARSE_WARNINGS", []).append(
            f"COMP_IMP_{c}: {len(intervalli)} intervalli, troncati a 5"
        )

    for i, iv in enumerate(intervalli[:5], start=1):
        base = f"COMP_IMP_{c}_INT_{i}"
        # ... campi già esistenti: _PREZZO, _UNITA, _FASCIA, _VALIDITA ...
        # NUOVI: scaglioni di consumo. Senza questi non si sa quale
        # IntervalloPrezzi applicare a un dato consumo annuo.
        record[f"{base}_CONSUMO_DA"] = (iv.findtext(f"{NS}CONSUMO_DA") or "").strip() or None
        record[f"{base}_CONSUMO_A"] = (iv.findtext(f"{NS}CONSUMO_A") or "").strip() or None

# Conteggio complessivo: se > 5 il flattener sta perdendo componenti.
_tutti = offerta.findall(f"{NS}ComponenteImpresa")
record["N_COMP_IMP_XML"] = len(_tutti)
record["COMP_IMP_TRONCATE"] = len(_tutti) > 5
N_COMP_IMP_XML e COMP_IMP_TRONCATE sono il controllo diretto sull'ipotesi "il prezzo energia è oltre il quinto componente".

2. engine/component_matrix.py — la trasformazione pulita
Sostituisce il confronto posizionale con wide → long → pivot. Autonomo: non dipende da altri moduli, si innesta sul codice che avete adesso.

python
Copy
"""engine/component_matrix.py

Ricostruisce per ogni offerta la matrice dei prezzi volumetrici per fascia
partendo dalle colonne COMP_IMP_{c}_INT_{i}_*.

Perché non confrontare COMP_IMP_2_INT_1 con COMP_IMP_2_INT_2:
nello schema AU, IntervalloPrezzi è un array che porta *insieme* la fascia
(FASCIA_COMPONENTE) e lo scaglione di consumo (CONSUMO_DA/CONSUMO_A). L'indice
{i} non ha semantica: assumere INT_1=F1, INT_2=F2, INT_3=F3 significa fidarsi
dell'ordine di caricamento del venditore. Inoltre la componente energia non sta
sempre in COMP_IMP_2.
"""
from __future__ import annotations

import logging
import re

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

BANDE = ("F1", "F2", "F3")

# Fascia dichiarata -> bande su cui il prezzo si applica.
# Accetta sia i codici SII grezzi sia le label transcodificate.
_FASCIA_BANDE = {
    "01": ("F1",), "monorario/f1": ("F1",), "monorario": ("F1",), "f1": ("F1",),
    "02": ("F2",), "f2": ("F2",),
    "03": ("F3",), "f3": ("F3",),
    "91": ("F2", "F3"), "f2+f3": ("F2", "F3"), "f2 + f3": ("F2", "F3"),
    "92": ("F1", "F3"), "f1+f3": ("F1", "F3"), "f1 + f3": ("F1", "F3"),
    "93": ("F1", "F2"), "f1+f2": ("F1", "F2"), "f1 + f2": ("F1", "F2"),
}

# TIPOLOGIA_FASCE che identificano un'offerta monoraria: il prezzo dichiarato
# come 'monorario/F1' vale sull'intero consumo, non sulla sola F1.
_TIPOLOGIE_MONO = {"01", "monorario/f1", "monorario"}

KIND_KWH, KIND_SMC, KIND_KW = "KWH", "SMC", "KW"
KIND_FISSO, KIND_PCT, KIND_UNKNOWN = "FISSO", "PERCENTUALE", "SCONOSCIUTA"
KIND_VOLUMETRICI = (KIND_KWH, KIND_SMC)

_VUOTI = {"", "nan", "none", "null", "<na>"}


def _norm(v) -> str:
    return re.sub(r"\s+", " ", str(v if v is not None else "").strip().lower())


def _to_num(s: pd.Series) -> pd.Series:
    """Parsing numerico tollerante a virgola decimale e separatore migliaia."""
    raw = s.astype(str).str.strip()
    txt = raw.str.replace(r"[^\d,.\-]", "", regex=True)
    # '1.234,56' -> '1234.56' ; '0,13' -> '0.13' ; '0.13' invariato
    ha_virgola = txt.str.contains(",", na=False)
    txt = txt.where(~ha_virgola, txt.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    out = pd.to_numeric(txt, errors="coerce")
    scarti = out.isna() & ~raw.str.lower().isin(_VUOTI)
    if scarti.any():
        logger.warning("%s: %d valori non parsabili. Esempi: %s",
                       s.name, int(scarti.sum()), raw[scarti].unique()[:5].tolist())
    return out


def _str_col(df: pd.DataFrame, name: str) -> pd.Series:
    if name in df.columns:
        return df[name].astype(str)
    return pd.Series("", index=df.index, dtype=object)


def classify_unita(unita) -> str:
    """Ordine obbligatorio: 'kwh' contiene 'kw'."""
    n = _norm(unita)
    if n in _VUOTI:
        return KIND_UNKNOWN
    if "kwh" in n:
        return KIND_KWH
    if "smc" in n:
        return KIND_SMC
    if "kw" in n:
        return KIND_KW
    if "percent" in n or "%" in n:
        return KIND_PCT
    if n.startswith("€") or "euro" in n or n == "€/anno":
        return KIND_FISSO
    return KIND_UNKNOWN


def resolve_bande(fascia, tipologia_fasce) -> tuple[str, ...]:
    """Bande su cui si applica il prezzo. Tupla vuota = fascia non interpretabile.

    >>> resolve_bande('F2+F3', 'F1, F2, F3')
    ('F2', 'F3')
    >>> resolve_bande('monorario/F1', 'monorario/F1')
    ('F1', 'F2', 'F3')
    >>> resolve_bande('monorario/F1', 'F1, F2, F3')
    ('F1',)
    """
    if _norm(tipologia_fasce) in _TIPOLOGIE_MONO:
        return BANDE                      # monoraria: vale su tutto il consumo
    f = _norm(fascia)
    if f in _VUOTI:
        return BANDE                      # componente senza fascia: su tutto
    return _FASCIA_BANDE.get(f, ())


# ==============================================================================
# wide -> long
# ==============================================================================
def build_long(df: pd.DataFrame, max_comp: int = 5, max_int: int = 5,
               consumo_annuo: float | None = None) -> pd.DataFrame:
    """Una riga per (offerta, componente, intervallo). Preserva df.index in 'row'."""
    tipologia = _str_col(df, "TIPOLOGIA_FASCE")
    blocchi = []

    for c in range(1, max_comp + 1):
        pcol = f"COMP_IMP_{c}_INT_1_PREZZO"
        if pcol not in df.columns and f"COMP_IMP_{c}_INT_1_UNITA" not in df.columns:
            continue
        for i in range(1, max_int + 1):
            base = f"COMP_IMP_{c}_INT_{i}"
            if f"{base}_PREZZO" not in df.columns:
                continue
            blk = pd.DataFrame({
                "row": df.index,
                "comp": c,
                "intervallo": i,
                "prezzo": _to_num(df[f"{base}_PREZZO"]).values,
                "unita": _str_col(df, f"{base}_UNITA").values,
                "fascia": _str_col(df, f"{base}_FASCIA").values,
                "validita": _str_col(df, f"{base}_VALIDITA").values,
                "consumo_da": _to_num(_str_col(df, f"{base}_CONSUMO_DA")).values,
                "consumo_a": _to_num(_str_col(df, f"{base}_CONSUMO_A")).values,
                # livello componente: presenti solo dopo la patch al flattener
                "macroarea": _str_col(df, f"COMP_IMP_{c}_MACROAREA").values,
                "macroarea_cod": _str_col(df, f"COMP_IMP_{c}_MACROAREA_COD").values,
                "tipologia_comp": _str_col(df, f"COMP_IMP_{c}_TIPOLOGIA_COD").values,
                "nome_comp": _str_col(df, f"COMP_IMP_{c}_NOME").values,
                "tipologia_fasce": tipologia.values,
            })
            blocchi.append(blk)

    if not blocchi:
        return pd.DataFrame(columns=["row", "comp", "intervallo", "prezzo", "unita",
                                     "fascia", "kind", "macroarea"])

    long = pd.concat(blocchi, ignore_index=True)
    long = long[long["prezzo"].notna() & (long["prezzo"] != 0)]
    long["kind"] = long["unita"].map(classify_unita)
    long = _select_scaglione(long, consumo_annuo)
    return long.reset_index(drop=True)


def _select_scaglione(long: pd.DataFrame, consumo_annuo: float | None) -> pd.DataFrame:
    """Un solo IntervalloPrezzi per (offerta, componente, fascia).

    Con CONSUMO_DA/CONSUMO_A disponibili si seleziona lo scaglione applicabile.
    Senza, si tiene il primo intervallo — comportamento del codice attuale,
    corretto quando gli intervalli sono fasce, sbagliato quando sono scaglioni.
    """
    long = long.copy()
    long["_k"] = (long["row"].astype(str) + "\x1f" + long["comp"].astype(str)
                  + "\x1f" + long["fascia"].map(_norm))

    ha_scaglioni = long[["consumo_da", "consumo_a"]].notna().any(axis=1)
    if consumo_annuo is None or not ha_scaglioni.any():
        if ha_scaglioni.any():
            logger.warning("CONSUMO_DA/A presenti ma consumo_annuo non fornito: "
                           "selezionato il primo intervallo di ogni componente.")
        out = long.sort_values(["row", "comp", "intervallo"]).drop_duplicates("_k")
        return out.drop(columns="_k")

    da = long["consumo_da"].fillna(-np.inf)
    a = long["consumo_a"].fillna(np.inf)
    applicabile = (consumo_annuo >= da) & (consumo_annuo <= a)

    sel = long[applicabile]
    resto = long[~long["_k"].isin(set(sel["_k"]))]
    resto = resto.sort_values(["row", "comp", "intervallo"]).drop_duplicates("_k")
    out = pd.concat([sel, resto]).sort_values(["row", "comp", "intervallo"])
    return out.drop_duplicates("_k").drop(columns="_k")


# ==============================================================================
# long -> matrice prezzi per banda
# ==============================================================================
def explode_bande(long: pd.DataFrame) -> pd.DataFrame:
    """Espande ogni componente volumetrica sulle bande su cui si applica."""
    vol = long[long["kind"].isin(KIND_VOLUMETRICI)].copy()
    if vol.empty:
        return vol.assign(banda=pd.Series(dtype=object))
    vol["bande"] = [resolve_bande(f, t) for f, t in
                    zip(vol["fascia"], vol["tipologia_fasce"])]
    non_risolte = vol["bande"].map(len) == 0
    if non_risolte.any():
        logger.warning("%d componenti con FASCIA non interpretabile: %s",
                       int(non_risolte.sum()),
                       vol.loc[non_risolte, "fascia"].unique()[:5].tolist())
    vol = vol[~non_risolte]
    return vol.explode("bande").rename(columns={"bande": "banda"})


def price_matrix(df: pd.DataFrame, long: pd.DataFrame | None = None,
                 consumo_annuo: float | None = None) -> pd.DataFrame:
    """Prezzo volumetrico effettivo per banda, in €/kWh (o €/Smc).

    Somma tutte le componenti volumetriche che ricadono sulla banda: energia,
    sbilanciamento, dispacciamento dichiarato dal venditore, ecc.
    Colonne: F1, F2, F3. NaN = banda non prezzata.
    """
    long = build_long(df, consumo_annuo=consumo_annuo) if long is None else long
    exp = explode_bande(long)
    m = pd.DataFrame(index=df.index, columns=list(BANDE), dtype=float)
    if exp.empty:
        return m
    piv = exp.pivot_table(index="row", columns="banda", values="prezzo",
                          aggfunc="sum")
    for b in BANDE:
        if b in piv.columns:
            m[b] = piv[b]
    return m


def multiorario_flags(df: pd.DataFrame, long: pd.DataFrame | None = None,
                      tol: float = 1e-6,
                      consumo_annuo: float | None = None) -> pd.DataFrame:
    """Rileva le false multiorarie: prezzo identico su tutte le bande prezzate.

    Copre in un colpo solo:
      - triorario dichiarato con F1 = F2 = F3
      - biorario dichiarato con F1 = F2+F3
      - multiorario dichiarato ma prezzato con un'unica componente senza fascia

    Colonne: n_bande_prezzate, n_prezzi_distinti, prezzo_min, prezzo_max,
             spread_assoluto, spread_relativo, falsa_multioraria
    """
    long = build_long(df, consumo_annuo=consumo_annuo) if long is None else long
    m = price_matrix(df, long=long)

    n_bande = m.notna().sum(axis=1)
    p_min, p_max = m.min(axis=1), m.max(axis=1)
    spread = (p_max - p_min).fillna(0.0)
    # Conteggio dei prezzi distinti con arrotondamento a 6 decimali: evita che
    # differenze di rappresentazione float contino come differenziazione reale.
    n_prezzi = m.round(6).nunique(axis=1, dropna=True)

    out = pd.DataFrame({
        "n_bande_prezzate": n_bande,
        "n_prezzi_distinti": n_prezzi,
        "prezzo_min": p_min,
        "prezzo_max": p_max,
        "spread_assoluto": spread,
        "spread_relativo": np.where(p_max > 0, spread / p_max, 0.0),
    }, index=df.index)
    out["falsa_multioraria"] = (out["n_bande_prezzate"] >= 2) & (spread <= tol)
    return out


# ==============================================================================
# Completezza del prezzo energia
# ==============================================================================
# Codici MACROAREA che identificano la materia prima. DA CONFERMARE con
# scripts/audit_componenti.py: la tabella dei codici AU non è verificata.
MACROAREE_ENERGIA_DEFAULT: set[str] = set()

_KEYWORD_ENERGIA = re.compile(
    r"prezzo\s+(energia|fisso|materia|gas|luce)|materia\s+prima|"
    r"corrispettivo\s+energia|componente\s+energia|pe\b|p_?fisso",
    re.IGNORECASE,
)
_KEYWORD_NON_ENERGIA = re.compile(
    r"sbilanciam|commercializ|dispacciam|oneri|perdite|trasporto|"
    r"distribuz|garanzia|origine|certificat|ricarica|cauzion",
    re.IGNORECASE,
)


def energia_flags(df: pd.DataFrame, long: pd.DataFrame | None = None,
                  macroaree_energia: set[str] | None = None,
                  soglia_kwh: float = 0.03, soglia_smc: float = 0.10,
                  frazione_mediana: float = 0.40,
                  consumo_annuo: float | None = None) -> pd.DataFrame:
    """Verifica che l'offerta dichiari un prezzo energia plausibile.

    Tre livelli, dal più affidabile al più euristico:
      1. MACROAREA in macroaree_energia (strutturale, richiede la patch al
         flattener + i codici confermati da audit_componenti.py)
      2. NOME della componente che matcha le keyword energia e non quelle
         accessorie
      3. Soglia sul prezzo volumetrico totale: assoluta e relativa alla mediana
         del campione confrontabile

    Il livello 3 da solo non basta a decidere: serve a mettere in quarantena,
    non a nascondere. Vedi 'motivo'.
    """
    macroaree = MACROAREE_ENERGIA_DEFAULT if macroaree_energia is None else macroaree_energia
    long = build_long(df, consumo_annuo=consumo_annuo) if long is None else long

    vol = long[long["kind"].isin(KIND_VOLUMETRICI)]
    tot_vol = vol.groupby("row")["prezzo"].sum().reindex(df.index).fillna(0.0)

    # --- livello 1: MACROAREA ---
    ha_macroarea = (long["macroarea_cod"].map(_norm) != "").groupby(long["row"]).any() \
        .reindex(df.index).fillna(False)
    if macroaree:
        en_macro = vol["macroarea_cod"].map(_norm).isin({_norm(x) for x in macroaree})
        by_macro = en_macro.groupby(vol["row"]).any().reindex(df.index).fillna(False)
    else:
        by_macro = pd.Series(False, index=df.index)

    # --- livello 2: NOME componente ---
    nomi = vol["nome_comp"].fillna("").astype(str)
    en_nome = nomi.str.contains(_KEYWORD_ENERGIA) & ~nomi.str.contains(_KEYWORD_NON_ENERGIA)
    by_nome = en_nome.groupby(vol["row"]).any().reindex(df.index).fillna(False)

    # --- livello 3: soglie ---
    is_ee = (df.get("commodity", pd.Series("E", index=df.index)) == "E")
    soglia_abs = np.where(is_ee, soglia_kwh, soglia_smc)
    mediana = tot_vol[tot_vol > 0].median()
    soglia_rel = frazione_mediana * mediana if pd.notna(mediana) else 0.0
    soglia = np.maximum(soglia_abs, soglia_rel)
    sopra_soglia = tot_vol.to_numpy() >= soglia

    out = pd.DataFrame({
        "prezzo_volumetrico_totale": tot_vol,
        "ha_macroarea": ha_macroarea,
        "energia_da_macroarea": by_macro,
        "energia_da_nome": by_nome,
        "sopra_soglia": sopra_soglia,
        "soglia_applicata": soglia,
    }, index=df.index)

    strutturale_disponibile = out["ha_macroarea"] & bool(macroaree)
    out["prezzo_energia_ok"] = np.where(
        strutturale_disponibile,
        out["energia_da_macroarea"],
        out["energia_da_nome"] | out["sopra_soglia"],
    )
    out["motivo"] = np.select(
        [
            out["prezzo_energia_ok"],
            strutturale_disponibile & ~out["energia_da_macroarea"],
            ~out["sopra_soglia"],
        ],
        ["", "MACROAREA_ENERGIA_ASSENTE", "PREZZO_VOLUMETRICO_IMPLAUSIBILE"],
        default="PREZZO_ENERGIA_NON_IDENTIFICATO",
    )
    return out
3. filter_offers riscritta
python
Copy
# ==============================================================================
# In cima a engine/sas_calculator_fast.py
# ==============================================================================
import logging
from engine import component_matrix as cm

logger = logging.getLogger(__name__)

ISTAT_REGIONI = {
    'Piemonte': '01', "Valle d'Aosta": '02', 'Lombardia': '03',
    'Trentino-Alto Adige': '04', 'Veneto': '05', 'Friuli-Venezia Giulia': '06',
    'Liguria': '07', 'Emilia-Romagna': '08', 'Toscana': '09', 'Umbria': '10',
    'Marche': '11', 'Lazio': '12', 'Abruzzo': '13', 'Molise': '14',
    'Campania': '15', 'Puglia': '16', 'Basilicata': '17', 'Calabria': '18',
    'Sicilia': '19', 'Sardegna': '20',
}
_TERRITORIO_NAZIONALE = {'', 'nan', 'none', 'null', '<na>'}


# ==============================================================================
# Metodo della classe FastSASCalculator
# ==============================================================================
    def filter_offers(self, commodity='E', tipo_offerta='Fisso',
                      tipo_cliente='Domestico', fasce='A Fasce',
                      regione='Lombardia', provincia='015', comune=None,
                      consumo_annuo=None,
                      falsa_multioraria='escludi',
                      richiedi_prezzo_energia=True,
                      macroaree_energia=None,
                      tol_multiorario=1e-6):
        """Replica la selezione del Portale Offerte.

        falsa_multioraria:
            'escludi'      -> le offerte con prezzo identico su tutte le bande
                              non compaiono né in 'A Fasce' né in 'Monorario'
            'riclassifica' -> compaiono in 'Monorario' (ipotesi alternativa:
                              il PO le tratta come monorarie)
            'mantieni'     -> comportamento pre-fix, per il confronto A/B

        Le esclusioni sono tracciate in self.diagnostica_esclusioni.
        """
        if falsa_multioraria not in ('escludi', 'riclassifica', 'mantieni'):
            raise ValueError(f"falsa_multioraria non valido: {falsa_multioraria!r}")

        f = self.df
        n0 = len(f)
        self.diagnostica_esclusioni = {}
        self._offerte_scartate = None

        def _drop(mask_keep, etichetta):
            nonlocal f
            prima = len(f)
            f = f[mask_keep]
            persi = prima - len(f)
            if persi:
                self.diagnostica_esclusioni[etichetta] = persi
            return f

        # --- Commodity ---
        _drop(f['commodity'] == commodity, 'commodity')

        # --- Tipo di prezzo: match esatto, non substring ---
        if tipo_offerta and tipo_offerta != 'Tutte':
            v = f['TIPO_OFFERTA'].astype(str).str.strip().str.casefold()
            _drop(v == tipo_offerta.strip().casefold(), f'tipo_offerta={tipo_offerta}')

        # --- Tipo cliente: match esatto ---
        # FIX: rf'\b{tipo_cliente}\b' NON esclude 'Condominio Uso Domestico
        # (Gas)': il word boundary matcha anche all'interno della frase.
        if tipo_cliente and tipo_cliente != 'Tutti':
            v = f['TIPO_CLIENTE'].astype(str).str.strip().str.casefold()
            _drop(v == tipo_cliente.strip().casefold(), f'tipo_cliente={tipo_cliente}')

        # --- Territorialità ---
        def _territoriale(col, target):
            v = f[col].astype(str).str.strip()
            nazionale = v.str.casefold().isin(_TERRITORIO_NAZIONALE)
            return nazionale | (v == str(target))

        if regione and regione != 'Tutte' and 'REGIONE' in f.columns:
            if regione not in ISTAT_REGIONI:
                raise KeyError(f"Regione '{regione}' non mappata sui codici ISTAT.")
            _drop(_territoriale('REGIONE', ISTAT_REGIONI[regione]), f'regione={regione}')

        if provincia and 'PROVINCIA' in f.columns:
            _drop(_territoriale('PROVINCIA', provincia), f'provincia={provincia}')

        # comune=None per default: passare un codice nel formato sbagliato
        # (Belfiore 'F205' contro ISTAT '015146') scarta tutte le offerte
        # comunali lasciando solo quelle nazionali.
        if comune and 'COMUNE' in f.columns:
            _drop(_territoriale('COMUNE', comune), f'comune={comune}')

        _drop(~f['NOME_OFFERTA'].astype(str).str.contains('Sottocosto', case=False, na=False),
              'nome_sottocosto')

        if f.empty:
            return f

        # --- Matrice componenti: calcolata una volta e riusata ---
        long = cm.build_long(f, consumo_annuo=consumo_annuo)
        flags_mo = cm.multiorario_flags(f, long=long, tol=tol_multiorario)
        self.ultima_price_matrix = cm.price_matrix(f, long=long)
        self.ultimi_flags_multiorario = flags_mo

        # --- Fasce, con la policy sulle false multiorarie ---
        if commodity == 'E' and fasce and fasce != 'Tutte' and 'TIPOLOGIA_FASCE' in f.columns:
            tipol = f['TIPOLOGIA_FASCE'].astype(str).map(cm._norm)
            dichiarata_mono = tipol.isin(cm._TIPOLOGIE_MONO)
            falsa = flags_mo['falsa_multioraria'].reindex(f.index).fillna(False)

            if fasce in ('A Fasce', 'Biorario', 'Multiorario'):
                keep = ~dichiarata_mono
                if falsa_multioraria in ('escludi', 'riclassifica'):
                    keep &= ~falsa
                _drop(keep, f'fasce={fasce}')
            elif fasce == 'Monorario':
                keep = dichiarata_mono.copy()
                if falsa_multioraria == 'riclassifica':
                    keep |= falsa
                _drop(keep, 'fasce=Monorario')
            else:
                raise ValueError(f"Valore 'fasce' non gestito: {fasce!r}")

            if falsa_multioraria != 'mantieni':
                self.diagnostica_esclusioni['false_multiorarie'] = int(falsa.sum())

        # --- Completezza del prezzo energia ---
        if richiedi_prezzo_energia and not f.empty:
            en = cm.energia_flags(f, long=long, macroaree_energia=macroaree_energia,
                                  consumo_annuo=consumo_annuo)
            en = en.reindex(f.index)
            ko = ~en['prezzo_energia_ok'].fillna(False)
            if ko.any():
                col_cod = 'CODICE_OFFERTA' if 'CODICE_OFFERTA' in f.columns else 'COD_OFFERTA'
                self._offerte_scartate = pd.DataFrame({
                    'COD_OFFERTA': f.loc[ko, col_cod],
                    'NOME_OFFERTA': f.loc[ko, 'NOME_OFFERTA'],
                    'prezzo_volumetrico': en.loc[ko, 'prezzo_volumetrico_totale'].round(5),
                    'soglia': en.loc[ko, 'soglia_applicata'].round(5),
                    'motivo': en.loc[ko, 'motivo'],
                })
                logger.warning(
                    "%d offerte senza prezzo energia identificabile. Prime: %s",
                    int(ko.sum()),
                    self._offerte_scartate['COD_OFFERTA'].head(5).tolist(),
                )
            _drop(~ko, 'prezzo_energia_assente')
            self.ultimi_flags_energia = en

        logger.info("filter_offers: %d -> %d offerte. Esclusioni: %s",
                    n0, len(f), self.diagnostica_esclusioni)
        return f

    @property
    def offerte_scartate(self) -> pd.DataFrame:
        """Offerte escluse per prezzo energia non identificabile, con motivo.
        Da esporre in dashboard: un'esclusione non spiegabile è un bug nascosto."""
        return getattr(self, '_offerte_scartate', None)
Da esporre in app.py, sotto il ranking:

python
Copy
with st.expander(f"Offerte escluse dal ranking ({sum(calc.diagnostica_esclusioni.values())})"):
    st.write(calc.diagnostica_esclusioni)
    if calc.offerte_scartate is not None:
        st.dataframe(calc.offerte_scartate, use_container_width=True)
Chiamata aggiornata:

python
Copy
filtered = calc.filter_offers(
    commodity='E', fasce=fasce, tipo_offerta=tipo_offerta, regione=regione,
    provincia='015',
    comune=None,                      # fino a quando il formato non è verificato
    consumo_annuo=2700,
    falsa_multioraria='escludi',      # -> 'riclassifica' se il test sul PO lo conferma
)
E rimuovete res = res[res['PREZZO_UNITARIO'] > 0]: era il surrogato grezzo di questo controllo, e taglia anche offerte legittime.

4. scripts/audit_componenti.py
Scopre dai vostri XML i codici MACROAREA reali e quante offerte sono nelle due categorie sospette.

python
Copy
"""Enumera MACROAREA / TIPOLOGIA delle ComponenteImpresa sull'XML grezzo e
quantifica le offerte senza prezzo energia e le false multiorarie.

    python scripts/audit_componenti.py --commodity E --date 2026-08-25
"""
from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

from lxml import etree

NS = "{http://www.acquirenteunico.it/schemas/SII_AU/OffertaRetail/01}"


def txt(node, tag):
    v = node.findtext(f"{NS}{tag}")
    return (v or "").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commodity", default="E")
    ap.add_argument("--date", default=None)
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--out", default="data/config/audit_componenti.json")
    args = ap.parse_args()

    pattern = f"**/PO_Offerte_{args.commodity}_MLIBERO_*.xml*"
    files = sorted(Path(args.raw).glob(pattern), reverse=True)
    if args.date:
        d = args.date.replace("-", "")
        files = [f for f in files if d in f.name] or files[:1]
    else:
        files = files[:1]
    if not files:
        raise SystemExit("Nessun XML trovato.")
    path = files[0]
    print(f"Analisi di {path}\n")

    macroaree = Counter()
    tipologie = Counter()
    nomi_per_macroarea = defaultdict(Counter)
    n_comp = Counter()
    n_intervalli = Counter()
    fasce = Counter()
    tipologie_fasce = Counter()
    senza_volumetrico = []
    false_multiorarie = []
    tot = 0

    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as fh:
        for _, off in etree.iterparse(fh, tag=f"{NS}offerta"):
            tot += 1
            cod = off.findtext(f".//{NS}COD_OFFERTA") or "?"
            tf = off.findtext(f".//{NS}TIPOLOGIA_FASCE") or ""
            tipologie_fasce[tf] += 1

            comps = off.findall(f".//{NS}ComponenteImpresa")
            n_comp[len(comps)] += 1
            prezzi_per_fascia = defaultdict(float)
            ha_volumetrico = False

            for comp in comps:
                ma, tp, nome = txt(comp, "MACROAREA"), txt(comp, "TIPOLOGIA"), txt(comp, "NOME")
                macroaree[ma] += 1
                tipologie[tp] += 1
                if nome:
                    nomi_per_macroarea[ma][nome[:60]] += 1
                ivs = comp.findall(f"{NS}IntervalloPrezzi")
                n_intervalli[len(ivs)] += 1
                for iv in ivs:
                    um, fa = txt(iv, "UNITA_MISURA"), txt(iv, "FASCIA_COMPONENTE")
                    fasce[fa] += 1
                    if um in ("03", "04"):      # €/kWh, €/Smc
                        ha_volumetrico = True
                        try:
                            prezzi_per_fascia[fa] += float(txt(iv, "PREZZO").replace(",", "."))
                        except ValueError:
                            pass

            if not ha_volumetrico:
                senza_volumetrico.append(cod)
            elif tf not in ("01",) and len(set(round(v, 6) for v in prezzi_per_fascia.values())) == 1 \
                    and len(prezzi_per_fascia) >= 2:
                false_multiorarie.append(cod)
            off.clear()

    def show(titolo, counter, limit=30):
        print(f"--- {titolo} ---")
        for k, v in counter.most_common(limit):
            print(f"  {k!r:>12}  {v:>7}")
        print()

    print(f"Offerte analizzate: {tot}\n")
    show("MACROAREA (codice -> occorrenze)", macroaree)
    show("TIPOLOGIA ComponenteImpresa", tipologie)
    show("FASCIA_COMPONENTE", fasce)
    show("TIPOLOGIA_FASCE", tipologie_fasce)
    show("N. ComponenteImpresa per offerta", n_comp)
    show("N. IntervalloPrezzi per componente", n_intervalli)

    print("--- NOME per MACROAREA (per identificare i codici energia) ---")
    for ma, nomi in sorted(nomi_per_macroarea.items()):
        print(f"  MACROAREA {ma!r}:")
        for nome, v in nomi.most_common(6):
            print(f"      {v:>6}  {nome}")
    print()

    print(f"Offerte SENZA alcuna componente volumetrica: {len(senza_volumetrico)}")
    print(f"  esempi: {senza_volumetrico[:10]}")
    print(f"False multiorarie (prezzo identico su tutte le fasce): {len(false_multiorarie)}")
    print(f"  esempi: {false_multiorarie[:10]}")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps({
        "file": str(path), "offerte": tot,
        "macroaree": dict(macroaree), "tipologie_componente": dict(tipologie),
        "fasce": dict(fasce), "tipologie_fasce": dict(tipologie_fasce),
        "n_componenti_per_offerta": {str(k): v for k, v in n_comp.items()},
        "n_intervalli_per_componente": {str(k): v for k, v in n_intervalli.items()},
        "nomi_per_macroarea": {k: dict(v) for k, v in nomi_per_macroarea.items()},
        "senza_volumetrico": senza_volumetrico,
        "false_multiorarie": false_multiorarie,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReport in {args.out}")


if __name__ == "__main__":
    main()
Da nomi_per_macroarea ricavate i codici da mettere in MACROAREE_ENERGIA_DEFAULT. n_intervalli_per_componente vi dice subito se il troncamento a 5 vi sta costando qualcosa.

5. Altri bug nel codice che avete incollato
Bloccanti — possono spiegare da soli parte della divergenza

#	Dove	Problema
1	app.py load_data	df[df['DATA_FINE'] >= today] scarta le righe con DATA_FINE NaT: NaT >= Timestamp è False. Tutte le offerte senza data di fine (a tempo indeterminato) vengono eliminate. Serve df['DATA_FINE'].isna() | (df['DATA_FINE'] >= ...).
2	app.py	DATA_FINE confrontata con pd.Timestamp.today() invece che con data_rif: il Time Travel è rotto sul lato di chiusura.
3	app.py	comune='F205' (Belfiore) con provincia='015' (ISTAT). Formati incoerenti: se COMUNE è ISTAT, restano solo le offerte nazionali.
4	filter_offers	rf'\b{tipo_cliente}\b' non esclude Condominio Uso Domestico (Gas): \b matcha anche a metà frase.
5	filter_offers	.astype(float) sui COMP_IMP_2_INT_*_PREZZO solleva ValueError su '', 'None' o virgola decimale. Sta funzionando per caso.
6	calculate_sas	seen_fasce tiene il primo intervallo per componente: sbagliato quando gli IntervalloPrezzi sono scaglioni di consumo.
Da sistemare a seguire

for idx in range(len(df)) dentro il doppio loop componenti: 25 × N iterazioni Python, la vettorizzazione è persa. La price_matrix di §2 può sostituire tutto il blocco.
dispbt_fix = -10.7718 e pun_base = 0.105 / 0.35 hardcoded nel motore.
get_gas_costi_regolati(..., strict=False): una regione non mappata cade su Nord Occidentale in silenzio.
cdispd: .fillna(default) non copre il caso valore 0 nell'XML, che resta 0.
La card mostra "(escluse imposte e tasse)" ma SAS include accise e IVA.
La mappatura venditore: nel vostro ranking una riga ha 039679ESFFL00XXCasaFix1206260300 nella colonna PIVA — è una chiave composita, non una P.IVA. Se compare nel campo usato per la deduplica, dedup e attribuzione venditore sono inaffidabili per quelle righe. Le altre P.IVA nel testo che mi avete passato risultano sostituite da un segnaposto dal vostro strumento di export, quindi non ho potuto verificare la mappatura.
6. Test da aggiungere
python
Copy
def test_falsa_multioraria_triorario(make_df, offer_factory):
    df = make_df(offer_factory(tipologia_fasce="F1, F2, F3", componenti=[
        {"prezzo": 0.12, "unita": "€/kWh", "fascia": "monorario/F1"},
        {"prezzo": 0.12, "unita": "€/kWh", "fascia": "F2"},
        {"prezzo": 0.12, "unita": "€/kWh", "fascia": "F3"},
    ]))
    assert cm.multiorario_flags(df)["falsa_multioraria"].iloc[0]

def test_falsa_multioraria_biorario(make_df, offer_factory):
    """Il vostro is_fake attuale non copre questo caso."""
    df = make_df(offer_factory(tipologia_fasce="biorario (F1 / F2+F3)", componenti=[
        {"prezzo": 0.12, "unita": "€/kWh", "fascia": "monorario/F1"},
        {"prezzo": 0.12, "unita": "€/kWh", "fascia": "F2+F3"},
    ]))
    assert cm.multiorario_flags(df)["falsa_multioraria"].iloc[0]

def test_biorario_genuino_non_flaggato(make_df, offer_factory):
    df = make_df(offer_factory(tipologia_fasce="biorario (F1 / F2+F3)", componenti=[
        {"prezzo": 0.1105, "unita": "€/kWh", "fascia": "monorario/F1"},
        {"prezzo": 0.1076, "unita": "€/kWh", "fascia": "F2+F3"},
    ]))
    f = cm.multiorario_flags(df)
    assert not f["falsa_multioraria"].iloc[0]
    assert f["n_bande_prezzate"].iloc[0] == 3

def test_componente_indipendente_dalla_posizione(make_df, offer_factory):
    """L'energia in COMP_IMP_1 o in COMP_IMP_3 deve dare lo stesso risultato:
    il vostro is_fake guarda solo COMP_IMP_2."""
    a = make_df(offer_factory(tipologia_fasce="F1, F2, F3", componenti=[
        {"prezzo": 0.12, "unita": "€/kWh", "fascia": "monorario/F1"},
        {"prezzo": 0.12, "unita": "€/kWh", "fascia": "F2"},
        {"prezzo": 0.12, "unita": "€/kWh", "fascia": "F3"},
    ]))
    b = make_df(offer_factory(tipologia_fasce="F1, F2, F3", componenti=[
        {"prezzo": 80.0, "unita": "€/Anno", "fascia": ""},
        {"prezzo": 0.12, "unita": "€/kWh", "fascia": "monorario/F1"},
        {"prezzo": 0.12, "unita": "€/kWh", "fascia": "F2"},
        {"prezzo": 0.12, "unita": "€/kWh", "fascia": "F3"},
    ]))
    assert cm.multiorario_flags(a)["falsa_multioraria"].iloc[0]
    assert cm.multiorario_flags(b)["falsa_multioraria"].iloc[0]

def test_intervalli_fuori_ordine(make_df, offer_factory):
    """INT_1=F3, INT_2=F1, INT_3=F2: il confronto posizionale fallisce, il
    pivot per fascia no."""
    df = make_df(offer_factory(tipologia_fasce="F1, F2, F3", componenti=[
        {"prezzo": 0.11, "unita": "€/kWh", "fascia": "F3"},
        {"prezzo": 0.13, "unita": "€/kWh", "fascia": "monorario/F1"},
        {"prezzo": 0.12, "unita": "€/kWh", "fascia": "F2"},
    ]))
    m = cm.price_matrix(df)
    assert m.loc[0, "F1"] == pytest.approx(0.13)
    assert m.loc[0, "F3"] == pytest.approx(0.11)
    assert not cm.multiorario_flags(df)["falsa_multioraria"].iloc[0]

def test_offerta_senza_prezzo_energia_flaggata(make_df, offer_factory):
    """Caso MONO2026DOME129EE: commercializzazione + sbilanciamento, niente energia."""
    df = make_df(offer_factory(componenti=[
        {"prezzo": 138.0, "unita": "€/Anno", "fascia": ""},
        {"prezzo": 0.005, "unita": "€/kWh", "fascia": "monorario/F1"},
    ]))
    assert not cm.energia_flags(df)["prezzo_energia_ok"].iloc[0]

def test_scaglioni_di_consumo(make_df, offer_factory):
    """Due IntervalloPrezzi della stessa fascia sono scaglioni: va scelto quello
    applicabile, non il primo."""
    df = make_df(offer_factory(
        tipologia_fasce="monorario/F1",
        COMP_IMP_1_INT_1_PREZZO=0.15, COMP_IMP_1_INT_1_UNITA="€/kWh",
        COMP_IMP_1_INT_1_FASCIA="monorario/F1",
        COMP_IMP_1_INT_1_CONSUMO_DA=0, COMP_IMP_1_INT_1_CONSUMO_A=1500,
        COMP_IMP_1_INT_2_PREZZO=0.11, COMP_IMP_1_INT_2_UNITA="€/kWh",
        COMP_IMP_1_INT_2_FASCIA="monorario/F1",
        COMP_IMP_1_INT_2_CONSUMO_DA=1501, COMP_IMP_1_INT_2_CONSUMO_A=None,
    ))
    assert cm.price_matrix(df, consumo_annuo=2700).loc[0, "F1"] == pytest.approx(0.11)
    assert cm.price_matrix(df, consumo_annuo=1000).loc[0, "F1"] == pytest.approx(0.15)
7. Cosa mi serve da voi
Nell'ordine di utilità:

python scripts/dump_offerta_xml.py --cod MONO2026DOME129EE — decide se l'Anomalia 1 è un filtro da scrivere o un bug di parsing da correggere. È la domanda più importante.
CasaFix1206260300 compare nel ranking Monorario del Portale? — decide falsa_multioraria='escludi' vs 'riclassifica'.
python scripts/audit_componenti.py --commodity E — mi dà i codici MACROAREA reali, così MACROAREE_ENERGIA_DEFAULT smette di essere vuoto e il controllo diventa strutturale invece che euristico.
df['COMUNE'].value_counts().head() — formato ISTAT o Belfiore.
Output di dump_offerta_xml.py --cod sull'E.ON biorariaVerde — il residuo di 0.46 € (783.06 contro 783.52, 0.06%) è il primo caso golden utile: su un'offerta con soli due prezzi e nessuno sconto, uno scostamento così piccolo isola quasi certamente lo split dei consumi F1/F2+F3 o una componente regolata. Vale la pena chiuderlo, perché è l'unico numero che avete già confrontato con l'ufficiale.
Un'ultima nota di metodo: ogni filtro che aggiungete per avvicinarvi al Portale è anche un'ipotesi sul suo comportamento. Tenerle parametrizzate e tracciate (diagnostica_esclusioni, offerte_scartate) è ciò che vi permette di distinguere "ho replicato il PO" da "ho tarato i filtri su tre casi". Con 18 concorrenti monitorati, la seconda cosa si rompe silenziosamente al primo aggiornamento del portale.