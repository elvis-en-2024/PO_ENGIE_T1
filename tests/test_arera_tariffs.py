"""Unit test su AreraTariffs: validazione, zone, scaglioni."""
from __future__ import annotations

import copy

import pytest
from freezegun import freeze_time

from engine.arera_tariffs import (
    ACCISA_TERRITORIO_BY_REGIONE,
    GAS_ZONE_BY_REGIONE,
    AreraTariffs,
    UnknownRegionError,
    _norm_regione,
)
from tests.conftest import build_synthetic_tariffs

REGIONI_ITALIANE = [
    "Piemonte", "Valle d'Aosta", "Lombardia", "Trentino-Alto Adige", "Veneto",
    "Friuli-Venezia Giulia", "Liguria", "Emilia-Romagna", "Toscana", "Umbria",
    "Marche", "Lazio", "Abruzzo", "Molise", "Campania", "Puglia", "Basilicata",
    "Calabria", "Sicilia", "Sardegna",
]

ZONE_VALIDE = {
    "Nord Occidentale", "Nord Orientale", "Centrale",
    "Centro-Sud Orientale", "Centro-Sud Occidentale", "Meridionale",
}


# ==============================================================================
# Validazione file di configurazione
# ==============================================================================
def test_file_mancante_solleva():
    with pytest.raises(FileNotFoundError):
        AreraTariffs("percorso/che/non/esiste.json")


@freeze_time("2026-08-25")
def test_tariffe_obsolete_hard_stop(write_tariffs):
    payload = build_synthetic_tariffs("Q1", 2026)   # ma siamo in Q3
    with pytest.raises(ValueError, match="obsolete"):
        AreraTariffs(write_tariffs(payload))


@freeze_time("2026-08-25")
def test_tariffe_correnti_ok(write_tariffs):
    payload = build_synthetic_tariffs("Q3", 2026)
    assert AreraTariffs(write_tariffs(payload)).metadata["validity_quarter"] == "Q3"


@freeze_time("2026-04-03")
def test_grace_period_solo_warning(write_tariffs, caplog):
    """Nei primi 5 giorni del trimestre le tariffe scadute passano con warning."""
    payload = build_synthetic_tariffs("Q1", 2026)
    AreraTariffs(write_tariffs(payload))     # non deve sollevare
    assert "GRACE PERIOD" in caplog.text


@freeze_time("2026-04-10")
def test_oltre_grace_period_solleva(write_tariffs):
    payload = build_synthetic_tariffs("Q1", 2026)
    with pytest.raises(ValueError):
        AreraTariffs(write_tariffs(payload))


@pytest.mark.parametrize("tipo", ["residente", "non_residente"])
def test_blocco_ele_mancante_solleva(write_tariffs, synthetic_tariffs_dict, tipo):
    payload = copy.deepcopy(synthetic_tariffs_dict)
    del payload["ELE"][tipo]
    with pytest.raises(ValueError, match=tipo):
        AreraTariffs(write_tariffs(payload))


@pytest.mark.parametrize(
    "chiave",
    ["dist_fix", "oneri_fix", "trasp_pot", "oneri_pot",
     "trasp_vol", "oneri_vol", "cdispd"],
)
def test_parametro_ele_negativo_solleva(write_tariffs, synthetic_tariffs_dict, chiave):
    payload = copy.deepcopy(synthetic_tariffs_dict)
    payload["ELE"]["residente"][chiave] = -1.0
    with pytest.raises(ValueError, match=chiave):
        AreraTariffs(write_tariffs(payload))


def test_ultimo_scaglione_chiuso_solleva(write_tariffs, synthetic_tariffs_dict):
    """Un ultimo scaglione con limite finito perde silenziosamente il volume
    residuo: la validazione deve intercettarlo."""
    payload = copy.deepcopy(synthetic_tariffs_dict)
    payload["GAS_VOL"]["Nord Occidentale"] = [[120, 0.20], [480, 0.18], [1560, 0.16]]
    with pytest.raises(ValueError, match="ultimo scaglione"):
        AreraTariffs(write_tariffs(payload))


