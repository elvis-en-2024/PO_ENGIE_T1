# Allegato 1 — Codice Sorgente Moduli Core

> Da allegare a Claude browser insieme al prompt principale

---

## engine/sas_calculator_fast.py (PRODUZIONE — Calcolo SAS Vettorizzato)

```python
import pandas as pd
import numpy as np
from engine.arera_tariffs import AreraTariffs

class FastSASCalculator:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.arera = AreraTariffs()
        
    def filter_offers(self, commodity='E', tipo_offerta='Fisso', tipo_cliente='Domestico', fasce='Biorario', regione='Lombardia', provincia='015', comune='F205'):
        filtered = self.df
        filtered = filtered[
            (filtered['commodity'] == commodity) & 
            (filtered['TIPO_OFFERTA'].astype(str).str.contains(tipo_offerta, case=False, na=False)) &
            (filtered['TIPO_CLIENTE'].astype(str).str.contains(tipo_cliente, case=False, na=False))
        ]
        
        if regione and regione != 'Tutte' and 'REGIONE' in filtered.columns:
            istat_regioni = {
                'Piemonte': '01', 'Valle d\'Aosta': '02', 'Lombardia': '03', 'Trentino-Alto Adige': '04', 
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
            
        if commodity == 'E' and 'TIPOLOGIA_FASCE' in filtered.columns:
            if fasce == 'Biorario':
                filtered = filtered[filtered['TIPOLOGIA_FASCE'].astype(str).str.contains('F2|F3|biorario|Peak/OffPeak', na=False, regex=True, case=False)]
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
        
        # --- COMPONENTI DI PREZZO ---
        for c in range(1, 6):
            for i in range(1, 6):
                prezzo_col = f'COMP_IMP_{c}_INT_{i}_PREZZO'
                unita_col = f'COMP_IMP_{c}_INT_{i}_UNITA'
                fascia_col = f'COMP_IMP_{c}_INT_{i}_FASCIA'
                
                if prezzo_col not in df.columns:
                    continue
                    
                prezzo_str = df[prezzo_col].astype(str).str.replace(',', '.')
                prezzo_series = pd.to_numeric(prezzo_str, errors='coerce').fillna(0)
                prezzo = prezzo_series.to_numpy()
                
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
                is_f1_mono = (fascia == 'monorario/F1')
                is_vero_mono = np.isin(tipologia_fasce, ['monorario/F1', '01', 'monorario'])
                
                costo_vol += np.where(is_kwh & is_f1_mono & is_vero_mono, prezzo * TOT_CONS, 0)
                costo_vol += np.where(is_kwh & is_f1_mono & ~is_vero_mono, prezzo * F1, 0)
                costo_vol += np.where(is_kwh & (fascia == 'F2'), prezzo * F2, 0)
                costo_vol += np.where(is_kwh & (fascia == 'F3'), prezzo * F3, 0)
                costo_vol += np.where(is_kwh & (fascia == 'F2+F3'), prezzo * F23, 0)
                costo_vol += np.where(is_kwh & ~np.isin(fascia, ['monorario/F1', 'F2', 'F3', 'F2+F3']), prezzo * TOT_CONS, 0)
                
                is_smc = unita_s.str.contains('Smc').fillna(False).to_numpy()
                costo_vol += np.where(is_smc, prezzo * TOT_CONS, 0)
                
        # --- SCONTI ---
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
            applica_sconto &= ~((cond_app == 'Pagamento SDD') & (not is_domiciliazione))
            
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
                is_fisso = (s_tipo == 'Sconto fisso')
                costo_fix -= np.where(sconto_attivo & (is_anno | is_fisso), s_val, 0)
                
                is_kwh = s_unita_s.str.contains('kWh').fillna(False).to_numpy()
                costo_vol -= np.where(sconto_attivo & is_kwh & (codice_comp == 'F1'), s_val * F1, 0)
                costo_vol -= np.where(sconto_attivo & is_kwh & (codice_comp == 'F2'), s_val * F2, 0)
                costo_vol -= np.where(sconto_attivo & is_kwh & (codice_comp == 'F3'), s_val * F3, 0)
                costo_vol -= np.where(sconto_attivo & is_kwh & (codice_comp == 'F2+F3'), s_val * F23, 0)
                costo_vol -= np.where(sconto_attivo & is_kwh & ~np.isin(codice_comp, ['F1','F2','F3','F2+F3']), s_val * TOT_CONS, 0)
                
                is_smc = s_unita_s.str.contains('Smc').fillna(False).to_numpy()
                costo_vol -= np.where(sconto_attivo & is_smc, s_val * TOT_CONS, 0)

        # --- CDISPD E PUN/PSV ---
        ele_conf = self.arera.ELE['residente' if residente else 'non_residente']
        cdispd_col = df.get('DISP_CdispD_VALORE', pd.Series([ele_conf['cdispd']]*len(df))).astype(str).str.replace(',', '.')
        cdispd = pd.to_numeric(cdispd_col, errors='coerce').fillna(ele_conf['cdispd']).to_numpy()
        
        pun_base = 0.105
        pun_effettivo = np.where(comprensivo != 'SI', pun_base * 1.10, pun_base)
        
        costo_vol += np.where(is_ee, cdispd * TOT_CONS, 0)
        costo_vol += np.where(is_ee & tipo_offerta_variabile, pun_effettivo * TOT_CONS, 0)
        costo_vol += np.where(is_gas & tipo_offerta_variabile, 0.35 * TOT_CONS, 0)
        
        # --- TARIFFE ARERA ---
        ele_conf = self.arera.ELE['residente' if residente else 'non_residente']
        p_val = potenza if potenza is not None else 0.0
        tot_reti_oneri_ele = (
            ele_conf['dist_fix'] + ele_conf['oneri_fix'] + 
            (ele_conf['trasp_pot'] + ele_conf['oneri_pot']) * p_val + 
            (ele_conf['trasp_vol'] + ele_conf['oneri_vol']) * TOT_CONS
        )
        
        # --- CALCOLO FINALE ---
        costo_venditore = costo_fix + costo_vol
        
        # Accisa EE
        p_val = potenza if potenza is not None else 0.0
        if residente and p_val <= 3.0:
            accisa_ee = 0.0227 * np.maximum(0, TOT_CONS - 1800)
        else:
            accisa_ee = 0.0227 * TOT_CONS
            
        imponibile_ee = costo_venditore + tot_reti_oneri_ele + accisa_ee
        sas_ele = imponibile_ee * 1.10  # IVA 10%
        
        # Gas
        gas_fix_arera, gas_vol_arera = self.arera.get_gas_costi_regolati(regione, TOT_CONS, include_taxes=False)
        tot_arera_netto_gas = gas_fix_arera + (gas_vol_arera * TOT_CONS)
        
        # Accisa Gas a scaglioni
        acc_g_1 = 0.044 * np.minimum(120, TOT_CONS)
        acc_g_2 = 0.175 * np.maximum(0, np.minimum(480, TOT_CONS) - 120)
        acc_g_3 = 0.170 * np.maximum(0, np.minimum(1560, TOT_CONS) - 480)
        acc_g_4 = 0.186 * np.maximum(0, TOT_CONS - 1560)
        accisa_gas = acc_g_1 + acc_g_2 + acc_g_3 + acc_g_4
        
        addiz_rate = self.arera.GAS_ADDIZIONALE.get(regione, self.arera.GAS_ADDIZIONALE.get('DEFAULT', 0.019))
        addiz_gas = addiz_rate * TOT_CONS
        accisa_gas += addiz_gas
        
        imponibile_gas = costo_fix + costo_vol + tot_arera_netto_gas + accisa_gas
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
```

