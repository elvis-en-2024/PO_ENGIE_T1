# Guida Completa all'Architettura e al Flusso Dati del Simulatore

Questa guida è un documento di approfondimento tecnico e funzionale. Ha lo scopo di spiegare in modo esaustivo, passo dopo passo e senza dare nulla per scontato, come funziona l'intero "motore" che alimenta la nostra applicazione: dal momento in cui i dati vengono messi a disposizione dall'Autorità, fino a quando compaiono sulla nostra tabella finale. 

È una guida pensata per permettere a partner, stakeholder e futuri sviluppatori (anche esterni al mondo dell'energia) di comprendere la solidità, la scalabilità e la logica ingegneristica dell'intero progetto.

---

## 1. Il Contesto: Il Portale Offerte ARERA

In Italia, il mercato dell'energia (Luce e Gas) è parzialmente liberalizzato. Per garantire trasparenza, l'ARERA (L'Autorità di Regolazione per Energia Reti e Ambiente) ha istituito il **Portale Offerte**. 
Tutti i venditori di energia del mercato libero (es. Enel, Plenitude, Engie, A2A, ecc.) hanno l'obbligo di legge di caricare su questo portale le caratteristiche economiche di **tutte** le loro offerte commerciali destinate ai clienti domestici e alle piccole imprese.

Il Portale mette a disposizione del pubblico questi dati in modalità "Open Data". Ogni giorno vengono pubblicati enormi archivi contenenti le "fotografie" di tutte le offerte valide. Il nostro software si innesta esattamente qui: preleva automaticamente queste fotografie, le processa e permette di simulare scenari di mercato e competitività.

---

## 2. Il Flusso Dati (Data Pipeline): Passo per Passo

Il sistema non è un semplice "lettore di file", ma una vera e propria pipeline di Ingegneria dei Dati (*Data Engineering*). L'orchestrazione di tutto il processo è affidata allo script `scripts/update_daily.py`, che viene eseguito ogni mattina. 

Ecco i 4 step fondamentali che compie la pipeline.

### STEP 1: Il Download Automatico (`download/downloader.py`)
Il primo scoglio tecnico è reperire i dati. Il Portale non fornisce un Database a cui connettersi, ma pubblica dei file zippati in formato **XML** (eXtensible Markup Language).
1. **Scarico delle Offerte (XML):** Lo script si collega al sito istituzionale e scarica i file contenenti le offerte per tre categorie:
   - **E (Energia Elettrica)**
   - **G (Gas Naturale)**
   - **D (Dual Fuel - Luce e Gas venduti insieme)**
2. **Scarico dei Parametri ARERA:** Oltre alle offerte private, il software scarica anche i file "Parametri". Questi file contengono tutte le tasse, gli oneri di sistema, i costi di trasporto e le regole di calcolo aggiornate fissate dallo Stato. Senza questi parametri, non potremmo calcolare la bolletta finale.
3. **Robustezza:** Se per caso il server del Portale Offerte è offline o i file del giorno sono corrotti, il downloader se ne accorge, segnala l'errore e passa automaticamente a riutilizzare i dati del giorno precedente, garantendo che l'App non vada mai offline.

### STEP 2: Il Parsing Intelligente e lo "Schiacciamento" (`parse/parser.py` e `parse/flattener.py`)
I file XML scaricati sono giganteschi (spesso pesano centinaia di Megabyte) e hanno una struttura "ad albero" molto profonda e complessa. Ad esempio, una singola offerta contiene dei nodi per i prezzi, che contengono nodi per le fasce orarie, che contengono nodi per gli sconti, che a loro volta contengono nodi per le regioni di validità.

*   **Il Problema della Memoria (Parsing in Streaming):** Se provassimo ad aprire questo file XML caricandolo interamente nella RAM del computer (come farebbe Excel), il server andrebbe in blocco (Out of Memory). Per risolvere questo problema, il `parser.py` utilizza una tecnica chiamata **Streaming Iterativo** (tramite la libreria `lxml.iterparse`). In parole povere, legge il file "riga per riga", estrae i dati di un'offerta, li salva, e poi "dimentica" quella parte di file, mantenendo il consumo di memoria vicinissimo allo zero.
*   **Il Flattener (L'Appiattimento):** Una volta estratto l'albero di una singola offerta, interviene il `flattener.py`. Il suo scopo è prendere questo albero complesso e "schiacciarlo" (flatten) in una normalissima riga di tabella (una per ogni offerta). 
    *   *Come gestisce le eccezioni?* Se un'offerta è valida in più regioni (es. Lombardia e Veneto), invece di creare due righe duplicate, il flattener unisce i nomi con una barra verticale (`Lombardia|Veneto`). Se un'offerta ha più sconti, li somma o li concatena logicamente. Il risultato finale è una tabella pulita e rigorosa.

### STEP 3: L'Integrazione dei Dati di Borsa (`download/gme.py`)
Per valutare le offerte a "Prezzo Variabile" (che non hanno un prezzo fisso deciso a tavolino, ma seguono l'andamento del mercato), non bastano i dati del Portale. 
Il sistema si collega ai server del **GME (Gestore Mercati Energetici)**, ovvero la "Borsa" italiana dell'energia. Da qui scarica le stime ("Forward") su quanto costerà l'energia nei prossimi 12 mesi. Questo permette al nostro simulatore di prevedere in modo realistico quanto pagherà il cliente in futuro.

### STEP 4: Il Salvataggio e l'Archiviazione Scalabile (`storage/daily_store.py`)
Dopo che migliaia di offerte sono state appiattite e arricchite con i dati di borsa, devono essere salvate.
1. **Il Formato Parquet:** Abbandoniamo completamente formati lenti e pesanti come CSV o Excel. I dati vengono convertiti nel formato **Apache Parquet**. È un formato "colonnare", super-compresso e utilizzato dai Big Data. Un file che in Excel peserebbe 150 MB, in Parquet pesa 15 MB e viene letto dal sistema in frazioni di millisecondo.
2. **Il Partizionamento dello Storico:** Per rendere il sistema ultra-veloce e scalabile negli anni, i dati non vengono inseriti in un singolo file gigante. Vengono divisi (partizionati) in cartelle sul disco. Il percorso (Layout) è strutturato così: `data/storage/storico/commodity=Luce/anno=2026/2026-10.parquet`.
   In questo modo, se l'utente vuole analizzare solo l'ultimo mese, il sistema caricherà in memoria solo quel micro-file, ignorando completamente anni di storico inutile.

---

## 3. Il Dizionario dell'Energia: Cosa significano i campi?

Per chi non mastica l'energia, il mercato può sembrare un labirinto di sigle. Ecco un dizionario "a prova di idiota" per capire esattamente cosa stiamo calcolando e cosa rappresentano le colonne finali nell'applicazione.

### Informazioni Identificative
*   **`VENDITORE`**: La compagnia energetica vera e propria (Enel, A2A, Iren, ecc.).
*   **`COD_OFFERTA`**: Un codice lungo e illeggibile (es. `012345ESFML0102...`). È la "Targa" dell'offerta, l'unico modo per essere sicuri che stiamo parlando esattamente dello stesso contratto, visto che i venditori tendono a usare nomi commerciali molto simili tra loro (es. "Luce Special", "Luce Special Plus").
*   **`Commodity`**: La materia venduta. **E** sta per Energia Elettrica, **G** sta per Gas Naturale.

### La Struttura dei Prezzi
Le bollette sono composte da due voci fondamentali dettate dal venditore:
1.  **Quota Fissa (`QUOTA_FISSA` / PCV / QVD)**: È l'abbonamento. Si paga in *Euro all'anno*. Che tu tenga le luci sempre accese o la casa vuota e al buio, questo costo lo paghi sempre. Di solito oscilla tra i 60€ e i 150€ all'anno.
2.  **Prezzo dell'Energia (`PREZZO_UNITARIO`)**: È il costo al consumo. Si paga in *Euro per kWh* (Luce) o *Euro per Metro Cubo - Smc* (Gas). 
    L'offerta può essere di due Tipi:
    *   **Prezzo Fisso**: Il venditore fissa un costo (es. 0,15 €/kWh) e te lo garantisce invariato per 12 o 24 mesi.
    *   **Prezzo Variabile (Indicizzato)**: Il venditore ti dice: "Non so quanto costerà la luce domani. Ti farò pagare il prezzo esatto a cui io la compro all'ingrosso, più un mio piccolo ricarico per il disturbo". Questo ricarico si chiama **Spread** o Fee. (Es. *Prezzo all'ingrosso + 0,02 €/kWh di Spread*).

### Le "Fasce Orarie" (Solo per la Luce)
Il prezzo dell'energia elettrica può variare in base a *quando* la usi.
*   **F1 (Ore di Punta / Giorno)**: Dal Lunedì al Venerdì, dalle 8:00 alle 19:00. Storicamente costa di più.
*   **F2 e F3 (Sera e Weekend)**: La sera, la notte, i sabati e le domeniche.
Oggi, moltissime offerte sono "Monorarie", ovvero applichino un unico prezzo 24 ore su 24 (sulla tabella non avranno l'indicazione F1/F2).

### I Mercati all'Ingrosso (Gli Indici)
Nelle offerte Variabili abbiamo parlato del "prezzo all'ingrosso". Come si calcola?
*   **PUN (Prezzo Unico Nazionale)**: È la media aritmetica di quanto costa l'energia elettrica alla borsa italiana.
*   **PSV (Punto di Scambio Virtuale)**: È l'equivalente del PUN, ma per il mercato del Gas.
Il nostro software si occupa di fare le medie di questi indici usando le vere previsioni di Borsa (vedi Step 3).

### La Bolletta Totale e le Tasse
*   **Rete e Trasporto (`RETE`)**: Sono i costi che vanno pagati al distributore locale (chi possiede fisicamente i tubi sotto la strada o i cavi sui tralicci) per portare l'energia fino a casa. Sono uguali per tutti i venditori.
*   **Oneri di Sistema (`ONERI`)**: Sono tasse fisse governative per finanziare fonti rinnovabili, bonus sociali, smantellamento nucleare, ecc.
*   **Accise e IVA (`IMPOSTE`, `IVA`)**: Le tasse dirette dello Stato sui consumi.

### Il Numero Magico: La SAS (Spesa Annua Stimata)
Il parametro **`SAS`** è il fulcro di tutta l'applicazione. Se un utente consuma 2000 kWh all'anno, quanto spenderà IN TOTALE in 12 mesi con un'offerta?
La SAS non è una stima casuale. Il nostro modulo interno `engine/sas_calculator_fast.py` è un motore matematico potentissimo che calcola:
*(Quota Fissa) + (Consumo * Prezzo Energia) + (Sconti) + (Costi di Rete) + (Oneri) + (Accise) + (IVA)*.
Tutte queste formule ricalcano millimetricamente (al singolo decimale) le complesse leggi redatte dall'ARERA, per garantire che il posizionamento e il ranking delle offerte sull'App siano legali e inoppugnabili.

---

## 4. Perché questa architettura scala? (Per il Partner)

Da un punto di vista di business e ingegneristico, il sistema è costruito per scalare su volumi di dati altissimi:
1.  **Nessun database costoso:** Non stiamo pagando per mantenere istanze MySQL o PostgreSQL accese. L'uso dei file *Parquet* divisi per partizioni (Data Lake architecture) permette di archiviare GigaByte di storico a costo di archiviazione puro (quasi zero) leggendoli in maniera istantanea.
2.  **Motore di Calcolo Vettoriale (FastSASCalculator):** Invece di calcolare il prezzo di 100.000 offerte facendo 100.000 calcoli in fila (che richiederebbe svariati secondi o minuti), il motore è "vettorializzato" tramite la libreria Pandas. Esegue le moltiplicazioni matematiche in blocco direttamente sulla CPU, restituendo il calcolo di tutte le bollette nazionali in circa `0.2 secondi`.
3.  **Deploy Agnostico (Streamlit):** L'interfaccia non richiede complessi server web. È totalmente basata su Python e Streamlit, il che significa che può girare indistintamente dal laptop di uno sviluppatore fino ai cluster cloud gestiti, con zero configurazione di rete necessaria.
