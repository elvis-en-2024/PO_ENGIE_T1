# Problema di allineamento con il Portale Offerte

Questo file contiene il contesto per Claude per aiutarci a capire le discrepanze tra i risultati del nostro script e i risultati del Portale Offerte ARERA.

## Il Problema

1. L'utente ha selezionato "Prezzo Fisso" per una fornitura domestica di Elettricità a Milano (Provincia 015, Comune 015146), 2700 kWh/anno (3 kW).
2. L'interfaccia originale del nostro applicativo Streamlit e del Portale Offerte ufficiale prevede solo due scelte per il profilo: "A Fasce" o "Monorario".
3. **Discrepanza 1 (Offerte sporche classificate come Fisse):** Nel nostro ranking compaiono offerte con prezzi irrealistici per un Fisso (es. `MONO2026DOME129EE` a 412.49€ annui con P.Unitario 0.0055€/kWh). Queste offerte sono verosimilmente offerte a prezzo Variabile (PUN) che il fornitore ha caricato erroneamente con il flag `TIPO_OFFERTA="Fisso"` nell'XML, oppure nascondono costi in altre componenti non standard. Sul Portale Offerte queste offerte non sono visibili o sono filtrate.
4. **Discrepanza 2 (Gestione Multiorario/Biorario/Triorario):** Nel nostro ranking, scegliendo "A Fasce", compare al vertice `CasaFix1206260300` (SAS: 779.63€, Triorario: F1=F2=F3=0.12€/kWh). Tuttavia, sul Portale Offerte, l'utente segnala che al primo posto c'è `E.ON LuceClick biorariaVerde` (SAS: 783.52€, Biorario reale: F1=0.1105, F23=0.1076).
   Sembra che il Portale Offerte, quando si cerca "A Fasce", filtri via (o classifichi come Monorario) le offerte caricate come "Triorario" ma aventi F1=F2=F3 (le cosiddette false multiorarie). Abbiamo provato a implementare questa logica (escludendo chi ha prezzi uguali in F1, F2 e F3) e questo riporta E.ON al primo posto, ma l'utente segnala ancora anomalie.

## I file

Lo script dell'app (`app.py`) carica il parquet, imposta i pesi dei consumi standard ARERA per F1/F2/F3 (33%, 31%, 36%) per le offerte a fasce (indipendentemente che siano dichiarate biorarie o triorarie dal venditore) e chiama il motore `sas_calculator_fast.py` per calcolare il ranking.

### Top 5 Ranking (Discrepante):
1. MONO2026DOME129EE (022119ESFML01XXMONO2026DOME129EE) - SAS: 412.49
2. Luce sicura casa (027241ESFFL01XX20260601EE3FAFIXD) - SAS: 440.39
3. NeN Dieci Luce (029748ESFML01XX260805LD10X000000) - SAS: 760.03
4. E.ON LuceClick - Amico new (000362ESFML01XXL616U0DA00000A000) - SAS: 769.80
5. CasaFix1206260300 (039679ESFFL00XXCasaFix1206260300) - SAS: 779.63
6. E.ON Luce Insieme (000362DSFML01XXZA16U0D000000A000) - SAS: 781.24
7. E.ON LuceClick biorariaVerde (000362ESFFL01XXL626U0D000000A000) - SAS: 783.06


## Codice Sorgente