---

## engine/arera_tariffs.py (Tariffe ARERA)

```python
import json
import os
import logging
from datetime import datetime

class AreraTariffs:
    def __init__(self, config_path="data/config/arera_tariffs.json"):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configurazione ARERA non trovata in {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.metadata = data.get('metadata', {})
        self.ELE = data.get('ELE', {})
        self.GAS_FIX = data.get('GAS_FIX', {})
        self.GAS_VOL = data.get('GAS_VOL', {})
        self.GAS_ACCISE = data.get('GAS_ACCISE', {})
        self.GAS_ADDIZIONALE = data.get('GAS_ADDIZIONALE', {})
        self.GAS_ZONES = {
            '01': 'Nord Occidentale', '02': 'Nord Orientale', '03': 'Centrale',
            '04': 'Centro-Sud Orientale', '05': 'Centro-Sud Occidentale', '06': 'Meridionale'
        }
        self._validate_tariffs()

    def _validate_tariffs(self):
        now = datetime.now()
        current_quarter = f"Q{(now.month - 1) // 3 + 1}"
        current_year = now.year
        val_q = self.metadata.get('validity_quarter')
        val_y = self.metadata.get('validity_year')
        if val_q != current_quarter or val_y != current_year:
            grace_period = 5
            is_new_quarter_start = (now.month - 1) % 3 == 0 and now.day <= grace_period
            error_msg = (
                f"\n{'='*60}\n"
                f"ERRORE CRITICO: Tariffe ARERA obsolete!\n"
                f"Il sistema si aspetta le tariffe per {current_quarter} {current_year}, "
                f"ma il file è configurato per {val_q} {val_y}.\n"
                f"{'='*60}\n"
            )
            if is_new_quarter_start:
                logging.warning(error_msg.replace("ERRORE CRITICO", "WARNING (GRACE PERIOD)"))
            else:
                raise ValueError(error_msg)

        required_ele_keys = ['dist_fix', 'oneri_fix', 'trasp_pot', 'oneri_pot', 'trasp_vol', 'oneri_vol', 'cdispd']
        for tipo in ['residente', 'non_residente']:
            if tipo not in self.ELE:
                raise ValueError(f"Manca la configurazione ELE per {tipo}")
            for key in required_ele_keys:
                val = self.ELE[tipo].get(key)
                if val is None or val < 0:
                    raise ValueError(f"Parametro ELE '{key}' per {tipo} mancante o negativo: {val}")

    def get_gas_costi_regolati(self, regione, consumo_annuo, include_taxes=True):
        map_zone = {
            'Lombardia': ('Nord Occidentale', 'Nord'), 'Piemonte': ('Nord Occidentale', 'Nord'),
            'Liguria': ('Nord Occidentale', 'Nord'), 'Veneto': ('Nord Orientale', 'Nord'),
            'Emilia-Romagna': ('Nord Orientale', 'Nord'), 'Toscana': ('Centrale', 'Nord'),
            'Lazio': ('Centro-Sud Occidentale', 'Sud'), 'Campania': ('Centro-Sud Occidentale', 'Sud'),
            'Calabria': ('Meridionale', 'Sud'), 'Sicilia': ('Meridionale', 'Sud'),
            'Puglia': ('Centro-Sud Orientale', 'Sud'), 'Abruzzo': ('Centro-Sud Orientale', 'Sud'),
        }
        zona, territorio = map_zone.get(regione, ('Nord Occidentale', 'Nord'))
        fix_arera = self.GAS_FIX[zona]
        vol_arera = self.get_gas_vol_avg(zona, consumo_annuo)
        if include_taxes:
            accisa = self.get_gas_accisa_avg(territorio, consumo_annuo)
            addizionale = self.GAS_ADDIZIONALE.get(regione, self.GAS_ADDIZIONALE['DEFAULT'])
            return fix_arera, vol_arera + accisa + addizionale
        return fix_arera, vol_arera

    def get_gas_vol_avg(self, zona, consumo_annuo):
        tiers = self.GAS_VOL.get(zona, self.GAS_VOL['Nord Occidentale'])
        if isinstance(tiers, (float, int)): return tiers
        tot_vol = 0.0
        rimanente = consumo_annuo
        prev_limit = 0
        for limit, rate in tiers:
            scaglione = limit - prev_limit
            if rimanente > scaglione:
                tot_vol += scaglione * rate
                rimanente -= scaglione
                prev_limit = limit
            else:
                tot_vol += rimanente * rate
                break
        return tot_vol / consumo_annuo if consumo_annuo > 0 else 0.0

    def get_gas_accisa_avg(self, territorio, consumo_annuo):
        tiers = self.GAS_ACCISE.get(territorio, self.GAS_ACCISE['Nord'])
        tot_accisa = 0.0
        rimanente = consumo_annuo
        prev_limit = 0
        for limit, rate in tiers:
            scaglione = limit - prev_limit
            if rimanente > scaglione:
                tot_accisa += scaglione * rate
                rimanente -= scaglione
                prev_limit = limit
            else:
                tot_accisa += rimanente * rate
                break
        return tot_accisa / consumo_annuo if consumo_annuo > 0 else 0.0
```

