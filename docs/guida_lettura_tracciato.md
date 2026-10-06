# MANUALE OPERATIVO E TRACCIATO RECORD OFFERTE (A PROVA DI ERRORE)
Questo documento contiene **ogni singolo dettaglio** necessario per interpretare e importare il file Parquet contenente le offerte energetiche. Qualsiasi sviluppatore o analista, anche senza esperienza nel settore energia, deve seguire queste indicazioni per evitare errori.

## PARTE 1: LA LOGICA STRUTTURALE (IL "FLATTENING")
I dati originari del Sistema Informativo Integrato (SII) sono in formato XML gerarchico. Poiché il Parquet è una tabella piatta (righe e colonne), abbiamo applicato un processo di **flattening**.

### Cosa significa per lo sviluppatore?
- Quando un'offerta ha **più componenti di prezzo** (es. Quota Fissa e Quota Energia), nel Parquet non c'è una sola colonna 'PREZZO', ma ci saranno colonne numerate come `COMP_IMP_1_...`, `COMP_IMP_2_...` fino al numero massimo di componenti riscontrate.
- Quando un'offerta ha **più sconti**, troverete `SCONTO_1_...`, `SCONTO_2_...`.
- Quando una componente varia nel tempo (es. prezzo scontato il primo anno, prezzo pieno il secondo), troverete l'indicatore dell'intervallo: `_INT_1_`, `_INT_2_`.

La logica che segue per i campi ripetitivi (`COMP_IMP`, `SCONTO`, `COND`) va quindi applicata aggiungendo il suffisso numerico desiderato. I campi vuoti (NULL) indicano semplicemente che quell'offerta non ha un 2°, 3° o N° sconto/componente.

### Colonne prodotte dal flattener (`parse/flattener.py`, aggiornato a ottobre 2026)

| Gruppo | Colonne | Note |
|---|---|---|
| Zone | `REGIONE`, `PROVINCIA`, `COMUNE` | tutti i codici ISTAT dell'offerta separati da `\|` (es. `03\|05`); vuoto = tutta Italia |
| Componenti impresa | `COMP_IMP_{c}_NOME`, `_DESCRIZIONE`, `_TIPOLOGIA` (+ `_TIPOLOGIA_COD`), `_MACROAREA` (+ `_MACROAREA_COD`) | `c` = 1…60. Lo schema è dinamico: esistono solo le colonne dei nodi presenti nel file |
| Intervalli di prezzo | `COMP_IMP_{c}_INT_{i}_FASCIA`, `_CONSUMO_DA`, `_CONSUMO_A`, `_PREZZO`, `_UNITA`, `_TIPO_PREZZO`, `_VALIDO_FINO`, `_DURATA` | `i` = 1…10. Lo storico vecchio usava `_CONS_DA/_CONS_A`: il motore legge entrambi |
| Sconti | `SCONTO_{s}_NOME`, `_CODICE_COMP`, `_VALIDITA`, `_IVA`, `_DURATA`, `_VALIDO_FINO`, `_MESE_VALIDITA`, `_COND_APP` | `s` = 1…15 |
| Prezzi sconto | `SCONTO_{s}_PREZZO_{p}_TIPO`, `_VAL`, `_UNITA`, `_DA`, `_FINO` | `p` = 1…5; `_DA/_FINO` = scaglione di consumo (0/0 = tutto) |
| Dispacciamento | `DISP_<voce>` (bool), `DISP_<voce>_VALORE` | voci: `TIDE`, `PD`, `Cod_03`…`Cod_08`, `Capacita_STG`, `Capacita_MT`, `Salvaguardia`, `Tutele_Graduali`, `DispBT`, `CdispD`, `Altro` |
| Componenti regolate | `REGOLATA_<nome>` (bool) | `PCV`, `PPE`, `CCR`, `CPR`, `GRAD`, `QTint`, `QTpsv`, `QVD_Fissa`, `QVD_Variabile` |
| Indici | `IDX_<nome>` (bool), `IDX_<nome>_COEFF` | `PUN_Trim`, `TTF_Trim`, `PSV_Trim`, `PUN_Bim`, `TTF_Bim`, `PSV_Bim`, `Psbil_Bim`, `PE_Bim`, `Pfor_Bim`, `PUN_Men`, `TTF_Men`, `PSV_Men`, `Psbil_Men`, `Cmem_Men`, `Altro`. Il coefficiente pesa l'indice nella spesa |
| Condizioni | `COND_<tipo>` (bool), `COND_<tipo>_LIMITANTE` | `Attivazione`, `Disattivazione`, `Recesso`, `Pluriennale`, `Oneri_Recesso`, `Altro` |
| Servizi | `SERVIZIO_<macroarea>` (bool) | `Caldaia`, `Mobility`, `Solare`, `Fotovoltaico`, `Clima`, `Polizza`, `Altro` |
| Rilevazione | `DATA_RILEVAZIONE`, `commodity` | aggiunte in fase di parsing e storico: data del file, `E`/`G`/`D` |

