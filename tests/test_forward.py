"""Stime delle offerte variabili con le regole del Portale (engine.forward)."""
import json
from datetime import date

import pytest

from download import gme
from engine import forward
from engine.sas_calculator_fast import FastSASCalculator

OGGI = date(2026, 10, 2)
CCR_PORTALE = {"2026-Q4": 0.025212, "2027-Q1": 0.025212, "2027-Q2": 0.027267, "2027-Q3": 0.027267}


def test_periodo_di_stima():
    assert forward.trimestri(OGGI) == [(2026, 4), (2027, 1), (2027, 2), (2027, 3)]
    assert forward.mesi(date(2026, 5, 15))[0] == (2026, 4)  # esempio delle Regole
    assert forward.mese_rilevazione(OGGI) == (2026, 9)
    assert forward.mese_rilevazione(date(2027, 1, 10)) == (2026, 12)


def test_profilo_gas_allineato_al_periodo():
    p = forward.profilo_gas("Lombardia", OGGI)
    assert sum(p) == pytest.approx(1)
    gennaio = forward.profilo_gas("Lombardia", date(2027, 1, 5))
    assert gennaio[0] == pytest.approx(p[3])  # il periodo parte da gennaio


def test_ccr_come_dettaglio_portale():
    # CHIARISSIMA-like, Milano 1.400 Smc del 01/10/2026: CCR in vendita 35,79 €
    trim = forward.ccr_trimestri({"ccr": CCR_PORTALE}, OGGI)
    ccr = forward.pesa_trimestri(trim, forward.profilo_gas("Lombardia", OGGI))
    assert ccr * 1400 == pytest.approx(35.79, abs=0.01)
    assert forward.ccr_trimestri({"ccr": {"2026-Q4": 0.02}}, OGGI) is None


def _sessione(root, mercato, giorno, prezzi):
    p = gme.path_sessione(mercato, giorno, root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(prezzi), encoding="utf-8")


def test_stima_dalle_sessioni_gme(tmp_path):
    ee = {f"{prof}-Q-{a}-{q:02d}": v for prof, base in (("BL", 100.0), ("PL", 120.0))
          for (a, q), v in zip(forward.trimestri(OGGI), (base, base + 20, base - 20, base))}
    gas = {"M-2026-10": 30.0, "M-2026-11": 40.0, "M-2026-12": 50.0,
           "Q-2027-01": 60.0, "Q-2027-02": 20.0, "Q-2027-03": 10.0}
    for g, k in ((date(2026, 9, 1), 1.0), (date(2026, 9, 2), 3.0)):  # media delle sessioni
        _sessione(tmp_path, "mte", g, {p: v * k / 2 for p, v in ee.items()})
        _sessione(tmp_path, "mtgas", g, {p: v * k / 2 for p, v in gas.items()})
    s = forward.stima(OGGI, root=tmp_path)
    assert s["ee"]["F0"] == pytest.approx(0.100)
    assert s["ee"]["F1"] == pytest.approx(0.120)
    assert s["ee"]["F23"] < s["ee"]["F0"] < s["ee"]["F1"]
    assert s["gas_mesi"][0] == pytest.approx(30.0 * forward.KWH_PER_SMC / 1000)
    assert s["gas_mesi"][3:6] == [pytest.approx(60.0 * forward.KWH_PER_SMC / 1000)] * 3
    assert forward.stima(date(2026, 12, 1), root=tmp_path) is None  # niente sessioni a novembre


def test_luce_variabile_perdite_solo_sul_forward(offer_factory, make_df, arera):
    # Regole: (media forward x (1+lambda) + spread) x consumo; spread già con le perdite
    df = make_df(offer_factory(
        tipo_offerta="Variabile", tipologia_fasce="Monorario", comprensivo_perdite="NO",
        componenti=[{"prezzo": 72.0, "unita": "€/Anno"},
                    {"prezzo": 0.0077, "unita": "€/kWh", "fascia": "F0"}],
        IDX_PUN_Men=True, IDX_PUN_Men_COEFF="1"))
    calc = FastSASCalculator(df, arera=arera)
    calc.forward = {"ee": {"F0": 0.169898, "F1": 0.18, "F23": 0.16}, "gas_mesi": [0.8] * 12}
    res = calc.calculate_sas(df, consumi={"F1": 2700, "F2": 0, "F3": 0}, potenza=3)
    cdispd = arera.ELE["residente"]["cdispd"]
    attesa = 72 + 2700 * (0.169898 * 1.1 + 0.0077 + cdispd)
    assert float(res.iloc[0]["SPESA_MATERIA_PRIMA"]) == pytest.approx(attesa, abs=0.01)


def test_coefficiente_indici(offer_factory, make_df):
    import pandas as pd
    df = make_df(offer_factory(IDX_PUN_Men=True, IDX_PUN_Men_COEFF="0,5",
                               IDX_TTF_Men=True, IDX_TTF_Men_COEFF=None),
                 offer_factory(IDX_PUN_Men=False))
    assert list(FastSASCalculator._coefficiente_indici(pd.DataFrame(df))) == [1.5, 1.0]