---

## parse/flattener.py (XML → Record Flat — Transcodifica SII)

```python
# Dizionari di transcodifica del SII/Acquirente Unico (estratto)
DECODE_MAPS = {
    "TIPO_MERCATO": {"01": "Elettrico", "02": "Gas", "03": "Dual Fuel"},
    "TIPO_CLIENTE": {"01": "Domestico", "02": "Altri Usi", "03": "Condominio Uso Domestico (Gas)"},
    "TIPO_OFFERTA": {"01": "Fisso", "02": "Variabile", "03": "FLAT", "04": "Mista"},
    "TIPOLOGIA_FASCE": {
        "01": "monorario/F1", "02": "F2", "03": "F1, F2, F3",
        "91": "biorario (F1 / F2+F3)", "92": "biorario (F2 / F1+F3)", "93": "biorario (F3 / F1+F2)"
    },
    "UNITA_MISURA": {"01": "€/Anno", "02": "€/kW", "03": "€/kWh", "04": "€/Smc", "05": "€", "06": "Percentuale"},
    "FASCIA_COMPONENTE": {
        "01": "monorario/F1", "02": "F2", "03": "F3", "91": "F2+F3", "92": "F1+F3", "93": "F1+F2"
    },
    # ... + MACROAREA_COMP, LIMITANTE, TIPOLOGIA_SCONTO, CONDIZIONE_APP, CODICE_SCONTO, etc.
}

# flatten_offer() estrae da ogni nodo <offerta> XML:
# - Campi scalari: PIVA, COD_OFFERTA, NOME, DURATA, DATE, CONSUMI, URL, REGIONE, PROVINCIA, COMUNE
# - Flag booleani: ATT_CONTR (5 codici), MOD_ATTIVAZIONE (6), PAGAMENTO (5), DISP (14+), REGOLATA (9), COND (6), IDX (15+), SERVIZIO (7)
# - Array posizionali: COMP_IMP_1..5_INT_1..5 (prezzo, unità, fascia, validità) e SCONTO_1..15_PREZZO_1..2 (tipo, valore, unità)
```