### app.py
```python
import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import os
from engine.sas_calculator_fast import FastSASCalculator

st.set_page_config(page_title="Portale Offerte - Simulatore", layout="wide", page_icon="⚡", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .po-header { background-color: #792A65; color: white; padding: 20px; font-size: 24px; font-weight: bold; border-radius: 5px; margin-bottom: 20px; }
    .po-step { color: #792A65; font-weight: bold; font-size: 18px; margin-bottom: 10px; border-bottom: 2px solid #792A65; padding-bottom: 5px; }
    .stButton>button { background-color: #792A65; color: white; border-radius: 5px; font-weight: bold; width: 100%; }
    .stButton>button:hover { background-color: #5c1e4d; border-color: #5c1e4d; }
</style>
""", unsafe_allow_html=True)

def highlight_engie(row):
    is_engie = 'ENGIE' in str(row.get('Player', '')).upper()
    return ['background-color: #e6f2ff' if is_engie else '' for _ in row]

@st.cache_data(show_spinner=False)
def load_data(data_rif_str):
    import pandas as pd
    import datetime as dt
    path = 'data/processed/storico_2026_full.parquet'
    
    df = pd.read_parquet(path)
    
    # OPTIMIZATION: cast string columns to category to prevent OOM
    for col in ['commodity', 'TIPO_OFFERTA', 'TIPO_CLIENTE', 'TIPOLOGIA_FASCE', 'REGIONE', 'PROVINCIA', 'COMUNE', 'PIVA_VENDITORE', 'NOME_VENDITORE', 'PIVA_UTENTE']:
        if col in df.columns:
            df[col] = df[col].astype('category')
    
    col_piva = 'PIVA_UTENTE' if 'PIVA_UTENTE' in df.columns else 'PIVA_VENDITORE'
    col_cod = 'CODICE_OFFERTA' if 'CODICE_OFFERTA' in df.columns else 'COD_OFFERTA'
    
    # Filter by date
    if 'DATA_FINE' in df.columns:
        dt_fine = df['DATA_FINE'].astype(str).str.split('_').str[0]
        df['DATA_FINE'] = pd.to_datetime(dt_fine, format='%d/%m/%Y', errors='coerce')
        df = df[df['DATA_FINE'] >= pd.Timestamp.today()]
        
    # Convert data_rif_str to datetime
    data_rif = pd.to_datetime(data_rif_str, format='%Y-%m-%d')
    if 'DATA_INIZIO' in df.columns:
        # Extract first part of DATA_INIZIO
        dt_inizio = df['DATA_INIZIO'].astype(str).str.split('_').str[0]
        dt_inizio = pd.to_datetime(dt_inizio, format='%d/%m/%Y', errors='coerce')
        df = df[dt_inizio <= data_rif]
        
    # Deduplicate
    subset = [col_piva, col_cod]
    if 'commodity' in df.columns:
        subset.append('commodity')
        
    if 'DATA_RILEVAZIONE' in df.columns:
        df = df.sort_values(['DATA_RILEVAZIONE', col_cod], ascending=[False, True])
        
    df = df.drop_duplicates(subset=subset)
    
    piva_map = {
        '09633951000': 'Enel Energia', '06655971007': 'Enel Energia', '11475730154': 'ENGIE',
        '11956540153': 'A2A Energia', '02863660359': 'E.ON', '02319210213': 'Iren',
        '04584980962': 'Fastweb', '12874490159': 'Plenitude', '02031070994': 'Acea',
        '04179130963': 'Octopus'
    }
    
    df['NOME_VENDITORE'] = df[col_piva].map(piva_map).fillna(df[col_piva])
    df['Player'] = df['NOME_VENDITORE']
    return df
def highlight_engie(row):
    color = '#d4f0ff' if 'ENGIE' in str(row.get('Player', '')) else ''
    return [f'background-color: {color}' for _ in row]


st.sidebar.markdown("### Impostazioni")
filtro_data = st.sidebar.date_input("Data di validita offerte", dt.date.today())
data_rif_str = filtro_data.strftime("%Y-%m-%d")

with st.spinner("Caricamento offerte in corso..."):
    df_attive = load_data(data_rif_str)

if 'step' not in st.session_state:

    st.session_state.step = 1

if st.session_state.step == 1:
    st.markdown('<div class="po-header">Confronto tariffe e prezzi luce e gas</div>', unsafe_allow_html=True)
    st.markdown('<div class="po-step">Step 1: Scegli la fornitura</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔌 Energia Elettrica"):
            st.session_state.commodity = 'E'
            st.session_state.step = 2
            st.rerun()
    with c2:
        if st.button("🔥 Gas Naturale"):
            st.session_state.commodity = 'G'
            st.session_state.step = 2
            st.rerun()

elif st.session_state.step == 2:
    st.markdown('<div class="po-header">Dettagli della fornitura</div>', unsafe_allow_html=True)
    st.markdown('<div class="po-step">Step 2: Inserisci i tuoi parametri</div>', unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    if st.session_state.commodity == 'E':
        with col_a:
            st.session_state.regione = st.selectbox("Ambito Territoriale (Regione)", ["Lombardia", "Lazio", "Campania", "Sicilia", "Piemonte", "Veneto"])
            st.session_state.residenza = st.radio("Residenza", ["Residente", "Non Residente"])
            st.session_state.potenza = st.selectbox("Potenza Impegnata (kW)", [1.5, 3.0, 4.5, 6.0, 10.0], index=1)
        with col_b:
            st.session_state.profilo = st.radio("Profilo di Consumo", ["A Fasce (Biorario/Multiorario)", "Monorario"])
            st.session_state.tipo_offerta = st.selectbox("Tipo di Prezzo", ["Fisso", "Variabile"], index=0)
    else:
        with col_a:
            st.session_state.regione = st.selectbox("Ambito Territoriale (Regione)", ["Lombardia", "Lazio", "Campania", "Sicilia", "Piemonte", "Veneto"])
            st.session_state.tipo_offerta = st.selectbox("Tipo di Prezzo", ["Fisso", "Variabile"], index=0)
        with col_b:
            st.session_state.uso_gas = st.multiselect("Utilizzo del Gas", ["Cottura", "Acqua Calda", "Riscaldamento"], default=["Cottura", "Acqua Calda", "Riscaldamento"])
            
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Avanti ➡️ (Calcola Ranking)"):
        st.session_state.step = 3
        st.rerun()

elif st.session_state.step == 3:
    st.markdown('<div class="po-header">Risultati della Ricerca (Ranking)</div>', unsafe_allow_html=True)
    st.info(f"Dati storici riferiti alla data: **{filtro_data.strftime('%d/%m/%Y')}**")
    
    calc = FastSASCalculator(df_attive)

    def render_html_cards(df, commodity):
        html_content = f"""<div style="height: 650px; overflow-y: auto; padding-right: 15px;">"""
        for idx, row in df.iterrows():
            is_engie = 'ENGIE' in str(row['Player']).upper()
            border_left_color = "#0099cc" if commodity == 'E' else "#ff9900"
            bg_color = "#e6f2ff" if is_engie else "#ffffff"
            
            sas_val = f"{row['SAS']:.2f}".replace('.', ',')
            sas_mese = f"{(row['SAS']/12):.2f}".replace('.', ',')
            prezzo_unitario = f"{row['PREZZO_UNITARIO']:.4f}".replace('.', ',')
            quota_fissa = f"{row['QUOTA_FISSA']:.2f}".replace('.', ',')
            unita = "kWh" if commodity == 'E' else "Smc"
            
            card_html = f"""
            <div style="background-color: {bg_color}; border: 1px solid #e0e0e0; border-left: 6px solid {border_left_color}; border-radius: 8px; padding: 20px; margin-bottom: 15px; display: flex; flex-direction: row; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="flex: 0 0 60px; font-size: 28px; font-weight: bold; color: #792A65; text-align: center;">#{idx}</div>
                <div style="flex: 2; padding-left: 20px;">
                    <div style="font-size: 14px; color: #555; text-transform: uppercase; font-weight: 700; letter-spacing: 1px;">{row['Player']}</div>
                    <div style="font-size: 20px; font-weight: bold; color: #222; margin-top: 5px;">{row['NOME_OFFERTA']}</div>
                    <div style="font-size: 12px; color: #888; margin-top: 4px;">Codice: {row['COD_OFFERTA']}</div>
                    <div style="font-size: 13px; color: #444; margin-top: 10px; background-color: rgba(0,0,0,0.03); padding: 5px; border-radius: 4px; display: inline-block;">
                        Quota Fissa: <b>{quota_fissa} €/anno</b> | Prezzo Energia: <b>{prezzo_unitario} €/{unita}</b>
                    </div>
                </div>
                <div style="flex: 1; text-align: right; border-left: 1px solid #eaeaea; padding-left: 20px;">
                    <div style="font-size: 13px; color: #666;">Spesa stimata in un anno<br><span style="font-size: 11px;">(escluse imposte e tasse)</span></div>
                    <div style="font-size: 32px; font-weight: 800; color: #333; margin-top: 5px;">{sas_val} €</div>
                    <div style="font-size: 14px; color: #777; font-style: italic;">(circa {sas_mese} € / mese)</div>
                </div>
            </div>
            """
            html_content += card_html
        html_content += "</div>"
        st.markdown(html_content, unsafe_allow_html=True)
    
    if st.session_state.commodity == 'E':
        is_residente = st.session_state.get('residenza', 'Residente') == 'Residente'
        potenza = st.session_state.get('potenza', 3.0)
        fasce = 'Monorario' if st.session_state.get('profilo', '') == 'Monorario' else 'A Fasce'
        regione = st.session_state.get('regione', 'Lombardia')
        tipo_offerta = st.session_state.get('tipo_offerta', 'Fisso')
        
        filtered = calc.filter_offers(commodity='E', fasce=fasce, tipo_offerta=tipo_offerta, regione=regione, provincia='015', comune='F205')
        
        # DEFAULT PO FILTERS
        filtered = filtered[filtered['COND_Attivazione_LIMITANTE'].isna() | (filtered['COND_Attivazione_LIMITANTE'] == '') | (filtered['COND_Attivazione_LIMITANTE'] == 'None') | filtered['COND_Attivazione_LIMITANTE'].astype(str).str.contains('non', case=False, na=False)]
        filtered = filtered[~filtered['NOME_OFFERTA'].astype(str).str.contains('Sottocosto', case=False, na=False)]
        
        t1, t2, t3, t4 = st.tabs(["Media ARERA (2700 kWh)", "Media ENGIE (2100 kWh)", "Slot Custom 1", "Slot Custom 2"])
        with t3: c_custom1 = st.number_input("Consumo Slot 1 (kWh)", value=3500, step=100)
        with t4: c_custom2 = st.number_input("Consumo Slot 2 (kWh)", value=4500, step=100)

        def display_ele(c_tot):
            if fasce == 'Monorario':
                cons = {'F1': c_tot}
            else:
                cons = {
                    'F1': c_tot * (891 / 2700),
                    'F2': c_tot * (837 / 2700),
                    'F3': c_tot * (972 / 2700)
                }
            res = calc.calculate_sas(filtered, cons, potenza=potenza, residente=is_residente, is_domiciliazione=False)
            if not res.empty:
                res = res[res['PREZZO_UNITARIO'] > 0] # Filter out garbage
                res_display = res[['COD_OFFERTA', 'NOME_OFFERTA', 'PREZZO_UNITARIO', 'QUOTA_FISSA', 'SAS']].copy()
                # Map Player
                res_display['Player'] = res['PIVA_VENDITORE'].map(dict(zip(df_attive['PIVA_UTENTE'] if 'PIVA_UTENTE' in df_attive.columns else df_attive['PIVA_VENDITORE'], df_attive['NOME_VENDITORE']))).fillna(res['PIVA_VENDITORE'])
                res_display = res_display[['Player', 'NOME_OFFERTA', 'COD_OFFERTA', 'PREZZO_UNITARIO', 'QUOTA_FISSA', 'SAS']].head(30)
                res_display.index = np.arange(1, len(res_display)+1)
                
                view_mode = st.radio("Vista", ["Simulazione Portale Offerte", "Tabella Dati"], horizontal=True, label_visibility="collapsed", key=f"view_ele_{c_tot}")
                
                if view_mode == "Simulazione Portale Offerte":
                    render_html_cards(res_display, 'E')
                else:
                    styled = res_display.style.apply(highlight_engie, axis=1).format({
                        'PREZZO_UNITARIO': '{:.4f} €/kWh', 'QUOTA_FISSA': '{:.2f} €', 'SAS': '{:.2f} €'
                    })
                    st.dataframe(styled, use_container_width=True, height=650)
            else:
                st.warning("Nessuna offerta trovata.")
                
        with t1: display_ele(2700)
        with t2: display_ele(2100)
        with t3: display_ele(c_custom1)
        with t4: display_ele(c_custom2)
            
    elif st.session_state.commodity == 'G':
        regione = st.session_state.get('regione', 'Lombardia')
        tipo_offerta = st.session_state.get('tipo_offerta', 'Fisso')
        
        filtered = calc.filter_offers(commodity='G', tipo_offerta=tipo_offerta, regione=regione, provincia='015', comune='F205')
        
        # DEFAULT PO FILTERS
        filtered = filtered[filtered['COND_Attivazione_LIMITANTE'].isna() | (filtered['COND_Attivazione_LIMITANTE'] == '') | (filtered['COND_Attivazione_LIMITANTE'] == 'None') | filtered['COND_Attivazione_LIMITANTE'].astype(str).str.contains('non', case=False, na=False)]
        filtered = filtered[~filtered['NOME_OFFERTA'].astype(str).str.contains('Sottocosto', case=False, na=False)]
        
        t1, t2, t3, t4 = st.tabs(["Media ARERA (1400 Smc)", "Media ENGIE (651 Smc)", "Slot Custom 1", "Slot Custom 2"])
        with t3: c_custom1 = st.number_input("Consumo Slot 1 (Smc)", value=1000, step=50)
        with t4: c_custom2 = st.number_input("Consumo Slot 2 (Smc)", value=2500, step=50)
        
        def display_gas(c_tot):
            cons = {'F1': c_tot}
            res = calc.calculate_sas(filtered, cons, potenza=0, residente=True, is_domiciliazione=False)
            if not res.empty:
                res = res[res['PREZZO_UNITARIO'] > 0]
                res_display = res[['COD_OFFERTA', 'NOME_OFFERTA', 'PREZZO_UNITARIO', 'QUOTA_FISSA', 'SAS']].copy()
                res_display['Player'] = res['PIVA_VENDITORE'].map(dict(zip(df_attive['PIVA_UTENTE'] if 'PIVA_UTENTE' in df_attive.columns else df_attive['PIVA_VENDITORE'], df_attive['NOME_VENDITORE']))).fillna(res['PIVA_VENDITORE'])
                res_display = res_display[['Player', 'NOME_OFFERTA', 'COD_OFFERTA', 'PREZZO_UNITARIO', 'QUOTA_FISSA', 'SAS']].head(30)
                res_display.index = np.arange(1, len(res_display)+1)
                
                view_mode = st.radio("Vista", ["Simulazione Portale Offerte", "Tabella Dati"], horizontal=True, label_visibility="collapsed", key=f"view_gas_{c_tot}")
                
                if view_mode == "Simulazione Portale Offerte":
                    render_html_cards(res_display, 'G')
                else:
                    styled = res_display.style.apply(highlight_engie, axis=1).format({
                        'PREZZO_UNITARIO': '{:.4f} €/Smc', 'QUOTA_FISSA': '{:.2f} €', 'SAS': '{:.2f} €'
                    })
                    st.dataframe(styled, use_container_width=True, height=800)
            else:
                st.warning("Nessuna offerta trovata.")
                
        with t1: display_gas(1400)
        with t2: display_gas(651)
        with t3: display_gas(c_custom1)
        with t4: display_gas(c_custom2)

```

