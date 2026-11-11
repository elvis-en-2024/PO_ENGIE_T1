import pandas as pd
import numpy as np
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(BASE_DIR.as_posix())

from engine.offerta_simulata import NuovaOfferta
from engine.sas_calculator_fast import FastSASCalculator

from freezegun import freeze_time

@freeze_time("2026-09-15")
def run_multi_test_fast():
    crm_path = r"C:\Users\XP6566\OneDrive - ENGIE\Documenti\PO_scraping_2026\TEST CRM\Product2-08_10_2026.csv"
    print(f"Caricamento file CRM da: {crm_path}")
    df_crm = pd.read_csv(crm_path)
    
    dummy_df = pd.DataFrame(columns=["commodity", "PIVA_UTENTE", "COD_OFFERTA", "TIPO_OFFERTA"])
    calc = FastSASCalculator(dummy_df)
    
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
    
    # 1. Costruiamo due DataFrame (Luce e Gas) con TUTTE le offerte valide del CRM
    offerte_luce_rows = []
    offerte_gas_rows = []
    nomi_luce = []
    nomi_gas = []
    
    # Mappatura per riassemblare i risultati alla fine
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
                riga_e['ID_CRM'] = idx # per il join
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
                riga_g['ID_CRM'] = idx # per il join
                offerte_gas_rows.append(riga_g)
                
    df_luce_all = pd.DataFrame(offerte_luce_rows)
    df_gas_all = pd.DataFrame(offerte_gas_rows)
    
    print(f"Preparate {len(df_luce_all)} offerte Luce e {len(df_gas_all)} offerte Gas per il calcolo vettoriale in blocco.")
    
    # 2. Calcoliamo i profili LUCE (8 chiamate vettoriali)
    if not df_luce_all.empty:
        for res, pot, cons in profili_ee:
            res_str = "Res" if res else "NonRes"
            col_name = f"ELE_{res_str}_{pot}kW_{cons}kWh"
            try:
                res_e = calc.calculate_sas(df_luce_all, consumi={'F1': cons}, potenza=pot, residente=res, regione='Lombardia')
                for i, row_idx in enumerate(df_luce_all['ID_CRM']):
                    results_dict[row_idx][col_name] = res_e.iloc[i]['SAS']
            except Exception as e:
                print(f"Errore profilo luce {col_name}: {e}")
                
    # 3. Calcoliamo i profili GAS (36 chiamate vettoriali)
    if not df_gas_all.empty:
        for reg, macro in ambiti:
            for cons in consumi_gas:
                col_name = f"GAS_{reg}_{cons}smc"
                try:
                    res_g = calc.calculate_sas(df_gas_all, consumi={'F1': cons}, potenza=3, regione=reg)
                    for i, row_idx in enumerate(df_gas_all['ID_CRM']):
                        results_dict[row_idx][col_name] = res_g.iloc[i]['SAS']
                except Exception as e:
                    print(f"Errore profilo gas {col_name}: {e}")
                    
    # Assemblaggio finale
    df_res = pd.DataFrame(list(results_dict.values()))
    out_path = BASE_DIR / "data" / "processed" / "TEST_CRM_multi_risultati_Settembre.csv"
    df_res.to_csv(out_path, index=False, sep=';', decimal=',')
    print(f"File salvato vettorialmente in un lampo in: {out_path}")

if __name__ == "__main__":
    run_multi_test_fast()
