"""Simulatore del Portale Offerte: ricerca, ranking, dettaglio offerta e
posizionamento di una nuova offerta.

    streamlit run app.py
"""
import datetime as dt

import pandas as pd
import streamlit as st

from engine import component_matrix as cm
from engine import forward
from engine import offerta_simulata as osim
from engine.sas_calculator_fast import FastSASCalculator, ISTAT_REGIONI
from ui import portale as ui

st.set_page_config(page_title="Portale Offerte · Simulatore", layout="wide", page_icon="⚡",
                   initial_sidebar_state="collapsed")
st.markdown(ui.CSS, unsafe_allow_html=True)

PIVA_NOMI = {
    '09633951000': 'Enel Energia', '06655971007': 'Enel Energia', '11475730154': 'ENGIE',
    '11956540153': 'A2A Energia', '02863660359': 'E.ON', '02319210213': 'Iren',
    '04584980962': 'Fastweb', '12874490159': 'Plenitude', '02031070994': 'Acea',
    '04179130963': 'Octopus', osim.PIVA_SIMULATA: 'LA TUA NUOVA OFFERTA',
}
FASCE_PROFILO = {'F1': 891 / 2700, 'F2': 837 / 2700, 'F3': 972 / 2700}   # profilo tipo ARERA
CONSUMO_STD = {'E': 2700, 'G': 1400}
USI_GAS = ["Cottura cibi", "Acqua calda", "Riscaldamento"]
PER_PAGINA = 20

DEFAULT = dict(commodity='E', regione='Lombardia', tipo='Fisso', residente=True, potenza=3.0,
               fasce='Monoraria', consumo=2700, f1=891, f2=837, f3=972, usi=list(USI_GAS),
               domiciliazione=False, bolletta_web=False)

ss = st.session_state
ss.setdefault('pagina', 'tipo')
ss.setdefault('p', dict(DEFAULT))
P = ss.p


def vai(pagina: str, **extra):
    ss.pagina = pagina
    for k, v in extra.items():
        ss[k] = v


# ---------------------------------------------------------------- dati e calcolo

@st.cache_data(show_spinner=False, ttl=3600)  # ttl: rilegge dopo update_daily
def load_data(data_rif_str):
    import re
    from storage import daily_store

    # come il Portale: le offerte del file dell'ultima rilevazione fino alla data scelta
    df = daily_store.leggi_finestra(dt.date.fromisoformat(data_rif_str), giorni=1)
    if df.empty:
        return df
    if 'DATA_INIZIO' in df.columns:
        inizio = pd.to_datetime(df['DATA_INIZIO'].astype(str).str.split('_').str[0],
                                format='%d/%m/%Y', errors='coerce')
        df = df[inizio <= pd.Timestamp(data_rif_str)]

    def dal_sito(url):
        if pd.isna(url) or not str(url).strip():
            return None
        s = re.sub(r'^(https?://)?(www\.)?', '', str(url).lower().strip()).split('/')[0].split('.')[0]
        return 'EstEnergy' if s == 'estenergy' else s.title()

    sito = df['URL_SITO_VENDITORE'].apply(dal_sito) if 'URL_SITO_VENDITORE' in df.columns else None
    df['NOME_VENDITORE'] = df['PIVA_UTENTE'].map(PIVA_NOMI).fillna(sito).fillna(df['PIVA_UTENTE'])
    return df


@st.cache_resource(show_spinner=False, ttl=3600)
def calcolatore(data_rif_str):
    return FastSASCalculator(load_data(data_rif_str))


def consumi(p: dict) -> dict:
    if p['commodity'] == 'G':
        return {'F1': p['consumo']}
    if p['fasce'] == 'Monoraria':
        return {'F1': p['consumo']}
    return {'F1': p['f1'], 'F2': p['f2'], 'F3': p['f3']}


def kw_calcolo(p: dict) -> dict:
    luce = p['commodity'] == 'E'
    return dict(consumi=consumi(p), potenza=p['potenza'] if luce else 0,
                regione=p['regione'], residente=p['residente'] if luce else True,
                is_domiciliazione=p['domiciliazione'], is_bolletta_web=p['bolletta_web'])


def colonne_prezzo(p: dict) -> list[str]:
    """Colonne del prezzo dichiarato dall'offerta per la ricerca corrente."""
    u = 'kWh' if p['commodity'] == 'E' else 'Smc'
    base = 'Spread' if p['tipo'] == 'Variabile' else 'Prezzo'
    fasce = ['F1', 'F2', 'F3'] if p['commodity'] == 'E' and p['fasce'] == 'Fasce' else ['']
    cols = [f"{base} {f} €/{u}".replace("  ", " ") for f in fasce]
    if p['tipo'] == 'Variabile':
        cols += [f"Prezzo stimato {f} €/{u}".replace("  ", " ") for f in fasce]
    return cols


