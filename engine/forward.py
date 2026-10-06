"""Stime degli indici per le offerte variabili, come il Portale Offerte.

Regole per il calcolo della spesa (Portale Offerte, v4.0 16/02/2026, cap. 3 e 5;
ARERA, pagina "stima della spesa", delibera 289/2022):
- periodo di stima: 4 trimestri solari dal primo giorno del trimestre di
  consultazione;
- valori: media aritmetica delle quotazioni forward dell'indice per quei
  trimestri, rilevate nel mese precedente la consultazione;
- luce: prezzo = media dei 4 trimestri x (1 + lambda) + spread, per F0
  (monorarie), F1 e F23;
- gas: indice mese per mese, pesato sui consumi mensili dei profili di
  prelievo convenzionali (zona climatica e uso).

I valori ufficiali sono elaborati da Acquirente Unico e non pubblicati: qui si
usano le quotazioni dei mercati a termine GME (download.gme). Il mercato a
termine GME è poco liquido, quindi le stime sono approssimate (verifica del
02/10/2026: luce entro il 4%, gas entro il 10% del valore del Portale).
"""
from __future__ import annotations

import calendar
import json
import logging
import statistics
from datetime import date
from pathlib import Path

from download import gme

logger = logging.getLogger(__name__)

COMPONENTI_PORTALE = Path(__file__).resolve().parents[1] / "data" / "processed" / "componenti_portale.json"

KWH_PER_SMC = 10.7  # PCS convenzionale 0,03852 GJ/Smc

# Profili di prelievo gas, anno termico 2025/2026 (appendice delle Regole),
# da ottobre a settembre. C1 = riscaldamento per zona climatica, C2 = cottura
# cibi e acqua calda sanitaria.
PROFILI_GAS = {
    "C1_B": (0.0, 0.0, 26.0816357, 31.9118241, 24.7889579, 17.2175799, 0, 0, 0, 0, 0, 0),
    "C1_C": (0.0, 10.5605109, 22.5061041, 26.6326652, 20.7234414, 15.2857002, 4.2915763, 0, 0, 0, 0, 0),
    "C1_D": (0.0, 13.5467630, 21.1883316, 25.8516945, 19.1039767, 13.4431506, 6.8660818, 0, 0, 0, 0, 0),
    "C1_E": (5.5194873, 14.8851505, 22.0494524, 24.2610252, 17.5032776, 10.9498316, 4.8317740,
             0, 0, 0, 0, 0),
    "C1_F": (6.4769407, 13.7764218, 20.2207842, 22.7314363, 16.6800704, 10.6482268, 4.9866098,
             2.4582801, 0.3817316, 0, 0, 1.6394976),
    "C2": (7.2982139, 9.1423084, 12.2074716, 13.4956479, 11.2628566, 11.1005836, 7.5419819,
           6.2026357, 5.4659533, 5.1313777, 5.2406872, 5.9102822),
}
# Zona climatica del capoluogo di regione (DPR 412/1993)
ZONA_CLIMATICA = {
    "Valle d'Aosta": "E", "Piemonte": "E", "Liguria": "D", "Lombardia": "E",
    "Trentino-Alto Adige": "E", "Veneto": "E", "Friuli-Venezia Giulia": "E",
    "Emilia-Romagna": "E", "Toscana": "D", "Umbria": "E", "Marche": "D",
    "Lazio": "D", "Abruzzo": "E", "Molise": "E", "Campania": "C", "Puglia": "C",
    "Basilicata": "E", "Calabria": "D", "Sicilia": "B", "Sardegna": "C",
}
# Quota di riscaldamento nel profilo di un cliente con riscaldamento, cottura e
# acqua calda (ricerca standard del Portale). Tarata sul CCR applicato dal
# Portale a Milano, 1.400 Smc, il 01/10/2026 (35,79 €: quota 0,6 +-0,01).
QUOTA_RISCALDAMENTO = 0.6


# ---------------------------------------------------------------- periodi

def trimestri(oggi: date) -> list[tuple[int, int]]:
    """I 4 trimestri (anno, trimestre) dal trimestre di consultazione."""
    a, q = oggi.year, (oggi.month - 1) // 3 + 1
    out = []
    for _ in range(4):
        out.append((a, q))
        a, q = (a + 1, 1) if q == 4 else (a, q + 1)
    return out