Il significato di ogni campo nel calcolo della spesa è in `docs/guida_calcolo_sas.md`.

---
## PARTE 2: DIZIONARIO DETTAGLIATO DI TUTTI I CAMPI (TRACCIATO COMPLETO)
Di seguito l'elenco di **tutte le colonne** previste, divise per sezione logica. Per ogni campo viene spiegato cosa contiene, se è obbligatorio, e i valori ammessi (codifiche).

### Sezione: Identificativi Offerta
#### Campo: `PIVA_UTENTE`
- **Descrizione**: Partita IVA del Utente che richiede l'attivazione
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (16)

#### Campo: `COD_OFFERTA`
- **Descrizione**: Codice univoco per offerta presente sui sistemi del Venditore
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (32)

### Sezione: DettaglioOfferta
#### Campo: `TIPO_MERCATO`
- **Descrizione**: Definisce la commodity
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (2) - 01:Elettrico, 02:Gas, 03:Dual Fuel

#### Campo: `OFFERTA_SINGOLA`
- **Descrizione**: Indica se Ã¨ un'offerta puÃ² essere sottoscritta singolarmente
- **Obbligatorio**: SI (se TIPO_MERCATO diverso da 03)
- **Formato e Valori Ammessi**: Alfanumerico (2) - SI/NO

#### Campo: `TIPO_CLIENTE`
- **Descrizione**: Tipologia di cliente finale
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Numerico (2) 01:Domestico 02:Altri Usi 03: Condominio Uso Domestico (Gas)

#### Campo: `DOMESTICO_RESIDENTE`
- **Descrizione**: Indica se l'Utente Ã¨ domestico residente o no
- **Obbligatorio**: NO
- **Formato e Valori Ammessi**: Alfanumerico (2) - 01:Residente, 02:NON Residente, 03:Tutte

#### Campo: `TIPO_OFFERTA`
- **Descrizione**: Tipologia offerta inserita
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Numerico (2) - 01:Fisso, 02:Variabile, 03:FLAT

#### Campo: `TIPOLOGIA_ATT_CONTR`
- **Descrizione**: Casistiche in cui l'offerta si ritiene valida
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Numerico (2): 01: Cambio Fornitore 02: Prima Attivazione (Contatore non presente) 03: Riattivazione (Contatore presente ma disattivato) 04: Voltura 99: sempre

#### Campo: `NOME_OFFERTA`
- **Descrizione**: Nome dell'offerta
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (255)

#### Campo: `DESCRIZIONE`
- **Descrizione**: Descrizione estesa dell'offerta
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (3000)

#### Campo: `DURATA`
- **Descrizione**: Durata delle condizioni economiche in mesi
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Numerico (2) (se -1 = indeterminata)

#### Campo: `GARANZIE`
- **Descrizione**: Descrizione delle garanzie previste dal contratto
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (3000)

### Sezione: DettaglioOfferta/ModalitaAttivazione
#### Campo: `MODALITA`
- **Descrizione**: ModalitÃ  di attivazione dell'offerta
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (2) 01: Offerta attivabile solo da web 02: Offerta attivabile da qualsiasi canale 03: Presso punto vendita 04: Teleselling 05:Agenzia 99:Altro

