import pandas as pd
import numpy as np
from engine.arera_tariffs import AreraTariffs

class SASCalculator:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.arera = AreraTariffs()

        
    def filter_offers(self, commodity='E', tipo_offerta='Fisso', tipo_cliente='Domestico', fasce=None, regione=None):
        filtered = self.df.copy()
        filtered = filtered[
            (filtered['commodity'] == commodity) & 
            (filtered['TIPO_OFFERTA'].str.contains(tipo_offerta, case=False, na=False)) &
            (filtered['TIPO_CLIENTE'].str.contains(tipo_cliente, case=False, na=False))
        ]
        
        if regione and regione != 'Tutte':
            # Mappa nomi regioni in codici ISTAT a 2 cifre
            istat_regioni = {
                'Piemonte': '01', 'Valle d\'Aosta': '02', 'Lombardia': '03', 'Trentino-Alto Adige': '04', 
                'Veneto': '05', 'Friuli-Venezia Giulia': '06', 'Liguria': '07', 'Emilia-Romagna': '08', 
                'Toscana': '09', 'Umbria': '10', 'Marche': '11', 'Lazio': '12', 'Abruzzo': '13', 
                'Molise': '14', 'Campania': '15', 'Puglia': '16', 'Basilicata': '17', 'Calabria': '18', 
                'Sicilia': '19', 'Sardegna': '20'
            }
            regione_code = istat_regioni.get(regione, '')
            if regione_code:
                # Per Elettricita' la rete è nazionale, non scartiamo offerte libere
                if commodity == 'E':
                    pass
                else:
                    is_national = filtered['REGIONE'].isna() | (filtered['REGIONE'] == 'None') | (filtered['REGIONE'] == '')
                    is_regional = filtered['REGIONE'].astype(str) == regione_code
                    filtered = filtered[is_national | is_regional]

        if fasce == 'Biorario':
            filtered = filtered[filtered['TIPOLOGIA_FASCE'].str.contains('F2|F3|biorario', na=False, regex=True)]
        elif fasce == 'Monorario':
            filtered = filtered[filtered['TIPOLOGIA_FASCE'].str.contains('monorario', na=False, regex=True, case=False)]
        elif fasce == 'Fasce':
            pass
            
        # Hardcode exclusion for offers hidden by ARERA portal
        filtered = filtered[~filtered['NOME_OFFERTA'].astype(str).str.contains('Sottocosto', case=False, na=False)]
        col_cod = 'CODICE_OFFERTA' if 'CODICE_OFFERTA' in filtered.columns else 'COD_OFFERTA'
        filtered = filtered[~filtered[col_cod].astype(str).str.contains('FIXDOM', na=False)]
        
        return filtered

    def calculate_sas(self, 
                      filtered_df: pd.DataFrame, 
                      consumi: dict, 
                      potenza: float, 
                      is_dual_fuel: bool = False,
                      is_domiciliazione: bool = False,
                      regione: str = 'Lombardia',
                      residente: bool = True):
        
        results = []
        
        F1 = consumi.get('F1', 0)
        F2 = consumi.get('F2', 0)
        F3 = consumi.get('F3', 0)
        F23 = F2 + F3
        TOT_CONS = F1 + F2 + F3
        
        # Oneri e Reti (Verranno calcolati dinamicamente nel loop o qui)
        ele_conf = self.arera.ELE['residente' if residente else 'non_residente']
        tot_reti_oneri_ele = (
            ele_conf['dist_fix'] + ele_conf['oneri_fix'] + 
            (ele_conf['trasp_pot'] + ele_conf['oneri_pot']) * potenza + 
            (ele_conf['trasp_vol'] + ele_conf['oneri_vol']) * TOT_CONS
        )
        accisa_ele = self.arera.get_ele_accisa_avg(residente, TOT_CONS) * TOT_CONS
        
        gas_fix_arera, gas_vol_arera = self.arera.get_gas_costi_regolati(regione, TOT_CONS)

        
        for idx, row in filtered_df.iterrows():
            costo_venditore_fix = 0.0
            costo_venditore_vol = 0.0
            commodity = str(row.get('commodity', 'E'))
            
            # 1. Componenti di Prezzo
            for c in range(1, 6):
                viste_fasce_c = set()
                # Se c'è una MACROAREA specificata ma noi non la supportiamo a fondo, la ignoriamo e applichiamo tutto
                # Il codice originale faceva un continue se pd.isna, che saltava tutte le righe senza macroarea
                # In realtà, se non c'è macroarea, si applica a livello nazionale, quindi NON DOBBIAMO fare continue!
                
                for i in range(1, 6):
                    fascia = str(row.get(f'COMP_IMP_{c}_INT_{i}_FASCIA')).strip()
                    prezzo_str = row.get(f'COMP_IMP_{c}_INT_{i}_PREZZO')
                    unita = str(row.get(f'COMP_IMP_{c}_INT_{i}_UNITA'))
                    
                    if pd.isna(prezzo_str) or unita == 'nan' or unita == 'None':
                        continue
                        
                    if commodity == 'E' and 'kWh' in unita and fascia in viste_fasce_c:
                        continue
                    viste_fasce_c.add(fascia)
                    
                    try:
                        prezzo = float(str(prezzo_str).replace(',', '.'))
                    except ValueError:
                        continue
                        
                    # Applica Perdite di Rete (maggiorazione 10% se non incluse) (SOLO ELE)
                    comprensivo = str(row.get('PREZZO_COMPRENSIVO_PERDITE_RETE')).strip().upper()
                    if 'kWh' in unita and comprensivo != 'SI':
                        prezzo = prezzo * 1.10
                        
                    if 'Anno' in unita:
                        costo_venditore_fix += prezzo
                    elif 'kW' in unita and 'kWh' not in unita:
                        costo_venditore_fix += prezzo * potenza
                    elif 'kWh' in unita:
                        if fascia == 'monorario/F1':
                            if str(row.get('TIPOLOGIA_FASCE')) in ['monorario/F1', '01', 'monorario']:
                                costo_venditore_vol += prezzo * TOT_CONS
                            else:
                                costo_venditore_vol += prezzo * F1
                        elif fascia == 'F2':
                            costo_venditore_vol += prezzo * F2
                        elif fascia == 'F3':
                            costo_venditore_vol += prezzo * F3
                        elif fascia == 'F2+F3':
                            costo_venditore_vol += prezzo * F23
                        else:
                            costo_venditore_vol += prezzo * TOT_CONS
                    elif 'Smc' in unita:
                        costo_venditore_vol += prezzo * TOT_CONS

            # 2. Sconti
            for s in range(1, 16):
                if pd.isna(row.get(f'SCONTO_{s}_NOME')):
                    continue
                validita = str(row.get(f'SCONTO_{s}_VALIDITA'))
                condizione = str(row.get(f'SCONTO_{s}_COND_APP')).strip()
                codice_comp = str(row.get(f'SCONTO_{s}_CODICE_COMP'))
                
                # Valutazione Condizioni (Filtri)
                # Se è uno sconto condizionato, verifichiamo se l'utente lo soddisfa
                applica_sconto = True
                if condizione == 'Altro':
                    # Assumiamo "Altro" includa Bonus Dual, se non is_dual_fuel scartiamo
                    if not is_dual_fuel:
                        applica_sconto = False
                elif condizione == 'Pagamento SDD':
                    if not is_domiciliazione:
                        applica_sconto = False
                
                if not applica_sconto:
                    continue

                if validita in ['Ingresso', 'entro 12 mesi', 'nan', '', 'None', 'Sempre']:
                    for p in range(1, 3):
                        s_tipo = str(row.get(f'SCONTO_{s}_PREZZO_{p}_TIPO'))
                        s_val = row.get(f'SCONTO_{s}_PREZZO_{p}_VAL')
                        s_unita = str(row.get(f'SCONTO_{s}_PREZZO_{p}_UNITA'))
                        
                        if pd.isna(s_val): continue
                        try:
                            sconto = float(str(s_val).replace(',', '.'))
                        except ValueError:
                            continue
                            
                        if 'Anno' in s_unita or s_tipo == 'Sconto fisso':
                            costo_venditore_fix -= sconto
                        elif 'kWh' in s_unita:
                            if codice_comp == 'F1':
                                costo_venditore_vol -= sconto * F1
                            elif codice_comp == 'F2':
                                costo_venditore_vol -= sconto * F2
                            elif codice_comp == 'F3':
                                costo_venditore_vol -= sconto * F3
                            elif codice_comp == 'F2+F3':
                                costo_venditore_vol -= sconto * F23
                            else:
                                costo_venditore_vol -= sconto * TOT_CONS
                        elif 'Smc' in s_unita:
                            costo_venditore_vol -= sconto * TOT_CONS

            if commodity == 'E':
                # 3. CDISPd (Sbilanciamento)
                cdispd_val = row.get('DISP_CdispD_VALORE')
                if not pd.isna(cdispd_val):
                    try:
                        cdispd = float(str(cdispd_val).replace(',', '.'))
                    except ValueError:
                        cdispd = ele_conf['cdispd']
                else:
                    cdispd = ele_conf['cdispd']
                    
                costo_venditore_vol += cdispd * TOT_CONS
                
                # FIX: Se l'offerta è variabile, aggiungiamo il PUN (stima 0.105 €/kWh) * eventuali perdite di rete
                if str(row.get('TIPO_OFFERTA')).strip().lower() == 'variabile':
                    pun = 0.105
                    comprensivo = str(row.get('PREZZO_COMPRENSIVO_PERDITE_RETE')).strip().upper()
                    if comprensivo != 'SI':
                        pun = pun * 1.10
                    costo_venditore_vol += pun * TOT_CONS
                
                # Totali ELE
                costo_venditore = costo_venditore_fix + costo_venditore_vol
                tot_netto = costo_venditore + tot_reti_oneri_ele + accisa_ele
                iva = tot_netto * 0.10  # 10% IVA su tutto per l'elettricità residenziale
                if not residente:
                    iva = tot_netto * 0.22 # Non residenti 22%
                tot_sas = tot_netto + iva
            else:
                # GAS
                # FIX: Se l'offerta è variabile, aggiungiamo il PSV (stima 0.35 €/Smc)
                if str(row.get('TIPO_OFFERTA')).strip().lower() == 'variabile':
                    costo_venditore_vol += 0.35 * TOT_CONS
                    
                costo_venditore = costo_venditore_fix + costo_venditore_vol
                
                # Oneri regolate + Accise + Addizionali ivati
                tot_arera_ivato = (gas_fix_arera * 1.22) + (gas_vol_arera * TOT_CONS * 1.10)
                
                # IVA 22% su base fissa, 10% su base variabile venditore
                tot_sas = (costo_venditore_fix * 1.22) + (costo_venditore_vol * 1.10) + tot_arera_ivato

            
            results.append({
                'PIVA_VENDITORE': row.get('PIVA_UTENTE'),
                'COD_OFFERTA': row.get('CODICE_OFFERTA', row.get('COD_OFFERTA')),
                'NOME_OFFERTA': row.get('NOME_OFFERTA'),
                'COND_Attivazione_LIMITANTE': str(row.get('COND_Attivazione_LIMITANTE')),
                'COND_Pluriennale_LIMITANTE': str(row.get('COND_Pluriennale_LIMITANTE')),
                'SPESA_MATERIA_PRIMA': round(costo_venditore, 2),
                'QUOTA_FISSA': round(costo_venditore_fix, 2),
                'PREZZO_UNITARIO': round(costo_venditore_vol / TOT_CONS, 4) if TOT_CONS > 0 else 0.0,
                'SAS': round(tot_sas, 2)
            })

        res_df = pd.DataFrame(results)
        if len(res_df) > 0:
            res_df = res_df.sort_values('SAS').reset_index(drop=True)
        return res_df

if __name__ == '__main__':
    df = pd.read_csv("data/storage/verifica_piatta_20260820.csv", dtype=str)
    calc = SASCalculator(df)
    
    # Simula scenario utente BASE (Niente dual fuel, niente domiciliazione)
    filtered = calc.filter_offers(fasce='Biorario')
    consumi = {'F1': 891, 'F2': 837, 'F3': 972}
    
    print("=== RANKING BASE (No Dual, No SDD) ===")
    res_base = calc.calculate_sas(filtered, consumi, potenza=3.0, is_dual_fuel=False, is_domiciliazione=False)
    print(res_base.head(10).to_string())
    
    print("\n=== RANKING CON DUAL FUEL ===")
    res_dual = calc.calculate_sas(filtered, consumi, potenza=3.0, is_dual_fuel=True, is_domiciliazione=False)
    print(res_dual.head(10).to_string())
