# PO_scraping_2026: ranking delle offerte luce e gas come il Portale Offerte

Strumento di competitive intelligence ENGIE sul mercato libero domestico. Il progetto:

1. scarica ogni giorno gli **open data del Portale Offerte** ARERA (offerte XML e parametri di calcolo);
2. ricostruisce uno **storico** giornaliero di tutte le offerte;
3. calcola la **Spesa Annua Stimata (SAS)** con le stesse regole del Portale;
4. mostra il **ranking** per regione, profilo di consumo e tipo di prezzo in un'app Streamlit in stile
   Portale Offerte, con:
   - dettaglio della spesa di ogni offerta;
   - tabella con sconti e note;
   - **simulatore di una nuova offerta**, che indica la posizione nel ranking e il prezzo necessario per
     salire.

Accanto a questo c'è un flusso separato (Fase 1) di scraping delle CTE dai siti dei competitor:
vedi `docs/Fase1_Scraping_Logics.md`.

## Avvio rapido

Requisiti: Windows, Python 3.9+ ("Add Python to PATH"), Chromium per Playwright.

```cmd
setup.bat                              :: crea venv, installa requirements e Chromium
call venv\Scripts\activate

python -m scripts.update_daily         :: aggiornamento giornaliero (ogni mattina)
streamlit run app.py                   :: app di ranking su http://localhost:8501
```

`update_daily` fa tutto in un solo passaggio:

| Passo | Output |
|---|---|
| offerte E/G/D dei giorni mancanti (ultimi 30) | `data/storage/storico/commodity=X/anno=YYYY/YYYY-MM.parquet` |
| parametri di calcolo del Portale | `data/raw/parametri/{E,G}/YYYY/*.csv` |
| quotazioni forward GME (mercati a termine) | `data/raw/gme/{mte,mtgas}/YYYY/*.json` |
| PPE e CCR dal dettaglio offerta del Portale (1 volta al giorno) | `data/processed/componenti_portale.json` |
| parquet della dashboard | `data/processed/storico_2026_full.parquet` |

Le istruzioni sono idempotenti: rilanciare lo stesso giorno non duplica righe.

Opzioni:
- `--date AAAA-MM-GG` rielabora un giorno;
- `--giorni 90` recupera i buchi più vecchi.

Altri comandi utili:

```cmd
python scripts\verifica_portale.py                  :: confronto online SAS locale vs Portale (Playwright)
python scripts\verifica_portale.py G_fisso_Milano   :: un solo scenario
python scripts\rileva_imposte_gas.py                :: rileva accise/addizionali gas per regione dal Portale
python scripts\rileva_componenti_portale.py         :: rileva PPE e CCR dal Portale
python scripts\rebuild_storico.py                   :: ricostruisce lo storico dai raw XML
python -m pytest                                    :: test (circa 7 s)
```

## Come si calcola la spesa

Il calcolo replica le *Regole per il calcolo della spesa* del Portale (v4.0, 16/02/2026). Dettaglio completo,
con formule ed esempi verificati: **[docs/guida_calcolo_sas.md](docs/guida_calcolo_sas.md)**.

In sintesi:
- **Vendita:** componenti dell'offerta, sconti, dispacciamento e componenti regolate (PCV, PPE, CCR, QVD).
- **Rete e oneri:** dai parametri giornalieri del Portale.
- **Imposte:** accisa luce dai parametri; accise e addizionali gas rilevate dal Portale.
- **IVA:** 10% luce; gas 10% sui primi 480 Smc e 22% sul resto.
- **Offerte variabili:** media dei forward dei 4 trimestri × (1+λ) + spread. Per il gas, mese per mese sul
  profilo di prelievo. I forward vengono dal GME.

## Stato della verifica col Portale (02/10/2026)

| Scenario | SAS uguale al Portale (±1 €) |
|---|---|
| Luce fisso monorario, Milano | 267 / 268 |
| Luce fisso a fasce, Milano | 102 / 102 |
| Gas fisso, Milano | 209 / 218 (tutte entro l'1%) |
| Luce variabile, Palermo | scarto costante −24 € (forward GME sotto quelli AU) |
| Gas variabile, Roma | scarto mediano −108 € (forward GME sotto quelli AU) |

Limiti principali:
- **Forward ufficiali:** li elabora Acquirente Unico e li vedono solo gli operatori nell'area SII. Con quel file
  anche le variabili tornerebbero esatte.
- **Offerte PLACET:** non sono ancora nello storico.

Recap completo dei lavori e attività aperte: [docs/recap_lavori_2026-10.md](docs/recap_lavori_2026-10.md).

## Struttura

```
app.py                 app Streamlit (ricerca, ranking, dettaglio, simulatore nuova offerta)
ui/portale.py          stile Portale Offerte e descrizioni delle offerte (sconti, note, componenti)
download/              downloader.py (open data Portale), gme.py (forward GME)
parse/                 parser.py (XML in streaming), flattener.py (XML → colonne)
storage/daily_store.py storico partizionato per commodity/anno/mese e parquet della dashboard
engine/                sas_calculator_fast.py (filtri + SAS), component_matrix.py (prezzi per fascia/scaglione),
                       parametri_po.py (parametri del Portale), forward.py (indici variabili),
                       offerta_simulata.py (nuova offerta e posizionamento),
                       arera_tariffs.py (configurazione di riserva)
scripts/               update_daily, verifica_portale, rileva_*, rebuild_storico, diff_sas, crawler CTE
tests/                 suite pytest
data/                  raw, storage, processed, config (non versionati)
docs/                  documentazione
archive/               codice legacy non più importato (conservato per riferimento)
```

Dettaglio: [docs/struttura_progetto.md](docs/struttura_progetto.md). Architettura e flussi:
[docs/logica_progetto.md](docs/logica_progetto.md). Tracciato delle colonne:
[docs/guida_lettura_tracciato.md](docs/guida_lettura_tracciato.md).

## Note aziendali

- **SSL:** gli script `requests` usano `verify=False` per la SSL inspection dei proxy aziendali; i browser
  Playwright usano `ignore_https_errors`. In caso di timeout, verificare la VPN.
- **Configurazione manuale:** `data/config/arera_tariffs.json` è solo una riserva: in produzione i valori
  regolati arrivano dai parametri del Portale. Va modificato solo dopo aver verificato i valori.