#### Campo: `DESCRIZIONE`
- **Descrizione**: Descrizione della modalitÃ  di attivazione
- **Obbligatorio**: SI (se MODALITA =99)
- **Formato e Valori Ammessi**: Alfanumerico (2000)

### Sezione: DettaglioOfferta/Contatti
#### Campo: `TELEFONO`
- **Descrizione**: Recapito telefonico per contattare l'impresa
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (15)

#### Campo: `URL_SITO_VENDITORE`
- **Descrizione**: Sito web del venditore
- **Obbligatorio**: SI (se disponibile)
- **Formato e Valori Ammessi**: Alfanumerico (100)

#### Campo: `URL_OFFERTA`
- **Descrizione**: Pagina web dell'offerta del venditore
- **Obbligatorio**: SI (se disponibile)
- **Formato e Valori Ammessi**: Alfanumerico (100)

### Sezione: RiferimentiPrezzoEnergia
#### Campo: `IDX_PREZZO_ENERGIA`
- **Descrizione**: Indice di riferimento per il calcolo del prezzo energia
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Numerico (2) PeriodicitÃ  trimestrale 01: PUN 02: TTF 03: PSV 04:Psbil 05: PE 06: Cmem 07: Pfor PeriodicitÃ  bimestrale 08: PUN 09: TTF 10: PSV 11: Psbil PeriodicitÃ  mensile 12: PUN 13: TTF 14: PSV 15: Psbil 99: Altro

#### Campo: `ALTRO`
- **Descrizione**: Descrizione indice personalizzato
- **Obbligatorio**: SI (se IDX_PREZZO_ENERGIA='99')
- **Formato e Valori Ammessi**: Alfanumerico (3000)

### Sezione: ValiditaOfferta
#### Campo: `DATA_INIZIO`
- **Descrizione**: Data inizio validitÃ  offerta
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: GG/MM/AAAA_HH:MM:SS

#### Campo: `DATA_FINE`
- **Descrizione**: Data fine validitÃ  offerta
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: GG/MM/AAAA_HH:MM:SS

### Sezione: CaratteristicheOfferta
#### Campo: `CONSUMO_MIN`
- **Descrizione**: Soglia minima di consumo annuo
- **Obbligatorio**: SI (se TIPO_OFFERTA=03)
- **Formato e Valori Ammessi**: Numerico (9)

#### Campo: `CONSUMO_MAX`
- **Descrizione**: Soglia massima di consumo annuo
- **Obbligatorio**: SI (se TIPO_OFFERTA=03)
- **Formato e Valori Ammessi**: Numerico (9)

#### Campo: `POTENZA_MIN`
- **Descrizione**: Soglia minima di potenza impegnata (kW)
- **Obbligatorio**: NO
- **Formato e Valori Ammessi**: Numerico (2,1)

#### Campo: `POTENZA_MAX`
- **Descrizione**: Soglia massima di potenza impegnata (kW)
- **Obbligatorio**: NO
- **Formato e Valori Ammessi**: Numerico (2,1)

### Sezione: OffertaDUAL
#### Campo: `OFFERTE_CONGIUNTE_EE`
- **Descrizione**: Lista ID offerte congiunte elettriche
- **Obbligatorio**: SI (se TIPO_MERCATO =03)
- **Formato e Valori Ammessi**: Alfanumerico (32)

#### Campo: `OFFERTE_CONGIUNTE_GAS`
- **Descrizione**: Lista ID offerte congiunte gas
- **Obbligatorio**: SI (se TIPO_MERCATO = 03)
- **Formato e Valori Ammessi**: Alfanumerico (32)

### Sezione: MetodoPagamento
#### Campo: `MODALITA_PAGAMENTO`
- **Descrizione**: Tipologie di pagamento associate all'offerta
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (2) - 01:Dom.bancaria, 02:Dom.postale, 03:Carta credito, 04:Bollettino, 99:Altro

