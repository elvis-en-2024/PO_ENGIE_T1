import logging
import os
from pathlib import Path
from datetime import date
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import gzip

logger = logging.getLogger(__name__)


class ErroreServerTemporaneo(Exception):
    """HTTP 429 o 5xx: il portale potrebbe rispondere al tentativo successivo."""


class PortaleOfferteDownloader:
    BASE_URL = "https://ilportaleofferte.it/portaleOfferte/resources/opendata/csv/offerteML"

    def __init__(self, raw_dir: Path):
        self.raw_dir = raw_dir
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self._pulisci_tmp()
        # HTTPX Client per performance e rispetto degli standard moderni
        self.client = httpx.Client(
            timeout=30.0,
            headers={"User-Agent": "PO-Data-Engineering-ETL/1.0 (Contact: data@company.it)"},
            verify=False
        )

    def _pulisci_tmp(self):
        """Download interrotti a metà lasciano .tmp che non vanno riusati."""
        for p in self.raw_dir.rglob("*.tmp"):
            logger.warning(f"Rimosso download incompleto: {p}")
            p.unlink()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException,
                                       ErroreServerTemporaneo)),
        reraise=True,
    )
    def fetch_file(self, target_date: date, commodity: str) -> Path | None:
        """
        Scarica il file XML per la data e la commodity specificata (E, G, D).
        Gestisce i 404 (giorni senza pubblicazione) ritornando None.
        Salva direttamente il file in formato compresso .gz nel raw layer partizionato.
        """
        dir_month = f"{target_date.year}_{target_date.month}" # Nessun padding mese come richiesto
        file_date = target_date.strftime("%Y%m%d")

        filename = f"PO_Offerte_{commodity}_MLIBERO_{file_date}.xml"
        url = f"{self.BASE_URL}/{dir_month}/{filename}"

        # Pattern partizionamento: raw/commodity/YYYY/MM/
        out_dir = self.raw_dir / commodity / str(target_date.year) / f"{target_date.month:02d}"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{filename}.gz"

        if out_path.exists():
            logger.debug(f"File già presente (skip): {out_path}")
            return out_path

        logger.info(f"Download in corso: {url}")
        response = self.client.get(url)

        if response.status_code == 404:
            logger.warning(f"File non trovato (404) sul portale per {target_date} {commodity}")
            return None
        if response.status_code == 429 or response.status_code >= 500:
            logger.warning(f"HTTP {response.status_code} per {target_date} {commodity}, nuovo tentativo")
            raise ErroreServerTemporaneo(f"HTTP {response.status_code} su {url}")

        response.raise_for_status()

        # scrittura atomica: un .gz troncato verrebbe saltato per sempre come "già presente"
        tmp_path = out_path.with_name(out_path.name + ".tmp")
        with gzip.open(tmp_path, 'wb') as f:
            f.write(response.content)
        os.replace(tmp_path, out_path)

        return out_path

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException,
                                       ErroreServerTemporaneo)),
        reraise=True,
    )
    def fetch_parametri(self, target_date: date, commodity: str) -> Path | None:
        """Parametri di calcolo del Portale (oneri, accise, IVA) per E o G.
        Salvati in chiaro in raw/parametri/{E|G}/YYYY/; None se non pubblicati."""
        filename = f"PO_Parametri_Mercato_Libero_{commodity}_{target_date:%Y%m%d}.csv"
        url = (f"{self.BASE_URL.replace('/offerteML', '/parametriML')}/"
               f"{target_date.year}_{target_date.month}/{filename}")
        out_path = self.raw_dir / "parametri" / commodity / str(target_date.year) / filename
        if out_path.exists():
            return out_path

        response = self.client.get(url)
        if response.status_code == 404:
            logger.warning(f"Parametri non trovati (404) per {target_date} {commodity}")
            return None
        if response.status_code == 429 or response.status_code >= 500:
            raise ErroreServerTemporaneo(f"HTTP {response.status_code} su {url}")
        response.raise_for_status()

        out_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = out_path.with_name(out_path.name + ".tmp")
        tmp_path.write_bytes(response.content)
        os.replace(tmp_path, out_path)
        return out_path

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
