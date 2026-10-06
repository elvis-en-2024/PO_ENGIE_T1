"""Test di contratto sulla transcodifica SII e sull'interfaccia
flattener → sas_calculator_fast.

L'obiettivo non è ri-testare i dizionari in sé, ma verificare che i valori
prodotti dal flattener siano esattamente quelli su cui il calcolatore fa
pattern matching. Ogni disallineamento qui è un errore silenzioso in produzione.
"""
from __future__ import annotations

import pytest

flattener = pytest.importorskip("parse.flattener")
DECODE_MAPS = flattener.DECODE_MAPS


# ==============================================================================
# Struttura dei dizionari
# ==============================================================================
CHIAVI_ATTESE = [
    "TIPO_MERCATO", "TIPO_CLIENTE", "TIPO_OFFERTA",
    "TIPOLOGIA_FASCE", "UNITA_MISURA", "FASCIA_COMPONENTE",
]


@pytest.mark.parametrize("chiave", CHIAVI_ATTESE)
def test_dizionario_presente_e_non_vuoto(chiave):
    assert chiave in DECODE_MAPS
    assert DECODE_MAPS[chiave]


@pytest.mark.parametrize("chiave", CHIAVI_ATTESE)
def test_codici_sono_stringhe_a_due_cifre(chiave):
    for codice in DECODE_MAPS[chiave]:
        assert isinstance(codice, str), f"{chiave}: codice {codice!r} non stringa"
        assert codice.isdigit() and len(codice) == 2, \
            f"{chiave}: codice {codice!r} non conforme al formato SII (2 cifre)"


@pytest.mark.parametrize("chiave", CHIAVI_ATTESE)
def test_nessun_valore_vuoto(chiave):
    for codice, valore in DECODE_MAPS[chiave].items():
        assert str(valore).strip(), f"{chiave}[{codice}] è vuoto"


# ==============================================================================
# Mappature puntuali documentate
# ==============================================================================
@pytest.mark.parametrize(
    "chiave,codice,atteso",
    [
        ("TIPO_MERCATO", "01", "Elettrico"),
        ("TIPO_MERCATO", "02", "Gas"),
        ("TIPO_MERCATO", "03", "Dual Fuel"),
        ("TIPO_OFFERTA", "01", "Fisso"),
        ("TIPO_OFFERTA", "02", "Variabile"),
        ("TIPO_OFFERTA", "03", "FLAT"),
        ("TIPO_OFFERTA", "04", "Mista"),
        ("TIPO_CLIENTE", "01", "Domestico"),
        ("TIPO_CLIENTE", "02", "Altri Usi"),
        ("UNITA_MISURA", "01", "€/Anno"),
        ("UNITA_MISURA", "03", "€/kWh"),
        ("UNITA_MISURA", "04", "€/Smc"),
        ("FASCIA_COMPONENTE", "01", "monorario/F1"),
        ("FASCIA_COMPONENTE", "02", "F2"),
        ("FASCIA_COMPONENTE", "03", "F3"),
        ("FASCIA_COMPONENTE", "91", "F2+F3"),
    ],
)
def test_transcodifica_puntuale(chiave, codice, atteso):
    assert DECODE_MAPS[chiave][codice] == atteso


# ==============================================================================
# Contratto con il calcolatore: fasce (engine.component_matrix.resolve_bande)
# ==============================================================================
from engine.component_matrix import (  # noqa: E402
    BANDE, KIND_FISSO, KIND_KW, KIND_KWH, KIND_PCT, KIND_SMC, _TIPOLOGIE_MONO,
    _norm, classify_unita, resolve_bande,
)


@pytest.mark.parametrize("fascia,bande", [
    ("monorario/F1", ("F1",)), ("F2", ("F2",)), ("F3", ("F3",)),
    ("F2+F3", ("F2", "F3")), ("F1+F3", ("F1", "F3")), ("F1+F2", ("F1", "F2")),
    ("", BANDE),
])
def test_fasce_risolte_in_bande(fascia, bande):
    assert resolve_bande(fascia, "F1, F2, F3") == bande


def test_fascia_di_offerta_monoraria_vale_su_tutto_il_consumo():
    assert resolve_bande("monorario/F1", "monorario/F1") == BANDE


def test_fasce_prodotte_non_risolte_sono_solo_quelle_note():
    """Le fasce non risolte vengono applicate al consumo totale."""
    prodotti = set(DECODE_MAPS["FASCIA_COMPONENTE"].values())
    non_risolte = {f for f in prodotti if not resolve_bande(f, "F1, F2, F3")}
    assert non_risolte <= {"F4", "F5", "F6", "Peak", "OffPeak"}


