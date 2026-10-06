# Calcolo della Spesa Annua Stimata (SAS)

Questo documento descrive **come il motore calcola la SAS** (`engine/sas_calculator_fast.py`) e
**da dove prende ogni valore**. Le regole sono quelle del Portale Offerte. Sono state verificate
voce per voce sul dettaglio offerta di ilportaleofferte.it il 01-02/10/2026.

Riferimenti ufficiali:
- *Regole per il calcolo della spesa*, Portale Offerte v4.0 del 16/02/2026 (pagina Trasparenza →
  Calcolo della spesa; copia testuale in `docs/markdown/7d0a872b48e8796c84366afedd2ce7ec.md`);
- pagina ARERA "Stima della spesa annua" (delibera 289/2022/R/com) per gli indici delle offerte variabili;
- tracciato delle offerte: `docs/guida_lettura_tracciato.md`.

---

## 0. Struttura generale

```
SAS = (Vendita + Rete + Oneri + Imposte) con IVA  −  sconti non soggetti a IVA
```

| Blocco | Contenuto | Fonte |
|---|---|---|
| **Vendita** | componenti impresa dell'offerta, sconti, dispacciamento, componenti regolate dichiarate (PCV, PPE, CCR, QVD…), indice per le offerte variabili | XML dell'offerta + parametri del Portale + forward |
| **Rete** | trasporto, distribuzione, misura | parametri giornalieri del Portale |
| **Oneri** | oneri generali di sistema (ASOS, ARIM / RE, UG…) | parametri giornalieri del Portale |
| **Imposte** | accisa (e addizionale regionale gas) | parametri del Portale (luce), dettaglio offerta del Portale (gas) |
| **IVA** | luce 10% (domestico); gas 10% sui primi 480 Smc e 22% sul resto | parametri del Portale |

### Fonti dei valori regolati, in ordine di priorità

| Valore | Fonte primaria | File | Aggiornamento |
|---|---|---|---|
| Reti, oneri, dispacciamento, PCV, QVD, CPR, GRAD, accisa luce, IVA, λ | open data *Parametri* del Portale | `data/raw/parametri/{E,G}/YYYY/PO_Parametri_Mercato_Libero_*.csv` | `update_daily` (giornaliero) |
| Accisa e addizionale regionale gas | dettaglio offerta del Portale | `data/processed/imposte_gas_portale.json` | `scripts/rileva_imposte_gas.py` (da rilanciare a ogni cambio di aliquote) |
| PPE, CCR (4 trimestri) | dettaglio offerta del Portale | `data/processed/componenti_portale.json` | `update_daily` (una volta al giorno) |
| Forward PUN / PSV (offerte variabili) | mercati a termine GME (MTE, MT-GAS) | `data/raw/gme/{mte,mtgas}/YYYY/YYYYMMDD.json` | `update_daily` (giornaliero) |
| Riserva se mancano i file sopra | configurazione manuale | `data/config/arera_tariffs.json` | manuale, solo con conferma |

`FastSASCalculator(df)` senza altri argomenti è la modalità di **produzione**: carica in automatico l'ultimo file
parametri, le imposte gas, PPE/CCR e i forward. Se gli si passa `arera=` o `tariffs_path=` (test,
simulazioni), usa solo il JSON.

---

## 1. Input dell'utente

| Input | Uso |
|---|---|
| `consumi` = `{'F1','F2','F3'}` | consumo annuo per fascia (luce); gas: il totale va in `F1` |
| `potenza` (kW) | quote di potenza (σ2, UC6 secondo, componenti €/kW) |
| `residente` | accisa luce, oneri (tariffa residente / non residente) |
| `regione` | ambito tariffario gas, imposte gas, zona climatica (profilo di prelievo) |
| `is_domiciliazione`, `is_bolletta_web`, `is_dual_fuel` | applicabilità degli sconti condizionati |

