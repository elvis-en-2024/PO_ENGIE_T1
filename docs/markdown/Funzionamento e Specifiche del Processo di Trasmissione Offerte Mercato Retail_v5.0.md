SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

1/70

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS

FUNZIONAMENTO E SPECIFICHE DEL PROCESSO DI

TRASMISSIONE OFFERTE MERCATO RETAIL

 DELIBERAZIONE 848/2017/R/COM

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

2/70

Sommario
1  Glossario ................................................................................................................. 7

2

3

Contesto normativo ................................................................................................ 10

Scopo e contenuto del documento ............................................................................ 12

3.1

Riferimenti ...................................................................................................... 13

4

Registrazione degli Utenti al Processo ....................................................................... 14

5  Modello generale dei Processi di Trasmissione Offerte ................................................. 15

5.1

Modello generale del Processo di Trasmissione Offerte PLACET .............................. 16

Regole di prevalenza e validità delle offerte PLACET ...................................... 17

5.2

Modello generale Processo di trasmissione Offerte MERCATO LIBERO ..................... 20

Regole di prevalenza e validità delle offerte MERCATO LIBERO ........................ 21

Annullamento Trasmissione Offerta ............................................................. 29

6

Specifiche tecniche del Processo di Trasmissione Offerta ............................................. 30

6.1

Trasmissione offerta PLACET ............................................................................. 30

TO1.0050 - Trasmissione offerta EE ............................................................ 31

TO1.0100 – Ammissibilità offerta EE ............................................................ 35

TO1.0051 - Trasmissione offerta GAS .......................................................... 36

TO1.0101 - Ammissibilità offerta GAS .......................................................... 40

6.2

Trasmissione offerta MERCATO LIBERO .............................................................. 42

TO2.0050 - Trasmissione offerta ................................................................. 42

TO2.0100 – Ammissibilità offerta ................................................................ 44

TO2.0051 - Aggiornamento Offerta ............................................................. 45

TO2.0101 - Ammissibilità offerta ................................................................. 47

TO2.0052 - Elimina Offerta ........................................................................ 48

TO2.0102 - Ammissibilità offerta ................................................................. 49

7

Formato e tracciato delle Offerte .............................................................................. 51

7.1

7.2

Formato Offerta ............................................................................................... 52

Modalità di Trasmissione Offerte non simulabili .................................................... 63

Appendice .................................................................................................................... 66

A – Tabella di codifica delle inammissibilità ................................................................... 66

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

3/70

Tabella A.1 - Codici Inammissibilità .......................................................................... 66

Revisioni del documento

Versione

Data

Natura della Modifica

1.00

22/12/2017  Prima stesura del documento

1.00a

12/01/2018

Errata corrige:

•

•

su obbligatorietà del flusso TO1.0050 nei campi P_FIX_F,
P_FIX_V, ALPHA
su obbligatorietà del flusso TO1.0051 nei campi P_FIX_F,
P_FIX_V, ALPHA

Inseriti nuovi controlli di inammissibilità (512,513)

Errata corrige:

1.00b

31/01/2018

PVOL_B_F23 per flusso TO1.0050

•  Modifica Obbligatorietà dei campi PVOL_B_F1 e

Formato

•  Modifica

dei
ComponentiPrezziElettrico e ComponentiPrezzoGas
•  Modifica Formato dei campi PROVINCIA e COMUNE

campi

delle

sezioni

1.1

19/02/2018

Adeguamento Formato PFIX e Comune

Aggiornamento codici di inammissibilità

2.0

13/07/2018

2.1

20/11/2018

Versionamento  della  Specifica  tecnica  con  l’adeguamento  dei
tracciati delle offerte PLACET e delle offerte del mercato libero
secondo quanto previsto dalla deliberazione 51/2018/R/com

Allineamento  codici  delle  unità  di  misura,  e  inserimento  su
richiesta  del  mercato  del  dispacciamento  PD  della  maggior
tutela e la QVD per le offerte gas.

Integrazione delle specifiche con il tracciato per la trasmissione
delle  offerte  per  la  cui  comparazione  è  necessaria  una
evoluzione  dei  tracciati  o  degli  algoritmi  di  calcolo  della  stima
della spesa.

3.0

25/07/2019  Ottimizzazione Tracciato Offerta paragrafo 7.2:

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

4/70

•  Modifica  gestione  eliminazione  offerte  congiunte
all’interno di un’offerta DUAL FUEL (TIPO MERCATO=03).

•  Modifica logica dell’attributo OFFERTA_SINGOLA.

Modifica  gestione  flusso  di  aggiornamento  (TO2.0051)  per
consentire la riapertura di offerte SCADUTE.

Modifica dei  controlli di ammissibilità nel flusso di inserimento
(T02.0050) e aggiornamento (T02.0051).

Inserimento nel flusso TO2.0052 (eliminazione) della causale e
motivazione eliminazione.

Caricamenti Massivi

Nuova versione Tracciato Offerta paragrafo 7.1 :

•  Componenti regolate
•  Fasce configurabili
•  Validità condizioni economiche
•
•  Sconto differenziato per fascia (settore EE)

Introduzione offerte tipologia FLAT

3.1

12/08/2019  Errata Corrige nomenclatura Nome File ZIP per invio massivo e

COD_FLUSSO

•  Campo  TIPOLOGIA_FASCE  in  sezione  TipoPrezzo  codici

07 e 08 unificati in 07

3.2

08/11/2019

•  Caratteri speciali accettati in nomenclatura file
•  Non  obbligatorietà  SCONTO  e  SERVIZI  AGGIUNTIVI

(tracciato offerte c.d. non simulabili)

•  Campo  CODICE

in
eliminato codice 08 - QTmcv (del. 366/2019)

sezione  ComponentiRegolate

4.0

15/07/2020

•

Inserimento  dell’annullamento  trasmissione  Offerta,
paragrafo 5.2.2

4.1

18/02/2022

Funzionalità disponibile dal 14/09/2020

•

Inserimento nuovi codici nei campi:
-

IDX_PREZZO_ENERGIA, frequenza aggiornamento e
aggiunta nuovi indici;

-  CODICE, inserimento DispBT;
-  TIPO_DISPACCIAMENTO,  esplicitazione  di  tutte  le
singole  componenti  così  che  il  venditore  possa
scegliere quali applicare ai fini della spesa.

Campo  DURATA,  precisazione  che  l’informazione  riguarda  la
durata delle condizioni economiche

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

5/70

4.2

20/05/2022  Recepimento  delle

logiche  di  valorizzazione  del  campo

COD_OFFERTA definite dalla deliberazione 135/2022

4.3

15/06/2022

Posticipo  introduzione  dei  controlli  rispetto  standard  della
deliberazione 135/2021, come da deliberazione 258/2022
Correzione refusi

4.4

04/10/2023

4.5

06/12/2023

4.6

26/11/2024

Aggiornamento  a  seguito  della  deliberazione  100/2023/R/com
(rimozione  del  servizio  di  tutela  gas)  e  della  deliberazione
250/2023/R/com (oneri di recesso e rinnovi contrattuali):
del

Introduzione
campo
codice
TIPOLOGIA_CONDIZIONE  della  sezione  “Condizioni
Contrattuali” nel formato offerta per il Mercato Libero
-  Aggiornamento  delle  regole  di  prevalenza  delle

“05”

nel

-

offerte PLACET

Inibizione caratteri speciali nel campo codice offerta,  a partire
dall’11  dicembre  2023  come  da  comunicato  ARERA  del  4
dicembre  2023  aventi  ad  oggetto  “Modalità  applicative  del
codice offerta standard”

1.  Aggiornamento  a  seguito  dell’introduzione  del  TIDE
(Testo Integrato del Dispacciamento Elettrico) a partire
dal 01/01/2025:
-  Eliminazione dei codici “03”,”04”,”05”,”06”,”07”,”08”
e  nuova  definizione  del  codice  “01”  all’interno  del
campo  TIPO_DISPACCIAMENTO  della
sezione
“Dispacciamento”  nel  formato  offerta  per  il  Mercato
Libero

-  Nuova  definizione  dell’indice  PUN  all’interno  del
campo
sezione
“RiferimentiPrezzoEnergia” nel formato offerta per il
Mercato Libero

IDX_PREZZO_ENERGIA

della

2.  Modifiche/chiarimenti riguardo:

formato dei campi P_FIX_F e P_FIX_V

-
-  obbligatorietà campo URL_SITO_VENDITORE
-  utilizzo

indici  PE  e  Cmem  esclusivamente

in
abbinamento  a  Sconto  su  Tutela  e  spostamento
dell’indice Cmem fra quelli ad aggiornamento mensile

5.0

15/12/2025

1.  Introduzione delle offerte “miste”
2.  Inibizione  della  possibilità  di  trasmettere  più  di  una
componente  impresa  in  quota  annua  e  una  dipendente
dai consumi per TIPO_CLIENTE = ‘01’

3.  Introduzione  delle

offerte
“onnicomprensive a canone” per TIPO_CLIENTE = ‘01’

“onnicomprensive”

e

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

6/70

4.  Introduzione del  codice ‘14’ per indicare il corrispettivo
CdispD nel campo TIPO_DISPACCIAMENTO nella sezione
‘Dispacciamento’

5.  Introduzione obbligatorietà per il campo URL_OFFERTA
6.  Introduzione della possibilità di indicare più di un indice

di riferimento, solo per TIPO_CLIENTE = ‘01’

7.  Introduzione  di  nuovi  controlli  di  ammissibilità  e

correzione di refusi

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

7/70

1  Glossario

Voce

Accreditamento
al SII

Acquirente Unico
(AU)

Attivazione
contrattuale

Autorità
Catalogo dei
Processi e dei
Servizi

Catalogo Profili

Cliente Finale

Controparte
commerciale

Definizione
Processo,  originato  da  Utente  e  autorizzato  dal  Gestore  SII,  che
permette  l’accreditamento  di  Utente  come  soggetto  attivamente
partecipe del SII

Soggetto di cui all’articolo 4 del decreto legislativo n.79/99

E’  il  processo  attraverso  cui  è  gestita  nel  SII  l’esecuzione  di  un  nuovo
contratto  di  vendita,  che  comporta  l’aggiornamento  della  relazione  di
sistema nel RCU con riferimento ai dati anagrafici del cliente finale e/o
all’utente del dispacciamento associato al punto di prelievo
Autorità di Regolazione per Energia Reti e Ambiente

Il Catalogo dei Processi e dei servizi contiene tutte le informazioni che
descrivono un processo applicativo.

Il  Catalogo  dei  Profili  descrive  chi  può  utilizzare  i  servizi  del  SII  e  con
quale modalità.
In particolare, esso contiene:

•  L’anagrafica dei soggetti coinvolti dal SII
•
•

I profili delle PdC qualificate
I profili di accesso e di fruizione dei servizi erogati in ambito SII.
Questo  catalogo  è  aggiornato  via  via  che  i  soggetti  aderiscono  al  SII,
qualificano  le  loro  PdC,  richiedono  l’adesione  ad  un  processo,  si
qualificano per l’accesso o l’erogazione di servizi
Persona  fisica  o  giuridica  che  acquista  energia  elettrica  o  gas  naturale
esclusivamente per uso proprio
E’ l’Utente che si accredita al SII in qualità di controparte commerciale
di un Punto di prelievo ai sensi della deliberazione 166/2013/R/com, nel
caso  di  POD  in  maggior  tutela,  la  controparte  commerciale  del  cliente
finale è rappresentata dall’Esercente la maggior tutela.

Meccanismo  di  identificazione  e  autenticazione  degli  utenti  finali.  I
meccanismi di autenticazione e identificazione in uso nel SII sono:

•  UserID e Password (credenziali deboli)
•  Certificati  digitali  memorizzati  su  dispositivi  elettronici  (es.

Credenziali

Smartcard)  accessibili mediante PIN(credenziali forti)

•  Certificati  digitali  installati  sui  Sistemi  PdC,  Portale  Web,

Archiviazione, ecc. (credenziali forti)

I certificati digitali sono dei file, con una validità temporale limitata, usati
per garantire l'identità di un soggetto, sia esso un server o una persona.

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

8/70

Voce

Esercente la
maggior tutela

Gestore del SII

Mese di
competenza

Operazione

Operatore di
Processo
Porta di
Comunicazione
(PdC)

PdC SII

PdC Utente

PdC Web

Pratica

Processi
Referente del
Processo

Referente tecnico
per il SII

Registro Centrale
Ufficiale (RCU)

Regolamento

Responsabile del
SII

Definizione
All’interno  di  una  comunicazione  servono  per  stabilire  con  esattezza
l'identità delle parti.
Soggetto che, ai sensi dell’articolo 1, commi 2 e 3, del decreto-legge 18
giugno 2007, eroga il servizio di maggior tutela
Acquirente  Unico,  quale  soggetto  titolare  e  gestore  del  Sistema
Informativo Integrato di cui all’Art. 1bis della legge n. 129/2010

E’ il mese di riferimento dei dati oggetto della trasmissione

Singola entità di interazione (generalmente individuata tra un erogatore
e un fruitore) esplicata all’interno di un Descrittore di Servizio
Utente finale del SII che può operare sui processi in funzione del proprio
livello di abilitazione (op. dispositivo, op. semplice, op. massivo)
Componente  standardizzata  del  modello  tecnologico  del  SII  per
l’interazione, in architettura SOA, tra il sistema informatico dell’Utente e
l’infrastruttura centrale, di cui al successivo art. 4
Porta di comunicazione, componente del SII, dedicata al dialogo A2A con
la PdC dell’Utente
Porta  di  Comunicazione  risiedente  nell’infrastruttura  Utente,  atta  a
creare il canale di comunicazione A2A tra Utente e SII
Porta di Comunicazione, componente del SII, dedicata al dialogo tra la
PdC SII e il Portale SII
All’interno del SII si definisce pratica l’insieme di attività, informazioni,
messaggi  applicativi e documenti scambiati fra uno o più Utenti e il SII
e riguardante un determinato processo applicativo
Processi gestiti tramite SII, come definiti dall’Autorità
Persona  fisica  designata  dall’Utente  o  dal  Gestore  a  cui  è  assegnato  il
compito di assicurare l’operatività del processo
Persona  fisica  designata  dall’Utente  o  dal  Gestore  a  cui  è  assegnato  il
compito  di  sovrintendere  alla  realizzazione  ed  al  funzionamento  delle
componenti  tecniche  necessarie  alla  corretta  gestione  dei  processi
mediante il SII
Registro  contenente  l’elenco  completo  dei  punti  di  prelievo  di  energia
elettrica e di riconsegna di gas naturale e dei  dati fondamentali per la
gestione dei Processi, ai sensi del comma 1 del citato Art. 1bis della legge
n. 129/2010
Regolamento  che,  ai  sensi  del  comma  2.6  Allegato  A  delibera  ARG/elt
201/10, disciplina il funzionamento del SII, ivi inclusi i rapporti tra il SII
e gli Utenti, le modalità di trattamento dei dati personali e sensibili e i
requisiti e le condizioni di accesso al sistema stesso

Persona fisica che rappresenta l’Utente o il Gestore nei confronti del SII

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

9/70

Voce

Responsabile per
la Sicurezza

Ruolo di Processo

Ruolo utente

Sistema
Informativo
Integrato (SII)

utente finale
Utente

Voltura

Workspace

Definizione
Persona fisica designata dall’Utente o dal Gestore a cui è assegnata la
responsabilità  relativa  alla  gestione  della    sicurezza,  nel  rispetto  di
quanto previsto nel presente regolamento
Ruolo ricoperto dall’Utente di un Servizio all’interno del singolo Processo.
Es. UDD-E: Utente del Dispacciamento Entrante
Ruolo assegnato all’utente finale
Es.  Operatore  semplice,  operatore  dispositivo,  Responsabile  SII,
Referente Tecnico, Referente di Processo
Sistema  Informativo  Integrato  basato  su  una  banca  dati  dei  punti  di
prelievo di energia elettrica e di gas naturale e dei dati identificativi dei
clienti finali di cui all’Art. 1bis della legge n. 129/2010, ovvero l’insieme
di strutture organizzative, infrastrutture tecnologiche e regole tecniche,
per la condivisione, l’integrazione e lo scambio dei flussi di dati funzionali
ai  Processi  necessari  per  il  funzionamento  dei  mercati  dell’energia
elettrica e il gas
Persone fisica autorizzata dall’Utente ad operare con il SII
Soggetto giuridico che partecipa al SII
E’ la variazione dell’intestazione del contratto di fornitura in essere per
un punto di prelievo attivo di cui è titolare un cliente finale diverso dal
cliente finale richiedente
Ambiente  di  lavoro,  messo  a  disposizione  dal  Portale  SII.  Esso  è  di
proprietà di ciascun utente finale ed è funzione dei ruoli utente

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

10/70

2  Contesto normativo

L’art. 1 bis della legge 129/10 ha istituito, presso Acquirente Unico SpA, il Sistema Informatico

Integrato per la gestione dei flussi informativi relativi ai mercati dell’energia elettrica e del gas

naturale (SII), basato su una banca dati dei punti di prelievo e dei dati identificativi dei clienti

finali.

L’Allegato  A  alla  deliberazione  ARG/com  201/10  dell’Autorità  per  l’energia  elettrica  il  gas  e  il

sistema idrico, ora Autorità di Regolazione per Energia Reti e Ambiente (di seguito: Autorità) ha

definito  i  criteri  generali,  il  modello  di  funzionamento  e  il  modello  organizzativo  del  SII  ed  ha

attributo ad Acquirente Unico il ruolo di Gestore del SII.

Con la deliberazione 79/2012/R/com l’Autorità ha approvato il Regolamento per il funzionamento

del SII (Regolamento di Funzionamento), proposto da Acquirente Unico ai sensi dell’articolo 2,

comma 2.6, del suindicato Allegato A alla deliberazione ARG/com 201/10.

Con la delibera 555/2017/R/com l'Autorità approva la disciplina delle offerte a Prezzo Libero A

Condizioni Equiparate di Tutela (offerte PLACET), contenuta nell'Allegato A del provvedimento,

con  lo  scopo  di  rafforzare  la  capacità  di  scelta  dei  clienti  di  piccole  dimensioni  e  superare

l'asimmetria informativa.

