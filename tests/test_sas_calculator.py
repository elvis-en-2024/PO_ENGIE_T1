"""Test del FastSASCalculator: filtri, aritmetica, sconti, golden dataset."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from engine.sas_calculator_fast import FastSASCalculator
from tests.conftest import PROFILO_BIORARIO_ARERA, make_offer
from tests.golden_loader import case_ids, is_true, load_golden_cases, to_float

BIO = PROFILO_BIORARIO_ARERA          # F1=891 F2=837 F3=972 → 2700
MONO_2700 = {"F1": 2700, "F2": 0, "F3": 0}
GAS_1400 = {"F1": 1400, "F2": 0, "F3": 0}

QF = {"prezzo": 0.0, "unita": "€/Anno", "fascia": ""}   # template quota fissa


def comp(prezzo, unita="€/kWh", fascia="monorario/F1"):
    return {"prezzo": prezzo, "unita": unita, "fascia": fascia}


# ==============================================================================
# filter_offers
# ==============================================================================
class TestFilterOffers:

    @pytest.fixture
    def offer_factory(self):
        """Offerte con un prezzo energia di default: senza, filter_offers le
        scarta (giustamente) come 'prezzo_energia_assente'."""
        def _make(**kw):
            kw.setdefault("componenti", [comp(0.10)])
            return make_offer(**kw)
        return _make

    def test_esclude_sottocosto(self, offer_factory, make_df, arera):
        df = make_df(
            offer_factory(cod_offerta="A", nome_offerta="Offerta Luce"),
            offer_factory(cod_offerta="B", nome_offerta="Luce Sottocosto Web"),
        )
        out = FastSASCalculator(df, arera=arera).filter_offers()
        assert set(out["COD_OFFERTA"]) == {"A"}

    def test_tiene_offerte_nazionali_e_di_regione(self, offer_factory, make_df, arera):
        df = make_df(
            offer_factory(cod_offerta="NAZ", regione=None),
            offer_factory(cod_offerta="LOM", regione="03"),
            offer_factory(cod_offerta="PIE", regione="01"),
        )
        out = FastSASCalculator(df, arera=arera).filter_offers(regione="Lombardia")
        assert set(out["COD_OFFERTA"]) == {"NAZ", "LOM"}

    def test_offerta_multizona_inclusa_in_ogni_sua_regione(self, offer_factory,
                                                           make_df, arera):
        df = make_df(
            offer_factory(cod_offerta="PIE_LIG", regione="01|07"),
            offer_factory(cod_offerta="LOM", regione="03"),
        )
        calc = FastSASCalculator(df, arera=arera)
        assert set(calc.filter_offers(regione="Liguria", provincia=None)["COD_OFFERTA"]) == {"PIE_LIG"}
        assert set(calc.filter_offers(regione="Lombardia", provincia=None)["COD_OFFERTA"]) == {"LOM"}

    def test_sette_componenti_tutte_nel_calcolo(self, offer_factory, make_df, sas_of):
        uno = make_df(offer_factory(componenti=[comp(0.07)]))
        sette = make_df(offer_factory(componenti=[comp(0.01)] * 7))
        assert sas_of(sette, MONO_2700) == pytest.approx(sas_of(uno, MONO_2700), abs=0.01)

    def test_scaglione_scelto_sul_consumo_annuo(self, offer_factory, make_df, sas_of):
        """Due intervalli della stessa componente: si applica solo quello
        che contiene il consumo annuo."""
        scaglioni = make_df(offer_factory(
            componenti=[comp(0.10)],
            COMP_IMP_1_INT_1_CONSUMO_DA="0", COMP_IMP_1_INT_1_CONSUMO_A="2000",
            COMP_IMP_1_INT_2_PREZZO=0.20, COMP_IMP_1_INT_2_UNITA="€/kWh",
            COMP_IMP_1_INT_2_FASCIA="monorario/F1",
            COMP_IMP_1_INT_2_CONSUMO_DA="2001", COMP_IMP_1_INT_2_CONSUMO_A="99999",
        ))
        piatta = make_df(offer_factory(componenti=[comp(0.20)]))
        assert sas_of(scaglioni, MONO_2700) == pytest.approx(sas_of(piatta, MONO_2700), abs=0.01)

    def test_fascia_f1_piu_f2_sul_consumo_f1_f2(self, offer_factory, make_df, sas_of):
        consumi = {"F1": 1000, "F2": 800, "F3": 900}
        df = make_df(offer_factory(tipologia_fasce="biorario (F3 / F1+F2)",
                                   componenti=[comp(0.0)]))
        base = sas_of(df, consumi)
        df = make_df(offer_factory(tipologia_fasce="biorario (F3 / F1+F2)",
                                   componenti=[comp(0.10, fascia="F1+F2")]))
        assert sas_of(df, consumi) - base == pytest.approx(0.10 * 1800 * 1.10, abs=0.05)

    def test_limiti_consumo_e_potenza_dichiarati(self, offer_factory, make_df, arera):
        from engine.sas_calculator_fast import FastSASCalculator
        df = make_df(
            offer_factory(cod_offerta="LIBERA", componenti=[comp(0.10)]),
            offer_factory(cod_offerta="FINO1500", componenti=[comp(0.10)],
                          CONSUMO_MIN="1000", CONSUMO_MAX="1500"),
            offer_factory(cod_offerta="DA4KW", componenti=[comp(0.10)], POTENZA_MIN="4.5"),
            offer_factory(cod_offerta="NONRES", componenti=[comp(0.10)],
                          DOMESTICO_RESIDENTE="NON Residente"),
        )
        calc = FastSASCalculator(df, arera=arera)
        f = calc.filter_offers(commodity="E", fasce="Tutte", regione="Lombardia",
                               consumo_annuo=2700, potenza=3, residente=True)
        assert sorted(f["COD_OFFERTA"]) == ["LIBERA"]
        f = calc.filter_offers(commodity="E", fasce="Tutte", regione="Lombardia",
                               consumo_annuo=1500, potenza=6, residente=False)
        assert sorted(f["COD_OFFERTA"]) == ["DA4KW", "FINO1500", "LIBERA", "NONRES"]

    def test_filtro_monorario(self, offer_factory, make_df, arera):
        df = make_df(
            offer_factory(cod_offerta="M", tipologia_fasce="monorario/F1"),
            offer_factory(cod_offerta="B", tipologia_fasce="biorario (F1 / F2+F3)"),
        )
        out = FastSASCalculator(df, arera=arera).filter_offers(fasce="Monorario")
        assert set(out["COD_OFFERTA"]) == {"M"}

    def test_filtro_biorario_esclude_trioraria(self, offer_factory, make_df, arera):
        df = make_df(
            offer_factory(cod_offerta="BIO", tipologia_fasce="biorario (F1 / F2+F3)"),
            offer_factory(cod_offerta="TRI", tipologia_fasce="F1, F2, F3"),
        )
        out = FastSASCalculator(df, arera=arera).filter_offers(fasce="Biorario")
        assert set(out["COD_OFFERTA"]) == {"BIO"}, \
            "L'offerta trioraria non deve entrare nel ranking biorario"

    def test_domestico_non_deve_includere_condominio(self, offer_factory, make_df, arera):
        """Il match per token non deve far rientrare
        'Condominio Uso Domestico (Gas)' (TIPO_CLIENTE 03) in 'Domestico'."""
        df = make_df(
            offer_factory(cod_offerta="DOM", commodity="G", tipo_cliente="Domestico"),
            offer_factory(cod_offerta="CON", commodity="G",
                          tipo_cliente="Condominio Uso Domestico (Gas)"),
        )
        out = FastSASCalculator(df, arera=arera).filter_offers(
            commodity="G", tipo_cliente="Domestico", fasce=None
        )
        assert set(out["COD_OFFERTA"]) == {"DOM"}

    def test_dataframe_vuoto_non_crasha(self, offer_factory, make_df, arera):
        df = make_df(offer_factory())
        out = FastSASCalculator(df, arera=arera).filter_offers(commodity="G")
        assert out.empty
        assert FastSASCalculator(df, arera=arera).calculate_sas(
            out, consumi=BIO, potenza=3.0
        ).empty


# ==============================================================================
# Componenti di prezzo — elettrico
# ==============================================================================
class TestElettricoAritmetica:

    def test_caso_base_biorario_residente_3kw(self, offer_factory, make_df, sas_of):
        """
        Componenti: QF 96 €/anno; F1 0.13, F2 0.12, F3 0.11 €/kWh
        costo_fix = 96.00
        costo_vol = 0.13*891 + 0.12*837 + 0.11*972      = 323.19
                  + cdispd 0.0150*2700                   =  40.50  -> 363.69
        reti      = 20 + 0 + (10+0)*3 + (0.010+0.020)*2700 = 131.00
        accisa    = 0.0227 * (2700 - 1800)                =  20.43
        imponibile= 459.69 + 131.00 + 20.43               = 611.12
        SAS       = 611.12 * 1.10                         = 672.23
        """
        df = make_df(offer_factory(componenti=[
            {"prezzo": 96.0, "unita": "€/Anno", "fascia": ""},
            comp(0.13, fascia="monorario/F1"),
            comp(0.12, fascia="F2"),
            comp(0.11, fascia="F3"),
        ]))
        assert sas_of(df, BIO, potenza=3.0, residente=True) == pytest.approx(672.23, abs=0.01)

    def test_caso_monorario_non_residente_4_5kw(self, offer_factory, make_df, sas_of):
        """
        TIPOLOGIA_FASCE monorario → il prezzo F1 si applica al consumo TOTALE.
        costo_fix = 120.00
        costo_vol = 0.125*2700 + 0.0150*2700 = 337.50 + 40.50 = 378.00
        reti      = 30 + 12*4.5 + (0.010+0.030)*2700 = 30 + 54 + 108 = 192.00
        accisa    = 0.0227 * 2700 (nessuna esenzione) = 61.29
        SAS       = (498.00 + 192.00 + 61.29) * 1.10  = 826.42
        """
        df = make_df(offer_factory(
            tipologia_fasce="monorario/F1",
            componenti=[
                {"prezzo": 120.0, "unita": "€/Anno", "fascia": ""},
                comp(0.125, fascia="monorario/F1"),
            ],
        ))
        assert sas_of(df, BIO, potenza=4.5, residente=False) == pytest.approx(826.42, abs=0.01)

    def test_biorario_applica_f1_solo_a_f1(self, offer_factory, make_df, sas_of):
        """Stesso prezzo, stessa TIPOLOGIA biorario: la componente
        'monorario/F1' va moltiplicata per F1, non per il totale."""
        base = dict(componenti=[comp(0.10, fascia="monorario/F1")])
        mono = make_df(offer_factory(tipologia_fasce="monorario/F1", **base))
        bio = make_df(offer_factory(tipologia_fasce="biorario (F1 / F2+F3)", **base))
        delta = sas_of(mono, BIO) - sas_of(bio, BIO)
        assert delta == pytest.approx(0.10 * (837 + 972) * 1.10, abs=0.02)

    def test_fascia_f2_piu_f3_aggregata(self, offer_factory, make_df, sas_of):
        df_agg = make_df(offer_factory(componenti=[comp(0.12, fascia="F2+F3")]))
        df_sep = make_df(offer_factory(componenti=[
            comp(0.12, fascia="F2"), comp(0.12, fascia="F3"),
        ]))
        assert sas_of(df_agg, BIO) == pytest.approx(sas_of(df_sep, BIO), abs=0.01)

    def test_componente_euro_per_kw(self, offer_factory, make_df, sas_of):
        df3 = make_df(offer_factory(componenti=[{"prezzo": 6.0, "unita": "€/kW", "fascia": ""}]))
        s3 = sas_of(df3, MONO_2700, potenza=3.0, residente=False)
        s6 = sas_of(df3, MONO_2700, potenza=6.0, residente=False)
        assert s6 - s3 == pytest.approx((6.0 * 3 + 12.0 * 3) * 1.10, abs=0.02)

    @pytest.mark.parametrize("unita", ["€/Anno", "€"])
    def test_componenti_fisse(self, offer_factory, make_df, sas_of, unita):
        df0 = make_df(offer_factory(componenti=[comp(0.10)]))
        dfq = make_df(offer_factory(componenti=[
            comp(0.10), {"prezzo": 50.0, "unita": unita, "fascia": ""},
        ]))
        assert sas_of(dfq, MONO_2700) - sas_of(df0, MONO_2700) == \
               pytest.approx(50.0 * 1.10, abs=0.01)

    # --- Accisa elettrica ---
    def test_esenzione_1800_kwh_residente_fino_3kw(self, offer_factory, make_df, sas_of):
        df = make_df(offer_factory(componenti=[comp(0.10)]))
        consumi = {"F1": 1500, "F2": 0, "F3": 0}
        atteso_senza_accisa = (
            0.10 * 1500 + 0.0150 * 1500 + (20 + 30 + 0.03 * 1500)
        ) * 1.10
        assert sas_of(df, consumi, potenza=3.0, residente=True) == \
               pytest.approx(atteso_senza_accisa, abs=0.02)

    def test_nessuna_esenzione_sopra_3kw(self, offer_factory, make_df, sas_of):
        df = make_df(offer_factory(componenti=[comp(0.10)]))
        s3 = sas_of(df, MONO_2700, potenza=3.0, residente=True)
        s35 = sas_of(df, MONO_2700, potenza=3.5, residente=True)
        delta_accisa = 0.0227 * 1800
        delta_potenza = 10.0 * 0.5
        assert s35 - s3 == pytest.approx((delta_accisa + delta_potenza) * 1.10, abs=0.02)

    # --- Perdite di rete ---
    def test_perdite_di_rete_uplift_10pct(self, offer_factory, make_df, sas_of):
        kw = dict(componenti=[comp(0.10)])
        df_si = make_df(offer_factory(comprensivo_perdite="SI", **kw))
        df_no = make_df(offer_factory(comprensivo_perdite="NO", **kw))
        consumi = {"F1": 1000, "F2": 0, "F3": 0}
        assert sas_of(df_no, consumi) - sas_of(df_si, consumi) == \
               pytest.approx(0.10 * 1000 * 0.10 * 1.10, abs=0.01)

    def test_perdite_non_si_applicano_alle_quote_fisse(self, offer_factory, make_df, sas_of):
        kw = dict(componenti=[{"prezzo": 100.0, "unita": "€/Anno", "fascia": ""}])
        df_si = make_df(offer_factory(comprensivo_perdite="SI", **kw))
        df_no = make_df(offer_factory(comprensivo_perdite="NO", **kw))
        assert sas_of(df_si, MONO_2700) == pytest.approx(sas_of(df_no, MONO_2700), abs=0.01)

    def test_perdite_gas_non_applicate(self, offer_factory, make_df, sas_of):
        kw = dict(commodity="G", tipologia_fasce="",
                  componenti=[{"prezzo": 0.35, "unita": "€/Smc", "fascia": ""}])
        df_si = make_df(offer_factory(comprensivo_perdite="SI", **kw))
        df_no = make_df(offer_factory(comprensivo_perdite="NO", **kw))
        assert sas_of(df_si, GAS_1400) == pytest.approx(sas_of(df_no, GAS_1400), abs=0.01)

    # --- CdispD ---
    def test_cdispd_da_offerta_sovrascrive_default(self, offer_factory, make_df, sas_of):
        kw = dict(componenti=[comp(0.10)])
        df_def = make_df(offer_factory(cdispd=None, **kw))
        df_off = make_df(offer_factory(cdispd=0.0250, **kw))
        assert sas_of(df_off, MONO_2700) - sas_of(df_def, MONO_2700) == \
               pytest.approx((0.0250 - 0.0150) * 2700 * 1.10, abs=0.02)

    def test_cdispd_decimale_con_virgola(self, offer_factory, make_df, sas_of):
        kw = dict(componenti=[comp(0.10)])
        df_virgola = make_df(offer_factory(cdispd="0,0250", **kw))
        df_punto = make_df(offer_factory(cdispd=0.0250, **kw))
        assert sas_of(df_virgola, MONO_2700) == \
               pytest.approx(sas_of(df_punto, MONO_2700), abs=0.01)


# ==============================================================================
# Offerte variabili / indicizzate
# ==============================================================================
class TestVariabile:

    def test_pun_da_configurazione(self, offer_factory, make_df, sas_of):
        """Il PUN di stima viene da PARAMETRI.pun_stima (0.105 nelle tariffe
        sintetiche)."""
        kw = dict(componenti=[comp(0.02)])
        fisso = make_df(offer_factory(tipo_offerta="Fisso", **kw))
        var = make_df(offer_factory(tipo_offerta="Variabile", **kw))
        consumi = {"F1": 1000, "F2": 0, "F3": 0}
        assert sas_of(var, consumi) - sas_of(fisso, consumi) == \
               pytest.approx(0.105 * 1000 * 1.10, abs=0.01)

    def test_psv_gas_da_configurazione(self, offer_factory, make_df, sas_of):
        """PSV di stima da PARAMETRI.psv_stima (0.35); IVA gas media su
        1400 Smc = (480*10% + 920*22%) / 1400."""
        kw = dict(commodity="G", tipologia_fasce="",
                  componenti=[{"prezzo": 0.02, "unita": "€/Smc", "fascia": ""}])
        fisso = make_df(offer_factory(tipo_offerta="Fisso", **kw))
        var = make_df(offer_factory(tipo_offerta="Variabile", **kw))
        iva = (480 * 0.10 + 920 * 0.22) / 1400
        assert sas_of(var, GAS_1400) - sas_of(fisso, GAS_1400) == \
               pytest.approx(0.35 * 1400 * (1 + iva), abs=0.02)

    @pytest.mark.known_bug
    def test_indice_offerta_ignorato(self, offer_factory, make_df, sas_of):
        """BUG: i campi IDX_* estratti dal flattener non entrano nel calcolo."""
        kw = dict(tipo_offerta="Variabile", componenti=[comp(0.02)])
        df_pun = make_df(offer_factory(IDX_TIPO="PUN", **kw))
        df_altro = make_df(offer_factory(IDX_TIPO="PSV_TRIM", **kw))
        assert sas_of(df_pun, MONO_2700) != sas_of(df_altro, MONO_2700)


# ==============================================================================
# Gas
# ==============================================================================
class TestGas:

    def test_caso_base_lombardia_1400_smc(self, offer_factory, make_df, sas_of):
        df = make_df(offer_factory(
            commodity="G", tipologia_fasce="",
            componenti=[
                {"prezzo": 100.0, "unita": "€/Anno", "fascia": ""},
                {"prezzo": 0.35, "unita": "€/Smc", "fascia": ""},
            ],
        ))
        assert sas_of(df, GAS_1400, potenza=None, regione="Lombardia") == \
               pytest.approx(1360.50, abs=0.02)

    def test_accisa_gas_differenzia_nord_sud(self, offer_factory, make_df, sas_of):
        """L'accisa gas dipende dal territorio (GAS_ACCISE Nord/Sud)."""
        df = make_df(offer_factory(
            commodity="G", tipologia_fasce="",
            componenti=[{"prezzo": 0.35, "unita": "€/Smc", "fascia": ""}],
        ))
        nord = sas_of(df, GAS_1400, potenza=None, regione="Lombardia")
        sud = sas_of(df, GAS_1400, potenza=None, regione="Sicilia")
        assert nord - sud > 60.0, "L'accisa del Mezzogiorno è più bassa"

    def test_potenza_none_non_crasha(self, offer_factory, make_df, sas_of):
        df = make_df(offer_factory(
            commodity="G", tipologia_fasce="",
            componenti=[{"prezzo": 0.35, "unita": "€/Smc", "fascia": ""}],
        ))
        assert sas_of(df, GAS_1400, potenza=None, regione="Lombardia") > 0


