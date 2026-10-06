"""Parametri di calcolo pubblicati ogni giorno dal Portale Offerte.

Open data: PO_Parametri_Mercato_Libero_{E|G}_YYYYMMDD.csv (nome_parametro,
valore, descrizione), scaricati da scripts/update_daily in
data/raw/parametri/{E|G}/YYYY/. Sono i valori che il Portale usa per la parte
regolata della spesa annua (reti, oneri, dispacciamento, accise luce, IVA):
leggerli da qui evita l'aggiornamento manuale trimestrale delle tariffe.

Non contengono accise e addizionali gas né le stime PUN/PSV per le offerte
variabili: quelle restano in data/config/arera_tariffs.json.
"""
from __future__ import annotations

import csv
import json
import logging
import re
from datetime import date, datetime
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

PARAMETRI_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "parametri"
IMPOSTE_GAS = Path(__file__).resolve().parents[1] / "data" / "processed" / "imposte_gas_portale.json"
_RE_DATA = re.compile(r"_(\d{8})\.csv$")

# Ambiti tariffari gas ARERA (suffisso _a1.._a6 dei parametri)
AMBITO_GAS_BY_REGIONE = {
    "Valle d'Aosta": 1, "Piemonte": 1, "Liguria": 1,
    "Lombardia": 2, "Trentino-Alto Adige": 2, "Veneto": 2,
    "Friuli-Venezia Giulia": 2, "Emilia-Romagna": 2,
    "Toscana": 3, "Umbria": 3, "Marche": 3,
    "Abruzzo": 4, "Molise": 4, "Puglia": 4, "Basilicata": 4,
    "Lazio": 5, "Campania": 5,
    "Calabria": 6, "Sicilia": 6,
    # Sardegna fuori dagli ambiti metano: assimilata al Meridionale
    "Sardegna": 6,
}

# Limiti superiori (Smc/anno) degli scaglioni di TAU3 e UG2
SCAGLIONI_GAS = (120, 480, 1560, 5000, 80000, 200000)


def leggi_file(path: Path) -> dict[str, float]:
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        return {r["nome_parametro"].strip(): float(r["valore"])
                for r in csv.DictReader(f) if r.get("valore")}


def carica(commodity: str, fino_a: date | None = None,
           root: Path = PARAMETRI_DIR) -> dict[str, float] | None:
    """Parametri dell'ultimo file pubblicato entro `fino_a` (default oggi).
    La data del file è in par['_data']. None se non ci sono file."""
    fino_a = fino_a or date.today()
    candidati = []
    for p in (root / commodity).glob("*/PO_Parametri_Mercato_Libero_*.csv"):
        m = _RE_DATA.search(p.name)
        if m and (g := datetime.strptime(m.group(1), "%Y%m%d").date()) <= fino_a:
            candidati.append((g, p))
    if not candidati:
        return None
    g, p = max(candidati)
    par = leggi_file(p)
    par["_data"] = g
    return par


def stesso_trimestre(a: date, b: date) -> bool:
    return a.year == b.year and (a.month - 1) // 3 == (b.month - 1) // 3


# ---------------------------------------------------------------- luce

def accisa_ele(par: dict, consumo_annuo: float, potenza: float, residente: bool) -> float:
    """Accisa annua. Residenti fino a 3 kW: esenzione mensile di 150 kWh che
    si riduce oltre 220 kWh/mese e si annulla a 370 kWh/mese."""
    if not residente:
        return par["acc_c_nr"] * consumo_annuo
    if potenza > 3:
        return par["acc_c_r_h"] * consumo_annuo
    c = consumo_annuo / 12
    if c <= 150:
        tassati = 0.0
    elif c <= 220:
        tassati = c - 150
    elif c <= 370:
        tassati = 2 * c - 370
    else:
        tassati = c
    return par["acc_c_r_l"] * tassati * 12


def voci_ele(par: dict, consumo_annuo: float, potenza: float, residente: bool) -> dict[str, float]:
    """Voci del dettaglio offerta del Portale (€/anno, IVA esclusa): 'rete'
    (tariffa per l'uso della rete), 'oneri' (oneri generali), 'imposte' (accisa)."""
    rete = (par["sigma1"] + (par["sigma2"] + par["uc6s_d"]) * potenza
            + (par["sigma3"] + par["uc3"] + par["uc6p_d"]) * consumo_annuo)
    if residente:
        oneri = (par["asos_dr"] + par["arim_dr"]) * consumo_annuo
    else:
        oneri = (par["asos_dnr_f"] + par["arim_dnr_f"]
                 + (par["asos_dnr_v"] + par["arim_dnr_v"]) * consumo_annuo)
    return {"rete": rete, "oneri": oneri,
            "imposte": accisa_ele(par, consumo_annuo, potenza, residente)}


def regolati_ele(par: dict, consumo_annuo: float, potenza: float, residente: bool) -> float:
    """Trasporto, misura, oneri generali e accisa (€/anno, IVA esclusa).
    Il dispacciamento è a parte (dispacciamento_ele): dipende dall'offerta."""
    return sum(voci_ele(par, consumo_annuo, potenza, residente).values())