Con la deliberazione 848/2017/R/com l'Autorità individua lo strumento per la comparazione delle

offerte  a  prezzo  libero  a  condizioni  equiparate  di  tutela  (offerte  PLACET)  e  reca  chiarimenti  in

merito alla deliberazione 555/2017/R/com.

Con  la  deliberazione  51/2018/R/com  sono  approvati  i  criteri  generali  per  la  realizzazione  del

Portale Offerte, di cui all’articolo 1, comma 61, della legge 124/17.

Con la deliberazione 426/2020/R/com l’Autorità ha approvato interventi di rafforzamento degli

obblighi  informativi  dei  venditori  a  vantaggio  dei  clienti  finali  nelle  fasi  precontrattuale  e

contrattuale mediante la revisione del Codice di condotta commerciale.

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

11/70

Con la deliberazione 135/2022/R/com l’Autorità dispone la standardizzazione del codice offerta

nei settori energia elettrica e gas naturale e di popolamento e aggiornamento del codice offerta

nel Registro Centrale Ufficiale (RCU).

Con  la  deliberazione  258/2022/R/COM  l’Autorità  dispone  il  posticipo  dell’entrata  in  vigore

dell’obbligo di utilizzo del codice standard.

Con la deliberazione 100/2023/R/com l’Autorità definisce le disposizioni in merito alla rimozione

del servizio di tutela del gas naturale e adegua gli obblighi informativi previsti dal Regolamento

di funzionamento del Portale Offerte al contesto risultante dalla rimozione delle tutele di prezzo.

Con la deliberazione 250/2023/R/com l’Autorità modifica e adegua gli obblighi informativi in capo

ai venditori nei confronti dei clienti di piccole dimensioni in materia di oneri di recesso anticipato

dei clienti finali di energia elettrica, nonché di rinnovo delle condizioni economiche nei contratti

di fornitura di energia elettrica e gas naturale.

Con

la  deliberazione  345/2023/R/eel

l’Autorità  ha  approvato

il  Testo  Integrato  del

Dispacciamento Elettrico (TIDE), in vigore dal 01/01/2025.

Con  la  deliberazione  386/2025/R/com  l’Autorità  ha  definito  misure  di  razionalizzazione  dei

corrispettivi  delle  offerte  di  energia  elettrica  e  gas  naturale  per  i  clienti  domestici  e  introdotto

obblighi informativi nella fase precontrattuale, per la redazione dei contratti di fornitura e per le

comunicazioni  di  modifica  delle  condizioni  contrattuali,  al  fine  di  dare  piena  attuazione  delle

disposizioni sulla trasparenza e confrontabilità delle offerte.

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

12/70

3  Scopo e contenuto del documento

Il presente documento definisce il Funzionamento e le Specifiche del Processo per la Trasmissione

delle Offerte al SII.

In particolare definisce, secondo quanto previsto all’art. 14.1 del Regolamento di Funzionamento,

per il Processo di Trasmissione Offerte:

1.  Le regole tecniche per la registrazione degli Utenti (art. 14.1.5), che descrivono:

-

la  procedura  di  registrazione  degli  Utenti  sul  processo  nonché  le  procedure  di

autorizzazione e di revoca degli utenti finali, i ruoli e i relativi profili di accesso;

2.  Il modello generale del Processo e il flusso operativo delle comunicazioni (art. 14.1.4).

3.  La procedura per la Trasmissione delle Offerte al SII (art. 14.1.6), che descrive:

-

-

i servizi, le operazioni ed i dati del Processo;

il formato e i tracciati dei file.

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

13/70

3.1  Riferimenti

La presente specifica ed i suoi allegati fanno riferimento alla documentazione seguente.

RIF.

DOCUMENTO

INDIRIZZO DI PUBBLICAZIONE

[0]

Regolamento di funzionamento

[0.A]

Allegato
Tecnologico del SII

A:

Modello

https://siiportale.acquirenteunico.it/funzionamento-del-
sii/regolamento-di-funzionamento

[0.C]

[1]

[1.A]

[2]

Allegato C: Regole e misure di
sicurezza

Procedura di accreditamento
al SII
Procedura  di  registrazione  al
processo

https://siiportale.acquirenteunico.it/procedure/trasversali

https://siiportale.acquirenteunico.it/procedure/trasversali

Specifiche tecniche del Portale
Web del SII

https://siiportale.acquirenteunico.it/processi/trasversali/portale-web-
e-pdc

[3]

Specifiche tecniche della PdC

[3.A]

[4]

[5]

[6]

Allegato  A-
MessaggioPdC

specifica  del

Specifica tecnica
Accreditamento Venditori

Procedura Trasmissione
Offerte PLACET non vulnerabili
Struttura codice offerta
standard

https://siiportale.acquirenteunico.it/processi/trasversali/portale-web-
e-pdc

https://siiportale.acquirenteunico.it/processi/settore-elettrico/venditori

https://siiportale.acquirenteunico.it/processi/settore-gas/venditori

https://siiportale.acquirenteunico.it/processi/trasversali/mercato-retail

https://siiportale.acquirenteunico.it/procedure/trasversali

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

14/70

4  Registrazione degli Utenti al Processo

Gli Utenti coinvolti, previsti dalla deliberazione 848/2017/R/com, sono le Controparti Commerciali

(CC), le quali in conformità a quanto previsto dall’art. 11 e dall’articolo 14.1.5 del Regolamento

di funzionamento, gli Utenti, in seguito all’accreditamento, per poter eseguire le attività previste

dai  processi  devono  registrarsi  ai  processi  secondo  quanto  stabilito  nella  procedura  di

Registrazione a Processo [1.A].

Sono classificati in RCU in qualità di Controparti Commerciali tutti gli Utenti che hanno effettuato

l’accreditamento al SII con il suddetto ruolo secondo le modalità definite dalle Specifiche tecniche

Accreditamento Venditori [4] e gli UDD titolari del dispacciamento dei POD per i quali non è stata

associata una CC.

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

15/70

5  Modello generale dei Processi di Trasmissione Offerte

Il  modello  generale  del  processo  di  Trasmissione  Offerte  descrive  le  modalità  e  i  flussi  per  la

trasmissione dell’offerte del mercato libero al SII mediante il processo di Trasmissione Offerte

(TO).

Le comunicazioni tra gli Utenti e il SII, con le quali vengono scambiati i messaggi del Processo,

avvengono mediante il Portale Web, attraverso il quale gli operatori possono gestire le pratiche

mediante upload e download massivo di file csv (solo per le offerte PLACET) o xml (per le tutte

offerte del Mercato Libero).

La struttura dei messaggi è conforme alla specifica del MessaggioPdC [3.A].

Il  processo  di  Trasmissione  Offerte  permette  il  caricamento  in  input  di  tutte  le  informazioni

necessarie per la raccolta e successivamente la pubblicazione in modalità open data, mediante il

Portale Offerte, delle offerte vigenti sul mercato retail che gli operatori della vendita sono tenuti

a  trasmettere,  in  ottemperanza  alle  disposizioni  di  cui  all’articolo  1,  comma  61  della  legge  4

agosto 2017, n. 124 (di seguito: legge 124/17), entrata in vigore il 29 agosto 2017.

Dovranno essere pubblicate nel Portale Offerte tutte le offerte generalizzate di energia elettrica

e gas naturale, anche dual fuel, per gli clienti:

•  domestici

•  non domestico

•  Altri usi gas <200.000 Smc

•  Condominio uso domestico gas <200.000 Smc

Gli  Utenti  abilitati  potranno  effettuare  lo  scambio  di  messaggi  con  il  SII,  mediante

upload/download di file in formato “xml”, secondo i tracciati pubblicati al capitolo 7.

Al termine del caricamento del file, il SII verifica la coerenza delle informazioni riportate nel file

e, in caso di ammissibilità positiva, apre una pratica per ogni tipologia delle suddette offerte e

aggiorna il database.

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

16/70

In  caso  di  upload  di  un  file  non  conforme,  il  portale  restituisce  l’inammissibilità  del  file  e  dà

evidenza dell’errore di formato permettendo il nuovo upload del file.

La sincronizzazione delle offerte trasmesse mediante il processo TO con il Portale Offerte viene

effettuata ogni 24h, con la possibilità per il Gestore di aumentarne la frequenza.

5.1  Modello generale del Processo di Trasmissione Offerte PLACET

Il processo è composto dal servizio TO1 - Trasmissione Offerta PLACET mediante il quale la

controparte commerciale trasmette al SII le offerte PLACET per le commodity elettricità e gas.

Le  controparti  commerciali  possono  trasmettere  al  SII  le  Offerte  PLACET,  mediante  i  seguenti

due flussi massivi:

•  Trasmissione  Offerta  EE  (TO1.0050)  per  la  trasmissione  dell’offerta  PLACET  per  la

fornitura di energia elettrica;

•  Trasmissione  Offerta  GAS  (TO1.0051)  per  la  trasmissione  dell’offerta  PLACET  per  la

fornitura di gas naturale.

A  tal  fine  il  Gestore  del  SII,  mette  a  disposizione  delle  controparti  commerciali,  apposite

funzionalità di upload e download per la gestione delle offerte PLACET.

La trasmissione delle offerte al SII avviene mediante l’upload di uno o più file composti da una o

più righe corrispondenti a una o più tipologie di offerta:

•  Elettrica domestico (fisso o variabile)

•  Elettrica non domestico (fisso o variabile)

•  Gas Domestico (fisso o variabile)

•  Gas Altri usi <200.000 Smc (fisso o variabile)

•  Gas Condominio uso domestico <200.000 Smc (fisso o variabile)

Al termine del caricamento del file, il SII verifica la coerenza delle informazioni riportate nel file

e, in caso di ammissibilità positiva, apre una pratica per ogni tipologia delle suddette offerte e

aggiorna il database.

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

17/70

Figure 1. Modello generale del processo di trasmissione Offerta PLACET

Qualora  l’Utente  ha  la  necessità  di  modificare  un’offerta  ammissibile  e  trasmessa  al  SII,  può
effettuare  un  nuovo  upload  di  uno  o  più  file  in  sostituzione  dell’offerta  precedentemente
trasmessa.

Nel paragrafo successivo sono riportate le regole di validità e prevalenza delle offerte.

  Regole di prevalenza e validità delle offerte PLACET

Ciascun venditore di energia elettrica e di gas naturale ha l’obbligo di offrire ai clienti individuati,

in  tutte  le  aree  territoriali  in  cui  opera,  in  aggiunta  alle  proprie  offerte  commerciali,  le  offerte

PLACET a prezzo fisso e PLACET a prezzo variabile.

1.  Le  offerte  PLACET  sono  offerte  di  mercato  libero  e  sono  formulate  distintamente  con

riferimento  al  settore  dell’energia  elettrica  e  al  settore  del  gas  naturale.  Le  offerte

PLACET non possono riguardare congiuntamente i due settori. Pertanto le offerte devono

essere  univoche  per  venditore,  settore  (ELE  o  GAS),  tipologia  di  cliente,  tipologia  di

offerta (chiave dell’offerta).

2.  Le offerte PLACET non possono includere la fornitura di servizi o di prodotti aggiuntivi.

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

Richiesta di trasmissione Offerta PLACET Controparte CommercialeSIIRicezione richiesta trasmissione offertaTO1.0050TO1.0051Verifica ammissibilitàComunicazione ammissibilità negativaNon ammissibileApertura pratica AmmissibileComunicazione ammissibilità positivaRicezione ammissibilità negativaRicezione ammissibilità positivaTO1.0100TO1.0101TO1.0100TO1.0101Aggiornamnto DB Offerte

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

18/70

3.  Per  una  stessa  chiave  deve  essere  attiva  una  sola  offerta1  ad  una  certa  data,

indipendentemente  dall’ambito  territoriale  che  ricopre.  L’inserimento  di  una  nuova

offerta modifica l’intervallo di validità delle offerte già attive sulla stessa chiave e sullo

stesso intervallo di tempo.

4.  In caso di trasmissione di più offerte per una stessa tipologia, ad esempio domestico a

prezzo fisso, con stessa data di inizio validità, il SII:

a.  Se la data inizio validità è nel futuro manterrà valida l’ultima offerta trasmessa.

b.  Se la data inizio validità è nel passato o oggi, scarta l’offerta con l’opportuno errore.

In  caso  di  data  inizio  validità  differente  tra  due  offerte  della  tipologia,  la  validità  di

un’offerta,  con  data  inizio  antecedente,  sarà  terminata  dal  SII  alla  data  di  inizio  della

nuova offerta.

5.  Pubblicata un’offerta in una o più aree geografiche, qualora la controparte commerciale

ha  la  necessità  di  modificare,  in  aggiunta  o  in  cancellazione,  le  zone  in  cui  offre  la

suddetta offerta, è necessario trasmettere al SII una nuova offerta, con la modifica delle

zone, anche mantenendo invariate le restanti componenti dell’offerta.

6.  Non  possono  essere  trasmesse  offerte  con  data  inizio  dell’offerta  antecedente  alla

sysdate.

7.  Le offerte non più valide vengono archiviate in una tabella di storico.

8.  La zona di un’offerta, se l’offerta è ammissibile, viene normalizzata riconducendo le zone

alla zona  territoriale  superiore secondo le regole di seguito dettagliate. In particolare

ogni venditore dovrà, ai sensi della deliberazione 555/2017/R/com, inserire le zone che

corrispondono  alle  aree  territoriali  in  cui  opera  commercialmente  -  o  dove  intende

operare –  ossia relativamente alle aree territoriali dove sta già offrendo o intende offrire

altre offerte del mercato libero con riferimento ai clienti di piccola dimensione.

a.  Se nel campo COMUNE sono indicati tutti i comuni di una provincia, nell’archivio

offerte viene indicata solo la provincia (anche se non espressamente indicata nel

flusso);

1 Dal 01/09/2023 è garantita la facoltà della Controparte Commerciale di inviare un’offerta PLACET dedicata
ai clienti non vulnerabili in aggiunta a quelle già trasmesse per la generalità dei clienti della stessa tipologia,
secondo quanto definito nella Procedura Trasmissione Offerte PLACET non vulnerabili[5]. In questo caso per
una stessa chiave, a una certa data, possono essere attive più offerte (purché i codici offerta seguano le
indicazioni fornite nella Struttura codice offerta standard[6] e nella Procedura Trasmissione Offerte PLACET
non vulnerabili[5]).

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

19/70

b.  Se  nel  campo  PROVINCIA  sono  indicati  tutte  le  provincie  di  una  regione,

nell’archivio  offerte  viene  indicata  solo  la  regione  (anche  se  non  espressamente

indicata nel flusso);

c.  Se nel campo REGIONE sono indicati tutte le regioni italiane, nell’archivio offerte

non viene indicata alcuna regione (l’assenza di zone equivale a tutto il territorio

nazionale nel flusso);

9.  Per il gas il sistema tiene conto delle zone non metanizzate, di conseguenza per le

offerte nazionali non è necessario escludere i codici ISTAT dei comuni non

metanizzati;

10. Ogni offerta deve avere una data inizio e una data fine, qualora venga inserita una

nuova offerta con data inizio nel periodo di validità di una medesima offerta PLACET in

corso (fissa o variabile), l’offerta in corso si chiude alla mezzanotte del giorno

precedente la data inizio della nuova offerta.

11. I codici offerta contenuti nei flussi T01.0050 e T01.0052 devono rispettare lo standard

definito  dalla  del.  135/2022/R/com,  ossia  contenere  le  caratteristiche  dell’offerta  per

commodity.

Il SII verifica il rispetto del nuovo standard a decorrere dall’1 ottobre 2022 per il settore

energia elettrica e dall’1 gennaio 2023 per il settore gas naturale.

Si riportano in modo esemplificativo ma non esaustivo due scenari di esempio:

Scenario 1

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

20/70

Scenario 2

Per trasmettere più offerte con data inizio offerta differenziate nel tempo, in fase di trasmissione
deve essere rispettato l’ordine cronologico che si vuole dare alle offerte.

5.2  Modello  generale  Processo  di  trasmissione  Offerte  MERCATO

LIBERO

Il processo è composto dal servizio TO2 - Trasmissione Offerta MERCATO LIBERO mediante
il quale la controparte commerciale trasmette al SII le offerte per le commodity elettricità e gas.

Le controparti commerciali potranno trasmettere al SII le Offerte del Mercato Libero, mediante i

seguenti flussi:

o  Trasmissione Offerta (TO2.0050) mediante il quale la controparte commerciale trasmette

al SII un’offerta del Mercato Libero per la fornitura di energia elettrica o gas;

o  Aggiornamento  Offerta  (TO2.0051)  mediante  il  quale  la  controparte  commerciale,  con

l’obiettivo  di  aggiornarne  alcuni  parametri  di  un’offerta,  trasmette  al  SII  un’offerta  in

sostituzione  di  una  precedentemente  comunicata  o  riapre  un’offerta  scaduta  variando

alcuni parametri precedentemente trasmessi;

o  Elimina  Offerta  (TO2.0052)  mediante  il  quale  la  controparte  commerciale  trasmette

l’identificativo di un’offerta al SII per eliminarla.

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

21/70

Le  controparti  commerciali  possono  effettuare  la  trasmissione  delle  offerte  del  mercato  libero

anche mediante la funzionalità di trasmissione massiva. La funzionalità di trasmissione massiva

consente alle Controparti Commerciali di inviare al SII una o più offerte (simulabili e non) tramite

il caricamento di un file compresso (avente al suo interno i file xml delle offerte).

L’operatore  dispone,  in  modo  massivo  della  possibilità  di  Inserire  o  Aggiornare  le  offerte.  La

cancellazione massiva delle offerte avviene mediante i canali massivi previsti dai processi del SII.

In  fase  di  Upload  del  file  compresso,  il  sistema  sottoporrà  il  file  caricato  ad  un  controllo  sulla

validità / struttura aspettandosi un file compresso (non corrotto) in formato “Zip” il cui contenuto

è costituito da soli file in formato ”xml” ignorando eventuali cartelle/sottocartelle.

Per  consentire  al  sistema  di  gestire  l’offerta  nella  modalità  corretta,  il  file  zip  deve  seguire  la

nomenclatura definita di seguito.

Nome File ZIP per invio massivo:

<PIVA_UTENTE>_TO2_<COD_FLUSSO>_<VERSIONE_FILE>_<DESCRIZIONE>.ZIP

•  PIVA_UTENTE: Partita IVA del Utente che richiede l’attivazione
•  COD_FLUSSO: il codice del flusso massivo da trasmettere (“0050”-Inserimento
•
•  VERSIONE_FORMATO_FILE:  Codice  che  identifica  le  tipologie  di  formato  attuali  o

“0051”-Aggiornamento)

future del tracciato (01=offerte standard; 02:offerte non simulabili )

•  DESCRIZIONE: campo libero, massimo 25 caratteri alfanumerici (non ammessi spazi,

“_” o caratteri speciali)

Nei  paragrafi  relativi  ai  flussi  di  inserimento  e  aggiornamento  di  una  offerta  sono  riportati  i
dettagli sulle rispettive nomenclature (par 6.2.1 e par 6.2.2) .

Per  la  gestione  dei  caricamenti  massivi  relativi  alle  eliminazioni  di  più  offerte  sarà  utilizzato  il
formato csv con intestazione e indicazioni descritte nel paragrafo 6.2.3

Nel paragrafo successivo sono riportate le regole di validità e prevalenza delle offerte.

  Regole di prevalenza e validità delle offerte MERCATO LIBERO

1.  Le  offerte  MERCATO  LIBERO  possono  includere  la  fornitura  di  servizi  o  di  prodotti

aggiuntivi.

2.  Per una stessa chiave (COD_OFFERTA & PIVA_UTENTE) deve essere attiva una sola offerta

(tra PLACET, RETAIL, RETAIL non simulabili) ad una certa data.

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

22/70

3.  Qualora la controparte commerciale ha la necessità aggiornare o eliminare un’offerta già

presente

(precedentemente

caricata)  è  possibile  effettuare

tale  operazione

rispettivamente con i flussi TO2.0051 e TO2.0052.

4.  Non possono essere trasmesse offerte con data inizio dell’offerta antecedente alla sysdate.

5.  Le offerte non più valide vengono archiviate in una tabella di storico.

6.  La zona di un’offerta, se l’offerta è ammissibile, viene normalizzata riconducendo le zone

alla zona territoriale superiore secondo le seguenti regole:

a.  se nel campo COMUNE sono indicati tutti i comuni di una provincia, nell’archivio

offerte viene indicata solo la provincia (anche se non espressamente indicata nel

flusso);

b.  se  nel  campo  PROVINCIA  sono  indicati  tutte  le  provincie  di  una  regione,

nell’archivio  offerte  viene  indicata  solo  la  regione  (anche  se  non  espressamente

indicata nel flusso);

c.  se nel campo REGIONE sono indicati tutte le regioni italiane, nell’archivio offerte

non viene indicata alcuna regione (l’assenza di zone  equivale  a tutto il territorio

nazionale nel flusso);

7.  Le  offerte  a  prezzo  variabile  possono  essere  indicizzate  con  riferimento  ad  un  prodotto

forward,  qualora  il  prodotto  forward  non  fosse  già  disponibile  tra  gli  indici  del  portale

Offerte, il Gestore comunicherà all’utente i tempi necessari per l’acquisizione dell’indice e

per la messa a disposizione dell’offerta indicizzata sul portale.

Il campo IDX_PREZZO_ENERGIA deve essere valorizzato SOLO se l’offerta è variabile e

indicizzata o a sconto sui servizi di tutela, non può essere valorizzato se l’offerta è a prezzo

fisso.

La periodicità si riferisce all’aggiornamento dell’indice ai fini della fatturazione al cliente

finale, mentre per la simulazione della spesa annua i forward sono trimestrali sul Portale

Offerte.

8.  In caso di modifica di un’offerta, se questa è in corso di validità SYSDATE>= DATA_INIZIO

l’Utente  potrà  modificare  esclusivamente  la  DATA_FINE,  MODALITA  (Attivazione),

MOD_PAGAMENTO

e

la

lista

delle  OFFERTE_CONGIUNTE,

in

alternativa

(SYSDATE<DATA_INIZIO),  prima  che  l’offerta  diventi  attiva,  la  CC  potrà  variare  tutti  i

parametri  dell’offerta.  Qualora  invece  l’offerta  sia  SCADUTA  (SYSDATE>DATA_FINE)

l’Utente potrà modificare esclusivamente DATA_INIZIO e DATA_FINE. Nei casi di offerta

ELIMINATA, non potranno essere effettuate modifiche.

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

23/70

9.  Le offerte MERCATO LIBERO possono essere formulate distintamente con riferimento al

settore dell’energia elettrica e al settore del gas naturale o dual fuel (come definito da art.

1 Allegato A delibera 51/2018/R/com).

Per trasmettere offerte DUAL FUEL e renderle visibili come tali nel Portale Offerte è necessario

valorizzare correttamente i campi TIPO_MERCATO presenti nella sezione “DettaglioOfferta” e,

di conseguenza, i campi della sezione “OffertaDUAL”.

La generazione di una  offerta DUAL FUEL può  essere data dalla combinazione di due  o tre

flussi TO (cap. 7), rispettivamente caso 1 e 2.

Caso 1:

Valorizzando il campo TIPO_MERCATO con 01 o 02 si definiscono tutti i dettagli dell’offerta

EE  o  GAS.  Contemporaneamente  il  campo  OFFERTA_SINGOLA  indicherà  se  l’offerta  è

disponibile singolarmente o anche in abbinamento con l’altra commodity.

Nel caso di OFFERTA_SINGOLA=NO l’offerta sarà disponibile esclusivamente in abbinamento

con offerte dell’altra commodity, l’offerta sarà visibile sul PO nei seguenti casi:

•

In fase di trasmissione è stata valorizzato il campo OFFERTE_CONGIUNTE (commodity

opposta)

•

Il  COD_OFFERTA  dell’offerta  trasmessa  con  OFFERTA_SINGOLA=NO  è  presente  nel

campo OFFERTE_CONGIUNTE di offerta Dual presente a sistema.

Nel caso di OFFERTA_SINGOLA=SI l’offerta sarà disponibile sia singolarmente che, qualora

l’utente  espliciti  nella  sezione  “OfferteDUAL”  le  OFFERTE_CONGIUNTE  della  commodity

opposta da abbinare, anche congiuntamente.

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

TIPO_MERCATOOFFERTA_SINGOLAOFFERTE CONGIUNTEVISIBILE SINGOLARMENTEVISIBILE  SE DUAL01SINO01SISI01NONO01NOSI02SINO02SISI02NONO02NOSI

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

24/70

Caso 2:

Il  flusso  con  il  campo  TIPO_MERCATO=03  è  idoneo  ad  abbinare  due  offerte  ELE  e  GAS

precedentemente  caricate  e  combinarle  in  una  nuova  offerta  DUAL  FUEL,  prevedendo

eventuali sconti.

Nel  caso  di  TIPO_MERCATO=03  sono  obbligatori  entrambi  i  campi  della  sezione

“OffertaDUAL”, inserendo un COD_OFFERTA per il GAS e uno per EE.

Due offerte congiunte, abbinate tra loro in una dual tramite un flusso TIPO_MERCATO=03,

NON  possono  essere  eliminate.  È  pertanto  necessario  eliminare

l’offerta  dual  e

successivamente le offerte congiunte.

Nel  caso  in  cui  tra  le  OFFERTE_CONGIUNTE  sia  presente  un’offerta  con  campo

OFFERTA_SINGOLA=NO, questa sarà visibile sul PO solo nel formato dual.

I codici offerta contenuti nei flussi con TIPO_MERCATO 01 o 02 devono rispettare lo standard

definito  dalla  del.  135/2022/R/com,  ossia  contenere  le  caratteristiche  dell’offerta  per

commodity.  Per  TIPO_MERCATO  03,  essendo  l’associazione  di  due  offerte  di  commodity

differenti, è previsto il rispetto dello standard solo nei casi ove possibile. Pertanto i caratteri

del codice offerta dovranno essere valorizzati secondo i valori previsti dallo standard, ma non

verranno  eseguiti  controlli  di  coerenza  riferibili  ad  uno  specifico  settore  energetico.  Ad

esempio il codice deve contenere all’ottavo carattere le lettere S, T o P.

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

25/70

Il  SII  verifica  il  rispetto  del  nuovo  standard  a  decorrere  dall’1  ottobre  2022  per  il  settore

energia elettrica e dall’1 gennaio 2023 per il settore gas naturale e per le dual fuel.

Se un’offerta è disponibile sia singolarmente che abbinata all’altra commodity, è necessario

trasmettere  due  flussi  distinti,  uno  con  il  settimo  carattere=E/G  per  le  offerte  vendibili

singolarmente e l’altro con il settimo carattere=D per le offerte vendibili solo in abbinamento

con l’altra commodity. I restanti caratteri definiscono le caratteristiche dell’offerta elettrica o

gas che si sta trasmettendo.

10. Per il calcolo della spesa annua per il dispacciamento è richiesto al Venditore di indicare

quale  corrispettivo  sarà  applicato  valorizzando  la  sezione  “Dispacciamento”.  È  possibile

indicare i corrispettivi previsti dal TIDE, il corrispettivo applicato alla Maggior Tutela (PD)

o, in alternativa, valorizzare “altro” e quindi precisare i corrispettivi applicati nel campo

VALORE_DISP (al lordo delle perdite di rete).

Con le modifiche introdotte dal 1 gennaio 2025 i codici disponibili diventano 8 nel campo

TIPO_DISPACCIAMENTO della sezione DISPACCIAMENTO, a cui si aggiunge il corrispettivo

CdispD dal 1 aprile 2026. La sezione è ripetibile (*) pertanto è possibile indicare più codici

per le offerte elettriche.

Selezionando i diversi codici per la stima della  spesa annua verranno  applicati i relativi

corrispettivi:

-  01 = Corrispettivo Dispacciamento (previsto dal TIDE);

-  02 = il corrispettivo PD definito dalla Autorità (comprensivo del corrispettivo capacità

di mercato MT);

-  09 = corrispettivo capacità di mercato servizi a tutele graduali2;

-  10 = corrispettivo capacità di mercato della maggior tutela3;

-  11  a  13  =  tali  corrispettivi  devono  essere  selezionati  se  il  venditore  li  applica  in

fattura4;

2 Il corrispettivo capacità STG è mensile (m1, m2 e m3) e definito trimestralmente dalla Autorità;
il Portale Offerte applica tali corrispettivi a quattro trimestri al fine di simulare la spesa annua.
3  Il  corrispettivo  capacità  MT  è  trimestrale  e  definito  trimestralmente  dalla  Autorità;  il  Portale
offerte applica il corrispettivo a quattro trimestri al fine di simulare la spesa annua.
4  I  corrispettivi,  ai  fini  della  simulazione  della  spesa  annua,  sono  applicati  alternativamente  in
funzione delle caratteristiche del cliente finale che interroga il Portale Offerte. Ad esempio, se il
venditore li seleziona tutti, il Portale Offerte applica solo quello legato al servizio di tutela a cui
ha diritto il cliente (Salvaguardia, Tutele Graduali o Maggior Tutela).

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

26/70

-  14  =  CdispD  (Corrispettivo  Dispacciamento  applicato  nel  servizio  a  Tutele  Graduali

Domestici,  disponibile  dal  01/04/2026  e  unico  valore  selezionabile  per  offerte

destinate a clienti domestici)

-  99  =  corrispettivo  indicato  dal  venditore,  può  includere  o  aggiungersi  ai  precedenti

corrispettivi.

Per  i  casi  in  cui  il  venditore  definisca  un  proprio  corrispettivo  capacità  di  mercato,  se

questo è monorario e indifferenziato nell’anno, deve utilizzare il campo 99 e indicarne il

valore. Se tale corrispettivo è invece differenziato per fascia e/o per intervalli inferiori al

primo anno di fornitura può utilizzare la sezione “Componente Impresa”.

Il codice 99 può indicare il totale del dispacciamento applicato (incluso mercato capacità)

o solo una parte (ad esempio solo mercato capacità).

I  corrispettivi  sono  considerati  tutti  comprensivi  delle  perdite,  anche  il  codice  99  che

pertanto deve essere trasmesso al lordo delle perdite.

11. Il campo COD_OFFERTA è stato previsto con un formato alfanumerico 32 (esclusi tutti i

caratteri speciali).

Si  specifica  che  per  consentire  l’aggiornamento  delle  offerte  trasmesse  prima  del  11
dicembre 2023 nel flusso di aggiornamento TO2.0051 sarà consentito utilizzare i caratteri
speciali.

12. Sezione ComponeteImpresa con MACROAREA = 06 (FER/Energia Verde)

Se TIPOLOGIA = 01 (Standard) il prezzo è sempre considerato nel calcolo della spesa e

fa  riferimento  ad  energia  100%  verde:  non  necessario  trasmettere  ulteriori

ComponentiImpresa con MACROAREA = 04 (Prezzo quota energia)

Se  TIPOLOGIA  =  02  (Opzionale)  il  prezzo  è  considerato  nel  calcolo  della  spesa  solo  se

applicato filtro “Energia Verde”: è necessario trasmettere il prezzo della commodity come

ComponentiImpresa con MACROAREA = 04 (Prezzo quota energia).

13. Qualora un’offerta sia SCADUTA (SYSDATE>DATA_FINE) l’Utente potrà riattivare l’offerta

con  flusso  di  aggiornamento  TO2.0051,  modificando  esclusivamente  DATA_INIZIO  e

DATA_FINE.

14. Il venditore potrà selezionare le componenti regolate applicate al cliente finale, nella stima

della spesa annua saranno considerati i valori aggiornati (sez. ComponentiRegolate).

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

27/70

In  caso  di  offerta  GAS  a  sconto  sui  servizi  di  tutela  non  sarà  possibile  selezionare  le

componenti regolate 06:QTint, 07:QTpsv.

15. Il  Venditore  che  valorizza  TIPOLOGIA_FASCE=02,  04,  05  o  06  dovrà  necessariamente

configurare le fasce orarie utilizzando la sezione FasceOrarieSettimanale.

Il campo <F_giornosettimana> della sezione FasceOrarieSettimanale deve avere sempre

l’ultimo quarto d’ora impostato a 96.

16. In  caso  di  TIPOLOGIA_FASCE  =  03,  07  qualora  non  venga  valorizzata  la  sezione

FasceOrarieSettimanale, sarà ereditata la configurazione delle 3 fasce standard (F1,F2,F3)

o  le  2  standard  Peak/Offpeak  dei  mercati  all’ingrosso  (si  veda  Vademecum  della

Piattaforma dei Conti Energia a Termine).

17. È  possibile  indicare  la  validità  delle  condizioni  economiche  (prezzi  e  sconti),  anche

indicando periodi successivi, comunque fino al primo anno di fornitura, utilizzando diverse

modalità  con  i  campi  DURATA,  MESE_VALIDITA  e  VALIDO_FINO.  Le  3  modalità  di

trasmissione  sono  sempre  alternative.  Inoltre,  solo  il  campo  VALIDO_FINO  può  essere

utilizzato in più IntervalliPrezzo per la stessa ComponenteImpresa.

18. Offerta  FLAT  -  Il  Venditore  deve  selezionare  TIPO_OFFERTA=03,  inserire  una  sola

ComponenteImpresa che contenga il prezzo della materia energia e il CONSUMO_MIN e

CONSUMO_MAX  entro  i  quali  l’offerta  è  valida.  Tale  prezzo,  moltiplicato  per  il  limite

superiore  dello  scaglione  di  consumo  (CONSUMO_MAX),  restituisce  l’importo  in  euro

previsto per la “taglia”.

ESEMPIO: Offerta FLAT energia  elettrica che prevede taglia di 20€/mese per clienti per

consumi annuali da 1000 a 3000 kWh. Il venditore inserirà nel flusso un prezzo di x €/kWh.

Il Portale calcolerà tutte le sezioni della spesa (trasporto, oneri, imposte e materia prima

energia)  prendendo  a  riferimento  3000  kWh/anno.  La  sezione  spesa  Materia  prima

energia=3000 kWh * x €/kWh.

Eventuali  compensazioni  per  consumi  inferiori  o  superiori  alla  taglia  dovranno

obbligatoriamente essere descritte nei campi testo preposti del flusso. Tali compensazioni

non contribuiranno al calcolo della stima della spesa annua.

19. Offerta MISTA - Dal 01/04/2026 il Venditore che intenda trasmettere questo tipo di offerta

deve selezionare TIPO_OFFERTA = 04 e valorizzare il campo TIPO_PREZZO nella sezione

“ComponenteImpresa/IntervalloPrezzi”  per  definire  se

la  componente

impresa

corrispondente debba essere considerata per un calcolo a prezzo fisso o variabile.

20. Offerta ONNICOMPRENSIVA – Dal 01/04/2026 il Venditore che intenda trasmettere questo

tipo  di

offerta

(esclusivamente  per

clienti  domestici)  deve

selezionare

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

28/70

OFFERTA_ONNICOMPRENSIVA  =  01  e  inserire  una  sola  componente  impresa  in

MACROAREA  =  01  con  UNITA_MISURA  =  01  e  una  sola  in  MACROAREA  =  02  con

UNITA_MISURA = 03 per offerte EE e con UNITA_MISURA = 04 per offerte GAS.

21. Offerta  ONNICOMPRENSIVA  A  CANONE  -  Dal  01/04/2026  il  Venditore  che  intenda

trasmettere questo tipo di offerta (esclusivamente per clienti domestici) deve selezionare

OFFERTA_ONNICOMPRENSIVA  =  02  e  inserire  una  sola  componente  impresa  in

MACROAREA = 01 con UNITA_MISURA = 01 (da intendersi come canone annuale) e una

sola in MACROAREA = 02 con UNITA_MISURA = 03 per offerte EE e con UNITA_MISURA

= 04 per offerte GAS (da intendersi come corrispettivo con il quale vengono conguagliati

consumi in difetto o in eccesso rispetto al consumo di riferimento dell'offerta, indicato nel

campo CONSUMO_CANONE).

22. Somma  di  indici  -  Per le offerte destinate ai clienti domestici,  dal 01/04/2026 è possibile

trasmettere più  di un  indice di  riferimento,  ad  ognuno dei  quali deve  essere  attribuito  un

