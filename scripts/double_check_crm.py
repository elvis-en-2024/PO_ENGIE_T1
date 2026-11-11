import pandas as pd
import numpy as np
import sys
import xlsxwriter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(BASE_DIR.as_posix())

from engine.offerta_simulata import NuovaOfferta
from engine.sas_calculator_fast import FastSASCalculator

def run_double_check():
    crm_path = r"C:\Users\XP6566\OneDrive - ENGIE\Documenti\PO_scraping_2026\TEST CRM\Prodotti_Ottobre_CRM.csv"
        
    df_crm = pd.read_csv(crm_path)
    
    calc = FastSASCalculator(pd.DataFrame(columns=["commodity", "PIVA_UTENTE", "COD_OFFERTA", "TIPO_OFFERTA"]))
    
    # Parametri ARERA Scheda Sintetica
    PSV_SCHEDA_SINTETICA = 0.54395
    PUN_SCHEDA_SINTETICA = 0.125
    
    calc.forward = {
        'gas_mesi': [PSV_SCHEDA_SINTETICA] * 12,
        'ee': {'F0': PUN_SCHEDA_SINTETICA, 'F1': PUN_SCHEDA_SINTETICA, 'F23': PUN_SCHEDA_SINTETICA}
    }
    
    ambiti = [
        ("Piemonte", "NORD OCCIDENTALE"), ("Lombardia", "NORD ORIENTALE"),
        ("Toscana", "CENTRALE"), ("Abruzzo", "CENTRO-SUD ORIENTALE"),
        ("Lazio", "CENTRO-SUD OCCIDENTALE"), ("Calabria", "MERIDIONALE")
    ]
    consumi_gas = [120, 480, 700, 1400, 2000, 5000]
    
    profili_ee = [
        (True, 3, 1500), (True, 3, 2200), (True, 3, 2700), (True, 3, 3200),
        (True, 4.5, 3500), (True, 6, 6000), (False, 3, 900), (False, 3, 4000)
    ]
    
    offerte_gas_rows = []
    offerte_luce_rows = []
    
    results = {}
    
    for idx, row in df_crm.iterrows():
        name = row.get('Name', 'Sconosciuto')
        tipo_prezzo = row.get('Tipo_prezzo__c', '')
        if pd.isna(tipo_prezzo):
            continue
            
        codice = row.get('Codice_univoco__c', '')
        tipo_offerta = 'Variabile' if tipo_prezzo == 'Indicizzato' else 'Fisso'
        
        info = {
            'Codice Univoco': codice,
            'Nome Prodotto': name,
            'Tipo': tipo_offerta,
            'Mercato': '',
            'Quota Fissa': 0.0,
            'Spread o Prezzo Fisso': 0.0,
            'Indice Usato (ARERA SS)': 0.0
        }
        
        # GAS
        if str(row.get('Tipo_servizio_GAS__c')).strip().upper() in ('X', 'SI'):
            info['Mercato'] = 'GAS'
            q_fissa = row.get('Quota_Comm_fissa_domestico_ENGIE_Gas__c')
            if pd.isna(q_fissa): q_fissa = row.get('Quota_Comm_fissa_ENGIE_Gas_anno__c', 0.0)
            
            p_gas = row.get('Quota_variabile_gas__c') if tipo_offerta == 'Fisso' else row.get('Spread_gas__c')
            if pd.isna(p_gas) and tipo_offerta == 'Fisso': p_gas = row.get('Corrispettivo_energia__c')
            if pd.isna(p_gas) and tipo_offerta == 'Variabile': p_gas = row.get('Quota_Alfa_Smc__c')
                
            if pd.notna(p_gas) and pd.notna(q_fissa):
                off = NuovaOfferta()
                off.commodity = 'G'
                off.tipo_offerta = tipo_offerta
                off.quota_fissa = float(q_fissa)
                off.prezzi = {'G': float(p_gas)}
                riga = off.riga()
                riga['PIVA_UTENTE'] = str(idx)
                offerte_gas_rows.append(riga)
                
                info['Quota Fissa'] = float(q_fissa)
                info['Spread o Prezzo Fisso'] = float(p_gas)
                info['Indice Usato (ARERA SS)'] = PSV_SCHEDA_SINTETICA if tipo_offerta == 'Variabile' else 0.0
                
                crm_1400 = row.get('CodCondSpeStimAnnoDOM1400smc__c')
                if pd.notna(crm_1400) and crm_1400 > 0 and tipo_offerta == 'Variabile':
                    info['Indice Stimato dal CRM (inverso)'] = round((crm_1400 - float(q_fissa)) / 1400 - float(p_gas), 5)
                else:
                    info['Indice Stimato dal CRM (inverso)'] = None
                
        # LUCE
        elif str(row.get('Tipo_servizio_EE__c')).strip().upper() in ('X', 'SI'):
            info['Mercato'] = 'LUCE'
            q_fissa = row.get('Quota_Comm_fissa_dom_ENGIE_Luce__c')
            if pd.isna(q_fissa): q_fissa = row.get('Quota_Comm_fissa_ENGIE_Luce_anno__c', 0.0)
            
            p_luce = row.get('Corrispettivo_energia_lordo_perdite_kW__c') if tipo_offerta == 'Fisso' else row.get('Spread_luce_lordo_perdite__c')
            if pd.isna(p_luce) and tipo_offerta == 'Fisso': p_luce = row.get('Corrispettivo_F1_lordo_perdite_kWh__c')
            if pd.isna(p_luce) and tipo_offerta == 'Variabile': p_luce = row.get('Quota_Alfa_kWh__c')
                
            if pd.notna(p_luce) and pd.notna(q_fissa):
                off = NuovaOfferta()
                off.commodity = 'E'
                off.tipo_offerta = tipo_offerta
                off.quota_fissa = float(q_fissa)
                off.prezzi = {'F0': float(p_luce)}
                riga = off.riga()
                riga['PIVA_UTENTE'] = str(idx)
                offerte_luce_rows.append(riga)
                
                info['Quota Fissa'] = float(q_fissa)
                info['Spread o Prezzo Fisso'] = float(p_luce)
                info['Indice Usato (ARERA SS)'] = PUN_SCHEDA_SINTETICA if tipo_offerta == 'Variabile' else 0.0
                
                crm_2700 = row.get('CodCondSpeStimAnnoR3kW2700kWh__c')
                if pd.notna(crm_2700) and crm_2700 > 0 and tipo_offerta == 'Variabile':
                    info['Indice Stimato dal CRM (inverso)'] = round((crm_2700 - float(q_fissa)) / 2700 - float(p_luce), 5)
                else:
                    info['Indice Stimato dal CRM (inverso)'] = None
                
        results[idx] = info
        
    df_gas_all = pd.DataFrame(offerte_gas_rows)
    df_luce_all = pd.DataFrame(offerte_luce_rows)
    
    # ------------------
    # CALCOLO GAS
    # ------------------
    if not df_gas_all.empty:
        for reg, macro in ambiti:
            for cons in consumi_gas:
                try:
                    res_g = calc.calculate_sas(df_gas_all, consumi={'F1': cons}, potenza=3, regione=reg)
                    res_g = res_g.set_index('PIVA_VENDITORE')
                    for row_idx in df_gas_all['PIVA_UTENTE']:
                        row_data = res_g.loc[str(row_idx)]
                        row_idx = int(row_idx)
                        # 1. Vista Codici Condotta (Solo Materia Prima)
                        results[row_idx][f"MAT_PRIMA_{macro}_{cons}smc"] = row_data['VENDITA']
                        if results[row_idx]['Codice Univoco'] == 'PLVD#00006' and cons == 120 and macro == 'NORD OCCIDENTALE':
                            print(f"DEBUG IN LOOP: {row_data['VENDITA']}")
                        # 2. Vista Lettera Rinnovo (SAS Senza Tasse)
                        results[row_idx][f"RINNOVO_{macro}_{cons}smc"] = row_data['VENDITA'] + row_data['RETE'] + row_data['ONERI']
                except Exception as e:
                    pass

    # ------------------
    # CALCOLO LUCE
    # ------------------
    if not df_luce_all.empty:
        for res, pot, cons in profili_ee:
            res_str = "Res" if res else "NonRes"
            try:
                res_e = calc.calculate_sas(df_luce_all, consumi={'F1': cons}, potenza=pot, residente=res, regione='Lombardia')
                res_e = res_e.set_index('PIVA_VENDITORE')
                for row_idx in df_luce_all['PIVA_UTENTE']:
                    row_data = res_e.loc[str(row_idx)]
                    row_idx = int(row_idx)
                    # 1. Vista Codici Condotta (Solo Materia Prima)
                    results[row_idx][f"MAT_PRIMA_{res_str}_{pot}kW_{cons}kWh"] = row_data['VENDITA']
                    # 2. Vista Lettera Rinnovo (SAS Senza Tasse)
                    results[row_idx][f"RINNOVO_{res_str}_{pot}kW_{cons}kWh"] = row_data['VENDITA'] + row_data['RETE'] + row_data['ONERI']
            except Exception as e:
                pass

    df_res = pd.DataFrame(list(results.values()))
    df_res = df_res[df_res['Codice Univoco'].notna() & (df_res['Codice Univoco'] != '')]
    
    out_path = BASE_DIR / "data" / "processed" / "Double_Check_CRM_v5.xlsx"
    workbook = xlsxwriter.Workbook(out_path)
    
    # FORMATI
    fmt_head = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
    fmt_mat = workbook.add_format({'bg_color': '#E3F2FD', 'num_format': '#,##0.00'})
    fmt_rinnovo = workbook.add_format({'bg_color': '#E8F5E9', 'num_format': '#,##0.00'})
    fmt_info = workbook.add_format({'bg_color': '#FFF9C4', 'num_format': '#,##0.0000'})
    
    # ---- SHEET 1: VISTA CODICI CONDOTTA (MATERIA PRIMA) ----
    ws1 = workbook.add_worksheet('1. Vista Codici Condotta')
    cols_mat = [c for c in df_res.columns if c.startswith('MAT_PRIMA_') or c in ['Codice Univoco', 'Nome Prodotto', 'Mercato']]
    df_mat = df_res[cols_mat]
    for c, col_name in enumerate(df_mat.columns):
        ws1.write(0, c, col_name.replace('MAT_PRIMA_', ''), fmt_head)
    for r, row_data in enumerate(df_mat.values):
        for c, val in enumerate(row_data):
            if pd.isna(val): ws1.write(r+1, c, "")
            elif isinstance(val, (int, float)): ws1.write(r+1, c, val, fmt_mat)
            else: ws1.write(r+1, c, val)
            
    # ---- SHEET 2: VISTA LETTERA RINNOVO (SAS NO TASSE) ----
    ws2 = workbook.add_worksheet('2. Lettere di Rinnovo')
    cols_rinnovo = [c for c in df_res.columns if c.startswith('RINNOVO_') or c in ['Codice Univoco', 'Nome Prodotto', 'Mercato']]
    df_rinnovo = df_res[cols_rinnovo]
    for c, col_name in enumerate(df_rinnovo.columns):
        ws2.write(0, c, col_name.replace('RINNOVO_', ''), fmt_head)
    for r, row_data in enumerate(df_rinnovo.values):
        for c, val in enumerate(row_data):
            if pd.isna(val): ws2.write(r+1, c, "")
            elif isinstance(val, (int, float)): ws2.write(r+1, c, val, fmt_rinnovo)
            else: ws2.write(r+1, c, val)
            
    # ---- SHEET 3: INFO CHECK / COMPONENTI BASE ----
    ws3 = workbook.add_worksheet('3. Info Check')
    cols_info = ['Codice Univoco', 'Nome Prodotto', 'Mercato', 'Tipo', 'Quota Fissa', 'Spread o Prezzo Fisso', 'Indice Usato (ARERA SS)']
    for c, col_name in enumerate(cols_info):
        ws3.write(0, c, col_name, fmt_head)
    for r, row_data in enumerate(df_res[cols_info].values):
        for c, val in enumerate(row_data):
            if pd.isna(val): ws3.write(r+1, c, "")
            elif isinstance(val, (int, float)): ws3.write(r+1, c, val, fmt_info)
            else: ws3.write(r+1, c, val)

    # ---- SHEET 4: STORICO INDICI ROLLING ----
    ws4 = workbook.add_worksheet('4. Storico Indici (Ref)')
    storici = [
        ['Mese Estrazione CRM', 'Indice Rolling GAS (€/Smc)', 'Indice Rolling EE (€/kWh)'],
        ['Luglio 2026', 0.60661, 0.11200],
        ['Agosto 2026', 0.47930, 0.12629],
        ['Settembre 2026', 0.62321, 0.14791],
        ['Ottobre 2026', 0.68000, 0.15736]
    ]
    for r, row_data in enumerate(storici):
        for c, val in enumerate(row_data):
            if r == 0: ws4.write(r, c, val, fmt_head)
            elif isinstance(val, (int, float)): ws4.write(r, c, val, fmt_info)
            else: ws4.write(r, c, val)
            
    # ---- SHEET 5: DOCUMENTAZIONE FORMULE ----
    ws5 = workbook.add_worksheet('5. Documentazione Formule')
    ws5.set_column('A:A', 30)
    ws5.set_column('B:B', 80)
    ws5.set_column('C:C', 60)
    
    docs = [
        ['Concetto / Calcolo', 'Formula Logica Utilizzata nello Script', 'Campi CRM di partenza / Mapping'],
        ['Quota Fissa (GAS)', 'Se vuoto Quota_Comm_fissa_domestico, usa Quota_Comm_fissa_anno', 'Quota_Comm_fissa_domestico_ENGIE_Gas__c (oppure Quota_Comm_fissa_ENGIE_Gas_anno__c)'],
        ['Spread / Prezzo Fisso (GAS)', 'Se Variabile: Spread_gas__c (o Quota_Alfa_Smc__c). Se Fisso: Quota_variabile_gas__c (o Corrispettivo_energia__c)', 'Spread_gas__c, Quota_Alfa_Smc__c, Quota_variabile_gas__c, Corrispettivo_energia__c'],
        ['PSV Lettere Rinnovo (GAS)', 'Indice Rolling fissato nel codice per le Lettere di Rinnovo (Attualmente fisso a 0.54395 come da vecchi rinnovi)', 'Variabile hardcoded (PSV_SCHEDA_SINTETICA)'],
        ['Spesa Materia Prima (Foglio 1)', 'Quota Fissa + Consumo_smc * (PSV + Spread)', 'Calcolo puro componente energia (motore FastSASCalculator senza reti/oneri/tasse)'],
        ['Spesa Lettera Rinnovo (Foglio 2)', 'Materia Prima + Rete + Oneri di Sistema (NO TASSE: escluse Accise e IVA)', 'Calcolo completo FastSASCalculator con tariffe ARERA. No campi CRM diretti'],
        ['Indice Stimato CRM inverso (Foglio 3)', '[(Spesa CRM 1400 smc - Quota Fissa) / 1400] - Spread', 'Reverse engineering su: CodCondSpeStimAnnoDOM1400smc__c'],
    ]
    for r, row_data in enumerate(docs):
        for c, val in enumerate(row_data):
            if r == 0: ws5.write(r, c, val, fmt_head)
            else: ws5.write(r, c, val)
            
    workbook.close()
    print(f"File salvato in: {out_path}")

if __name__ == "__main__":
    run_double_check()