# Voci di Dispacciamento dell'XML (colonne DISP_<nome>) -> parametri €/kWh.
# TIDE = MSD + eolico + essenzialità + Terna + interrompibilità + capacità
# produttiva; CdispD = TIDE + capacity market (media dei tre mesi).
DISP_KWH = {
    "TIDE": ("msd", "modeol", "uniess", "terna", "interr", "capprod"),
    "Cod_03": ("msd",), "Cod_04": ("modeol",), "Cod_05": ("uniess",),
    "Cod_06": ("terna",), "Cod_07": ("capprod",), "Cod_08": ("interr",),
    "Capacita_MT": ("cpty_mrkt_mt",),
    "Salvaguardia": ("rst",), "Tutele_Graduali": ("rstg",),
    "CdispD": ("cdispd",),
    "PD": (), "Altro": (),  # solo valore dichiarato dall'offerta
}


def disp_kwh(par: dict, voce: str) -> float:
    """Valore del Portale (€/kWh) di una voce di dispacciamento."""
    if voce == "Capacita_STG":
        return sum(par[f"cpty_mrkt_{m}"] for m in (1, 2, 3)) / 3
    return sum(par.get(p, 0.0) for p in DISP_KWH[voce])


VOCI_DISP_KWH = tuple(DISP_KWH) + ("Capacita_STG",)


def dispacciamento_ele(par: dict, consumo_annuo: float, voci: dict[str, tuple],
                       dispbt: np.ndarray | None = None) -> np.ndarray:
    """Dispacciamento annuo per offerta (€, IVA esclusa).
    voci: nome -> (dichiarata: bool array, valore dichiarato €/kWh: float
    array, NaN o 0 = valore del Portale). DispBT (€/anno) se dichiarato."""
    tot = 0.0 if dispbt is None else np.where(dispbt, par["dispbt_d"], 0.0)
    for voce, (dichiarata, valore) in voci.items():
        v = np.where(np.isnan(valore) | (valore <= 0), disp_kwh(par, voce), valore)
        tot = tot + np.where(dichiarata, v * consumo_annuo, 0.0)
    return tot


# ---------------------------------------------------------------- gas

def ambito_gas(regione: str) -> int:
    if regione not in AMBITO_GAS_BY_REGIONE:
        raise KeyError(f"Regione '{regione}' senza ambito tariffario gas")
    return AMBITO_GAS_BY_REGIONE[regione]


def a_scaglioni(consumo: float, aliquote: list[float], limiti=SCAGLIONI_GAS) -> float:
    """Importo annuo di una componente a scaglioni progressivi."""
    tot, prec = 0.0, 0.0
    for lim, a in zip(limiti, aliquote):
        tot += a * max(0.0, min(consumo, lim) - prec)
        prec = lim
    return tot + aliquote[-1] * max(0.0, consumo - limiti[-1])


# Soglia annua entro cui i consumi civili gas hanno IVA agevolata
SOGLIA_IVA_GAS = 480


def voci_gas(par: dict, regione: str, consumo: float) -> dict[str, float]:
    """Rete e oneri gas divisi come nel dettaglio offerta del Portale (€/anno,
    contatore fino a G6, domestico). Rete: TAU1, ST, VR, QT, TAU3, RS, UG1.
    Oneri: UG2 secondo, RE, UG2 primo, UG3. Il Portale non conteggia il bonus GS."""
    a = ambito_gas(regione)
    tau3 = [par[f"tau3_f{i}_a{a}"] for i in range(1, 7)]
    ug2 = [par[f"ug2p_d_f{i}"] for i in range(1, 7)]
    return {
        "rete_fisso": par[f"tau1_cc1_a{a}"] + par[f"st_a{a}"] + par[f"vr_a{a}"],
        "rete_vol": (par["qt"] + par["rs"] + par["ug1"]) * consumo + a_scaglioni(consumo, tau3),
        "oneri_fisso": par["ug2s"],
        "oneri_vol": (par["re"] + par["ug3"]) * consumo + a_scaglioni(consumo, ug2),
    }


def regolati_gas_fisso(par: dict, regione: str) -> float:
    """Quote fisse di rete e oneri (€/anno), contatore fino a G6, domestico."""
    v = voci_gas(par, regione, 0.0)
    return v["rete_fisso"] + v["oneri_fisso"]


def regolati_gas_vol(par: dict, regione: str, consumo: float) -> float:
    """Quote variabili di rete e oneri (€) per i primi `consumo` Smc."""
    v = voci_gas(par, regione, consumo)
    return v["rete_vol"] + v["oneri_vol"]


def importo_tiers(tiers: list, consumo: float) -> float:
    """Importo dei primi `consumo` Smc con aliquote [[limite, €/Smc], ...]."""
    tot, prec = 0.0, 0.0
    for lim, a in tiers:
        tot += a * max(0.0, min(consumo, lim) - prec)
        prec = lim
    return tot


def carica_imposte_gas(path: Path = IMPOSTE_GAS) -> dict:
    """Accise e addizionali per regione rilevate dal Portale
    (scripts/rileva_imposte_gas.py). Vuoto se il file non c'è."""
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def regolati_gas(par: dict, regione: str, consumo_annuo: float) -> float:
    """Distribuzione, misura, trasporto e oneri (€/anno, imposte escluse)."""
    return regolati_gas_fisso(par, regione) + regolati_gas_vol(par, regione, consumo_annuo)