### sas_calculator_fast.py
```python
import pandas as pd
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
            (filtered['TIPO_CLIENTE'].astype(str).str.contains(rf'\b{tipo_cliente}\b', case=False, regex=True, na=False))
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
            
        # Fasce (Solo per Elettricita)
        if commodity == 'E' and 'TIPOLOGIA_FASCE' in filtered.columns:
            if fasce == 'A Fasce':
                # Biorario/Triorario. Exclude fake monoraria where F1==F2==F3 in COMP_IMP_2
                filtered = filtered[~filtered['TIPOLOGIA_FASCE'].astype(str).str.contains('monorario', na=False, regex=True, case=False)]
                if 'COMP_IMP_2_INT_1_PREZZO' in filtered.columns:
                    # Filter out fake multiorario (if F1 == F2 == F3)
                    is_fake = (filtered['COMP_IMP_2_INT_1_PREZZO'].astype(float) == filtered['COMP_IMP_2_INT_2_PREZZO'].astype(float)) & (filtered['COMP_IMP_2_INT_2_PREZZO'].astype(float) == filtered['COMP_IMP_2_INT_3_PREZZO'].astype(float))
                    filtered = filtered[~is_fake]
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
                is_fisso = (s_tipo == 'Sconto fisso') | pd.Series(s_tipo).str.contains('Una Tantum', case=False).fillna(False).to_numpy()
                costo_fix -= np.where(sconto_attivo & (is_anno | is_fisso), s_val, 0)
                
                is_kwh = s_unita_s.str.contains('kWh').fillna(False).to_numpy()
                costo_vol -= np.where(sconto_attivo & is_kwh & (codice_comp == 'F1'), s_val * F1 , 0)
                costo_vol -= np.where(sconto_attivo & is_kwh & (codice_comp == 'F2'), s_val * F2 , 0)
                costo_vol -= np.where(sconto_attivo & is_kwh & (codice_comp == 'F3'), s_val * F3 , 0)
                costo_vol -= np.where(sconto_attivo & is_kwh & (codice_comp == 'F2+F3'), s_val * F23 , 0)
                costo_vol -= np.where(sconto_attivo & is_kwh & ~np.isin(codice_comp, ['F1','F2','F3','F2+F3']), s_val * TOT_CONS , 0)
                
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

```