def mesi(oggi: date) -> list[tuple[int, int]]:
    """I 12 mesi (anno, mese) del periodo di stima."""
    a, m = oggi.year, 3 * ((oggi.month - 1) // 3) + 1
    out = []
    for _ in range(12):
        out.append((a, m))
        a, m = (a + 1, 1) if m == 12 else (a, m + 1)
    return out


def mese_rilevazione(oggi: date) -> tuple[int, int]:
    return (oggi.year - 1, 12) if oggi.month == 1 else (oggi.year, oggi.month - 1)


def _ore_trimestre(a: int, q: int) -> tuple[int, int]:
    """Ore totali e ore di picco (lun-ven 8-20) del trimestre."""
    ore, picco = 0, 0
    for m in range(3 * q - 2, 3 * q + 1):
        for g in range(1, calendar.monthrange(a, m)[1] + 1):
            ore += 24
            picco += 12 if date(a, m, g).weekday() < 5 else 0
    return ore, picco


# ---------------------------------------------------------------- quotazioni

def _media(sessioni: list[dict], prodotto: str) -> float | None:
    v = [s[prodotto] for s in sessioni if s.get(prodotto)]
    return statistics.mean(v) if v else None


def _prima(sessioni: list[dict], prodotti: list[str]) -> float | None:
    for p in prodotti:
        if (v := _media(sessioni, p)) is not None:
            return v
    return None


def _trimestre_ee(sessioni: list[dict], profilo: str, a: int, q: int) -> float | None:
    """Quotazione €/MWh di un trimestre: prodotto trimestrale, altrimenti
    media dei mensili, altrimenti annuale."""
    v = _media(sessioni, f"{profilo}-Q-{a}-{q:02d}")
    if v is not None:
        return v
    mensili = [_media(sessioni, f"{profilo}-M-{a}-{m:02d}") for m in range(3 * q - 2, 3 * q + 1)]
    if all(x is not None for x in mensili):
        return statistics.mean(mensili)
    return _media(sessioni, f"{profilo}-Y-{a}")


def _mese_gas(sessioni: list[dict], a: int, m: int) -> float | None:
    q = (m - 1) // 3 + 1
    stagione = f"WS-{a}/{a + 1}" if m >= 10 else (f"WS-{a - 1}/{a}" if m <= 3 else f"SS-{a}")
    return _prima(sessioni, [f"M-{a}-{m:02d}", f"Q-{a}-{q:02d}", stagione, f"CY-{a}"])


def stima(oggi: date | None = None, root: Path = gme.GME_DIR) -> dict | None:
    """Stime per il periodo che comprende `oggi`, dalle sessioni GME del mese
    precedente. None se mancano le sessioni o una quotazione.
    ee: {'F0','F1','F23'} €/kWh al netto delle perdite (media dei 4 trimestri);
    gas_mesi: 12 valori €/Smc da ottobre/gennaio/aprile/luglio."""
    oggi = oggi or date.today()
    a_ril, m_ril = mese_rilevazione(oggi)
    s_ee = gme.sessioni("mte", a_ril, m_ril, root)
    s_gas = gme.sessioni("mtgas", a_ril, m_ril, root)
    if not s_ee or not s_gas:
        logger.warning("Forward GME: nessuna sessione di %02d/%d", m_ril, a_ril)
        return None

    f0, f1, f23 = [], [], []
    for a, q in trimestri(oggi):
        bl, pl = _trimestre_ee(s_ee, "BL", a, q), _trimestre_ee(s_ee, "PL", a, q)
        if bl is None or pl is None:
            logger.warning("Forward GME: manca la quotazione luce %d-Q%d", a, q)
            return None
        ore, picco = _ore_trimestre(a, q)
        # F1 ~ picco (lun-ven 8-20); F23 dalle ore fuori picco del baseload
        f0.append(bl)
        f1.append(pl)
        f23.append((bl * ore - pl * picco) / (ore - picco))
    gas_mesi = []
    for a, m in mesi(oggi):
        v = _mese_gas(s_gas, a, m)
        if v is None:
            logger.warning("Forward GME: manca la quotazione gas %02d/%d", m, a)
            return None
        gas_mesi.append(v * KWH_PER_SMC / 1000)
    return {
        "fonte": "GME", "rilevazione": f"{a_ril}-{m_ril:02d}",
        "sessioni": min(len(s_ee), len(s_gas)),
        "periodo": [f"{a}-Q{q}" for a, q in trimestri(oggi)],
        "ee": {k: statistics.mean(v) / 1000 for k, v in (("F0", f0), ("F1", f1), ("F23", f23))},
        "gas_mesi": gas_mesi,
    }


# ---------------------------------------------------------------- profili gas

def profilo_gas(regione: str, oggi: date, quota_riscaldamento: float = QUOTA_RISCALDAMENTO) -> list[float]:
    """Quote mensili (somma 1) del consumo annuo nei 12 mesi del periodo di stima."""
    c1 = PROFILI_GAS[f"C1_{ZONA_CLIMATICA.get(regione, 'E')}"]
    c2 = PROFILI_GAS["C2"]
    da_ottobre = [quota_riscaldamento * x / sum(c1) + (1 - quota_riscaldamento) * y / sum(c2)
                  for x, y in zip(c1, c2)]
    # i profili partono da ottobre: si allineano al primo mese del periodo
    inizio = (mesi(oggi)[0][1] - 10) % 12
    return da_ottobre[inizio:] + da_ottobre[:inizio]


def pesa_trimestri(valori_trim: list[float], quote_mesi: list[float]) -> float:
    """Valore medio di una componente trimestrale pesata sui consumi mensili."""
    return sum(valori_trim[i // 3] * w for i, w in enumerate(quote_mesi))


# ---------------------------------------------------------------- componenti del Portale

def carica_componenti(path: Path = COMPONENTI_PORTALE) -> dict:
    """PPE e CCR letti dal dettaglio offerta del Portale
    (scripts/rileva_componenti_portale.py). Vuoto se il file non c'è."""
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def ccr_trimestri(componenti: dict, oggi: date) -> list[float] | None:
    """CCR dei 4 trimestri del periodo di stima, se rilevati."""
    ccr = componenti.get("ccr", {})
    chiavi = [f"{a}-Q{q}" for a, q in trimestri(oggi)]
    if not all(k in ccr for k in chiavi):
        return None
    return [ccr[k] for k in chiavi]
