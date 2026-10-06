# Analisi Critica Claude — Bug e Criticità FastSASCalculator

> Risposta di Claude browser del 25/08/2026 dopo revisione del codice

---

## Criticità Bloccanti (Impatto sulla correttezza SAS)

### 1. Prezzi indicizzati hardcoded per offerte Variabili
- pun_base = 0.105 e 0.35 euro/Smc per gas variabile sono costanti nel codice
- I campi IDX_* estratti dal flattener non vengono mai usati
- Lo spread è già dentro COMP_IMP → rischio doppio conteggio
- Impatto: Tutte le offerte Variabili hanno SAS non confrontabile con il Portale ufficiale

### 2. Accise Gas hardcoded bypassano ARERA config
- I valori 0.044 / 0.175 / 0.170 / 0.186 sono direttamente in calculate_sas()
- self.arera.GAS_ACCISE (che distingue Nord/Sud) viene ignorato
- Impatto: Per regioni del Sud l'accisa è sovrastimata

### 3. map_zone incompleta in arera_tariffs.py
- Mancano: Marche, Umbria, Friuli-Venezia Giulia, Trentino-Alto Adige, Molise, Basilicata, Sardegna, Valle d'Aosta
- Fallback silenzioso su "Nord Occidentale" senza warning

### 4. Componenti in percentuale (UNITA_MISURA 06)
- Percentuale finisce nel ramo is_fix e viene sommata come euro/anno
- Va gestita come ramo dedicato o esclusa

### 5. Filtro Biorario difettoso
- Regex F2|F3|biorario|Peak/OffPeak intercetta anche trioraria
- is_vero_mono mischia codici SII grezzi e valori transcodificati

---

## Fragilità / Debito Tecnico

### 6. applica_sconto — ndarray and bool bug latente
### 7. Shadowing variabili is_kwh / is_smc
### 8. PREZZO_UNITARIO include CdispD e PUN (nome fuorviante)
### 9. Parsing prezzi fragile (separatore migliaia → 0 silenzioso)

---

## Problemi Architetturali

### 10. Deduplica errata in app.py (PARTITION BY COD_OFFERTA senza PIVA)
### 11. Asimmetria EE/Gas nel calcolo tariffe

---

## Raccomandazione: Opzione 1 + Opzione 4
Golden dataset 20-30 casi + suite pytest con tolleranza ±1%
