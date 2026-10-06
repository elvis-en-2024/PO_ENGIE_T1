import duckdb
import pandas as pd
import numpy as np
import sys
sys.path.append('.')
from engine.sas_calculator_fast import FastSASCalculator

conn = duckdb.connect()
df = conn.execute("SELECT * FROM 'data/processed/storico_2026_full.parquet' WHERE COD_OFFERTA IN ('000362ESFFL01XXL626U0D000000A000', '000788ESFFL01XXFWEBE06326X3X0000', '000155ESFFL07XXZZ03839Z260805E03', '026160ESFFL51XXLFIXA24VSMA130726')").df()
df = df.drop_duplicates(subset=['COD_OFFERTA'])

# Fix the calculator logic!
class FixedFastSASCalculator(FastSASCalculator):
    def calculate_sas(self, filtered_df: pd.DataFrame, consumi: dict, potenza: float, 
                      is_dual_fuel: bool = False, is_domiciliazione: bool = False, 
                      regione: str = 'Lombardia', residente: bool = True):
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
        
        # Keep track of seen fasce per offerta
        seen_fasce = {idx: set() for idx in range(len(df))}
        
        for c in range(1, 6):
            for i in range(1, 6):
                prezzo_col = f'COMP_IMP_{c}_INT_{i}_PREZZO'
                unita_col = f'COMP_IMP_{c}_INT_{i}_UNITA'
                fascia_col = f'COMP_IMP_{c}_INT_{i}_FASCIA'
                
                if prezzo_col not in df.columns: continue
                    
                prezzo_str = df[prezzo_col].astype(str).str.replace(',', '.')
                prezzo = pd.to_numeric(prezzo_str, errors='coerce').fillna(0).to_numpy()
                unita_s = df.get(unita_col, pd.Series(['']*len(df))).astype(str)
                fascia_s = df.get(fascia_col, pd.Series(['']*len(df))).astype(str)
                fascia = fascia_s.to_numpy()
                
                is_kwh = unita_s.str.contains('kWh').fillna(False).to_numpy()
                is_smc = unita_s.str.contains('Smc').fillna(False).to_numpy()
                is_kw = (unita_s.str.contains('kW').fillna(False).to_numpy()) & ~is_kwh
                
                perdite_mask = is_ee & is_kwh & (comprensivo != 'SI')
                prezzo = np.where(perdite_mask, prezzo * 1.10, prezzo)
                
                is_fix = ~is_kwh & ~is_smc & ~is_kw & (unita_s != 'nan') & (unita_s != 'None') & (unita_s != '')
                costo_fix += np.where(is_fix, prezzo, 0)
                
                p_val = potenza if potenza is not None else 0.0
                costo_fix += np.where(is_kw, prezzo * p_val, 0)
                
                tipologia_fasce = df.get('TIPOLOGIA_FASCE', pd.Series(['']*len(df))).astype(str).to_numpy()
                
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
                        elif f_val not in ['monorario/F1', 'F2', 'F3', 'F2+F3']:
                            costo_vol[idx] += prezzo[idx] * TOT_CONS
                            
        # Sconti
        for s in range(1, 4):
            s_val = pd.to_numeric(df.get(f'SCONTO_{s}_PREZZO_1_VAL', pd.Series([0]*len(df))), errors='coerce').fillna(0).to_numpy()
            s_tipo = df.get(f'SCONTO_{s}_PREZZO_1_TIPO', pd.Series(['']*len(df))).astype(str)
            s_cond = df.get(f'SCONTO_{s}_COND_APP', pd.Series(['']*len(df))).astype(str).str.lower()
            
            sconto_attivo = np.ones(len(df), dtype=bool)
            if not is_dual_fuel: sconto_attivo = sconto_attivo & ~s_cond.str.contains('dual')
            if not is_domiciliazione: sconto_attivo = sconto_attivo & ~(s_cond.str.contains('sdd') | s_cond.str.contains('domiciliazione') | s_cond.str.contains('rid') | s_cond.str.contains('conto corrente'))
            
            s_is_fisso = s_tipo.str.contains('Fisso', case=False) | s_tipo.str.contains('Una Tantum', case=False)
            costo_fix -= np.where(sconto_attivo & s_is_fisso, s_val, 0)
            
            s_unita = df.get(f'SCONTO_{s}_PREZZO_1_UNITA', pd.Series(['']*len(df))).astype(str)
            s_is_kwh = s_unita.str.contains('kWh')
            costo_vol -= np.where(sconto_attivo & s_is_kwh, s_val * TOT_CONS * 1.10, 0)

        ele_conf = self.arera.ELE['residente' if residente else 'non_residente']
        cdispd_col = df.get('DISP_CdispD_VALORE', pd.Series([ele_conf['cdispd']]*len(df))).astype(str).str.replace(',', '.')
        cdispd = pd.to_numeric(cdispd_col, errors='coerce').fillna(ele_conf['cdispd']).to_numpy()
        pun_base = 0.105
        pun_effettivo = np.where(comprensivo != 'SI', pun_base * 1.10, pun_base)
        
        # ADD CdispD ONLY IF DISP_CdispD == True OR MISSING!
        disp_cdispd = df.get('DISP_CdispD', pd.Series([True]*len(df))).fillna(True).astype(bool).to_numpy()
        costo_vol += np.where(is_ee & disp_cdispd, cdispd * TOT_CONS, 0)
        
        # APPLY DispBT!
        dispbt_fix = -10.7718 # 10.7718 in 2026? Wait, it used to be -18.xx
        disp_dispbt = df.get('DISP_DispBT', pd.Series([True]*len(df))).fillna(True).astype(bool).to_numpy()
        costo_fix += np.where(is_ee & disp_dispbt, dispbt_fix, 0)
        
        costo_vol += np.where(is_ee & tipo_offerta_variabile, pun_effettivo * TOT_CONS, 0)
        
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
        
        df['SPESA_MATERIA_PRIMA'] = np.round(costo_venditore, 2)
        df['QUOTA_FISSA'] = np.round(costo_fix, 2)
        df['PREZZO_UNITARIO'] = np.where(TOT_CONS > 0, np.round(costo_vol / TOT_CONS, 4), 0.0)
        df['SAS'] = np.round(sas_ele, 2)
        return df[['NOME_OFFERTA', 'SAS']]

calc = FixedFastSASCalculator(df)
res = calc.calculate_sas(df, {'F1': 891, 'F2': 837, 'F3': 972}, 3.0, is_domiciliazione=True)
print(res)
