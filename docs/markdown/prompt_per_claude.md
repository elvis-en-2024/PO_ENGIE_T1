Ciao Claude, 
siamo al lavoro su un'app Streamlit per clonare il calcolatore del Portale Offerte ARERA partendo dal database XML scraping 2026. Abbiamo due grosse anomalie nel nostro ranking rispetto al portale ufficiale e vorremmo il tuo aiuto per perfezionare i filtri e il calcolo nel nostro file `sas_calculator_fast.py`.

### Anomalia 1: Offerte con prezzi anomali (Es. MONO2026DOME129EE)
Scegliendo "Monorario" / "Fisso" / "2700 kWh", il nostro ranking restituisce al primo posto l'offerta `MONO2026DOME129EE` a soli 412.49€ annui. 
Verificando il dataset, abbiamo scoperto che l'offerta dichiara solo due componenti `COMP_IMP`:
- COMP_IMP_1: Oneri di commercializzazione (138€/Anno)
- COMP_IMP_2: Corrispettivo di Sbilanciamento (0.005€/kWh)
Manca totalmente la macro-voce del Prezzo Energia (la materia prima)! Sul Portale Offerte questa offerta non compare proprio (probabilmente viene filtrata come invalida). Come possiamo implementare un filtro robusto in `sas_calculator_fast.py` per escludere offerte "zoppe" che non dichiarano il Prezzo Energia principale?

### Anomalia 2: Offerte Triorarie nascoste come Biorarie (Es. CasaFix)
Scegliendo "A Fasce", il portale ufficiale raggruppa Biorario e Triorario. Nel nostro script, la prima in assoluto diventa `CasaFix1206260300` (SAS 779.63€), tuttavia sul portale ufficiale questa non c'è, e al primo posto svetta `E.ON LuceClick biorariaVerde` (SAS 783.52€, con prezzi reali in F1 e F23).
Andando a ispezionare CasaFix (che il vendor ha caricato con `TIPOLOGIA_FASCE = F1, F2, F3`), notiamo che i prezzi per F1, F2 e F3 sono IDENTICI (es. 0.12€/kWh per tutte). 
Evidentemente il Portale Offerte scarta automaticamente queste "finte multiorarie" dai risultati "A Fasce", trattandole come monorarie. Abbiamo fatto un tentativo di filtro (lo vedrai nel codice sotto alla voce `is_fake`), ma forse c'è un modo più pulito ed elegante per rilevarle usando le colonne `COMP_IMP_X_INT_Y` in pandas.

Ti allego in contesto il nostro `app.py` e il `sas_calculator_fast.py`. Come adatteresti il `filter_offers` per replicare alla perfezione la pulizia dati del Portale Offerte?
