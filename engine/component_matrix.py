"""engine/component_matrix.py

Ricostruisce per ogni offerta la matrice dei prezzi volumetrici per fascia
partendo dalle colonne COMP_IMP_{c}_INT_{i}_*.
"""
from __future__ import annotations

import logging
import re
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

BANDE = ("F1", "F2", "F3")

_FASCIA_BANDE = {
    "01": ("F1",), "monorario/f1": ("F1",), "monorario": ("F1",), "f1": ("F1",),
    "02": ("F2",), "f2": ("F2",),
    "03": ("F3",), "f3": ("F3",),
    "91": ("F2", "F3"), "f2+f3": ("F2", "F3"), "f2 + f3": ("F2", "F3"),
    "92": ("F1", "F3"), "f1+f3": ("F1", "F3"), "f1 + f3": ("F1", "F3"),
    "93": ("F1", "F2"), "f1+f2": ("F1", "F2"), "f1 + f2": ("F1", "F2"),
}

_TIPOLOGIE_MONO = {"01", "monorario/f1", "monorario"}

KIND_KWH, KIND_SMC, KIND_KW = "KWH", "SMC", "KW"
KIND_FISSO, KIND_PCT, KIND_UNKNOWN = "FISSO", "PERCENTUALE", "SCONOSCIUTA"
KIND_VOLUMETRICI = (KIND_KWH, KIND_SMC)

_VUOTI = {"", "nan", "none", "null", "<na>"}

LONG_COLUMNS = ["row", "comp", "intervallo", "prezzo", "unita", "fascia",
                "validita", "consumo_da", "consumo_a", "macroarea",
                "macroarea_cod", "tipologia_comp", "nome_comp",
                "tipologia_fasce", "kind"]


def _norm(v) -> str:
    return re.sub(r"\s+", " ", str(v if v is not None else "").strip().lower())


