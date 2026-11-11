import pandas as pd
from pathlib import Path
import xlsxwriter

BASE_DIR = Path(r"C:\PO_ENGIE\PO_ENGIE_T1")

def extract_val(row, fields, default=0.0):
    for f in fields:
        if pd.notna(row.get(f)):
            return float(row.get(f))
    return default

def run_double_check():
    crm_path = r"C:\Users\XP6566\OneDrive - ENGIE\Documenti\PO_scraping_2026\TEST CRM\Prodotti_Ottobre_CRM.csv"
    df_crm = pd.read_csv(crm_path)
    
    # Parametri ARERA Scheda Sintetica
    PSV_SCHEDA_SINTETICA = 0.54395
    PUN_SCHEDA_SINTETICA = 0.12489  # Estratto esattamente dal CRM (non arrotondato a 0.125)
    
    # PERDITE RETE (10%)
    LAMBDA_PERDITE = 0.10
    
    # Colonne CRM e Consumi
    gas_dom = [('CodCondSpeStimAnnoDOM120smc__c', 120), ('CodCondSpeStimAnnoDOM480smc__c', 480), ('CodCondSpeStimAnnoDOM700smc__c', 700), ('CodCondSpeStimAnnoDOM1400smc__c', 1400), ('CodCondSpeStimAnnoDOM2000smc__c', 2000), ('CodCondSpeStimAnnoDOM5000smc__c', 5000)]
    gas_au = [('CodCondSpeStimAnnoAU1500smc__c', 1500), ('CodCondSpeStimAnnoAU3000smc__c', 3000), ('CodCondSpeStimAnnoAU5000smc__c', 5000), ('CodCondSpeStimAnnoAU20000smc__c', 20000), ('CodCondSpeStimAnnoAU45000smc__c', 45000)]
    ee_res = [('CodCondSpeStimAnnoR3kW1500kWh__c', 1500), ('CodCondSpeStimAnnoR3kW2200kWh__c', 2200), ('CodCondSpeStimAnnoR3kW2700kWh__c', 2700), ('CodCondSpeStimAnnoR3kW3200kWh__c', 3200), ('CodCondSpeStimAnnoR4_5kW3500kWh__c', 3500), ('CodCondSpeStimAnnoR6kW6000kWh__c', 6000)]
    ee_nores = [('CodCondSpeStimAnnoNR3kW900kWh__c', 900), ('CodCondSpeStimAnnoNR3kW4000kWh__c', 4000)]
    ee_au = [('CodCondSpeStimAnnoAU1900kWh__c', 1900), ('CodCondSpeStimAnnoAU3600kWh__c', 3600), ('CodCondSpeStimAnnoAU6800kWh__c', 6800), ('CodCondSpeStimAnnoAU45000kWh__c', 45000), ('CodCondSpeStimAnnoAU100000kWh__c', 100000)]
    
    rows_codici = []
    
    for idx, row in df_crm.iterrows():
        codice = row.get('Codice_univoco__c')
        if pd.isna(codice): continue
        
        segmento = str(row.get('Segmento_Vendita__c')).strip().upper()
        if segmento == 'NAN':
            segmento = 'MM' # Fallback
            
        # Tipi
        is_gas = str(row.get('Tipo_servizio_GAS__c')).strip().upper() in ('X', 'SI')
        is_luce = str(row.get('Tipo_servizio_EE__c')).strip().upper() in ('X', 'SI')
        tipo_offerta = 'Fisso' if 'FISS' in str(row.get('Tipologia_offerta__c')).upper() else 'Variabile'
        
        # Componenti
        if segmento in ('MM', 'DOM', 'RES'):
            q_fissa_gas = extract_val(row, ['Quota_Comm_fissa_domestico_ENGIE_Gas__c', 'Quota_Comm_fissa_ENGIE_Gas_anno__c', 'Quota_fissa_gas__c'])
            q_fissa_luce = extract_val(row, ['Quota_Comm_fissa_dom_ENGIE_Luce__c', 'Quota_Comm_fissa_ENGIE_Luce_anno__c', 'Quota_fissa_luce__c'])
        else:
            q_fissa_gas = extract_val(row, ['Quota_Comm_fissa_altri_usi_ENGIE_Gas__c', 'Quota_Comm_fissa_ENGIE_Gas_anno__c', 'Quota_fissa_gas__c'])
            q_fissa_luce = extract_val(row, ['Quota_Comm_fissa_altri_usi_BT_ENGIE_Luce__c', 'Quota_Comm_fissa_altri_usi_MTENGIE_Luce__c', 'Quota_Comm_fissa_ENGIE_Luce_anno__c', 'Quota_fissa_luce__c'])
        
        if tipo_offerta == 'Variabile':
            p_gas = extract_val(row, ['Spread_gas__c', 'Quota_Alfa_Smc__c'])
            p_luce = extract_val(row, ['Spread_luce__c', 'Quota_Alfa_kWh__c'])
            costo_unitario_gas = PSV_SCHEDA_SINTETICA + p_gas
            # Luce: di solito in bolletta si aggiungono le perdite al PUN. Dipende se il CRM calcola PUN * 1.1 + Spread o (PUN+Spread)*1.1
            costo_unitario_luce = PUN_SCHEDA_SINTETICA * (1 + LAMBDA_PERDITE) + p_luce
        else:
            p_gas = extract_val(row, ['Quota_variabile_gas__c', 'Corrispettivo_energia__c'])
            p_luce = extract_val(row, ['Quota_variabile_luce__c', 'Corrispettivo_energia__c'])
            costo_unitario_gas = p_gas
            costo_unitario_luce = p_luce
            
        riga_cod = {
            'Codice Univoco': codice,
            'Nome': row.get('Name'),
            'Segmento': segmento,
            'Materia': 'GAS' if is_gas else 'LUCE'
        }
        
        # Inizializziamo a 0 ed estraiamo SEMPRE i valori CRM reali
        for col, cons in gas_dom + gas_au + ee_res + ee_nores + ee_au:
            riga_cod[col] = extract_val(row, [col])
            riga_cod[f"Mio Calcolo {col}"] = 0.0
        
        # Compila GAS (Mio Calcolo dipendente dal segmento)
        if is_gas:
            if segmento in ('MM', 'DOM', 'RES'):
                for col, cons in gas_dom:
                    riga_cod[f"Mio Calcolo {col}"] = q_fissa_gas + cons * costo_unitario_gas
            elif segmento in ('SME', 'AU'):
                for col, cons in gas_au:
                    riga_cod[f"Mio Calcolo {col}"] = q_fissa_gas + cons * costo_unitario_gas
                    
        # Compila LUCE (Mio Calcolo dipendente dal segmento)
        if is_luce:
            if segmento in ('MM', 'DOM', 'RES'):
                for col, cons in ee_res + ee_nores:
                    riga_cod[f"Mio Calcolo {col}"] = q_fissa_luce + cons * costo_unitario_luce
            elif segmento in ('SME', 'AU'):
                for col, cons in ee_au:
                    riga_cod[f"Mio Calcolo {col}"] = q_fissa_luce + cons * costo_unitario_luce
                    
        rows_codici.append(riga_cod)
        
    df_cod = pd.DataFrame(rows_codici)
    
    out_path = BASE_DIR / "data" / "processed" / "Codici_Condotta_CRM_vs_CALC_v2.xlsx"
    writer = pd.ExcelWriter(out_path, engine='xlsxwriter')
    
    df_cod.to_excel(writer, sheet_name='1. Codici Condotta (MP)', index=False)
    
    workbook = writer.book
    fmt_head = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
    fmt_mio = workbook.add_format({'num_format': '#,##0.00 €', 'bg_color': '#E2EFDA'}) # Verde chiaro
    fmt_crm = workbook.add_format({'num_format': '#,##0.00 €', 'bg_color': '#FFF2CC'}) # Giallo chiaro
    
    ws1 = writer.sheets['1. Codici Condotta (MP)']
    ws1.set_column('A:D', 20)
    
    # Colora le colonne
    for c_idx, col_name in enumerate(df_cod.columns):
        if 'Mio Calcolo' in col_name: ws1.set_column(c_idx, c_idx, 20, fmt_mio)
        elif 'CodCond' in col_name: ws1.set_column(c_idx, c_idx, 20, fmt_crm)
            
    # ---- SHEET 2: DOCUMENTAZIONE FORMULE ----
    ws2 = workbook.add_worksheet('2. Documentazione Formule')
    ws2.set_column('A:A', 30)
    ws2.set_column('B:B', 80)
    ws2.set_column('C:C', 60)
    
    docs = [
        ['Concetto / Calcolo', 'Formula Logica Utilizzata nello Script', 'Campi CRM di partenza / Mapping'],
        ['Segmento Cliente', 'Se MM/DOM -> popola campi Domestico/Res. Se SME/AU -> popola campi Altri Usi', 'Segmento_Vendita__c'],
        ['Quota Fissa (GAS)', 'Se vuoto dom, usa anno, ecc.', 'Quota_Comm_fissa_domestico_ENGIE_Gas__c (oppure _anno o _altri_usi)'],
        ['Quota Fissa (EE)', 'Se vuoto dom, usa anno, ecc.', 'Quota_Comm_fissa_dom_ENGIE_Luce__c (oppure _anno o _altri_usi)'],
        ['Prezzo GAS', 'Variabile = PSV_SCHEDA_SINTETICA + Spread_gas__c. Fisso = Quota_variabile_gas__c', 'Spread_gas__c, Quota_Alfa_Smc__c, Quota_variabile_gas__c'],
        ['Prezzo LUCE', 'Variabile = PUN_SCHEDA_SINTETICA * 1.10 (perdite) + Spread_luce__c. Fisso = Quota_variabile_luce__c', 'Spread_luce__c, Quota_Alfa_kWh__c, Quota_variabile_luce__c'],
        ['PSV Lettere Rinnovo (GAS)', 'Indice Rolling fissato nel codice per le Lettere di Rinnovo (Attualmente fisso a 0.54395)', 'Variabile hardcoded (PSV_SCHEDA_SINTETICA)'],
        ['PUN Lettere Rinnovo (LUCE)', 'Indice Rolling fissato nel codice (Attualmente fisso a 0.125)', 'Variabile hardcoded (PUN_SCHEDA_SINTETICA)'],
        ['Spesa Materia Prima (Mio Calcolo)', 'Quota Fissa + Consumo_smc * Prezzo Unitario', 'Formula Matematica (uguale alla logica CRM, usata per check)'],
        ['Spesa Materia Prima (CRM)', 'Copia pura del campo esatto', 'Tutti i campi CC sp stim ann (CodCondSpeStimAnno...)']
    ]
    for r, row_data in enumerate(docs):
        for c, val in enumerate(row_data):
            if r == 0: ws2.write(r, c, val, fmt_head)
            else: ws2.write(r, c, val)

    workbook.close()
    print(f"File salvato in: {out_path}")

if __name__ == "__main__":
    run_double_check()
