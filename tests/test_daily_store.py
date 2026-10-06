"""Storico partizionato mensile: idempotenza e assenza di duplicati."""
from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from storage import daily_store as ds


def _giorno(g: date, offerte: dict[str, str]) -> pl.DataFrame:
    return pl.DataFrame({
        "commodity": ["E"] * len(offerte),
        "PIVA_UTENTE": ["111"] * len(offerte),
        "COD_OFFERTA": list(offerte),
        "NOME_OFFERTA": list(offerte.values()),
    }).with_columns(pl.lit(g).alias("DATA_RILEVAZIONE"))


def _leggi(root):
    return pl.read_parquet(ds.glob_storico(root), hive_partitioning=False)


def test_rielaborare_un_giorno_non_duplica(tmp_path):
    g = date(2026, 9, 24)
    ds.scrivi_giorni([_giorno(g, {"A": "v1", "B": "v1"})], "E", root=tmp_path)
    ds.scrivi_giorni([_giorno(g, {"A": "v2"})], "E", root=tmp_path)
    df = _leggi(tmp_path)
    assert df.height == 1
    assert df["NOME_OFFERTA"].to_list() == ["v2"]


def test_giorni_diversi_stesso_mese_coesistono(tmp_path):
    ds.scrivi_giorni([_giorno(date(2026, 9, 1), {"A": "x"})], "E", root=tmp_path)
    ds.scrivi_giorni([_giorno(date(2026, 9, 2), {"A": "x", "C": "y"})], "E", root=tmp_path)
    assert _leggi(tmp_path).height == 3
    assert ds.giorni_presenti("E", tmp_path) == {date(2026, 9, 1), date(2026, 9, 2)}
    assert len(list(tmp_path.rglob("*.parquet"))) == 1


def test_partizione_per_mese_e_commodity(tmp_path):
    ds.scrivi_giorni([_giorno(date(2026, 8, 31), {"A": "x"}),
                      _giorno(date(2026, 9, 1), {"A": "x"})], "E", root=tmp_path)
    nomi = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*.parquet"))
    assert nomi == ["commodity=E/anno=2026/2026-08.parquet",
                    "commodity=E/anno=2026/2026-09.parquet"]
    assert ds.ultima_rilevazione(tmp_path) == date(2026, 9, 1)


def test_colonne_nuove_unite_allo_schema_esistente(tmp_path):
    ds.scrivi_giorni([_giorno(date(2026, 9, 1), {"A": "x"})], "E", root=tmp_path)
    nuovo = _giorno(date(2026, 9, 2), {"A": "x"}).with_columns(
        pl.lit("0.1").alias("COMP_IMP_7_INT_1_PREZZO"))
    ds.scrivi_giorni([nuovo], "E", root=tmp_path)
    df = _leggi(tmp_path)
    assert "COMP_IMP_7_INT_1_PREZZO" in df.columns
    assert df.filter(pl.col("DATA_RILEVAZIONE") == date(2026, 9, 1))[
        "COMP_IMP_7_INT_1_PREZZO"].to_list() == [None]


def test_giorni_presenti_con_schemi_diversi_tra_mesi(tmp_path):
    ds.scrivi_giorni([_giorno(date(2026, 8, 31), {"A": "x"})], "E", root=tmp_path)
    nuovo = _giorno(date(2026, 9, 1), {"A": "x"}).with_columns(
        pl.lit("0.1").alias("COMP_IMP_10_NOME"))
    ds.scrivi_giorni([nuovo], "E", root=tmp_path)
    assert ds.giorni_presenti("E", tmp_path) == {date(2026, 8, 31), date(2026, 9, 1)}


def test_finestra_ultima_versione_e_offerte_scadute_escluse(tmp_path):
    ds.scrivi_giorni([_giorno(date(2026, 8, 20), {"VECCHIA": "x", "A": "v0"}),
                      _giorno(date(2026, 8, 31), {"A": "v1"})], "E", root=tmp_path)
    ds.scrivi_giorni([_giorno(date(2026, 9, 2), {"A": "v2", "B": "y"}),
                      _giorno(date(2026, 9, 5), {"A": "futura"})], "E", root=tmp_path)
    df = ds.leggi_finestra(date(2026, 9, 3), giorni=8, root=tmp_path)
    assert dict(zip(df["COD_OFFERTA"], df["NOME_OFFERTA"])) == {"A": "v2", "B": "y"}


def test_finestra_senza_dati(tmp_path):
    assert ds.leggi_finestra(date(2026, 9, 3), root=tmp_path).empty


def test_pulisci_tmp(tmp_path):
    (tmp_path / "x.parquet.tmp").write_text("")
    assert ds.pulisci_tmp(tmp_path) == 1
    assert not list(tmp_path.rglob("*.tmp"))


@pytest.mark.parametrize("nome,atteso", [
    ("PO_Offerte_E_MLIBERO_20260924.xml.gz", date(2026, 9, 24)),
    ("PO_Offerte_G_MLIBERO_20250101.xml", date(2025, 1, 1)),
    ("altro.xml", None),
])
def test_data_da_nome_file(nome, atteso):
    assert ds.data_da_nome_file(nome) == atteso
