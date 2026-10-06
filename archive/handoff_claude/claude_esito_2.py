Procedo con i tre interventi. Prima due punti che vanno chiariti subito, perché condizionano il resto.

Blocchi da confermare
1. _validate_tariffs rifiuta i valori negativi. Il validatore esistente contiene:

python
Copy
if val is None or val < 0:
    raise ValueError(f"Parametro ELE '{key}' ... negativo: {val}")
Se il DispBT è stato aggiunto al blocco ELE e a required_ele_keys, il caricamento delle tariffe solleva ValueError su -10.77. Se invece è stato hardcoded in calculate_sas, abbiamo replicato il problema del PUN. Nel §4 fornisco la patch con whitelist di chiavi a segno libero: serve in entrambi i casi.

2. I test aritmetici impattati sono 4, non 3. Audit completo sui test con valore assoluto atteso e residente=True:

Test	Atteso pre	Atteso post
test_caso_base_biorario_residente_3kw	672.23	660.39
test_perdite_di_rete_uplift_10pct	214.50 / 225.50	202.65 / 213.65
test_iva_elettrico_sempre_10	inline	inline + DispBT
test_esenzione_1800_kwh_residente_fino_3kw	inline	inline + DispBT
test_caso_monorario_non_residente_4_5kw (826.42) resta invariato: non residente. Tutti i test differenziali (delta fra due offerte) sono invarianti per costruzione. Se il quarto test ti risulta verde, il DispBT non è applicato in uno dei rami — dimmi quale e verifico.

3. Assunzione sul DispBT che ho dovuto fissare: l'ho modellato come dipendente solo da residente, non da potenza. Non ho modo di verificare se la detrazione decada sopra i 3 kW (a differenza dell'esenzione accisa, che decade). Ho aggiunto un test che documenta l'assunzione: va confermata su fonte ARERA prima del golden run.

1. parse/fasce.py — nuovo strato canonico
Radice del problema dei tre test flattener: sia il flattener sia il calcolatore fanno pattern matching su stringhe di display. Introduco un livello canonico condiviso.

python
Copy
"""Strato canonico per fasce, unità di misura, tipologia cliente.

Unica fonte di verità fra parse/flattener.py (scrive i campi canonici) ed
engine/sas_calculator_fast.py (li consuma). Elimina il pattern matching su
stringhe di display, causa delle tre classi di bug documentate:
  - fasce parziali F1+F3 / F1+F2 applicate al consumo totale
  - 'Percentuale' sommata come quota fissa in euro
  - 'Condominio Uso Domestico' incluso nel filtro 'Domestico'
"""
from __future__ import annotations

import re

TOT = "TOT"                      # marcatore: si applica al consumo totale
SEP = "|"                        # separatore dell'insieme canonico di fasce
UNKNOWN = "SCONOSCIUTA"

# ==============================================================================
# FASCIA_COMPONENTE — insieme di fasce su cui il prezzo si applica
# ==============================================================================
# Il codice 01 ('monorario/F1') è polisemico: vale F1 su offerta multioraria,
# ma vale l'intero consumo su offerta monoraria. Va quindi risolto insieme
# alla struttura dell'offerta -> resolve_fascia_set().
_BANDE_BY_FASCIA_CODE = {
    "01": ("F1",),
    "02": ("F2",),
    "03": ("F3",),
    "91": ("F2", "F3"),
    "92": ("F1", "F3"),          # prima cadeva nel ramo 'else -> TOT_CONS'
    "93": ("F1", "F2"),          # idem
}

# Label di display -> codice, per retrocompatibilità con i parquet già scritti
_FASCIA_CODE_BY_LABEL = {
    "monorario/f1": "01", "monorario": "01", "f1": "01",
    "f2": "02",
    "f3": "03",
    "f2+f3": "91", "f2 + f3": "91",
    "f1+f3": "92", "f1 + f3": "92",
    "f1+f2": "93", "f1 + f2": "93",
}

# ==============================================================================
# TIPOLOGIA_FASCE — struttura di fatturazione dell'offerta
# ==============================================================================
_STRUTTURA_BY_CODE = {
    "01": "MONO",
    "02": "BI",     # DA VERIFICARE: la label 'F2' nel DECODE_MAPS attuale è
                    # ambigua rispetto allo schema AU. Mappato BI in via
                    # prudenziale; vedi diagnostica FASCE_STRUTTURA_VERIFICATA.
    "03": "TRI",
    "91": "BI",
    "92": "BI",
    "93": "BI",
}
_STRUTTURA_DA_VERIFICARE = {"02"}

_STRUTTURA_CODE_BY_LABEL = {
    "monorario/f1": "01", "monorario": "01",
    "f2": "02",
    "f1, f2, f3": "03", "f1,f2,f3": "03", "trioraria": "03",
    "biorario (f1 / f2+f3)": "91",
    "biorario (f2 / f1+f3)": "92",
    "biorario (f3 / f1+f2)": "93",
    "biorario (f1 / f2 + f3)": "91",
}

# ==============================================================================
# UNITA_MISURA — natura del prezzo
# ==============================================================================
KIND_FISSO = "FISSO"                 # €/Anno, €
KIND_POTENZA = "POTENZA"             # €/kW
KIND_VOL_KWH = "VOL_KWH"             # €/kWh
KIND_VOL_SMC = "VOL_SMC"             # €/Smc
KIND_PERCENTUALE = "PERCENTUALE"     # % sull'indice di riferimento

_KIND_BY_UNITA_CODE = {
    "01": KIND_FISSO, "02": KIND_POTENZA, "03": KIND_VOL_KWH,
    "04": KIND_VOL_SMC, "05": KIND_FISSO, "06": KIND_PERCENTUALE,
}
_KIND_BY_UNITA_LABEL = {
    "€/anno": KIND_FISSO, "euro/anno": KIND_FISSO, "€": KIND_FISSO,
    "€/kw": KIND_POTENZA,
    "€/kwh": KIND_VOL_KWH,
    "€/smc": KIND_VOL_SMC,
    "percentuale": KIND_PERCENTUALE, "%": KIND_PERCENTUALE,
}

# ==============================================================================
# TIPO_CLIENTE
# ==============================================================================
TIPO_CLIENTE_LABEL = {
    "01": "Domestico",
    "02": "Altri Usi",
    "03": "Condominio Uso Domestico (Gas)",
}
_TIPO_CLIENTE_CODE_BY_LABEL = {
    "domestico": "01",
    "altri usi": "02",
    "condominio uso domestico (gas)": "03",
    "condominio uso domestico": "03",
}


# ==============================================================================
# Helper
# ==============================================================================
def _norm(v) -> str:
    return re.sub(r"\s+", " ", str(v or "").strip().lower())


def _as_code(value, by_label: dict, valid_codes) -> str | None:
    """Accetta indifferentemente un codice SII o una label di display."""
    raw = str(value or "").strip()
    if raw in valid_codes:
        return raw
    if raw.isdigit() and raw.zfill(2) in valid_codes:
        return raw.zfill(2)
    return by_label.get(_norm(raw))


def fascia_code(value) -> str | None:
    return _as_code(value, _FASCIA_CODE_BY_LABEL, _BANDE_BY_FASCIA_CODE)


def struttura_code(value) -> str | None:
    return _as_code(value, _STRUTTURA_CODE_BY_LABEL, _STRUTTURA_BY_CODE)


def struttura(value) -> str:
    """TIPOLOGIA_FASCE -> {'MONO','BI','TRI','SCONOSCIUTA'}."""
    code = struttura_code(value)
    return _STRUTTURA_BY_CODE.get(code, UNKNOWN) if code else UNKNOWN


def struttura_verificata(value) -> bool:
    return struttura_code(value) not in _STRUTTURA_DA_VERIFICARE


def resolve_fascia_set(fascia_value, tipologia_fasce_value) -> str:
    """Insieme canonico di fasce su cui applicare il prezzo.

    Ritorna 'TOT' oppure una stringa ordinata tipo 'F1|F3'. Ritorna
    'SCONOSCIUTA' se la fascia non è interpretabile: il chiamante decide se
    sollevare o degradare, ma non deve più cadere su un TOT implicito.

    >>> resolve_fascia_set('F1+F3', 'biorario (F1 / F2+F3)')
    'F1|F3'
    >>> resolve_fascia_set('monorario/F1', 'monorario/F1')
    'TOT'
    >>> resolve_fascia_set('monorario/F1', 'biorario (F1 / F2+F3)')
    'F1'
    """
    strutt = struttura(tipologia_fasce_value)
    if strutt == "MONO":
        return TOT

    code = fascia_code(fascia_value)
    if code is None:
        # Fascia assente su offerta non monoraria: caso legittimo per le
        # componenti non energetiche (es. commercializzazione a Smc sul gas).
        return TOT if not str(fascia_value or "").strip() else UNKNOWN

    bande = _BANDE_BY_FASCIA_CODE[code]
    if strutt == UNKNOWN and code == "01":
        # Non sappiamo se 01 significhi 'tutto' o 'F1': non indovinare.
        return UNKNOWN
    return SEP.join(sorted(bande))


def consumo_di_set(fascia_set: str, consumi: dict) -> float:
    """Consumo associato a un insieme canonico di fasce."""
    f1 = float(consumi.get("F1", 0) or 0)
    f2 = float(consumi.get("F2", 0) or 0)
    f3 = float(consumi.get("F3", 0) or 0)
    if fascia_set == TOT:
        return f1 + f2 + f3
    if fascia_set == UNKNOWN:
        return 0.0
    tot = {"F1": f1, "F2": f2, "F3": f3}
    return sum(tot[b] for b in fascia_set.split(SEP) if b in tot)


def unita_kind(unita_value) -> str:
    """UNITA_MISURA -> kind canonico. 'SCONOSCIUTA' se non riconosciuta."""
    code = _as_code(unita_value, _KIND_BY_UNITA_LABEL, _KIND_BY_UNITA_CODE)
    if code in _KIND_BY_UNITA_CODE:
        return _KIND_BY_UNITA_CODE[code]
    n = _norm(unita_value)
    if n in _KIND_BY_UNITA_LABEL:
        return _KIND_BY_UNITA_LABEL[n]
    if not n or n in ("nan", "none"):
        return UNKNOWN
    # Ordine obbligatorio: 'kwh' contiene 'kw'
    for needle, kind in (("kwh", KIND_VOL_KWH), ("smc", KIND_VOL_SMC),
                         ("kw", KIND_POTENZA), ("percent", KIND_PERCENTUALE),
                         ("%", KIND_PERCENTUALE)):
        if needle in n:
            return kind
    if n.startswith("€") or "euro" in n:
        return KIND_FISSO
    return UNKNOWN


def tipo_cliente_code(value) -> str | None:
    return _as_code(value, _TIPO_CLIENTE_CODE_BY_LABEL, TIPO_CLIENTE_LABEL)
2. parse/flattener.py — patch
python
Copy
# ==============================================================================
# In testa al file
# ==============================================================================
from parse import fasce as fz

# Chiavi di TIPO_CLIENTE che NON devono rientrare nel filtro "Domestico".
# Il display resta invariato per la dashboard; il filtro passa al codice.
# ==============================================================================


