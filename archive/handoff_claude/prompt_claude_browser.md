# Prompt per Claude Browser — Continuazione Progetto PO_scraping_2026

Copia e incolla il testo qui sotto in Claude (browser) come primo messaggio. Poi allega i file MD indicati alla fine.

---

## 🔽 INIZIO PROMPT — COPIA DA QUI 🔽

Sei un Senior Data Engineer e Python Developer con expertise in:
- Mercato energetico italiano (ARERA, Acquirente Unico, Portale Offerte)
- ETL pipelines con Polars/Pandas/DuckDB su dati Parquet
- Calcolo della Spesa Annua Stimata (SAS) secondo regolamento ARERA
- Web scraping avanzato (BeautifulSoup, Playwright)
- Streamlit dashboards

Sto lavorando al progetto **PO_scraping_2026**, un sistema di competitive intelligence per ENGIE Italia che:
1. Scarica XML giornalieri dal Portale Offerte di Acquirente Unico (Luce/Gas/Dual Fuel)
2. Parsa e appiattisce gli XML gerarchici in tabelle denormalizzate
3. Storicizza le offerte con SCD Type 2 (tracking variazioni via SHA-256)
4. Calcola la Spesa Annua Stimata (SAS) vettorizzata con NumPy
5. Mostra una dashboard Streamlit che simula il Portale Offerte ufficiale con Time Travel

### Stack Tecnologico
- Python 3.9+, Windows
- `lxml` (iterparse streaming XML), `polars` (SCD2), `pandas`+`numpy` (calcolo SAS vettorizzato)
- `duckdb` (query SQL su Parquet), `streamlit` (dashboard)
- `httpx`+`tenacity` (download con retry), `requests`+`beautifulsoup4`+`playwright` (scraping)
- Storage: Parquet files (dim_offerta.parquet ~83MB, storico_completo.parquet ~129MB)

### Struttura del Progetto
```
PO_scraping_2026/
├── app.py                          # Dashboard Streamlit (15.7 KB)
├── cli/main.py                     # CLI orchestrator (daily/backfill/simula)
├── config/
│   ├── pricing_params.yaml         # Parametri regolatori time-bracketed
│   └── xpath_mapping.yaml          # Mapping XML namespace AU
├── data/
│   ├── config/
│   │   ├── arera_tariffs.json      # Tariffe ARERA correnti
│   │   └── config_competitors.json # URL 18 fornitori
│   ├── processed/
│   │   └── storico_2026_full.parquet (78 MB, usato dalla dashboard)
│   └── storage/
│       ├── dim_offerta.parquet      (83 MB, SCD2)
│       └── storico_completo.parquet (129 MB, flat archive)
├── download/downloader.py          # Downloader XML Portale Offerte (httpx)
├── engine/
│   ├── arera_tariffs.py            # Loader/validator tariffe ARERA
│   ├── sas_calculator.py           # Calcolatore SAS row-by-row (reference)
│   └── sas_calculator_fast.py      # Calcolatore SAS vettorizzato NumPy (production)
├── model/schema.py                 # Schema Polars per dim_offerta
├── parse/
│   ├── flattener.py                # XML → record flat (transcodifica SII)
│   └── parser.py                   # Parser streaming (iterparse + gzip)
├── pricing/engine.py               # PricingEngine (STUB con TODO)
├── scripts/
│   ├── crawler_ctes.py             # Scraper BS4+Regex per PDF CTE/SS
│   ├── hera_scraper.py             # Bot Playwright per Hera
│   ├── poste_scraper.py            # Bot Playwright per Poste
│   ├── build_lake.py               # Costruisce data lake da .gz storici
│   ├── update_daily.py             # Aggiornamento incrementale storico
│   ├── rank_sas_full.py            # Ranking SAS standalone
│   └── run_pipeline.py             # Pipeline E2E (Download→Parse→SCD2)
├── storage/scd2_manager.py         # SCD Type 2 manager (Polars)
├── requirements.txt
└── setup.bat
```

### Cosa è Stato Completato ✅
- Pipeline ETL completa: Download XML → Parse streaming → Flatten → SCD2 → Parquet
- FastSASCalculator vettorizzato con: componenti fisse/volumetriche per fascia (F1/F2/F3), perdite di rete, CdispD, PUN/PSV, tariffe ARERA (distribuzione, trasmissione, oneri), accise EE/Gas a scaglioni, addizionali regionali, IVA 10%/22%
- Dashboard Streamlit con simulazione Portale Offerte, Time Travel, HTML cards
- Crawler PDF per 8 fornitori con bypass anti-scraping (Salesforce/AEM/WebComponents/DAM)
- SCD2 Manager con SHA-256 change detection e merge a 4 categorie

### TODO Aperti ⚠️
1. **pricing/engine.py** → Il `PricingEngine` è uno stub, mancano gli indicatori ICF/IC/IP
2. **pricing_params.yaml** → Mancano le componenti dagli allegati AU
3. **Fase 2 AI** → Estrazione dati da PDF CTE via Google Gemini non integrata nella pipeline
4. **Test strutturati** → Solo test manuali/esplorativi, nessuna suite pytest
5. **requirements.txt incompleto** → Mancano: polars, lxml, streamlit, duckdb, pyyaml, httpx, tenacity
6. **Copertura fornitori** → Solo 8/18 crawler funzionanti
7. **Validazione SAS** → Verifica di correttezza del calcolo SAS rispetto ai risultati ufficiali del Portale Offerte

### Regole Architetturali da Rispettare
- I file XML seguono lo schema `http://www.acquirenteunico.it/schemas/SII_AU/OffertaRetail/01`
- Il flattener usa codici numerici del SII che vengono transcodificati (es. TIPO_OFFERTA: 01→Fisso, 02→Variabile)
- Le offerte hanno fino a 5 ComponenteImpresa × 5 IntervalloPrezzi e fino a 15 Sconti × 2 PrezziSconto
- Le tariffe ARERA devono essere aggiornate trimestralmente (il sistema fa hard stop se obsolete)
- Il Gas ha 6 zone tariffarie + accise a 4 scaglioni + addizionale regionale
- L'Elettricità ha perdite di rete (×1.10 se non comprensivo), CdispD, esenzione 1800 kWh/anno residenti ≤3kW
- IVA: EE domestico 10% flat; Gas 10% fino a 480 Smc, 22% oltre

---

**Ti allego i file MD con i dettagli completi del progetto.** Leggili e poi dimmi cosa vuoi che faccia tra:

1. **Verificare il calcolo SAS** confrontando i risultati del FastSASCalculator con i valori attesi dal Portale Offerte ufficiale
2. **Completare il PricingEngine** (pricing/engine.py) con il calcolo degli indicatori ICF, IC, IP
3. **Aggiornare requirements.txt** con tutte le dipendenze mancanti
4. **Creare una suite di test pytest** strutturata per i moduli core
5. **Altro** (specifica tu)

## 🔼 FINE PROMPT — COPIA FINO A QUI 🔼
