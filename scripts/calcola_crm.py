import pandas as pd
import numpy as np
from datetime import date
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(BASE_DIR.as_posix())

from engine.offerta_simulata import NuovaOfferta, COD_SIMULATA
from engine.sas_calculator_fast import FastSASCalculator

def run_test():
    crm_path = r"C:\Users\XP6566\OneDrive - ENGIE\Documenti\PO_scraping_2026\TEST CRM\Product2-08_10_2026.csv"
    print(f"Caricamento file CRM da: {crm_path}")
    df_crm = pd.read_csv(crm_path)
    
    # Caricamento storico vuoto o minimo per instanziare il calcolatore
    # (FastSASCalculator scarica in automatico i parametri e forward per la data di oggi)
    dummy_df = pd.DataFrame(columns=["commodity", "PIVA_UTENTE", "COD_OFFERTA", "TIPO_OFFERTA"])
    calc = FastSASCalculator(dummy_df)
    
    results = []
    
    for idx, row in df_crm.iterrows():
        name = row.get('Name', 'Sconosciuto')
        tipo_prezzo = row.get('Tipo_prezzo__c', '')
        if pd.isna(tipo_prezzo):
            continue
            
        tipo_offerta = 'Variabile' if tipo_prezzo == 'Indicizzato' else 'Fisso'
        
        # --- ENERGIA ELETTRICA ---
        if str(row.get('Tipo_servizio_EE__c')).strip().upper() == 'X' or str(row.get('Tipo_servizio_EE__c')).strip().upper() == 'SI':
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
                if idx < 5:
                    print(f"Debug Luce {name}: Quota Fissa={quota_fissa_luce}, Prezzo/Spread={prezzo_luce}")
                df_off = pd.DataFrame([off_e.riga()])
                try:
                    res_e = calc.calculate_sas(df_off, consumi={'F1': 2700}, potenza=3, regione='Lombardia')
                    sas_luce = res_e.iloc[0]['SAS']
                except Exception as e:
                    sas_luce = f"Errore: {e}"
            else:
                sas_luce = "Dati incompleti"
        else:
            sas_luce = "N/A"
            
        # --- GAS NATURALE ---
        if str(row.get('Tipo_servizio_GAS__c')).strip().upper() == 'X' or str(row.get('Tipo_servizio_GAS__c')).strip().upper() == 'SI':
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
                if idx < 5:
                    print(f"Debug Gas {name}: Quota Fissa={quota_fissa_gas}, Prezzo/Spread={prezzo_gas}")
                df_off = pd.DataFrame([off_g.riga()])
                try:
                    res_g = calc.calculate_sas(df_off, consumi={'F1': 1400}, potenza=3, regione='Lombardia')
                    sas_gas = res_g.iloc[0]['SAS']
                except Exception as e:
                    sas_gas = f"Errore: {e}"
            else:
                sas_gas = "Dati incompleti"
        else:
            sas_gas = "N/A"
            
        results.append({
            'Nome CRM': name,
            'Tipo': tipo_offerta,
            'SAS Luce Stimata (2700 kWh)': sas_luce,
            'SAS Gas Stimata (1400 Smc)': sas_gas
        })
        
    df_res = pd.DataFrame(results)
    out_path = BASE_DIR / "data" / "processed" / "TEST_CRM_risultati.csv"
    df_res.to_csv(out_path, index=False, sep=';', decimal=',')
    print(f"Analisi completata! Esportati {len(df_res)} prodotti.")
    print(f"File salvato in: {out_path}")
    print("\nPrimi 10 risultati:")
    print(df_res.head(10).to_markdown())

if __name__ == "__main__":
    run_test()
