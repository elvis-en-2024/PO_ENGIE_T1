# Recap: revisione e verifica col Portale Offerte (settembre-ottobre 2026)

## Obiettivo

Rendere il ranking del progetto **completo, corretto e aggiornato** rispetto al Portale Offerte.
Il piano di lavoro era: rete di sicurezza dei test, parsing completo, motore SAS corretto e vettoriale,
pipeline dati affidabile, tariffe aggiornate, pulizia. A questo si è aggiunta la **verifica diretta sul sito
del Portale**, offerta per offerta, a parità di parametri.

Decisioni prese con l'utente:
- ricostruire lo storico solo per il 2025-2026;
- non scrivere in `arera_tariffs.json` valori non confermati;
- pulizia con git e `archive/`, senza cancellare nulla;
- PUN/PSV dalla fonte (GME), non ricavati dal Portale;
- accesso al GME con lo scraping del sito.

## Limiti iniziali e stato

| # | Limite trovato | Stato |
|---|---|---|
| L1 | Flattener troncato a 5 componenti × 5 intervalli | **Risolto**: schema dinamico (fino a 60 × 10, avviso oltre) |
| L2 | Zone dell'offerta: solo la prima regione/provincia/comune | **Risolto**: zone multiple `a\|b`, filtro sui codici |
| L3 | Colonne scaglioni con nomi diversi tra flattener e motore | **Risolto**: `_CONSUMO_DA/_A`, `_MACROAREA_COD`, `_TIPOLOGIA_COD` (alias legacy mantenuti) |
| L4 | L'app non passava la regione al calcolo gas | **Risolto** |
| L5 | Costanti fisse nel codice (PUN, PSV, DispBT, accisa, IVA) | **Risolto**: parametri giornalieri del Portale e forward; JSON solo di riserva |
| L6 | Tariffe Q3 nel JSON: blocco dell'app dal 06/10 | **Risolto**: la parte regolata viene dai parametri del Portale; con parametri del trimestre corrente il JSON vecchio dà solo un warning |
| L7 | Dashboard ferma al 24/08 | **Risolto**: `update_daily` rigenera la dashboard |
| L8 | Righe duplicate rilanciando un giorno, riscrittura completa del file da 130 MB | **Risolto**: storico partizionato per mese, idempotente |
| L9 | Nessun retry su 5xx/429; giorni mancanti | **Risolto**: retry, recupero dei buchi, pulizia dei `.tmp` |
| L10 | Calcolo SAS riga per riga, due logiche divergenti | **Risolto**: `component_matrix` unica, calcolo vettoriale |
| L11 | Crash dei filtri su casi limite | **Risolto** |
| L12 | Test lenti o falliti, golden segnaposto | **Risolto in parte**: 250 test verdi in circa 7 s; i 10 casi golden aspettano valori verificati |
| L13 | Codice morto o duplicato | **Risolto**: spostato in `archive/` |

Lo storico 2025-2026 è ricostruito dai raw con il nuovo flattener (22 mesi per commodity).

## Regole del Portale ricostruite (verificate sul dettaglio offerta)

1. **Parte regolata dagli open data *Parametri*:** reti, oneri, dispacciamento, PCV, QVD, CPR, GRAD,
   accisa luce, IVA, λ. Non serve più un aggiornamento trimestrale manuale.
2. **Accisa luce:** franchigia mensile per i residenti fino a 3 kW (0 fino a 150 kWh/mese, poi c−150 fino a
   220, 2c−370 fino a 370, poi tutto).
3. **Gas:**
   - IVA 10% sui soli costi volumetrici (imposte comprese) dei primi 480 Smc, 22% su quote fisse e resto;
   - bonus GS escluso;
   - τ3 e UG2 a scaglioni progressivi.
4. **Imposte gas per regione:** accisa Nord e Sud e addizionali regionali a scaglioni, rilevate dal Portale
   (non sono negli open data).
5. **Componenti regolate dichiarate dall'offerta:**
   - luce: PCV (€/anno) e PPE (€/kWh, senza perdite);
   - gas: QVD fissa e variabile, CCR trimestrale pesato sul profilo di prelievo.
6. **Offerte variabili** (Regole v4.0 e ARERA, delibera 289/2022):
   - media dei forward dei 4 trimestri dal trimestre corrente, rilevati nel mese precedente;
   - luce × (1+λ), senza perdite sullo spread, con F0/F1/F23;
   - gas mese per mese sul profilo di prelievo;
   - coefficienti degli indici dichiarati.
7. **Filtri come la ricerca del Portale:**
   - la ricerca a fasce esclude le monorarie dichiarate ma tiene le false multiorarie;
   - sconti per bolletta web solo se richiesta;
   - sconti con `IVA_SCONTO` = NO sottratti dopo l'IVA;
   - sconti con durata in mesi in proporzione all'anno.