def aggiungi_prezzi(res: pd.DataFrame, offerte: pd.DataFrame, p: dict, calc) -> pd.DataFrame:
    """Prezzo effettivo dell'offerta: somma delle sue componenti €/kWh o €/Smc per
    fascia (scaglione del consumo annuo, al netto di perdite e imposte). Per le
    variabili è lo spread, più il prezzo stimato con l'indice (forward x (1+lambda))."""
    long = cm.build_long(offerte, consumo_annuo=sum(consumi(p).values()))
    pm = cm.price_matrix(offerte, long=long).fillna(0.0)
    idx = {k: i for i, k in zip(offerte.index, zip(offerte['PIVA_UTENTE'], offerte['COD_OFFERTA']))}
    pos = [idx.get(k) for k in zip(res['PIVA_VENDITORE'], res['COD_OFFERTA'])]
    righe = pm.reindex(pos).to_numpy()
    # quota fissa e quota potenza dichiarate (escluse le una tantum)
    ricorrenti = long[long['macroarea_cod'].astype(str) != '05']
    for col, kind in (('Quota fissa €/anno', cm.KIND_FISSO), ('Quota potenza €/kW/anno', cm.KIND_KW)):
        somma = ricorrenti[ricorrenti['kind'] == kind].groupby('row')['prezzo'].sum()
        res[col] = somma.reindex(pos).fillna(0.0).to_numpy()
    if p['commodity'] == 'G' or not res['Quota potenza €/kW/anno'].any():
        res = res.drop(columns='Quota potenza €/kW/anno')
    cols = colonne_prezzo(p)
    fasce = len(cols) // (2 if p['tipo'] == 'Variabile' else 1)
    valori = [righe[:, 0]] if fasce == 1 else [righe[:, 0], righe[:, 1], righe[:, 2]]
    for c, v in zip(cols, valori):
        res[c] = v
    if p['tipo'] == 'Variabile':
        par = calc.arera.PARAMETRI
        perdite = 1 + (calc.parametri.get('E') or {}).get('lambda', par['perdite_rete_ee'])
        if p['commodity'] == 'G':
            indici = [sum(w * x for w, x in zip(forward.profilo_gas(p['regione'], calc.oggi),
                                                 calc.forward['gas_mesi'])) if calc.forward else par['psv_stima']]
        elif calc.forward:
            fw = calc.forward['ee']
            indici = ([fw['F0'] * perdite] if fasce == 1
                      else [fw['F1'] * perdite, fw['F23'] * perdite, fw['F23'] * perdite])
        else:
            indici = [par['pun_stima']] * fasce
        for c, v, i in zip(cols[fasce:], valori, indici):
            res[c] = v + i
    return res


@st.cache_data(show_spinner=False, ttl=3600, max_entries=30)
def cerca(data_rif_str: str, chiave: tuple, escludi_false: bool, solo_singole: bool):
    """Offerte della ricerca, ranking e informazioni per tabella e dettaglio."""
    p = dict(chiave)
    calc = calcolatore(data_rif_str)
    totale = sum(consumi(p).values())
    if p['commodity'] == 'E':
        f = calc.filter_offers(commodity='E', tipo_offerta=p['tipo'], tipo_cliente='Domestico',
                               fasce='Monorario' if p['fasce'] == 'Monoraria' else 'A Fasce',
                               regione=p['regione'], provincia=None, comune=None, consumo_annuo=totale,
                               falsa_multioraria='escludi' if escludi_false else 'mantieni',
                               solo_offerte_singole=solo_singole, potenza=p['potenza'],
                               residente=p['residente'])
    else:
        f = calc.filter_offers(commodity='G', tipo_offerta=p['tipo'], regione=p['regione'],
                               provincia=None, comune=None, consumo_annuo=totale,
                               solo_offerte_singole=solo_singole)
    esclusioni = dict(calc.diagnostica_esclusioni)
    scartate = calc.offerte_scartate
    # le offerte con condizioni di attivazione limitanti restano: il Portale le mostra
    # (verificato il 02/10/2026); si possono escludere con il filtro dell'elenco
    if f.empty:
        return pd.DataFrame(), f, esclusioni, scartate

    res = calc.calculate_sas(f, **kw_calcolo(p))
    info = f.drop_duplicates(['PIVA_UTENTE', 'COD_OFFERTA']).set_index(['PIVA_UTENTE', 'COD_OFFERTA'])
    righe = [info.loc[(a, b)] for a, b in zip(res['PIVA_VENDITORE'], res['COD_OFFERTA'])]
    res['Venditore'] = [r['NOME_VENDITORE'] for r in righe]
    res['Tipo'] = [str(r.get('TIPO_OFFERTA', '')) for r in righe]
    res['Sconti dichiarati'] = ["\n".join(ui.sconti(r)) for r in righe]
    res['Note'] = ["\n".join(ui.note(r)) for r in righe]
    res['Limitante'] = [str(r.get('COND_Attivazione_LIMITANTE', '')).startswith('Si') for r in righe]
    res = aggiungi_prezzi(res, f, p, calc)
    res.insert(0, 'Pos', range(1, len(res) + 1))
    return res, f, esclusioni, scartate


def riepilogo(p: dict) -> dict:
    luce = p['commodity'] == 'E'
    r = {'Commodity': 'Energia elettrica' if luce else 'Gas', 'Regione': p['regione'],
         'Tipo di offerta': p['tipo']}
    if luce:
        r.update({'Prezzo': p['fasce'], 'Potenza': f"{ui.euro(p['potenza'], 1)} kW",
                  'Consumo annuo': f"{ui.euro(sum(consumi(p).values()), 0)} kWh",
                  'Cliente': 'Domestico ' + ('residente' if p['residente'] else 'non residente')})
    else:
        r.update({'Consumo annuo': f"{ui.euro(p['consumo'], 0)} Smc", 'Usi': ', '.join(p['usi'])})
    extra = [n for n, v in (('domiciliazione', p['domiciliazione']), ('bolletta web', p['bolletta_web'])) if v]
    r['Sconti condizionati'] = ', '.join(extra) if extra else 'esclusi'
    return r


# ---------------------------------------------------------------- impostazioni

