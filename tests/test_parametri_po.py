from datetime import date

import pytest

from engine import parametri_po as pp

PAR_E = {"acc_c_r_l": 0.0227, "acc_c_r_h": 0.0227, "acc_c_nr": 0.0227,
         "sigma1": 23.04, "sigma2": 23.52, "sigma3": 0.0119, "uc3": 0.00276,
         "uc6s_d": 0.1988, "uc6p_d": 0.00007, "asos_dr": 0.031515, "arim_dr": 0.001638,
         "asos_dnr_f": 95.0916, "arim_dnr_f": 0.0, "asos_dnr_v": 0.031515,
         "arim_dnr_v": 0.001638}


@pytest.mark.parametrize("annuo,tassati", [
    (1800, 0),                    # 150 kWh/mese: esente
    (2400, (200 - 150) * 12),     # tra 150 e 220
    (2700, (2 * 225 - 370) * 12), # tra 220 e 370: esenzione decrescente
    (4800, 4800),                 # oltre 370: tutto tassato
])
def test_accisa_residente_3kw_soglie_mensili(annuo, tassati):
    assert pp.accisa_ele(PAR_E, annuo, 3, True) == pytest.approx(0.0227 * tassati)


def test_accisa_sopra_3kw_e_non_residente_su_tutto():
    assert pp.accisa_ele(PAR_E, 1800, 4.5, True) == pytest.approx(0.0227 * 1800)
    assert pp.accisa_ele(PAR_E, 1800, 3, False) == pytest.approx(0.0227 * 1800)


def test_regolati_non_residente_quota_fissa_asos():
    diff = pp.regolati_ele(PAR_E, 2700, 3, False) - pp.regolati_ele(PAR_E, 2700, 3, True)
    accise = pp.accisa_ele(PAR_E, 2700, 3, False) - pp.accisa_ele(PAR_E, 2700, 3, True)
    assert diff == pytest.approx(95.0916 + accise)


def test_a_scaglioni_progressivo():
    aliquote = [1, 2, 3, 4, 5, 6]
    # 120*1 + 360*2 + 520*3
    assert pp.a_scaglioni(1000, aliquote) == pytest.approx(120 + 720 + 1560)
    assert pp.a_scaglioni(0, aliquote) == 0


def test_carica_ultimo_file_entro_data(tmp_path):
    d = tmp_path / "E" / "2026"
    d.mkdir(parents=True)
    for g, v in (("20260930", "1"), ("20261001", "2"), ("20261005", "3")):
        (d / f"PO_Parametri_Mercato_Libero_E_{g}.csv").write_text(
            f"nome_parametro,valore,descrizione\nx,{v},prova\n", encoding="utf-8")
    par = pp.carica("E", date(2026, 10, 3), root=tmp_path)
    assert par["x"] == 2 and par["_data"] == date(2026, 10, 1)
    assert pp.carica("G", date(2026, 10, 3), root=tmp_path) is None


PAR_DISP = {"msd": 0.004663, "modeol": 0.001096, "uniess": 0.003322, "terna": 0.000717,
            "interr": 0.001079, "capprod": 0.0, "cpty_mrkt_1": 0.003765,
            "cpty_mrkt_2": 0.003765, "cpty_mrkt_3": 0.010167, "cdispd": 0.016776,
            "dispbt_d": 1.107}


def test_cdispd_uguale_a_tide_piu_capacity_market():
    # coerenza dei parametri del Portale osservata sui risultati del 01/10/2026
    assert pp.disp_kwh(PAR_DISP, "TIDE") + pp.disp_kwh(PAR_DISP, "Capacita_STG") == \
        pytest.approx(PAR_DISP["cdispd"], abs=1e-6)


def test_dispacciamento_voci_dichiarate():
    import numpy as np
    si, no = np.array([True, False]), np.array([False, False])
    nan = np.array([np.nan, np.nan])
    voci = {"TIDE": (si, nan), "Altro": (si, np.array([0.003, 0.003])), "CdispD": (no, nan)}
    tot = pp.dispacciamento_ele(PAR_DISP, 1000, voci, dispbt=si)
    assert tot[0] == pytest.approx(1.107 + (0.010877 + 0.003) * 1000)
    assert tot[1] == 0


def test_ambito_gas_regione_sconosciuta():
    with pytest.raises(KeyError):
        pp.ambito_gas("Atlantide")
