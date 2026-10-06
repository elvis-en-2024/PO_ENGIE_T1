import pandas as pd
import numpy as np

def compute_rank():
    # Carica il CSV
    df = pd.read_csv("data/storage/verifica_piatta_20260820.csv", dtype=str)
    
    # Filtra: Commodity Elettrica, Fisso, Domestico, Prezzo a fasce (non monorario)
    df = df[
        (df['commodity'] == 'E') & 
        (df['TIPO_OFFERTA'] == 'Fisso') & 
        (df['TIPO_CLIENTE'] == 'Domestico')
    ]
    
    # Rimuoviamo le offerte monorarie se l'utente ha chiesto 'a fasce', 
    # ma per sicurezza teniamole o gestiamole, filtriamo per TIPOLOGIA_FASCE contenente 'F2' o 'F3'
    df = df[df['TIPOLOGIA_FASCE'].str.contains('F2|F3|biorario', na=False, regex=True)]

    # Parametri di simulazione
    F1 = 891
    F2 = 837
    F3 = 972
    F23 = F2 + F3
    TOT = F1 + F2 + F3
    POTENZA = 3.0

    results = []

    for idx, row in df.iterrows():
        costo_venditore = 0.0
        
        # Somma le 5 Componenti Impresa
        for c in range(1, 6):
            if pd.isna(row.get(f'COMP_IMP_{c}_MACROAREA')):
                continue
                
            # Cerca negli intervalli
            for i in range(1, 6):
                fascia = row.get(f'COMP_IMP_{c}_INT_{i}_FASCIA')
                prezzo_str = row.get(f'COMP_IMP_{c}_INT_{i}_PREZZO')
                unita = row.get(f'COMP_IMP_{c}_INT_{i}_UNITA')
                
                if pd.isna(prezzo_str) or pd.isna(unita):
                    continue
                
                try:
                    prezzo = float(prezzo_str.replace(',', '.'))
                except:
                    continue
                
                # Applica i moltiplicatori in base all'unità
                if unita == '€/Anno':
                    costo_venditore += prezzo
                elif unita == '€/kW':
                    costo_venditore += prezzo * POTENZA
                elif unita == '€/kWh':
                    if fascia == 'monorario/F1':
                        # Se l'offerta ha fasce, la dicitura 'monorario/F1' indica la F1
                        costo_venditore += prezzo * F1
                    elif fascia == 'F2':
                        costo_venditore += prezzo * F2
                    elif fascia == 'F3':
                        costo_venditore += prezzo * F3
                    elif fascia == 'F2+F3':
                        costo_venditore += prezzo * F23
                    else:
                        # Fallback (non dovrebbe succedere se mappato bene)
                        costo_venditore += prezzo * TOT

        # Sottrai gli sconti
        for s in range(1, 16):
            if pd.isna(row.get(f'SCONTO_{s}_NOME')):
                continue
            validita = row.get(f'SCONTO_{s}_VALIDITA')
            codice_comp = row.get(f'SCONTO_{s}_CODICE_COMP')
            # Applichiamo lo sconto se valido entro il primo anno
            if validita in ['Ingresso', 'entro 12 mesi', None, '']:
                for p in range(1, 3):
                    s_tipo = row.get(f'SCONTO_{s}_PREZZO_{p}_TIPO')
                    s_val = row.get(f'SCONTO_{s}_PREZZO_{p}_VAL')
                    s_unita = row.get(f'SCONTO_{s}_PREZZO_{p}_UNITA')
                    
                    if pd.isna(s_val): continue
                    try:
                        sconto = float(s_val.replace(',', '.'))
                    except:
                        continue
                        
                    if s_unita == '€/Anno' or s_tipo == 'Sconto fisso':
                        costo_venditore -= sconto
                    elif s_unita == '€/kWh':
                        if codice_comp == 'F1':
                            costo_venditore -= sconto * F1
                        elif codice_comp == 'F2':
                            costo_venditore -= sconto * F2
                        elif codice_comp == 'F3':
                            costo_venditore -= sconto * F3
                        elif codice_comp == 'F2+F3':
                            costo_venditore -= sconto * F23
                        else:
                            costo_venditore -= sconto * TOT
                        
        results.append({
            'PIVA': row.get('PIVA_UTENTE'),
            'NOME_OFFERTA': row.get('NOME_OFFERTA'),
            'FASCE': row.get('TIPOLOGIA_FASCE'),
            'SPESA_VENDITORE_EURO': round(costo_venditore, 2)
        })

    # Convert to DataFrame and sort
    res_df = pd.DataFrame(results)
    if len(res_df) > 0:
        res_df = res_df.sort_values('SPESA_VENDITORE_EURO')
        print(res_df.head(10).to_string(index=False))
    else:
        print("Nessuna offerta trovata con questi parametri.")

if __name__ == '__main__':
    compute_rank()