# ==============================================================================
# Contratto con il calcolatore: unità di misura (classify_unita)
# ==============================================================================
@pytest.mark.parametrize(
    "unita,kind_atteso",
    [
        ("€/Anno", KIND_FISSO),
        ("€", KIND_FISSO),
        ("€/kW", KIND_KW),
        ("€/kWh", KIND_KWH),
        ("€/Smc", KIND_SMC),
        ("Percentuale", KIND_PCT),
    ],
)
def test_classificazione_unita_note(unita, kind_atteso):
    assert classify_unita(unita) == kind_atteso


def test_tutte_le_unita_sono_classificate():
    for codice, unita in DECODE_MAPS["UNITA_MISURA"].items():
        assert classify_unita(unita) in {KIND_FISSO, KIND_KW, KIND_KWH, KIND_SMC, KIND_PCT}, \
            f"UNITA_MISURA[{codice}] = '{unita}' non viene classificata"


# ==============================================================================
# Contratto con il calcolatore: tipologia fasce e tipo cliente
# ==============================================================================
def test_tipologie_monorarie_riconosciute():
    monorarie = {_norm(v) for v in DECODE_MAPS["TIPOLOGIA_FASCE"].values()
                 if "monorario" in v.lower() and "bi" not in v.lower()}
    assert monorarie <= _TIPOLOGIE_MONO

def test_biorario_distinguibile_da_monorario():
    """Il filtro fasce usa substring matching: nessuna tipologia biorario deve
    contenere 'monorario', altrimenti finirebbe nel ranking monorario."""
    for codice, valore in DECODE_MAPS["TIPOLOGIA_FASCE"].items():
        if "biorario" in valore.lower():
            assert "monorario" not in valore.lower(), \
                f"TIPOLOGIA_FASCE[{codice}] = '{valore}' ambigua"


def test_tipo_cliente_domestico_non_ambiguo():
    """'Condominio Uso Domestico (Gas)' contiene 'Domestico': il filtro di
    filter_offers deve fare match esatto per token, non per sottostringa."""
    import pandas as pd
    from engine.sas_calculator_fast import FastSASCalculator
    valori = pd.Series(list(DECODE_MAPS["TIPO_CLIENTE"].values()))
    calc = FastSASCalculator.__new__(FastSASCalculator)  # niente tariffe
    match = calc._match_multivalore(valori, "Domestico", "TIPO_CLIENTE")
    assert list(valori[match]) == ["Domestico"]


def test_tipo_offerta_fisso_non_ambiguo():
    ambigui = [v for v in DECODE_MAPS["TIPO_OFFERTA"].values()
               if "Fisso" in v and v != "Fisso"]
    assert not ambigui, f"Filtro tipo_offerta='Fisso' ambiguo per {ambigui}"


# ==============================================================================
# flatten_offer — smoke test (attivo solo se la funzione è esposta)
# ==============================================================================
XML_OFFERTA_MINIMA = """<?xml version="1.0" encoding="UTF-8"?>
<offerta xmlns="http://www.acquirenteunico.it/schemas/SII_AU/OffertaRetail/01">
  <IdentificativiOfferta>
    <PIVA_UTENTE>11475730154</PIVA_UTENTE>
    <COD_OFFERTA>SMOKE001</COD_OFFERTA>
  </IdentificativiOfferta>
  <DettaglioOfferta>
    <TIPO_MERCATO>01</TIPO_MERCATO>
    <TIPO_CLIENTE>01</TIPO_CLIENTE>
    <TIPO_OFFERTA>01</TIPO_OFFERTA>
    <NOME_OFFERTA>Offerta Smoke Test</NOME_OFFERTA>
  </DettaglioOfferta>
</offerta>
"""


NS = {"ns": "http://www.acquirenteunico.it/schemas/SII_AU/OffertaRetail/01"}


def _flatten(xml: str) -> dict:
    from lxml import etree
    return flattener.flatten_offer(etree.fromstring(xml.encode("utf-8")), "E", NS)


def test_flatten_offer_transcodifica_i_codici():
    record = _flatten(XML_OFFERTA_MINIMA)
    assert record["commodity"] == "E"
    assert record["COD_OFFERTA"] == "SMOKE001"
    assert record["TIPO_OFFERTA"] == "Fisso"
    assert record["TIPO_CLIENTE"] == "Domestico"
    assert "01" not in (record["TIPO_OFFERTA"], record["TIPO_CLIENTE"]), \
        "I codici SII devono essere transcodificati, non lasciati grezzi"


def _xml_offerta(corpo: str) -> str:
    return f"""<offerta xmlns="{NS['ns']}">
      <IdentificativiOfferta>
        <PIVA_UTENTE>11475730154</PIVA_UTENTE><COD_OFFERTA>X1</COD_OFFERTA>
      </IdentificativiOfferta>
      {corpo}
    </offerta>"""


