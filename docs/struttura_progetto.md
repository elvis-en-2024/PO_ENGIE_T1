# Struttura del progetto PO_scraping_2026

Aggiornata al 02/10/2026.

## Codice attivo

### `app.py` e `ui/portale.py`
App Streamlit in stile Portale Offerte (`streamlit run app.py`). Pagine, sempre con pulsanti Indietro:

| Pagina | Contenuto |
|---|---|
| 1. Tipo di offerta | luce o gas, regione, prezzo fisso o variabile, residenza |
| 2. Caratteristiche | potenza, fasce o monoraria, consumo annuo (ripartizione F1/F2/F3), usi gas, sconti condizionati a domiciliazione o bolletta web |
| 3. Elenco delle offerte | ulteriori filtri (venditore, nome, codice, solo con sconti, ordinamento); posizione della migliore offerta ENGIE; schede come il Portale oppure tabella dati a tutta larghezza con composizione della spesa, sconti dichiarati e note utili; export CSV |
| Dettaglio offerta | composizione della spesa come il dettaglio del Portale (vendita con le componenti, sconti, rete, oneri, imposte, IVA), dati del venditore, sconti e note |
| Simula offerta | form per una nuova offerta (prezzi per fascia o spread, quota fissa e potenza, energia verde, componenti regolate, sconti); posizione nel ranking della ricerca corrente, distanza dalla prima e dalla migliore ENGIE, prezzo o quota fissa necessari per arrivare #1, #3 o #10 |

- **Dati:** le offerte del file dell'ultima rilevazione fino alla data scelta (come il Portale), con calcolo
  in cache.
- **Avviso:** segnala se l'ultima rilevazione è più vecchia di 2 giorni.
- **`ui/portale.py`:** CSS e blocchi HTML in stile Portale; descrizioni leggibili di componenti, sconti e note
  di un'offerta dalle colonne del tracciato.