def _add_canonical_fields(record: dict) -> dict:
    """Arricchisce il record flat con i campi canonici consumati dal motore.

    Retrocompatibile: aggiunge colonne, non ne rinomina né rimuove. I parquet
    già scritti restano leggibili (il calcolatore ricava i canonici dalle label
    quando le colonne nuove sono assenti).
    """
    tipologia = record.get("TIPOLOGIA_FASCE")

    # --- Struttura di fatturazione: sostituisce str.contains('monorario') ---
    record["FASCE_STRUTTURA"] = fz.struttura(tipologia)
    record["FASCE_STRUTTURA_VERIFICATA"] = fz.struttura_verificata(tipologia)

    # --- Tipo cliente: sostituisce str.contains('Domestico') ---
    record["TIPO_CLIENTE_COD"] = fz.tipo_cliente_code(record.get("TIPO_CLIENTE"))

    # --- Componenti: insieme canonico di fasce + kind dell'unità ---
    non_gestite = []
    for c in range(1, 6):
        for i in range(1, 6):
            base = f"COMP_IMP_{c}_INT_{i}"
            if f"{base}_PREZZO" not in record:
                continue
            fascia_set = fz.resolve_fascia_set(record.get(f"{base}_FASCIA"), tipologia)
            kind = fz.unita_kind(record.get(f"{base}_UNITA"))
            record[f"{base}_FASCE_SET"] = fascia_set
            record[f"{base}_UNITA_KIND"] = kind
            if fascia_set == fz.UNKNOWN or kind == fz.UNKNOWN:
                non_gestite.append(f"{base}:{fascia_set}/{kind}")
            elif kind == fz.KIND_PERCENTUALE:
                non_gestite.append(f"{base}:PERCENTUALE")

    # --- Sconti: stessa normalizzazione su CODICE_COMP e unità ---
    for s in range(1, 16):
        if f"SCONTO_{s}_NOME" not in record:
            continue
        record[f"SCONTO_{s}_FASCE_SET"] = fz.resolve_fascia_set(
            record.get(f"SCONTO_{s}_CODICE_COMP"), tipologia
        )
        for p in range(1, 3):
            key = f"SCONTO_{s}_PREZZO_{p}"
            if f"{key}_VAL" in record:
                record[f"{key}_UNITA_KIND"] = fz.unita_kind(record.get(f"{key}_UNITA"))

    # --- Diagnostica: l'offerta è prezzabile senza approssimazioni? ---
    record["COMP_NON_GESTITE"] = ";".join(non_gestite) if non_gestite else None
    record["PREZZABILE"] = not non_gestite
    return record


# ==============================================================================
# In coda a flatten_offer(), immediatamente prima del return
# ==============================================================================
#   return _add_canonical_fields(record)
Nota sul terzo bug: la mancata gestione di Percentuale non è risolvibile nel flattener — serve il valore dell'indice di riferimento a cui la percentuale si applica. Il flattener ora la marca (COMP_NON_GESTITE, PREZZABILE=False); la risoluzione avviene nel calcolatore quando l'indice è noto (§6), altrimenti l'offerta viene esclusa dal ranking invece di essere sottoprezzata.

3. engine/index_prices.py — nuovo
python
Copy
"""Prezzi base degli indici di riferimento (PUN, PSV, TTF...).

Sostituisce le costanti hardcoded pun_base=0.105 e 0.35 €/Smc in
sas_calculator_fast.py. Tre requisiti che le costanti non soddisfacevano:

1. L'indice è dichiarato dall'offerta (campi IDX_* del flattener): due offerte
   variabili con indici diversi devono avere SAS diverse.
2. Gli indici a fasce (es. PUN orario) vanno applicati alla singola fascia,
   non al consumo totale.
3. La dashboard ha il Time Travel: il valore dell'indice deve essere risolto
   alla data di riferimento della simulazione, non alla data odierna.

ATTENZIONE — la tabella dei codici indice in data/config/index_prices.json è
un punto di partenza da validare contro i valori realmente presenti negli XML.
Usare scripts/audit_indici.py per enumerarli. Ogni voce ha un flag
'verificato': con strict=True gli indici non verificati sollevano.
"""
from __future__ import annotations

import json
import logging
import os
import warnings
from datetime import date, datetime

logger = logging.getLogger(__name__)

BANDE = ("F1", "F2", "F3")
ALL = "ALL"          # valore unico, applicato al consumo totale


class UnknownIndexError(ValueError):
    """Codice indice non presente nella configurazione."""