coefficiente  moltiplicativo  compreso  fra  0  e  2  (nel  campo  COEFFICIENTE  della  sezione

“RiferimentiPrezzoEnergia”)  e  la  fascia  oraria  a  cui  deve  essere  applicato  (nel  campo

FASCIA_PREZZO della sezione “RiferimentiPrezzoEnergia”); gli indici di riferimento identificati

dal  venditore  saranno  sommati

in  combinazione

lineare  (ad  es.  [Indice1*coeff1  +

Indice2*coeff2]).  È  possibile  anche  applicare  uno  spread  percentuale  a  un

indice,

valorizzando il relativo coefficiente con un valore maggiore di 1 (es. per spread pari al 10%

del PUN il coefficiente dev’essere pari a 1,1) e indicando uno spread pari a 0.

Il valore inserito nel campo COEFFICIENTE può essere maggiore di 1 solo se viene indicato un

solo indice.

23. È  possibile  applicare  uno  sconto,  espresso  in  percentuale,  ad  una  o  più  componenti

regolate  inserendo  i  relativi  codici  (01-10)  nel  campo  CODICE_COMPONENTE_FASCIA

della sezione Sconto.

24. È  possibile  differenziare  uno

sconto  per

fascia

valorizzando

il

campo

CODICE_COMPONENTE_FASCIA con i codici da 11 a 18.

25. Nella  sezione  ComponenteImpresa  se  il  venditore  utilizza  scaglioni  di  consumo  (campi

CONSUMO_DA  e  CONSUMO_A  della  sottosezione  IntevalloPrezzi)  e/o  la  validità  delle

condizioni  economiche  (campi  DURATA,  MESE_VALIDITA  e  VALIDO_FINO  nella

sottosezione IntervalloPrezzi/PeriodoValidita) è necessario aggiungere un Intervallo prezzi

che non abbia nessuno dei predetti campi valorizzati. Tale prezzo è considerato di “default”

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

29/70

e  utilizzato  nella  stima  della  spesa  solo  nel  caso  in  cui  ci  siano  periodi  temporali  e/o

scaglioni di consumo non coperti dai prezzi trasmessi.

  Annullamento Trasmissione Offerta

Al  fine  di  garantire  tempi  di  risposta  ridotti  in  fase  di  trasmissione  delle  offerte  Retail,  il  SII
restituisce una prima ammissibilità qualora il tracciato sia conforme ai flussi di ammissibilità citati
nell’appendice A.

In una fase successiva il sistema provvede ad elaborare le offerte ammissibili, applicando ulteriori
controlli di coerenza che consentono la corretta applicazione delle logiche di calcolo della spesa.
Qualora  tali  controlli  non  vengano  superati  il  SII  provvede  a  richiamare  il  processo  di
annullamento  della  pratica  su  cui  si  è  rilevato  l’errore  effettuando  un  eventuale  storno  alla
situazione  strettamente  precedente,  infatti  nel  caso  di  annullamento  di  una  pratica  di
aggiornamento, l’offerta sarà ripristinata al tracciato ammissibile più recente.

La motivazione dell’annullamento, sarà sempre visibile nella sezione Storico della Gestione delle
offerte, inoltre qualora la trasmissione avvenga attraverso PdC, verrà comunicata alla CC, tramite
medesimo
–
Specifiche_tecniche_Annullamento_AllA_v7.0).

annullamento

notifica

canale,

(APN

una

di

In  caso  di  annullamento  di  una  pratica  di  inserimento,  il  CODICE_OFFERTA  potrà  essere
riutilizzato nella eventuale trasmissione successiva.

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

30/70

6  Specifiche tecniche del Processo di Trasmissione Offerta

Nel presente capitolo sono descritti i flussi previsti nel SII per il processo di Trasmissione Offerta

TO composto dal solo servizio:

•

 TO1 - Trasmissione Offerta PLACET: che consente la trasmissione delle informazioni

relative alle offerte PLACET del mercato elettrico e gas.

6.1  Trasmissione offerta PLACET

Il  processo  è  composto  dal  servizio  TO1,  nei  paragrafi  successivi  sono  descritti  i  flussi  per  la
trasmissione delle offerte elettriche e gas.

Controparte
 commerciale

 Placet Settore Elettrico

Gestore

Trasmissione Offerta EE
TO1.0050

AmmissibilitàRichiesta
VTG1.0100

AmmissibilitàOffertaEE
TO1.0100

 Placet Settore GAS

Trasmissione Offerta GAS
TO1.0051

AmmissibilitàOffertaGAS
TO1.0101

S
I
I

La trasmissione delle offerte comprende le seguenti operazioni:

1.  TrasmissioneOffertaEE  (TO1.0050).  L’Utente  trasmette  le  offerte  PLACET  per  la

commodity elettrica.

2.  AmmissibilitàOffertaEE   (TO1.0100). Il SII verifica l’ammissibilità della richiesta  e, in

caso positivo, apre la pratica assegnando il numero di protocollo.

3.  TrasmissioneOffertaGAS  (TO1.0051).  L’Utente  trasmette  le  offerte  PLACET  per  la

commodity gas.

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

31/70

4.  AmmissibilitàOfferteGAS (TO1.0101). Il SII verifica l’ammissibilità della richiesta e, in

caso positivo, apre la pratica assegnando il numero di protocollo.

Nei  paragrafi  seguenti  sono  specificate  le  operazioni  previste  nella  fase  di  trasmissione  e  i
corrispondenti messaggi.

  TO1.0050 - Trasmissione offerta EE

Mediante il flusso TO1.0050 la Controparte commerciale trasmette le offerte PLACET al SII per la

commodity elettrica.

SEZIONE

OBBLIGATORI
ETA SEZIONE

DATI

OBBLIGATOR
IETA’  DATO

DESCRIZIONE

FORMATO
/VINCOLI

N/A

SI

COD_SERVIZIO

SI

COD_FLUSSO

SI

“TO1”

“0050”

PIVA_UTENTE

SI

Partita IVA del Utente che
richiede l’attivazione

Alfanumerico (16)

Identificativi
Richiesta

SI

PIVA_GESTORE

SI

Partita Iva del Gestore del SII  Alfanumerico (16)

CP_UTENTE

SI

Codice univoco di protocollo
associato alla pratica aperta

Alfanumerico (15)

TIPO_CLIENTE

SI

Tipologia di cliente finale

01: Domestico

Numerico (2)

DettaglioOffert
a

SI

TIPO_CONTRAT
TO

MODALITA_ATTI
VAZIONE

SI

SI

02: BT Altri Usi

Contratto redatto su modello
ARERA

01: SI

02: NO

Definisce le modalità di
attivazione dell’offerta

ALFANUMERICO (11)
01:Offerta attivabile
solo da web
02:Offerta attivabile
da qualsiasi canale
03: Presso punto
vendita

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

32/70

NOME_OFFERTA

SI

COD_OFFERTA

SI

Nome dell’offerta:

VENDITORE TIPO-OFFERTA
SETTORE TIPO-CLIENTE
NOME-OFFERTA

Ad esempio: “Venditore1
Placet Fissa Ele Domestici
Casa”

Cosi come riportato nell’art.
3.1 del 555/17

Codice univoco per offerta
presente sui sistemi del
Venditore che sarà indicato nel
campo CODICE CONTRATTO in
fase di sottoscrizione
dell’offerta da parte del cliente
finale nella richiesta di
switching.

MODALITA_PAG
AMENTO

SI

Modalità di pagamento rese
disponibili al cliente

04: Teleselling

05:Agenzia

06:Altro

Per elenco: i singoli
codici sono Numerico
2 separati da “,”

Esempio: ‘01,02,…’

Alfanumerico (55)

Alfanumerico (32)

Alfanumerico (14)

01: Domiciliazione
bancaria

02: Domiciliazione
postale

03: Domiciliazione su
carta di credito

04: Bollettino
precompilato

05: Altro

Per elenco: i singoli
codici sono Numerico
2 separati da “,”

Esempio: ‘01,02,…’

Numerico (2)

TIPO_OFFERTA

SI

Tipologia offerta inserita

01: Placet Fisso

02: Placet Variabile

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

DettaglioOffert
a/Contatti

SI

ComponentiPr
ezzoElettrico

SI

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

33/70

URL_OFFERTA

SI

TELEFONO

URL_SITO_VEN
DITORE

SI

SI

SI

P_FIX_F

P_FIX_V

PVOL_F1

PVOL_F2

PVOL_F3

(se
TIPO_OFFERT
A=01)

SI

(se
TIPO_OFFERT
A=02)

SI

(se
TIPO_OFFERT
A=01 e
TIPO_CLIENTE
= 02)

PVOL_B_F1

PVOL_B_F23

SI

(se
TIPO_OFFERT
A=01 e
TIPO_CLIENT
= 01)

PVOL_MONORAR
IA

SI

(se
TIPO_OFFERT
A=01)

Indica la pagina dell’offerta sul
sito del venditore. La URL non
deve contenere il carattere
punto e virgola ‘;’

ALFANUMERICO
(100)

Indica il recapito telefonico  ALFANUMERICO (15)

ALFANUMERICO
(100)

Numerico (4,2)

Separatore=’.’

Numerico (4,2)

Separatore=’.’

Numerico (1,5)

Separatore=’.’

Indica il sito web del venditore

Rappresenta la componente
espressa in quota punto di
prelievo (€/POD/anno)
nell’offerta a prezzo fisso

Rappresenta la componente
espressa in quota punto di
prelievo (€/POD/anno)
nell’offerta a prezzo variabile

Rappresenta la componente
espressa in quota energia
(€/kWh) nelle fasce orarie F1,
F2 e F3 a prezzo fisso.

In caso di offerta a prezzo
fisso è comprensiva delle
perdite di rete.

In caso di offerta a prezzo
variabile il SII calcola il

Pvol=(1+λ)*(P_INGM+α)

Rappresenta la componente
espressa in quota energia
(€/kWh) nelle fasce biorarie
F1, F23 a prezzo fisso.

In caso di offerta a prezzo
fisso è comprensiva delle
perdite di rete.

Numerico (1,5)

Separatore=’.’

In caso di offerta a prezzo
variabile il SII calcola il
Pvol=(1+λ)*(P_INGM+α)

Rappresenta la componente
espressa in quota energia
(€/kWh) monoraria a prezzo
fisso.

In caso di offerta a prezzo
fisso è comprensiva delle
perdite di rete.

Numerico (1,5)

Separatore=’.’

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

34/70

In caso di offerta a prezzo
variabile il SII calcola il

Pvol=(1+λ)*(P_INGM+α)

Parametro α, determinato dal
venditore al netto delle
perdite, fisso e invariabile per
12 mesi dalla data di
attivazione della fornitura,
espresso in €/kWh
rappresentativo dei costi per
la spesa della materia prima
non coperti dal PUN

Numerico (1,5)

Separatore=’.’

ALPHA

SI (se
TIPO_OFFERT
A=02)

DATA_INIZIO

DATA_FINE

SI

SI

Data di inizio della validità
dell’offerta

Alfanumerico (10)
GG/MM/AAAA

Data di termine della validità
dell’offerta

Alfanumerico (10)
GG/MM/AAAA

REGIONE

NO

Elenco Codici Istat delle
regioni in cui l'esercente
propone l'offerta PLACET.

PROVINCIA

NO

Elenco Codici Istat delle
provincie in cui l'esercente
propone l'offerta PLACET.

COMUNE

NO

Elenco Codici Istat dei comuni
in cui l'esercente propone
l'offerta PLACET.

Alfanumerico (60)

dove i singoli codici
istat sono Numerico 2
separati da “,” nel
formato:

‘<IstatRegione1>,<
IstatRegione2>, …’

Alfanumerico (4000)

dove i singoli codici
istat sono Numerico 3
separti da “,” nel
formato:

‘<IstatProvincia1>,<
IstatProvincia2>, …’

Alfanumerico
(55.000)

dove i singoli codici
istat sono Numerico 6
separti da “,” nel
formato:

‘<IstatProvincia1>,<
IstatProvincia2>, …’

ZonaOfferta

NO

(Se la zona di
offerta non è
valorizzata
l’offerta è
considerata
proposta su
tutto il territorio
nazionale)

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

35/70

Tracciato CSV

COD_SERVIZIO;COD_FLUSSO;PIVA_UTENTE;PIVA_GESTORE;CP_UTENTE;TIPO_CLIENTE;TIPO_CONTRATTO;MODALITA_ATTIV
AZIONE;NOME_OFFERTA;COD_OFFERTA;MODALITA_PAGAMENTO;TIPO_OFFERTA;URL_OFFERTA;TELEFONO;URL_SITO_VENDITO
RE;P_FIX_F;P_FIX_V;PVOL_F1;PVOL_F2;PVOL_F3;PVOL_B_F1;PVOL_B_F23;PVOL_MONORARIA;ALPHA;DATA_INIZIO;DATA
_FINE;REGIONE;PROVINCIA;COMUNE

  TO1.0100 – Ammissibilità offerta EE

Alla  ricezione  di  un  messaggio  di  richiesta  di  Trasmissione  Offerta  PLACET,  il  SII  verifica  la

coerenza delle informazioni riportate nel messaggio e, in caso di ammissibilità positiva, apre una

pratica assegnando un numero di protocollo.

In particolare, l’ammissibilità della verifica sarà negativa (VerificaAMM=0) se:

1.  I campi obbligatori sono tutti correttamente compilati

2.  A parità di intervallo temporale non è presente sia un’offerta fissa che un’offerta variabile

su una medesima zona.

3.  I campi relativi alle estensioni non sono riferiti a codici ISTAT validi.

4.  La DATA_INIZIO è antecedente alla data di ricezione del flusso.

SEZIONE

OBBLIGATORI
ETÀ SEZIONE

DATI

OBBLIGATORIET
À DATO

DESCRIZIONE

FORMATO
/VINCOLO

N/A

N/A

Identificativi
Richiesta

SI

COD_SERVIZIO

COD_FLUSSO

PIVA_UTENTE

PIVA_GESTORE

CP_UTENTE

SI

SI

SI

SI

SI

SI

CP_GESTORE

(obbligatorio se
VERIFICA_AMM =
1)

“TO1”

“0100”

Alfanumerico (16)

Alfanumerico (16)

Alfanumerico (15)

Alfanumerico (15)

Partita IVA del
Utente che
richiede
l’attivazione

Partita IVA del
Gestore del SII

Codice Pratica
definito dall’
Utente richiedente

Codice Pratica
definito dal
Gestore del SII

Ammissibilità

SI

VERIFICA_AMM

SI

Esito della verifica
di ammissibilità

Numerico (0/1)

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

36/70

COD_CAUSALE

SI

(obbligatorio se
VERIFICA_AMM =
0)

Descrizione
dell’esito di
inammissibilità –
Codifica

Dove:

-  ‘0’ = “Negativo”

-  ‘1’ = “Positivo”

Alfanumerico (3)

Vedi Tab. A.1

MOTIVAZIONE

SI (obbligatorio se
VERIFICA_AMM =
0)

Motivazione della
causale di
inammissibilità

Alfanumerico
(255)

Tracciato CSV

COD_SERVIZIO;COD_FLUSSO;PIVA_UTENTE;PIVA_GESTORE;CP_UTENTE;CP_GESTORE;VERIFICA_AMM;COD_CAUSALE;MOTIVA
ZIONE

  TO1.0051 - Trasmissione offerta GAS

Mediante il flusso TO1.0051 la Controparte commerciale trasmette le offerte PLACET al SII per il

mercato gas.

SEZIONE

OBBLIGATORI
ETA SEZIONE

DATI

OBBLIGATOR
IETA’  DATO

DESCRIZIONE

FORMATO
/VINCOLI

N/A

SI

COD_SERVIZIO

SI

COD_FLUSSO

SI

“TO1”

“0051”

IdentificativiRi
chiesta

SI

PIVA_UTENTE

SI

Partita IVA del Utente che
richiede l’attivazione

Alfanumerico (16)

PIVA_GESTORE

SI

Partita Iva del Gestore del SII  Alfanumerico (16)

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

37/70

CP_UTENTE

SI

Codice univoco di protocollo
associato alla pratica aperta

Alfanumerico (15)

TIPO_CLIENTE

SI

Tipologia di cliente finale

Numerico 2

01: Domestico

03: Altri Usi
<200.000 Smc/anno

04: CONDOMINI USO
DOM <200.000
Smc/anno

TIPO_CONTRAT
TO

SI

Contratto redatto su modello
ARERA

01: SI

02: NO

MODALITA_ATTI
VAZIONE

SI

Definisce le modalità di
attivazione dell’offerta

DatiOfferta

SI

NOME_OFFERTA

SI

COD_OFFERTA

SI

Nome dell’offerta:

VENDITORE TIPO-OFFERTA
SETTORE TIPO-CLIENTE
NOME-OFFERTA

Ad esempio: “Venditore1
Placet Fissa Gas Domestici
Casa”

Cosi come riportato nell’art.
3.1 del 555/17

Codice univoco per offerta
presente sui sistemi del
Venditore che sarà indicato nel
campo CODICE CONTRATTO in
fase di sottoscrizione
dell’offerta da parte del cliente
finale nella richiesta di
switching.

ALFANUMERICO (11)
01:Offerta attivabile
solo da web
02:Offerta attivabile
da qualsiasi canale
03: Presso punto
vendita
04: Teleselling

05:Agenzia

06:Altro

Per elenco: i singoli
codici sono Numerico
2 separati da “,”

Esempio: ‘01,02,…’

Alfanumerico (55)

Alfanumerico (32)

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

38/70

MODALITA_PAG
AMENTO

SI

Modalità di pagamento rese
disponibili al cliente

TIPO_OFFERTA

SI

Tipologia offerta inserita

Alfanumerico (14)

01: Domiciliazione
bancaria

02: Domiciliazione
postale

03: Domiciliazione su
carta di credito

04: Bollettino
precompilato

05: Altro

Per elenco: i singoli
codici sono Numerico
2 separati da “,”

Esempio: ‘01,02,…’

01: Placet Fisso

02: Placet Variabile

URL_OFFERTA

SI

Indica la pagina dell’offerta del
venditore

ALFANUMERICO
(100)

DettaglioOffert
a/Contatti

SI

TELEFONO

URL_SITO_VEN
DITORE

SI

SI

Indica il recapito telefonico

ALFANUMERICO (15)

Indica il sito web del venditore

ALFANUMERICO
(100)

P_FIX_F

P_FIX_V

SI (se
TIPO_OFFERT
A=01)

Rappresenta
la  componente
espressa  in  quota  punto  di
riconsegna (€/PDR/anno);

Numerico (4,2)

Separatore=’.’

SI (se
TIPO_OFFERT
A=02)

Rappresenta
la  componente
espressa  in  quota  punto  di
riconsegna (€/PDR/anno);

Numerico (4,2)

Separatore=’.’

ComponentiPr
ezzoGas

SI

PVOL

SI

(se
TIPO_OFFERT
A=01)

Rappresenta  la  componente  α
espressa
in  quota  energia
(€/Smc) a prezzo fisso.

In  caso  di  offerta  a  prezzo
variabile il SII calcola il

Numerico (1,5)

Separatore=’.’

Pvol=P_INGT+α

ALPHA

Si (se
TIPO_OFFERT
A=02)

Parametro  α,  determinato  dal
venditore,  fisso  e  invariabile
per  12  mesi  dalla  data  di
fornitura,
attivazione  della
espresso in €/Smc, a copertura
di
degli
e
approvvigionamento

ulteriori

costi

Numerico (1,5)

Separatore=’.’

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

39/70

consegna  del  gas  naturale  al
cliente finale

DATA_INIZIO

DATA_FINE

SI

SI

Data  di  inizio  della  validità
dell’offerta

Alfanumerico (10)
(gg/mm/aaaa)

Data  di  termine  della  validità
dell’offerta

Alfanumerico (10)
(gg/mm/aaaa)

REGIONE

NO

Elenco Codici Istat delle
regioni in cui l'esercente
propone l'offerta PLACET.

ZonaOfferta

NO

(Se la zona di
offerta non è
valorizzata
l’offerta è
considerata
proposta su
tutto il territorio
nazionale)

PROVINCIA

NO

Elenco Codici Istat delle
provincie in cui l'esercente
propone l'offerta PLACET.

COMUNE

NO

Elenco Codici Istat dei comuni
in cui l'esercente propone
l'offerta PLACET.

Alfanumerico (60)

dove i singoli codici
istat sono Numerico 2
separti da “,” nel
formato:

‘<IstatRegione1>,<
IstatRegione2>, …’

Alfanumerico (60)

dove i singoli codici
istat sono Numerico 3
separti da “,” nel
formato:

‘<IstatProvincia1>,<
IstatProvincia2>, …’

Alfanumerico
(55.000)

dove i singoli codici
istat sono Numerico 6
separti da “,” nel
formato:

‘<IstatProvincia1>,<
IstatProvincia2>, …’

Tracciato CSV

COD_SERVIZIO;COD_FLUSSO;PIVA_UTENTE;PIVA_GESTORE;CP_UTENTE;TIPO_CLIENTE;TIPO_CONTRATTO;MODALITA_ATTIV
AZIONE;NOME_OFFERTA;COD_OFFERTA;MODALITA_PAGAMENTO;TIPO_OFFERTA;URL_OFFERTA;TELEFONO;URL_SITO_VENDITO
RE;P_FIX_F;P_FIX_V;PVOL;ALPHA;DATA_INIZIO;DATA_FINE;REGIONE;PROVINCIA;COMUNE

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

40/70

  TO1.0101 - Ammissibilità offerta GAS

Alla  ricezione  di  un  messaggio  di  richiesta  di  Trasmissione  Offerta  PLACET,  il  SII  verifica  la

coerenza delle informazioni riportate nel messaggio e, in caso di ammissibilità positiva, apre una

pratica assegnando un numero di protocollo.

In particolare, l’ammissibilità della verifica sarà negativo (VerificaAMM=0) se:

1.  I campi obbligatori sono tutti correttamente compilati

2.  A parità di intervallo temporale non è presente sia un’offerta fissa che un’offerta variabile

su una medesima zona.

3.  I campi relativi alle estensioni non sono riferiti a codici ISTAT validi.

4.  La DATA_INIZIO è antecedente alla data di ricezione del flusso.

SEZIONE

OBBLIGATORI
ETÀ SEZIONE

DATI

OBBLIGATORIET
À DATO

DESCRIZIONE

N/A

N/A

Identificativi
Richiesta

SI

COD_SERVIZIO

COD_FLUSSO

PIVA_UTENTE

PIVA_GESTORE

CP_UTENTE

SI

SI

SI

SI

SI

Partita IVA del
Utente che
richiede
l’attivazione

Partita IVA del
Gestore del SII

Codice Pratica
definito dall’
Utente richiedente

Ammissibilità

SI

CP_GESTORE

SI (obbligatorio se
VERIFICA_AMM =
1)

Codice Pratica
definito dal
Gestore del SII

VERIFICA_AMM

SI

Esito della verifica
di ammissibilità

COD_CAUSALE

SI

(obbligatorio se
VERIFICA_AMM =
0)

Descrizione
dell’esito di
inammissibilità –
Codifica

FORMATO
/VINCOLO

“TO1”

“0101”

Alfanumerico (16)

Alfanumerico (16)

Alfanumerico (15)

Alfanumerico (15)

Numerico (0/1)

Dove:

-  ‘0’ = “Negativo”

-  ‘1’ = “Positivo”

Alfanumerico (3)

Vedi Tab. A.1

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

41/70

MOTIVAZIONE

SI (obbligatorio se
VERIFICA_AMM =
0)

Motivazione della
causale di
inammissibilità

Alfanumerico
(255)

Tracciato CSV

COD_SERVIZIO;COD_FLUSSO;PIVA_UTENTE;PIVA_GESTORE;CP_UTENTE;CP_GESTORE;VERIFICA_AMM;COD_CAUSALE;MOTIVA
ZIONE

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

42/70

6.2  Trasmissione offerta MERCATO LIBERO

La presente procedura descrive le modalità e i flussi per la trasmissione dell’offerte per il Mercato

Libero al SII mediante il processo di Trasmissione Offerte Mercato Libero (TO2).

Il  processo  si  occupa  della  trasmissione  delle  Offerte  del  Libero  Mercato  al  SII  da  parte  delle

controparti commerciali.

Le controparti commerciali potranno trasmettere al SII le Offerte del Mercato Libero, mediante i

seguenti tre flussi:

o  TrasmissioneOfferta (TO2.0050) mediante il quale la controparte commerciale trasmette

al SII un’offerta del Mercato Libero per la fornitura di energia elettrica, gas o dual fuel;

o  AggiornamentoOfferta  (TO2.0051)  mediante  il  quale  la  controparte  commerciale,  con

l’obiettivo  di  aggiornarne  alcuni  parametri  di  un’offerta,  trasmette  al  SII  un’offerta  in

sostituzione di una precedentemente comunicata o in riapertura di un’offerta scaduta;

o  EliminaOfferta  (TO2.0052)  mediante  il  quale  la  controparte  commerciale  trasmette

l’identificativo di un’offerta al SII per eliminarla.

Un’offerta è descritta mediante un file xml conforme alla struttura indicata al paragrafo  7.1. Il

file è allegato ad un messaggio A2A di Trasmissione o Aggiornamento.

È  anche  possibile  trasmettere  il  file  tramite  il  Portale  Web,  lasciando  a  quest’ultimo  l’onere  di

generare il messaggioPdC verso il SII garantendo la tracciatura dell’azione.

  TO2.0050 - Trasmissione offerta

Mediante il flusso TO2.0050 la Controparte commerciale trasmette una nuova offerta del Mercato

Libero al SII.

L’offerta  sarà  identificata  dai  parametri  COD_OFFERTA  +  PIVA_UTENTE,  quindi,  per  uno

stesso Utente non saranno accettate 2 o più offerte con il medesimo  COD_OFFERTA, anche se

validi  in  periodi  temporali  differenti  o  di  tipologia  differente  (PLACET,  RETAIL,  RETAIL  non

simulabili).

Alla ricezione del file, il SII verifica il rispetto dei formati secondo quanto descritto e restituisce

all’Utente  una  risposta  contenente  l’esito  di  tali  verifiche.  In  caso  di  esito  negativo,  il  file

trasmesso viene scartato.

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

43/70

SEZIONE

OBBLIGATORI
ETÀ SEZIONE

DATI

OBBLIGATORI
ETÀ DATO

DESCRIZIONE

N/A

Identificativi
Richiesta

COD_SERVIZIO

COD_FLUSSO

PIVA_UTENTE

PIVA_GESTORE

CP_UTENTE

SI

SI

SI

SI

SI

COD_OFFERTA

SI

FORMATO
/VINCOLO

“TO2”

“0050”

Partita IVA utente

Alfanumerico (16)

Partita IVA del
Gestore

Codice Pratica
definito dall’
Utente richiedente

Codice
identificativo
dell’offerta
trasmessa in
allegato

Alfanumerico (16)

Alfanumerico (15)

Alfanumerico (32)

TIPO_FILE

SI

Specifica  il  tipo  di
file trasmesso

Alfanumerico (3)
“XML”

Informazione
Trasmissione

SI

IDENTIFICATIVO
_FILE

VERSIONE_FOR
MATO_FILE

SI

SI

N/A

N/A

FILE_ALLEGATO

SI

Alfanumerico (255)

Valore univoco per
ciascun file di dati
dell’offerta
(es:timestamp+
nome del file)

Alfanumerico (2)

01: Tracciato
versione Retail 01

Riferimento
mnemonico
all’allegato
trasmesso

Codice che
identifica le
tipologie di
formato attuali o
future del
tracciato

Rappresenta il file
dei dati trasmesso

Formati in conformità
a  quanto  specificato
al capitolo 7

Nome File Allegato XML per Inserimento MASSIVO

<CP_UTENTE>_<COD_OFFERTA>_<DESCRIZIONE>.XML

•  CP_UTENTE:  Codice  Pratica  definito  dall’  Utente  richiedente  (max  15  caratteri

alfanumerici)

•  COD_OFFERTA:  Codice  identificativo  dell’offerta  (max  32*  caratteri  alfanumerici,

sono esclusi tutti i caratteri speciali)

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

44/70

•  DESCRIZIONE: campo libero, massimo 25 caratteri alfanumerici (non ammessi spazi,

“_” o caratteri speciali)

*  Nel  transitorio  dal  1  ottobre  2022  al  1  gennaio  2023  saranno  accettati  codici  offerta  a  35
caratteri per il TIPO_MERCATO = 02 e 03.

Nel  caso  in  cui  il  sistema  rilevi  errori  nel  nome  file  restituirà  determinati  messaggi  di  errore,
oppure  in  caso  di  anomalie  su  alcuni  dei  file  caricati,  potrà  essere  completata  la  trasmissione
parziale.

  TO2.0100 – Ammissibilità offerta

Alla ricezione di un messaggio di richiesta di Trasmissione Offerta, il SII verifica la coerenza delle

informazioni  riportate  nel  messaggio  e,  in  caso  di  ammissibilità  positiva,  apre  una  pratica

assegnando un numero di protocollo.

In particolare, l’ammissibilità della verifica sarà positivo (VerificaAMM=1) se:

1)  I campi obbligatori sono tutti correttamente compilati