Profili standard del Portale: luce 2.700 kWh (a fasce F1 891 / F2 837 / F3 972), 3 kW, residente;
gas 1.400 Smc, riscaldamento + cottura + acqua calda.

---

## 2. Vendita: componenti impresa (`ComponenteImpresa`)

Per ogni offerta, `component_matrix.build_long` trasforma le colonne `COMP_IMP_{c}_INT_{i}_*` in una riga per
ogni (componente, intervallo) con prezzo diverso da zero, poi:

1. **Tipo di prezzo** dall'unità di misura (`_UNITA`):
   - `€/anno` (o altra quota in €) → quota fissa;
   - `€/kW` → × potenza;
   - `€/kWh` → × consumo della fascia;
   - `€/Smc` → × consumo totale.
2. **Fascia** (`_FASCIA`): F1, F2, F3, F2+F3, F1+F3 o F1+F2 → consumo delle fasce corrispondenti.
   - Monorario o fascia vuota → consumo totale.
   - Le offerte con `TIPOLOGIA_FASCE` monoraria usano sempre il consumo totale.
3. **Scaglioni di consumo** (`_CONSUMO_DA` / `_CONSUMO_A`): per ogni (componente, fascia) si usa il prezzo
   dell'intervallo che contiene il **consumo annuo** (prezzo unico, non progressivo).
   - Senza scaglioni si usa il primo intervallo.
4. **Perdite di rete (luce)**: se `PREZZO_COMPRENSIVO_PERDITE_RETE` ≠ `SI`, i prezzi €/kWh si moltiplicano
   per (1 + λ), con λ = 0,10 dai parametri.
   - Per le offerte **variabili** le perdite si applicano solo al forward, non allo spread (Regole, rev. 3.01).

## 3. Vendita: sconti (`Sconto`)

Uno sconto si applica solo se:
- **Condizione di applicazione**: "Non condizionato", oppure la condizione è soddisfatta dagli input.
  - Domiciliazione / SDD solo se `is_domiciliazione`.
  - Fatturazione elettronica / bolletta web solo se `is_bolletta_web`.
  - "Altro" solo nel dual fuel.
- **Validità** (`_VALIDITA`): *Ingresso*, *entro 12 mesi* o vuota. Gli sconti "oltre 12 mesi" non entrano.

Importo dello sconto:

| Unità / tipo | Importo |
|---|---|
| €/anno, sconto fisso, una tantum | valore intero |
| €/kWh, €/Smc | valore × consumo della fascia indicata (`_CODICE_COMP`) o totale, limitato allo scaglione `_DA`…`_FINO` (0/0 = tutto) |
| percentuale, tipo "Sconto Vendita" | % × componenti volumetriche dell'offerta |
| `_DURATA` = n mesi | importo × n/12 (le una tantum restano intere) |

Lo sconto si sottrae alla vendita, prima dell'IVA. Se `_IVA` = `NO` si sottrae invece **dopo** l'IVA, dalla spesa finale.

## 4. Vendita: dispacciamento e componenti regolate (luce)

**Dispacciamento.** Per ogni voce dichiarata in `Dispacciamento` (`DISP_<voce>` = True), si somma il valore
dichiarato (`DISP_<voce>_VALORE`) oppure, se è vuoto o zero, quello del Portale:

| Voce XML | Parametro del Portale |
|---|---|
| CdispD (cod. 14) | `cdispd` |
| TIDE (cod. 01) | `msd + modeol + uniess + terna + interr + capprod` |
| Cod. 03…08 | `msd`, `modeol`, `uniess`, `terna`, `capprod`, `interr` |
| Capacità STG (09) / MT (10) | media `cpty_mrkt_1..3` / `cpty_mrkt_mt` |
| Salvaguardia (11), Tutele graduali (12) | `rst`, `rstg` |
| DispBT (13) | `dispbt_d` (€/anno, fisso) |

**Componenti regolate dichiarate** (`REGOLATA_*`, sezione `ComponentiRegolate`), sommate alla vendita:

| Componente | Valore | Fonte |
|---|---|---|
| PCV | `pcv_c` (domestico) / `pcv_a` (altri usi), €/anno | parametri |
| PPE | `ppe` × consumo, senza perdite (oggi −0,010270 €/kWh) | `componenti_portale.json` |

## 5. Vendita: componenti regolate (gas)

| Componente | Valore | Fonte |
|---|---|---|
| QVD_Fissa | `qvd_f_d`, €/anno | parametri |
| QVD_Variabile, CPR, GRAD | `qvd_v_d`, `cpr`, `grad` × Smc | parametri |
| QTint, QTpsv | 0 (così nel dettaglio del Portale) | — |
| CCR | 4 valori trimestrali pesati sul profilo di prelievo × Smc | `componenti_portale.json` |

CCR ponderato: `Σ_mesi quota_mese × CCR_trimestre(mese)`. Con CCR 2026-Q4 / 2027-Q1 = 0,025212 e
Q2 / Q3 = 0,027267, il CCR effettivo a Milano è 0,025564 €/Smc. Su 1.400 Smc fa 35,79 €, come sul Portale.

## 6. Offerte variabili: indice (`engine/forward.py`)

Regola ARERA e Portale:
- **Periodo di stima:** **4 trimestri solari** a partire dal trimestre di consultazione. Dal 02/10/2026 sono
  IV-2026, I, II e III-2027.
- **Valore dell'indice:** **media aritmetica delle quotazioni forward** dell'indice rilevate **nel mese
  precedente** la consultazione. L'aggiornamento è mensile (delibera 289/2022).

**Luce** (Regole §3.3.1.5-6):

```
monoraria:  [ media_4_trimestri(F0) × (1 + λ) + SPREAD ] × consumo_totale
a fasce:    [ media(F1) × (1+λ) + SPREAD ] × F1  +  [ media(F23) × (1+λ) + SPREAD ] × (F2+F3)
```

**Gas** (Regole §4.3.1.1):

```
Σ_mesi  consumo_mese × (indice_mese + SPREAD)
consumo_mese = consumo_annuo × quota_mese del profilo di prelievo
```

- **Profilo di prelievo gas:** viene dall'appendice delle Regole (anno termico 2025/26).
  - C1 = riscaldamento, per la zona climatica del capoluogo di regione (`ZONA_CLIMATICA`).
  - C2 = cottura e acqua calda.
  - La ricerca standard (riscaldamento + cottura + acqua calda) usa il 60% di C1 e il 40% di C2
    (`QUOTA_RISCALDAMENTO`). Il valore è tarato sul CCR di Milano.
- **Indici dichiarati:** ogni indice dichiarato dall'offerta (`IDX_*`) entra con il suo `COEFFICIENTE`.
  Coefficiente assente = 1; nessun indice dichiarato = 1. Tutti gli indici luce usano il forward PUN, tutti
  quelli gas il forward PSV.

**Fonte dei forward.** I valori ufficiali li elabora Acquirente Unico e li pubblica solo per gli operatori,
nell'area SII "Trasmissione Offerte di Mercato": non sono negli open data. Il motore usa i mercati a termine GME
(`download/gme.py`):

| Indice | Prodotti GME usati |
|---|---|
| Luce F0 | baseload trimestrale `BL-Q-AAAA-0q`; se manca, media dei mensili `BL-M`, poi annuale `BL-Y` |
| Luce F1 | peakload `PL-…` (lun-ven 8-20) come approssimazione di F1 |
| Luce F23 | ore fuori picco: `(BL × ore − PL × ore_picco) / (ore − ore_picco)` |
| Gas, mese per mese | mensile `M-AAAA-MM`; se manca, trimestrale `Q-`, stagionale `WS-/SS-`, annuale `CY-`. Conversione €/MWh → €/Smc con PCS 0,03852 GJ/Smc (10,7 kWh/Smc) |

