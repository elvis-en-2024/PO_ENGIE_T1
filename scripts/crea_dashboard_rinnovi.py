import pandas as pd
import numpy as np
import sys
import xlsxwriter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(BASE_DIR.as_posix())

from engine.offerta_simulata import NuovaOfferta
from engine.sas_calculator_fast import FastSASCalculator

def run_rinnovi_dashboard():
    crm_path = BASE_DIR / "TEST CRM" / "Product2-08_10_2026.csv"
    if not crm_path.exists():
        crm_path = r"C:\Users\XP6566\OneDrive - ENGIE\Documenti\PO_scraping_2026\TEST CRM\Product2-08_10_2026.csv"
        
    print(f"Caricamento file CRM da: {crm_path}")
    df_crm = pd.read_csv(crm_path)
    
    dummy_df = pd.DataFrame(columns=["commodity", "PIVA_UTENTE", "COD_OFFERTA", "TIPO_OFFERTA"])
    calc = FastSASCalculator(dummy_df)
    
    # -------------------------------------------------------------
    # PARAMETRI ARERA SCHEDA SINTETICA / LETTERA RINNOVO
    # -------------------------------------------------------------
    # Sostituiamo i forward del GME con i parametri fissi ARERA
    # per la Scheda Sintetica (es. Settembre 2026)
    PSV_SCHEDA_SINTETICA = 0.54395
    PUN_SCHEDA_SINTETICA = 0.125  # Inserire PUN Scheda Sintetica corretto
    
    calc.forward = {
        'gas_mesi': [PSV_SCHEDA_SINTETICA] * 12,
        'ee': {'F0': PUN_SCHEDA_SINTETICA, 'F1': PUN_SCHEDA_SINTETICA, 'F23': PUN_SCHEDA_SINTETICA}
    }
    
    profili_ee = [
        (True, 3, 1500), (True, 3, 2200), (True, 3, 2700), (True, 3, 3200),
        (True, 4.5, 3500), (True, 6, 6000), (False, 3, 900), (False, 3, 4000)
    ]
    
    ambiti = [
        ("Piemonte", "NORD OCCIDENTALE"), ("Lombardia", "NORD ORIENTALE"),
        ("Toscana", "CENTRALE"), ("Abruzzo", "CENTRO-SUD ORIENTALE"),
        ("Lazio", "CENTRO-SUD OCCIDENTALE"), ("Calabria", "MERIDIONALE")
    ]
    consumi_gas = [120, 480, 700, 1400, 2000, 5000]
    
    offerte_luce_rows = []
    offerte_gas_rows = []
    results_dict = {}
    
    for idx, row in df_crm.iterrows():
        name = row.get('Name', 'Sconosciuto')
        tipo_prezzo = row.get('Tipo_prezzo__c', '')
        if pd.isna(tipo_prezzo):
            continue
            
        tipo_offerta = 'Variabile' if tipo_prezzo == 'Indicizzato' else 'Fisso'
        results_dict[idx] = {'Codice Univoco': row.get('Codice_univoco__c', ''), 'Nome CRM': name, 'Tipo': tipo_offerta}
        
        # --- LUCE ---
        if str(row.get('Tipo_servizio_EE__c')).strip().upper() in ('X', 'SI'):
            q_fissa = row.get('Quota_Comm_fissa_dom_ENGIE_Luce__c')
            if pd.isna(q_fissa): q_fissa = row.get('Quota_Comm_fissa_ENGIE_Luce_anno__c', 0.0)
            
            p_luce = row.get('Corrispettivo_energia_lordo_perdite_kW__c') if tipo_offerta == 'Fisso' else row.get('Spread_luce_lordo_perdite__c')
            if pd.isna(p_luce) and tipo_offerta == 'Fisso': p_luce = row.get('Corrispettivo_F1_lordo_perdite_kWh__c')
            if pd.isna(p_luce) and tipo_offerta == 'Variabile': p_luce = row.get('Quota_Alfa_kWh__c')
                
            if pd.notna(p_luce) and pd.notna(q_fissa):
                off_e = NuovaOfferta()
                off_e.commodity = 'E'
                off_e.tipo_offerta = tipo_offerta
                off_e.quota_fissa = float(q_fissa)
                off_e.prezzi = {'F0': float(p_luce)}
                riga_e = off_e.riga()
                riga_e['ID_CRM'] = idx
                offerte_luce_rows.append(riga_e)
        
        # --- GAS ---
        if str(row.get('Tipo_servizio_GAS__c')).strip().upper() in ('X', 'SI'):
            q_fissa_g = row.get('Quota_Comm_fissa_domestico_ENGIE_Gas__c')
            if pd.isna(q_fissa_g): q_fissa_g = row.get('Quota_Comm_fissa_ENGIE_Gas_anno__c', 0.0)
                
            p_gas = row.get('Quota_variabile_gas__c') if tipo_offerta == 'Fisso' else row.get('Spread_gas__c')
            if pd.isna(p_gas) and tipo_offerta == 'Fisso': p_gas = row.get('Corrispettivo_energia__c')
            if pd.isna(p_gas) and tipo_offerta == 'Variabile': p_gas = row.get('Quota_Alfa_Smc__c')
                
            if pd.notna(p_gas) and pd.notna(q_fissa_g):
                off_g = NuovaOfferta()
                off_g.commodity = 'G'
                off_g.tipo_offerta = tipo_offerta
                off_g.quota_fissa = float(q_fissa_g)
                off_g.prezzi = {'G': float(p_gas)}
                riga_g = off_g.riga()
                riga_g['ID_CRM'] = idx
                offerte_gas_rows.append(riga_g)
                
    df_luce_all = pd.DataFrame(offerte_luce_rows)
    df_gas_all = pd.DataFrame(offerte_gas_rows)
    
    print(f"Preparate {len(df_luce_all)} offerte Luce e {len(df_gas_all)} offerte Gas.")
    
    # Calcolo Spesa Annua ESCLUDENDO LE IMPOSTE (VENDITA + RETE + ONERI)
    if not df_luce_all.empty:
        for res, pot, cons in profili_ee:
            res_str = "Res" if res else "NonRes"
            col_name = f"ELE_{res_str}_{pot}kW_{cons}kWh"
            try:
                res_e = calc.calculate_sas(df_luce_all, consumi={'F1': cons}, potenza=pot, residente=res, regione='Lombardia')
                for i, row_idx in enumerate(df_luce_all['ID_CRM']):
                    row_data = res_e.iloc[i]
                    results_dict[row_idx][col_name] = row_data['VENDITA'] + row_data['RETE'] + row_data['ONERI']
            except Exception as e:
                pass
                
    if not df_gas_all.empty:
        for reg, macro in ambiti:
            for cons in consumi_gas:
                col_name = f"GAS_{reg}_{cons}smc"
                try:
                    res_g = calc.calculate_sas(df_gas_all, consumi={'F1': cons}, potenza=3, regione=reg)
                    for i, row_idx in enumerate(df_gas_all['ID_CRM']):
                        row_data = res_g.iloc[i]
                        results_dict[row_idx][col_name] = row_data['VENDITA'] + row_data['RETE'] + row_data['ONERI']
                except Exception as e:
                    pass
                    
    df_res = pd.DataFrame(list(results_dict.values()))
    df_res = df_res[df_res['Codice Univoco'].notna() & (df_res['Codice Univoco'] != '')]
    
    # -------------------------------------------------------------
    # CREAZIONE EXCEL DASHBOARD LETTERA DI RINNOVO
    # -------------------------------------------------------------
    out_path = BASE_DIR / "data" / "processed" / "Lettera_Rinnovo_Dashboard.xlsx"
    workbook = xlsxwriter.Workbook(out_path)
    
    # Foglio Database
    ws_db = workbook.add_worksheet('Database')
    headers = list(df_res.columns)
    for col_num, header in enumerate(headers):
        ws_db.write(0, col_num, header)
    for row_num, row_data in enumerate(df_res.values):
        for col_num, cell_data in enumerate(row_data):
            if not pd.isna(cell_data):
                ws_db.write(row_num + 1, col_num, cell_data)
                
    # Foglio Dashboard Lettera
    ws = workbook.add_worksheet('Lettera di Rinnovo')
    fmt_title = workbook.add_format({'bold': True, 'font_size': 16, 'bg_color': '#4CAF50', 'font_color': 'white'})
    fmt_subtitle = workbook.add_format({'bold': True, 'font_size': 12, 'bg_color': '#E8F5E9'})
    fmt_header = workbook.add_format({'bold': True, 'bottom': 1, 'bg_color': '#F1F8E9'})
    fmt_currency = workbook.add_format({'num_format': '#,##0.00 €'})
    fmt_bold = workbook.add_format({'bold': True})
    
    ws.set_column('A:A', 25)
    ws.set_column('B:B', 20)
    ws.set_column('C:C', 20)
    ws.set_column('D:D', 20)
    ws.set_column('E:E', 20)
    ws.set_column('F:F', 20)
    ws.set_column('G:G', 20)
    
    ws.write('A1', 'DASHBOARD LETTERA DI RINNOVO (SENZA IMPOSTE)', fmt_title)
    ws.write('A3', 'Seleziona Codice Univoco:', fmt_bold)
    
    num_rows = len(df_res)
    ws.data_validation('B3', {'validate': 'list', 'source': f'=Database!$A$2:$A${num_rows+1}'})
    ws.write('B3', str(df_res.iloc[0]['Codice Univoco']) if num_rows > 0 else "")
    
    ws.write('A4', 'Nome Prodotto:', fmt_bold)
    ws.write_formula('B4', f'=VLOOKUP(B3, Database!A:AW, 2, FALSE)')
    ws.write('A5', 'PSV Usato (Scheda Sintetica):', fmt_bold)
    ws.write('B5', f'{PSV_SCHEDA_SINTETICA} €/Smc')
    
    row = 7
    ws.merge_range(f'A{row}:D{row}', 'ENERGIA ELETTRICA (Al netto di IVA e Imposte)', fmt_title)
    row += 1
    ws.write(f'A{row}', 'Tipo abitazione', fmt_header)
    ws.write(f'B{row}', 'Potenza', fmt_header)
    ws.write(f'C{row}', 'Consumo', fmt_header)
    ws.write(f'D{row}', 'Spesa annua stimata', fmt_header)
    row += 1
    
    profili_ee = [
        ('Residente', '3 kW', '1.500 kWh', 4), ('Residente', '3 kW', '2.200 kWh', 5),
        ('Residente', '3 kW', '2.700 kWh', 6), ('Residente', '3 kW', '3.200 kWh', 7),
        ('Residente', '4.5 kW', '3.500 kWh', 8), ('Residente', '6 kW', '6.000 kWh', 9),
        ('Non residente', '3 kW', '900 kWh', 10), ('Non residente', '3 kW', '4.000 kWh', 11)
    ]
    for res, pot, cons, col_idx in profili_ee:
        ws.write(f'A{row}', res)
        ws.write(f'B{row}', pot)
        ws.write(f'C{row}', cons)
        ws.write_formula(f'D{row}', f'=VLOOKUP($B$3, Database!$A:$AW, {col_idx}, FALSE)', fmt_currency)
        row += 1
        
    row += 2
    ws.merge_range(f'A{row}:F{row}', 'GAS (Al netto di IVA e Imposte)', fmt_title)
    row += 2
    
    ambiti_left = [
        ("AMBITO NORD OCCIDENTALE VALLE D'AOSTA, PIEMONTE, LIGURIA", 12),
        ("AMBITO CENTRALE TOSCANA, UMBRIA, MARCHE", 24),
        ("AMBITO CENTRO-SUD OCCIDENTALE LAZIO, CAMPANIA", 36)
    ]
    ambiti_right = [
        ("AMBITO NORD ORIENTALE LOMBARDIA, TRENTINO, VENETO, FRIULI, EMR", 18),
        ("AMBITO CENTRO-SUD ORIENTALE ABRUZZO, MOLISE, PUGLIA, BASILICATA", 30),
        ("AMBITO MERIDIONALE CALABRIA, SICILIA, SARDEGNA", 42)
    ]
    
    start_row_gas = row
    for i in range(3):
        r = start_row_gas + i * 9
        titolo_L, col_idx_L = ambiti_left[i]
        ws.merge_range(f'A{r}:C{r}', titolo_L, fmt_subtitle)
        ws.write(f'A{r+1}', 'Consumo annuo', fmt_header)
        ws.write(f'C{r+1}', 'Spesa annua stimata', fmt_header)
        for j, c in enumerate([120, 480, 700, 1400, 2000, 5000]):
            ws.write(f'A{r+2+j}', f'{c} smc')
            ws.write_formula(f'C{r+2+j}', f'=VLOOKUP($B$3, Database!$A:$AW, {col_idx_L+j}, FALSE)', fmt_currency)
            
        titolo_R, col_idx_R = ambiti_right[i]
        ws.merge_range(f'D{r}:F{r}', titolo_R, fmt_subtitle)
        ws.write(f'D{r+1}', 'Consumo annuo', fmt_header)
        ws.write(f'F{r+1}', 'Spesa annua stimata', fmt_header)
        for j, c in enumerate([120, 480, 700, 1400, 2000, 5000]):
            ws.write(f'D{r+2+j}', f'{c} smc')
            ws.write_formula(f'F{r+2+j}', f'=VLOOKUP($B$3, Database!$A:$AW, {col_idx_R+j}, FALSE)', fmt_currency)

    workbook.close()
    print(f"Lettera di Rinnovo Dashboard creata con successo in: {out_path}")

if __name__ == "__main__":
    run_rinnovi_dashboard()
