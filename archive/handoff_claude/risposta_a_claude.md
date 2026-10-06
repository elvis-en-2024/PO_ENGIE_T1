# Risposta da dare a Claude Browser

> Copia e incolla il testo tra le due linee ---

---

Analisi eccellente. Procedi esattamente con il piano che hai descritto (Opzione 1 + 4). Alcune precisazioni operative:

## Sul Golden Dataset
Non ho casi di confronto pronti dal Portale, quindi costruisci il template 	ests/golden/sas_expected.csv con colonne chiare e 2-3 casi già compilati usando valori plausibili che posso verificare manualmente sul sito. Per il resto, lascia le righe vuote con i parametri da compilare (ti segnalerò i valori reali dopo il confronto manuale).

Assicurati che il golden dataset copra:
- EE Fisso Biorario Residente 3kW Lombardia (caso base ARERA 2700 kWh)
- EE Fisso Monorario Non Residente 4.5kW Lazio
- EE Variabile Biorario Residente 3kW Lombardia
- Gas Fisso Lombardia 1400 Smc
- Gas Fisso Sicilia 1400 Smc (per testare Sud vs Nord)
- Gas Variabile Campania 651 Smc
- Caso con sconto condizionato SDD
- Caso con sconto dual fuel
- Caso con prezzo comprensivo perdite = SI vs NO

## Sui fix immediati
Sì, includi direttamente nel deliverable:
1. **requirements.txt** aggiornato con versioni pinnate
2. **map_zone completa** con raise/warning per regioni sconosciute
3. **Fix deduplica** in load_data() → PARTITION BY PIVA_UTENTE, COD_OFFERTA, commodity

## Sui test
Struttura la suite così:
- 	ests/conftest.py — fixture condivise
- 	ests/golden/sas_expected.csv — golden dataset
- 	ests/test_arera_tariffs.py — unit test accise, zone, mapping
- 	ests/test_sas_calculator.py — test parametrizzati SAS con golden dataset
- 	ests/test_flattener.py — test transcodifica codici SII

Procedi con tutti i file.

---
