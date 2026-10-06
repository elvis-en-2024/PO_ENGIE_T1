"""Offerta simulata: stessa SAS di un'offerta reale equivalente e prezzo obiettivo coerente."""
import pandas as pd
import pytest

from engine import offerta_simulata as osim
from engine.sas_calculator_fast import FastSASCalculator

CONS = {"F1": 2700, "F2": 0, "F3": 0}


def _concorrenti(offer_factory, make_df):
    return make_df(*[offer_factory(cod_offerta=f"C{i}", tipologia_fasce="monorario/F1",
                                   componenti=[{"prezzo": 60.0 + 10 * i, "unita": "€/Anno"},
                                               {"prezzo": 0.10 + 0.01 * i, "unita": "€/kWh",
                                                "fascia": "monorario/F1"}])
                     for i in range(5)])


def test_stessa_sas_di_un_offerta_reale(offer_factory, make_df, arera):
    reale = make_df(offer_factory(tipologia_fasce="monorario/F1", componenti=[
        {"prezzo": 96.0, "unita": "€/Anno"}, {"prezzo": 0.14, "unita": "€/kWh", "fascia": "monorario/F1"}],
        sconti=[{"nome": "Benvenuto", "cond_app": "Non condizionato", "validita": "Ingresso",
                 "prezzi": [{"val": 30.0, "unita": "€/Anno"}]}]))
    nuova = osim.NuovaOfferta(quota_fissa=96.0, prezzi={"F0": 0.14},
                              sconti=[osim.Sconto("Benvenuto", 30.0)])
    calc = FastSASCalculator(reale, arera=arera)
    attesa = calc.calculate_sas(reale, consumi=CONS, potenza=3)["SAS"].iloc[0]
    sim = calc.calculate_sas(pd.DataFrame([nuova.riga()]), consumi=CONS, potenza=3)
    assert sim["SAS"].iloc[0] == pytest.approx(attesa)
    assert sim["SCONTI"].iloc[0] == pytest.approx(-30.0)


def test_prezzo_obiettivo_porta_in_prima_posizione(offer_factory, make_df, arera):
    conc = _concorrenti(offer_factory, make_df)
    calc = FastSASCalculator(conc, arera=arera)
    nuova = osim.NuovaOfferta(quota_fissa=100.0, prezzi={"F0": 0.16})
    esito = osim.posiziona(calc, conc, nuova, consumi=CONS, potenza=3)
    assert esito["posizione"] == 6 and esito["totale"] == 6
    d = esito["obiettivi"][1]["d_energia"]
    assert d < 0
    migliorata = osim.posiziona(calc, conc, nuova.con_variazione(d_energia=d), consumi=CONS, potenza=3)
    assert migliorata["posizione"] == 1


def test_composizione_somma_alla_sas(offer_factory, make_df, arera):
    conc = _concorrenti(offer_factory, make_df)
    res = FastSASCalculator(conc, arera=arera).calculate_sas(conc, consumi=CONS, potenza=3)
    somma = res[["VENDITA", "SCONTI", "RETE", "ONERI", "IMPOSTE", "IVA", "SCONTI_NO_IVA"]].sum(axis=1)
    assert (somma - res["SAS"]).abs().max() < 0.03
