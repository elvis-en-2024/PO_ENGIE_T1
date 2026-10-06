# Logica e architettura di PO_scraping_2026

## 1. Scopo

Motore di **competitive intelligence** per il mercato retail luce e gas: replica il ranking del
**Portale Offerte** ARERA (Spesa Annua Stimata, SAS) su tutte le offerte del mercato libero, per
posizionare le offerte ENGIE rispetto ai concorrenti.

Il ranking deve essere:
- **completo:** tutte le offerte valide nella zona;
- **corretto:** SAS uguale a quella del Portale;
- **aggiornato:** dati del giorno.

## 2. Flussi

### Flusso B: Portale Offerte (flusso principale)

```
 ilportaleofferte.it (open data)            mercatoelettrico.org (GME)        ilportaleofferte.it (dettaglio offerta)
   XML offerte E/G/D + CSV Parametri          forward MTE / MT-GAS              PPE, CCR, accise e addizionali gas
            │                                        │                                   │
   download/downloader.py                     download/gme.py              scripts/rileva_componenti_portale.py
            │                                        │                     scripts/rileva_imposte_gas.py
   parse/parser.py + flattener.py                    │                                   │
            │                                        │                                   │
   storage/daily_store.py ─ storico partizionato     │                                   │
            │                                        ▼                                   ▼
            └──────────► engine/sas_calculator_fast.py ◄── engine/forward.py, engine/parametri_po.py
                                    │
                         app.py (Streamlit)  ·  scripts/verifica_portale.py (confronto online)
```

Orchestrazione: `scripts/update_daily.py`, da lanciare ogni mattina (o con `scripts/auto_update.bat`).

1. **Download:**
   - XML giornalieri delle offerte e CSV *Parametri* (il Portale li pubblica in mattinata);
   - sessioni GME del mese precedente e di quello in corso;
   - PPE e CCR, una volta al giorno.
   - I passi GME e Portale sono tolleranti agli errori: se falliscono, il motore usa gli ultimi valori disponibili.
2. **Parsing:** `lxml.iterparse` in streaming. Il flattener produce una riga per offerta con tutte le
   componenti, gli intervalli, gli sconti e le zone (nessun troncamento; zone multiple separate da `|`).
3. **Storico:** un file parquet per commodity e mese. Rielaborare un giorno ne sostituisce le righe.
   `genera_dashboard` rigenera il parquet unico per la dashboard.
4. **Calcolo:** `filter_offers` seleziona le offerte come la ricerca del Portale; `calculate_sas` calcola la
   spesa annua. Il dettaglio è in `guida_calcolo_sas.md`.
5. **Verifica:** `verifica_portale.py` compila il form del Portale con Playwright e confronta le SAS per codice
   offerta, a parità di parametri. `dettaglio_portale()` legge la composizione della spesa di una singola offerta.

### Flusso A: CTE dai siti dei competitor (Fase 1)

Crawler `requests`/BeautifulSoup e Playwright (`crawler_ctes.py`, `hera_scraper.py`, `poste_scraper.py`):
- scaricano le CTE in PDF;
- l'estrazione delle componenti dai PDF (`extract_cte_data.py`) usa un LLM.

Dettaglio: `Fase1_Scraping_Logics.md`.

## 3. Motore di calcolo

| Modulo | Responsabilità |
|---|---|
| `component_matrix.py` | una vista unica delle componenti impresa (prezzo per componente, fascia e scaglione) usata sia dai filtri sia dal calcolo |
| `sas_calculator_fast.py` | filtri e SAS, vettoriali su tutte le offerte |
| `parametri_po.py` | parte regolata dai parametri giornalieri del Portale (nessun aggiornamento trimestrale manuale) |
| `forward.py` | indici delle offerte variabili con le regole ARERA/Portale (forward GME, profili gas, CCR) |
| `arera_tariffs.py` | configurazione JSON di riserva, usata dai test e quando mancano i parametri |

Scelte principali:
- **Una sola fonte per valore.** Valori pubblicati dal Portale (parametri) → presi dagli open data; valori
  non pubblicati ma visibili nel dettaglio offerta (PPE, CCR, imposte gas) → rilevati in automatico;
  forward → GME.
- **Modalità produzione vs test.** `FastSASCalculator(df)` carica tutto in automatico. Con `arera=` o
  `tariffs_path=` usa solo le tariffe passate, così i test sono deterministici.
- **Niente scritture automatiche in `arera_tariffs.json`.** I valori rilevati vanno in file separati in
  `data/processed/`.

## 4. Qualità e test

- **Suite pytest** (`python -m pytest`, circa 7 s):
  - aritmetica con tariffe sintetiche;
  - casi reali riprodotti al centesimo sul dettaglio del Portale (gas, CCR, forward);
  - parsing, storico e download.
  - I `known_bug` sono `xfail(strict=True)`: diventano rossi quando il bug viene risolto.
- **Confronto online:** `scripts/verifica_portale.py` è la verifica di non regressione rispetto al Portale.
  Va rilanciato dopo ogni modifica al motore e a ogni cambio trimestrale.

## 5. Riferimenti normativi

- *Funzionamento e Specifiche del Processo di Trasmissione Offerte Mercato Retail* v5.0
  (`docs/markdown/`): il tracciato XML con cui i venditori trasmettono le offerte.
- *Regole per il calcolo della spesa* v4.0 (`docs/markdown/7d0a872b48e8796c84366afedd2ce7ec.md`): gli
  algoritmi della spesa annua del Portale, i parametri e i profili di prelievo gas.
- *Regole di calcolo indicatori sintetici di prezzo* (`docs/markdown/0f7a9b80925931637af9050c90350ee2.md`).
- ARERA, pagina "Stima della spesa annua", delibera 289/2022/R/com: i forward per le offerte variabili.
