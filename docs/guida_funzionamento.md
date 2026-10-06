# Flusso Dati: Dal Portale Offerte al Database

Questo documento spiega in modo semplice e lineare come il sistema raccoglie, trasforma e salva i dati dal **Portale Offerte** ufficiale, permettendo di costruire il simulatore. È pensato per fornire una visione chiara a chiunque, anche a chi non ha familiarità con il mercato dell'energia o con la programmazione.

---

## 1. Cos'è il Portale Offerte?
Il Portale Offerte è un sito istituzionale (gestito dall'autorità ARERA) dove **tutti i fornitori di energia** (Enel, Eni, Engie, ecc.) sono obbligati per legge a pubblicare le loro offerte per il mercato libero. 

Ogni giorno, il Portale mette a disposizione dei file pubblici contenenti centinaia di migliaia di righe di dati. Il nostro sistema ha il compito di scaricarli in automatico, "digerirli" e trasformarli in un formato comodo per fare analisi e simulazioni di prezzo.

---

## 2. Il processo passo dopo passo (La Pipeline)

L'intero processo viene avviato da un singolo script "regista" chiamato `update_daily.py` (nella cartella `scripts`). Quando viene eseguito, orchestra 4 fasi principali:

### Fase A: Il Download (`download/downloader.py`)
Il sistema si collega ai server del Portale Offerte e scarica i file "grezzi" aggiornati.
I file sono in formato **XML** (un formato di testo strutturato, simile al codice di una pagina web, molto pesante e difficile da leggere per un umano).
*   **Cosa scarica?** Le offerte della Luce (E = Energia), del Gas (G) e quelle "Dual Fuel" (D = Luce + Gas insieme).
*   **I Parametri:** Oltre alle offerte, scarica anche un piccolo file che contiene i "Parametri" giornalieri stabiliti dall'Autorità (tasse, accise, costi di rete).

### Fase B: Il Parsing e l'Appiattimento (`parse/parser.py` e `flattener.py`)
I file XML sono enormi e nidificati (un'offerta contiene fasce di prezzo, che contengono sconti, che contengono regioni...). Se li aprissimo su Excel, il computer si bloccherebbe.
*   **Lettura intelligente (Streaming):** Il `parser.py` legge il file un pezzettino alla volta per non saturare la memoria.
*   **Il Flattener (Lo "Schiacciasassi"):** Il modulo `flattener.py` prende questi dati annidati e li "schiaccia". Trasforma l'albero complesso di ogni offerta in **una singola riga di una tabella**, mettendo le informazioni in colonne separate (es. colonna "Prezzo Giorno", colonna "Prezzo Notte"). Se un'offerta è valida in più regioni, i nomi delle regioni vengono uniti con una barra verticale (es. `Lombardia|Veneto`).

### Fase C: I Dati di Mercato (`download/gme.py`)
Per le offerte a prezzo variabile (che cambiano in base alla borsa elettrica), il sistema si collega al **GME** (Gestore Mercati Energetici) e scarica le quotazioni "Forward", ovvero le stime di quanto costerà l'energia nei prossimi 12 mesi.

### Fase D: Salvataggio nel Database (`storage/daily_store.py`)
Tutte queste righe schiacciate vengono salvate nel disco del computer (nella cartella `data/storage/storico/`). 
*   **Il Formato Parquet:** Non usiamo Excel o CSV, ma un formato ultra-veloce e compresso chiamato **Parquet**. Leggere un file Parquet da 100 milioni di righe richiede frazioni di secondo, a differenza di Excel che andrebbe in blocco.
*   **Organizzazione in archivi (Partizionamento):** I dati non vengono buttati in un unico calderone, ma archiviati ordinatamente per Mese e per Tipo (es. `cartella E -> cartella 2026 -> file 2026-10.parquet`). Se ri-scarichiamo i dati di oggi, il sistema sa esattamente in quale scatola infilarli senza dover rileggere gli anni passati.

---

## 3. Dizionario dell'Energia (Cosa significano i dati?)

Quando si apre la tabella finale sull'App, si trovano molte colonne tecniche. Ecco cosa significano le voci principali in linguaggio "umano":

### Informazioni di base dell'offerta
*   **`Venditore`**: Il nome della compagnia che vende la luce o il gas (es. Enel, Plenitude, Engie).
*   **`Codice Offerta`**: Un codice alfanumerico univoco che identifica quell'offerta specifica (è come la targa dell'offerta, assegnata dallo Stato).
*   **`Tipo` (Fisso o Variabile)**:
    *   **Fisso:** Il prezzo della materia prima è bloccato e garantito per 12 o 24 mesi.
    *   **Variabile (Indicizzato):** Il prezzo cambia ogni mese in base agli andamenti del mercato all'ingrosso.

### I Costi (Il Prezzo dell'Energia)
*   **`Quota Fissa` (PCV per la luce / QVD per il gas)**: È l'abbonamento mensile/annuale. Un costo fisso in Euro che il cliente paga a prescindere da quanto consuma (come il canone della linea telefonica).
*   **`Prezzo Energia` / `Spread`**: Il costo dell'energia pura consumata.
    *   Nelle offerte **Fisse**, è un numero deciso dal fornitore (es. 0,12 € per ogni kWh di luce).
    *   Nelle offerte **Variabili**, il fornitore non decide il prezzo totale, ma ti fa pagare il costo di borsa (PUN o PSV) più un suo margine di guadagno (chiamato **Spread** o *Fee*). Se lo Spread è 0,02, pagherai il costo all'ingrosso + 2 centesimi di ricarico.
*   **`Fasce (F1, F2, F3)`**: Esistono solo per la luce. F1 è il giorno lavorativo (costa di più). F2 e F3 sono la sera, la notte e i weekend. Molte offerte oggi sono "Monorarie" (stesso prezzo a tutte le ore, indicate senza fascia).

### Gli Indici di Borsa (Le "Materie Prime")
*   **PUN (Prezzo Unico Nazionale)**: Il costo all'ingrosso della Luce in Italia.
*   **PSV (Punto di Scambio Virtuale)**: Il costo all'ingrosso del Gas in Italia.

### La Bolletta Totale
*   **`SAS` (Spesa Annua Stimata)**: È il numero più importante. È una simulazione ufficiale di **quanto spenderebbe un cliente in 12 mesi** con quell'offerta, inclusi: abbonamento, prezzo energia, spread, tasse statali (Accise/IVA) e costi di Rete/Trasporto (i costi per far arrivare fisicamente il tubo o il filo a casa). 
*   **Il Motore di Calcolo (`sas_calculator_fast.py`)**: È il cuore matematico del nostro simulatore. Prende i dati dell'offerta, legge le tasse statali, e ricrea esattamente le formule matematiche legali dell'Autorità per calcolare la Spesa Annua Stimata spaccata al singolo centesimo.