# ==============================================================================
# Sconti
# ==============================================================================
class TestSconti:

    @staticmethod
    def _offerta_con_sconto(offer_factory, **sconto):
        return offer_factory(
            componenti=[comp(0.10)],
            sconti=[sconto],
        )

    def test_sconto_sdd_solo_con_domiciliazione(self, offer_factory, make_df, sas_of):
        df = make_df(self._offerta_con_sconto(
            offer_factory,
            nome="Sconto SDD", cond_app="Pagamento SDD", validita="Sempre",
            prezzi=[{"tipo": "Sconto fisso", "val": 24.0, "unita": "€/Anno"}],
        ))
        senza = sas_of(df, MONO_2700, is_domiciliazione=False)
        con = sas_of(df, MONO_2700, is_domiciliazione=True)
        assert senza - con == pytest.approx(24.0 * 1.10, abs=0.01)

    def test_sconto_dual_fuel_solo_con_dual(self, offer_factory, make_df, sas_of):
        df = make_df(self._offerta_con_sconto(
            offer_factory,
            nome="Sconto Doppia Fornitura", cond_app="Altro", validita="Sempre",
            prezzi=[{"tipo": "Sconto fisso", "val": 30.0, "unita": "€/Anno"}],
        ))
        senza = sas_of(df, MONO_2700, is_dual_fuel=False)
        con = sas_of(df, MONO_2700, is_dual_fuel=True)
        assert senza - con == pytest.approx(30.0 * 1.10, abs=0.01)

    def test_sconto_incondizionato_sempre_applicato(self, offer_factory, make_df, sas_of):
        base = make_df(offer_factory(componenti=[comp(0.10)]))
        scontata = make_df(self._offerta_con_sconto(
            offer_factory,
            nome="Sconto Benvenuto", cond_app="", validita="Ingresso",
            prezzi=[{"tipo": "Sconto fisso", "val": 40.0, "unita": "€/Anno"}],
        ))
        assert sas_of(base, MONO_2700) - sas_of(scontata, MONO_2700) == \
               pytest.approx(40.0 * 1.10, abs=0.01)

    @pytest.mark.parametrize("validita", ["Ingresso", "entro 12 mesi", "Sempre", ""])
    def test_validita_ammesse(self, offer_factory, make_df, sas_of, validita):
        base = make_df(offer_factory(componenti=[comp(0.10)]))
        df = make_df(self._offerta_con_sconto(
            offer_factory, nome="S", cond_app="", validita=validita,
            prezzi=[{"tipo": "Sconto fisso", "val": 10.0, "unita": "€/Anno"}],
        ))
        assert sas_of(df, MONO_2700) < sas_of(base, MONO_2700)

    @pytest.mark.parametrize("validita", ["oltre 12 mesi", "dopo 24 mesi"])
    def test_validita_escluse(self, offer_factory, make_df, sas_of, validita):
        base = make_df(offer_factory(componenti=[comp(0.10)]))
        df = make_df(self._offerta_con_sconto(
            offer_factory, nome="S", cond_app="", validita=validita,
            prezzi=[{"tipo": "Sconto fisso", "val": 10.0, "unita": "€/Anno"}],
        ))
        assert sas_of(df, MONO_2700) == pytest.approx(sas_of(base, MONO_2700), abs=0.01)

    @pytest.mark.parametrize(
        "codice_comp,kwh_attesi",
        [("F1", 891), ("F2", 837), ("F3", 972), ("F2+F3", 1809), ("", 2700)],
    )
    def test_sconto_volumetrico_per_fascia(self, offer_factory, make_df, sas_of,
                                           codice_comp, kwh_attesi):
        base = make_df(offer_factory(componenti=[
            comp(0.10, fascia="monorario/F1"), comp(0.10, fascia="F2"),
            comp(0.10, fascia="F3"),
        ]))
        df = make_df(offer_factory(
            componenti=[comp(0.10, fascia="monorario/F1"), comp(0.10, fascia="F2"),
                        comp(0.10, fascia="F3")],
            sconti=[{
                "nome": "Sconto energia", "cond_app": "", "codice_comp": codice_comp,
                "validita": "Sempre",
                "prezzi": [{"tipo": "Sconto", "val": 0.01, "unita": "€/kWh"}],
            }],
        ))
        assert sas_of(base, BIO) - sas_of(df, BIO) == \
               pytest.approx(0.01 * kwh_attesi * 1.10, abs=0.02)

    def test_sconto_iva_no_sottratto_dopo_iva(self, offer_factory, make_df, sas_of):
        base = make_df(offer_factory(componenti=[comp(0.10)]))
        df = make_df(self._offerta_con_sconto(
            offer_factory, nome="Bonus", cond_app="", validita="Ingresso", iva="NO",
            prezzi=[{"tipo": "Sconto fisso", "val": 70.0, "unita": "€/Anno"}],
        ))
        assert sas_of(base, MONO_2700) - sas_of(df, MONO_2700) == pytest.approx(70.0, abs=0.01)

    def test_sconto_kwh_limitato_allo_scaglione(self, offer_factory, make_df, sas_of):
        # "Sconto sui primi 840 kWh/a": VALIDO_DA=0, VALIDO_FINO=840
        base = make_df(offer_factory(componenti=[comp(0.10)]))
        df = make_df(self._offerta_con_sconto(
            offer_factory, nome="Primi 840", cond_app="", validita="entro 12 mesi",
            prezzi=[{"tipo": "Sconto", "val": 0.05, "unita": "€/kWh", "da": "0",
                     "fino": "840"}],
        ))
        assert sas_of(base, MONO_2700) - sas_of(df, MONO_2700) == \
               pytest.approx(0.05 * 840 * 1.10, abs=0.01)

    @pytest.mark.parametrize("durata,mesi", [("3", 3), ("12", 12), ("30", 12), (None, 12)])
    def test_sconto_per_durata_in_mesi(self, offer_factory, make_df, sas_of, durata, mesi):
        base = make_df(offer_factory(componenti=[comp(0.10)]))
        df = make_df(self._offerta_con_sconto(
            offer_factory, nome="Primi mesi", cond_app="", validita="entro 12 mesi",
            durata=durata, prezzi=[{"tipo": "Sconto Vendita", "val": 0.06, "unita": "€/kWh"}],
        ))
        assert sas_of(base, MONO_2700) - sas_of(df, MONO_2700) == \
               pytest.approx(0.06 * 2700 * mesi / 12 * 1.10, abs=0.01)

    def test_sconto_bolletta_web_solo_se_richiesta(self, offer_factory, make_df, sas_of):
        df = make_df(self._offerta_con_sconto(
            offer_factory, nome="Bolletta web", cond_app="Fatturazione elettronica",
            validita="Sempre",
            prezzi=[{"tipo": "Sconto fisso", "val": 12.0, "unita": "€/Anno"}],
        ))
        senza = sas_of(df, MONO_2700)
        con = sas_of(df, MONO_2700, is_bolletta_web=True)
        assert senza - con == pytest.approx(12.0 * 1.10, abs=0.01)

    def test_sconto_percentuale_su_energia(self, offer_factory, make_df, sas_of):
        base = make_df(offer_factory(componenti=[comp(0.10)]))
        df = make_df(self._offerta_con_sconto(
            offer_factory, nome="-30%", cond_app="", validita="Ingresso",
            prezzi=[{"tipo": "Sconto Vendita", "val": 30.0, "unita": "Percentuale"}],
        ))
        assert sas_of(base, MONO_2700) - sas_of(df, MONO_2700) == \
               pytest.approx(0.30 * 0.10 * 2700 * 1.10, abs=0.01)