#### Campo: `DESCRIZIONE`
- **Descrizione**: Descrizione modalitÃ  pagamento personalizzata
- **Obbligatorio**: SI (se MODALITA_PAGAMENTO=99)
- **Formato e Valori Ammessi**: Alfanumerico (25)

### Sezione: ComponentiRegolate
#### Campo: `CODICE`
- **Descrizione**: Componente definita dall'autoritÃ
- **Obbligatorio**: NO
- **Formato e Valori Ammessi**: Alfanumerico (02) Valori TIPO MERCATO = 01: 01:PCV 02:PPE Valori TIPO MERCATO = 02: 03:CCR, 04:CPR, 05:GRAD, 06:QTint, 07:QTpsv, 09:QVD_fissa, 10:QVD_Variabile

### Sezione: TipoPrezzo
#### Campo: `TIPOLOGIA_FASCE`
- **Descrizione**: Fasce per cui Ã¨ dedicata l'offerta
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (2): 01: monorario 02: F1, F2 03: F1, F2, F3 04: F1, F2, F3,F4 05: F1, F2, F3, F4, F5 06: F1, F2, F3, F4, F5, F6 07: Peak/OffPeak 91: ""biorario (F1 / F2+F3)"" 92: ""biorario (F2 /F1+F3)"" 93: ""biorario (F3 / F1+F2)""

### Sezione: FasceOrarieSettimanale
#### Campo: `F_LUNEDI`
- **Descrizione**: Fasce orarie per il lunedÃ¬
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (49) Formato XX-Y,XX-YII,..,XXN-YN con XX (numerico da 1 a 96): ultimo quarto d'ora di applicazione della fascia Y (numerico da 1 a 8): numero della fascia applicata (7: Peak , 8: Offpeak) Devono essere sempre verificate le presenti relazioni: XXi+1>XXi N<=10 Es. F3: 00:01- 07:00 F2: 07:00 08:00 F1: 08:00 - 19:00 F2: 19:00 23:00 F3: 23:00 24:00 diventa: 28-3,32-2,76-1,92-2,96-3

#### Campo: `F_MARTEDI`
- **Descrizione**: Fasce orarie per il martedÃ¬
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (49) Formato XX-Y,XX-YII,..,XXN-YN con XX (numerico da 1 a 96): ultimo quarto d'ora di applicazione della fascia Y (numerico da 1 a 8): numero della fascia applicata (7: Peak , 8: Offpeak) Devono essere sempre verificate le presenti relazioni: XXi+1>XXi N<=10 Es. F3: 00:01- 07:00 F2: 07:00 08:00 F1: 08:00 - 19:00 F2: 19:00 23:00 F3: 23:00 24:00 diventa: 28-3,32-2,76-1,92-2,96-3

#### Campo: `F_MERCOLEDI`
- **Descrizione**: Fasce orarie per il mercoledÃ¬
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (49) Formato XX-Y,XX-YII,..,XXN-YN con XX (numerico da 1 a 96): ultimo quarto d'ora di applicazione della fascia Y (numerico da 1 a 8): numero della fascia applicata (7: Peak , 8: Offpeak) Devono essere sempre verificate le presenti relazioni: XXi+1>XXi N<=10 Es. F3: 00:01- 07:00 F2: 07:00 08:00 F1: 08:00 - 19:00 F2: 19:00 23:00 F3: 23:00 24:00 diventa: 28-3,32-2,76-1,92-2,96-3

#### Campo: `F_GIOVEDI`
- **Descrizione**: Fasce orarie per il giovedÃ¬
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (49) Formato XX-Y,XX-YII,..,XXN-YN con XX (numerico da 1 a 96): ultimo quarto d'ora di applicazione della fascia Y (numerico da 1 a 8): numero della fascia applicata (7: Peak , 8: Offpeak) Devono essere sempre verificate le presenti relazioni: XXi+1>XXi N<=10 Es. F3: 00:01- 07:00 F2: 07:00 08:00 F1: 08:00 - 19:00 F2: 19:00 23:00 F3: 23:00 24:00 diventa: 28-3,32-2,76-1,92-2,96-3