def test_scaglioni_non_ordinati_solleva(write_tariffs, synthetic_tariffs_dict):
    payload = copy.deepcopy(synthetic_tariffs_dict)
    payload["GAS_ACCISE"]["Nord"] = [[480, 0.175], [120, 0.044], [9_999_999, 0.186]]
    with pytest.raises(ValueError, match="non ordinati"):
        AreraTariffs(write_tariffs(payload))


# ==============================================================================
# Mappatura regioni → zone
# ==============================================================================
@pytest.mark.parametrize("regione", REGIONI_ITALIANE)
def test_tutte_le_regioni_hanno_zona_e_territorio(arera, regione):
    zona, territorio = arera.resolve_zona_gas(regione)
    assert zona in ZONE_VALIDE
    assert territorio in {"Nord", "Sud"}


def test_copertura_mappatura_completa():
    assert len(GAS_ZONE_BY_REGIONE) == 20
    assert set(GAS_ZONE_BY_REGIONE) == set(ACCISA_TERRITORIO_BY_REGIONE)


def test_regione_sconosciuta_strict_solleva(arera):
    with pytest.raises(UnknownRegionError):
        arera.resolve_zona_gas("Ruritania")


def test_regione_sconosciuta_non_strict_warning(arera):
    with pytest.warns(RuntimeWarning):
        zona, terr = arera.resolve_zona_gas("Ruritania", strict=False)
    assert (zona, terr) == ("Nord Occidentale", "Nord")


@pytest.mark.parametrize(
    "variante",
    ["Emilia-Romagna", "Emilia Romagna", "emilia romagna", "EMILIA-ROMAGNA"],
)
def test_normalizzazione_nomi_regione(arera, variante):
    assert arera.resolve_zona_gas(variante)[0] == "Nord Orientale"


@pytest.mark.parametrize(
    "variante", ["Valle d'Aosta", "Valle d\u2019Aosta", "Valle D Aosta"]
)
def test_normalizzazione_apostrofi(variante):
    norm = _norm_regione(variante)
    assert norm in {"valle d aosta", "valle daosta"}


@pytest.mark.parametrize(
    "regione,zona_attesa",
    [
        ("Lombardia", "Nord Occidentale"),
        ("Veneto", "Nord Orientale"),
        ("Marche", "Centrale"),
        ("Puglia", "Centro-Sud Orientale"),
        ("Lazio", "Centro-Sud Occidentale"),
        ("Sicilia", "Meridionale"),
    ],
)
def test_zone_gas_note(arera, regione, zona_attesa):
    assert arera.resolve_zona_gas(regione)[0] == zona_attesa


@pytest.mark.parametrize(
    "regione,territorio_atteso",
    [
        ("Lombardia", "Nord"), ("Toscana", "Nord"), ("Lazio", "Nord"),
        ("Campania", "Sud"), ("Sicilia", "Sud"), ("Sardegna", "Sud"),
        ("Abruzzo", "Sud"), ("Basilicata", "Sud"),
    ],
)
def test_territorio_accisa(arera, regione, territorio_atteso):
    """Lazio = Nord: aliquota piena. La versione precedente lo dava per Sud."""
    assert arera.resolve_zona_gas(regione)[1] == territorio_atteso


# ==============================================================================
# Scaglioni: accise e quota volumetrica
# ==============================================================================
def test_accisa_media_1400_smc_nord(arera):
    # 120*0.044 + 360*0.175 + 920*0.170 = 5.28 + 63.00 + 156.40 = 224.68
    assert arera.get_gas_accisa_avg("Nord", 1400) == pytest.approx(224.68 / 1400, abs=1e-9)


def test_accisa_media_1400_smc_sud(arera):
    # 120*0.038 + 360*0.135 + 920*0.120 = 4.56 + 48.60 + 110.40 = 163.56
    assert arera.get_gas_accisa_avg("Sud", 1400) == pytest.approx(163.56 / 1400, abs=1e-9)