2)  La DATA_INIZIO non è antecedente alla data di ricezione del flusso

3)  Non esiste un’offerta valida con lo stesso COD_OFFERTA

SEZIONE

OBBLIGATORI
ETÀ SEZIONE

DATI

OBBLIGATORIET
À DATO

DESCRIZIONE

N/A

N/A

Identificativi
Richiesta

SI

COD_SERVIZIO

COD_FLUSSO

PIVA_UTENTE

PIVA_GESTORE

CP_UTENTE

SI

SI

SI

SI

SI

SI

CP_GESTORE

(obbligatorio se
VERIFICA_AMM =
1)

Partita IVA del
Utente che
richiede
l’attivazione

Partita IVA del
Gestore del SII

Codice Pratica
definito dall’
Utente richiedente

Codice Pratica
definito dal
Gestore del SII

FORMATO
/VINCOLO

“TO2”

“0100”

Alfanumerico (16)

Alfanumerico (16)

Alfanumerico (15)

Alfanumerico (15)

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

45/70

VERIFICA_AMM

SI

Esito della verifica
di ammissibilità

Ammissibilità

SI

COD_CAUSALE

SI

(obbligatorio se
VERIFICA_AMM =
0)

Descrizione
dell’esito di
inammissibilità –
Codifica

Numerico (0/1)

Dove:

-  ‘0’ = “Negativo”

-  ‘1’ = “Positivo”

Alfanumerico (3)

Vedi Tab. A.1

MOTIVAZIONE

SI (obbligatorio se
VERIFICA_AMM =
0)

Motivazione della
causale di
inammissibilità

Alfanumerico
(255)

  TO2.0051 - Aggiornamento Offerta

Mediante il flusso TO2.0051 la Controparte commerciale trasmette le offerte al SII per aggiornare

un’offerta già presente.

Poiché  l’offerta  è  identificata  dai  parametri  COD_OFFERTA  +  PIVA_UTENTE,  nel  SII,  per

l’Utente che trasmette l’aggiornamento deve già esistere l’offerta da modificare.

Alla ricezione del file, il SII verifica il rispetto dei formati secondo quanto descritto e restituisce

all’Utente  una  risposta  contenente  l’esito  di  teli  verifiche.  In  caso  di  esito  negativo,  il  file

trasmesso viene scartato.

Se  l’offerta  è  in  corso  di  validità  SYSDATE>=DATA_INIZIO  l’Utente  potrà  modificare

esclusivamente la DATA_FINE, MODALITA (Attivazione), MOD_PAGAMENTO, URL OFFERTA e la

lista  delle  OFFERTE_CONGIUNTE,  in  alternativa,  prima  che  l’offerta  diventi  attiva,  la  CC  potrà

variare

tutti

i

parametri

dell’offerta.  Qualora

invece

l’offerta

sia  SCADUTA

(SYSDATE>DATA_FINE) l’Utente potrà modificare esclusivamente DATA_INIZIO e DATA_FINE.

SEZIONE

OBBLIGATORI
ETÀ SEZIONE

DATI

OBBLIGATORIET
À DATO

DESCRIZIONE

N/A

Identificativi
Richiesta

COD_SERVIZIO

COD_FLUSSO

PIVA_UTENTE

PIVA_GESTORE

SI

SI

SI

SI

FORMATO
/VINCOLO

“TO2”

“0051”

Partita IVA utente  Alfanumerico (16)

Partita IVA del
Gestore

Alfanumerico (16)

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

46/70

CP_UTENTE

COD_OFFERTA

TIPO_FILE

Informazione
Trasmissione

SI

IDENTIFICATIVO
_FILE

VERSIONE_FOR
MATO_FILE

SI

SI

SI

SI

SI

N/A

N/A

FILE_ALLEGATO

SI

Codice Pratica
definito dall’
Utente richiedente

Codice
identificativo
dell’offerta

Alfanumerico (15)

Alfanumerico(32)*

Specifica  il  tipo  di
file trasmesso

Alfanumerico (3)
“XML”

Riferimento
mnemonico
all’allegato
trasmesso

Codice che
identifica le
tipologie di
formato attuali o
future del
tracciato

Rappresenta il file
dei dati trasmesso

Alfanumerico
(255)

Valore univoco per
ciascun  file  di  dati
dell’offerta
(es:timestamp+
nome del file)

Alfanumerico 2

01: Tracciato
versione Retail 01

in
Formati
conformità
a
quanto  specificato
al capitolo 7

Nome File Allegato XML per Aggiornamento5 MASSIVO:

<CP_UTENTE>_<COD_OFFERTA>_<DESCRIZIONE>.XML

•  CP_UTENTE:  Codice  Pratica  definito  dall’  Utente  richiedente  (max  15  caratteri

alfanumerici)

•  COD_OFFERTA: Codice identificativo dell’offerta (max 35 caratteri alfanumerici, sono

esclusi tutti i caratteri speciali tranne il carattere “underscore”, “.” e “-“)

•  DESCRIZIONE: campo libero, massimo 25 caratteri alfanumerici (non ammessi spazi,

“_” o caratteri speciali)

Nel  caso  in  cui  il  sistema  rilevi  errori  nel  nome  file  restituirà  determinati  messaggi  di  errore,
oppure  in  caso  di  anomalie  su  alcuni  dei  file  caricati,  potrà  essere  completata  la  trasmissione
parziale.

5 Informazione deducibile dal cod_servizio e cod_flusso del file compresso

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

47/70

  TO2.0101 - Ammissibilità offerta

Alla ricezione di un messaggio di richiesta di Aggiornamento Offerta, il SII verifica la coerenza

delle informazioni riportate nel messaggio e, in caso di ammissibilità positiva, aggiorna i dati della

pratica associata al COD_OFFERTA.

In particolare, l’ammissibilità della verifica sarà positivo (VerificaAMM=1) se:

1)  I campi obbligatori sono tutti correttamente compilati

2)  Esiste un’offerta già trasmessa da modificare

3)  In caso di una richiesta di modifica su un’offerta già attiva, i dati non modificabili sono

invariati

SEZIONE

OBBLIGATORI
ETÀ SEZIONE

DATI

OBBLIGATORIET
À DATO

DESCRIZIONE

N/A

N/A

Identificativi
Richiesta

SI

COD_SERVIZIO

COD_FLUSSO

PIVA_UTENTE

PIVA_GESTORE

CP_UTENTE

SI

SI

SI

SI

SI

Partita IVA del
Utente che
richiede
l’attivazione

Partita IVA del
Gestore del SII

Codice Pratica
definito dall’
Utente richiedente

CP_GESTORE

SI (obbligatorio se
VERIFICA_AMM =
1)

Codice Pratica
definito dal
Gestore del SII

VERIFICA_AMM

SI

Esito della verifica
di ammissibilità

Ammissibilità

SI

COD_CAUSALE

SI

(obbligatorio se
VERIFICA_AMM =
0)

Descrizione
dell’esito di
inammissibilità –
Codifica

FORMATO
/VINCOLO

“TO2”

“0101”

Alfanumerico (16)

Alfanumerico (16)

Alfanumerico (15)

Alfanumerico (15)

Numerico (0/1)

Dove:

-  ‘0’ = “Negativo”

-  ‘1’ = “Positivo”

Alfanumerico (3)

Vedi Tab. A.1