---

## storage/scd2_manager.py (SCD Type 2 — Polars)

```python
# Logica chiave del merge SCD2:
# 1. Calcola offerta_id = PIVA_UTENTE + COD_OFFERTA + commodity
# 2. Calcola content_hash = SHA-256 di tutti i campi payload
# 3. Outer join con i record attivi correnti
# 4. Classifica:
#    - CHIUSI: presenti ieri, assenti oggi → is_current=False, valid_to=ieri
#    - NUOVI: assenti ieri, presenti oggi → is_current=True, valid_from=oggi
#    - INVARIATI: hash uguale → n_giorni_pubblicazione += 1
#    - MODIFICATI: hash diverso → chiude vecchio, apre nuovo
# 5. Salvataggio atomico: temp.parquet → rename
```

---

## download/downloader.py (Download XML Portale Offerte)

```python
# URL base: https://ilportaleofferte.it/portaleOfferte/resources/opendata/csv/offerteML
# Pattern file: PO_Offerte_{E|G|D}_MLIBERO_{YYYYMMDD}.xml
# Partizionamento: raw/{commodity}/{anno}/{mese}/
# Client: httpx con retry esponenziale (5 tentativi, 2-30s)
# Salvataggio: compressione gzip (.xml.gz)
# Skip se file già presente
```

---

## model/schema.py (Schema Dimensione)

```python
DIM_OFFERTA_SCHEMA = {
    "offerta_id": pl.Utf8,
    "sk_offerta_versione": pl.Utf8,
    "valid_from": pl.Date, "valid_to": pl.Date,
    "is_current": pl.Boolean,
    "content_hash": pl.Utf8,
    "n_giorni_pubblicazione": pl.Int32,
    "commodity": pl.Utf8,
    "codice_offerta": pl.Utf8, "piva_venditore": pl.Utf8,
    "nome_offerta": pl.Utf8,
    "tipo_mercato": pl.Utf8, "tipo_offerta": pl.Utf8,
    "prezzo_monorario": pl.Float64,
    "prezzo_f1": pl.Float64, "prezzo_f2": pl.Float64, "prezzo_f3": pl.Float64,
    "quota_fissa_annua": pl.Float64, "spread": pl.Float64,
    "sconto_nome": pl.Utf8, "sconto_valore": pl.Float64,
}
OPEN_END_DATE = "2099-12-31"
```