# ==============================================================================
# Robustezza e contratto di output
# ==============================================================================
class TestRobustezza:

    def test_colonne_output(self, offer_factory, make_df, run_sas):
        df = make_df(offer_factory(componenti=[comp(0.10)]))
        res = run_sas(df, MONO_2700)
        assert list(res.columns)[:7] == [
            "PIVA_VENDITORE", "COD_OFFERTA", "NOME_OFFERTA",
            "SPESA_MATERIA_PRIMA", "QUOTA_FISSA", "PREZZO_UNITARIO", "SAS",
        ]

    def test_ordinamento_per_sas_crescente(self, offer_factory, make_df, run_sas):
        df = make_df(
            offer_factory(cod_offerta="CARA", componenti=[comp(0.20)]),
            offer_factory(cod_offerta="ECON", componenti=[comp(0.08)]),
            offer_factory(cod_offerta="MEDIA", componenti=[comp(0.14)]),
        )
        res = run_sas(df, MONO_2700)
        assert list(res["COD_OFFERTA"]) == ["ECON", "MEDIA", "CARA"]
        assert res["SAS"].is_monotonic_increasing

    def test_prezzo_con_virgola_decimale(self, offer_factory, make_df, sas_of):
        df_v = make_df(offer_factory(componenti=[{"prezzo": "0,10", "unita": "€/kWh",
                                                  "fascia": "monorario/F1"}]))
        df_p = make_df(offer_factory(componenti=[comp(0.10)]))
        assert sas_of(df_v, MONO_2700) == pytest.approx(sas_of(df_p, MONO_2700), abs=0.01)

    def test_prezzo_non_numerico_non_crasha(self, offer_factory, make_df, sas_of):
        df = make_df(offer_factory(componenti=[
            comp(0.10), {"prezzo": "N.D.", "unita": "€/kWh", "fascia": "F2"},
        ]))
        assert sas_of(df, BIO) > 0

    def test_consumo_zero_non_solleva(self, offer_factory, make_df, run_sas):
        df = make_df(offer_factory(componenti=[comp(0.10)]))
        res = run_sas(df, {"F1": 0, "F2": 0, "F3": 0})
        assert len(res) == 1
        assert res.iloc[0]["PREZZO_UNITARIO"] == 0.0