MOTIVAZIONE

SI (obbligatorio se
VERIFICA_AMM =
0)

Motivazione della
causale di
inammissibilità

Alfanumerico
(255)

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

48/70

  TO2.0052 - Elimina Offerta

Mediante  il  flusso  TO2.0052  la  Controparte  commerciale  trasmette  al  SII  il  codice  pratica  di

un’offerta  già  presente  (precedentemente  caricata)  per  eliminarla  specificando  attraverso

apposita causale la motivazione dell’eliminazione.

L’offerta sarà identificata dai parametri COD_OFFERTA & PIVA_UTENTE. L’utente potrà richiedere

l’eliminazione di offerte Attive o Non Attive, non è prevista l’eliminazione di offerte scadute.

SEZIONE

OBBLIGATORI
ETÀ SEZIONE

DATI

OBBLIGATORIET
À DATO

DESCRIZIONE

N/A

N/A

COD_SERVIZIO

COD_FLUSSO

PIVA_UTENTE

Identificativi
Richiesta

SI

PIVA_GESTORE

CP_UTENTE

SI

SI

SI

SI

SI

COD_OFFERTA

SI

Partita IVA del
Utente che
richiede
l’attivazione

Partita IVA del
Gestore del SII

Codice Pratica
definito dall’
Utente richiedente

Codice
identificativo
dell’offerta

Informazione
Trasmissione

SI

COD_CAUSALE

SI

Causale
eliminazione

FORMATO
/VINCOLO

“TO2”

“0101”

Alfanumerico (16)

Alfanumerico (16)

Alfanumerico (15)

Alfanumerico 35*

Alfanumerico (3)

Valori:

-

“Offerta
001
per
eliminata
errore
del
Venditore  in  fase
di trasmissione”

002 – “Altro”

MOTIVAZIONE

SI (obbligatorio se
COD_CAUSALE
=002)

Motivazione della
causale di
eliminazione

Alfanumerico
(255)

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

49/70

*Si specifica che per consentire l’eliminazione delle offerte trasmesse prima del 1 ottobre 2022
per il settore energia elettrica e del 1 gennaio 2023 per il settore gas naturale e per le dual fuel
verrà mantenuto in eliminazione la lunghezza del codice offerta a 35 caratteri.

Tracciato CSV – Eliminazione Massiva

COD_SERVIZIO;COD_FLUSSO;PIVA_UTENTE;PIVA_GESTORE;CP_UTENTE;COD_OFFERTA;COD_CAUSALE;MOTIVAZIONE

  TO2.0102 - Ammissibilità offerta

Alla ricezione di un messaggio di richiesta di Eliminazione Offerta, il SII verifica la coerenza delle

informazioni riportate nel messaggio.

In particolare, l’ammissibilità della verifica sarà positivo (VerificaAMM=1) se:

1.  I campi obbligatori sono tutti correttamente compilati

2.  Non esiste una pratica utente già caricata sul SII con il CP_UTENTE indicato, ma esiste

un’offerta con COD_OFFERTA già caricata sul SII.

3.  L’offerta  da  eliminare  non  sia  una  delle  OFFERTE  CONGIUNTE  di  una  DUAL  FUEL

(TIPO_MERCATO=03).

SEZIONE

OBBLIGATORI
ETÀ SEZIONE

DATI

OBBLIGATORIET
À DATO

DESCRIZIONE

N/A

N/A

Identificativi
Richiesta

SI

COD_SERVIZIO

COD_FLUSSO

PIVA_UTENTE

PIVA_GESTORE

CP_UTENTE

SI

SI

SI

SI

SI

FORMATO
/VINCOLO

“TO2”

“0102”

Partita IVA del
Utente che
richiede
l’attivazione

Partita IVA del
Gestore del SII

Codice Pratica
definito dall’
Utente richiedente

Alfanumerico (16)

Alfanumerico (16)

Alfanumerico (15)

CP_GESTORE

SI (obbligatorio se
VERIFICA_AMM =
1)

Codice Pratica
definito dal
Gestore del SII

Alfanumerico (15)

Ammissibilità

SI

VERIFICA_AMM

SI

Esito della verifica
di ammissibilità

Numerico (0/1)

Dove:

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

50/70

COD_CAUSALE

SI

(obbligatorio se
VERIFICA_AMM =
0)

Descrizione
dell’esito di
inammissibilità –
Codifica

-  ‘0’ = “Negativo”

-  ‘1’ = “Positivo”

Alfanumerico (3)

Vedi Tab. A.1

MOTIVAZIONE

SI (obbligatorio se
VERIFICA_AMM =
0)

Motivazione della
causale di
inammissibilità

Alfanumerico
(255)

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

51/70

7  Formato e tracciato delle Offerte

Nel presente capitolo sono riportati i formati ed i tracciati del file previsto per la trasmissione al

SII delle offerte del Mercato libero.

Il formato utilizzato per la rappresentazione è XML.  La codifica utilizzata è “UTF-8”, mentre gli

schemi da utilizzare per validazione dei  singoli  tracciati  sono specificati nei singoli paragrafi di

descrizione dei formati.

La nomenclatura da adottare per ogni singolo file XML è:

  <PIVA_UTENTE>_<AZIONE>_<DESCRIZIONE>.XML

<PIVA_UTENTE>: rappresenta la partita IVA dell’utente accreditato.

<AZIONE>: rappresenta l’azione da eseguire, le possibili valorizzazioni sono:

•

•

‘INSERIMENTO’: se il flusso identifica la trasmissione di una nuova offerta

‘AGGIORNAMENTO’: se il flusso identifica l’aggiornamento di un’offerta già presente

<DESCRIZIONE>: campo libero, massimo 25 caratteri alfanumerici (non ammessi spazi e “_”)

La trasmissione dei file tramite i messaggiPdC avviene utilizzando il formato XML eventualmente

compresso ed è il portale Web che in seguito al upload sul Portale del SII comprimere il file prima

di trasmetterlo.

Il file allegato dovrà necessariamente seguire la struttura e il formato dati definito nella tabella

seguente.

Nelle sezioni e nei campi non obbligatori si indica con (*) la possibilità di inserire 0 o più volte la

sezione o il campo a cui si fa riferimento. Invece, nei campi e nelle sezioni obbligatori si indicato

con (*) la possibilità di inserire 1 o più volte la sezione o il campo.

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

52/70

7.1  Formato Offerta

(tracciato disponibile dal 01/04/2026)

SEZIONE

OBBLIGATORI
ETA’ SEZIONE

DATI

OBBLIGATORI
ETA’  DATO

PIVA_UTENTE

SI

Identificativi
Offerta

SI

COD_OFFERTA

SI

DESCRIZIONE

Partita IVA del Utente che
richiede l’attivazione
Codice univoco per offerta
presente sui sistemi del
Venditore che sarà indicato
nel campo CODICE
CONTRATTO in fase di
sottoscrizione dell’offerta da
parte del cliente finale nella
richiesta di switching.

TIPO_MERCAT
O

SI

Definisce la commodity

OFFERTA_SING
OLA

SI (se
TIPO_MERCATO
diverso da 03)

Indica se è un’offerta può
essere sottoscritta
singolarmente, o anche se
legata ad un’offerta DUAL

TIPO_CLIENTE

SI

Tipologia di cliente finale

DettaglioOffert
a

SI

DOMESTICO_R
ESIDENTE

NO

Indica se l'Utente è
domestico residente o no

TIPO_OFFERTA

SI

Tipologia offerta inserita

OFFERTA_ONNI
COMPRENSIVA

NO

Indica se l’offerta è
onnicomprensiva o
onnicomprensiva a canone

CONSUMO_CA
NONE

SI (se
OFFERTA_ONNI
COMPRENSIVA
= ‘02’)

Indica il consumo di
riferimento dell’offerta
onnicomprensiva a canone
(espresso in kWh)

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

FORMATO/VIN
COLI
Alfanumerico
(16)

Alfanumerico
(32)

Alfanumerico (2)
01:Elettrico
02:Gas
03:Dual Fuel
Alfanumerico (2)
SI: offerta
sottoscrivibile
singolarmente
NO: offerta
sottoscrivibile
solo in
abbinamento con
offerta di altra
commodity
Numerico (2)
01:Domestico
02:Altri Usi
03: Condominio
Uso Domestico
(Gas)
Alfanumerico (2)
01:Domestico
Residente
02:Domestico
NON Residente
03: Tutte
Numerico (2)
01: Fisso
02: Variabile
03: FLAT
04: Mista
Numerico (2)
01: Offerta
onnicomprensiva
02: Offerta
onnicomprensiva
a canone

Numerico (9)

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

53/70

TIPOLOGIA_AT
T_CONTR (*)

NOME_OFFERT
A

DESCRIZIONE

DURATA

SI

SI

SI

SI

GARANZIE

SI

Indicazione delle casistiche
in cui l’offerta si ritiene
valida

Nome dell’offerta

Descrizione estesa
dell'offerta
Indica la durata delle
condizioni economiche,
espresso in mesi.
Descrizione delle garanzie
previste dal contratto (es.
depositi
cauzionali/domiciliazione).
Se nessuna garanzia = NO

DettaglioOffert
a/ModalitaAtti
vazione

SI

MODALITA (*)

SI

Definisce le modalità di
attivazione dell’offerta

DESCRIZIONE

SI (se
MODALITA =99)

DettaglioOffert
a/Contatti

SI

RiferimentiPre
zzoEnergia
(*)6

SI
(solo se
TIPO_OFFERTA
= ‘02’ o ‘04’ e
SCONTO/TIPOL
OGIA<>04 se
presente

TELEFONO

URL_SITO_VEN
DITORE

URL_OFFERTA

IDX_PREZZO_E
NERGIA

SI

SI

SI

SI

Descrizione della modalità di
attivazione
Indica il recapito telefonico
che l’impresa vuole rendere
disponibile al cliente per
essere contattata in merito
all’offerta
Indica il sito web del
venditore
Indica la pagina web
dell’offerta del venditore

Indica l’indice di riferimento
per il calcolo del prezzo
dell’energia

Numerico (2):
01: Cambio
Fornitore
02: Prima
Attivazione
(Contatore non
presente)
03: Riattivazione
(Contatore
presente ma
disattivato)
04: Voltura
99: sempre
Alfanumerico
(255)
Alfanumerico
(3000)
Numerico (2)
(se -1 =
indeterminata)

Alfanumerico
(3000)

Alfanumerico (2)
01:Offerta
attivabile solo da
web
02:Offerta
attivabile da
qualsiasi canale
03: Presso punto
vendita
04:Teleselling
05:Agenzia
99:Altro
Alfanumerico
(2000)

Alfanumerico
(15)

Alfanumerico
(100)
Alfanumerico
(100)
Numerico (2)
Periodicità7
- trimestrale
01: PUN Index
GME
02: TTF
03: PSV

6 Sezione ripetibile esclusivamente per TIPO_CLIENTE = ‘01’
7 Indica la periodicità di aggiornamento dell’indice ai soli fini della fatturazione al cliente finale, tale dato è riportato nella
scheda sintetica consultabile sul Portale Offerte. Si precisa che i forward utilizzati dal Portale Offerte per la simulazione
della spesa annua sono sempre PUN, TTF e PSV trimestrali, indipendentemente dalla periodicità.

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

54/70

almeno uno
sconto)

COEFFICIENTE

NO

Indica il coefficiente da
applicare all’indice in caso di
combinazione lineare di
indici diversi o di
applicazione di uno spread
percentuale

FASCIA_PREZZ
O

NO

Indica la fascia per la quale
è valido l’indice di
riferimento: se omesso,
l’indice viene applicato alla
totalità dei consumi

ALTRO

SI (Se
IDX_PREZZO_E
NERGIA=’99’)

DATA_INIZIO

DATA_FINE

SI

SI

Descrive l’indice utilizzato
dal Venditore se il campo
precedente è valorizzato in
modo generico ‘Altro’
Ad esempio “Brent”
Indica la data in formato
timestamp dell'inizio di
validità dell'offerta
Indica la data in formato
timestamp della fine validità
dell'offerta

ValiditaOfferta

SI

04: Psbil8
05: PE9
07: Pfor
- bimestrale
08: PUN Index
GME
09: TTF
10: PSV
11: Psbil
- mensile
06: Cmem10
12: PUN Index
GME
13: TTF
14: PSV
15: Psbil
99:Altro11

Numerico (1,1)
Ammessi valori
compresi fra 0 e
212

Alfanumerico
(2):
01:monorario/F1
02: F2
03: F3
04: F4
05: F5
06: F6
07:Peak
08:OffPeak

91: F2+F3
92: F1+F3
93: F1+F2

Alfanumerico
(3000)

GG/MM/AAAA_H
H:MM:SS

GG/MM/AAAA_H
H:MM:SS

Caratteristiche
Offerta

NO

CONSUMO_MIN

SI (se
TIPO_OFFERTA=
03)

Soglia minima di consumo
annuo del cliente al di sotto

Numerico (9)

8 Il Psbil è il prezzo di sbilanciamento di acquisto del gas naturale nel mercato all’ingrosso. Questi valori sono pubblicati
giornalmente dal GME. Ai fini della stima della spesa annua il portale offerte utilizza i forward trimestrali del PSV.
9 Da utilizzare esclusivamente in abbinamento a Sconto/PREZZISconto/TIPOLOGIA = 04
10 Da utilizzare esclusivamente in abbinamento a Sconto/PREZZISconto/TIPOLOGIA = 04
11 Il codice ‘99’ rappresenta un indice non gestito dal Portale Offerte, pertanto l’offerta è recepita dal SII, ma non sarà
visibile sul portale offerte. L’offerta sarà visibile appena il SII avrà implementato l’indice; l’Utente sarà informato circa le
relative tempistiche. Si precisa che la sola recezione dell’offerta rende l’Utente adempiente alla regolazione.
12 Il valore inserito può essere maggiore di 1 solo se viene indicato un solo indice.

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

55/70

CONSUMO_MA
X

SI (se
TIPO_OFFERTA=
03)

POTENZA_MIN

NO

POTENZA_MAX

NO

OFFERTE_CON
GIUNTE_EE (*)

OFFERTE_CON
GIUNTE_GAS
(*)

SI
(se
TIPO_MERCATO
=03)
SI
(se
TIPO_MERCATO
= 03)

della quale l'Offerta non è
valida (espresso in kWh)
Soglia massima di consumo
annuo del cliente al di sopra
della quale l'Offerta non è
valida (espresso in kWh)
Per le sole Offerte relative al
servizio elettrico indica la
soglia minima di potenza
impegnata al di sotto della
quale l'Offerta non è valida
(espresso in kW)
Per le sole Offerte relative al
servizio elettrico indica la
soglia massima di potenza
impegnata al di sotto della
quale l'Offerta non è valida
(espresso in kW)

Se valorizzato, rappresenta
la lista degli ID relativi alle
Offerte congiunte elettriche

Numerico (9)

Numerico (2,1)
Separatore ‘.’

Numerico (2,1)
Separatore ‘.’

Alfanumerico
(32)

Se valorizzato, rappresenta
la lista degli ID relativi alle
Offerte congiunte gas

Alfanumerico
(32)

OffertaDUAL

SI
(se
TIPO_MERCATO
= 03)

MetodoPagam
ento (*)

SI

MODALITA_PA
GAMENTO

SI

Indica una delle tipologie di
pagamento associate
all'offerta

Alfanumerico (2)

01:
Domiciliazione
bancaria
02:
Domiciliazione
postale
03:
Domiciliazione su
carta di credito
04: Bollettino
precompilato
99: Altro

DESCRIZIONE

SI (se
MODALITA_PAG
AMENTO=99)

Descrizione della modalità di
pagamento

Alfanumerico
(25)

ComponentiRe
golate

NO

CODICE
(*)

NO

Applicazione componente
definita dall’Autorità

Alfanumerico
(02)

Valori
TIPO_MERCATO = 01:
01:PCV
02:PPE
Valori
TIPO_MERCATO = 02:
03:CCR,
04:CPR,
05:GRAD,
06:QTint,
07:QTpsv,
09:QVD_fissa,
10:QVD_Variabile

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

56/70

TipoPrezzo

SI
(se
TIPO_MERCATO
=01 e
TIPO_OFFERTA
≠03)

TIPOLOGIA_FA
SCE

SI

Indica per quali fasce è
dedicata l’offerta.

Alfanumerico
(2):
01: monorario
02: F1, F2
03: F1, F2, F313
04: F1, F2, F3,F4
05: F1, F2, F3,
F4, F5
06: F1, F2, F3,
F4, F5, F6
07:
Peak/OffPeak14

91: “biorario (F1
/ F2+F3)”
92: “biorario (F2
/ F1+F3)”
93: “biorario (F3
/ F1+F2)”

13 La configurazione di TIPOLOGIA_FASCIA = 03 permette di ereditare la configurazione delle 3 fasce standard
(F1,F2,F3) qualora non venga valorizzata la sezione FasceOrarieSettimanali.
14  La  configurazione di  TIPOLOGIA_FASCIA  = 07 permette di  ereditare  le 2  fasce  standard  Peak/Offpeak dei  mercati
all’ingrosso (si veda Vademecum della Piattaforma dei Conti Energia a Termine) qualora non venga valorizzata la sezione
FasceOrarieSettimanali.

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

57/70

Alfanumerico
(49)
Formato

XXI-YI,XXII-
YII,..,XXN-YN

con
XXi (numerico da
1 a 96): ultimo
quarto d’ora di
applicazione
della fascia
Yi (numerico da 1
a 8) : numero
della fascia
applicata (7:Peak
, 8:Offpeak)

Devono essere
sempre verificate
le presenti
relazioni:
•
•

XXi+1>XXi
N <= 10

Es.
F3 : 00:01 –
07:00
F2 : 07:00 –
08:00
F1 : 08:00 –
19:00
F2 : 19:00 –
23:00
F3 : 23:00 –
24:00
diventa:
28-3,32-2,76-
1,92-2,96-3

Alfanumerico
(49)

Alfanumerico
(49)
Alfanumerico
(49)
Alfanumerico
(49)
Alfanumerico
(49)

F_LUNEDI

SI

Fasce orarie per il lunedì

FasceOrarieSe
ttimanale

SI
(se
TIPOLOGIA_FAS
CE =02 o 04 o
05 o 06)

