import sys

new_content = '''import pandas as pd
import numpy as np
from engine.arera_tariffs import AreraTariffs

class FastSASCalculator:
    def __init__(self, df: pd.DataFrame, arera: AreraTariffs = None,
                 tariffs_path: str = None):
        """
        arera:         istanza gia costruita (usata dai test / da chi orchestra).
        tariffs_path:  path alternativo al JSON tariffe.
        Se entrambi None -> comportamento storico (path di default).
        """
        self.df = df.copy()
        if arera is not None:
            self.arera = arera
        elif tariffs_path is not None:
            self.arera = AreraTariffs(tariffs_path)
        else:
            self.arera = AreraTariffs()
        
    def filter_offers(self, commodity='E', tipo_offerta='Fisso', tipo_cliente='Domestico', fasce='Biorario', regione='Lombardia', provincia='015', comune='F205'):
        filtered = self.df
        
        # Commodity & Cliente
        filtered = filtered[
            (filtered['commodity'] == commodity) & 
            (filtered['TIPO_OFFERTA'].astype(str).str.contains(tipo_offerta, case=False, na=False)) &
            (filtered['TIPO_CLIENTE'].astype(str).str.contains(rf'\\b{tipo_cliente}\\b', case=False, regex=True, na=False))
        ]
        
        if regione and regione != 'Tutte' and 'REGIONE' in filtered.columns:
            istat_regioni = {
                'Piemonte': '01', 'Valle d\\'Aosta': '02', 'Lombardia': '03', 'Trentino-Alto Adige': '04', 
                'Veneto': '05', 'Friuli-Venezia Giulia': '06', 'Liguria': '07', 'Emilia-Romagna': '08', 
                'Toscana': '09', 'Umbria': '10', 'Marche': '11', 'Lazio': '12', 'Abruzzo': '13', 
                'Molise': '14', 'Campania': '15', 'Puglia': '16', 'Basilicata': '17', 'Calabria': '18', 
                'Sicilia': '19', 'Sardegna': '20'
            }
            regione_code = istat_regioni.get(regione, '03')
            is_national = filtered['REGIONE'].isna() | (filtered['REGIONE'] == '')
            is_regional = filtered['REGIONE'].astype(str) == regione_code
            filtered = filtered[is_national | is_regional]
            
        if provincia and 'PROVINCIA' in filtered.columns:
            is_national_prov = filtered['PROVINCIA'].isna() | (filtered['PROVINCIA'] == '') | (filtered['PROVINCIA'] == 'None')
            is_prov = filtered['PROVINCIA'].astype(str) == provincia
            filtered = filtered[is_national_prov | is_prov]
            
        if comune and 'COMUNE' in filtered.columns:
            is_national_com = filtered['COMUNE'].isna() | (filtered['COMUNE'] == '') | (filtered['COMUNE'] == 'None')
            is_com = filtered['COMUNE'].astype(str) == comune
            filtered = filtered[is_national_com | is_com]
            
        # Fasce (Solo per Elettricita)
        if commodity == 'E' and 'TIPOLOGIA_FASCE' in filtered.columns:
            if fasce == 'Biorario':
                # Biorario in PO means "Not Monorario" (Fasce).
                filtered = filtered[~filtered['TIPOLOGIA_FASCE'].astype(str).str.contains('monorario', na=False, regex=True, case=False) & filtered['TIPOLOGIA_FASCE'].astype(str).str.strip().astype(bool)]
            elif fasce == 'Monorario':
                filtered = filtered[filtered['TIPOLOGIA_FASCE'].astype(str).str.contains('monorario', na=False, regex=True, case=False)]
        
        filtered = filtered[~filtered['NOME_OFFERTA'].astype(str).str.contains('Sottocosto', case=False, na=False)]
        return filtered

    def calculate_sas(self, filtered_df: pd.DataFrame, consumi: dict, potenza: float, 
                      is_dual_fuel: bool = False, is_domiciliazione: bool = False, 
                      regione: str = 'Lombardia', residente: bool = True):
        
        if filtered_df.empty:
            return pd.DataFrame()
            
        df = filtered_df.copy()
        
        F1 = consumi.get('F1', 0)
        F2 = consumi.get('F2', 0)
        F3 = consumi.get('F3', 0)
        F23 = F2 + F3
        TOT_CONS = F1 + F2 + F3
        
        costo_fix = np.zeros(len(df))
        costo_vol = np.zeros(len(df))
        
        is_ee = (df['commodity'] == 'E').to_numpy()
        is_gas = (df['commodity'] == 'G').to_numpy()
        comprensivo = df.get('PREZZO_COMPRENSIVO_PERDITE_RETE', pd.Series(['SI']*len(df))).astype(str).str.strip().str.upper().to_numpy()
        tipo_offerta_variabile = df.get('TIPO_OFFERTA', pd.Series(['Fisso']*len(df))).astype(str).str.strip().str.lower().str.contains('variabile').to_numpy()
        
        seen_fasce = {idx: set() for idx in range(len(df))}
        tipologia_fasce = df.get('TIPOLOGIA_FASCE', pd.Series(['']*len(df))).astype(str).to_numpy()
        
        for c in range(1, 6):
            for i in range(1, 6):
                prezzo_col = f'COMP_IMP_{c}_INT_{i}_PREZZO'
                unita_col = f'COMP_IMP_{c}_INT_{i}_UNITA'
                fascia_col = f'COMP_IMP_{c}_INT_{i}_FASCIA'
                
                if prezzo_col not in df.columns:
                    continue
                    
                prezzo_str = df[prezzo_col].astype(str).str.replace(',', '.')
                prezzo = pd.to_numeric(prezzo_str, errors='coerce').fillna(0).to_numpy()
                unita_s = df.get(unita_col, pd.Series(['']*len(df))).astype(str)
                fascia_s = df.get(fascia_col, pd.Series(['']*len(df))).astype(str)
                fascia = fascia_s.to_numpy()
                
                is_kwh = unita_s.str.contains('kWh').fillna(False).to_numpy()
                is_smc = unita_s.str.contains('Smc').fillna(False).to_numpy()
                is_kw = (unita_s.str.contains('kW').fillna(False).to_numpy()) & ~is_kwh
                is_percent = unita_s.str.contains('%|ercentuale', case=False, regex=True).fillna(False).to_numpy()
                
                perdite_mask = is_ee & is_kwh & (comprensivo != 'SI')
                prezzo = np.where(perdite_mask, prezzo * 1.10, prezzo)
                
                is_fix = ~is_kwh & ~is_smc & ~is_kw & ~is_percent & (unita_s != 'nan') & (unita_s != 'None') & (unita_s != '')
                costo_fix += np.where(is_fix, prezzo, 0)
                
                p_val = potenza if potenza is not None else 0.0
                costo_fix += np.where(is_kw, prezzo * p_val, 0)
                
                for idx in range(len(df)):
                    if prezzo[idx] == 0: continue
                    if is_kwh[idx]:
                        f_name = f"C{c}_" + str(fascia[idx])
                        if f_name in seen_fasce[idx]: continue
                        seen_fasce[idx].add(f_name)
                        
                        f_val = fascia[idx]
                        is_vero_mono = tipologia_fasce[idx] in ['monorario/F1', '01', 'monorario']
                        
                        if f_val == 'monorario/F1':
                            if is_vero_mono: costo_vol[idx] += prezzo[idx] * TOT_CONS
                            else: costo_vol[idx] += prezzo[idx] * F1
                        elif f_val == 'F2': costo_vol[idx] += prezzo[idx] * F2
                        elif f_val == 'F3': costo_vol[idx] += prezzo[idx] * F3
                        elif f_val == 'F2+F3': costo_vol[idx] += prezzo[idx] * F23
                        elif f_val == 'F1+F2': costo_vol[idx] += prezzo[idx] * (F1 + F2)
                        elif f_val == 'F1+F3': costo_vol[idx] += prezzo[idx] * (F1 + F3)
                        elif f_val not in ['monorario/F1', 'F2', 'F3', 'F2+F3', 'F1+F2', 'F1+F3']:
                            costo_vol[idx] += prezzo[idx] * TOT_CONS
                            
                    elif is_smc[idx]:
                        f_name = f"C{c}_SMC"
                        if f_name in seen_fasce[idx]: continue
                        seen_fasce[idx].add(f_name)
                        costo_vol[idx] += prezzo[idx] * TOT_CONS
                
        for s in range(1, 16):
            nome_sconto_col = f'SCONTO_{s}_NOME'
            if nome_sconto_col not in df.columns:
                continue
                
            has_sconto = df[nome_sconto_col].notna().to_numpy()
            cond_app = df.get(f'SCONTO_{s}_COND_APP', pd.Series(['']*len(df))).astype(str).str.strip().to_numpy()
            codice_comp = df.get(f'SCONTO_{s}_CODICE_COMP', pd.Series(['']*len(df))).astype(str).to_numpy()
            validita = df.get(f'SCONTO_{s}_VALIDITA', pd.Series(['']*len(df))).astype(str).to_numpy()
            
            applica_sconto = has_sconto.copy()
            applica_sconto &= ~((cond_app == 'Altro') & (not is_dual_fuel))
            
            cond_sdd_mask = df.get(f'SCONTO_{s}_COND_APP', pd.Series(['']*len(df))).astype(str).str.lower().str.contains('sdd|domiciliazione|rid|conto corrente', na=False).to_numpy()
            applica_sconto &= ~(cond_sdd_mask & (not is_domiciliazione))
            
            val_ok = np.isin(validita, ['Ingresso', 'entro 12 mesi', 'nan', '', 'None', 'Sempre'])
            applica_sconto &= val_ok
            
            for p in range(1, 3):
                s_tipo_col = f'SCONTO_{s}_PREZZO_{p}_TIPO'
                s_val_col = f'SCONTO_{s}_PREZZO_{p}_VAL'
                s_unita_col = f'SCONTO_{s}_PREZZO_{p}_UNITA'
                
                if s_val_col not in df.columns: continue
                
                s_val_str = df[s_val_col].astype(str).str.replace(',', '.')
                s_val = pd.to_numeric(s_val_str, errors='coerce').fillna(0).to_numpy()
                
                s_unita_s = df.get(s_unita_col, pd.Series(['']*len(df))).astype(str)
                s_tipo = df.get(s_tipo_col, pd.Series(['']*len(df))).astype(str).to_numpy()
                
                sconto_attivo = applica_sconto & (s_val > 0)
                
                is_anno = s_unita_s.str.contains('Anno').fillna(False).to_numpy()
                is_fisso = (s_tipo == 'Sconto fisso') | s_tipo.str.contains('Una Tantum', case=False)
                costo_fix -= np.where(sconto_attivo & (is_anno | is_fisso), s_val, 0)
                
                is_kwh = s_unita_s.str.contains('kWh').fillna(False).to_numpy()
                costo_vol -= np.where(sconto_attivo & is_kwh & (codice_comp == 'F1'), s_val * F1 * 1.10, 0)
                costo_vol -= np.where(sconto_attivo & is_kwh & (codice_comp == 'F2'), s_val * F2 * 1.10, 0)
                costo_vol -= np.where(sconto_attivo & is_kwh & (codice_comp == 'F3'), s_val * F3 * 1.10, 0)
                costo_vol -= np.where(sconto_attivo & is_kwh & (codice_comp == 'F2+F3'), s_val * F23 * 1.10, 0)
                costo_vol -= np.where(sconto_attivo & is_kwh & ~np.isin(codice_comp, ['F1','F2','F3','F2+F3']), s_val * TOT_CONS * 1.10, 0)
                
                is_smc = s_unita_s.str.contains('Smc').fillna(False).to_numpy()
                costo_vol -= np.where(sconto_attivo & is_smc, s_val * TOT_CONS, 0)

        ele_conf = self.arera.ELE['residente' if residente else 'non_residente']
        
        cdispd_col = df.get('DISP_CdispD_VALORE', pd.Series([ele_conf['cdispd']]*len(df))).astype(str).str.replace(',', '.')
        cdispd = pd.to_numeric(cdispd_col, errors='coerce').fillna(ele_conf['cdispd']).to_numpy()
        
        pun_base = 0.105
        pun_effettivo = np.where(comprensivo != 'SI', pun_base * 1.10, pun_base)
        
        disp_cdispd = df.get('DISP_CdispD', pd.Series([True]*len(df))).fillna(True).astype(bool).to_numpy()
        costo_vol += np.where(is_ee & disp_cdispd, cdispd * TOT_CONS, 0)
        
        dispbt_fix = -10.7718
        disp_dispbt = df.get('DISP_DispBT', pd.Series([True]*len(df))).fillna(True).astype(bool).to_numpy()
        costo_fix += np.where(is_ee & disp_dispbt, dispbt_fix, 0)
        
        costo_vol += np.where(is_ee & tipo_offerta_variabile, pun_effettivo * TOT_CONS, 0)
        costo_vol += np.where(is_gas & tipo_offerta_variabile, 0.35 * TOT_CONS, 0)
        
        p_val = potenza if potenza is not None else 0.0
        tot_reti_oneri_ele = (
            ele_conf['dist_fix'] + ele_conf['oneri_fix'] + 
            (ele_conf['trasp_pot'] + ele_conf['oneri_pot']) * p_val + 
            (ele_conf['trasp_vol'] + ele_conf['oneri_vol']) * TOT_CONS
        )
        
        costo_venditore = costo_fix + costo_vol
        
        if residente and p_val <= 3.0:
            accisa_ee = 0.0227 * np.maximum(0, TOT_CONS - 1800)
        else:
            accisa_ee = 0.0227 * TOT_CONS
            
        imponibile_ee = costo_venditore + tot_reti_oneri_ele + accisa_ee
        sas_ele = imponibile_ee * 1.10
        
        gas_fix_arera, gas_vol_arera = self.arera.get_gas_costi_regolati(regione, TOT_CONS, include_taxes=True, strict=False)
        tot_arera_gas = gas_fix_arera + (gas_vol_arera * TOT_CONS)
        imponibile_gas = costo_fix + costo_vol + tot_arera_gas
        
        quota_10 = np.minimum(480, TOT_CONS) / np.maximum(1, TOT_CONS)
        quota_22 = np.maximum(0, TOT_CONS - 480) / np.maximum(1, TOT_CONS)
        iva_gas = (imponibile_gas * quota_10 * 0.10) + (imponibile_gas * quota_22 * 0.22)
        sas_gas = imponibile_gas + iva_gas
        
        sas_finale = np.where(is_ee, sas_ele, sas_gas)
        
        df['SPESA_MATERIA_PRIMA'] = np.round(costo_venditore, 2)
        df['QUOTA_FISSA'] = np.round(costo_fix, 2)
        df['PREZZO_UNITARIO'] = np.where(TOT_CONS > 0, np.round(costo_vol / TOT_CONS, 4), 0.0)
        df['SAS'] = np.round(sas_finale, 2)
        
        col_piva = 'PIVA_UTENTE' if 'PIVA_UTENTE' in df.columns else 'PIVA_VENDITORE'
        col_cod = 'CODICE_OFFERTA' if 'CODICE_OFFERTA' in df.columns else 'COD_OFFERTA'
        
        out_cols = [col_piva, col_cod, 'NOME_OFFERTA', 'SPESA_MATERIA_PRIMA', 'QUOTA_FISSA', 'PREZZO_UNITARIO', 'SAS']
        
        if 'COND_Attivazione_LIMITANTE' in df.columns: out_cols.append('COND_Attivazione_LIMITANTE')
        if 'COND_Pluriennale_LIMITANTE' in df.columns: out_cols.append('COND_Pluriennale_LIMITANTE')
            
        res_df = df[out_cols].copy()
        res_df = res_df.rename(columns={col_piva: 'PIVA_VENDITORE', col_cod: 'COD_OFFERTA'})
        
        if len(res_df) > 0:
            res_df = res_df.sort_values('SAS').reset_index(drop=True)
            
        return res_df
'''
with open('engine/sas_calculator_fast.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
print("File sas_calculator_fast.py rewritten!")