### `download/`
| File | Ruolo |
|---|---|
| `downloader.py` | download dei file XML giornalieri (E, G, D) e dei CSV *Parametri* dal Portale Offerte; retry su errori di rete, HTTP 5xx e 429; scrittura atomica |
| `gme.py` | sessioni giornaliere dei mercati a termine GME (MTE luce, MT-GAS), via Playwright (l'API del sito richiede la sessione del browser) |

### `parse/`
| File | Ruolo |
|---|---|
| `parser.py` | lettura in streaming (`lxml.iterparse`) dei file XML del Portale |
| `flattener.py` | trasforma ogni `Offerta` in una riga piatta: componenti, intervalli e sconti senza troncamento (fino a 60 × 10 e 15 × 5, con avviso oltre), zone multiple separate da `\|`, colonne `REGOLATA_*`, `DISP_*`, `IDX_*` e `_COEFF` |

### `storage/daily_store.py`
Storico partizionato `data/storage/storico/commodity=X/anno=YYYY/YYYY-MM.parquet`.
- **Scrittura:** riscrivere un giorno ne sostituisce le righe (nessun duplicato).
- **Funzioni:** `leggi_finestra`, `ultima_rilevazione`, `giorni_presenti`, `pulisci_tmp`, `genera_dashboard`
  (`data/processed/storico_2026_full.parquet`).

### `engine/`
| File | Ruolo |
|---|---|
| `sas_calculator_fast.py` | `FastSASCalculator`: `filter_offers` (commodity, tipo, cliente, zona ISTAT, fasce, limiti di consumo e potenza, prezzo energia) e `calculate_sas` (vedi `guida_calcolo_sas.md`) |
| `component_matrix.py` | vista "long" delle componenti impresa: prezzo per (componente, fascia), scaglione sul consumo annuo, classificazione delle unità, flag delle false multiorarie |
| `parametri_po.py` | lettura dei parametri giornalieri del Portale; rete, oneri e accisa luce; rete e oneri gas per ambito; dispacciamento; imposte gas a scaglioni |
| `forward.py` | regole del Portale per le offerte variabili: periodo di 4 trimestri, media del mese precedente, F0/F1/F23, profili di prelievo gas, CCR pesato; carica PPE e CCR |
| `offerta_simulata.py` | `NuovaOfferta`: riga nel formato del flattener per un'offerta ipotetica; `posiziona` calcola la posizione nel ranking e la variazione di prezzo energia o quota fissa per raggiungere una posizione obiettivo (la SAS è lineare nei prezzi) |
| `arera_tariffs.py` | configurazione di riserva `data/config/arera_tariffs.json` (stime PUN/PSV, tariffe per quando mancano i parametri) |

### `scripts/` (operativi)
| Script | Ruolo |
|---|---|
| `update_daily.py` | entrypoint giornaliero: offerte, parametri, forward GME, PPE/CCR, dashboard |
| `verifica_portale.py` | confronto online: compila il form del Portale (Playwright), legge le schede e confronta la SAS con il motore per codice offerta. Scrive `data/processed/verifica_portale_<scenario>.csv`. Contiene anche `dettaglio_portale()` per leggere la composizione della spesa di un'offerta |
| `rileva_imposte_gas.py` | accise e addizionali gas per regione, dal dettaglio offerta del Portale |
| `rileva_componenti_portale.py` | PPE e CCR dal dettaglio di un'offerta che li dichiara |
| `rebuild_storico.py` | ricostruzione dello storico dai raw XML |
| `download_missing.py` | recupero dei giorni mancanti |
| `diff_sas.py` | confronto della SAS tra due versioni di motore e dati (`data/processed/diff_sas.csv`) |
| `auto_update.bat` | lancio pianificato dell'aggiornamento |
| `crawler_ctes.py`, `hera_scraper.py`, `poste_scraper.py`, `discover_ctes.py`, `extract_cte_data.py`, `parser_ctes.py`, `phase2_parser.py` | Fase 1: scraping ed estrazione delle CTE dai siti dei competitor |
| `bisect_filtri.py`, `dump_colonne_filtro.py`, `dump_offerta.py`, `introspect_xml.py`, `test_*.py` | diagnostica e prove dei singoli siti |

### `tests/`
Suite pytest (circa 7 s; `pytest.ini` esclude `archive/` e le cartelle `sandbox`):

| File | Contenuto |
|---|---|
| `test_sas_calculator.py` | aritmetica del motore con tariffe sintetiche (`conftest.py`) e casi golden |
| `test_parametri_po.py` | parametri del Portale: rete, oneri, accisa, dispacciamento |
| `test_gas_portale.py` | gas fisso riprodotto al centesimo (CHIARISSIMA, Milano 1.400 Smc = 1.732,03 €) |
| `test_forward.py` | periodo di stima, profili gas, CCR del Portale, stima dalle sessioni GME, perdite solo sul forward, coefficienti indici |
| `test_offerta_simulata.py` | offerta simulata con la stessa SAS di un'offerta reale equivalente; prezzo obiettivo che porta davvero in prima posizione; voci della composizione che sommano alla SAS |
| `test_flattener.py`, `test_daily_store.py`, `test_downloader.py`, `test_arera_tariffs.py` | parsing, storico, download, configurazione |

## Dati (`data/`, non versionati)

| Cartella | Contenuto |
|---|---|
| `raw/{E,G,D}/YYYY/` | XML giornalieri del Portale |
| `raw/parametri/{E,G}/YYYY/` | CSV *Parametri* giornalieri |
| `raw/gme/{mte,mtgas}/YYYY/` | sessioni dei mercati a termine GME (`{prodotto: €/MWh}`) |
| `storage/storico/` | storico partizionato delle offerte |
| `processed/storico_2026_full.parquet` | parquet della dashboard |
| `processed/imposte_gas_portale.json` | accise e addizionali gas per regione (dal Portale) |
| `processed/componenti_portale.json` | PPE e CCR per trimestre (dal Portale) |
| `processed/verifica_portale_*.csv` | esiti del confronto online |
| `config/arera_tariffs.json` | configurazione di riserva (modificare solo dopo verifica) |
| `config/config_competitors.json` | siti dei competitor (Fase 1) |

## Documentazione (`docs/`)

| File | Contenuto |
|---|---|
| `guida_calcolo_sas.md` | calcolo della spesa annua, voce per voce, con esempi verificati |
| `logica_progetto.md` | architettura e flussi |
| `guida_lettura_tracciato.md` | tracciato delle offerte e colonne del flattener |
| `recap_lavori_2026-10.md` | recap della revisione e verifica di settembre-ottobre 2026 |
| `Fase1_Scraping_Logics.md` | scraping CTE dei competitor |
| `Databricks_Migration_Guide.md` | note di migrazione |
| `markdown/` | specifiche ufficiali convertite (trasmissione offerte v5.0, Regole per il calcolo della spesa, indicatori sintetici) e appunti |

## `archive/`

Codice non più importato, conservato per riferimento (spostato senza cancellare nulla):
- vecchio `sas_calculator.py`, `pricing/`;
- pipeline SCD2 e CLI;
- script one-off e vecchi test sandbox;
- handoff delle conversazioni precedenti.

## Convenzioni

- **Script nuovi:** gli operativi vanno in `scripts/`; diagnostica e prove una tantum non vanno nel codice attivo
  (eventualmente in `archive/`).
- **Test nuovi:** in `tests/`, con valori attesi verificati sul Portale o tariffe sintetiche esplicite.
- **Dati rilevati in automatico:** vanno in file separati in `data/processed/`. `arera_tariffs.json` si tocca solo
  a mano, dopo verifica.