F_MARTEDI

F_MERCOLEDI

F_GIOVEDI

F_VENERDI

F_SABATO

SI

SI

SI

SI

SI

Fasce orarie per il martedì

Fasce orarie per il mercoledì

Fasce orarie per il giovedì

Fasce orarie per il venerdì

Fasce orarie per il sabato

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

58/70

F_DOMENICA

F_FESTIVITA

SI

SI

Fasce orarie per la domenica

Fasce orarie per le festività

TIPO_DISPACC
IAMENTO

SI

Indica la componente
applicata (regolata o scelta
dal venditore) per il
dispacciamento

Dispacciament
o (*)

SI
(se
TIPO_MERCATO
=01)

VALORE_DISP

NOME

DESCRIZIONE

NOME

DESCRIZIONE

SI(se
TIPO_DISPACCI
AMENTO=99)

SI

NO

SI

SI

TIPOLOGIA

SI

MACROAREA

SI

Valore in €/kWh

Nome della componente

Descrizione della
componente
Nome della componente
impresa
Descrizione della
componente impresa
Tipologia della componente

Ad es. Energia da Fonti
rinnovabili se Standard il
prezzo dell’energia verde è
già incluso nel prezzo; se
Opzionale il prezzo
dell’energia verde non è
compreso nel prezzo.

Indica la macro area di
prezzo che vengono coperte
dalla componente impresa.
In funzione di questo, nel
portale, il valore della
componente verrà mostrato
nel dettaglio prezzi più
corretto

Componente
Impresa (*)

NO

Alfanumerico
(49)
Alfanumerico
(49)
Numerico (2)
01:Corrispettivo
Dispacciamento
02: PD
09: Corrispettivo
Capacità di
Mercato STG
10: Corrispettivo
capacità di
mercato MT
11:
Reintegrazione
oneri
salvaguardia
12:
Reintegrazione
oneri tutele
graduali
13: DispBT15
14: CdispD
99:Altro

Numerico (1,6)
Separatore ‘.’

Alfanumerico
(25)
Alfanumerico
(255)
Alfanumerico
(255)
Alfanumerico
(255)

Alfanumerico (2)

01: STANDARD
02:OPZIONALE

Numerico (2)

01:
Commercializzazi
one quota fissa
02:Commercializ
zazione quota
energia
04:Prezzo quota
energia
05: Una Tantum
06: FER/Energia
Verde

15 Indica se il venditore applica la DispBT in fatturazione, solo se selezionata dal venditore è considerata nel calcolo della
spesa del Portale Offerte.

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

59/70

ComponenteI
mpresa/Interv
alloPrezzi (*)

SI **

FASCIA_COMP
ONENTE

NO

CONSUMO_DA

NO

CONSUMO_A

NO

PREZZO

SI

Indica la singola fascia
impostata nel parametro
TIPO_FASCE

Compilare solo per offerte
Elettrico

Per valorizzare una
componente impresa non
legata alle fasce orarie, il
campo sarà omesso

Consumo annuo che
costituisci il limite inferiore
di consumi, per il quale
s’intende definire il valore
unitario della componente
Consumo annuo che
costituisci il limite superiore
dello scaglione (primo
scaglione o scaglione unico)
per il quale s’intende definire
il valore unitario della
componente
Indica il valore unitario della
componente. comprensivo
delle perdite di rete

UNITA_MISURA

SI

l’unità di misura del valore
indicato nel campo “Prezzo”

TIPO_PREZZO

SI (se
TIPO_OFFERTA
= ‘04’)

DURATA

NO

VALIDO_FINO

NO

Indica se la componente
impresa è da applicarsi
come prezzo fisso o variabile
Indica il numero di mesi di
validità dall’attivazione
dell’offerta a cui è applicato
il prezzo. Es. 3 per i primi
tre mesi dall’attivazione
Indica il mese fino al quale il
prezzo è valido

ComponenteI
mpresa/Interv
alloPrezzi/Peri
odoValidita

NO

MESE_VALIDIT
A (*)

NO

Indica il mese solare di
validità del prezzo.

Condizioni
contrattuali(*)

SI

TIPOLOGIA_CO
NDIZIONE

SI

Descrizione della tipologia di
condizione contrattuale

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

Alfanumerico
(2):
01:monorario/F1
02: F2
03: F3
04: F4
05: F5
06: F6
07:Peak
08:OffPeak

91: F2+F3
92: F1+F3
93: F1+F2

Numerico(9)

Numerico(9)

Numerico (6,6)

Numerico (2):
01:€/Anno
02:€/kW
03:€/kWh
04:€/Smc
05:€
Numerico (2)
01: Fisso
02: Variabile

Numerico(2)

MM/AAAA

Numerico(2)
01: Gennaio
02: Febbraio
03: Marzo
04: Aprile
05: Maggio
06: Giugno
07: Luglio
08: Agosto
09: Settembre
10: Ottobre
11: Novembre
12: Dicembre

Alfanumerico (2)
01: Attivazione
02:
Disattivazione

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

60/70

ALTRO

SI (Se
TIPOLOGIA_CO
NDIZIONE
=’99’)

DESCRIZIONE

SI

Descrizione della tipologia di
condizione contrattuale se il
campo precedente è
valorizzato in modo generico
‘Altro’
Descrizione della condizione
contrattuale

LIMITANTE

SI

Indica se la condizione è
limitante

REGIONE (*)

NO

Zone
Offerta

NO

PROVINCIA(*)

NO

COMUNE(*)

NO

NOME

DESCRIZIONE

SI

SI

Sconto
(*)

NO

CODICE_COMP
ONENTE_FASCI
A(*)

NO

Elenco Codici Istat delle
regioni in cui l'esercente
propone l'offerta.

Elenco Codici Istat delle
province in cui l'esercente
propone l'offerta.

Elenco Codici Istat delle
comuni in cui l'esercente
propone l'offerta.

Indica il nome dello sconto

Indica la descrizione dello
sconto

Indica l’identificativo della
ComponenteRegolata o della
Fascia a cui si applica lo
sconto
(Componenti e Fasce non
possono essere inserite
contemporaneamente)

03: Recesso
04: Offerta
Pluriennale
05: Oneri di
Recesso
Anticipato16
99: Altro

Alfanumerico
(20)

Alfanumerico
(3000)
Alfanumerico
01: Si, è
limitante
02:No, non è
limitante
Alfanumerico (2)
dove i singoli
codici istat sono
Numerico 2
Alfanumerico (3)
dove i singoli
codici istat sono
Numerico 3
Alfanumerico (6)
dove i singoli
codici istat sono
Numerico 6
Alfanumerico
(255)
Alfanumerico
(3000)

Alfanumerico(02)
Componenti:
01:PCV
02:PPE
03:CCR,
04: CPR,
05:GRAD,
06:QTint,
07:QTpsv,
09:QVD_Fissa
10:QVD_Variabile
Fasce:
11: F1
12: F2
13: F3
14: F4
15: F5
16: F6
17: Peak
18: OffPeak
91=F2+F3
92=F1+F3
93=F1+F2

VALIDITA

SI (se
Sconto/PeriodoV

Indica quando è applicato lo
sconto

Alfanumerico (2)
01: Ingresso

16 Indica la presenza dell’eventuale onere di recesso anticipato nei casi previsti. È possibile inserire il codice
‘05’ a partire dal 1 gennaio 2024.

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

61/70

alidita non ha
campi
valorizzati)

IVA_SCONTO

SI

DURATA

NO

VALIDO_FINO

NO

Indica se lo sconto è
soggetto ad IVA

Indica il numero di mesi di
validità dall’attivazione
dell’offerta a cui è applicato
il prezzo. Es. 3 per i primi
tre mesi dall’attivazione
Indica il mese fino al quale il
prezzo è valido

Sconto/Period
oValidita

NO

MESE_VALIDIT
A (*)

NO

Indica il mese solare di
validità del prezzo.

Sconto/Condizi
one

SI (per ogni
Sconto definito)

CONDIZIONE_
APPLICAZIONE

SI

Definisce se e quali
condizioni definiscono
l’applicazione dello sconto,
sconti condizionati non
concorrono al calcolo della
spesa

02: entro 12
mesi
03: oltre 12 mesi
Alfanumerico (2)
01:SI
02: NO

Numerico(2)

MM/AAAA

Numerico(2)
01: Gennaio
02: Febbraio
03: Marzo
04: Aprile
05: Maggio
06: Giugno
07: Luglio
08: Agosto
09: Settembre
10: Ottobre
11: Novembre
12: Dicembre

Alfanumerico (2)

00: Non
condizionato
01: Fatturazione
elettronica
02:Gestione
online
03: fatturazione
elettronica+domi
ciliazione
bancaria
99: Altro

DESCRIZIONE_
CONDIZIONE

SI (Se
CONDIZIONE_A
PPLICAZIONE=9
9)

Descrive eventuali altre
condizioni per l’applicazione
dello sconto

Alfanumerico
(3000)

TIPOLOGIA

SI

Sconto/PREZZ
ISconto
(*)

SI (almeno 1
per ogni Sconto
definito)

VALIDO_DA

NO

VALIDO_FINO

NO

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

consumo annuo che
costituisce il limite inferiore
di consumo per il quale si
intende definire il valore
unitario dello sconto
consumo annuo che
costituisce il limite superiore
dello scaglione (primo
scaglione o scaglione unico)
per il quale si intende
definire il valore dello sconto

Versione: 5.0

Uso Pubblico

Numerico (2)
01: Sconto fisso
02:Sconto
Potenza
03: Sconto
Vendita
04: sconto su
tutela

Numerico (9)

Numerico (9)

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

62/70

UNITA_MISURA

SI

l’unità di misura del valore
indicato nel campo “Prezzo”

PREZZO

NOME

DETTAGLIO

SI

SI

SI

 Prezzo applicato
Nome del prodotto o servizio
aggiuntivo offerto
Descrizione dettagliata del
prodotto o servizio
aggiuntivo offerto

ProdottiServizi
Aggiuntivi (*)

NO

MACROAREA

NO

Indica la macro area di
interesse del servizio

DETTAGLI_MAC
ROAREA

SI (se
MACROAREA=99
)

Numerico (2)
01:€/Anno
02:€/kW
03:€/kWh
04:€/Smc
05:€
06:Percentuale
Numerico (6,6)
Alfanumerico
(255)

Alfanumerico
(3000)

Numerico (2)

01: Caldaia
02: Mobility
03: Solare
termico
04: Fotovoltaico
05:
Climatizzazione
06: Polizza
assicurativa
99: Altro

Alfanumerico
(100)

(*) Le sezioni con l’asterisco possono essere ripetute tante volte in funzione di quante sono le
componenti definite dal venditore

(**)  Per  TIPO_MERCATO  =  02  è  obbligatoria  una  sezione  IntervalloPrezzi  per  ogni
ComponenteImpresa inserita. Per TIPO_MERCATO = 01 se:

•  MACROAREA  (ComponenteImpresa)  =  02,  04  o  06  e  UNITA_MISURA
(ComponenteImpresa/IntervalloPrezzi)  =   03  (per  tutti  gli  intervalli  prezzi  della
componente). E’ obbligatorio inserire un num. di sezioni Intervallo Prezzo uguale
al numero di fasce inserite nella TIPOLOGIA_FASCE della sezione TipoPrezzo.
•  MACROAREA  (ComponenteImpresa)=  01  o  04  o  05  o  06  e  UNITA_MISURA
(ComponenteImpresa/IntervalloPrezzi)  =  01,02  o  05.  E’  obbligatorio  inserire  un
unico Intervallo Prezzi per ogni “ComponentiImpresa” non valorizzando il campo
FASCIA_COMPONENTE.

Per  TIPO_CLIENTE  =  01,  è  possibile  valorizzare  una  sola  ComponenteImpresa  con
UNITA_MISURA  =  01  e  una  sola  ComponenteImpresa  con  UNITA_MISURA  03  o  04
(rispettivamente per TIPO_MERCATO 01 o 02) per intervallo di validità, fascia oraria e intervallo
di consumo annuo.

Nella sezione IntervalloPrezzi della Componente Impresa, i valori CONSUMO_DA e CONSUMO_A

definiscono  i  range  nei  quali  viene  applicato  il  prezzo  della  componente.  Nell’ipotesi  in  cui

definisco due range, uno da 0 a 100 con prezzo x e uno da 101 a 200 con prezzo y, se l’utente

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

63/70

ha  un  consumo  di  150  (kWh  o  Smc),  il  prezzo  della  componente  sarà  calcolato  a  scaglioni,  in

questo caso verrà applicato il prezzo x per i primi 100 e il prezzo y per i successivi 50 (100*x +

50*y).

7.2  Modalità di Trasmissione Offerte non simulabili

Tutte le offerte non simulabili tramite gli algoritmi pubblicati dal Gestore nel documento “Regole

di calcolo della spesa” potranno essere trasmesse tramite il seguente tracciato.

Tale procedura consente la presenza delle offerte sul Portale Offerte in una pagina dedicata, fino

al  rilascio  di  algoritmi  idonei  al  calcolo  della  spesa  annua.  Successivamente  l’Utente  potrà

trasmettere l’offerta come da paragrafo 7.1 e sarà pertanto disponibile tra i risultati della ricerca.

OBBLIGATORI
ETA SEZIONE

DATI

OBBLIGA
TORIETA’

DESCRIZIONE

FORMATO

SEZIONE

Identificati
vi Offerta

SI

PIVA_UTENTE

COD_OFFERTA

Dettaglio
Offerta

SI

NOME_OFFERTA
DESCRIZIONE

TIPO_MERCATO

SI

SI

SI
SI

SI

Partita IVA dell'Utente
che richiede l'attivazione
Codice univoco per
l'offerta presente sui
sistemi del Venditore che
sarà indicato nel campo
CODICE CONTRATTO in
fase di sottoscrizione
dell'offerta da parte del
cliente finale nella
richiesta di switching
Nome dell'Offerta
Descrizione estesa
dell'offerta
Definisce la commodity

Alfanumerico (16)

Alfanumerico (32)

Alfanumerico (255)
Alfanumerico
(3000)
Alfanumerico (2)
01: Elettrico
02: Gas
03: Dual

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

64/70

TIPO_OFFERTA

SI

Tipologia offerta inserita

TIPO_CLIENTE

SI

Tipologia di cliente finale

Dettaglio
Offerta/Co
ntatti
Validità
Offerta

NO

URL_OFFERTA

SI

DATA_INIZIO

DATA_FINE

Sconto (*)1

NO

TIPO_SCONTO

SI

SI

SI

SI

Indica la pagina web
dell'offerta del venditore
se disponibile
Indica la data in formato
timestamp dell'inizio di
validità dell'offerta
Indica la data in formato
timestamp della fine
validità dell'offerta
Tipologia dello sconto
applicato alla fornitura

Prodotti
Servizi
Aggiuntivi
(*)

NO

MACROAREA

SI

Indica la macro area di
interesse del servizio

Numerico (2)
01: Fisso
02: Variabile
03: Misto
04: Altro

Numerico (2)
01:Domestico
02:Altri Usi
03: Condominio
Uso Domestico
(Gas)
Alfanumerico (100)

GG/MM/AAAA_HH:
MM:SS

GG/MM/AAAA_HH:
MM:SS

Numerico (2)
01:Una Tantum
02: Permanente

Numerico (2)
01: Caldaia
02: Mobility
03: Solare termico
04: Fotovoltaico
05: Climatizzazione
06: Polizza
assicurativa
99: Altro

DETTAGLI_MAC
ROAREA

SI( se
MACRO
AREA=9
9)

Nome del prodotto o
servizio aggiuntivo offerto

Alfanumerico (100)

1.

Il carattere asterisco (*) indica che una sezione può essere ripetuta più volte (la sezione Sconto al più 2 volte)

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

65/70

L’inserimento  di tali offerte avverrà attraverso le medesime modalità  delle  offerte del mercato
il  campo
retail  (web  e  A2A),  con
VERSIONE_FORMATO_FILE=02.

l’Utente  dovrà  selezionare

l’unica  variante  che

Per questa tipologia di offerte sarà possibile effettuare esclusivamente inserimenti ed eliminazioni
(par 5.3 – File csv_eliminazione).

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

66/70

Appendice

A – Tabella di codifica delle inammissibilità

Nelle seguenti tabelle sono riportati i codici causale utilizzati nei flussi di ammissibilità.

Causale

950

951

5

15

Tabella A.1 - Codici Inammissibilità

Motivazione

PIVA_UTENTE diversa da quella del Richiedente

PIVA_GESTORE diversa da quella del Gestore

La richiesta (identificata dal codice pratica utente) è già pervenuta con codice Gestore <CP_GESTORE>[1]

La richiesta non è eseguibile (il campo COD_OFFERTA può contenere esclusivamente caratteri alfanumerici, score,
underscore e punti)

516

La richiesta di inserimento di una nuova offerta con COD_OFFERTA è già pervenuta con codice Gestore <CP_GESTORE>

15

581

569

570

571

572

573

574

575

576

577

4

4

1

1

15

528

4

15

532

501

515

La richiesta non è eseguibile (il Richiedente ha già trasmesso l’offerta <COD_OFFERTA> in ambito PLACET)

Il Codice Offerta non rispetta il vincolo di 32 caratteri o presenta dei caratteri speciali non previsti

Il Codice Offerta non coerente con la Controparte Commerciale

Codice Offerta con settimo carattere non previsto dalla delibera di riferimento

Codice Offerta con ottavo carattere non previsto dalla delibera di riferimento

Codice Offerta con nono carattere non previsto dalla delibera di riferimento

Codice Offerta con decimo carattere non previsto dalla delibera di riferimento

Codice Offerta con undicesimo carattere non previsto dalla delibera di riferimento

Codice Offerta con dodicesimo e tredicesimo carattere non numerico

Codice Offerta con quattordicesimo e quindicesimo carattere non previsti per il Offerte Placet o su Mercato Libero

Codice Offerta con quindicesimo carattere non previsto dalla delibera di riferimento

I campi obbligatori non sono stati compilati o non sono stati correttamente compilati (TIPO_FILE non previsto)

I campi obbligatori non sono stati compilati o non sono stati correttamente compilati (VERSIONE_FORMATO_FILE non
previsto)