Se le sessioni GME del mese precedente mancano, il motore usa `pun_stima` e `psv_stima` di
`arera_tariffs.json`, con la vecchia regola: perdite sul PUN solo per le offerte non comprensive di perdite.

> **Limite noto.** Il mercato a termine GME è poco liquido: a settembre 2026 non ci sono stati scambi e sono
> stati pubblicati solo prezzi di controllo. Le stime restano quindi sotto quelle del Portale:
> PUN F0 162,5 contro 169,9 €/MWh, PSV pesato 0,767 contro 0,832 €/Smc. Sulla SAS lo scarto è costante, circa
> −24 € sulla luce (2.700 kWh) e −108 € sul gas (1.400 Smc). Con l'indice del Portale il motore riproduce
> esattamente il 99% delle offerte variabili. Il valore esatto si ottiene solo con il file di Acquirente Unico.

## 7. Rete e oneri

**Luce** (`parametri_po.regolati_ele`, domestico):

```
fisso   = sigma1 + (sigma2 + uc6s_d) × potenza
per kWh = sigma3 + uc3 + uc6p_d
residente:      + (asos_dr + arim_dr) per kWh
non residente:  + asos_dnr_f + arim_dnr_f (fissi)  + (asos_dnr_v + arim_dnr_v) per kWh
```

**Gas** (`parametri_po.regolati_gas_fisso` / `_vol`, contatore fino a G6). L'ambito tariffario `a` dipende dalla regione:

```
fisso   = tau1_cc1_a{a} + ug2s + st_a{a} + vr_a{a}
per Smc = qt + ug1 + ug3 + re + rs                        (il bonus GS non entra)
+ tau3_f{1..6}_a{a} e ug2p_d_f{1..6} a scaglioni progressivi: 0-120, 121-480, 481-1560, 1561-5000, 5001-80000, 80001-200000 Smc
```

## 8. Imposte

**Accisa luce** (`parametri_po.accisa_ele`):
- **Non residente:** `acc_c_nr` × consumo.
- **Residente oltre 3 kW:** `acc_c_r_h` × consumo.
- **Residente fino a 3 kW:** `acc_c_r_l` × kWh tassati, su base mensile (c = consumo/12):

| Consumo mensile c | kWh tassati al mese |
|---|---|
| ≤ 150 | 0 |
| 150-220 | c − 150 |
| 220-370 | 2c − 370 |
| > 370 | c |

**Gas.** Accisa e addizionale regionale sono a scaglioni progressivi
(`importo_tiers`), con le aliquote rilevate dal dettaglio offerta del Portale per ogni regione
(`imposte_gas_portale.json`):
- **Accisa:** Nord 0,044 / 0,175 / 0,170 / 0,186 €/Smc; ex Mezzogiorno (Abruzzo, Molise, Campania, Puglia,
  Basilicata, Calabria, Sicilia, Latina e Frosinone) 0,038 / 0,135 / 0,120 / 0,150 €/Smc. Gli scaglioni sono
  0-120, 121-480, 481-1560 Smc e oltre.
- **Addizionale regionale:** varia per regione. È zero in Valle d'Aosta, Lombardia, Trentino-Alto Adige, Friuli e Sicilia.

## 9. IVA

- **Luce:** `(vendita + rete + oneri + accisa) × (1 + iva_c)`, con IVA 10% per il domestico.
- **Gas** (come il dettaglio offerta: righe "IVA 10%" e "IVA 22%"):

```
fisso       = quote fisse di vendita + quote fisse di rete/oneri
vol         = vendita volumetrica + rete/oneri volumetrici + imposte        (consumo totale)
vol_ridotta = vendita volumetrica × min(c,480)/c + rete/oneri e imposte dei primi 480 Smc
SAS_gas     = fisso × (1+iva_f3) + vol_ridotta × (1+iva_f1) + (vol − vol_ridotta) × (1+iva_f3)
```

con `iva_f1` = 10% e `iva_f3` = 22% (parametri gas).

