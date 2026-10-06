"""Downloader: retry su errori temporanei del portale, scrittura atomica."""
from __future__ import annotations

import gzip
from datetime import date

import httpx
import pytest
from tenacity import wait_none

from download.downloader import ErroreServerTemporaneo, PortaleOfferteDownloader


@pytest.fixture
def downloader(tmp_path, monkeypatch):
    monkeypatch.setattr(PortaleOfferteDownloader.fetch_file.retry, "wait", wait_none())

    def _crea(risposte):
        d = PortaleOfferteDownloader(tmp_path)
        coda = list(risposte)
        d.client = httpx.Client(transport=httpx.MockTransport(
            lambda req: httpx.Response(*coda.pop(0)[:1], content=b"<xml/>")))
        return d
    return _crea


def test_retry_su_503_poi_successo(downloader):
    d = downloader([(503,), (429,), (200,)])
    out = d.fetch_file(date(2026, 9, 24), "E")
    assert gzip.open(out).read() == b"<xml/>"
    assert not list(out.parent.glob("*.tmp"))


def test_404_restituisce_none_senza_retry(downloader):
    assert downloader([(404,)]).fetch_file(date(2026, 9, 24), "E") is None


def test_5xx_persistente_solleva(downloader):
    with pytest.raises(ErroreServerTemporaneo):
        downloader([(500,)] * 5).fetch_file(date(2026, 9, 24), "E")


def test_tmp_orfani_rimossi_all_avvio(tmp_path):
    orfano = tmp_path / "E" / "2026" / "09" / "PO_Offerte_E_MLIBERO_20260924.xml.gz.tmp"
    orfano.parent.mkdir(parents=True)
    orfano.write_bytes(b"troncato")
    PortaleOfferteDownloader(tmp_path).close()
    assert not orfano.exists()
