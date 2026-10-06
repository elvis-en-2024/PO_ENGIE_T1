import pandas as pd
import io

df = pd.read_csv('data/spreadsheets/tabella_xml_v2.csv', encoding='latin1')

md = []
md.append("# MANUALE OPERATIVO E TRACCIATO RECORD OFFERTE (A PROVA DI ERRORE)\n")
md.append("Questo documento contiene **ogni singolo dettaglio** necessario per interpretare e importare il file Parquet contenente le offerte energetiche. Qualsiasi sviluppatore o analista, anche senza esperienza nel settore energia, deve seguire queste indicazioni per evitare errori.\n\n")

md.append("## PARTE 1: LA LOGICA STRUTTURALE (IL \"FLATTENING\")\n")
md.append("I dati originari del Sistema Informativo Integrato (SII) sono in formato XML gerarchico. Poiché il Parquet è una tabella piatta (righe e colonne), abbiamo applicato un processo di **flattening**.\n\n")
md.append("### Cosa significa per lo sviluppatore?\n")
md.append("- Quando un'offerta ha **più componenti di prezzo** (es. Quota Fissa e Quota Energia), nel Parquet non c'è una sola colonna 'PREZZO', ma ci saranno colonne numerate come `COMP_IMP_1_...`, `COMP_IMP_2_...` fino al numero massimo di componenti riscontrate.\n")
md.append("- Quando un'offerta ha **più sconti**, troverete `SCONTO_1_...`, `SCONTO_2_...`.\n")
md.append("- Quando una componente varia nel tempo (es. prezzo scontato il primo anno, prezzo pieno il secondo), troverete l'indicatore dell'intervallo: `_INT_1_`, `_INT_2_`.\n\n")
md.append("La logica che segue per i campi ripetitivi (`COMP_IMP`, `SCONTO`, `COND`) va quindi applicata aggiungendo il suffisso numerico desiderato. I campi vuoti (NULL) indicano semplicemente che quell'offerta non ha un 2°, 3° o N° sconto/componente.\n\n")

md.append("---\n")
md.append("## PARTE 2: DIZIONARIO DETTAGLIATO DI TUTTI I CAMPI (TRACCIATO COMPLETO)\n")
md.append("Di seguito l'elenco di **tutte le colonne** previste, divise per sezione logica. Per ogni campo viene spiegato cosa contiene, se è obbligatorio, e i valori ammessi (codifiche).\n\n")

current_section = ""

for index, row in df.iterrows():
    sezione = str(row['SEZIONE']).strip()
    if pd.isna(sezione) or not isinstance(sezione, str):
        continue
        
    dati = str(row['DATI']).strip()
    descrizione = str(row['DESCRIZIONE']).strip()
    obblig = str(row.iloc[3]).strip()
    formato = str(row['FORMATO/VINCOLI']).strip()
    
    if pd.isna(dati) or dati == 'nan':
        continue
        
    if sezione != current_section:
        current_section = sezione
        md.append(f"### Sezione: {current_section}\n")
    
    # Gestione formattazione e codifiche
    formato_testo = formato.replace('\n', ' | ') if not pd.isna(formato) and formato != 'nan' else 'N/A'
    descrizione_testo = descrizione.replace('\n', ' ') if not pd.isna(descrizione) and descrizione != 'nan' else 'Nessuna descrizione'
    obblig_testo = obblig if not pd.isna(obblig) and obblig != 'nan' else 'N/A'
    
    md.append(f"#### Campo: `{dati}`\n")
    md.append(f"- **Descrizione**: {descrizione_testo}\n")
    md.append(f"- **Obbligatorio**: {obblig_testo}\n")
    md.append(f"- **Formato e Valori Ammessi**: {formato_testo}\n\n")

md.append("---\n")
md.append("## PARTE 3: GLOSSARIO DEI TERMINI ENERGETICI (PER NON ADDETTI AI LAVORI)\n")
md.append("- **Commodity**: Il tipo di fornitura (01=Luce, 02=Gas).\n")
md.append("- **PUN (Prezzo Unico Nazionale)**: Indice di borsa per l'energia elettrica. Le offerte a prezzo variabile di solito aggiungono un ricarico (Spread) al PUN.\n")
md.append("- **PSV (Punto di Scambio Virtuale)**: Indice di borsa per il gas naturale. \n")
md.append("- **Quota Fissa / Commercializzazione (Macroarea 01)**: Importo in €/mese o €/anno fisso, indipendente dai consumi.\n")
md.append("- **Quota Energia (Macroarea 04)**: Il prezzo pagato per la materia prima vera e propria (€/kWh o €/Smc).\n")
md.append("- **Spread / Fee (Macroarea 04 in offerte Variabili)**: Il guadagno/ricarico del fornitore sopra l'indice di borsa (es. PUN + 0,02 €/kWh). L'indice è definito in `IDX_PREZZO_ENERGIA`, il valore numerico 0,02 in `_PREZZO`.\n")
md.append("- **Dual Fuel**: Un'offerta in cui lo stesso fornitore vende sia Luce che Gas allo stesso cliente in un unico pacchetto.\n")
md.append("- **Energia Verde / FER (Macroarea 06)**: Energia prodotta da Fonti Energetiche Rinnovabili. Nelle componenti di prezzo, se un'offerta ha l'opzione verde, troverete una componente dedicata con MACROAREA 06.\n")
md.append("- **Fasce Orarie (F1, F2, F3)**: Applicabili solo alla Luce. F1 sono le ore di punta nei giorni lavorativi, F2/F3 le sere, i weekend e festivi.\n")
md.append("- **Oneri di Recesso Anticipato (Codice 05 in TIPOLOGIA_CONDIZIONE)**: Penale economica applicata se il cliente abbandona il contratto prima della naturale scadenza.\n")

with open("docs/guida_lettura_tracciato.md", "w", encoding="utf-8") as f:
    f.writelines(md)

print("Documento completo generato!")
