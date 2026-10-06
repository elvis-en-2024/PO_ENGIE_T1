"""Gas: riproduzione del dettaglio offerta del Portale Offerte.

Caso reale del 01/10/2026: CHIARISSIMA FIX PERTE (Segnoverde), Milano,
1400 Smc, contatore G6. Dettaglio del Portale: vendita 818,00; rete 364,39;
oneri 74,57; sconto una tantum -20,00; imposte 224,68; IVA 10% 42,64;
IVA 22% 227,75; spesa annua 1.732,03 €.
"""
import pytest

from engine import parametri_po as pp
from engine.sas_calculator_fast import FastSASCalculator

APERTO = 9_999_999

# Parametri del Portale del 01/10/2026 necessari per l'ambito Nord-Orientale
PAR_G = {
    "tau1_cc1_a2": 69.60, "st_a2": -0.35, "vr_a2": -0.01, "ug2s": -21.63,
    "qt": 0.105049, "ug1": 0.034837, "ug3": 0.007292, "re": 0.029417,
    "rs": 0.002788, "gs": 0.003907,
    "tau3_f1_a2": 0.0, "tau3_f2_a2": 0.079367, "tau3_f3_a2": 0.072643,
    "tau3_f4_a2": 0.072949, "tau3_f5_a2": 0.054508, "tau3_f6_a2": 0.027610,
    "ug2p_d_f1": 0.0, "ug2p_d_f2": 0.0496, "ug2p_d_f3": 0.0293,
    "ug2p_d_f4": 0.0237, "ug2p_d_f5": 0.017, "ug2p_d_f6": 0.0071,
    "qvd_f_d": 55.39, "qvd_v_d": 0.007946, "cpr": 0.0, "grad": 0.0,
    "iva_f1": 0.10, "iva_f2": 0.10, "iva_f3": 0.22, "iva_f4": 0.22, "iva_ui": 0.22,
}
IMPOSTE_LOMBARDIA = {
    "accisa": [[120, 0.044], [480, 0.175], [1560, 0.17], [APERTO, 0.186]],
    "addizionale": [],
}


def test_rete_e_oneri_senza_bonus_gs():
    # rete 364,39 + oneri 74,57 del dettaglio offerta
    assert pp.regolati_gas(PAR_G, "Lombardia", 1400) == pytest.approx(364.39 + 74.57, abs=0.01)


def test_importo_tiers_accisa():
    assert pp.importo_tiers(IMPOSTE_LOMBARDIA["accisa"], 1400) == pytest.approx(224.68)
    assert pp.importo_tiers([], 1400) == 0


def test_sas_come_dettaglio_portale(offer_factory, make_df, arera):
    df = make_df(offer_factory(
        commodity="G", tipologia_fasce="", regione="03",
        componenti=[{"prezzo": 159.99996, "unita": "€/Anno"},
                    {"prezzo": 0.47, "unita": "€/Smc"}],
        sconti=[{"nome": "Sconto Corrispettivo Gestione Triennale",
                 "cond_app": "Non condizionato", "validita": "Ingresso",
                 "prezzi": [{"val": 20.0, "unita": "€/Anno"}]}],
    ))
    calc = FastSASCalculator(df, arera=arera, parametri={"G": PAR_G})
    calc.imposte_gas = {"Lombardia": IMPOSTE_LOMBARDIA}
    res = calc.calculate_sas(df, consumi={"F1": 1400, "F2": 0, "F3": 0}, potenza=None,
                             regione="Lombardia")
    assert float(res.iloc[0]["SAS"]) == pytest.approx(1732.03, abs=0.02)