st.sidebar.markdown("### Impostazioni")
filtro_data = st.sidebar.date_input("Data di riferimento delle offerte", dt.date.today())
data_rif_str = filtro_data.strftime("%Y-%m-%d")
escludi_false = st.sidebar.checkbox("Escludi false multiorarie (F1=F2=F3)", value=False)
solo_singole = st.sidebar.checkbox("Escludi offerte solo Dual Fuel", value=True)

with st.spinner("Caricamento offerte in corso..."):
    df_attive = load_data(data_rif_str)
if df_attive.empty:
    st.error(f"Nessuna offerta nello storico fino al {filtro_data:%d/%m/%Y}. Eseguire scripts/update_daily.py.")
    st.stop()
ultima = pd.to_datetime(df_attive['DATA_RILEVAZIONE']).max().date()
st.sidebar.caption(f"Ultima rilevazione disponibile: {ultima:%d/%m/%Y}")
if (filtro_data - ultima).days > 2:
    st.sidebar.warning(f"I dati sono di {(filtro_data - ultima).days} giorni prima della data scelta: "
                       "aggiornare lo storico (scripts/update_daily.py).")


def intestazione(pagina: str, titolo: str, passo: int | None = None):
    st.markdown(ui.testata(pagina), unsafe_allow_html=True)
    c1, c2, c3 = st.columns([5, 1.3, 1.6])
    c1.markdown(f'<div class="po-title">{ui.esc(titolo)}</div>', unsafe_allow_html=True)
    c2.button("Confronta", key="nav_conf", on_click=vai, args=('tipo',), use_container_width=True)
    c3.button("Simula offerta", key="nav_sim", on_click=vai, args=('simula',),
              type="primary", use_container_width=True)
    if passo:
        st.markdown(ui.stepper(passo), unsafe_allow_html=True)


def riga(domanda: str):
    """Riga del form: domanda a sinistra, controllo a destra (come il Portale)."""
    a, b = st.columns([2, 3], vertical_alignment="center")
    a.markdown(ui.domanda(domanda), unsafe_allow_html=True)
    return b


