"""Fixture condivise per la suite PO_scraping_2026.

Principio guida:
- I test aritmetici usano tariffe SINTETICHE (valori tondi, iniettate via
  dependency injection) → asserzioni esatte, indipendenti dal trimestre.
- I test golden usano le tariffe REALI di data/config/arera_tariffs.json,
  altrimenti il confronto con il Portale Offerte non ha senso.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REAL_TARIFFS = PROJECT_ROOT / "data" / "config" / "arera_tariffs.json"
HISTORICAL_PARQUET = PROJECT_ROOT / "data" / "processed" / "storico_2026_full.parquet"

OPEN = 9_999_999  # limite ultimo scaglione


# ==============================================================================
# Tariffe sintetiche
# ==============================================================================
def build_synthetic_tariffs(quarter: str, year: int) -> dict:
    """Tariffe con valori tondi, scelte per rendere l'aritmetica verificabile
    a mano. NON sono valori regolatori reali."""
    gas_vol_tiers = [[120, 0.20], [480, 0.18], [1560, 0.16], [OPEN, 0.15]]
    zone = ["Nord Occidentale", "Nord Orientale", "Centrale",
            "Centro-Sud Orientale", "Centro-Sud Occidentale", "Meridionale"]

    return {
        "metadata": {
            "validity_quarter": quarter,
            "validity_year": year,
            "source": "SYNTHETIC — test fixture, non usare in produzione",
        },
        "ELE": {
            "residente": {
                "dist_fix": 20.0, "oneri_fix": 0.0,
                "trasp_pot": 10.0, "oneri_pot": 0.0,
                "trasp_vol": 0.010, "oneri_vol": 0.020,
                "cdispd": 0.0150,
            },
            "non_residente": {
                "dist_fix": 30.0, "oneri_fix": 0.0,
                "trasp_pot": 12.0, "oneri_pot": 0.0,
                "trasp_vol": 0.010, "oneri_vol": 0.030,
                "cdispd": 0.0150,
            },
        },
        # Identiche su tutte le zone: così i test Nord vs Sud isolano
        # esclusivamente l'effetto dell'accisa.
        "GAS_FIX": {z: 60.0 for z in zone},
        "GAS_VOL": {z: gas_vol_tiers for z in zone},
        # Aliquote accisa gas uso civile REALI (le uniche non sintetiche:
        # servono a dimostrare la divergenza Nord/Sud).
        "GAS_ACCISE": {
            "Nord": [[120, 0.044], [480, 0.175], [1560, 0.170], [OPEN, 0.186]],
            "Sud":  [[120, 0.038], [480, 0.135], [1560, 0.120], [OPEN, 0.150]],
        },
        # Volutamente uguali per Lombardia/Sicilia/Campania: idem come sopra.
        "GAS_ADDIZIONALE": {
            "Lombardia": 0.031, "Sicilia": 0.031, "Campania": 0.031,
            "Lazio": 0.031, "DEFAULT": 0.019,
        },
        # Parametri di stima sintetici: DispBT a zero per non sporcare
        # l'aritmetica dei test; accisa e IVA ai valori normativi.
        "PARAMETRI": {
            "pun_stima": 0.105,
            "psv_stima": 0.35,
            "dispbt": 0.0,
            "accisa_ee": 0.0227,
            "accisa_ee_franchigia": 1800,
            "iva_ee": 0.10,
            "iva_gas_soglie": [[480, 0.10], [OPEN, 0.22]],
            "perdite_rete_ee": 0.10,
        },
    }


def pytest_collection_modifyitems(config, items):
    """known_bug → xfail(strict=True): il test diventa rosso quando il bug
    viene risolto, ricordando di rimuovere il marker."""
    for item in items:
        if item.get_closest_marker("known_bug"):
            item.add_marker(pytest.mark.xfail(strict=True,
                                              reason="known_bug: divergenza nota"))


@pytest.fixture(scope="session")
def current_quarter() -> tuple[str, int]:
    now = datetime.now()
    return f"Q{(now.month - 1) // 3 + 1}", now.year


@pytest.fixture(scope="session")
def synthetic_tariffs_dict(current_quarter) -> dict:
    return build_synthetic_tariffs(*current_quarter)


@pytest.fixture(scope="session")
def synthetic_tariffs_path(tmp_path_factory, synthetic_tariffs_dict) -> str:
    p = tmp_path_factory.mktemp("arera") / "arera_tariffs.json"
    p.write_text(json.dumps(synthetic_tariffs_dict), encoding="utf-8")
    return str(p)


@pytest.fixture
def arera(synthetic_tariffs_path):
    from engine.arera_tariffs import AreraTariffs
    return AreraTariffs(synthetic_tariffs_path)


@pytest.fixture
def write_tariffs(tmp_path):
    """Scrive un JSON tariffe arbitrario e ne restituisce il path."""
    def _write(payload: dict, name: str = "arera_tariffs.json") -> str:
        p = tmp_path / name
        p.write_text(json.dumps(payload), encoding="utf-8")
        return str(p)
    return _write


@pytest.fixture(scope="session")
def arera_real():
    from engine.arera_tariffs import AreraTariffs
    if not REAL_TARIFFS.exists():
        pytest.skip(f"Tariffe di produzione non trovate: {REAL_TARIFFS}")
    return AreraTariffs(str(REAL_TARIFFS))


# ==============================================================================
# Factory offerte sintetiche
# ==============================================================================
PROFILO_BIORARIO_ARERA = {"F1": 891, "F2": 837, "F3": 972}   # 2700 kWh
PROFILO_ENGIE = {"F1": 693, "F2": 651, "F3": 756}            # 2100 kWh


def make_offer(
    commodity: str = "E",
    tipo_offerta: str = "Fisso",
    tipo_cliente: str = "Domestico",
    tipologia_fasce: str = "biorario (F1 / F2+F3)",
    nome_offerta: str = "Offerta Test",
    piva: str = "11475730154",
    cod_offerta: str = "TEST001",
    comprensivo_perdite: str = "SI",
    regione: str | None = None,
    provincia: str | None = None,
    comune: str | None = None,
    cdispd: float | None = None,
    componenti: list[dict] | None = None,
    sconti: list[dict] | None = None,
    **overrides,
) -> dict:
    """Costruisce una riga-offerta con i soli campi letti dal calcolatore.

    componenti: [{"prezzo":0.13,"unita":"€/kWh","fascia":"monorario/F1",
                  "validita":""}, ...]  → mappati su COMP_IMP_{n}_INT_1
    sconti:     [{"nome":"...","cond_app":"Pagamento SDD","codice_comp":"",
                  "validita":"Sempre",
                  "prezzi":[{"tipo":"Sconto fisso","val":24.0,"unita":"€/Anno"}]}]
    """
    row = {
        "commodity": commodity,
        "TIPO_OFFERTA": tipo_offerta,
        "TIPO_CLIENTE": tipo_cliente,
        "TIPOLOGIA_FASCE": tipologia_fasce,
        "NOME_OFFERTA": nome_offerta,
        "PIVA_UTENTE": piva,
        "COD_OFFERTA": cod_offerta,
        "PREZZO_COMPRENSIVO_PERDITE_RETE": comprensivo_perdite,
        "REGIONE": regione,
        "PROVINCIA": provincia,
        "COMUNE": comune,
        "DISP_CdispD_VALORE": np.nan if cdispd is None else cdispd,
        "COND_Attivazione_LIMITANTE": None,
        "COND_Pluriennale_LIMITANTE": None,
    }

    for idx, comp in enumerate(componenti or [], start=1):
        if idx > 15:
            raise ValueError("Massimo 15 ComponenteImpresa")
        row[f"COMP_IMP_{idx}_INT_1_PREZZO"] = comp["prezzo"]
        row[f"COMP_IMP_{idx}_INT_1_UNITA"] = comp.get("unita", "€/kWh")
        row[f"COMP_IMP_{idx}_INT_1_FASCIA"] = comp.get("fascia", "")
        row[f"COMP_IMP_{idx}_INT_1_VALIDITA"] = comp.get("validita", "")

    for s, sc in enumerate(sconti or [], start=1):
        if s > 15:
            raise ValueError("Massimo 15 Sconti")
        row[f"SCONTO_{s}_NOME"] = sc.get("nome", f"Sconto {s}")
        row[f"SCONTO_{s}_COND_APP"] = sc.get("cond_app", "")
        row[f"SCONTO_{s}_CODICE_COMP"] = sc.get("codice_comp", "")
        row[f"SCONTO_{s}_VALIDITA"] = sc.get("validita", "Sempre")
        row[f"SCONTO_{s}_IVA"] = sc.get("iva", "SI")
        row[f"SCONTO_{s}_DURATA"] = sc.get("durata")
        for p, pr in enumerate(sc.get("prezzi", []), start=1):
            if p > 5:
                raise ValueError("Massimo 5 PrezziSconto per sconto")
            row[f"SCONTO_{s}_PREZZO_{p}_TIPO"] = pr.get("tipo", "Sconto fisso")
            row[f"SCONTO_{s}_PREZZO_{p}_VAL"] = pr["val"]
            row[f"SCONTO_{s}_PREZZO_{p}_UNITA"] = pr.get("unita", "€/Anno")
            row[f"SCONTO_{s}_PREZZO_{p}_DA"] = pr.get("da", "0")
            row[f"SCONTO_{s}_PREZZO_{p}_FINO"] = pr.get("fino", "0")

    row.update(overrides)
    return row


@pytest.fixture
def offer_factory():
    return make_offer


@pytest.fixture
def make_df():
    def _make(*rows: dict) -> pd.DataFrame:
        return pd.DataFrame(list(rows))
    return _make


@pytest.fixture
def run_sas(arera):
    """Esegue il calcolo SAS su un DataFrame e restituisce il risultato."""
    from engine.sas_calculator_fast import FastSASCalculator

    def _run(df: pd.DataFrame, consumi: dict, potenza: float = 3.0, **kwargs):
        calc = FastSASCalculator(df, arera=arera)
        return calc.calculate_sas(df, consumi=consumi, potenza=potenza, **kwargs)
    return _run


@pytest.fixture
def sas_of(run_sas):
    """Scorciatoia: SAS della prima (e unica) offerta del DataFrame."""
    def _sas(df: pd.DataFrame, consumi: dict, potenza: float = 3.0, **kwargs):
        res = run_sas(df, consumi, potenza, **kwargs)
        assert len(res) == 1, f"Attesa 1 riga, ottenute {len(res)}"
        return float(res.iloc[0]["SAS"])
    return _sas


# ==============================================================================
# Dati di produzione (golden)
# ==============================================================================
@pytest.fixture(scope="session")
def historical_parquet() -> str:
    if not HISTORICAL_PARQUET.exists():
        pytest.skip(f"Parquet storico non trovato: {HISTORICAL_PARQUET}")
    return str(HISTORICAL_PARQUET)