#### Campo: `F_VENERDI`
- **Descrizione**: Fasce orarie per il venerdÃ¬
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (49) Formato XX-Y,XX-YII,..,XXN-YN con XX (numerico da 1 a 96): ultimo quarto d'ora di applicazione della fascia Y (numerico da 1 a 8): numero della fascia applicata (7: Peak , 8: Offpeak) Devono essere sempre verificate le presenti relazioni: XXi+1>XXi N<=10 Es. F3: 00:01- 07:00 F2: 07:00 08:00 F1: 08:00 - 19:00 F2: 19:00 23:00 F3: 23:00 24:00 diventa: 28-3,32-2,76-1,92-2,96-3

#### Campo: `F_SABATO`
- **Descrizione**: Fasce orarie per il sabato
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (49) Formato XX-Y,XX-YII,..,XXN-YN con XX (numerico da 1 a 96): ultimo quarto d'ora di applicazione della fascia Y (numerico da 1 a 8): numero della fascia applicata (7: Peak , 8: Offpeak) Devono essere sempre verificate le presenti relazioni: XXi+1>XXi N<=10 Es. F3: 00:01- 07:00 F2: 07:00 08:00 F1: 08:00 - 19:00 F2: 19:00 23:00 F3: 23:00 24:00 diventa: 28-3,32-2,76-1,92-2,96-3

#### Campo: `F_DOMENICA`
- **Descrizione**: Fasce orarie per la domenica
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (49) Formato XX-Y,XX-YII,..,XXN-YN con XX (numerico da 1 a 96): ultimo quarto d'ora di applicazione della fascia Y (numerico da 1 a 8): numero della fascia applicata (7: Peak , 8: Offpeak) Devono essere sempre verificate le presenti relazioni: XXi+1>XXi N<=10 Es. F3: 00:01- 07:00 F2: 07:00 08:00 F1: 08:00 - 19:00 F2: 19:00 23:00 F3: 23:00 24:00 diventa: 28-3,32-2,76-1,92-2,96-3

#### Campo: `F_FESTIVITA`
- **Descrizione**: Fasce orarie per le festivitÃ
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (49) Formato XX-Y,XX-YII,..,XXN-YN con XX (numerico da 1 a 96): ultimo quarto d'ora di applicazione della fascia Y (numerico da 1 a 8): numero della fascia applicata (7: Peak , 8: Offpeak) Devono essere sempre verificate le presenti relazioni: XXi+1>XXi N<=10 Es. F3: 00:01- 07:00 F2: 07:00 08:00 F1: 08:00 - 19:00 F2: 19:00 23:00 F3: 23:00 24:00 diventa: 28-3,32-2,76-1,92-2,96-3

### Sezione: Dispacciamento
#### Campo: `TIPO_DISPACCIAMENTO`
- **Descrizione**: Componente applicata per il dispacciamento
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Numerico (2) | 01:Disp.del.111/06 | 02: PD | 03: MSD | 04: Modulazione Eolico | 05: UnitÃ  essenziali | 06: Funz. Terna | 07: CapacitÃ  Produttiva | 08:InterrompibilitÃ  | 09: Corrispettivo CapacitÃ  di Mercato STG | 10: Corrispettivo capacitÃ  di mercato MT | 11:Reintegrazione oneri salvaguardia | 12: Reintegrazione oneri tutele graduali | 13: DispBT11 | 99:Altro

#### Campo: `VALORE_DISP`
- **Descrizione**: Valore in â¬/Kwh
- **Obbligatorio**: SI (se TIPO_DISPACCIAMENTO=99)
- **Formato e Valori Ammessi**: Numerico (1,6) | Separatore â.â

#### Campo: `NOME`
- **Descrizione**: Nome della componente
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (25)

#### Campo: `DESCRIZIONE`
- **Descrizione**: Descrizione della componente
- **Obbligatorio**: NO
- **Formato e Valori Ammessi**: Alfanumerico (255)

### Sezione: ComponenteImpresa
#### Campo: `NOME`
- **Descrizione**: Nome della componente impresa
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (255)