def test_accisa_sud_sempre_minore_di_nord(arera):
    for consumo in (100, 300, 1000, 1400, 5000):
        assert arera.get_gas_accisa_avg("Sud", consumo) < \
               arera.get_gas_accisa_avg("Nord", consumo)


@pytest.mark.parametrize(
    "consumo,totale_atteso",
    [
        (0, 0.0),
        (120, 120 * 0.044),                                    # confine esatto
        (121, 120 * 0.044 + 1 * 0.175),                        # primo salto
        (480, 120 * 0.044 + 360 * 0.175),                       # confine IVA
        (1560, 120 * 0.044 + 360 * 0.175 + 1080 * 0.170),
        (2000, 120 * 0.044 + 360 * 0.175 + 1080 * 0.170 + 440 * 0.186),
    ],
)
def test_accisa_scaglioni_confini(arera, consumo, totale_atteso):
    avg = arera.get_gas_accisa_avg("Nord", consumo)
    totale = avg * consumo
    assert totale == pytest.approx(totale_atteso, abs=1e-9)


def test_consumo_oltre_ultimo_scaglione_non_perde_volume(arera):
    """Regressione: con l'implementazione originale il volume oltre l'ultimo
    limite non veniva tariffato."""
    avg = arera.get_gas_accisa_avg("Nord", 50_000)
    assert avg * 50_000 > 0.180 * 50_000 * 0.9


def test_consumo_zero_non_divide_per_zero(arera):
    assert arera.get_gas_accisa_avg("Nord", 0) == 0.0
    assert arera.get_gas_vol_avg("Nord Occidentale", 0) == 0.0


def test_gas_vol_avg_scalare(write_tariffs, synthetic_tariffs_dict):
    payload = copy.deepcopy(synthetic_tariffs_dict)
    payload["GAS_VOL"]["Centrale"] = 0.17
    arera = AreraTariffs(write_tariffs(payload))
    assert arera.get_gas_vol_avg("Centrale", 1400) == pytest.approx(0.17)


def test_territorio_sconosciuto_solleva(arera):
    with pytest.raises(KeyError):
        arera.get_gas_accisa_avg("Centro", 1000)


# ==============================================================================
# Costi regolati aggregati
# ==============================================================================
def test_costi_regolati_include_taxes(arera):
    fix_no, vol_no = arera.get_gas_costi_regolati("Lombardia", 1400, include_taxes=False)
    fix_si, vol_si = arera.get_gas_costi_regolati("Lombardia", 1400, include_taxes=True)
    assert fix_no == fix_si == 60.0
    delta = vol_si - vol_no
    atteso = 224.68 / 1400 + 0.031     # accisa media + addizionale Lombardia
    assert delta == pytest.approx(atteso, abs=1e-9)


def test_addizionale_fallback_default(arera):
    _, vol = arera.get_gas_costi_regolati("Molise", 1000, include_taxes=True)
    _, vol_no_tax = arera.get_gas_costi_regolati("Molise", 1000, include_taxes=False)
    accisa = arera.get_gas_accisa_avg("Sud", 1000)
    assert vol - vol_no_tax - accisa == pytest.approx(0.019, abs=1e-9)


# ==============================================================================
# Tariffe di produzione
# ==============================================================================
@pytest.mark.requires_data
def test_tariffe_produzione_caricabili(arera_real):
    """Fallisce se il JSON di produzione è obsoleto o malformato."""
    assert arera_real.ELE["residente"]["cdispd"] > 0
    assert set(arera_real.GAS_FIX) >= ZONE_VALIDE


@pytest.mark.requires_data
@pytest.mark.parametrize("regione", REGIONI_ITALIANE)
def test_produzione_copre_tutte_le_regioni(arera_real, regione):
    fix, vol = arera_real.get_gas_costi_regolati(regione, 1400)
    assert fix >= 0 and vol > 0
