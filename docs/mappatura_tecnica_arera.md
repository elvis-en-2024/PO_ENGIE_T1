# Mappatura e Dizionario Dati: Da XML ARERA a Parquet

Questa guida è un riferimento 1:1, di livello tecnico, che spiega esplicitamente come i file XML crudi scaricati dal **Portale Offerte (ARERA/SII)** vengono tradotti e appiattiti nel nostro database analitico in formato **Parquet**.

Ogni colonna del file Parquet è frutto di un'estrazione precisa dal tracciato XML ufficiale. Poiché l'XML di ARERA ha una struttura gerarchica ad albero (molto nidificata), il nostro motore (`parse/flattener.py`) si occupa di "appiattirlo", generando un record unico per ogni singola offerta, e posizionando gli elementi multipli (come le Fasce o gli Sconti) in colonne numerate (es. SCONTO_1, SCONTO_2).

---

## 1. Regole generali di appiattimento (Flattener)

- **Unicità del Record:** Ogni riga nel file Parquet rappresenta una singola offerta (identificata in modo univoco da `PIVA_UTENTE` + `COD_OFFERTA`).
- **Gestione Vettori:** Quando un nodo XML può ripetersi (es. un'offerta ha 3 Sconti), il sistema crea colonne incrementali: `SCONTO_1_NOME`, `SCONTO_2_NOME`, ecc.
- **Join Condizionale:** Quando un nodo può avere più valori (es. un'offerta è disponibile in 5 Regioni diverse), i valori vengono estratti, decodificati e concatenati con il carattere `|` (es. `Lombardia|Veneto|Lazio`), permettendo query rapide in SQL/DuckDB tramite clausole `LIKE '%Lombardia%'`.
- **Decodifica Tabelle ARERA:** I codici incomprensibili (es. TIPO_MERCATO = `01`) vengono automaticamente tradotti nei nomi parlanti ufficiali ARERA (es. `Libero`) tramite dizionari interni (`DECODE_MAPS`).

---

## 2. Dizionario delle Colonne e Mappatura 1:1

Qui di seguito l'elenco completo dei campi che si trovano nel file Parquet (`storico_2026_full.parquet`), con l'origine XML e il significato di business.

### A. Anagrafica e Identificativi (Nodo: `IdentificativiOfferta`)

| Colonna Parquet | Nodo XML Originale (XPath) | Significato / Dizionario Energy |
| :--- | :--- | :--- |
| **`commodity`** | (Dalla cartella/file) | Il tipo di fornitura. Valori: `E` (Energia Elettrica), `G` (Gas Naturale), `D` (Dual Fuel, entrambe). |
| **`PIVA_UTENTE`** | `IdentificativiOfferta/PIVA_UTENTE` | La Partita IVA della società di vendita (es. Enel, Engie). Viene usata come ID primario del venditore. |
| **`COD_OFFERTA`** | `IdentificativiOfferta/COD_OFFERTA` | Il Codice Identificativo Univoco dell'offerta (assegnato secondo le regole SII). Fondamentale per tracciare lo storico. |
| **`DATA_INIZIO`** | `Validita/DATA_INIZIO` | Data e ora di inizio validità commerciale dell'offerta. |
| **`DATA_FINE`** | `Validita/DATA_FINE` | Data e ora in cui l'offerta non è più sottoscrivibile dai nuovi clienti. |
| **`DATA_RILEVAZIONE`** | (Timestamp del download) | La data in cui il nostro sistema ha "fotografato" l'offerta sul Portale (es. `2026-10-06`). |

### B. Caratteristiche Commerciali (Nodo: `DettaglioOfferta`)

| Colonna Parquet | Nodo XML Originale | Significato / Dizionario Energy |
| :--- | :--- | :--- |
| **`TIPO_MERCATO`** | `DettaglioOfferta/TIPO_MERCATO` | Indica se l'offerta è del Mercato `Libero` o delle vecchie Tutele Graduali. |
| **`TIPO_CLIENTE`** | `DettaglioOfferta/TIPO_CLIENTE` | Target dell'offerta: `Domestico` (Famiglie) o `Non Domestico` (Aziende/PMI). Il nostro simulatore filtra per il Domestico. |
| **`DOMESTICO_RESIDENTE`** | `.../DOMESTICO_RESIDENTE` | Solo per luce: indica se è sottoscrivibile solo da residenti, solo da non residenti (es. seconda casa), o `Entrambi`. Le tariffe fisse statali (Oneri) cambiano drasticamente se non sei residente. |
| **`TIPO_OFFERTA`** | `DettaglioOfferta/TIPO_OFFERTA` | **Critico.** `Fisso` (prezzo energia bloccato per 12/24 mesi) o `Variabile` (prezzo energia che segue gli indici di borsa PUN/PSV mese per mese). |
| **`NOME_OFFERTA`** | `DettaglioOfferta/NOME_OFFERTA` | Nome commerciale dell'offerta (es. "Luce Special Green"). |
| **`DESCRIZIONE_OFFERTA`** | `DettaglioOfferta/DESCRIZIONE` | Testo di marketing e limitazioni. |
| **`DURATA`** | `DettaglioOfferta/DURATA` | In mesi, per quanti mesi sono garantite le condizioni economiche scritte nel contratto. |
| **`MODALITA_ATTIVAZIONE`** | `Filtri/MODALITA_ATTIVAZIONE` | Concatenato. Come si può firmare: `Web|Sportello|Telefono`. |

### C. Componenti di Prezzo (Nodo multiplo: `ComponentiImpresa/Componente`)
*Le componenti economiche fissate dal fornitore. L'XML può contenere decine di componenti. Il Flattener crea colonne `COMP_IMP_1_*`, `COMP_IMP_2_*`, ecc. fino a un massimo di 60.*

| Colonna Parquet | Nodo XML Originale | Significato / Dizionario Energy |
| :--- | :--- | :--- |
| **`COMP_IMP_n_NOME`** | `Componente/NOME` | Es: "Quota Energia", "Corrispettivo di commercializzazione", "Spread". |
| **`COMP_IMP_n_TIPOLOGIA`** | `Componente/TIPOLOGIA` | Indica se questo costo si paga "a contatore" in base al consumo (`Quota Energia`), o è un abbonamento fisso (`Quota Fissa`), o si paga sulla potenza impegnata (`Quota Potenza`). |
| **`COMP_IMP_n_MACROAREA`** | `Componente/MACROAREA` | Codice che identifica la famiglia di costo. Quelli che impattano la concorrenza sono tipicamente "Materia Prima" o "Commercializzazione". |

*(All'interno di ogni componente, possono esserci più Fasce di prezzo: `IntervalloPrezzi`)*
| Colonna Parquet | Nodo XML Originale | Significato / Dizionario Energy |
| :--- | :--- | :--- |
| **`COMP_IMP_n_INT_m_FASCIA`** | `IntervalloPrezzi/FASCIA_COMPONENTE` | Luce: `F1` (Giorno), `F2` (Sera/Sabato), `F3` (Notte/Festivi), `F23` (F2+F3 accorpate). Per Monorarie e Gas è assente. |
| **`COMP_IMP_n_INT_m_PREZZO`** | `IntervalloPrezzi/PREZZO` | Il valore in Euro puro. È il prezzo dell'energia per la fissa, o lo Spread/Fee per la variabile. |
| **`COMP_IMP_n_INT_m_UNITA`** | `IntervalloPrezzi/UNITA_MISURA` | Unità di misura: `Euro/kWh` (Energia elettrica), `Euro/Smc` (Standard Metro Cubo, Gas), `Euro/Anno` (Quote fisse). |

### D. Sconti (Nodo multiplo: `Sconti/Sconto`)
*Gli sconti vengono processati linearmente. `SCONTO_1_*`, `SCONTO_2_*` fino a 15.*

| Colonna Parquet | Nodo XML Originale | Significato / Dizionario Energy |
| :--- | :--- | :--- |
| **`SCONTO_n_NOME`** | `Sconto/NOME` | Es. "Sconto domiciliazione bancaria", "Bonus Benvenuto". |
| **`SCONTO_n_TIPOLOGIA`** | `Sconto/TIPOLOGIA` | Indica se lo sconto è `Fisso` (es. -20€ una tantum sulla prima bolletta) o `Percentuale` (es. -10% sul prezzo energia). |
| **`SCONTO_n_RICORRENTE`** | `Sconto/SCONTO_RICORRENTE` | Boolean. Indica se lo sconto vale per sempre o sparisce dopo il primo anno. Molte offerte hanno sconti "civetta" non ricorrenti per scalare i comparatori. |
| **`SCONTO_n_VALORE`** | `Sconto/IntervalloSconto/VALORE` | L'ammontare dello sconto (es. 20.0, o 10.0 se percentuale). |

### E. Dettagli Indicizzazione (Variabile) (Nodo: `ParametriVariabilita`)
*Questi campi sono compilati SOLO per le offerte `TIPO_OFFERTA = Variabile`. Il flattener li estrae per capire che formula matematica usa il venditore.*

| Colonna Parquet | Nodo XML Originale | Significato / Dizionario Energy |
| :--- | :--- | :--- |
| **`INDICE_RIF`** | `ParametriVariabilita/INDICE_RIFERIMENTO` | Quale Borsa usa. Per la luce è il `PUN`, per il gas è il `PSV` (raramente TTF). |
| **`MOLTIPLICATORE`** | `ParametriVariabilita/MOLTIPLICATORE` | Alcune offerte moltiplicano la borsa per un fattore di rischio (es. PUN * 1,1). (Corrisponde al "lambda" nelle nostre formule). |
| **`VALORE_MAX` (Cap)** | `ParametriVariabilita/VALORE_MAX_PREZZO` | Una clausola di sicurezza (Cap). Se l'energia in borsa esplode, il cliente non pagherà mai più di questo valore. |

### F. Geometria di Vendita (Filtri)

| Colonna Parquet | Nodo XML Originale | Significato / Dizionario Energy |
| :--- | :--- | :--- |
| **`REGIONE`** | `Filtri/CoperturaTerritoriale/REGIONE` | Concatenato. Quali regioni possono sottoscrivere. Es. `Lombardia|Piemonte`. |
| **`CAP_INCLUSI`** | `Filtri/CoperturaTerritoriale/CAP` | Se l'offerta è ultra-locale, contiene i CAP espliciti (es. `20121|20122`). |
| **`FASCIA_POTENZA`** | `Filtri/FasciaPotenza` | Luce. Potenze permesse (es. fino a 3kW, o >3kW). |
| **`CONSUMO_MAX`** | `Filtri/ConsumoMax` | Se il venditore rifiuta clienti altospendenti, fissa un tetto massimo (es. 5000 kWh/anno). |

---

## 3. Come il Simulatore usa questi Dati (`engine/sas_calculator_fast.py`)

Per passare da questo mega-database alla **Tabella Finale** che vede l'utente, interviene il nostro motore. Il motore fa questo ragionamento per ogni singola offerta (riga del parquet):
1. Cerca nella riga tutte le colonne `COMP_IMP_*_TIPOLOGIA = Quota Fissa` e le somma. Trova la **Quota Fissa**.
2. Cerca le colonne `Quota Energia` e legge i prezzi/spread. Se l'offerta è **Variabile**, va a pescare la nostra simulazione GME (il Forward) del PUN/PSV e lo addiziona allo spread. Trova il **Prezzo Energia**.
3. Cerca tutte le colonne `SCONTO_*` che si applicano al caso specifico e calcola il totale in Euro. Trova lo **Sconto**.
4. Aggiunge i **Parametri Regolati ARERA** (Distribuzione, Trasporto, Oneri di Sistema ASOS e ARIM), che abbiamo scaricato separatamente in `data/raw/parametri/`.
5. Calcola le **Accise** statali (che cambiano se il gas è usato al Sud o al Nord Italia, o se la luce è usata da residenti con consumo superiore a 1800 kWh).
6. Applica l'**IVA** (10% per usi civili normali, o 22% sul gas oltre i 480 Smc).
7. Somma tutto. Il risultato è la **SAS (Spesa Annua Stimata)** finale che compare a video.

Questo intero processo matematico viene vettorializzato, permettendo l'analisi e il ranking di tutto il database nazionale in meno di mezzo secondo.