#### Campo: `DESCRIZIONE`
- **Descrizione**: Descrizione della componente impresa
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (255)

#### Campo: `TIPOLOGIA`
- **Descrizione**: Tipologia della componente
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (2) - 01:STANDARD, 02:OPZIONALE

#### Campo: `MACROAREA`
- **Descrizione**: Macro area di prezzo coperte dalla componente
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Numerico (2) 01: Commercializzazione quota fissa 02:Commercializzazione quota energia 04: Prezzo quota energia 05: Una Tantum 06: FER/Energia Verde

### Sezione: ComponenteImpresa/IntervalloPrezzi
#### Campo: `FASCIA_COMPONENTE`
- **Descrizione**: Fascia impostata nel parametro TIPO_FASCE
- **Obbligatorio**: NO
- **Formato e Valori Ammessi**: Alfanumerico (2): 01:monorario/F1 02: F2 03: F3 04: F4 05: F5 06: F6 07: Peak 08: OffPeak 91: F2+F3 92: F1+F3 93: F1+F2

#### Campo: `CONSUMO_DA`
- **Descrizione**: Limite inferiore di consumi
- **Obbligatorio**: NO
- **Formato e Valori Ammessi**: Numerico(9)

#### Campo: `CONSUMO_A`
- **Descrizione**: Limite superiore dello scaglione
- **Obbligatorio**: NO
- **Formato e Valori Ammessi**: Numerico(9)

#### Campo: `PREZZO`
- **Descrizione**: Valore unitario della componente
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Numerico (6,6)

#### Campo: `UNITA_MISURA`
- **Descrizione**: UnitÃ  di misura del prezzo
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Numerico (2): 01:â¬Anno 02:CkW 03:â¬kWh 04:â¬Sm3 05:â¬

### Sezione: ComponenteImpresa/IntervalloPrezzi/PeriodoValidita
#### Campo: `DURATA`
- **Descrizione**: Indica il numero di mesi di validitÃ  dallâattivazione dellâofferta a cui Ã¨ applicato il prezzo. Es. 3 per i primi tre mesi dallâattivazione
- **Obbligatorio**: NO
- **Formato e Valori Ammessi**: Numerico(2)

#### Campo: `VALIDA_FINO`
- **Descrizione**: Indica il mese fino al quale il prezzo Ã¨ valido
- **Obbligatorio**: NO
- **Formato e Valori Ammessi**: MM/AAAA

#### Campo: `MESE_VALIDITA`
- **Descrizione**: Indica il mese solare di validitÃ  del prezzo.
- **Obbligatorio**: NO
- **Formato e Valori Ammessi**: Numerico(2) 01: Gennaio 02: Febbraio 03: Marzo 04: Aprile 05: Maggio 06: Giugno 07: Luglio 08: Agosto 09: Settembre 10: Ottobre 11: Novembre 12: Dicembre

### Sezione: CondizioniContrattuali
#### Campo: `TIPOLOGIA_CONDIZIONE`
- **Descrizione**: Tipologia di condizione contrattuale
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (2) 01: Attivazione 02: Disattivazione 03: Recesso 04: Offerta Pluriennale 05: Oneri di Recesso Anticipato 99: Altro

#### Campo: `ALTRO`
- **Descrizione**: Descrizione della tipologia di condizione contrattuale se il campo precedente Ã¨ valorizzato in modo generico âAltroâ
- **Obbligatorio**: SI (Se
TIPOLOGIA_CO
NDIZIONE
=â99â)
- **Formato e Valori Ammessi**: Alfanumerico (20)

#### Campo: `DESCRIZIONE`
- **Descrizione**: Descrizione della condizione contrattuale
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico(3000)

#### Campo: `LIMITANTE`
- **Descrizione**: Indica se la condizione Ã¨ limitante
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico | 01: Si, Ã¨ limitante | 02:No, non Ã¨ limitante

### Sezione: ZoneOfferta
#### Campo: `REGIONE`
- **Descrizione**: Elenco Codici Istat delle regioni in cui l'esercente propone l'offerta.
- **Obbligatorio**: NO
- **Formato e Valori Ammessi**: Alfanumerico (2) dove i singoli codici istat sono Numerico 2

