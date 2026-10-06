# Walkthrough — Applicazione Deliverable Claude al Progetto

> Data: 26 Agosto 2026

---

## Modifiche Applicate

### File Nuovi Creati (10)

| File | Dimensione | Scopo |
|------|-----------|-------|
| [`requirements-dev.txt`](file:///c:/Users/XP6566/OneDrive%20-%20ENGIE/Documenti/PO_scraping_2026/requirements-dev.txt) | 128 B | Dev dependencies (pytest, coverage, freezegun) |
| [`pytest.ini`](file:///c:/Users/XP6566/OneDrive%20-%20ENGIE/Documenti/PO_scraping_2026/pytest.ini) | 338 B | Configurazione pytest con 4 marker custom |
| [`tests/__init__.py`](file:///c:/Users/XP6566/OneDrive%20-%20ENGIE/Documenti/PO_scraping_2026/tests/__init__.py) | 16 B | Package init |
| [`tests/conftest.py`](file:///c:/Users/XP6566/OneDrive%20-%20ENGIE/Documenti/PO_scraping_2026/tests/conftest.py) | 8.7 KB | Fixture sintetiche: tariffe ARERA, factory offerte, helper SAS |
| [`tests/golden_loader.py`](file:///c:/Users/XP6566/OneDrive%20-%20ENGIE/Documenti/PO_scraping_2026/tests/golden_loader.py) | 1.1 KB | Caricatore golden dataset CSV |
| [`tests/golden/__init__.py`](file:///c:/Users/XP6566/OneDrive%20-%20ENGIE/Documenti/PO_scraping_2026/tests/golden/__init__.py) | 27 B | Package init |
| [`tests/golden/sas_expected.csv`](file:///c:/Users/XP6566/OneDrive%20-%20ENGIE/Documenti/PO_scraping_2026/tests/golden/sas_expected.csv) | 2.7 KB | Golden dataset con 10 casi test (da compilare con valori PO reali) |
| [`tests/test_arera_tariffs.py`](file:///c:/Users/XP6566/OneDrive%20-%20ENGIE/Documenti/PO_scraping_2026/tests/test_arera_tariffs.py) | 10 KB | 30+ test su validazione config, mapping zone, scaglioni accise |
| [`tests/test_sas_calculator.py`](file:///c:/Users/XP6566/OneDrive%20-%20ENGIE/Documenti/PO_scraping_2026/tests/test_sas_calculator.py) | 23 KB | 40+ test su filtri, aritmetica EE/Gas, sconti, perdite, golden |
| [`tests/test_flattener.py`](file:///c:/Users/XP6566/OneDrive%20-%20ENGIE/Documenti/PO_scraping_2026/tests/test_flattener.py) | 10 KB | 20+ test contratto flattener↔calculator |

### File Modificati (3)

| File | Fix Applicato |
|------|--------------|
| [`requirements.txt`](file:///c:/Users/XP6566/OneDrive%20-%20ENGIE/Documenti/PO_scraping_2026/requirements.txt) | Aggiornato con tutte le dipendenze mancanti + versioni pinnate |
| [`engine/arera_tariffs.py`](file:///c:/Users/XP6566/OneDrive%20-%20ENGIE/Documenti/PO_scraping_2026/engine/arera_tariffs.py) | Mappatura completa 20 regioni, `resolve_zona_gas()` con strict/warning, normalizzazione nomi, validazione scaglioni, Lazio→Nord per accise, Sardegna aggiunta |
| [`engine/sas_calculator_fast.py`](file:///c:/Users/XP6566/OneDrive%20-%20ENGIE/Documenti/PO_scraping_2026/engine/sas_calculator_fast.py) | Dependency injection: `arera` e `tariffs_path` iniettabili nel costruttore |
| [`app.py`](file:///c:/Users/XP6566/OneDrive%20-%20ENGIE/Documenti/PO_scraping_2026/app.py) | Fix deduplica: `PARTITION BY PIVA + COD_OFFERTA + commodity`, parametro SQL `?` anti-injection |

---

## Fix Applicati (dettaglio)

### ✅ Fix #3 — map_zone completa in arera_tariffs.py
- Aggiunte **8 regioni mancanti**: Marche, Umbria, Friuli-VG, Trentino-AA, Molise, Basilicata, Sardegna, Valle d'Aosta
- Lazio spostato da "Sud" a **"Nord"** per le accise (più corretto per la maggior parte del territorio)
- `resolve_zona_gas()` con mode `strict=True` (raise) o `strict=False` (warning + fallback)
- Normalizzazione nomi regione (accenti, apostrofi, trattini, case)
- Validazione scaglioni: controlla ordinamento e copertura ultimo scaglione

### ✅ Fix #4 — Dependency injection in FastSASCalculator
- Nuovo parametro `arera=` per iniettare istanza AreraTariffs (usata dai test)
- Nuovo parametro `tariffs_path=` per path alternativo
- **100% retrocompatibile**: nessuna chiamata esistente cambia

### ✅ Fix #10 — Deduplica app.py
- `PARTITION BY` ora usa `PIVA_UTENTE, COD_OFFERTA, commodity` (chiave logica corretta)
- Tiebreaker deterministico con `DATA_RILEVAZIONE`
- Parametro SQL `?` al posto di f-string (no SQL injection)

### ✅ Fix requirements.txt
- Aggiunte: polars, lxml, duckdb, streamlit, altair, httpx, tenacity, PyYAML, pypdf
- Tutte le versioni pinnate con note su numpy 1.26.x

---

## Come Eseguire i Test

```bash
# Installa dev dependencies
pip install -r requirements-dev.txt

# Suite completa (esclusi test su dati di produzione)
pytest -m "not requires_data and not golden"

# Solo bug noti (report delle divergenze da correggere)
pytest -m known_bug -v

# Solo confronto con il Portale Offerte (richiede golden dataset compilato)
pytest -m golden -v

# Copertura sui moduli core
pytest --cov=engine --cov=parse --cov-report=term-missing
```

---

## Bug Documentati nei Test (known_bug)

I test marcati `known_bug` **falliscono per progetto** — sono la lista di lavoro:

| # | Bug | Severità | Test |
|---|-----|---------|------|
| 1 | PUN hardcoded 0.105 (offerte Variabili) | 🔴 Alta | `test_pun_hardcoded_0_105` |
| 2 | Accise gas hardcoded (bypassano GAS_ACCISE Nord/Sud) | 🔴 Alta | `test_accisa_gas_differenzia_nord_sud` |
| 4 | Percentuale sommata come €/anno | 🟡 Media | `test_unita_percentuale_non_sommata_come_euro` |
| 5 | Filtro biorario intercetta trioraria | 🟡 Media | `test_filtro_biorario_intercetta_trioraria` |
| 12 | str.contains('Domestico') include Condominio | 🔴 Alta | `test_domestico_non_deve_includere_condominio` |
| 13 | Fasce F1+F3/F1+F2 non gestite | 🟡 Media | `test_fasce_multiorarie_parziali_gestite` |

> Con `-m "not known_bug"` la suite è verde ✅