class IndexPriceProvider:
    def __init__(self, config_path: str = "data/config/index_prices.json",
                 strict: bool = True, max_age_days: int = 45):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configurazione indici non trovata: {config_path}")
        with open(config_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        self.metadata = data.get("metadata", {})
        self.periodi = data.get("periodi", [])
        self.alias = {self._norm(k): v for k, v in data.get("alias", {}).items()}
        self.fallback = data.get("fallback", {})
        self.uplift_perdite = float(data.get("uplift_perdite_ee", 1.10))
        self.strict = strict
        self.max_age_days = max_age_days
        self._validate()

    # ------------------------------------------------------------------ setup
    @staticmethod
    def _norm(v) -> str:
        return str(v or "").strip().upper().replace(" ", "_").replace("-", "_")

    @staticmethod
    def _to_date(v) -> date:
        if isinstance(v, date):
            return v
        return datetime.strptime(str(v)[:10], "%Y-%m-%d").date()

    def _validate(self):
        if not self.periodi:
            raise ValueError("index_prices.json: nessun periodo definito.")

        periodi = sorted(self.periodi, key=lambda p: self._to_date(p["valid_from"]))
        prev_to = None
        for p in periodi:
            vf, vt = self._to_date(p["valid_from"]), self._to_date(p["valid_to"])
            if vt < vf:
                raise ValueError(f"Periodo invertito: {vf} -> {vt}")
            if prev_to is not None and vf <= prev_to:
                raise ValueError(f"Periodi sovrapposti attorno a {vf}")
            prev_to = vt
            for code, spec in p["indici"].items():
                valori = spec.get("valori", {})
                if not valori:
                    raise ValueError(f"Indice '{code}' ({vf}) senza valori.")
                ignote = set(valori) - set(BANDE) - {ALL}
                if ignote:
                    raise ValueError(f"Indice '{code}': chiavi ignote {ignote}")
                if ALL in valori and len(valori) > 1:
                    raise ValueError(
                        f"Indice '{code}': 'ALL' non può coesistere con le fasce."
                    )
                for k, v in valori.items():
                    if not isinstance(v, (int, float)) or v < 0:
                        raise ValueError(f"Indice '{code}'.{k}: valore non valido {v!r}")
                if spec.get("commodity") not in ("E", "G"):
                    raise ValueError(f"Indice '{code}': commodity mancante o errata.")

        # Freschezza: il periodo che copre oggi non deve essere troppo vecchio.
        oggi = date.today()
        copre_oggi = [p for p in periodi
                      if self._to_date(p["valid_from"]) <= oggi <= self._to_date(p["valid_to"])]
        if not copre_oggi:
            msg = (f"index_prices.json non copre la data odierna ({oggi}). "
                   f"Ultimo periodo: {self._to_date(periodi[-1]['valid_to'])}.")
            if self.strict:
                raise ValueError(msg)
            warnings.warn(msg, RuntimeWarning, stacklevel=2)

        # Gli alias devono puntare a codici esistenti in almeno un periodo.
        noti = {c for p in periodi for c in p["indici"]}
        rotti = {k: v for k, v in self.alias.items() if v not in noti}
        if rotti:
            raise ValueError(f"Alias che puntano a indici inesistenti: {rotti}")

    # ------------------------------------------------------------- resoluzione
    def _periodo(self, data_rif: date) -> dict:
        for p in self.periodi:
            if self._to_date(p["valid_from"]) <= data_rif <= self._to_date(p["valid_to"]):
                return p
        raise UnknownIndexError(f"Nessun periodo indici copre la data {data_rif}.")

    def resolve_code(self, raw_code, commodity: str) -> str | None:
        """Normalizza e risolve gli alias. None se non risolvibile."""
        code = self._norm(raw_code)
        if not code or code in ("NAN", "NONE"):
            return None
        return self.alias.get(code, code)

    def get(self, raw_code, commodity: str, data_rif: date | None = None) -> dict:
        """Ritorna {'F1':x,'F2':y,'F3':z} oppure {'ALL':x} per l'indice dato.

        Con strict=True solleva su indice ignoto o non verificato; altrimenti
        applica il fallback per commodity emettendo un warning.
        """
        data_rif = data_rif or date.today()
        periodo = self._periodo(data_rif)
        code = self.resolve_code(raw_code, commodity)

        spec = periodo["indici"].get(code) if code else None
        if spec is None or spec.get("commodity") != commodity:
            fb = self.fallback.get(commodity)
            msg = (f"Indice '{raw_code}' (risolto '{code}') non definito per "
                   f"commodity '{commodity}' al {data_rif}.")
            if self.strict:
                raise UnknownIndexError(
                    f"{msg} Indici noti: "
                    f"{sorted(c for c, s in periodo['indici'].items() if s.get('commodity') == commodity)}"
                )
            if fb is None:
                raise UnknownIndexError(f"{msg} Nessun fallback configurato.")
            warnings.warn(f"{msg} Fallback su '{fb}'.", RuntimeWarning, stacklevel=2)
            spec = periodo["indici"][fb]

        if self.strict and not spec.get("verificato", False):
            raise UnknownIndexError(
                f"Indice '{code}' presente ma con verificato=false: il valore non è "
                f"stato validato contro il Portale Offerte. Usare strict=False per "
                f"procedere consapevolmente."
            )
        return dict(spec["valori"])

    def per_fascia(self, raw_code, commodity: str, data_rif=None) -> dict:
        """Come get(), ma sempre nella forma {'F1','F2','F3'} espansa.

        Un indice monorario ('ALL') viene replicato su tutte le fasce: così il
        calcolatore usa un solo percorso e il consumo pesa correttamente.
        """
        valori = self.get(raw_code, commodity, data_rif)
        if ALL in valori:
            return {b: valori[ALL] for b in BANDE}
        return {b: valori.get(b, 0.0) for b in BANDE}

    def codici_noti(self, commodity: str | None = None, data_rif=None) -> list[str]:
        periodo = self._periodo(data_rif or date.today())
        return sorted(
            c for c, s in periodo["indici"].items()
            if commodity is None or s.get("commodity") == commodity
        )
data/config/index_prices.json
json
Copy
{
  "metadata": {
    "descrizione": "Valori base degli indici di riferimento per le offerte a prezzo variabile.",
    "unita": "€/kWh per commodity E, €/Smc per commodity G",
    "AVVERTENZA": "I codici e i valori sono un punto di partenza NON VALIDATO. Popolare da scripts/audit_indici.py e dagli allegati AU, poi impostare verificato=true.",
    "last_review": "2026-08-26"
  },
  "uplift_perdite_ee": 1.10,
  "alias": {
    "PUN": "PUN_MONORARIO",
    "PUN_MEDIO": "PUN_MONORARIO",
    "PUN_ORARIO": "PUN_FASCE",
    "PUN_F1": "PUN_FASCE",
    "PSV": "PSV_MENSILE",
    "PSV_TRIM": "PSV_TRIMESTRALE",
    "PFOR": "PSV_TRIMESTRALE"
  },
  "fallback": {
    "E": "PUN_MONORARIO",
    "G": "PSV_MENSILE"
  },
  "periodi": [
    {
      "valid_from": "2026-07-01",
      "valid_to": "2026-09-30",
      "indici": {
        "PUN_MONORARIO": {
          "commodity": "E",
          "descrizione": "PUN medio aritmetico, valore unico su tutte le fasce",
          "valori": { "ALL": 0.105 },
          "verificato": false,
          "fonte": "valore ereditato dalla costante hardcoded, DA SOSTITUIRE"
        },
        "PUN_FASCE": {
          "commodity": "E",
          "descrizione": "PUN differenziato per fascia oraria",
          "valori": { "F1": 0.0, "F2": 0.0, "F3": 0.0 },
          "verificato": false,
          "fonte": "DA COMPILARE dagli esiti MGP"
        },
        "PSV_MENSILE": {
          "commodity": "G",
          "descrizione": "PSV medio mensile",
          "valori": { "ALL": 0.35 },
          "verificato": false,
          "fonte": "valore ereditato dalla costante hardcoded, DA SOSTITUIRE"
        },
        "PSV_TRIMESTRALE": {
          "commodity": "G",
          "descrizione": "PSV/PFOR trimestrale",
          "valori": { "ALL": 0.0 },
          "verificato": false,
          "fonte": "DA COMPILARE"
        }
      }
    }
  ]
}
scripts/audit_indici.py
Non ho la tabella ufficiale dei codici IDX dello schema AU, quindi la popoliamo dai dati reali invece di inventarla.

python
Copy
"""Enumera gli indici realmente dichiarati dalle offerte variabili.

Uso:
    python scripts/audit_indici.py [--parquet PATH] [--data 2026-08-25]

Produce la lista dei codici da inserire in data/config/index_prices.json,
ordinati per numero di offerte impattate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb

DEFAULT_PARQUET = "data/processed/storico_2026_full.parquet"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", default=DEFAULT_PARQUET)
    ap.add_argument("--data", default=None, help="filtro DATA_INIZIO <= data")
    ap.add_argument("--out", default="data/config/indici_rilevati.json")
    args = ap.parse_args()

    cols = duckdb.query(
        f"DESCRIBE SELECT * FROM read_parquet('{args.parquet}')"
    ).df()["column_name"].tolist()

    idx_cols = [c for c in cols if c.startswith("IDX")]
    if not idx_cols:
        print("Nessuna colonna IDX* nel parquet: il flattener non le sta scrivendo.")
        return

    print(f"Colonne indice trovate ({len(idx_cols)}):")
    for c in idx_cols:
        print(f"  {c}")

    report = {}
    for c in idx_cols:
        df = duckdb.query(f"""
            SELECT commodity, TIPO_OFFERTA, "{c}" AS valore, COUNT(*) AS n
            FROM read_parquet('{args.parquet}')
            WHERE "{c}" IS NOT NULL
              AND CAST("{c}" AS VARCHAR) NOT IN ('', 'nan', 'None', 'false', '0')
            GROUP BY 1, 2, 3
            ORDER BY n DESC
        """).df()
        if df.empty:
            continue
        report[c] = df.to_dict("records")
        print(f"\n--- {c} ---")
        print(df.head(20).to_string(index=False))

    # Offerte variabili senza alcun indice dichiarato: sono il problema vero,
    # perché oggi ricevono silenziosamente il valore hardcoded.
    orfane = duckdb.query(f"""
        SELECT commodity, COUNT(*) AS n
        FROM read_parquet('{args.parquet}')
        WHERE lower(CAST(TIPO_OFFERTA AS VARCHAR)) LIKE '%variabile%'
          AND {' AND '.join(f'''("{c}" IS NULL OR CAST("{c}" AS VARCHAR) IN ('', 'nan', 'None', 'false', '0'))''' for c in idx_cols)}
        GROUP BY 1
    """).df()
    print("\n=== Offerte VARIABILI senza indice dichiarato ===")
    print(orfane.to_string(index=False) if not orfane.empty else "nessuna")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(
        json.dumps({"indici": report, "variabili_senza_indice": orfane.to_dict("records")},
                   indent=2, default=str), encoding="utf-8")
    print(f"\nReport salvato in {args.out}")


if __name__ == "__main__":
    main()
4. engine/arera_tariffs.py — patch DispBT
python
Copy
# ==============================================================================
# Costanti di modulo
# ==============================================================================
# Chiavi ELE il cui valore può essere negativo per costruzione regolatoria.
# Il validatore originale respingeva ogni valore < 0, rendendo impossibile
# configurare la detrazione DispBT per i clienti domestici residenti.
ELE_SIGNED_KEYS = frozenset({"dispbt_fix"})

# Chiavi ELE obbligatorie e non negative.
ELE_REQUIRED_KEYS = (
    "dist_fix", "oneri_fix", "trasp_pot", "oneri_pot",
    "trasp_vol", "oneri_vol", "cdispd",
)

# Chiavi ELE opzionali, con default se assenti.
ELE_OPTIONAL_DEFAULTS = {
    "dispbt_fix": 0.0,   # €/anno. Negativo = detrazione (residenti).
}


# ==============================================================================
# In _validate_tariffs(): sostituire il blocco di validazione ELE
# ==============================================================================
        for tipo in ("residente", "non_residente"):
            if tipo not in self.ELE:
                raise ValueError(f"Manca la configurazione ELE per {tipo}")
            conf = self.ELE[tipo]

            for key in ELE_REQUIRED_KEYS:
                val = conf.get(key)
                if val is None:
                    raise ValueError(f"Parametro ELE '{key}' per {tipo} mancante")
                if val < 0:
                    raise ValueError(
                        f"Parametro ELE '{key}' per {tipo} negativo: {val}. "
                        f"Le sole chiavi a segno libero sono {sorted(ELE_SIGNED_KEYS)}."
                    )

            for key, default in ELE_OPTIONAL_DEFAULTS.items():
                if key not in conf:
                    logging.info(
                        "ELE[%s]: '%s' assente, default %s applicato.",
                        tipo, key, default
                    )
                    conf[key] = default
                elif not isinstance(conf[key], (int, float)):
                    raise ValueError(f"ELE[{tipo}]['{key}'] non numerico: {conf[key]!r}")

            # Coerenza di segno: una detrazione configurata positiva sarebbe un
            # aumento silenzioso della SAS. Meglio bloccare.
            if conf["dispbt_fix"] > 0:
                raise ValueError(
                    f"ELE[{tipo}]['dispbt_fix'] = {conf['dispbt_fix']} è positivo. "
                    f"DispBT è modellata come detrazione (<= 0). Se la componente "
                    f"è diventata un onere, aggiornare esplicitamente il segno "
                    f"e questo controllo."
                )


# ==============================================================================
# Nuovo metodo
# ==============================================================================
    def get_ele_dispbt(self, residente: bool) -> float:
        """Quota fissa DispBT in €/anno (<= 0 se detrazione).

        ASSUNZIONE DA VALIDARE: la detrazione dipende solo dalla residenza,
        non dalla potenza impegnata (a differenza dell'esenzione accisa sui
        primi 1800 kWh, che decade sopra i 3 kW). Confermare su delibera ARERA
        prima di validare il golden dataset.
        """
        conf = self.ELE["residente" if residente else "non_residente"]
        return float(conf.get("dispbt_fix", 0.0))
5. engine/sas_calculator_fast.py — calculate_sas riscritta
Interventi: DispBT, indici da configurazione, fasce generiche, unità per kind, filtro TIPO_CLIENTE esatto, diagnostica.

python
Copy
import logging
from datetime import date

import numpy as np
import pandas as pd

from engine.arera_tariffs import AreraTariffs
from engine.index_prices import IndexPriceProvider
from parse import fasce as fz

logger = logging.getLogger(__name__)

ACCISA_EE = 0.0227
SOGLIA_ESENZIONE_KWH = 1800
POTENZA_MAX_ESENZIONE = 3.0
IVA_EE = 1.10
SOGLIA_IVA_GAS_SMC = 480
UPLIFT_PERDITE = 1.10


class FastSASCalculator:
    def __init__(self, df, arera: AreraTariffs = None, tariffs_path: str = None,
                 indici: IndexPriceProvider = None, indici_path: str = None,
                 strict: bool = False):
        self.df = df.copy()
        self.strict = strict
        if arera is not None:
            self.arera = arera
        else:
            self.arera = AreraTariffs(tariffs_path) if tariffs_path else AreraTariffs()
        if indici is not None:
            self.indici = indici
        elif indici_path:
            self.indici = IndexPriceProvider(indici_path, strict=strict)
        else:
            self.indici = IndexPriceProvider(strict=strict)

    # ------------------------------------------------------------------ utils
    def _col(self, df, name, default=""):
        if name in df.columns:
            return df[name].astype(str)
        return pd.Series([str(default)] * len(df), index=df.index, dtype=object).astype(str)

    def _num(self, df, name, default=0.0):
        """Parsing numerico con log degli scarti (prima erano silenziosi)."""
        if name not in df.columns:
            return np.full(len(df), default, dtype=float)
        raw = df[name].astype(str).str.strip().str.replace(",", ".", regex=False)
        out = pd.to_numeric(raw, errors="coerce")
        scarti = out.isna() & ~raw.isin(["", "nan", "None", "NaN", "<NA>"])
        if scarti.any():
            esempi = raw[scarti].unique()[:5].tolist()
            logger.warning("%s: %d valori non parsabili azzerati. Esempi: %s",
                           name, int(scarti.sum()), esempi)
        return out.fillna(default).to_numpy(dtype=float)

    def _fasce_set(self, df, base_col, tipologia_col="TIPOLOGIA_FASCE"):
        """Insieme canonico di fasce. Usa la colonna scritta dal flattener se
        presente, altrimenti la ricava dalle label (parquet storici)."""
        canon = f"{base_col}_FASCE_SET"
        if canon in df.columns:
            s = df[canon].astype(str)
            if not s.isin([fz.UNKNOWN, "nan", "None", ""]).all():
                return s.to_numpy()
        fascia = self._col(df, f"{base_col}_FASCIA")
        tipologia = self._col(df, tipologia_col)
        return np.array([
            fz.resolve_fascia_set(f, t) for f, t in zip(fascia, tipologia)
        ], dtype=object)

    def _unita_kind(self, df, col):
        canon = f"{col}_KIND"
        if canon in df.columns:
            s = df[canon].astype(str)
            if not s.isin([fz.UNKNOWN, "nan", "None", ""]).all():
                return s.to_numpy()
        return np.array([fz.unita_kind(u) for u in self._col(df, col)], dtype=object)

    # ----------------------------------------------------------------- filtro
    def filter_offers(self, commodity="E", tipo_offerta="Fisso",
                      tipo_cliente="Domestico", fasce="Biorario",
                      regione="Lombardia", provincia="015", comune="F205",
                      escludi_non_prezzabili=True):
        f = self.df
        f = f[f["commodity"] == commodity]

        # TIPO_OFFERTA: match esatto sulla label canonica. 'Fisso' con
        # str.contains non era ambiguo, ma l'esattezza previene regressioni.
        if tipo_offerta and tipo_offerta != "Tutte":
            f = f[self._col(f, "TIPO_OFFERTA").str.strip().str.casefold()
                  == tipo_offerta.strip().casefold()]

        # FIX: str.contains('Domestico') includeva 'Condominio Uso Domestico
        # (Gas)' (TIPO_CLIENTE 03), contaminando il ranking domestico gas.
        if tipo_cliente and tipo_cliente != "Tutti":
            atteso = fz.tipo_cliente_code(tipo_cliente)
            if "TIPO_CLIENTE_COD" in f.columns:
                codici = f["TIPO_CLIENTE_COD"].astype(str)
            else:
                codici = pd.Series(
                    [fz.tipo_cliente_code(v) for v in self._col(f, "TIPO_CLIENTE")],
                    index=f.index, dtype=object,
                ).astype(str)
            f = f[codici == str(atteso)]

        # Territorialità: 'None' come stringa ora è trattata come nazionale
        # anche per REGIONE (prima solo PROVINCIA e COMUNE).
        NAZ = {"", "nan", "None", "none", "NONE", "<NA>"}
        if regione and regione != "Tutte" and "REGIONE" in f.columns:
            istat = {
                "Piemonte": "01", "Valle d'Aosta": "02", "Lombardia": "03",
                "Trentino-Alto Adige": "04", "Veneto": "05",
                "Friuli-Venezia Giulia": "06", "Liguria": "07",
                "Emilia-Romagna": "08", "Toscana": "09", "Umbria": "10",
                "Marche": "11", "Lazio": "12", "Abruzzo": "13", "Molise": "14",
                "Campania": "15", "Puglia": "16", "Basilicata": "17",
                "Calabria": "18", "Sicilia": "19", "Sardegna": "20",
            }
            if regione not in istat:
                raise KeyError(f"Regione '{regione}' non mappata sui codici ISTAT.")
            v = self._col(f, "REGIONE")
            f = f[v.isin(NAZ) | (v == istat[regione])]

        for col, target in (("PROVINCIA", provincia), ("COMUNE", comune)):
            if target and col in f.columns:
                v = self._col(f, col)
                f = f[v.isin(NAZ) | (v == str(target))]

        # FIX: la regex 'F2|F3|biorario|Peak/OffPeak' intercettava anche
        # TIPOLOGIA_FASCE = 'F1, F2, F3' (trioraria). Ora si filtra sulla
        # struttura canonica.
        if commodity == "E" and fasce and fasce != "Tutte":
            if "FASCE_STRUTTURA" in f.columns:
                strutt = f["FASCE_STRUTTURA"].astype(str)
            else:
                strutt = pd.Series(
                    [fz.struttura(v) for v in self._col(f, "TIPOLOGIA_FASCE")],
                    index=f.index, dtype=object,
                ).astype(str)
            atteso = {"Monorario": "MONO", "Biorario": "BI", "Triorario": "TRI"}
            if fasce not in atteso:
                raise ValueError(f"Valore 'fasce' non gestito: {fasce!r}")
            f = f[strutt == atteso[fasce]]

        f = f[~self._col(f, "NOME_OFFERTA").str.contains("Sottocosto", case=False, na=False)]

        # Un'offerta che non sappiamo prezzare non deve comparire in cima al
        # ranking come la più conveniente: la si esclude e la si conta.
        if escludi_non_prezzabili and "PREZZABILE" in f.columns:
            non_prezzabili = ~f["PREZZABILE"].fillna(True).astype(bool)
            if non_prezzabili.any():
                logger.warning("%d offerte escluse perché non prezzabili "
                               "(componenti percentuali o fasce ignote).",
                               int(non_prezzabili.sum()))
            f = f[~non_prezzabili]
        return f

    # ---------------------------------------------------------------- calcolo
    def calculate_sas(self, filtered_df, consumi: dict, potenza: float,
                      is_dual_fuel: bool = False, is_domiciliazione: bool = False,
                      regione: str = "Lombardia", residente: bool = True,
                      data_riferimento: date = None):
        if filtered_df is None or filtered_df.empty:
            return pd.DataFrame()

        df = filtered_df.copy()
        n = len(df)
        data_rif = data_riferimento or date.today()

        F = {b: float(consumi.get(b, 0) or 0) for b in ("F1", "F2", "F3")}
        TOT_CONS = sum(F.values())
        p_val = float(potenza) if potenza is not None else 0.0

        costo_fix = np.zeros(n)
        costo_vol = np.zeros(n)

        is_ee = (df["commodity"] == "E").to_numpy()
        is_gas = (df["commodity"] == "G").to_numpy()
        comprensivo = self._col(df, "PREZZO_COMPRENSIVO_PERDITE_RETE", "SI") \
            .str.strip().str.upper().to_numpy()
        applica_perdite = is_ee & (comprensivo != "SI")
        is_variabile = self._col(df, "TIPO_OFFERTA").str.strip().str.lower() \
            .str.contains("variabile").to_numpy()
        is_mista = self._col(df, "TIPO_OFFERTA").str.strip().str.lower() \
            .str.contains("mista").to_numpy()
        if is_mista.any():
            logger.warning("%d offerte TIPO_OFFERTA='Mista': la quota indicizzata "
                           "non è modellata, SAS potenzialmente sottostimata.",
                           int(is_mista.sum()))

        # --- Indici di riferimento, per riga e per fascia -------------------
        idx_base = self._resolve_index_base(df, data_rif)   # dict fascia -> array

        # --- Componenti di prezzo ------------------------------------------
        pct_non_risolte = np.zeros(n, dtype=bool)
        for c in range(1, 6):
            for i in range(1, 6):
                base = f"COMP_IMP_{c}_INT_{i}"
                if f"{base}_PREZZO" not in df.columns:
                    continue

                prezzo = self._num(df, f"{base}_PREZZO")
                kind = self._unita_kind(df, f"{base}_UNITA")
                fset = self._fasce_set(df, base)

                is_vol = np.isin(kind, [fz.KIND_VOL_KWH, fz.KIND_VOL_SMC])
                prezzo_eff = np.where(applica_perdite & (kind == fz.KIND_VOL_KWH),
                                      prezzo * UPLIFT_PERDITE, prezzo)

                costo_fix += np.where(kind == fz.KIND_FISSO, prezzo, 0.0)
                costo_fix += np.where(kind == fz.KIND_POTENZA, prezzo * p_val, 0.0)

                # Consumo associato all'insieme canonico di fasce: un unico
                # percorso, nessun ramo 'else -> TOT_CONS' che sovrastimava
                # F1+F3 e F1+F2.
                cons = self._consumo_da_set(fset, consumi)
                costo_vol += np.where(is_vol, prezzo_eff * cons, 0.0)

                # FIX: 'Percentuale' non è più sommata come euro/anno.
                # Si applica all'indice quando è noto, altrimenti si marca.
                is_pct = kind == fz.KIND_PERCENTUALE
                if is_pct.any():
                    base_idx = self._indice_su_set(idx_base, fset, consumi, applica_perdite)
                    ok = is_pct & (base_idx > 0)
                    costo_vol += np.where(ok, prezzo / 100.0 * base_idx, 0.0)
                    pct_non_risolte |= is_pct & ~ok

                ignote = np.isin(kind, [fz.UNKNOWN]) & (prezzo != 0)
                if ignote.any():
                    logger.warning("%s: %d componenti con unità non riconosciuta, "
                                   "ignorate nel calcolo.", base, int(ignote.sum()))

        # --- Sconti ---------------------------------------------------------
        for s in range(1, 16):
            if f"SCONTO_{s}_NOME" not in df.columns:
                continue
            has = df[f"SCONTO_{s}_NOME"].notna().to_numpy()
            cond = self._col(df, f"SCONTO_{s}_COND_APP").str.strip().to_numpy()
            valid = self._col(df, f"SCONTO_{s}_VALIDITA").str.strip().to_numpy()
            fset_sc = self._fasce_set(df, f"SCONTO_{s}", tipologia_col="TIPOLOGIA_FASCE") \
                if f"SCONTO_{s}_FASCE_SET" in df.columns else None

            applica = has.copy()
            # Riscritto: 'ndarray & bool' funzionava per caso.
            if not is_dual_fuel:
                applica &= cond != "Altro"
            if not is_domiciliazione:
                applica &= cond != "Pagamento SDD"
            applica &= np.isin(valid, ["Ingresso", "entro 12 mesi", "Sempre",
                                       "nan", "", "None"])

            for p in range(1, 3):
                if f"SCONTO_{s}_PREZZO_{p}_VAL" not in df.columns:
                    continue
                val = self._num(df, f"SCONTO_{s}_PREZZO_{p}_VAL")
                kind = self._unita_kind(df, f"SCONTO_{s}_PREZZO_{p}_UNITA")
                tipo = self._col(df, f"SCONTO_{s}_PREZZO_{p}_TIPO").to_numpy()
                attivo = applica & (val > 0)

                costo_fix -= np.where(
                    attivo & ((kind == fz.KIND_FISSO) | (tipo == "Sconto fisso")), val, 0.0)

                is_vol = np.isin(kind, [fz.KIND_VOL_KWH, fz.KIND_VOL_SMC])
                if fset_sc is not None:
                    cons = self._consumo_da_set(fset_sc, consumi)
                else:
                    codice = self._col(df, f"SCONTO_{s}_CODICE_COMP").to_numpy()
                    fset_legacy = np.array([
                        fz.resolve_fascia_set(cc, tt)
                        for cc, tt in zip(codice, self._col(df, "TIPOLOGIA_FASCE"))
                    ], dtype=object)
                    cons = self._consumo_da_set(fset_legacy, consumi)
                costo_vol -= np.where(attivo & is_vol, val * cons, 0.0)

        # --- CdispD e quota indicizzata ------------------------------------
        conf = self.arera.ELE["residente" if residente else "non_residente"]
        cdispd = self._num(df, "DISP_CdispD_VALORE", conf["cdispd"])
        cdispd = np.where(cdispd == 0, conf["cdispd"], cdispd)
        costo_vol += np.where(is_ee, cdispd * TOT_CONS, 0.0)

        # Sostituisce pun_base=0.105 e 0.35 hardcoded.
        quota_indice = np.zeros(n)
        for b in ("F1", "F2", "F3"):
            base_b = np.where(applica_perdite, idx_base[b] * UPLIFT_PERDITE, idx_base[b])
            quota_indice += base_b * F[b]
        gas_idx = idx_base["F1"] * TOT_CONS      # gas: indice sempre monorario
        costo_vol += np.where(is_ee & is_variabile, quota_indice, 0.0)
        costo_vol += np.where(is_gas & is_variabile, gas_idx, 0.0)

        costo_venditore = costo_fix + costo_vol

        # --- Elettrico: reti, oneri, DispBT, accisa, IVA -------------------
        reti_ele = (
            conf["dist_fix"] + conf["oneri_fix"]
            + (conf["trasp_pot"] + conf["oneri_pot"]) * p_val
            + (conf["trasp_vol"] + conf["oneri_vol"]) * TOT_CONS
        )
        # NUOVO: detrazione DispBT per i domestici residenti (€/anno, <= 0).
        # Entra nell'imponibile, quindi è soggetta a IVA; non incide sulle
        # accise, che si applicano ai kWh.
        dispbt = self.arera.get_ele_dispbt(residente)

        if residente and p_val <= POTENZA_MAX_ESENZIONE:
            accisa_ee = ACCISA_EE * max(0.0, TOT_CONS - SOGLIA_ESENZIONE_KWH)
        else:
            accisa_ee = ACCISA_EE * TOT_CONS

        sas_ele = (costo_venditore + reti_ele + dispbt + accisa_ee) * IVA_EE

        # --- Gas ------------------------------------------------------------
        gas_fix, gas_vol = self.arera.get_gas_costi_regolati(
            regione, TOT_CONS, include_taxes=False)
        arera_gas = gas_fix + gas_vol * TOT_CONS

        # Accise dalla configurazione (prima erano hardcoded coi valori Nord,
        # ignorando GAS_ACCISE e sovrastimando il Mezzogiorno).
        _, territorio = self.arera.resolve_zona_gas(regione)
        accisa_gas = self.arera.get_gas_accisa_avg(territorio, TOT_CONS) * TOT_CONS
        addiz = self.arera.GAS_ADDIZIONALE.get(
            regione, self.arera.GAS_ADDIZIONALE.get("DEFAULT", 0.019))
        imposte_gas = accisa_gas + addiz * TOT_CONS

        imponibile_gas = costo_venditore + arera_gas + imposte_gas
        den = max(1.0, TOT_CONS)
        q10 = min(SOGLIA_IVA_GAS_SMC, TOT_CONS) / den
        q22 = max(0.0, TOT_CONS - SOGLIA_IVA_GAS_SMC) / den
        sas_gas = imponibile_gas * (1 + q10 * 0.10 + q22 * 0.22)

        sas = np.where(is_ee, sas_ele, sas_gas)

        # --- Output ---------------------------------------------------------
        df["SPESA_MATERIA_PRIMA"] = np.round(costo_venditore, 2)
        df["QUOTA_FISSA"] = np.round(costo_fix, 2)
        df["PREZZO_UNITARIO"] = np.round(costo_vol / TOT_CONS, 4) if TOT_CONS > 0 else 0.0
        df["SAS"] = np.round(sas, 2)
        df["DISPBT_APPLICATO"] = np.where(is_ee, round(dispbt, 2), 0.0)
        df["INDICE_APPLICATO"] = np.round(
            np.where(is_ee & is_variabile, quota_indice,
                     np.where(is_gas & is_variabile, gas_idx, 0.0)), 2)
        df["DIAGNOSTICA"] = np.where(
            pct_non_risolte, "COMP_PERCENTUALE_NON_RISOLTA",
            np.where(is_mista, "TIPO_OFFERTA_MISTA_NON_MODELLATA", ""))

        col_piva = "PIVA_UTENTE" if "PIVA_UTENTE" in df.columns else "PIVA_VENDITORE"
        col_cod = "CODICE_OFFERTA" if "CODICE_OFFERTA" in df.columns else "COD_OFFERTA"
        out = [col_piva, col_cod, "NOME_OFFERTA", "SPESA_MATERIA_PRIMA",
               "QUOTA_FISSA", "PREZZO_UNITARIO", "SAS",
               "DISPBT_APPLICATO", "INDICE_APPLICATO", "DIAGNOSTICA"]
        for extra in ("COND_Attivazione_LIMITANTE", "COND_Pluriennale_LIMITANTE"):
            if extra in df.columns:
                out.append(extra)

        res = df[out].rename(columns={col_piva: "PIVA_VENDITORE", col_cod: "COD_OFFERTA"})
        return res.sort_values("SAS").reset_index(drop=True) if len(res) else res

    # ----------------------------------------------------------- helper vett.
    @staticmethod
    def _consumo_da_set(fset_arr, consumi: dict) -> np.ndarray:
        """Mappa l'insieme canonico di fasce sul consumo. Il numero di insiemi
        distinti è piccolo (<= 8): si risolve una volta e si mappa."""
        cache = {s: fz.consumo_di_set(s, consumi) for s in set(map(str, fset_arr))}
        return np.array([cache[str(s)] for s in fset_arr], dtype=float)

    def _resolve_index_base(self, df, data_rif) -> dict:
        """Valore base dell'indice per riga e per fascia."""
        codici = self._declared_index(df)
        commodity = df["commodity"].astype(str).to_numpy()
        out = {b: np.zeros(len(df)) for b in ("F1", "F2", "F3")}
        cache = {}
        for i, (code, comm) in enumerate(zip(codici, commodity)):
            key = (code, comm)
            if key not in cache:
                try:
                    cache[key] = self.indici.per_fascia(code, comm, data_rif)
                except Exception as exc:
                    if self.strict:
                        raise
                    logger.warning("Indice non risolto (%s, %s): %s", code, comm, exc)
                    cache[key] = {b: 0.0 for b in ("F1", "F2", "F3")}
            for b in ("F1", "F2", "F3"):
                out[b][i] = cache[key][b]
        return out

    def _declared_index(self, df) -> np.ndarray:
        """Codice indice dichiarato dall'offerta.

        Precedenza: IDX_CODICE (canonico) > IDX_TIPO (legacy) > flag IDX_*.
        """
        for col in ("IDX_CODICE", "IDX_TIPO"):
            if col in df.columns:
                s = self._col(df, col).str.strip()
                if not s.isin(["", "nan", "None"]).all():
                    return s.to_numpy()

        flag_cols = [c for c in df.columns
                     if c.startswith("IDX_") and c not in ("IDX_CODICE", "IDX_TIPO")]
        if not flag_cols:
            return np.array([""] * len(df), dtype=object)

        out = np.array([""] * len(df), dtype=object)
        for c in flag_cols:
            attivo = df[c].astype(str).str.strip().str.lower() \
                .isin(["true", "1", "si", "sì", "x"]).to_numpy()
            nuovo = attivo & (out == "")
            out = np.where(nuovo, c[len("IDX_"):], out)
        return out

    def _indice_su_set(self, idx_base, fset_arr, consumi, applica_perdite):
        """Base monetaria dell'indice sull'insieme di fasce, per le componenti
        espresse in percentuale."""
        tot = np.zeros(len(fset_arr))
        for b in ("F1", "F2", "F3"):
            cons_b = float(consumi.get(b, 0) or 0)
            in_set = np.array([b in str(s).split(fz.SEP) or str(s) == fz.TOT
                               for s in fset_arr])
            base = np.where(applica_perdite, idx_base[b] * UPLIFT_PERDITE, idx_base[b])
            tot += np.where(in_set, base * cons_b, 0.0)
        return tot
6. tests/conftest.py — aggiunte
python
Copy
# ==============================================================================
# Costanti condivise: espresse come simboli, non come float magici, così un
# aggiornamento regolatorio è una modifica di una riga.
# ==============================================================================
DISPBT_RESIDENTE = -10.77      # €/anno, detrazione domestici residenti
DISPBT_NON_RESIDENTE = 0.0
IVA_EE = 1.10
ACCISA_EE = 0.0227
SOGLIA_ESENZIONE_KWH = 1800

# Indici sintetici: valori tondi, per rendere l'aritmetica verificabile a mano.
IDX_SYN = {
    "PUN_MONORARIO": 0.100,
    "PUN_FASCE": {"F1": 0.120, "F2": 0.090, "F3": 0.070},
    "PSV_MENSILE": 0.300,
    "PSV_TRIMESTRALE": 0.320,
}


# --- in build_synthetic_tariffs(): aggiungere ai blocchi ELE ---
#   "residente":     {..., "dispbt_fix": DISPBT_RESIDENTE},
#   "non_residente": {..., "dispbt_fix": DISPBT_NON_RESIDENTE},


def build_synthetic_indices(valid_from="2020-01-01", valid_to="2099-12-31") -> dict:
    return {
        "metadata": {"source": "SYNTHETIC — test fixture"},
        "uplift_perdite_ee": 1.10,
        "alias": {"PUN": "PUN_MONORARIO", "PUN_F1": "PUN_FASCE",
                  "PSV": "PSV_MENSILE", "PSV_TRIM": "PSV_TRIMESTRALE"},
        "fallback": {"E": "PUN_MONORARIO", "G": "PSV_MENSILE"},
        "periodi": [{
            "valid_from": valid_from, "valid_to": valid_to,
            "indici": {
                "PUN_MONORARIO": {"commodity": "E", "verificato": True,
                                  "valori": {"ALL": IDX_SYN["PUN_MONORARIO"]}},
                "PUN_FASCE": {"commodity": "E", "verificato": True,
                              "valori": dict(IDX_SYN["PUN_FASCE"])},
                "PSV_MENSILE": {"commodity": "G", "verificato": True,
                                "valori": {"ALL": IDX_SYN["PSV_MENSILE"]}},
                "PSV_TRIMESTRALE": {"commodity": "G", "verificato": True,
                                    "valori": {"ALL": IDX_SYN["PSV_TRIMESTRALE"]}},
            },
        }],
    }


@pytest.fixture
def write_indices(tmp_path):
    def _write(payload: dict, name: str = "index_prices.json") -> str:
        p = tmp_path / name
        p.write_text(json.dumps(payload), encoding="utf-8")
        return str(p)
    return _write


@pytest.fixture(scope="session")
def synthetic_indices_path(tmp_path_factory) -> str:
    p = tmp_path_factory.mktemp("indici") / "index_prices.json"
    p.write_text(json.dumps(build_synthetic_indices()), encoding="utf-8")
    return str(p)


@pytest.fixture
def indici(synthetic_indices_path):
    from engine.index_prices import IndexPriceProvider
    return IndexPriceProvider(synthetic_indices_path, strict=True)


@pytest.fixture
def arera_no_dispbt(write_tariffs, synthetic_tariffs_dict):
    """Tariffe identiche ma con DispBT azzerata: isola l'effetto della
    detrazione senza confondere residente/non residente, che differiscono
    anche su dist_fix, trasp_pot e oneri_vol."""
    import copy
    from engine.arera_tariffs import AreraTariffs
    payload = copy.deepcopy(synthetic_tariffs_dict)
    for tipo in ("residente", "non_residente"):
        payload["ELE"][tipo]["dispbt_fix"] = 0.0
    return AreraTariffs(write_tariffs(payload))


# --- run_sas / sas_of: iniettare anche il provider indici ---
@pytest.fixture
def run_sas(arera, indici):
    from engine.sas_calculator_fast import FastSASCalculator

    def _run(df, consumi, potenza=3.0, calc_arera=None, **kwargs):
        calc = FastSASCalculator(df, arera=calc_arera or arera,
                                 indici=indici, strict=True)
        return calc.calculate_sas(df, consumi=consumi, potenza=potenza, **kwargs)
    return _run
7. tests/test_sas_calculator.py — sostituzioni
Sostituisci i quattro test indicati e la classe TestVariabile. Il resto del file resta valido.

python
Copy
from tests.conftest import (ACCISA_EE, DISPBT_RESIDENTE, IDX_SYN, IVA_EE,
                            PROFILO_BIORARIO_ARERA)

DISPBT_RES = DISPBT_RESIDENTE

# Aggregati delle tariffe sintetiche, per non ripetere i numeri nei test.
def reti_ele_residente(potenza, tot_cons):
    return 20.0 + 0.0 + (10.0 + 0.0) * potenza + (0.010 + 0.020) * tot_cons

def reti_ele_non_residente(potenza, tot_cons):
    return 30.0 + 0.0 + (12.0 + 0.0) * potenza + (0.010 + 0.030) * tot_cons

CDISPD_SYN = 0.0150


# ==============================================================================
# TestElettricoAritmetica — versioni aggiornate
# ==============================================================================
    def test_caso_base_biorario_residente_3kw(self, offer_factory, make_df, sas_of):
        """
        costo_fix   = 96.00
        energia     = 0.13*891 + 0.12*837 + 0.11*972      = 323.19
        cdispd      = 0.0150*2700                          =  40.50
        reti+oneri  = 20 + 10*3 + 0.030*2700               = 131.00
        DispBT      = detrazione residenti                 = -10.77
        accisa      = 0.0227*(2700-1800)                   =  20.43
        imponibile  = 96 + 363.69 + 131.00 - 10.77 + 20.43 = 600.35
        SAS         = 600.35 * 1.10                        = 660.39
                      (era 672.23 prima dell'introduzione del DispBT: -11.85)
        """
        df = make_df(offer_factory(componenti=[
            {"prezzo": 96.0, "unita": "€/Anno", "fascia": ""},
            comp(0.13, fascia="monorario/F1"),
            comp(0.12, fascia="F2"),
            comp(0.11, fascia="F3"),
        ]))
        imponibile = (96.0 + 323.19 + CDISPD_SYN * 2700
                      + reti_ele_residente(3.0, 2700) + DISPBT_RES
                      + ACCISA_EE * 900)
        assert imponibile == pytest.approx(600.35, abs=0.01)
        # abs=0.02 e non 0.01: 600.35*1.10 = 660.385 cade su un tie di
        # arrotondamento, np.round può restituire 660.38 o 660.39.
        assert sas_of(df, BIO, potenza=3.0, residente=True) == \
            pytest.approx(imponibile * IVA_EE, abs=0.02)

    def test_iva_elettrico_sempre_10(self, offer_factory, make_df, run_sas):
        df = make_df(offer_factory(componenti=[comp(0.10)]))
        res = run_sas(df, MONO_2700, potenza=3.0, residente=True)
        imponibile = (0.10 * 2700 + CDISPD_SYN * 2700
                      + reti_ele_residente(3.0, 2700) + DISPBT_RES
                      + ACCISA_EE * 900)
        assert float(res.iloc[0]["SAS"]) == pytest.approx(imponibile * IVA_EE, abs=0.02)

    def test_esenzione_1800_kwh_residente_fino_3kw(self, offer_factory, make_df, sas_of):
        df = make_df(offer_factory(componenti=[comp(0.10)]))
        consumi = {"F1": 1500, "F2": 0, "F3": 0}
        imponibile = (0.10 * 1500 + CDISPD_SYN * 1500
                      + reti_ele_residente(3.0, 1500) + DISPBT_RES)   # accisa = 0
        assert sas_of(df, consumi, potenza=3.0, residente=True) == \
            pytest.approx(imponibile * IVA_EE, abs=0.02)

    def test_perdite_di_rete_uplift_10pct(self, offer_factory, make_df, sas_of):
        kw = dict(componenti=[comp(0.10)])
        df_si = make_df(offer_factory(comprensivo_perdite="SI", **kw))
        df_no = make_df(offer_factory(comprensivo_perdite="NO", **kw))
        consumi = {"F1": 1000, "F2": 0, "F3": 0}
        fisso = CDISPD_SYN * 1000 + reti_ele_residente(3.0, 1000) + DISPBT_RES
        # 202.65 e 213.65 (erano 214.50 e 225.50: -11.85 di DispBT lordo IVA)
        assert sas_of(df_si, consumi) == pytest.approx((0.10 * 1000 + fisso) * IVA_EE, abs=0.02)
        assert sas_of(df_no, consumi) == pytest.approx((0.11 * 1000 + fisso) * IVA_EE, abs=0.02)
        assert sas_of(df_no, consumi) - sas_of(df_si, consumi) == \
            pytest.approx(0.10 * 1000 * 0.10 * IVA_EE, abs=0.02)


# ==============================================================================
# Nuova classe: DispBT
# ==============================================================================
class TestDispBT:

    def test_detrazione_applicata_ai_residenti(self, offer_factory, make_df,
                                               run_sas, arera_no_dispbt):
        df = make_df(offer_factory(componenti=[comp(0.10)]))
        con = float(run_sas(df, MONO_2700, residente=True).iloc[0]["SAS"])
        senza = float(run_sas(df, MONO_2700, residente=True,
                              calc_arera=arera_no_dispbt).iloc[0]["SAS"])
        assert con - senza == pytest.approx(DISPBT_RES * IVA_EE, abs=0.02)
        assert con < senza, "DispBT è una detrazione: deve abbassare la SAS"

    def test_non_applicata_ai_non_residenti(self, offer_factory, make_df,
                                            run_sas, arera_no_dispbt):
        df = make_df(offer_factory(componenti=[comp(0.10)]))
        con = float(run_sas(df, MONO_2700, residente=False).iloc[0]["SAS"])
        senza = float(run_sas(df, MONO_2700, residente=False,
                              calc_arera=arera_no_dispbt).iloc[0]["SAS"])
        assert con == pytest.approx(senza, abs=0.01)

    def test_soggetta_a_iva_10(self, offer_factory, make_df, run_sas, arera_no_dispbt):
        """La detrazione entra nell'imponibile: l'effetto sulla SAS è -10.77*1.10,
        non -10.77."""
        df = make_df(offer_factory(componenti=[comp(0.10)]))
        delta = (float(run_sas(df, MONO_2700).iloc[0]["SAS"])
                 - float(run_sas(df, MONO_2700, calc_arera=arera_no_dispbt).iloc[0]["SAS"]))
        assert delta == pytest.approx(-11.847, abs=0.02)
        assert delta != pytest.approx(DISPBT_RES, abs=0.5)

    @pytest.mark.parametrize("potenza", [3.0, 3.5, 4.5, 6.0])
    def test_indipendente_dalla_potenza(self, offer_factory, make_df, run_sas,
                                        arera_no_dispbt, potenza):
        """ASSUNZIONE DA VALIDARE: la detrazione non decade sopra i 3 kW,
        a differenza dell'esenzione accisa. Se la delibera dice il contrario,
        questo test va invertito e get_ele_dispbt() deve ricevere la potenza."""
        df = make_df(offer_factory(componenti=[comp(0.10)]))
        delta = (float(run_sas(df, MONO_2700, potenza=potenza).iloc[0]["SAS"])
                 - float(run_sas(df, MONO_2700, potenza=potenza,
                                 calc_arera=arera_no_dispbt).iloc[0]["SAS"]))
        assert delta == pytest.approx(DISPBT_RES * IVA_EE, abs=0.02)

    def test_non_applicata_al_gas(self, offer_factory, make_df, run_sas, arera_no_dispbt):
        df = make_df(offer_factory(commodity="G", tipologia_fasce="",
                                   componenti=[{"prezzo": 0.35, "unita": "€/Smc",
                                                "fascia": ""}]))
        con = float(run_sas(df, GAS_1400, potenza=None, regione="Lombardia").iloc[0]["SAS"])
        senza = float(run_sas(df, GAS_1400, potenza=None, regione="Lombardia",
                              calc_arera=arera_no_dispbt).iloc[0]["SAS"])
        assert con == pytest.approx(senza, abs=0.01)

    def test_esposta_in_output(self, offer_factory, make_df, run_sas):
        df = make_df(offer_factory(componenti=[comp(0.10)]))
        res = run_sas(df, MONO_2700, residente=True)
        assert res.iloc[0]["DISPBT_APPLICATO"] == pytest.approx(DISPBT_RES, abs=0.01)


# ==============================================================================
# TestVariabile — riscritta sugli indici da configurazione
# ==============================================================================
class TestVariabile:

    @staticmethod
    def _var(offer_factory, codice_idx, spread=0.02, **kw):
        return offer_factory(tipo_offerta="Variabile", IDX_CODICE=codice_idx,
                             componenti=[comp(spread)], **kw)

    def test_indice_monorario_applicato_al_totale(self, offer_factory, make_df, sas_of):
        fisso = make_df(offer_factory(tipo_offerta="Fisso", componenti=[comp(0.02)]))
        var = make_df(self._var(offer_factory, "PUN_MONORARIO"))
        assert sas_of(var, BIO) - sas_of(fisso, BIO) == \
            pytest.approx(IDX_SYN["PUN_MONORARIO"] * 2700 * IVA_EE, abs=0.02)

    def test_indice_a_fasce_pesa_le_singole_fasce(self, offer_factory, make_df, sas_of):
        """Il punto centrale del fix: un indice a fasce non va applicato al
        consumo totale."""
        fisso = make_df(offer_factory(tipo_offerta="Fisso", componenti=[comp(0.02)]))
        var = make_df(self._var(offer_factory, "PUN_FASCE"))
        atteso = (0.120 * 891 + 0.090 * 837 + 0.070 * 972)   # 250.29
        assert atteso == pytest.approx(250.29, abs=0.01)
        assert sas_of(var, BIO) - sas_of(fisso, BIO) == pytest.approx(atteso * IVA_EE, abs=0.02)

    def test_indici_diversi_producono_sas_diverse(self, offer_factory, make_df, sas_of):
        """Ex test_indice_offerta_ignorato, non più known_bug."""
        a = make_df(self._var(offer_factory, "PUN_MONORARIO"))
        b = make_df(self._var(offer_factory, "PUN_FASCE"))
        assert sas_of(a, BIO) != pytest.approx(sas_of(b, BIO), abs=1.0)
        # 270.00 vs 250.29 di base indice
        assert sas_of(a, BIO) - sas_of(b, BIO) == \
            pytest.approx((270.0 - 250.29) * IVA_EE, abs=0.05)

    def test_alias_risolto(self, offer_factory, make_df, sas_of):
        canonico = make_df(self._var(offer_factory, "PUN_MONORARIO"))
        alias = make_df(self._var(offer_factory, "PUN"))
        assert sas_of(alias, BIO) == pytest.approx(sas_of(canonico, BIO), abs=0.01)

    def test_indice_letto_da_flag_booleani(self, offer_factory, make_df, sas_of):
        """Formato legacy del flattener: colonne IDX_<CODICE> booleane."""
        esplicito = make_df(self._var(offer_factory, "PSV_MENSILE", commodity="G",
                                      tipologia_fasce=""))
        flag = make_df(offer_factory(tipo_offerta="Variabile", commodity="G",
                                     tipologia_fasce="", IDX_PSV_MENSILE="true",
                                     componenti=[comp(0.02, unita="€/Smc", fascia="")]))
        assert sas_of(flag, GAS_1400, potenza=None) == \
            pytest.approx(sas_of(esplicito, GAS_1400, potenza=None), abs=0.05)

    def test_gas_indici_diversi(self, offer_factory, make_df, sas_of):
        m = make_df(self._var(offer_factory, "PSV_MENSILE", commodity="G",
                              tipologia_fasce="",
                              ))
        t = make_df(self._var(offer_factory, "PSV_TRIM", commodity="G",
                              tipologia_fasce=""))
        assert sas_of(t, GAS_1400, potenza=None) > sas_of(m, GAS_1400, potenza=None)

    def test_indice_soggetto_a_perdite(self, offer_factory, make_df, sas_of):
        consumi = {"F1": 1000, "F2": 0, "F3": 0}
        si = make_df(self._var(offer_factory, "PUN_MONORARIO", comprensivo_perdite="SI"))
        no = make_df(self._var(offer_factory, "PUN_MONORARIO", comprensivo_perdite="NO"))
        atteso = (0.02 + IDX_SYN["PUN_MONORARIO"]) * 1000 * 0.10 * IVA_EE
        assert sas_of(no, consumi) - sas_of(si, consumi) == pytest.approx(atteso, abs=0.02)

    def test_offerta_fissa_ignora_indice(self, offer_factory, make_df, sas_of):
        senza = make_df(offer_factory(tipo_offerta="Fisso", componenti=[comp(0.02)]))
        con = make_df(offer_factory(tipo_offerta="Fisso", IDX_CODICE="PUN_MONORARIO",
                                    componenti=[comp(0.02)]))
        assert sas_of(con, BIO) == pytest.approx(sas_of(senza, BIO), abs=0.01)

    def test_nessun_valore_hardcoded_residuo(self, offer_factory, make_df, sas_of):
        """Regressione: 0.105 e 0.35 non devono più comparire nel risultato."""
        fisso = make_df(offer_factory(tipo_offerta="Fisso", componenti=[comp(0.02)]))
        var = make_df(self._var(offer_factory, "PUN_MONORARIO"))
        delta_unitario = (sas_of(var, BIO) - sas_of(fisso, BIO)) / IVA_EE / 2700
        assert delta_unitario == pytest.approx(IDX_SYN["PUN_MONORARIO"], abs=1e-4)
        assert delta_unitario != pytest.approx(0.105, abs=1e-4)

    def test_indice_ignoto_strict_solleva(self, offer_factory, make_df, arera, indici):
        from engine.index_prices import UnknownIndexError
        from engine.sas_calculator_fast import FastSASCalculator
        df = make_df(self._var(offer_factory, "INDICE_INVENTATO"))
        calc = FastSASCalculator(df, arera=arera, indici=indici, strict=True)
        with pytest.raises(UnknownIndexError):
            calc.calculate_sas(df, consumi=BIO, potenza=3.0)


# ==============================================================================
# Fasce parziali: ex known_bug, ora requisito
# ==============================================================================
class TestFasceParziali:

    @pytest.mark.parametrize(
        "fascia,kwh_attesi",
        [("monorario/F1", 891), ("F2", 837), ("F3", 972),
         ("F2+F3", 1809), ("F1+F3", 1863), ("F1+F2", 1728)],
    )
    def test_componente_su_insieme_di_fasce(self, offer_factory, make_df,
                                            sas_of, fascia, kwh_attesi):
        base = make_df(offer_factory(componenti=[comp(0.10, fascia="monorario/F1")]))
        df = make_df(offer_factory(componenti=[
            comp(0.10, fascia="monorario/F1"), comp(0.05, fascia=fascia)]))
        assert sas_of(df, BIO) - sas_of(base, BIO) == \
            pytest.approx(0.05 * kwh_attesi * IVA_EE, abs=0.02)

    def test_f1_piu_f3_non_e_il_totale(self, offer_factory, make_df, sas_of):
        """Prima F1+F3 cadeva nel ramo else e veniva applicata a 2700 kWh
        anziché a 1863."""
        tot = make_df(offer_factory(componenti=[comp(0.10, fascia="")]))
        f13 = make_df(offer_factory(componenti=[comp(0.10, fascia="F1+F3")]))
        assert sas_of(f13, BIO) < sas_of(tot, BIO)
        assert sas_of(tot, BIO) - sas_of(f13, BIO) == \
            pytest.approx(0.10 * 837 * IVA_EE, abs=0.02)


# ==============================================================================
# Componenti percentuali: ex known_bug
# ==============================================================================
class TestComponentiPercentuali:

    def test_percentuale_su_indice_noto(self, offer_factory, make_df, sas_of):
        """'PUN + 5%' vale 0.05*PUN*consumo, non 5 €/anno."""
        base = make_df(offer_factory(tipo_offerta="Variabile",
                                     IDX_CODICE="PUN_MONORARIO",
                                     componenti=[comp(0.02)]))
        pct = make_df(offer_factory(tipo_offerta="Variabile",
                                    IDX_CODICE="PUN_MONORARIO",
                                    componenti=[comp(0.02),
                                                {"prezzo": 5.0, "unita": "Percentuale",
                                                 "fascia": ""}]))
        atteso = 0.05 * IDX_SYN["PUN_MONORARIO"] * 2700 * IVA_EE
        assert sas_of(pct, BIO) - sas_of(base, BIO) == pytest.approx(atteso, abs=0.05)

    def test_percentuale_non_sommata_come_euro(self, offer_factory, make_df, sas_of):
        base = make_df(offer_factory(tipo_offerta="Variabile",
                                     IDX_CODICE="PUN_MONORARIO",
                                     componenti=[comp(0.02)]))
        pct = make_df(offer_factory(tipo_offerta="Variabile",
                                    IDX_CODICE="PUN_MONORARIO",
                                    componenti=[comp(0.02),
                                                {"prezzo": 5.0, "unita": "Percentuale",
                                                 "fascia": ""}]))
        assert sas_of(pct, BIO) - sas_of(base, BIO) != pytest.approx(5.0 * IVA_EE, abs=0.5)

    def test_percentuale_su_offerta_fissa_diagnosticata(self, offer_factory,
                                                        make_df, run_sas):
        """Senza indice non c'è base a cui applicare la percentuale: la si
        segnala invece di sottoprezzare l'offerta."""
        df = make_df(offer_factory(tipo_offerta="Fisso", componenti=[
            comp(0.10), {"prezzo": 5.0, "unita": "Percentuale", "fascia": ""}]))
        res = run_sas(df, BIO)
        assert res.iloc[0]["DIAGNOSTICA"] == "COMP_PERCENTUALE_NON_RISOLTA"
Aggiungi anche in TestFilterOffers, togliendo i marker known_bug:

python
Copy
    def test_domestico_esclude_condominio(self, offer_factory, make_df, arera, indici):
        from engine.sas_calculator_fast import FastSASCalculator
        df = make_df(
            offer_factory(cod_offerta="DOM", commodity="G", tipo_cliente="Domestico"),
            offer_factory(cod_offerta="CON", commodity="G",
                          tipo_cliente="Condominio Uso Domestico (Gas)"),
        )
        out = FastSASCalculator(df, arera=arera, indici=indici).filter_offers(
            commodity="G", tipo_cliente="Domestico", fasce=None)
        assert set(out["COD_OFFERTA"]) == {"DOM"}

    def test_biorario_esclude_trioraria(self, offer_factory, make_df, arera, indici):
        from engine.sas_calculator_fast import FastSASCalculator
        df = make_df(
            offer_factory(cod_offerta="BIO", tipologia_fasce="biorario (F1 / F2+F3)"),
            offer_factory(cod_offerta="TRI", tipologia_fasce="F1, F2, F3"),
        )
        out = FastSASCalculator(df, arera=arera, indici=indici).filter_offers(
            fasce="Biorario")
        assert set(out["COD_OFFERTA"]) == {"BIO"}
8. tests/test_index_prices.py — nuovo
python
Copy
"""Unit test su IndexPriceProvider."""
from __future__ import annotations

import copy
from datetime import date

import pytest

from engine.index_prices import ALL, IndexPriceProvider, UnknownIndexError
from tests.conftest import IDX_SYN, build_synthetic_indices


@pytest.fixture
def payload():
    return build_synthetic_indices()


# --- Validazione ---
def test_file_mancante(write_indices):
    with pytest.raises(FileNotFoundError):
        IndexPriceProvider("percorso/inesistente.json")


def test_nessun_periodo(write_indices, payload):
    payload["periodi"] = []
    with pytest.raises(ValueError, match="nessun periodo"):
        IndexPriceProvider(write_indices(payload))


def test_periodi_sovrapposti(write_indices, payload):
    payload["periodi"].append(copy.deepcopy(payload["periodi"][0]))
    with pytest.raises(ValueError, match="sovrapposti"):
        IndexPriceProvider(write_indices(payload))


def test_all_non_coesiste_con_fasce(write_indices, payload):
    payload["periodi"][0]["indici"]["PUN_MONORARIO"]["valori"] = {"ALL": 0.1, "F1": 0.2}
    with pytest.raises(ValueError, match="non può coesistere"):
        IndexPriceProvider(write_indices(payload))


def test_valore_negativo(write_indices, payload):
    payload["periodi"][0]["indici"]["PUN_MONORARIO"]["valori"] = {"ALL": -0.1}
    with pytest.raises(ValueError, match="non valido"):
        IndexPriceProvider(write_indices(payload))


def test_fascia_ignota(write_indices, payload):
    payload["periodi"][0]["indici"]["PUN_FASCE"]["valori"]["F4"] = 0.1
    with pytest.raises(ValueError, match="chiavi ignote"):
        IndexPriceProvider(write_indices(payload))


def test_alias_rotto(write_indices, payload):
    payload["alias"]["PIPPO"] = "INDICE_INESISTENTE"
    with pytest.raises(ValueError, match="Alias"):
        IndexPriceProvider(write_indices(payload))


def test_commodity_mancante(write_indices, payload):
    del payload["periodi"][0]["indici"]["PUN_MONORARIO"]["commodity"]
    with pytest.raises(ValueError, match="commodity"):
        IndexPriceProvider(write_indices(payload))


def test_configurazione_scaduta_strict(write_indices):
    payload = build_synthetic_indices("2020-01-01", "2020-12-31")
    with pytest.raises(ValueError, match="non copre la data odierna"):
        IndexPriceProvider(write_indices(payload), strict=True)


def test_configurazione_scaduta_non_strict(write_indices):
    payload = build_synthetic_indices("2020-01-01", "2020-12-31")
    with pytest.warns(RuntimeWarning):
        IndexPriceProvider(write_indices(payload), strict=False)


# --- Risoluzione ---
def test_get_monorario(indici):
    assert indici.get("PUN_MONORARIO", "E") == {ALL: IDX_SYN["PUN_MONORARIO"]}


def test_per_fascia_espande_monorario(indici):
    assert indici.per_fascia("PUN_MONORARIO", "E") == \
        {b: IDX_SYN["PUN_MONORARIO"] for b in ("F1", "F2", "F3")}


def test_per_fascia_indice_a_fasce(indici):
    assert indici.per_fascia("PUN_FASCE", "E") == IDX_SYN["PUN_FASCE"]


@pytest.mark.parametrize("alias,canonico", [
    ("PUN", "PUN_MONORARIO"), ("pun", "PUN_MONORARIO"),
    ("PUN-F1", "PUN_FASCE"), ("psv trim", "PSV_TRIMESTRALE"),
])
def test_normalizzazione_e_alias(indici, alias, canonico):
    assert indici.get(alias, indici.periodi[0]["indici"][canonico]["commodity"]) == \
        indici.get(canonico, indici.periodi[0]["indici"][canonico]["commodity"])


def test_commodity_sbagliata_strict_solleva(indici):
    """Un indice gas su un'offerta elettrica è un errore di dati, non un caso
    da gestire silenziosamente."""
    with pytest.raises(UnknownIndexError):
        indici.get("PSV_MENSILE", "E")


def test_indice_ignoto_strict_solleva(indici):
    with pytest.raises(UnknownIndexError, match="Indici noti"):
        indici.get("INVENTATO", "E")


def test_indice_ignoto_non_strict_fallback(write_indices, payload):
    prov = IndexPriceProvider(write_indices(payload), strict=False)
    with pytest.warns(RuntimeWarning, match="Fallback"):
        assert prov.get("INVENTATO", "E") == {ALL: IDX_SYN["PUN_MONORARIO"]}


def test_indice_non_verificato_strict_solleva(write_indices, payload):
    payload["periodi"][0]["indici"]["PUN_MONORARIO"]["verificato"] = False
    prov = IndexPriceProvider(write_indices(payload), strict=True)
    with pytest.raises(UnknownIndexError, match="verificato=false"):
        prov.get("PUN_MONORARIO", "E")


def test_codice_vuoto_non_risolve(indici):
    for vuoto in ("", None, "nan", "None"):
        assert indici.resolve_code(vuoto, "E") is None


# --- Time Travel ---
def test_valore_dipende_dalla_data(write_indices):
    payload = build_synthetic_indices("2026-01-01", "2026-06-30")
    secondo = copy.deepcopy(payload["periodi"][0])
    secondo.update({"valid_from": "2026-07-01", "valid_to": "2099-12-31"})
    secondo["indici"]["PUN_MONORARIO"]["valori"] = {ALL: 0.200}
    payload["periodi"].append(secondo)
    prov = IndexPriceProvider(write_indices(payload), strict=True)
    assert prov.get("PUN_MONORARIO", "E", date(2026, 3, 15))[ALL] == pytest.approx(0.100)
    assert prov.get("PUN_MONORARIO", "E", date(2026, 8, 15))[ALL] == pytest.approx(0.200)


def test_data_non_coperta_solleva(write_indices):
    payload = build_synthetic_indices("2026-01-01", "2099-12-31")
    prov = IndexPriceProvider(write_indices(payload), strict=True)
    with pytest.raises(UnknownIndexError, match="Nessun periodo"):
        prov.get("PUN_MONORARIO", "E", date(2025, 6, 1))


# --- Configurazione di produzione ---
@pytest.mark.requires_data
def test_produzione_caricabile():
    """Con strict=False: in produzione gli indici non sono ancora verificati."""
    prov = IndexPriceProvider(strict=False)
    assert prov.codici_noti("E")
    assert prov.codici_noti("G")


@pytest.mark.requires_data
@pytest.mark.known_bug
def test_produzione_tutti_gli_indici_verificati():
    """Fallisce finché index_prices.json contiene voci con verificato=false.
    È il tracker del lavoro di popolamento da audit_indici.py."""
    prov = IndexPriceProvider(strict=False)
    periodo = prov._periodo(date.today())
    da_verificare = [c for c, s in periodo["indici"].items()
                     if not s.get("verificato", False)]
    assert not da_verificare, f"Indici non ancora verificati: {da_verificare}"
9. tests/test_flattener.py — i tre test aggiornati
I tre known_bug diventano requisiti sui campi canonici. Sostituisci test_fasce_multiorarie_parziali_gestite, test_percentuale_non_classificata_come_fisso, test_tipo_cliente_domestico_non_ambiguo e test_whitelist_monorario_senza_codici_grezzi con:

python
Copy
from parse import fasce as fz

# ==============================================================================
# Fasce parziali (ex known_bug)
# ==============================================================================
@pytest.mark.parametrize(
    "codice,bande_attese",
    [("01", "F1"), ("02", "F2"), ("03", "F3"),
     ("91", "F2|F3"), ("92", "F1|F3"), ("93", "F1|F2")],
)
def test_fascia_componente_risolta_su_offerta_multioraria(codice, bande_attese):
    label = DECODE_MAPS["FASCIA_COMPONENTE"][codice]
    assert fz.resolve_fascia_set(label, "biorario (F1 / F2+F3)") == bande_attese
    assert fz.resolve_fascia_set(codice, "biorario (F1 / F2+F3)") == bande_attese


def test_nessuna_fascia_cade_su_tot_implicito():
    """Regressione del ramo 'else -> prezzo * TOT_CONS'."""
    for codice, label in DECODE_MAPS["FASCIA_COMPONENTE"].items():
        got = fz.resolve_fascia_set(label, "biorario (F1 / F2+F3)")
        assert got not in (fz.TOT, fz.UNKNOWN), \
            f"FASCIA_COMPONENTE[{codice}]='{label}' non risolta: {got}"


def test_monorario_polisemia_del_codice_01():
    """01 = 'monorario/F1' vale l'intero consumo su offerta monoraria e la sola
    F1 su offerta multioraria."""
    assert fz.resolve_fascia_set("monorario/F1", "monorario/F1") == fz.TOT
    assert fz.resolve_fascia_set("monorario/F1", "biorario (F1 / F2+F3)") == "F1"


@pytest.mark.parametrize("fascia_set,atteso", [
    ("TOT", 2700), ("F1", 891), ("F2", 837), ("F3", 972),
    ("F2|F3", 1809), ("F1|F3", 1863), ("F1|F2", 1728),
])
def test_consumo_di_set(fascia_set, atteso):
    consumi = {"F1": 891, "F2": 837, "F3": 972}
    assert fz.consumo_di_set(fascia_set, consumi) == pytest.approx(atteso)


def test_fascia_ignota_non_degrada_su_tot():
    """Meglio SCONOSCIUTA (diagnosticabile) che TOT (errore silenzioso)."""
    assert fz.resolve_fascia_set("F9", "biorario (F1 / F2+F3)") == fz.UNKNOWN


# ==============================================================================
# Unità di misura (ex known_bug sulla percentuale)
# ==============================================================================
@pytest.mark.parametrize("codice,kind_atteso", [
    ("01", fz.KIND_FISSO), ("02", fz.KIND_POTENZA), ("03", fz.KIND_VOL_KWH),
    ("04", fz.KIND_VOL_SMC), ("05", fz.KIND_FISSO), ("06", fz.KIND_PERCENTUALE),
])
def test_unita_kind_per_codice(codice, kind_atteso):
    assert fz.unita_kind(codice) == kind_atteso
    assert fz.unita_kind(DECODE_MAPS["UNITA_MISURA"][codice]) == kind_atteso


def test_percentuale_ha_kind_dedicato():
    """Non deve più finire nel bucket FISSO ed essere sommata come euro/anno."""
    for codice, label in DECODE_MAPS["UNITA_MISURA"].items():
        if "ercentuale" in label or "%" in label:
            assert fz.unita_kind(label) == fz.KIND_PERCENTUALE
            assert fz.unita_kind(label) != fz.KIND_FISSO


def test_kwh_prevale_su_kw():
    assert fz.unita_kind("€/kWh") == fz.KIND_VOL_KWH
    assert fz.unita_kind("€/kW") == fz.KIND_POTENZA


def test_tutte_le_unita_hanno_kind():
    for codice, label in DECODE_MAPS["UNITA_MISURA"].items():
        assert fz.unita_kind(label) != fz.UNKNOWN, \
            f"UNITA_MISURA[{codice}]='{label}' non classificata"


# ==============================================================================
# Tipo cliente (ex known_bug)
# ==============================================================================
@pytest.mark.parametrize("codice", ["01", "02", "03"])
def test_tipo_cliente_code_roundtrip(codice):
    assert fz.tipo_cliente_code(DECODE_MAPS["TIPO_CLIENTE"][codice]) == codice
    assert fz.tipo_cliente_code(codice) == codice


def test_condominio_non_e_domestico():
    """Il filtro deve distinguere TIPO_CLIENTE 01 da 03, che con substring
    matching collassavano insieme."""
    dom = fz.tipo_cliente_code("Domestico")
    con = fz.tipo_cliente_code("Condominio Uso Domestico (Gas)")
    assert dom == "01" and con == "03" and dom != con


# ==============================================================================
# Struttura fasce: sostituisce is_vero_mono e la whitelist con '01'
# ==============================================================================
@pytest.mark.parametrize("codice,strutt_attesa", [
    ("01", "MONO"), ("03", "TRI"), ("91", "BI"), ("92", "BI"), ("93", "BI"),
])
def test_struttura_per_codice(codice, strutt_attesa):
    assert fz.struttura(codice) == strutt_attesa
    assert fz.struttura(DECODE_MAPS["TIPOLOGIA_FASCE"][codice]) == strutt_attesa


def test_ogni_tipologia_ha_struttura():
    for codice, label in DECODE_MAPS["TIPOLOGIA_FASCE"].items():
        assert fz.struttura(label) != fz.UNKNOWN, \
            f"TIPOLOGIA_FASCE[{codice}]='{label}' senza struttura"


@pytest.mark.known_bug
def test_tipologia_fasce_02_da_verificare():
    """TIPOLOGIA_FASCE '02' ha label 'F2' nel DECODE_MAPS: ambigua rispetto allo
    schema AU. Mappata BI in via prudenziale. Verificare sulla documentazione
    Acquirente Unico e rimuovere questo test."""
    assert fz.struttura_verificata("02"), \
        "Struttura del codice 02 non ancora confermata su fonte AU"


# ==============================================================================
# Integrazione: campi canonici scritti dal flattener
# ==============================================================================
@pytest.mark.skipif(not hasattr(flattener, "_add_canonical_fields"),
                    reason="patch canonica non applicata")
def test_add_canonical_fields_offerta_biorario():
    record = {
        "TIPOLOGIA_FASCE": "biorario (F1 / F2+F3)",
        "TIPO_CLIENTE": "Domestico",
        "COMP_IMP_1_INT_1_PREZZO": "0,13",
        "COMP_IMP_1_INT_1_UNITA": "€/kWh",
        "COMP_IMP_1_INT_1_FASCIA": "F1+F3",
    }
    out = flattener._add_canonical_fields(dict(record))
    assert out["FASCE_STRUTTURA"] == "BI"
    assert out["TIPO_CLIENTE_COD"] == "01"
    assert out["COMP_IMP_1_INT_1_FASCE_SET"] == "F1|F3"
    assert out["COMP_IMP_1_INT_1_UNITA_KIND"] == fz.KIND_VOL_KWH
    assert out["PREZZABILE"] is True
    assert out["COMP_NON_GESTITE"] is None


@pytest.mark.skipif(not hasattr(flattener, "_add_canonical_fields"),
                    reason="patch canonica non applicata")
def test_add_canonical_fields_marca_percentuale():
    record = {
        "TIPOLOGIA_FASCE": "monorario/F1",
        "TIPO_CLIENTE": "Domestico",
        "COMP_IMP_1_INT_1_PREZZO": "5",
        "COMP_IMP_1_INT_1_UNITA": "Percentuale",
        "COMP_IMP_1_INT_1_FASCIA": "",
    }
    out = flattener._add_canonical_fields(dict(record))
    assert out["PREZZABILE"] is False
    assert "PERCENTUALE" in out["COMP_NON_GESTITE"]
10. Esecuzione
bash
Copy
# Suite unit, senza dati di produzione
pytest -m "not requires_data and not golden"

# Tracker del debito residuo (deve elencare 2 voci, non più 6)
pytest -m known_bug -v

# Popolamento della configurazione indici dai dati reali
python scripts/audit_indici.py --parquet data/processed/storico_2026_full.parquet
Stato dei known_bug
Test	Stato
test_filtro_biorario_intercetta_trioraria	risolto → rinominato test_biorario_esclude_trioraria
test_domestico_non_deve_includere_condominio	risolto
test_regione_stringa_None_trattata_come_nazionale	risolto
test_indice_offerta_ignorato	risolto → TestVariabile
test_unita_percentuale_non_sommata_come_euro	risolto
test_fasce_multiorarie_parziali_gestite	risolto
test_accisa_gas_differenzia_nord_sud	risolto (accise da GAS_ACCISE)
test_prezzo_illeggibile_non_deve_essere_silenzioso	risolto (_num logga)
test_produzione_tutti_gli_indici_verificati	aperto — dipende da audit_indici.py
test_tipologia_fasce_02_da_verificare	aperto — richiede fonte AU
Punti che richiedono una decisione, non codice
DispBT e potenza. L'assunzione "solo residenza" è codificata e testata. Va confermata su delibera prima del golden run, altrimenti tutti i casi ≥3.5 kW residenti sono sbagliati di 11.85 €.
Codici indice reali. index_prices.json eredita 0.105 e 0.35 come valori di partenza con verificato=false. Finché non passa audit_indici.py, il comportamento è identico a prima ma tracciato. Con strict=True il calcolo si blocca — consigliato in CI, non in dashboard.
Offerte Mista (TIPO_OFFERTA 04). Non modellate: la quota indicizzata è ignorata, la SAS è sottostimata. Oggi vengono loggate. Da decidere se escluderle dal ranking come le non prezzabili.
Doppio conteggio dello spread. Se una Variabile pubblica in COMP_IMP il prezzo pieno anziché il solo spread, ora l'indice si somma sopra. La colonna INDICE_APPLICATO in output serve esattamente a intercettarlo: verificare su 5-10 offerte reali prima di considerare il punto chiuso.
TIPOLOGIA_FASCE = '02'. La label F2 nel dizionario attuale non è coerente con una struttura di fatturazione. Sospetto un errore di trascrizione da correggere alla fonte in flattener.py.