def _to_num(s: pd.Series) -> pd.Series:
    raw = s.astype(str).str.strip()
    txt = raw.str.replace(r"[^\d,.\-]", "", regex=True)
    ha_virgola = txt.str.contains(",", na=False)
    txt = txt.where(~ha_virgola, txt.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    out = pd.to_numeric(txt, errors="coerce")
    return out


def _str_col(df: pd.DataFrame, name: str) -> pd.Series:
    if name in df.columns:
        return df[name].astype(str)
    return pd.Series("", index=df.index, dtype=object)


def classify_unita(unita) -> str:
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
    if _norm(tipologia_fasce) in _TIPOLOGIE_MONO:
        return BANDE
    f = _norm(fascia)
    if f in _VUOTI:
        return BANDE
    return _FASCIA_BANDE.get(f, ())


_RE_PREZZO_COMP = re.compile(r"^COMP_IMP_(\d+)_INT_(\d+)_PREZZO$")


def indici_componenti(df: pd.DataFrame) -> list[tuple[int, int]]:
    """Coppie (componente, intervallo) presenti come colonne _PREZZO."""
    coppie = []
    for col in df.columns:
        m = _RE_PREZZO_COMP.match(str(col))
        if m:
            coppie.append((int(m.group(1)), int(m.group(2))))
    return sorted(coppie)


def _str_col_alias(df: pd.DataFrame, *names: str) -> pd.Series:
    """Prima colonna esistente tra i nomi dati (nuovi prima, legacy dopo)."""
    for n in names:
        if n in df.columns:
            return df[n].astype(str)
    return pd.Series("", index=df.index, dtype=object)


def _codice_da_decodifica(df: pd.DataFrame, col_cod: str, col_dec: str,
                          mappa: dict) -> pd.Series:
    """Codice SII grezzo; per lo storico pre-fix lo ricava invertendo la
    transcodifica del flattener."""
    if col_cod in df.columns:
        return df[col_cod].astype(str)
    inversa = {v: k for k, v in mappa.items()}
    dec = _str_col(df, col_dec)
    return dec.map(lambda v: inversa.get(v, "")).astype(object)


def build_long(df: pd.DataFrame, consumo_annuo: float | None = None) -> pd.DataFrame:
    from parse.flattener import DECODE_MAPS
    tipologia = _str_col(df, "TIPOLOGIA_FASCE")
    blocchi = []

    for c, i in indici_componenti(df):
        base = f"COMP_IMP_{c}_INT_{i}"
        blk = pd.DataFrame({
            "row": df.index,
            "comp": c,
            "intervallo": i,
            "prezzo": _to_num(df[f"{base}_PREZZO"]).values,
            "unita": _str_col(df, f"{base}_UNITA").values,
            "fascia": _str_col(df, f"{base}_FASCIA").values,
            "validita": _str_col_alias(df, f"{base}_VALIDO_FINO", f"{base}_VALIDITA").values,
            "consumo_da": _to_num(_str_col_alias(df, f"{base}_CONSUMO_DA", f"{base}_CONS_DA")).values,
            "consumo_a": _to_num(_str_col_alias(df, f"{base}_CONSUMO_A", f"{base}_CONS_A")).values,
            "macroarea": _str_col(df, f"COMP_IMP_{c}_MACROAREA").values,
            "macroarea_cod": _codice_da_decodifica(
                df, f"COMP_IMP_{c}_MACROAREA_COD", f"COMP_IMP_{c}_MACROAREA",
                DECODE_MAPS["MACROAREA_COMP"]).values,
            "tipologia_comp": _codice_da_decodifica(
                df, f"COMP_IMP_{c}_TIPOLOGIA_COD", f"COMP_IMP_{c}_TIPOLOGIA",
                DECODE_MAPS["TIPOLOGIA_COMP"]).values,
            "nome_comp": _str_col(df, f"COMP_IMP_{c}_NOME").values,
            "tipologia_fasce": tipologia.values,
        })
        blocchi.append(blk)

    if not blocchi:
        return pd.DataFrame(columns=LONG_COLUMNS)

    long = pd.concat(blocchi, ignore_index=True)
    long = long[long["prezzo"].notna() & (long["prezzo"] != 0)]
    long["kind"] = long["unita"].map(classify_unita)
    long = _select_scaglione(long, consumo_annuo)
    return long.reset_index(drop=True)


def _select_scaglione(long: pd.DataFrame, consumo_annuo: float | None) -> pd.DataFrame:
    long = long.copy()
    long["_k"] = (long["row"].astype(str) + "\x1f" + long["comp"].astype(str)
                  + "\x1f" + long["fascia"].map(_norm))

    ha_scaglioni = long[["consumo_da", "consumo_a"]].notna().any(axis=1)
    if consumo_annuo is None or not ha_scaglioni.any():
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


def explode_bande(long: pd.DataFrame) -> pd.DataFrame:
    vol = long[long["kind"].isin(KIND_VOLUMETRICI)].copy()
    if vol.empty:
        return vol.assign(banda=pd.Series(dtype=object))
    vol["bande"] = [resolve_bande(f, t) for f, t in
                    zip(vol["fascia"], vol["tipologia_fasce"])]
    non_risolte = vol["bande"].map(len) == 0
    vol = vol[~non_risolte]
    return vol.explode("bande").rename(columns={"bande": "banda"})


def price_matrix(df: pd.DataFrame, long: pd.DataFrame | None = None,
                 consumo_annuo: float | None = None) -> pd.DataFrame:
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
    long = build_long(df, consumo_annuo=consumo_annuo) if long is None else long
    m = price_matrix(df, long=long)

    vol = long[long["kind"].isin(KIND_VOLUMETRICI)].copy()
    if vol.empty:
        base = pd.DataFrame(0, index=df.index,
                            columns=["n_bande_prezzate", "n_fasce_dichiarate",
                                     "n_prezzi_distinti"])
        base["falsa_multioraria"] = False
        return base

    vol["_f"] = vol["fascia"].map(_norm)
    dichiarate = vol[~vol["_f"].isin(_VUOTI) & vol["_f"].isin(_FASCIA_BANDE)]
    n_fasce = (dichiarate.groupby("row")["_f"].nunique()
               .reindex(df.index).fillna(0).astype(int))

    n_bande = m.notna().sum(axis=1)
    p_min, p_max = m.min(axis=1), m.max(axis=1)
    spread = (p_max - p_min).fillna(0.0)

    out = pd.DataFrame({
        "n_bande_prezzate": n_bande,
        "n_fasce_dichiarate": n_fasce,
        "n_prezzi_distinti": m.round(6).nunique(axis=1, dropna=True),
        "prezzo_min": p_min,
        "prezzo_max": p_max,
        "spread_assoluto": spread,
        "spread_relativo": np.where(p_max > 0, spread / p_max, 0.0),
    }, index=df.index)

    out["falsa_multioraria"] = (
        (out["n_fasce_dichiarate"] >= 2)
        & (out["n_bande_prezzate"] >= 2)
        & (spread <= tol)
    )
    return out


MACROAREE_ENERGIA_DEFAULT: set[str] = set()

_KEYWORD_ENERGIA = re.compile(r"(?i)energia|luce|corrispettivo|prezzo\s*materia|componente\s*energia|quota\s*energia|pe|ped")
_KEYWORD_NON_ENERGIA = re.compile(r"(?i)commercializzazione|dispacciamento|trasporto|oneri|imposte|pvc|qvd|ccv|fissa|capacit")


def energia_flags(df: pd.DataFrame, long: pd.DataFrame | None = None,
                  macroaree_energia: set[str] | None = None,
                  soglia_kwh: float = 0.03, soglia_smc: float = 0.10,
                  frazione_mediana: float = 0.40,
                  consumo_annuo: float | None = None) -> pd.DataFrame:
    macroaree = MACROAREE_ENERGIA_DEFAULT if macroaree_energia is None else macroaree_energia
    long = build_long(df, consumo_annuo=consumo_annuo) if long is None else long

    vol = long[long["kind"].isin(KIND_VOLUMETRICI)]
    tot_vol = vol.groupby("row")["prezzo"].sum().reindex(df.index).fillna(0.0)

    ha_macroarea = (long["macroarea_cod"].map(_norm) != "").groupby(long["row"]).any() \
        .reindex(df.index).fillna(False)
    if macroaree:
        en_macro = vol["macroarea_cod"].map(_norm).isin({_norm(x) for x in macroaree})
        by_macro = en_macro.groupby(vol["row"]).any().reindex(df.index).fillna(False)
    else:
        by_macro = pd.Series(False, index=df.index)

    nomi = vol["nome_comp"].fillna("").astype(str)
    en_nome = nomi.str.contains(_KEYWORD_ENERGIA) & ~nomi.str.contains(_KEYWORD_NON_ENERGIA)
    by_nome = en_nome.groupby(vol["row"]).any().reindex(df.index).fillna(False)

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
