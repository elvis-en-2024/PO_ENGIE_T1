import pandas as pd
import numpy as np

def compute_rank():
    # Carica il CSV
    df = pd.read_csv("data/storage/verifica_piatta_20260820.csv", dtype=str)
    
    # Filtra: Commodity Elettrica, Fisso, Domestico
    df = df[
        (df['commodity'] == 'E') & 
        (df['TIPO_OFFERTA'] == 'Fisso') & 
        (df['TIPO_CLIENTE'] == 'Domestico')
    ]
    
    # Filtriamo per biorario/multiorario
    df = df[df['TIPOLOGIA_FASCE'].str.contains('F2|F3|biorario', na=False, regex=True)]

    # Parametri di simulazione
    F1 = 891
    F2 = 837
    F3 = 972
    F23 = F2 + F3
    TOT_CONS = F1 + F2 + F3
    POTENZA = 3.0

    # ARERA costanti
    dist_fix = 23.04
    trasp_pot = 23.52
    qual_pot = 0.1988
    misura_vol = 0.0119
    pereq_vol = 0.00276
    qual_vol = 0.00007
    asos_vol = 0.031515
    arim_vol = 0.001638
    accisa = 21.79

    tot_reti_oneri = dist_fix + (trasp_pot + qual_pot)*POTENZA + (misura_vol + pereq_vol + qual_vol + asos_vol + arim_vol)*TOT_CONS

    results = []

    for idx, row in df.iterrows():
        costo_venditore = 0.0
        
        # Somma le 5 Componenti Impresa
        for c in range(1, 6):
            if pd.isna(row.get(f'COMP_IMP_{c}_MACROAREA')):
                continue
                
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
                    
                # Perdite di rete modifier
                comprensivo = str(row.get('PREZZO_COMPRENSIVO_PERDITE_RETE')).strip().upper()
                if 'kWh' in unita and comprensivo == 'NO':
                    prezzo = prezzo * 1.10
                
                # Applica i moltiplicatori in base all'unita
                if 'Anno' in unita:
                    costo_venditore += prezzo
                elif 'kW' in unita and 'kWh' not in unita:
                    costo_venditore += prezzo * POTENZA
                elif 'kWh' in unita:
                    if fascia == 'monorario/F1':
                        if row.get('TIPOLOGIA_FASCE') in ['monorario/F1', '01']:
                            costo_venditore += prezzo * TOT_CONS
                        else:
                            costo_venditore += prezzo * F1
                    elif fascia == 'F2':
                        costo_venditore += prezzo * F2
                    elif fascia == 'F3':
                        costo_venditore += prezzo * F3
                    elif fascia == 'F2+F3':
                        costo_venditore += prezzo * F23
                    else:
                        costo_venditore += prezzo * TOT_CONS

        # Sottrai gli sconti
        for s in range(1, 16):
            if pd.isna(row.get(f'SCONTO_{s}_NOME')):
                continue
            validita = row.get(f'SCONTO_{s}_VALIDITA')
            codice_comp = row.get(f'SCONTO_{s}_CODICE_COMP')
            if validita in ['Ingresso', 'entro 12 mesi', None, '', 'Sempre']:
                for p in range(1, 3):
                    s_tipo = row.get(f'SCONTO_{s}_PREZZO_{p}_TIPO')
                    s_val = row.get(f'SCONTO_{s}_PREZZO_{p}_VAL')
                    s_unita = row.get(f'SCONTO_{s}_PREZZO_{p}_UNITA')
                    
                    if pd.isna(s_val): continue
                    try:
                        sconto = float(s_val.replace(',', '.'))
                    except:
                        continue
                        
                    if 'Anno' in s_unita or s_tipo == 'Sconto fisso':
                        costo_venditore -= sconto
                    elif 'kWh' in s_unita:
                        if codice_comp == 'F1':
                            costo_venditore -= sconto * F1
                        elif codice_comp == 'F2':
                            costo_venditore -= sconto * F2
                        elif codice_comp == 'F3':
                            costo_venditore -= sconto * F3
                        elif codice_comp == 'F2+F3':
                            costo_venditore -= sconto * F23
                        else:
                            costo_venditore -= sconto * TOT_CONS

        # CDISPd logic
        cdispd_val = row.get('DISP_CdispD_VALORE')
        if not pd.isna(cdispd_val):
            try:
                cdispd = float(str(cdispd_val).replace(',', '.'))
            except:
                cdispd = 0.024
        else:
            cdispd = 0.024
            
        costo_venditore += cdispd * TOT_CONS
        
        tot_netto = costo_venditore + tot_reti_oneri + accisa
        tot_sas = tot_netto * 1.10
                        
        results.append({
            'VENDITORE': row.get('PIVA_UTENTE'),
            'NOME_OFFERTA': row.get('NOME_OFFERTA'),
            'SAS': round(tot_sas, 2)
        })

    # Convert to DataFrame and sort
    res_df = pd.DataFrame(results)
    if len(res_df) > 0:
        res_df = res_df.sort_values('SAS')
        print(res_df.head(10).to_string(index=False))
    else:
        print("Nessuna offerta trovata.")

if __name__ == '__main__':
    compute_rank()
