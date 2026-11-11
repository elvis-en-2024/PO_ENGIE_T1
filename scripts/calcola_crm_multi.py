import pandas as pd
import numpy as np
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(BASE_DIR.as_posix())

from engine.offerta_simulata import NuovaOfferta
from engine.sas_calculator_fast import FastSASCalculator

def run_multi_test():
    crm_path = r"C:\Users\XP6566\OneDrive - ENGIE\Documenti\PO_scraping_2026\TEST CRM\Product2-08_10_2026.csv"
    print(f"Caricamento file CRM da: {crm_path}")
    df_crm = pd.read_csv(crm_path)
    
    # Caricamento storico vuoto o minimo per instanziare il calcolatore
    dummy_df = pd.DataFrame(columns=["commodity", "PIVA_UTENTE", "COD_OFFERTA", "TIPO_OFFERTA"])
    calc = FastSASCalculator(dummy_df)
    
    # Profili Energia Elettrica: (Residente, Potenza, Consumo)
    profili_ee = [
        (True, 3, 1500),
        (True, 3, 2200),
        (True, 3, 2700),
        (True, 3, 3200),
        (True, 4.5, 3500),
        (True, 6, 6000),
        (False, 3, 900),
        (False, 3, 4000)
    ]
    
    # Profili Gas: (Regione_Rappresentativa, Macroarea, Consumo)
    profili_gas = []
    ambiti = [
        ("Piemonte", "NORD OCCIDENTALE (Valle d'Aosta, Piemonte, Liguria)"),
        ("Lombardia", "NORD ORIENTALE (Lombardia, Trentino-Alto Adige, Veneto, Friuli-Venezia Giulia, Emilia-Romagna)"),
        ("Toscana", "CENTRALE (Toscana, Umbria, Marche)"),
        ("Abruzzo", "CENTRO-SUD ORIENTALE (Abruzzo, Molise, Puglia, Basilicata)"),
        ("Lazio", "CENTRO-SUD OCCIDENTALE (Lazio, Campania)"),
        ("Calabria", "MERIDIONALE (Calabria, Sicilia, Sardegna)")
    ]
    consumi_gas = [120, 480, 700, 1400, 2000, 5000]
    
    results = []
    
    for idx, row in df_crm.iterrows():
        name = row.get('Name', 'Sconosciuto')
        tipo_prezzo = row.get('Tipo_prezzo__c', '')
        if pd.isna(tipo_prezzo):
            continue
            
        tipo_offerta = 'Variabile' if tipo_prezzo == 'Indicizzato' else 'Fisso'
        
        row_res = {
            'Nome CRM': name,
            'Tipo': tipo_offerta
        }
        
        # --- ENERGIA ELETTRICA ---
        if str(row.get('Tipo_servizio_EE__c')).strip().upper() in ('X', 'SI'):
            quota_fissa_luce = row.get('Quota_Comm_fissa_dom_ENGIE_Luce__c')
            if pd.isna(quota_fissa_luce):
                quota_fissa_luce = row.get('Quota_Comm_fissa_ENGIE_Luce_anno__c', 0.0)
                
            prezzo_luce = np.nan
            if tipo_offerta == 'Fisso':
                prezzo_luce = row.get('Corrispettivo_energia_lordo_perdite_kW__c')
                if pd.isna(prezzo_luce):
                    prezzo_luce = row.get('Corrispettivo_F1_lordo_perdite_kWh__c')
            else:
                prezzo_luce = row.get('Spread_luce_lordo_perdite__c')
                if pd.isna(prezzo_luce):
                    prezzo_luce = row.get('Quota_Alfa_kWh__c')
                    
            if pd.notna(prezzo_luce) and pd.notna(quota_fissa_luce):
                off_e = NuovaOfferta()
                off_e.commodity = 'E'
                off_e.tipo_offerta = tipo_offerta
                off_e.quota_fissa = float(quota_fissa_luce)
                off_e.prezzi = {'F0': float(prezzo_luce)}
                
                df_off = pd.DataFrame([off_e.riga()])
                
                for res, pot, cons in profili_ee:
                    res_str = "Res" if res else "NonRes"
                    col_name = f"ELE_{res_str}_{pot}kW_{cons}kWh"
                    try:
                        res_e = calc.calculate_sas(df_off, consumi={'F1': cons}, potenza=pot, residente=res, regione='Lombardia')
                        row_res[col_name] = res_e.iloc[0]['SAS']
                    except Exception as e:
                        row_res[col_name] = np.nan
            else:
                for res, pot, cons in profili_ee:
                    res_str = "Res" if res else "NonRes"
                    row_res[f"ELE_{res_str}_{pot}kW_{cons}kWh"] = np.nan
        
        # --- GAS NATURALE ---
        if str(row.get('Tipo_servizio_GAS__c')).strip().upper() in ('X', 'SI'):
            quota_fissa_gas = row.get('Quota_Comm_fissa_domestico_ENGIE_Gas__c')
            if pd.isna(quota_fissa_gas):
                quota_fissa_gas = row.get('Quota_Comm_fissa_ENGIE_Gas_anno__c', 0.0)
                
            prezzo_gas = np.nan
            if tipo_offerta == 'Fisso':
                prezzo_gas = row.get('Quota_variabile_gas__c')
                if pd.isna(prezzo_gas):
                    prezzo_gas = row.get('Corrispettivo_energia__c')
            else:
                prezzo_gas = row.get('Spread_gas__c')
                if pd.isna(prezzo_gas):
                    prezzo_gas = row.get('Quota_Alfa_Smc__c')
                    
            if pd.notna(prezzo_gas) and pd.notna(quota_fissa_gas):
                off_g = NuovaOfferta()
                off_g.commodity = 'G'
                off_g.tipo_offerta = tipo_offerta
                off_g.quota_fissa = float(quota_fissa_gas)
                off_g.prezzi = {'G': float(prezzo_gas)}
                
                df_off = pd.DataFrame([off_g.riga()])
                
                for reg, macro in ambiti:
                    for cons in consumi_gas:
                        col_name = f"GAS_{reg}_{cons}smc"
                        try:
                            res_g = calc.calculate_sas(df_off, consumi={'F1': cons}, potenza=3, regione=reg)
                            row_res[col_name] = res_g.iloc[0]['SAS']
                        except Exception as e:
                            row_res[col_name] = np.nan
            else:
                for reg, macro in ambiti:
                    for cons in consumi_gas:
                        row_res[f"GAS_{reg}_{cons}smc"] = np.nan
                        
        results.append(row_res)
        
    df_res = pd.DataFrame(results)
    out_path = BASE_DIR / "data" / "processed" / "TEST_CRM_multi_risultati.csv"
    df_res.to_csv(out_path, index=False, sep=';', decimal=',')
    print(f"Analisi multi-profilo completata! Esportati {len(df_res)} prodotti.")
    print(f"File salvato in: {out_path}")

if __name__ == "__main__":
    run_multi_test()