# ==============================================================================
# Golden dataset — confronto con il Portale Offerte
# ==============================================================================
GOLDEN_CASES = load_golden_cases()


def _load_offerta(parquet_path: str, piva: str, cod: str, commodity: str,
                  data_rif: str) -> pd.DataFrame:
    import duckdb
    cols = set(duckdb.query(
        f"DESCRIBE SELECT * FROM read_parquet('{parquet_path}')").df()["column_name"])
    col_piva = "PIVA_UTENTE" if "PIVA_UTENTE" in cols else "PIVA_VENDITORE"
    col_cod = "CODICE_OFFERTA" if "CODICE_OFFERTA" in cols else "COD_OFFERTA"
    q = f"""
        SELECT * FROM read_parquet('{parquet_path}')
        WHERE {col_piva} = ? AND {col_cod} = ? AND commodity = ?
          AND try_strptime(split_part(DATA_INIZIO, '_', 1), '%d/%m/%Y') <= ?::DATE
        ORDER BY try_strptime(split_part(DATA_INIZIO, '_', 1), '%d/%m/%Y') DESC NULLS LAST
        LIMIT 1
    """
    return duckdb.execute(q, [piva, cod, commodity, data_rif]).df()


@pytest.mark.golden
@pytest.mark.requires_data
@pytest.mark.skipif(not GOLDEN_CASES, reason="golden dataset vuoto o assente")
@pytest.mark.parametrize("case", GOLDEN_CASES, ids=case_ids(GOLDEN_CASES))
def test_golden_sas(case, historical_parquet, arera_real):
    if not is_true(case["verificato"]):
        pytest.skip(f"{case['case_id']}: valore PO non ancora verificato")

    sas_atteso = to_float(case["sas_atteso"])
    if sas_atteso is None:
        pytest.skip(f"{case['case_id']}: sas_atteso non compilato")

    df = _load_offerta(historical_parquet, case["piva_venditore"],
                       case["cod_offerta"], case["commodity"],
                       case["data_riferimento"])
    if df.empty:
        pytest.fail(
            f"{case['case_id']}: offerta {case['piva_venditore']}/"
            f"{case['cod_offerta']} non trovata alla data {case['data_riferimento']}"
        )

    consumi = {f: to_float(case[f"consumo_{f.lower()}"], 0.0) for f in ("F1", "F2", "F3")}
    calc = FastSASCalculator(df, arera=arera_real)
    res = calc.calculate_sas(
        df,
        consumi=consumi,
        potenza=to_float(case["potenza_kw"]),
        is_dual_fuel=is_true(case["is_dual_fuel"]),
        is_domiciliazione=is_true(case["is_domiciliazione"]),
        regione=case["regione"],
        residente=is_true(case["residente"]),
    )
    sas_calcolato = float(res.iloc[0]["SAS"])
    tolleranza = to_float(case["tolleranza_pct"], 1.0) / 100.0
    scostamento = abs(sas_calcolato - sas_atteso) / sas_atteso

    assert scostamento <= tolleranza, (
        f"{case['case_id']} [{case['scenario']}]\n"
        f"  atteso (PO):  {sas_atteso:>10.2f} €\n"
        f"  calcolato:    {sas_calcolato:>10.2f} €\n"
        f"  scostamento:  {scostamento * 100:>10.2f} % (tolleranza "
        f"{tolleranza * 100:.2f} %)\n"
        f"  materia prima: {res.iloc[0]['SPESA_MATERIA_PRIMA']:.2f} € | "
        f"quota fissa: {res.iloc[0]['QUOTA_FISSA']:.2f} €"
    )
