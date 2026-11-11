import pandas as pd
from engine.sas_calculator_fast import FastSASCalculator

def calcola_tutto():
    print("Inizializzazione...")
    # Carica prodotti CRM
    file_path = r"C:\Users\XP6566\OneDrive - ENGIE\Documenti\PO_scraping_2026\TEST CRM\Prodotti_Ottobre_CRM.csv"
    df_crm = pd.read_csv(file_path)
    
    offerte_list = []
    for _, row in df_crm.iterrows():
        codice = row.get("Codice_univoco__c", "")
        if pd.isna(codice):
            continue
            
        segment = row.get("Segment__c", "MM")
        # Identifichiamo Luce vs Gas
        if "LUCE" in str(row.get("Name", "")).upper() or pd.notna(row.get("Spread_luce__c")):
            commodity = "E"
        else:
            commodity = "G"
            
        fissa = row.get("Quota_Comm_fissa_altri_usi_ENGIE_Gas__c") if commodity=="G" and segment=="SME" else row.get("Quota_Comm_fissa_dom_ENGIE_Gas__c")
        if pd.isna(fissa):
            fissa = row.get("Quota_Comm_fissa_altri_usi_BT_ENGIE_Luce__c") if commodity=="E" and segment=="SME" else row.get("Quota_Comm_fissa_dom_BT_ENGIE_Luce__c")
        
        spread = row.get("Spread_gas__c") if commodity=="G" else row.get("Spread_luce_lordo_perdite__c")
        
        offerte_list.append({
            "PIVA_UTENTE": codice,
            "COD_OFFERTA": codice,
            "NOME_OFFERTA": row.get("Name", codice),
            "commodity": commodity,
            "TIPO_OFFERTA": "Variabile",
            "TIPO_CLIENTE": "Domestico" if segment=="MM" else "Altri Usi",
            "TIPOLOGIA_FASCE": "Monorario",
            "QUOTA_FISSA": float(fissa) if pd.notna(fissa) else 0.0,
            "PREZZO": float(spread) if pd.notna(spread) else 0.0,
            "segment_crm": segment
        })
        
    df_off = pd.DataFrame(offerte_list).drop_duplicates(subset=["COD_OFFERTA"])
    print(f"Offerte processate: {len(df_off)}")
    
    # Inizializza il motore ARERA
    calc = FastSASCalculator(df_off)
    
    # ---------------------------------------------------------
    # INIEZIONE DEI FORWARD UFFICIALI (Acquirente Unico)
    # ---------------------------------------------------------
    pun = 0.169897
    psv_mesi = [0.856855]*3 + [0.843246]*3 + [0.621851]*3 + [0.575161]*3
    
    calc.forward = {
        "ee": {"F0": pun, "F1": pun, "F23": pun},
        "gas_mesi": psv_mesi
    }
    
    # Colonne in output
    risultati = []
    
    df_gas = df_off[df_off['commodity'] == 'G']
    df_luce = df_off[df_off['commodity'] == 'E']
    
    print("Calcolo in corso per tutte le combinazioni ARERA...")
    
    # Gas: 120, 480, 700, 1400, 2000, 5000 (Domestico)
    # Gas AU: 1500, 3000, 5000, 20000, 45000
    
    for _, row in df_gas.iterrows():
        cod = row["COD_OFFERTA"]
        is_dom = row["segment_crm"] == "MM"
        
        # DOM
        res_gas_dom = calc.calculate_sas(df_gas[df_gas["COD_OFFERTA"]==cod], 
                                         consumi={'F1': 1400}, potenza=3, regione="Lombardia")
        if not res_gas_dom.empty:
            mp_dom = res_gas_dom.iloc[0]["VENDITA"]
            tot_dom = res_gas_dom.iloc[0]["SAS"]
        else:
            mp_dom, tot_dom = 0, 0
            
        # AU
        res_gas_au = calc.calculate_sas(df_gas[df_gas["COD_OFFERTA"]==cod], 
                                         consumi={'F1': 1500}, potenza=3, regione="Lombardia")
        if not res_gas_au.empty:
            mp_au = res_gas_au.iloc[0]["VENDITA"]
            tot_au = res_gas_au.iloc[0]["SAS"]
        else:
            mp_au, tot_au = 0, 0
            
        risultati.append({
            "Codice": cod,
            "Commodity": "Gas",
            "Segmento": row["segment_crm"],
            "Materia_Prima_DOM_1400": mp_dom if is_dom else 0.0,
            "Spesa_Totale_DOM_1400": tot_dom if is_dom else 0.0,
            "Materia_Prima_AU_1500": mp_au if not is_dom else 0.0,
            "Spesa_Totale_AU_1500": tot_au if not is_dom else 0.0
        })
        
    for _, row in df_luce.iterrows():
        cod = row["COD_OFFERTA"]
        is_dom = row["segment_crm"] == "MM"
        
        # DOM
        res_ee_dom = calc.calculate_sas(df_luce[df_luce["COD_OFFERTA"]==cod], 
                                        consumi={'F1': 2700}, potenza=3, residente=True)
        if not res_ee_dom.empty:
            mp_dom = res_ee_dom.iloc[0]["VENDITA"]
            tot_dom = res_ee_dom.iloc[0]["SAS"]
        else:
            mp_dom, tot_dom = 0, 0
            
        # AU
        res_ee_au = calc.calculate_sas(df_luce[df_luce["COD_OFFERTA"]==cod], 
                                        consumi={'F1': 100000}, potenza=15, residente=False)
        if not res_ee_au.empty:
            mp_au = res_ee_au.iloc[0]["VENDITA"]
            tot_au = res_ee_au.iloc[0]["SAS"]
        else:
            mp_au, tot_au = 0, 0
            
        risultati.append({
            "Codice": cod,
            "Commodity": "Luce",
            "Segmento": row["segment_crm"],
            "Materia_Prima_DOM_2700": mp_dom if is_dom else 0.0,
            "Spesa_Totale_DOM_2700": tot_dom if is_dom else 0.0,
            "Materia_Prima_AU_100000": mp_au if not is_dom else 0.0,
            "Spesa_Totale_AU_100000": tot_au if not is_dom else 0.0
        })
        
    df_out = pd.DataFrame(risultati)
    out_path = r"C:\PO_ENGIE\PO_ENGIE_T1\data\processed\CodiciCondotta_Corretti_Forward.xlsx"
    df_out.to_excel(out_path, index=False)
    print(f"Salvato in {out_path}")

if __name__ == '__main__':
    calcola_tutto()
