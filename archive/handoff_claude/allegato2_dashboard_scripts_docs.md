# Allegato 2 — Dashboard, Script Operativi e Documentazione

> Da allegare a Claude browser insieme al prompt principale e all'Allegato 1

---

## app.py (Dashboard Streamlit — Simulatore Portale Offerte)

```python
import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import os
from engine.sas_calculator_fast import FastSASCalculator

st.set_page_config(page_title="Portale Offerte - Simulatore", layout="wide", page_icon="⚡")

@st.cache_data(show_spinner=False)
def load_data(data_rif_str):
    import duckdb
    query = f"""
        SELECT * EXCLUDE(rn) FROM (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY COD_OFFERTA 
                ORDER BY try_strptime(split_part(DATA_INIZIO, '_', 1), '%d/%m/%Y') DESC NULLS LAST) as rn 
            FROM read_parquet('data/processed/storico_2026_full.parquet')
            WHERE try_strptime(split_part(DATA_INIZIO, '_', 1), '%d/%m/%Y') <= '{data_rif_str}'::DATE
        ) WHERE rn = 1
    """
    df = duckdb.query(query).df()
    piva_map = {
        '09633951000': 'Enel Energia', '06655971007': 'Enel Energia', '11475730154': 'ENGIE',
        '11956540153': 'A2A Energia', '02863660359': 'E.ON', '02319210213': 'Iren',
        '04584980962': 'Fastweb', '12874490159': 'Plenitude', '02031070994': 'Acea',
        '04179130963': 'Octopus'
    }
    col_piva = 'PIVA_UTENTE' if 'PIVA_UTENTE' in df.columns else 'PIVA_VENDITORE'
    df['NOME_VENDITORE'] = df[col_piva].map(piva_map).fillna(df[col_piva])
    # ... filtri di validità temporale (DATA_INIZIO, DATA_FINE, VALIDO_FINO)
    return df

# Step 1: Scelta commodity (E/G)
# Step 2: Parametri (Regione, Residenza, Potenza kW, Fasce, Tipo Prezzo)
# Step 3: Ranking SAS con FastSASCalculator
#   - Filtro: no condizioni limitanti, no "Sottocosto"
#   - 4 tab: ARERA 2700kWh, ENGIE 2100kWh, Custom 1, Custom 2
#   - EE Biorario: F1=891, F2=837, F3=972 (profilo ARERA)
#   - Gas: consumo diretto in F1
#   - Vista doppia: HTML cards (simula PO) + tabella dati
#   - Highlight ENGIE in azzurro
#   - Time Travel via sidebar date picker
```

---

## cli/main.py (Orchestratore CLI)

```python
# Subcomandi:
# 1. daily    → Scarica XML di oggi, parsa, merge SCD2 per E/G/D
# 2. backfill → Loop su range date (--start, --end, --commodity)
# 3. simula   → Placeholder

# Pipeline per singola data:
#   xml_file = downloader.fetch_file(target_date, commodity)
#   records = list(parser.parse(xml_file, commodity))
#   stats = scd2.process_daily_batch(records, target_date, commodity)
#   → Salva manifest JSON con statistiche merge
```

---

## scripts/crawler_ctes.py (Scraper PDF CTE/SS — 8 Fornitori)

```python
# Architettura a 2 livelli:
# LIVELLO 1: Naviga URL index → raccoglie tutti i link potenziali offerte
# LIVELLO 2: Naviga ogni pagina offerta → cerca PDF CTE/SS
#
# Tecniche anti-scraping superate:
# - Salesforce CDN (A2A): Regex su JSON embedded "url_scheda_sintetica":"..."
# - AEM (ACEA): Whitelist "visualizzaDocumento" come PDF valido
# - Web Components (E.ON): soup.find_all(href=True) invece di find_all('a')
# - DAM offuscato (Edison): Intercetta "getbusinessdoc.ashx" + "DocumentLink"
# - Semantica assente (Iren): Bypass filtro se dominio=iren e testo="visualizza"
#
# Output: data/raw/ctes/{fornitore}/{CTE|SS}/{data}_{hash}.pdf
# Report: data/crawling_history/crawling_report_{data}.json
```

---

## scripts/update_daily.py (Aggiornamento Incrementale)

