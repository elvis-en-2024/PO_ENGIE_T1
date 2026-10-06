# Guida alla Migrazione su Databricks (Scaling Aziendale)

Nel caso in cui si voglia scalare questo progetto da un PC locale a un ambiente Enterprise (come Azure Databricks o AWS Databricks) per automatizzare la pipeline giornalmente su nodi distribuiti, segui queste best practices.

## 1. Gestione Librerie e Ambiente (Cluster Configuration)
Databricks utilizza il framework Spark su cluster remoti Linux (Ubuntu).
- **Librerie Python**: Tutte le librerie in `requirements.txt` (`requests`, `beautifulsoup4`, `pydantic`, `google-genai`) possono essere caricate direttamente dal tab "Libraries" del Cluster (via PyPI).
- **Il problema Playwright**: Playwright richiede l'installazione dei browser binari (Chromium) a livello di sistema operativo. Poiché in Databricks i cluster sono effimeri, non basta un `pip install playwright`. Devi usare uno script di inizializzazione (`init script`).

### Init Script per Playwright su Databricks:
Crea uno script in Workspace o su cloud storage (es. DBFS) chiamato `install_playwright.sh`:
```bash
#!/bin/bash
sudo apt-get update
pip install playwright
playwright install chromium
playwright install-deps
```
Configura il cluster Databricks per eseguire questo init script all'avvio ("Advanced Options" > "Init Scripts").

## 2. Riorganizzazione dello Storage
Il codice attuale salva i file nella cartella locale `/data/raw/ctes`. 
In Databricks, devi puntare i percorsi al DBFS (Databricks File System) o direttamente a un Data Lake montato (es. Azure Data Lake Storage Gen2).
**Esempio Modifica Python:**
```python
# Da così (Locale)
base_dir = "data/raw/ctes"
# A così (Databricks ADLS)
base_dir = "/dbfs/mnt/datalake/po_scraping/raw/ctes"
```

## 3. Parallelizzazione dello Scraping (PySpark)
Al momento lo scraping avviene in modo sequenziale (fornitore dopo fornitore). In Databricks, puoi sfruttare i Worker nodes per scaricare simultaneamente le offerte.
- Salva la lista dei fornitori e degli URL di base in un DataFrame PySpark.
- Utilizza una **UDF (User Defined Function) in Pandas/Spark** per distribuire il carico.
```python
def scrape_provider(provider_name, start_url):
    # Logica di Requests o Playwright
    return f"Success: {provider_name}"

# Esecuzione distribuita sui nodi Databricks
df.rdd.map(lambda row: scrape_provider(row.provider, row.url)).collect()
```
*(Attenzione: usare Playwright su un RDD distribuito richiede di instanziare il browser `sync_playwright()` all'interno del nodo Worker, e non sul driver).*

## 4. Fase 2: Integrazione con i Modelli AI (Gemini / OpenAI)
Lo script locale `extract_cte_data.py` utilizza le API remote di Gemini.
- In ambiente enterprise aziendale (es. Azure), si raccomanda di utilizzare un Endopoint provisioned (es. Azure OpenAI GPT-4o, o l'endpoint GCP per Gemini Enterprise) sostituendo la chiave API locale con l'integrazione via Service Principal o managed identity (AKV - Azure Key Vault).
- I secret (API keys) non vanno mai hardcodati nei Notebook, ma richiamati tramite il modulo `dbutils.secrets.get(scope="my_scope", key="gemini_key")`.

## 5. Scheduler (Databricks Workflows)
Invece di eseguire script manuali, crea un **Job Workflow** in Databricks:
1. **Task 1 (Scraping HTML - Python Wheel o Notebook)**: Esegue `crawler_ctes.py` e scarica i PDF sul Data Lake.
2. **Task 2 (Scraping JS - Playwright)**: Esegue i bot dinamici (`hera_scraper.py`, `poste_scraper.py`).
3. **Task 3 (Estrazione Dati AI)**: Preleva i PDF appena scaricati, chiama l'API LLM e struttura i json.
4. **Task 4 (Datalake Merge)**: Converte i JSONestratti in formato `Parquet` (o Delta Table) e fa un operazione di `MERGE INTO` sul database storico per popolare le dashboard aziendali BI.