Il template (formato file e/o tracciato) utilizzato non è congruo

Il template (formato file e/o tracciato) utilizzato non è congruo (<errore di validazione riscontrato>)

La richiesta non è eseguibile (COD_OFFERTA diverso da quello inserito nel campo COD_OFFERTA del tracciato delle
Offerte in allegato)

Il valore del campo TIPO_MERCATO non è valido

I campi obbligatori non sono stati compilati o non sono stati correttamente compilati (OFFERTA SINGOLA obbligatoria
per TIPO_MERCATO = 01 o 02)

La richiesta non è eseguibile (Per TIPO_MERCATO = 03 il campo OFFERTA_SINGOLA deve essere valorizzato a “NO”)

Il valore del campo OFFERTA_SINGOLA non è valido

Il valore del campo TIPO_CLIENTE non è valido

TIPO_CLIENTE= 03 (Condominio Uso Domestico) solo se TIPO_MERCATO = 02 (Gas)

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

67/70

527

503

513

15

4

529

15

4

15

15

15

4

531

15

15

4

512

15

541

541

4

15

15

518

15

567

568

534

15

4

Il valore del campo DOMESTICO_RESIDENTE non è valido

Il valore del campo TIPO_OFFERTA non è valido

Il valore del campo TIPOLOGIA_ATT_CONTR non è valido

La richiesta non è eseguibile (Non è possibile utilizzare la stessa TIPOLOGIA_ATT_CONTR della sezione
“DettaglioOfferta” all’interno della medesima offerta)

I campi obbligatori non sono stati compilati o non sono stati correttamente compilati (Sezione “DettaglioOfferta”
campo DURATA)

Il valore del campo MODALITA della sezione “ModalitaAttivazione” non è valido

La richiesta non è eseguibile (In caso di più occorrenze del campo MODALITA della sezione
“DettaglioOfferta/ModalitaAttivazione” è ammessa una sola valorizzazione per categoria)

I campi obbligatori non sono stati compilati o non sono stati correttamente compilati (DESCRIZIONE della sezione
“DettaglioOfferta/ModalitaAttivazione”obbligatoria per MODALITA = 99)

La richiesta non è eseguibile (URL_SITO_VENDITORE obbligatorio)

La richiesta non è eseguibile (formato errato per campo URL_SITO_VENDITORE)

La richiesta non è eseguibile (formato errato per campo URL_OFFERTA)

I campi obbligatori non sono stati compilati o non sono stati correttamente compilati (Sez.“RiferimentiPrezzoEnergia”
obbligat. per offerta trasm. con TIPO_OFFERTA = 02 e nessuno dei valori di TIPOLOGIA della sezione
“Sconto/PREZZISconto” sia pari a 4)

Il valore del campo IDX_PREZZO_ENERGIA non è valido

La richiesta non è eseguibile (Indice di riferimento per il calcolo del prezzo dell’energia non coerente con la commodity
dell’offerta)

La richiesta non è eseguibile (Indice “99” non ancora gestito dal Portale Offerte)

I campi obbligatori non sono stati compilati o non sono stati correttamente compilati (campo ALTRO della sezione
“RiferimentiPrezzoEnergia” obbligatorio per IDX_PREZZO_ENERGIA = 99)

La data indicata nel campo DATA_INIZIO non può essere antecedente alla data di ricezione del flusso

La richiesta non è eseguibile (DATA_FINE minore della DATA_INIZIO)

Per TIPO_OFFERTA=03 è obbligatorio valorizzare il campo CONSUMO_MIN

Per TIPO_OFFERTA=03 è obbligatorio valorizzare il campo CONSUMO_MAX

I campi obbligatori non sono stati compilati o non sono stati correttamente compilati (Campi OFFERTE_CONGIUNTE_EE
e OFFERTE_CONGIUNTE_GAS obbligatori per TIPO_MERCATO = 03)

La richiesta non è eseguibile (Per TIPO_MERCATO = 03 è ammessa al più un’offerta congiunta per commodity)

La richiesta non è eseguibile (per offerta trasmessa con TIPO_MERCATO = 02 è possibile associare solo offerte
congiunte della commodity elettrica (quindi OFFERTE_CONGIUNTE_EE))

Il COD_OFFERTA definito in OFFERTE_CONGIUNTE non è presente nel sistema

La richiesta non è eseguibile (per offerta trasmessa con TIPO_MERCATO = 01 è possibile associare solo offerte
congiunte della commodity GAS (quindi OFFERTE_CONGIUNTE_GAS))

Lo stato delle offerte congiunte è in annullamento.

Lo stato delle offerte congiunte (dual fuel) è in annullamento.

Il valore del campo MODALITA_PAGAMENTO non è valido

La richiesta non è eseguibile (In caso di più occorrenze della sezione “MetodoPagamento” è ammessa una sola
MODALITA_PAGAMENTO per categoria)

I campi obbligatori non sono stati compilati o non sono stati correttamente compilati (DESCRIZIONE della sezione
“MetodoPagamento” obbligatoria per MODALITA_PAGAMENTO = 99)

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

68/70

15

540

546

4

564

15

551

547

15

4

15

15

15

4

522

15

15

535

15

15

15

15

15

15

15

536

550

548

La richiesta non è eseguibile (Il valore del campo CODICE della sezione “ComponentiRegolate” non è valido)

La componente <codice inviato> della sezione "ComponentiRegolate" non è coerente con il TIPO_MERCATO scelto

Non è possibile indicare le ComponentiRegolate con CODICE = 06 o 07 o 08 per TIPOLOGIA della sezione
“Sconto/PREZZISconto” pari a 04 (sconto su tutela)

I campi obbligatori non sono stati compilati o non sono stati correttamente compilati (Sezione “TipoPrezzo”
obbligatoria per TIPO_MERCATO = 01)

Il campo TIPOLOGIA_FASCE è obbligatorio per TIPO_MERCATO = 01 e TIPO_OFFERTA diverso da 03

La richiesta non è eseguibile (Il valore del campo TIPOLOGIA_FASCE non è valido)

Per TIPOLOGIA_FASCE = 02, 04, 05 o 06 è necessario configurare le fasce orarie utilizzando la sezione
FasceOrarieSettimanale

Il campo <F_giornosettimana> della sezione FasceOrarieSettimanale non è stato configurato correttamente

La richiesta non è eseguibile (Il valore YI dei campi F_giornosettimana DEVE essere coerente con il campo
TIPOLOGIA_FASCE della sezione TipoPrezzo)

I campi obbligatori non sono stati compilati o non sono stati correttamente compilati (Sezione “Dispacciamento”
obbligatoria per TIPO_MERCATO = 01)

La richiesta non è eseguibile (Sezione “Dispacciamento” non ammessa per TIPO_MERCATO = 02 o 03)

La richiesta non è eseguibile (Il valore del campo TIPO_DISPACCIAMENTO non è valido)

La richiesta non è eseguibile (non è possibile valorizzare lo stesso TIPO_DISPACCIAMENTO in più sezioni
“Dispacciamento”)
I campi obbligatori non sono stati compilati o non sono stati correttamente compilati (VALORE_DISP obbligatorio per
TIPO_DISPACCIAMENTO = 99)

Per TIPO_OFFERTA = 03 è obbligatoria e ammessa una sola occorrenza della sezione ComponenteImpresa

La richiesta non è eseguibile (Non è possibile valorizzare lo stesso NOME in più sezioni “ComponenteImpresa”)

La richiesta non è eseguibile (Il valore del campo TIPOLOGIA della sezione “ComponenteImpresa” non è valido)

Il valore del campo MACROAREA della sezione COMPONENTE_IMPRESA non è valido

La richiesta non è eseguibile (per TIPO_OFFERTA = 03 (FLAT) è ammesso ed obbligatorio solo l’IntervalloPrezzi di default
costituito dai soli campi PREZZO, UNITA_MISURA)

La richiesta non è eseguibile (per TIPO_MERCATO = 02 è necessario che sia presente almeno una sezione
“IntervalloPrezzi” per ogni sezione “ComponenteImpresa” inserita)

La richiesta non è eseguibile (per TIPO_MERCATO = 01 e MACROAREA (della “ComponenteImpresa”) = 01 o 05, per ogni
“ComponenteImpresa” è ammessa almeno una sezione “IntervalloPrezzi” in cui NON DEVE essere valorizzato il campo
FASCIA_COMPONENTE)

La richiesta non è eseguibile (per TIPO_MERCATO = 01 e MACROAREA (della “ComponenteImpresa”) = 02, è necessaria
ALMENO una sezione “IntervalloPrezzi” con FASCIA_COMPONENTE valorizzato e coerente per ogni fascia trasmessa in
TIPOLOGIA_FASCE)

La richiesta non è eseguibile (Il campo FASCIA_COMPONENTE di ogni sezione "IntervalloPrezzi" per la singola
“ComponenteImpresa” deve essere sempre valorizzato o sempre non presente)

La richiesta non è eseguibile (per TIPO_MERCATO = 01, MACROAREA (della “ComponenteImpresa”) = 04 o 06 e
FASCIA_COMPONENTE non valorizzato in tutte le occorrenze  “IntervalloPrezzi”, per ogni “ComponenteImpresa” è
ammessa almeno un “IntervalloPrezzi”

La richiesta non è eseguibile (per TIPO_MERCATO = 01, MACROAREA (della “ComponenteImpresa”) = 04 o 06 e
FASCIA_COMPONENTE valorizzato, è necessaria ALMENO una sezione “IntervalloPrezzi” con FASCIA_COMPONENTE
coerente per ogni fascia inviata in TIPOLOGIA_FASCE)

Il valore del campo FASCIA_COMPONENTE non è valido

Per la Componente Impresa <Nome Componente> non possono essere presenti intervalli di consumo che si
sovrappongono per una determinata FASCIA_COMPONENTE (TIPO_MERCATO=01)

E’ ammesso ed obbligatorio un solo IntervalloPrezzi di default (ovvero contraddistinto dai soli campi
FASCIA_COMPONENTE , PREZZO, UNITA_MISURA) all’interno della ComponenteImpresa <nomecomponente> per la
FASCIA_COMPONENTE <fascia>

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

69/70

15

537

521

15

543

552

556

555

557

15

4

15

507

508

509

544

15

15

558

15

560

559

15

15

15

552

556

555

557

15

4

La richiesta non è eseguibile (per ogni ComponenteImpresa avente tutti gli Interv. prezzi senza FASCIA_COMPONENTE,
se presenti i campi del periodo di validità o CONSUMO_DA/A è obbl. e ammesso un solo prezzo di default costituito da
PREZZO e UNITA_MISURA)

Il valore del campo UNITA_MISURA della sezione “ComponenteImpresa/IntervalloPrezzi” non è valido

Il valore del campo UNITA_MISURA della sezione “ComponenteImpresa/IntervalloPrezzi” non è valido per il
TIPO_MERCATO scelto

La richiesta non è eseguibile (Per offerte trasmesse con TIPO_MERCATO = 0101 e TIPO_OFFERTA <> 03 (FLAT), in caso di
FASCIA_COMPONENTE valorizzata è ammesso UNITA_MISURA = 03 (€/kWh) mentre in caso di FASCIA_COMPONENTE
NON valorizzata è ammesso UNITA_MISURA = 01, 02, 05)

Per TIPO_OFFERTA = 03 è possibile indicare solamente UNITA_MISURA = €/kWh per TIPO_MERCATO = 01 e
UNITA_MISURA =  €/Smc per TIPO_MERCATO=02

I campi DURATA, MESE_VALIDITA e VALIDO_FINO della sezione “IntervalloPrezzi” possono essere valorizzati in modo
esclusivo

Il campo DURATA della sezione “IntervalloPrezzi” non è valorizzato correttamente

Il campo VALIDO_FINO della sezione “IntervalloPrezzi” non è valorizzato correttamente

Il campo MESE_VALIDITA della sezione “IntervalloPrezzi” non è valorizzato correttamente

La richiesta non è eseguibile (Il valore del campo TIPOLOGIA_CONDIZIONE della sezione
“ComponenteImpresa/CondizioniContrattuali” non è valido)

I campi obbligatori non sono stati compilati o non sono stati correttamente compilati (campo ALTRO della sezione
“ComponenteImpresa/CondizioniContrattuali”obbligatorio per TIPOLOGIA_CONDIZIONE = 99)

La richiesta non è eseguibile (Il valore del campo LIMITANTE della sezione
“ComponenteImpresa/CondizioniContrattuali” non è valido)

Il codice Istat di una REGIONE nell’elenco non è valido (<codice REGIONE non valido>)

Il codice Istat di una PROVINCIA nell’elenco non è valido (<codice PROVINCIA non valido>)

Il codice Istat di un COMUNE nell’elenco non è valido (<codice COMUNE non valido>)

Per TIPO_OFFERTA=03 non è possibile associare Sconti

La richiesta non è eseguibile (non è possibile valorizzare lo stesso NOME in più sezioni “Sconto”)

La richiesta non è eseguibile (per offerte non simulabili sono ammesse al più due occorrenze della sezione “Sconto”)

Il campo CODICE_COMPONENTE_FASCIA non è valorizzato correttamente

La richiesta non è eseguibile (per ogni occorrenza della sezione “Sconto” sono ammessi codici componente o fascia
appartenenti alla stessa classe)

Il CODICE_COMPONENTE_FASCIA DEVE essere coerente con le informazioni inviate nel campo TIPOLOGIA_FASCE della
sezione “TipoPrezzo”

Il campo VALIDITA della sezione “Sconto” è obbligatorio se nessuno dei campi della sezione “Sconto/PeriodoValidita” è
stato valorizzato

La richiesta non è eseguibile (Il valore del campo VALIDITA della sezione “Sconto” non è valido)

La richiesta non è eseguibile (Il valore del campo TIPO_SCONTO non è valido)

La richiesta non è eseguibile (Il valore del campo IVA_SCONTO non è valido)

I campi DURATA, MESE_VALIDITA e VALIDO_FINO della sezione “Sconto” possono essere valorizzati in modo esclusivo

Il campo DURATA della sezione “Sconto” non è valorizzato correttamente

Il campo VALIDO_FINO della sezione “Sconto” non è valorizzato correttamente

Il campo MESE_VALIDITA della sezione “Sconto” non è valorizzato correttamente

La richiesta non è eseguibile (Il valore del campo CONDIZIONE_APPLICAZIONE non è valido)

I campi obbligatori non sono stati compilati o non sono stati correttamente compilati (DESCRIZIONE_CONDIZIONE della
sezione “Sconto/Condizione” obbligatoria per CONDIZIONE_APPLICAZIONE = 99)

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

SISTEMA INFORMATIVO INTEGRATO PER LA GESTIONE DEI FLUSSI INFORMATIVI
RELATIVI AI MERCATI DELL’ENERGIA ELETTRICA E DEL GAS (SII)

TRASMISSIONE OFFERTE MERCATO RETAIL

70/70

523

15

538

15

521

563

15

4

582

Per ogni 'Sconto', dovrà essere definito almeno un 'PrezziSconto'

La richiesta non è eseguibile (Il valore del campo TIPOLOGIA della sezione “Sconto/PREZZISconto” non è valido)

Il valore del campo UNITA_MISURA della sezione “Sconto/PREZZISconto” non è valido.

La richiesta non è eseguibile (è possibile indicare solamente UNITA_MISURA = €/kWh per TIPO_MERCATO = 01 e
UNITA_MISURA =  €/Smc per TIPO_MERCATO=02)

Il valore del campo UNITA_MISURA della sezione “Sconto/PREZZISconto” non è valido per il TIPO_MERCATO scelto

Lo Sconto su una Componente regolata DEVE essere espresso in percentuale

La richiesta non è eseguibile (il valore del campo MACROAREA della sezione “ProdottiServiziAggiuntivi” non è valido)

I campi obbligatori non sono stati compilati o non sono stati correttamente compilati (DETTAGLI_MACROAREA della
sezione “ProdottiServiziAggiuntivi” obbligatorio per MACROAREA = 99)

Il campo URL_OFFERTA è obbligatorio

583

Per le offerte destinate ai clienti domestici è possibile trasmettere solo il CdispD come corrispettivo di dispacciamento

585

586

587

588

589

590

591

592

593

594

595

596

4

per TIPO_OFFERTA= 04 è necessario valorizzare il campo ‘TIPO_PREZZO’ nella sezione
“ComponenteImpresa/IntervalloPrezzi”

È possibile valorizzare il campo OFFERTA_ONNICOMPRENSIVA solo per TIPO_CLIENTE=01

È possibile trasmettere un’offerta onnicomprensiva solo per TIPO_OFFERTA fissa o variabile

I campi COEFFICIENTE e FASCIA_PREZZO sono valorizzabili solo per offerte destinate ai clienti domestici

È possibile valorizzare il campo CONSUMO_CANONE solo se OFFERTA_ONNICOMPRENSIVA = 02

Per un’offerta onnicomprensiva a canone è possibile trasmettere solo una componente in MACROAREA = 01 e una sola
in MACROAREA = 02

È possibile trasmettere un’offerta onnicomprensiva a canone solo per TIPO_OFFERTA fissa o variabile

Per un’offerta onnicomprensiva è possibile trasmettere solo una componente in MACROAREA = 01 e una sola in
MACROAREA = 02

È possibile valorizzare il campo TIPO_PREZZO solo per componenti impresa €/kWh(Smc)

Per le offerte destinate ai clienti domestici è possibile trasmettere una sola componente impresa in €/anno e una sola
in €/kWh(Smc) per periodo temporale, fascia oraria e scaglione di consumo

La valorizzazione del campo FASCIA_PREZZO deve essere coerente ed esaustiva con la configurazione definita nella
sezione TipoPrezzo/TIPOLOGIA_FASCE

La sezione RiferimentiPrezzoEnergia può essere ripetibile solo per TIPO_CLIENTE = ‘01’

 I campi obbligatori non sono stati compilati o non sono stati correttamente compilati (Sez.“RiferimentiPrezzoEnergia”
obbligatoria. per offerta trasmessa con TIPO_OFFERTA = 02/04  e nessuno dei valori di TIPOLOGIA della sezione
“Sconto/PREZZISconto” sia pari a 4)

Nome doc:   Trasmissione Offerte Mercato Retail

Data:               15 dicembre 2025

Versione: 5.0

Uso Pubblico