```python
# Logica:
# 1. Legge storico_completo.parquet, trova ultima DATA_RILEVAZIONE
# 2. Calcola gap fino a ieri
# 3. Per ogni giorno mancante: Download → Parse → Append
# 4. Concat lazy Polars (scan_parquet + sink_parquet) per efficienza
# 5. Salvataggio atomico (tmp → rename)
# Supporta --date per forzare data specifica
```

---

## scripts/build_lake.py (Costruzione Data Lake)

```python
# Processa tutti i file .gz in data/raw/ (bulk storico)
# Batch di 100 file per gestione RAM
# Estrae commodity dal path, data dal nome file
# Output: data/lake/batch_{n}.parquet
# Schema safe: tutto Utf8 tranne DATA_RILEVAZIONE (Date)
```

---

## scripts/hera_scraper.py (Bot Playwright per Hera Comm)

```python
# Hera usa Liferay Portal con rendering JS dinamico
# I documenti non esistono nell'HTML statico
# Il bot:
# 1. Apre Chromium headless via Playwright
# 2. Naviga alla pagina offerta
# 3. Attende networkidle (DOM completamente reidratato)
# 4. Cerca link a /documents/ nel DOM reidratato
# 5. Scarica .pdf e .zip
```

---

## scripts/poste_scraper.py (Bot Playwright per Poste Italiane)

```python
# Poste usa hosting multi-dominio:
# - Index: poste.it → redirect → postepay.poste.it
# - PDF: media.poste.it (senza estensione .pdf)
# Il bot:
# 1. Apre Chromium, naviga, attende domcontentloaded
# 2. Filtra link verso media.poste.it
# 3. Identifica CTE/SS dal testo del pulsante
```

---

## docs/Fase1_Scraping_Logics.md (Documentazione Tecnica Scraping)

Contiene le logiche dettagliate di superamento anti-scraping per:
1. **Provider Standard** (Enel, Plenitude, Octopus): BS4 + Regex standard
2. **A2A**: JSON embedded in `<script>` con link Salesforce
3. **ACEA**: AEM con URL senza estensione `.pdf`
4. **E.ON**: Web Components custom (`<eon-ui-link>`)
5. **Edison**: DAM con `getbusinessdoc.ashx`
6. **Hera Comm**: Liferay Portal (Playwright)
7. **Iren**: Obfuscazione semantica (nessuna keyword nei nomi file)
8. **Poste Italiane**: Multi-dominio (Playwright)

---

## docs/Databricks_Migration_Guide.md (Guida Migrazione Enterprise)

Roadmap per scalare il progetto da PC locale a cluster Databricks:
1. **Cluster Config**: Init script per Playwright su worker nodes Ubuntu
2. **Storage**: DBFS / ADLS Gen2 al posto di cartelle locali
3. **Parallelizzazione**: UDF PySpark per scraping distribuito
4. **AI Integration**: Azure OpenAI / GCP Gemini Enterprise con AKV per secrets
5. **Scheduler**: Databricks Workflows con 4 task (HTML scraping → JS scraping → AI extraction → Delta merge)

---

## config/pricing_params.yaml (Parametri Regolatori)

```yaml
periodi:
  - valid_from: "2026-01-01"
    valid_to: "2026-03-31"
    parametri_elettrici:
      lambda_perdite: 0.10
      dispacciamento_tutele_graduali: false
      # TODO: Inserire componenti dagli allegati AU
      
  - valid_from: "2026-04-01"
    valid_to: "2099-12-31"
    parametri_elettrici:
      lambda_perdite: 0.10
      dispacciamento_tutele_graduali: true  # Nuove regole
```

---

## config/xpath_mapping.yaml (Mapping XML)

```yaml
root_offer_path: "/{http://...AU/OffertaRetail/01}ListaOfferteMercatoLibero/{...}offerta"
namespaces:
  ns: "http://www.acquirenteunico.it/schemas/SII_AU/OffertaRetail/01"
offerta_base:
  - target: "codice_offerta"
    xpath: "ns:IdentificativiOfferta/ns:COD_OFFERTA"
  - target: "piva_venditore"
    xpath: "ns:IdentificativiOfferta/ns:PIVA_UTENTE"
  - target: "nome_offerta"
    xpath: "ns:DettaglioOfferta/ns:NOME_OFFERTA"
```