#### Campo: `PROVINCIA`
- **Descrizione**: Elenco Codici Istat delle province in cui l'esercente propone l'offerta.
- **Obbligatorio**: NO
- **Formato e Valori Ammessi**: Alfanumerico (3) dove i singoli codici istat sono Numerico 3

#### Campo: `COMUNE`
- **Descrizione**: Elenco Codici Istat delle comuni in cui l'esercente propone l'offerta.
- **Obbligatorio**: NO
- **Formato e Valori Ammessi**: Alfanumerico (6) dove i singoli codici istat sono Numerico 6

### Sezione: Sconto
#### Campo: `NOME`
- **Descrizione**: Indica il nome dello sconto
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (255)

#### Campo: `DESCRIZIONE`
- **Descrizione**: Indica la descrizione dello sconto
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (3000)

#### Campo: `CODICE_COMPONENTE_FASCIA`
- **Descrizione**: Indica l'identificativo della ComponenteRegolata o della Fascia a cui si applica lo sconto (Componenti e Fasce non possono essere inserite contemporaneamente)
- **Obbligatorio**: NO
- **Formato e Valori Ammessi**: Alfanumerico (02) Componenti: 01:PCV 02:PPE 03:CCR, 04: CPR, 05:GRAD, 06:QTint, 07:QTpsv, 09:QVD_Fissa 10:QVD_Variabile Fasce: 11: F1 12: F2 13: F3 14: F4 15: F5 16: F6 17: Peak 18: (OffPeak 91=F2+F3 92=F1+F3 93=F1+F2)

#### Campo: `VALIDITA`
- **Descrizione**: Indica quando Ã¨ applicato lo sconto
- **Obbligatorio**: SI (se Sconto/PeriodoValidita non ha campi valorizzati)
- **Formato e Valori Ammessi**: Alfanumerico (2) 01: Ingresso 02: entro 12 mesi 03: oltre 12 mesi

#### Campo: `IVA_SCONTO`
- **Descrizione**: Indica se lo sconto Ã¨ soggetto ad IVA
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (2) 01:SI 02: NO

### Sezione: Sconto/Period
oValidita
#### Campo: `DURATA`
- **Descrizione**: Indica il numero di mesi di validitÃ  dall'attivazione dell'offerta a cui Ã¨ applicato il prezzo. Es. 3 per i primi tre mesi dall'attivazione
- **Obbligatorio**: NO
- **Formato e Valori Ammessi**: Numerico(2)

#### Campo: `VALIDO_FINO`
- **Descrizione**: Indica il mese fino al quale il prezzo Ã¨ valido
- **Obbligatorio**: NO
- **Formato e Valori Ammessi**: MM/AAAA

#### Campo: `MESE_VALIDITA`
- **Descrizione**: Indica il mese solare di validitÃ  del prezzo.
- **Obbligatorio**: NO
- **Formato e Valori Ammessi**: Numerico(2) | 01: Gennaio | 02: Febbraio | 03: Marzo | 04: Aprile | 05: Maggio | 06: Giugno | 07: Luglio | 08: Agosto | 09: Settembre | 10: Ottobre | 11: Novembre | 12: Dicembre

### Sezione: Sconto/Condizione
#### Campo: `CONDIZIONE APPLICAZIONE`
- **Descrizione**: Definisce se e quali condizioni definiscono l'applicazione dello sconto, sconti condizionati non concorrono al calcolo della spesa
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (2) 00: Non condizionato 01: Fatturazione elettronica 02: Gestione online 03: fatturazione elettronica+domiciliazione bancaria 99: Altro

#### Campo: `DESCRIZIONE CONDIZIONE`
- **Descrizione**: Descrive eventuali altre condizioni per l'applicazione dello sconto
- **Obbligatorio**: SI (Se CONDIZIONE_APPLICAZIONE=99)
- **Formato e Valori Ammessi**: Alfanumerico (3000)