def scelta(domanda: str, opzioni: list, campo: str, etichette=None):
    """Pulsanti a scelta singola: il valore resta in P anche cambiando pagina."""
    etichette = etichette or {o: str(o) for o in opzioni}
    v = riga(domanda).segmented_control(domanda, opzioni, default=P[campo], key=f"w_{campo}",
                                        format_func=lambda o: etichette[o], label_visibility="collapsed")
    if v is not None:
        P[campo] = v
    st.markdown('<div class="po-sep"></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- pagina 1: tipo di offerta

def pagina_tipo():
    intestazione("Confronta", "Confronta le offerte", 1)
    st.markdown(f'<div class="po-banner"><b>Simulatore interno ENGIE.</b> Le offerte sono quelle pubblicate '
                f'negli open data del Portale Offerte (ultima rilevazione {ultima:%d/%m/%Y}). La spesa annua '
                f'è calcolata con le Regole per il calcolo della spesa del Portale.</div>', unsafe_allow_html=True)
    with st.container(border=True):
        prima = P['commodity']
        scelta("Che tipo di offerte vuoi confrontare?", ['E', 'G'], 'commodity',
               {'E': 'Energia elettrica', 'G': 'Gas'})
        if P['commodity'] != prima:  # consumo standard della nuova commodity
            P.update(consumo=CONSUMO_STD[P['commodity']], f1=DEFAULT['f1'], f2=DEFAULT['f2'], f3=DEFAULT['f3'])
        reg = list(ISTAT_REGIONI)
        P['regione'] = riga("In quale regione si trova la fornitura?").selectbox(
            "Regione", reg, index=reg.index(P['regione']), key="w_regione", label_visibility="collapsed")
        st.markdown('<div class="po-sep"></div>', unsafe_allow_html=True)
        riga("Per quale tipologia di cliente?").markdown("**Casa** (cliente domestico)")
        st.markdown('<div class="po-sep"></div>', unsafe_allow_html=True)
        scelta("Ti interessa un'offerta a prezzo fisso o variabile?", ['Fisso', 'Variabile'], 'tipo',
               {'Fisso': 'Prezzo fisso', 'Variabile': 'Prezzo variabile'})
        if P['commodity'] == 'E':
            scelta("La fornitura è nell'abitazione di residenza?", [True, False], 'residente',
                   {True: 'Sì', False: 'No'})
    _, b = st.columns([4, 1])
    b.button("Avanti →", type="primary", use_container_width=True, on_click=vai, args=('caratteristiche',))


# ---------------------------------------------------------------- pagina 2: caratteristiche

def pagina_caratteristiche():
    intestazione("Confronta", "Confronta le offerte", 2)
    luce = P['commodity'] == 'E'
    with st.container(border=True):
        if luce:
            pot = [1.5, 3.0, 4.5, 6.0, 10.0]
            P['potenza'] = riga("Che livello di potenza desideri?").selectbox(
                "Potenza", pot, index=pot.index(P['potenza']), key="w_potenza",
                format_func=lambda v: f"{ui.euro(v, 1)} kW", label_visibility="collapsed")
            st.markdown('<div class="po-sep"></div>', unsafe_allow_html=True)
            scelta("Sei interessato a un prezzo per fasce orarie oppure a un prezzo monorario?",
                   ['Fasce', 'Monoraria'], 'fasce')
            nuovo = riga("Qual è il tuo consumo annuo (kWh)?").number_input(
                "Consumo", min_value=100, max_value=100000, step=100, value=int(P['consumo']),
                key="w_consumo", label_visibility="collapsed")
            if nuovo != P['consumo']:
                P['consumo'] = nuovo
                # ripartizione per fasce del profilo tipo ARERA
                P['f1'], P['f2'] = round(nuovo * FASCE_PROFILO['F1']), round(nuovo * FASCE_PROFILO['F2'])
                P['f3'] = nuovo - P['f1'] - P['f2']
            if P['fasce'] == 'Fasce':
                c = riga("Ripartizione per fasce (kWh)")
                f1, f2, f3 = c.columns(3)
                P['f1'] = f1.number_input("F1", 0, 100000, int(P['f1']), key="w_f1")
                P['f2'] = f2.number_input("F2", 0, 100000, int(P['f2']), key="w_f2")
                P['f3'] = f3.number_input("F3", 0, 100000, int(P['f3']), key="w_f3")
        else:
            usi = riga("Per quali usi utilizzi il gas?").pills(
                "Usi", USI_GAS, selection_mode="multi", default=P['usi'], key="w_usi",
                label_visibility="collapsed")
            P['usi'] = usi or P['usi']
            st.markdown('<div class="po-sep"></div>', unsafe_allow_html=True)
            P['consumo'] = riga("Qual è il tuo consumo annuo (Smc)?").number_input(
                "Consumo", min_value=50, max_value=50000, step=50, value=int(P['consumo']),
                key="w_consumo_g", label_visibility="collapsed")
        st.markdown('<div class="po-sep"></div>', unsafe_allow_html=True)
        scelta("Includere gli sconti condizionati alla domiciliazione bancaria?", [False, True],
               'domiciliazione', {False: 'No', True: 'Sì'})
        scelta("Includere gli sconti condizionati alla bolletta web?", [False, True],
               'bolletta_web', {False: 'No', True: 'Sì'})
    a, _, b = st.columns([1, 3, 1])
    a.button("← Indietro", use_container_width=True, on_click=vai, args=('tipo',))
    b.button("Confronta →", type="primary", use_container_width=True, on_click=vai,
             args=('elenco',), kwargs=dict(pag_risultati=1))


def chiave_ricerca() -> tuple:
    campi = ('commodity', 'regione', 'tipo', 'residente', 'potenza', 'fasce', 'consumo',
             'f1', 'f2', 'f3', 'domiciliazione', 'bolletta_web')
    return tuple((k, P[k]) for k in campi)


# ---------------------------------------------------------------- pagina 3: elenco

def schede(res: pd.DataFrame, unita: str, chiave: str):
    for _, r in res.iterrows():
        sim = r['PIVA_VENDITORE'] == osim.PIVA_SIMULATA
        engie = 'ENGIE' in str(r['Venditore']).upper()
        tipo = 'sim' if sim else ('engie' if engie else 'x')
        with st.container(key=f"card_{tipo}_{chiave}_{r['Pos']}"):
            a, b, c = st.columns([0.7, 3.3, 1.7], vertical_alignment="center")
            tag = ([r['Tipo']] + (["sconti"] if r.get('Sconti dichiarati') else [])
                   + (["attivazione limitante"] if r.get('Limitante') is True else []))
            pos, testo, prezzo = ui.scheda(r['Pos'], r['Venditore'], r['NOME_OFFERTA'], r['COD_OFFERTA'],
                                           r['SAS'], f"prezzo medio {ui.euro(r['PREZZO_UNITARIO'], 4)} €/{unita}",
                                           tag)
            a.markdown(pos, unsafe_allow_html=True)
            b.markdown(testo, unsafe_allow_html=True)
            c.markdown(prezzo, unsafe_allow_html=True)
            if not sim:
                c.button("Vai al dettaglio →", key=f"det_{chiave}_{r['Pos']}", use_container_width=True,
                         on_click=vai, args=('dettaglio',),
                         kwargs=dict(sel=(r['PIVA_VENDITORE'], r['COD_OFFERTA'])))


def tabella(res: pd.DataFrame, unita: str, nome_file: str):
    cols = ['Pos', 'Venditore', 'NOME_OFFERTA', 'COD_OFFERTA', 'Tipo', 'SAS', 'VENDITA', 'SCONTI',
            'RETE', 'ONERI', 'IMPOSTE', 'IVA', 'SCONTI_NO_IVA', 'QUOTA_FISSA', 'PREZZO_UNITARIO',
            'Sconti dichiarati', 'Note']
    t = res[[c for c in cols if c in res.columns]]
    money = st.column_config.NumberColumn
    st.dataframe(
        t, hide_index=True, use_container_width=True, height=620,
        column_config={
            'NOME_OFFERTA': 'Offerta', 'COD_OFFERTA': 'Codice',
            'SAS': money('Spesa annua €', format="%.2f"), 'VENDITA': money('Vendita €', format="%.2f"),
            'SCONTI': money('Sconti €', format="%.2f"), 'RETE': money('Rete €', format="%.2f"),
            'ONERI': money('Oneri €', format="%.2f"), 'IMPOSTE': money('Imposte €', format="%.2f"),
            'IVA': money('IVA €', format="%.2f"), 'SCONTI_NO_IVA': money('Sconti no IVA €', format="%.2f"),
            'QUOTA_FISSA': money('Quota fissa €/anno', format="%.2f"),
            'PREZZO_UNITARIO': money(f'Prezzo medio €/{unita}', format="%.4f"),
            'Sconti dichiarati': st.column_config.TextColumn('Sconti dichiarati', width="large"),
            'Note': st.column_config.TextColumn('Note utili', width="large"),
        })
    st.download_button("Scarica CSV", t.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig'),
                       file_name=nome_file, mime="text/csv")


def pagina_elenco():
    intestazione("Confronta", "Confronta le offerte", 3)
    a, b, _, c = st.columns([1.4, 1, 1.6, 1.6])
    a.button("Modifica la ricerca", use_container_width=True, on_click=vai, args=('tipo',))
    b.button("← Indietro", use_container_width=True, on_click=vai, args=('caratteristiche',))
    c.button("Simula una nuova offerta", type="primary", use_container_width=True, on_click=vai,
             args=('simula',))
    st.markdown(ui.riepilogo_ricerca(riepilogo(P)), unsafe_allow_html=True)

    with st.spinner("Calcolo della spesa annua in corso..."):
        res, _, esclusioni, scartate = cerca(data_rif_str, chiave_ricerca(), escludi_false, solo_singole)
    if res.empty:
        st.warning("Nessuna offerta trovata con questi parametri.")
        st.write("Esclusioni per filtro:", esclusioni)
        return
    unita = 'kWh' if P['commodity'] == 'E' else 'Smc'

    sx, dx = st.columns([1, 3.2])
    with sx:
        st.markdown('<div class="po-filtri">Ulteriori filtri</div>', unsafe_allow_html=True)
        venditori = ["Tutti"] + sorted(res['Venditore'].astype(str).unique())
        vend = st.selectbox("Venditori", venditori, key="f_vend")
        nome = st.text_input("Nome offerta", key="f_nome")
        codice = st.text_input("Codice offerta", key="f_cod")
        solo_sconti = st.checkbox("Solo offerte con sconti", key="f_sconti")
        no_limitanti = st.checkbox("Escludi condizioni di attivazione limitanti", key="f_lim",
                                   help="Il Portale le mostra: di default restano nell'elenco")
        ordine = st.selectbox("Ordina per", ["Spesa annua crescente", "Spesa annua decrescente",
                                             "Venditore", "Prezzo medio"], key="f_ord")
        vista = st.segmented_control("Vista", ["Schede", "Tabella dati"], default="Schede", key="f_vista")
    v = res
    if vend != "Tutti":
        v = v[v['Venditore'] == vend]
    if nome:
        v = v[v['NOME_OFFERTA'].astype(str).str.contains(nome, case=False, regex=False)]
    if codice:
        v = v[v['COD_OFFERTA'].astype(str).str.contains(codice, case=False, regex=False)]
    if solo_sconti:
        v = v[v['Sconti dichiarati'] != ""]
    if no_limitanti:
        v = v[~v['Limitante']]
    v = {"Spesa annua decrescente": v.sort_values('SAS', ascending=False),
         "Venditore": v.sort_values(['Venditore', 'SAS']),
         "Prezzo medio": v.sort_values('PREZZO_UNITARIO')}.get(ordine, v)

    with dx:
        st.markdown(f'<div class="po-found">Sono state trovate <span>{len(v)}</span> offerte</div>',
                    unsafe_allow_html=True)
        engie = res[res['Venditore'].astype(str).str.upper().str.contains('ENGIE')]
        if len(engie):
            e = engie.iloc[0]
            st.markdown(f'<div class="po-note">La migliore offerta <b>ENGIE</b> è <b>{ui.esc(e["NOME_OFFERTA"])}</b> '
                        f'in posizione <b>#{e["Pos"]}</b> su {len(res)}: € {ui.euro(e["SAS"])} annui, '
                        f'€ {ui.euro(e["SAS"] - res["SAS"].iloc[0])} sopra la prima.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="po-note">Nessuna offerta ENGIE in questa ricerca.</div>', unsafe_allow_html=True)
        if vista == "Tabella dati":
            st.caption("Tabella a tutta larghezza qui sotto ↓")
        else:
            n = ss.get('pag_risultati', 1) * PER_PAGINA
            schede(v.head(n), unita, "el")
            if n < len(v):
                st.button(f"Mostra altre offerte ({len(v) - n} rimanenti)", use_container_width=True,
                          on_click=vai, args=('elenco',), kwargs=dict(pag_risultati=ss.get('pag_risultati', 1) + 1))
    if vista == "Tabella dati":
        tabella(v, unita, f"ranking_{P['commodity']}_{P['regione']}_{data_rif_str}.csv")
    st.markdown('<div class="po-note">La spesa annua riportata rappresenta una stima che si basa su prezzi '
                'che nel tempo possono variare e su consumi dichiarati, che si possono discostare dai '
                'consumi futuri. Offerte variabili: indici stimati con i forward GME.</div>',
                unsafe_allow_html=True)
    with st.expander(f"Offerte escluse dalla ricerca ({sum(esclusioni.values())})"):
        st.write(esclusioni)
        if scartate is not None:
            st.dataframe(scartate, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------- pagina 4: dettaglio

def composizione(r: pd.Series, info: pd.Series | None, unita: str):
    h = ['<div class="po-box"><h4>Composizione della spesa annua stimata</h4>', ui.voce("Vendita di " + ("energia elettrica" if P['commodity'] == 'E' else "gas naturale"), r['VENDITA'])]
    if info is not None:
        for c in ui.componenti(info):
            nota = " · ".join(x for x in (c['fascia'], c['scaglione'] and f"scaglione {c['scaglione']}",
                                          "opzionale" if c['opzionale'] else "") if x)
            h.append(ui.sottovoce(c['nome'], c['prezzo'], nota))
        reg = [n[9:] for n in info.index if n.startswith('REGOLATA_') and ui._vero(info[n])]
        if reg:
            h.append(ui.sottovoce("Componenti regolate", ", ".join(reg)))
        if "ariabil" in str(info.get('TIPO_OFFERTA')):
            h.append(ui.sottovoce("Indice", "forward GME (4 trimestri)"))
    if r['SCONTI']:
        h.append(ui.voce("Sconti soggetti a IVA", r['SCONTI']))
    h.append(ui.voce("Tariffa per l'uso della rete", r['RETE']))
    h.append(ui.voce("Oneri generali di sistema", r['ONERI']))
    h.append(ui.voce("Spesa netto imposte stimata", r['VENDITA'] + r['SCONTI'] + r['RETE'] + r['ONERI'], True))
    h.append(ui.voce("Imposte", r['IMPOSTE']))
    h.append(ui.voce("IVA", r['IVA']))
    if r['SCONTI_NO_IVA']:
        h.append(ui.voce("Sconti non soggetti a IVA", r['SCONTI_NO_IVA']))
    h.append(ui.voce("Spesa annua stimata", r['SAS'], True))
    h.append('<div class="po-cod" style="margin-top:10px">Corrispettivi unitari al netto delle imposte; '
             'rete, oneri e imposte dai parametri del Portale del giorno.</div></div>')
    st.markdown("".join(h), unsafe_allow_html=True)


def pagina_dettaglio():
    intestazione("Confronta > Dettaglio", "Dettaglio Offerta")
    a, _ = st.columns([1.2, 4])
    a.button("← Torna ai risultati", type="primary", use_container_width=True, on_click=vai, args=('elenco',))
    st.markdown(ui.riepilogo_ricerca(riepilogo(P)), unsafe_allow_html=True)
    res, f, _, _ = cerca(data_rif_str, chiave_ricerca(), escludi_false, solo_singole)
    piva, cod = ss.get('sel', (None, None))
    m = res[(res['PIVA_VENDITORE'] == piva) & (res['COD_OFFERTA'] == cod)] if len(res) else res
    if m.empty:
        st.warning("Offerta non più presente nella ricerca.")
        return
    r = m.iloc[0]
    info = f[(f['PIVA_UTENTE'] == piva) & (f['COD_OFFERTA'] == cod)].iloc[0]
    unita = 'kWh' if P['commodity'] == 'E' else 'Smc'

    sx, dx = st.columns([1.15, 1])
    with sx:
        st.markdown(f'<div class="po-box"><h4>Descrizione offerta</h4>{ui.esc(info.get("DESCRIZIONE_OFFERTA"))}</div>',
                    unsafe_allow_html=True)
        composizione(r, info, unita)
    with dx:
        g = lambda c: str(info.get(c)) if ui._pieno(info.get(c)) else ""
        att = [n.replace('MOD_ATTIVAZIONE_', '') for n in info.index
               if n.startswith('MOD_ATTIVAZIONE_') and not n.endswith(('_DESC', '_A')) and ui._vero(info[n])]
        pag = [n.replace('PAGAMENTO_', '').replace('_', ' ') for n in info.index
               if n.startswith('PAGAMENTO_') and not n.endswith(('_DESC', '_A')) and ui._vero(info[n])]
        st.markdown(
            f'<div class="po-box" style="text-align:center"><b>Nome offerta:</b> '
            f'<span style="color:{ui.MAGENTA}">{ui.esc(r["NOME_OFFERTA"])}</span><br>'
            f'<span class="po-cod">Codice offerta: {ui.esc(cod)}</span><br>'
            f'<b>Posizione #{r["Pos"]} su {len(res)} · € {ui.euro(r["SAS"])} annui</b><br>'
            f'<span class="po-cod">Valida dal {ui.esc(g("DATA_INIZIO").split("_")[0])} al '
            f'{ui.esc(g("DATA_FINE").split("_")[0])}</span><hr>'
            f'<div class="po-vend">{ui.esc(r["Venditore"])}</div><br>'
            + ui.griglia_info([
                ("Numero telefonico", g("TELEFONO")), ("Sito web del venditore", g("URL_SITO_VENDITORE")),
                ("Pagina dell'offerta", g("URL_OFFERTA")), ("Tipo di prezzo", g("TIPO_OFFERTA")),
                ("Tipo cliente", g("TIPO_CLIENTE")), ("Configurazione fasce", g("TIPOLOGIA_FASCE")),
                ("Residenza", g("DOMESTICO_RESIDENTE")), ("Modalità di attivazione", ", ".join(att)),
                ("Metodi di pagamento", ", ".join(pag))]) + '</div>', unsafe_allow_html=True)
        sc = ui.sconti(info)
        st.markdown('<div class="po-box"><h4>Sconti</h4>' + ("<br>".join(f"• {ui.esc(s)}" for s in sc)
                    if sc else "Nessuno sconto dichiarato") + '</div>', unsafe_allow_html=True)
        st.markdown('<div class="po-box"><h4>Note utili</h4>' + "<br>".join(f"• {ui.esc(n)}" for n in ui.note(info))
                    + '</div>', unsafe_allow_html=True)
        if g("GARANZIE"):
            with st.expander("Garanzie"):
                st.write(g("GARANZIE"))


# ---------------------------------------------------------------- simulatore nuova offerta

def form_offerta() -> osim.NuovaOfferta | None:
    luce = P['commodity'] == 'E'
    variabile = P['tipo'] == 'Variabile'
    u = '€/kWh' if luce else '€/Smc'
    with st.form("nuova_offerta", border=True):
        st.markdown('<div class="po-filtri">La tua nuova offerta</div>', unsafe_allow_html=True)
        nome = st.text_input("Nome offerta", "Nuova offerta ENGIE")
        if luce:
            strutture = (["Monoraria"] if P['fasce'] == 'Monoraria'
                         else ["Bioraria (F1 / F2+F3)", "Trioraria (F1, F2, F3)"])
            fasce = st.selectbox("Struttura di prezzo", strutture,
                                 help="Deve corrispondere alla ricerca: il Portale mostra monorarie e offerte "
                                      "a fasce in elenchi separati")
        quota = st.number_input("Quota fissa di commercializzazione (€/anno)", 0.0, 2000.0, 120.0, 1.0)
        etichetta = f"Spread sull'indice ({u})" if variabile else f"Prezzo energia ({u})"
        prezzi = {}
        if luce:
            if fasce == "Monoraria":
                prezzi['F0'] = st.number_input(etichetta, -1.0, 2.0, 0.01 if variabile else 0.12, 0.001, format="%.6f")
            elif fasce.startswith("Bioraria"):
                c1, c2 = st.columns(2)
                prezzi['F1'] = c1.number_input(f"F1 {u}", -1.0, 2.0, 0.01 if variabile else 0.13, 0.001, format="%.6f")
                prezzi['F23'] = c2.number_input(f"F2+F3 {u}", -1.0, 2.0, 0.01 if variabile else 0.11, 0.001, format="%.6f")
            else:
                c1, c2, c3 = st.columns(3)
                for c, k, v in ((c1, 'F1', 0.13), (c2, 'F2', 0.12), (c3, 'F3', 0.11)):
                    prezzi[k] = c.number_input(f"{k} {u}", -1.0, 2.0, 0.01 if variabile else v, 0.001, format="%.6f")
            potenza = st.number_input("Quota potenza (€/kW/anno)", 0.0, 500.0, 0.0, 1.0)
        else:
            fasce, potenza = "Monoraria", 0.0
            prezzi['G'] = st.number_input(etichetta, -1.0, 5.0, 0.08 if variabile else 0.45, 0.001, format="%.6f")
        verde = st.number_input(f"Energia verde, se inclusa ({u})", 0.0, 1.0, 0.0, 0.001, format="%.6f")
        opz_reg = ["PCV", "PPE"] if luce else ["QVD_Fissa", "QVD_Variabile", "CCR", "CPR", "GRAD"]
        regolate = st.multiselect("Componenti regolate applicate", opz_reg,
                                  help="Il Portale le aggiunge alla vendita con i propri valori")
        cdispd = st.checkbox("Dispacciamento al valore del Portale (CdispD)", True) if luce else False
        st.markdown("**Sconti**")
        sconti = st.data_editor(
            pd.DataFrame([{"Sconto": "Bonus benvenuto", "Valore": 0.0, "Unità": "€/Anno",
                           "Condizione": "Non condizionato", "Validità": "Ingresso", "IVA": "SI", "Mesi": None}]),
            num_rows="dynamic", hide_index=True, use_container_width=True,
            column_config={
                "Unità": st.column_config.SelectboxColumn(options=["€/Anno", "€", u, "Percentuale"]),
                "Condizione": st.column_config.SelectboxColumn(
                    options=["Non condizionato", "Fatturazione elettronica",
                             "fatturazione elettronica+domiciliazione bancaria", "Altro"]),
                "Validità": st.column_config.SelectboxColumn(options=["Ingresso", "entro 12 mesi", "oltre 12 mesi"]),
                "IVA": st.column_config.SelectboxColumn(options=["SI", "NO"]),
                "Mesi": st.column_config.NumberColumn(help="Durata dello sconto in mesi (vuoto = 12)"),
            })
        inviato = st.form_submit_button("Calcola la posizione →", type="primary", use_container_width=True)
    if not inviato and 'offerta_sim' not in ss:
        return None
    if inviato:
        ss.offerta_sim = osim.NuovaOfferta(
            commodity=P['commodity'], nome=nome, tipo_offerta=P['tipo'], fasce=fasce, quota_fissa=quota,
            prezzi=prezzi, quota_potenza=potenza, verde=verde, regolate=tuple(regolate), cdispd=cdispd,
            sconti=[osim.Sconto(nome=str(s["Sconto"] or "Sconto"), valore=float(s["Valore"]), unita=s["Unità"],
                                condizione=s["Condizione"], validita=s["Validità"], iva=s["IVA"],
                                durata_mesi=int(s["Mesi"]) if pd.notna(s["Mesi"]) else None)
                    for s in sconti.to_dict("records") if s.get("Valore")])
    o = ss.offerta_sim
    stessa_struttura = o.commodity == 'G' or (o.fasce == 'Monoraria') == (P['fasce'] == 'Monoraria')
    return o if o.commodity == P['commodity'] and o.tipo_offerta == P['tipo'] and stessa_struttura else None


def pagina_simula():
    intestazione("Simula", "Simula una nuova offerta")
    a, b, _ = st.columns([1.2, 1.4, 3])
    a.button("← Indietro", use_container_width=True, on_click=vai, args=('elenco',))
    b.button("Modifica la ricerca", use_container_width=True, on_click=vai, args=('tipo',))
    st.markdown(ui.riepilogo_ricerca(riepilogo(P)), unsafe_allow_html=True)
    st.caption("La nuova offerta viene confrontata con le offerte della ricerca corrente; per cambiare "
               "commodity, regione, tipo di prezzo o consumi usa «Modifica la ricerca».")

    sx, dx = st.columns([1.1, 1.6])
    with sx:
        offerta = form_offerta()
    with dx:
        if offerta is None:
            st.markdown('<div class="po-note">Compila l\'offerta e premi <b>Calcola la posizione</b> per vedere '
                        'dove si posizionerebbe nel ranking del Portale.</div>', unsafe_allow_html=True)
            return
        res, f, _, _ = cerca(data_rif_str, chiave_ricerca(), escludi_false, solo_singole)
        calc = calcolatore(data_rif_str)
        with st.spinner("Calcolo del posizionamento..."):
            esito = osim.posiziona(calc, f, offerta, **kw_calcolo(P))
        rk = esito['ranking']
        nomi = dict(zip(f['PIVA_UTENTE'], f['NOME_VENDITORE'])) | {osim.PIVA_SIMULATA: 'LA TUA NUOVA OFFERTA'}
        rk['Venditore'] = rk['PIVA_VENDITORE'].map(nomi)
        rk['Tipo'] = P['tipo']
        rk['Sconti dichiarati'] = ""
        rk.insert(0, 'Pos', range(1, len(rk) + 1))
        pos, tot, sas = esito['posizione'], esito['totale'], esito['sas']
        unita = 'kWh' if P['commodity'] == 'E' else 'Smc'

        k1, k2, k3 = st.columns(3)
        k1.metric("Posizione nel ranking", f"#{pos} su {tot}")
        k2.metric("Spesa annua stimata", f"€ {ui.euro(sas)}")
        if esito['primo'] is not None:
            k3.metric("Distanza dalla prima", f"€ {ui.euro(sas - esito['primo'])}",
                      delta=f"{ui.euro(sas - esito['primo'])} €", delta_color="inverse")
        engie = rk[rk['Venditore'].astype(str).str.upper().str.contains('ENGIE')
                   & (rk['PIVA_VENDITORE'] != osim.PIVA_SIMULATA)]
        if len(engie):
            e = engie.iloc[0]
            st.markdown(f'<div class="po-note">Migliore offerta ENGIE attuale: <b>{ui.esc(e["NOME_OFFERTA"])}</b>, '
                        f'#{e["Pos"]} (€ {ui.euro(e["SAS"])}). La nuova offerta è '
                        f'{"più conveniente" if sas < e["SAS"] else "più cara"} di € {ui.euro(abs(sas - e["SAS"]))}.'
                        f'</div>', unsafe_allow_html=True)

        obiettivi = esito['obiettivi']
        if obiettivi:
            st.markdown('<div class="po-filtri">Cosa serve per salire</div>', unsafe_allow_html=True)
            righe = []
            unico = next(iter(offerta.prezzi)) if len(offerta.prezzi) == 1 else None
            for p, t in obiettivi.items():
                gia = t['delta_sas'] >= 0 or pos <= p
                d_e, d_f = (0.0, 0.0) if gia else (t['d_energia'], t['d_fissa'])
                riga_t = {"Obiettivo": f"#{p}", "Spesa da battere €": t['sas_obiettivo'] + 0.01,
                          "Riduzione spesa €": 0.0 if gia else -t['delta_sas'],
                          f"Δ prezzo energia €/{unita}": d_e}
                if unico:
                    riga_t[f"Prezzo energia necessario €/{unita}"] = offerta.prezzi[unico] + d_e
                riga_t["oppure Δ quota fissa €/anno"] = d_f
                riga_t["Quota fissa necessaria €/anno"] = offerta.quota_fissa + d_f
                riga_t["Stato"] = "già raggiunto" if gia else ""
                righe.append(riga_t)
            num = st.column_config.NumberColumn
            st.dataframe(pd.DataFrame(righe), hide_index=True, use_container_width=True, column_config={
                "Spesa da battere €": num(format="%.2f"), "Riduzione spesa €": num(format="%.2f"),
                f"Δ prezzo energia €/{unita}": num(format="%.6f"),
                f"Prezzo energia necessario €/{unita}": num(format="%.6f"),
                "oppure Δ quota fissa €/anno": num(format="%.2f"),
                "Quota fissa necessaria €/anno": num(format="%.2f")})
            st.caption("Le due leve sono alternative: basta una delle due variazioni"
                       + ("" if unico else "; il Δ prezzo energia si applica a tutte le fasce") + ".")
            st.caption(f"Sensibilità: +0,01 €/{unita} sul prezzo energia = "
                       f"€ {ui.euro(esito['sensibilita']['energia'] * 0.01)} di spesa annua; "
                       f"+1 €/anno di quota fissa = € {ui.euro(esito['sensibilita']['fissa'])}.")

        mia = rk[rk['PIVA_VENDITORE'] == osim.PIVA_SIMULATA].iloc[0]
        t1, t2, t3 = st.tabs(["Posizionamento", "Composizione della spesa", "Ranking completo"])
        with t1:
            vicine = rk.iloc[max(0, pos - 4): pos + 3]
            if pos > 4:
                schede(rk.head(1), unita, "simtop")
                st.markdown('<div style="text-align:center;color:#888">⋮</div>', unsafe_allow_html=True)
            schede(vicine, unita, "sim")
        with t2:
            composizione(mia, pd.Series(offerta.riga()), unita)
        with t3:
            tabella(rk, unita, f"ranking_simulato_{P['commodity']}_{P['regione']}.csv")


# ---------------------------------------------------------------- router

{'tipo': pagina_tipo, 'caratteristiche': pagina_caratteristiche, 'elenco': pagina_elenco,
 'dettaglio': pagina_dettaglio, 'simula': pagina_simula}.get(ss.pagina, pagina_tipo)()
st.markdown(f'<div class="po-footer">Simulatore basato sugli open data del Portale Offerte (ARERA - Acquirente '
            f'Unico) e sulle Regole per il calcolo della spesa v4.0. Dati al {ultima:%d/%m/%Y}. Uso interno ENGIE.'
            f'</div>', unsafe_allow_html=True)