Dalla spesa con IVA si sottraggono infine gli sconti con `IVA_SCONTO` = NO.

---

## 10. Esempi verificati sul Portale (01-02/10/2026)

### Luce, prezzo fisso: BasePF2024 (Sunrise), Milano, 2.700 kWh, 3 kW, residente

| Voce | Calcolo | € |
|---|---|---|
| Vendita | 180 (CI fissa) + 41,18 (PCV) + (0,25 − 0,010270 PPE + 0,016776 CDISPd) × 2.700 | 913,75 |
| Rete | 23,04 + (23,52 + 0,1988) × 3 + (0,0119 + 0,00276 + 0,00007) × 2.700 | 133,97 |
| Oneri | (0,031515 + 0,001638) × 2.700 | 89,51 |
| Imposte | 225 kWh/mese → (2×225 − 370) × 12 = 960 kWh × 0,0227 | 21,79 |
| IVA 10% | (1.137,23 + 21,79) × 10% | 115,90 |
| **Spesa annua** | | **1.274,92** |

### Luce, prezzo variabile: Segno-V-Luce CipCip, Palermo, 2.700 kWh

| Voce | Calcolo | € |
|---|---|---|
| Vendita | 72 + (0,169897 × 1,1 + 0,0077 spread + 0,016776 CDISPd) × 2.700 | 642,68 |
| Rete + oneri | come sopra | 223,48 |
| Sconto una tantum | | −36,00 |
| Imposte | | 21,79 |
| IVA 10% | | 85,20 |
| **Spesa annua** | | **937,15** |

0,169897 €/kWh è il forward F0 implicito nel Portale (media dei 4 trimestri, al netto delle perdite).

### Gas, prezzo fisso: CHIARISSIMA FIX PERTE (Segnoverde), Milano, 1.400 Smc

| Voce | € |
|---|---|
| Vendita: 160 + 0,47 × 1.400 | 818,00 |
| Rete: τ1 69,60 − 0,35 ST − 0,01 VR + QT, RS, UG1 e τ3 a scaglioni | 364,39 |
| Oneri: UG2s −21,63 + RE, UG3 e UG2 a scaglioni | 74,57 |
| Sconto una tantum | −20,00 |
| Imposte (accisa Lombardia; addizionale 0) | 224,68 |
| IVA 10% / IVA 22% | 42,64 / 227,75 |
| **Spesa annua** | **1.732,03** |

Il caso è codificato nei test `tests/test_gas_portale.py` (gas) e `tests/test_forward.py` (CCR, perdite sul forward).

---

## 11. Grado di allineamento con il Portale

Confronto online con `scripts/verifica_portale.py`, stessi parametri e stesso giorno (02/10/2026):

| Scenario | SAS uguale (±1 €) |
|---|---|
| Luce fisso monorario, Milano | 267 / 268 |
| Luce fisso a fasce, Milano | 102 / 102 |
| Gas fisso, Milano | 209 / 218 (tutte entro l'1%) |
| Luce variabile, Palermo | scarto costante −24,27 € (solo indice); 335 / 338 con l'indice del Portale |
| Gas variabile, Roma | scarto mediano −108 € (solo indice); 1.111 / 1.119 con l'indice del Portale |

## 12. Limiti noti

- **Forward GME:** sono un'approssimazione di quelli di Acquirente Unico (§6).
- **Imposte gas per regione:** i territori ex Mezzogiorno del Lazio (Latina, Frosinone) non sono distinti da
  Roma. La Sardegna non è rilevata.
- **Validità dei prezzi:** i `PeriodoValidita` delle componenti impresa (prezzi validi meno di 12 mesi) non
  sono ancora gestiti; si usa il prezzo dell'intervallo scelto.
- **Offerte PLACET:** non sono nello storico, quindi non entrano nel ranking.
- **Profilo gas:** la quota 60/40 riscaldamento / cottura e acqua calda è tarata su un solo caso.
