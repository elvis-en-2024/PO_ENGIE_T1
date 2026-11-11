import pandas as pd
from engine.sas_calculator_fast import FastSASCalculator

def calcola_schema():
    file_path = r"C:\Users\XP6566\OneDrive - ENGIE\Documenti\PO_scraping_2026\TEST CRM\Prodotti_Ottobre_CRM.csv"
    df_crm = pd.read_csv(file_path)
    
    # 1. PREPARA DF PER MOTORE ARERA
    offerte_list = []
    for _, row in df_crm.iterrows():
        codice = row.get("Codice_univoco__c", "")
        if pd.isna(codice):
            continue
        segment = row.get("Segment__c", "MM")
        if "LUCE" in str(row.get("Name", "")).upper() or pd.notna(row.get("Spread_luce__c")):
            commodity = "E"
            fissa = row.get("Quota_Comm_fissa_altri_usi_BT_ENGIE_Luce__c") if segment=="SME" else row.get("Quota_Comm_fissa_dom_BT_ENGIE_Luce__c")
            spread = row.get("Spread_luce_lordo_perdite__c")
        else:
            commodity = "G"
            fissa = row.get("Quota_Comm_fissa_altri_usi_ENGIE_Gas__c") if segment=="SME" else row.get("Quota_Comm_fissa_dom_ENGIE_Gas__c")
            spread = row.get("Spread_gas__c")
            
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
    
    calc = FastSASCalculator(df_off)
    # Forward passati dall'utente
    pun = 0.169897
    psv_mesi = [0.856855]*3 + [0.843246]*3 + [0.621851]*3 + [0.575161]*3
    calc.forward = {"ee": {"F0": pun, "F1": pun, "F23": pun}, "gas_mesi": psv_mesi}
    
    # 2. DEFINISCI COLONNE E CONSUMI
    gas_dom = [('CodCondSpeStimAnnoDOM120smc__c', 120), ('CodCondSpeStimAnnoDOM480smc__c', 480), ('CodCondSpeStimAnnoDOM700smc__c', 700), ('CodCondSpeStimAnnoDOM1400smc__c', 1400), ('CodCondSpeStimAnnoDOM2000smc__c', 2000), ('CodCondSpeStimAnnoDOM5000smc__c', 5000)]
    gas_au = [('CodCondSpeStimAnnoAU1500smc__c', 1500), ('CodCondSpeStimAnnoAU3000smc__c', 3000), ('CodCondSpeStimAnnoAU5000smc__c', 5000), ('CodCondSpeStimAnnoAU20000smc__c', 20000), ('CodCondSpeStimAnnoAU45000smc__c', 45000)]
    ee_res = [('CodCondSpeStimAnnoR3kW1500kWh__c', 1500, 3, True), ('CodCondSpeStimAnnoR3kW2200kWh__c', 2200, 3, True), ('CodCondSpeStimAnnoR3kW2700kWh__c', 2700, 3, True), ('CodCondSpeStimAnnoR3kW3200kWh__c', 3200, 3, True), ('CodCondSpeStimAnnoR4_5kW3500kWh__c', 3500, 4.5, True), ('CodCondSpeStimAnnoR6kW6000kWh__c', 6000, 6, True)]
    ee_nores = [('CodCondSpeStimAnnoNR3kW900kWh__c', 900, 3, False), ('CodCondSpeStimAnnoNR3kW4000kWh__c', 4000, 3, False)]
    ee_au = [('CodCondSpeStimAnnoAU1900kWh__c', 1900, 15, False), ('CodCondSpeStimAnnoAU3600kWh__c', 3600, 15, False), ('CodCondSpeStimAnnoAU6800kWh__c', 6800, 15, False), ('CodCondSpeStimAnnoAU45000kWh__c', 45000, 15, False), ('CodCondSpeStimAnnoAU100000kWh__c', 100000, 15, False)]
    
    # 3. CALCOLO E COSTRUZIONE RIGA
    risultati = []
    print("Elaborazione righe...")
    for _, row in df_crm.iterrows():
        codice = row.get("Codice_univoco__c", "")
        if codice not in df_off["COD_OFFERTA"].values: continue
        
        commodity = df_off[df_off["COD_OFFERTA"]==codice].iloc[0]["commodity"]
        is_dom = row.get("Segment__c", "MM") == "MM"
        
        out = {"Codice": codice, "Commodity": commodity, "Segmento": row.get("Segment__c", "MM"), "Release": row.get("Release__c", "")}
        
        if commodity == "G":
            # Domestici
            for campo, cons in gas_dom:
                out[f"CRM {campo}"] = row.get(campo, 0.0) if pd.notna(row.get(campo)) else 0.0
                if is_dom:
                    r = calc.calculate_sas(df_off[df_off["COD_OFFERTA"]==codice], consumi={'F1': cons}, potenza=3, regione="Lombardia")
                    out[f"Mio Calcolo MP {campo}"] = r.iloc[0]["VENDITA"] if not r.empty else 0.0
                    out[f"Mio Calcolo SAS {campo}"] = r.iloc[0]["SAS"] if not r.empty else 0.0
                else:
                    out[f"Mio Calcolo MP {campo}"] = 0.0
                    out[f"Mio Calcolo SAS {campo}"] = 0.0
            # AU
            for campo, cons in gas_au:
                out[f"CRM {campo}"] = row.get(campo, 0.0) if pd.notna(row.get(campo)) else 0.0
                if not is_dom:
                    r = calc.calculate_sas(df_off[df_off["COD_OFFERTA"]==codice], consumi={'F1': cons}, potenza=3, regione="Lombardia")
                    out[f"Mio Calcolo MP {campo}"] = r.iloc[0]["VENDITA"] if not r.empty else 0.0
                    out[f"Mio Calcolo SAS {campo}"] = r.iloc[0]["SAS"] if not r.empty else 0.0
                else:
                    out[f"Mio Calcolo MP {campo}"] = 0.0
                    out[f"Mio Calcolo SAS {campo}"] = 0.0
        else:
            # EE Res
            for campo, cons, pot, res in ee_res:
                out[f"CRM {campo}"] = row.get(campo, 0.0) if pd.notna(row.get(campo)) else 0.0
                if is_dom:
                    r = calc.calculate_sas(df_off[df_off["COD_OFFERTA"]==codice], consumi={'F1': cons}, potenza=pot, residente=res)
                    out[f"Mio Calcolo MP {campo}"] = r.iloc[0]["VENDITA"] if not r.empty else 0.0
                    out[f"Mio Calcolo SAS {campo}"] = r.iloc[0]["SAS"] if not r.empty else 0.0
                else:
                    out[f"Mio Calcolo MP {campo}"] = 0.0
                    out[f"Mio Calcolo SAS {campo}"] = 0.0
            # EE NoRes
            for campo, cons, pot, res in ee_nores:
                out[f"CRM {campo}"] = row.get(campo, 0.0) if pd.notna(row.get(campo)) else 0.0
                if is_dom:
                    r = calc.calculate_sas(df_off[df_off["COD_OFFERTA"]==codice], consumi={'F1': cons}, potenza=pot, residente=res)
                    out[f"Mio Calcolo MP {campo}"] = r.iloc[0]["VENDITA"] if not r.empty else 0.0
                    out[f"Mio Calcolo SAS {campo}"] = r.iloc[0]["SAS"] if not r.empty else 0.0
                else:
                    out[f"Mio Calcolo MP {campo}"] = 0.0
                    out[f"Mio Calcolo SAS {campo}"] = 0.0
            # EE AU
            for campo, cons, pot, res in ee_au:
                out[f"CRM {campo}"] = row.get(campo, 0.0) if pd.notna(row.get(campo)) else 0.0
                if not is_dom:
                    r = calc.calculate_sas(df_off[df_off["COD_OFFERTA"]==codice], consumi={'F1': cons}, potenza=pot, residente=res)
                    out[f"Mio Calcolo MP {campo}"] = r.iloc[0]["VENDITA"] if not r.empty else 0.0
                    out[f"Mio Calcolo SAS {campo}"] = r.iloc[0]["SAS"] if not r.empty else 0.0
                else:
                    out[f"Mio Calcolo MP {campo}"] = 0.0
                    out[f"Mio Calcolo SAS {campo}"] = 0.0
                    
        risultati.append(out)
        
    df_out = pd.DataFrame(risultati)
    out_path = r"C:\PO_ENGIE\PO_ENGIE_T1\data\processed\Codici_Condotta_CRM_Schema_Fwd.xlsx"
    df_out.to_excel(out_path, index=False)
    print(f"Salvato in {out_path}")

if __name__ == '__main__':
    calcola_schema()