## Confronto col Portale (02/10/2026, dati del giorno)

| Scenario | Offerte in comune | SAS uguale (±1 €) | Note |
|---|---|---|---|
| Luce fisso monorario, Milano, 2.700 kWh, 3 kW | 268 | 267 | ATENA +3,55 € |
| Luce fisso a fasce, Milano | 102 | 102 | |
| Gas fisso, Milano, 1.400 Smc | 218 | 209 | tutte entro l'1%; Magis +74 € il 01/10 (prezzo cambiato in giornata) |
| Luce variabile, Palermo | 341 | 0 | scarto costante −24,27 €: solo forward. Con l'indice del Portale: 335 / 338 |
| Gas variabile, Roma | 1.131 | 0 | scarto mediano −108 €: solo forward. Con l'indice del Portale: 1.111 / 1.119 |

Prima della revisione: gas fisso 0 su 211 corretti; luce variabile −88,65 € su tutte le offerte.

## Automazioni introdotte

| Cosa | Dove | Quando |
|---|---|---|
| Offerte, parametri, dashboard | `scripts/update_daily.py` | ogni giorno |
| Forward GME (MTE, MT-GAS) | `download/gme.py` | ogni giorno, dentro `update_daily` |
| PPE e CCR dal dettaglio offerta | `scripts/rileva_componenti_portale.py` | una volta al giorno, dentro `update_daily` |
| Accise e addizionali gas | `scripts/rileva_imposte_gas.py` | a mano, quando cambiano le aliquote |
| Confronto online | `scripts/verifica_portale.py` | dopo modifiche al motore, a ogni trimestre |

## Valori correnti (rilevati il 02/10/2026)

| Valore | Fonte | Valore |
|---|---|---|
| PPE | dettaglio Portale | −0,010270 €/kWh |
| CCR IV-2026 / I-2027 / II-2027 / III-2027 | dettaglio Portale | 0,025212 / 0,025212 / 0,027267 / 0,027267 €/Smc |
| Forward PUN F0 (media 4 trimestri, settembre) | GME | 0,16247 €/kWh (Portale: 0,169897) |
| Forward PSV pesato, Roma | GME | 0,7665 €/Smc (Portale: 0,8319) |

`data/config/arera_tariffs.json` non è stato modificato: è ancora la configurazione Q3 2026 ed è usato solo
come riserva.

## Attività aperte

1. **Forward ufficiali.** Il file di Acquirente Unico, nell'area SII "Trasmissione Offerte di Mercato", è
   accessibile agli operatori come ENGIE: con quello le offerte variabili tornerebbero esatte. Il motore è pronto
   a usarlo, va solo aggiunto il lettore del file.
2. **Offerte PLACET.** Circa 230 offerte per ricerca compaiono solo sul Portale, perché le PLACET non sono
   nello storico. Il Portale pubblica i loro CSV: vanno scaricati e uniti.
3. ~~**Finestra dell'app.**~~ Risolto: l'app usa solo il file dell'ultima rilevazione, come il Portale.
   Nella stessa revisione:
   - interfaccia rifatta in stile Portale, con Indietro, dettaglio offerta, tabella con sconti e note;
   - simulatore di nuova offerta;
   - corretta la lettura dei valori mancanti con pandas 3 (dispacciamento e validità degli sconti).
4. **Imposte gas.**
   - Latina e Frosinone, con accisa ridotta, vanno distinte dal resto del Lazio: serve la provincia nel calcolo.
   - La Sardegna non è ancora rilevata.
5. **Validità dei prezzi.** Le componenti con prezzo valido meno di 12 mesi (`PeriodoValidita`) non sono gestite.
6. **Profilo gas.** La quota 60/40 riscaldamento / cottura e acqua calda è tarata su un solo caso: verificarla su
   altre zone climatiche.
7. **Anomalie singole da analizzare:**
   - gas fisso Milano: ATENA, Gas Sales, YADA, Iren (scaglione aperto);
   - luce: ATENA +3,55 €.
8. **Golden test.** Vanno compilati i 10 casi golden con valori letti dal dettaglio del Portale.

## Commit principali

| Commit | Contenuto |
|---|---|
| `76a7386` | Fase 1: parsing completo e storico partizionato |
| `b75a8cd` | Fase 2: SAS vettoriale, regione nel calcolo, filtro biorario |
| `243173d` | Fase 3: update giornaliero idempotente, retry, avviso dati vecchi |
| `f906c49` | Fase 5: legacy in `archive/` |
| `415b994` | Verifica col Portale: parametri giornalieri, imposte gas, PPE/CCR, forward GME |
| `b433ee0` | App: schede del ranking ed etichetta della spesa |