def _componente(n: int, intervalli: str | None = None) -> str:
    intervalli = intervalli or (
        f"<IntervalloPrezzi><FASCIA_COMPONENTE>01</FASCIA_COMPONENTE>"
        f"<PREZZO>0.{n:03d}</PREZZO><UNITA_MISURA>03</UNITA_MISURA></IntervalloPrezzi>")
    return (f"<ComponenteImpresa><NOME>C{n}</NOME><DESCRIZIONE>d</DESCRIZIONE>"
            f"<TIPOLOGIA>01</TIPOLOGIA><MACROAREA>04</MACROAREA>{intervalli}"
            f"</ComponenteImpresa>")


def test_nessun_troncamento_oltre_5_componenti():
    """Il file E del 24/09/2026 ha offerte con 12 componenti: prima del fix
    venivano salvati solo i primi 5."""
    rec = _flatten(_xml_offerta("".join(_componente(n) for n in range(1, 8))))
    assert rec["COMP_IMP_7_NOME"] == "C7"
    assert rec["COMP_IMP_7_INT_1_PREZZO"] == "0.007"
    assert "COMP_IMP_8_NOME" not in rec, "schema dinamico: niente colonne vuote"


def test_nessun_troncamento_oltre_5_intervalli():
    intervalli = "".join(
        f"<IntervalloPrezzi><FASCIA_COMPONENTE>01</FASCIA_COMPONENTE>"
        f"<PREZZO>0.{j}</PREZZO><UNITA_MISURA>03</UNITA_MISURA></IntervalloPrezzi>"
        for j in range(1, 10))
    rec = _flatten(_xml_offerta(_componente(1, intervalli)))
    assert rec["COMP_IMP_1_INT_9_PREZZO"] == "0.9"


def test_scaglioni_e_codici_grezzi_con_nomi_letti_dal_motore():
    intervalli = (
        "<IntervalloPrezzi><FASCIA_COMPONENTE>01</FASCIA_COMPONENTE>"
        "<CONSUMO_DA>0</CONSUMO_DA><CONSUMO_A>6000</CONSUMO_A>"
        "<PREZZO>0.011</PREZZO><UNITA_MISURA>03</UNITA_MISURA>"
        "<PeriodoValidita><DURATA>12</DURATA><VALIDO_FINO>12/2026</VALIDO_FINO></PeriodoValidita>"
        "</IntervalloPrezzi>")
    rec = _flatten(_xml_offerta(_componente(1, intervalli)))
    assert rec["COMP_IMP_1_INT_1_CONSUMO_DA"] == "0"
    assert rec["COMP_IMP_1_INT_1_CONSUMO_A"] == "6000"
    assert rec["COMP_IMP_1_INT_1_VALIDO_FINO"] == "12/2026"
    assert rec["COMP_IMP_1_INT_1_DURATA"] == "12"
    assert rec["COMP_IMP_1_MACROAREA_COD"] == "04"
    assert rec["COMP_IMP_1_MACROAREA"] == "Prezzo quota energia"
    assert rec["COMP_IMP_1_TIPOLOGIA_COD"] == "01"


def test_zone_multiple_tutte_salvate():
    rec = _flatten(_xml_offerta(
        "<ZoneOfferta><REGIONE>01</REGIONE><REGIONE>07</REGIONE></ZoneOfferta>"))
    assert rec["REGIONE"] == "01|07"
    assert rec["PROVINCIA"] is None


def test_offerta_nazionale_senza_zone():
    rec = _flatten(_xml_offerta(""))
    assert rec["REGIONE"] is None and rec["COMUNE"] is None


def test_tre_prezzi_sconto():
    prezzi = "".join(
        f"<PrezziSconto><TIPOLOGIA>01</TIPOLOGIA><PREZZO>{v}</PREZZO>"
        f"<UNITA_MISURA>01</UNITA_MISURA></PrezziSconto>" for v in (10, 20, 30))
    rec = _flatten(_xml_offerta(
        f"<Sconto><NOME>S</NOME><VALIDITA>01</VALIDITA>{prezzi}</Sconto>"))
    assert rec["SCONTO_1_PREZZO_3_VAL"] == "30"
    assert rec["SCONTO_1_VALIDITA"] == "Ingresso"


def test_limite_superato_viene_segnalato(caplog, monkeypatch):
    monkeypatch.setattr(flattener, "MAX_COMPONENTI", 2)
    with caplog.at_level("WARNING"):
        rec = _flatten(_xml_offerta("".join(_componente(n) for n in range(1, 4))))
    assert "COMP_IMP_3_NOME" not in rec
    assert "3 ComponenteImpresa" in caplog.text