### Sezione: Sconto/PREZZISconto
#### Campo: `TIPOLOGIA`
- **Descrizione**: Indica la tipologia di sconto applicato
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Numerico (2) 01: Sconto fisso 02: Sconto Potenza 03: Sconto Vendita 04: sconto su tutela

#### Campo: `VALIDO_DA`
- **Descrizione**: consumo annuo che costituisce il limite inferiore di consumo per il quale si intende definire il valore unitario dello sconto
- **Obbligatorio**: NO
- **Formato e Valori Ammessi**: Numerico (9)

#### Campo: `VALIDO_FINO`
- **Descrizione**: consumo annuo che costituisce il limite superiore dello scaglione (primo scaglione o scaglione unico) per il quale si intende definire il valore dello sconto
- **Obbligatorio**: NO
- **Formato e Valori Ammessi**: Numerico (9)

#### Campo: `UNITA MISURA`
- **Descrizione**: l'unitÃ  di misura del valore indicato nel campo ""Prezzo""
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Numerico (2) 01:CAnno 02:CkW 03:CkWh 04:CSm3 05:â¬ 06: Percentuale

#### Campo: `PREZZO`
- **Descrizione**: Prezzo applicato
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Numerico (6,6)

### Sezione: ProdottiServiziAggiuntivi
#### Campo: `NOME`
- **Descrizione**: Nome del prodotto o servizio aggiuntivo offerto
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (255)

#### Campo: `DETTAGLIO`
- **Descrizione**: Descrizione dettagliata del prodotto o servizio aggiuntivo offerto
- **Obbligatorio**: SI
- **Formato e Valori Ammessi**: Alfanumerico (3000)

#### Campo: `MACROAREA`
- **Descrizione**: Indica la macro area di interesse del servizio
- **Obbligatorio**: NO
- **Formato e Valori Ammessi**: Numerico (2) 01: Caldaia 02: Mobility 03: Solare termico 04: Fotovoltaico 05: Climatizzazione 06: Polizza assicurativa 99: Altro

#### Campo: `DETTAGLI_MACROAREA`
- **Descrizione**: Nessuna descrizione
- **Obbligatorio**: SI (se MACROAREA=99)
- **Formato e Valori Ammessi**: Alfanumerico (100)

---
## PARTE 3: GLOSSARIO DEI TERMINI ENERGETICI (PER NON ADDETTI AI LAVORI)
- **Commodity**: Il tipo di fornitura (01=Luce, 02=Gas).
- **PUN (Prezzo Unico Nazionale)**: Indice di borsa per l'energia elettrica. Le offerte a prezzo variabile di solito aggiungono un ricarico (Spread) al PUN.
- **PSV (Punto di Scambio Virtuale)**: Indice di borsa per il gas naturale. 
- **Quota Fissa / Commercializzazione (Macroarea 01)**: Importo in €/mese o €/anno fisso, indipendente dai consumi.
- **Quota Energia (Macroarea 04)**: Il prezzo pagato per la materia prima vera e propria (€/kWh o €/Smc).
- **Spread / Fee (Macroarea 04 in offerte Variabili)**: Il guadagno/ricarico del fornitore sopra l'indice di borsa (es. PUN + 0,02 €/kWh). L'indice è definito in `IDX_PREZZO_ENERGIA`, il valore numerico 0,02 in `_PREZZO`.
- **Dual Fuel**: Un'offerta in cui lo stesso fornitore vende sia Luce che Gas allo stesso cliente in un unico pacchetto.
- **Energia Verde / FER (Macroarea 06)**: Energia prodotta da Fonti Energetiche Rinnovabili. Nelle componenti di prezzo, se un'offerta ha l'opzione verde, troverete una componente dedicata con MACROAREA 06.
- **Fasce Orarie (F1, F2, F3)**: Applicabili solo alla Luce. F1 sono le ore di punta nei giorni lavorativi, F2/F3 le sere, i weekend e festivi.
- **Oneri di Recesso Anticipato (Codice 05 in TIPOLOGIA_CONDIZIONE)**: Penale economica applicata se il cliente abbandona il contratto prima della naturale scadenza.
