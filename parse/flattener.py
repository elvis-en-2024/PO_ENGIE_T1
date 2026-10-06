import logging
from lxml import etree

logger = logging.getLogger(__name__)

# --- DIZIONARI DI TRANSCODIFICA (dal manuale SII) ---
DECODE_MAPS = {
    "TIPO_MERCATO": {"01": "Elettrico", "02": "Gas", "03": "Dual Fuel"},
    "TIPO_CLIENTE": {"01": "Domestico", "02": "Altri Usi", "03": "Condominio Uso Domestico (Gas)"},
    "DOMESTICO_RESIDENTE": {"01": "Residente", "02": "NON Residente", "03": "Tutte"},
    "TIPO_OFFERTA": {"01": "Fisso", "02": "Variabile", "03": "FLAT", "04": "Mista"},
    "OFFERTA_ONNICOMPRENSIVA": {"01": "Offerta onnicomprensiva", "02": "Offerta onnicomprensiva a canone"},
    "TIPOLOGIA_FASCE": {
        "01": "monorario/F1", "02": "F2", "03": "F1, F2, F3", "04": "F1, F2, F3, F4", 
        "05": "F1, F2, F3, F4, F5", "06": "F1, F2, F3, F4, F5, F6", "07": "Peak/OffPeak", 
        "91": "biorario (F1 / F2+F3)", "92": "biorario (F2 / F1+F3)", "93": "biorario (F3 / F1+F2)"
    },
    "UNITA_MISURA": {"01": "€/Anno", "02": "€/kW", "03": "€/kWh", "04": "€/Smc", "05": "€", "06": "Percentuale"},
    "TIPO_PREZZO": {"01": "Fisso", "02": "Variabile"},
    "FASCIA_COMPONENTE": {
        "01": "monorario/F1", "02": "F2", "03": "F3", "04": "F4", "05": "F5", "06": "F6", 
        "07": "Peak", "08": "OffPeak", "91": "F2+F3", "92": "F1+F3", "93": "F1+F2"
    },
    "MACROAREA_COMP": {
        "01": "Commercializzazione quota fissa", "02": "Commercializzazione quota energia",
        "04": "Prezzo quota energia", "05": "Una Tantum", "06": "FER/Energia Verde"
    },
    "LIMITANTE": {"01": "Si, è limitante", "02": "No, non è limitante"},
    "IVA_SCONTO": {"01": "SI", "02": "NO"},
    "TIPOLOGIA_SCONTO": {"01": "Sconto fisso", "02": "Sconto Potenza", "03": "Sconto Vendita", "04": "sconto su tutela"},
    "VALIDITA_SCONTO": {"01": "Ingresso", "02": "entro 12 mesi", "03": "oltre 12 mesi"},
    "CONDIZIONE_APP": {
        "00": "Non condizionato", "01": "Fatturazione elettronica", "02": "Gestione online", 
        "03": "fatturazione elettronica+domiciliazione bancaria", "99": "Altro"
    },
    "CODICE_SCONTO": {
        "01": "PCV", "02": "PPE", "03": "CCR", "04": "CPR", "05": "GRAD", "06": "QTint", "07": "QTpsv", 
        "09": "QVD_Fissa", "10": "QVD_Variabile", "11": "F1", "12": "F2", "13": "F3", "14": "F4", 
        "15": "F5", "16": "F6", "17": "Peak", "18": "OffPeak", "91": "F2+F3", "92": "F1+F3", "93": "F1+F2"
    },
    "TIPOLOGIA_COMP": {"01": "STANDARD", "02": "OPZIONALE"}
}

def decode(val, map_name):
    if not val: return val
    mapping = DECODE_MAPS.get(map_name, {})
    return mapping.get(val, val)

def get_text(elem, xpath, namespaces, default=None):
    if elem is None:
        return default
    nodes = elem.xpath(xpath, namespaces=namespaces)
    return nodes[0].text.strip() if nodes and nodes[0].text else default

def get_float(elem, xpath, namespaces, default=None):
    text = get_text(elem, xpath, namespaces)
    if text:
        try:
            return float(text.replace(',', '.'))
        except ValueError:
            return default
    return default

def get_texts(elem, xpath, namespaces, sep="|"):
    """Tutti i nodi che matchano xpath, uniti con sep (None se nessuno)."""
    if elem is None:
        return None
    vals = [n.text.strip() for n in elem.xpath(xpath, namespaces=namespaces)
            if n.text and n.text.strip()]
    return sep.join(vals) if vals else None


# Limiti posizionali delle colonne piatte. File del 24/09/2026: E fino a 12
# componenti e 9 intervalli, G fino a 53 componenti (un venditore pubblica un
# componente per zona), 6 sconti, 3 prezzi sconto.
MAX_COMPONENTI = 60
MAX_INTERVALLI = 10
MAX_SCONTI = 15
MAX_PREZZI_SCONTO = 5


def _avvisa_troncamento(record, cosa, n, limite):
    if n > limite:
        logger.warning("Offerta %s/%s: %d %s, ne vengono salvati solo %d",
                       record.get("PIVA_UTENTE"), record.get("COD_OFFERTA"),
                       n, cosa, limite)


def flatten_offer(elem: etree._Element, commodity: str, namespaces: dict) -> dict:
    record = {"commodity": commodity}
    
    # --- CAMPI SINGOLI ---
    record["PIVA_UTENTE"] = get_text(elem, "ns:IdentificativiOfferta/ns:PIVA_UTENTE", namespaces)
    record["COD_OFFERTA"] = get_text(elem, "ns:IdentificativiOfferta/ns:COD_OFFERTA", namespaces)
    
    record["TIPO_MERCATO"] = decode(get_text(elem, "ns:DettaglioOfferta/ns:TIPO_MERCATO", namespaces), "TIPO_MERCATO")
    record["OFFERTA_SINGOLA"] = get_text(elem, "ns:DettaglioOfferta/ns:OFFERTA_SINGOLA", namespaces)
    record["TIPO_CLIENTE"] = decode(get_text(elem, "ns:DettaglioOfferta/ns:TIPO_CLIENTE", namespaces), "TIPO_CLIENTE")
    record["DOMESTICO_RESIDENTE"] = decode(get_text(elem, "ns:DettaglioOfferta/ns:DOMESTICO_RESIDENTE", namespaces), "DOMESTICO_RESIDENTE")
    record["TIPO_OFFERTA"] = decode(get_text(elem, "ns:DettaglioOfferta/ns:TIPO_OFFERTA", namespaces), "TIPO_OFFERTA")
    record["OFFERTA_ONNICOMPRENSIVA"] = decode(get_text(elem, "ns:DettaglioOfferta/ns:OFFERTA_ONNICOMPRENSIVA", namespaces), "OFFERTA_ONNICOMPRENSIVA")
    record["CONSUMO_CANONE"] = get_float(elem, "ns:DettaglioOfferta/ns:CONSUMO_CANONE", namespaces)
    record["NOME_OFFERTA"] = get_text(elem, "ns:DettaglioOfferta/ns:NOME_OFFERTA", namespaces)
    record["DESCRIZIONE_OFFERTA"] = get_text(elem, "ns:DettaglioOfferta/ns:DESCRIZIONE", namespaces)
    record["DURATA"] = get_float(elem, "ns:DettaglioOfferta/ns:DURATA", namespaces)
    record["GARANZIE"] = get_text(elem, "ns:DettaglioOfferta/ns:GARANZIE", namespaces)
    record["TELEFONO"] = get_text(elem, "ns:DettaglioOfferta/ns:Contatti/ns:TELEFONO", namespaces)
    record["URL_SITO_VENDITORE"] = get_text(elem, "ns:DettaglioOfferta/ns:Contatti/ns:URL_SITO_VENDITORE", namespaces)
    record["URL_OFFERTA"] = get_text(elem, "ns:DettaglioOfferta/ns:Contatti/ns:URL_OFFERTA", namespaces)
    record["PREZZO_COMPRENSIVO_PERDITE_RETE"] = get_text(elem, "ns:DettaglioOfferta/ns:PrezzoComprensivoPerditeRete", namespaces)
    
    record["DATA_INIZIO"] = get_text(elem, "ns:ValiditaOfferta/ns:DATA_INIZIO", namespaces)
    record["DATA_FINE"] = get_text(elem, "ns:ValiditaOfferta/ns:DATA_FINE", namespaces)
    record["CONSUMO_MIN"] = get_float(elem, "ns:CaratteristicheOfferta/ns:CONSUMO_MIN", namespaces)
    record["CONSUMO_MAX"] = get_float(elem, "ns:CaratteristicheOfferta/ns:CONSUMO_MAX", namespaces)
    record["POTENZA_MIN"] = get_float(elem, "ns:CaratteristicheOfferta/ns:POTENZA_MIN", namespaces)
    record["POTENZA_MAX"] = get_float(elem, "ns:CaratteristicheOfferta/ns:POTENZA_MAX", namespaces)
    
    record["OFFERTE_CONGIUNTE_EE"] = get_text(elem, "ns:OffertaDual/ns:OFFERTE_CONGIUNTE_EE", namespaces)
    record["OFFERTE_CONGIUNTE_GAS"] = get_text(elem, "ns:OffertaDual/ns:OFFERTE_CONGIUNTE_GAS", namespaces)
    # Un'offerta può valere su più zone: codici separati da '|' (es. "01|07").
    record["REGIONE"] = get_texts(elem, "ns:ZoneOfferta/ns:REGIONE", namespaces)
    record["PROVINCIA"] = get_texts(elem, "ns:ZoneOfferta/ns:PROVINCIA", namespaces)
    record["COMUNE"] = get_texts(elem, "ns:ZoneOfferta/ns:COMUNE", namespaces)
    
    record["TIPOLOGIA_FASCE"] = decode(get_text(elem, "ns:TipoPrezzo/ns:TIPOLOGIA_FASCE", namespaces), "TIPOLOGIA_FASCE")

    # --- CAMPI MULTIPLI SEMANTICI (In base a Codice Enum) ---
    
    # 0. TIPOLOGIA_ATT_CONTR (Codici: 01, 02, 03, 04, 99)
    att_contr_names = {"01": "Cambio Fornitore", "02": "Prima Attivazione", "03": "Riattivazione", "04": "Voltura", "99": "Sempre"}
    for code, name in att_contr_names.items():
        record[f"ATT_CONTR_{name}"] = False
    for node in elem.xpath("ns:DettaglioOfferta/ns:TIPOLOGIA_ATT_CONTR", namespaces=namespaces):
        if node.text:
            mod = node.text.strip()
            if mod in att_contr_names: record[f"ATT_CONTR_{att_contr_names[mod]}"] = True

    # 0.1 MODALITA ATTIVAZIONE (Codici: 01, 02, 03, 04, 05, 99)
    mod_att_names = {"01": "Solo web", "02": "Qualsiasi canale", "03": "Punto vendita", "04": "Teleselling", "05": "Agenzia", "99": "Altro"}
    for code, name in mod_att_names.items():
        record[f"MOD_ATTIVAZIONE_{name}"] = False
    record["MOD_ATTIVAZIONE_Altro_DESC"] = None
    for node in elem.xpath("ns:DettaglioOfferta/ns:ModalitaAttivazione", namespaces=namespaces):
        mod = get_text(node, "ns:MODALITA", namespaces)
        if mod in mod_att_names:
            record[f"MOD_ATTIVAZIONE_{mod_att_names[mod]}"] = True
            if mod == "99":
                record["MOD_ATTIVAZIONE_Altro_DESC"] = get_text(node, "ns:DESCRIZIONE", namespaces)

    # 1. MetodoPagamento (Codici: 01, 02, 03, 04, 99)
    pag_names = {"01": "Dom_Bancaria", "02": "Dom_Postale", "03": "Carta_Credito", "04": "Bollettino", "99": "Altro"}
    for code, name in pag_names.items():
        record[f"PAGAMENTO_{name}"] = False
    record["PAGAMENTO_Altro_DESC"] = None
    for node in elem.xpath("ns:MetodoPagamento", namespaces=namespaces):
        mod = get_text(node, "ns:MODALITA_PAGAMENTO", namespaces)
        if mod in pag_names:
            record[f"PAGAMENTO_{pag_names[mod]}"] = True
            if mod == "99":
                record["PAGAMENTO_Altro_DESC"] = get_text(node, "ns:DESCRIZIONE", namespaces)

    # 2. Dispacciamento (Codici: 01..14, 99)
    disp_names = {"01": "TIDE", "02": "PD", "09": "Capacita_STG", "10": "Capacita_MT", "11": "Salvaguardia", "12": "Tutele_Graduali", "13": "DispBT", "14": "CdispD", "99": "Altro"}
    for code in [f"{i:02d}" for i in range(1, 15)] + ["99"]:
        name = disp_names.get(code, f"Cod_{code}")
        record[f"DISP_{name}"] = False
        record[f"DISP_{name}_VALORE"] = None
    for node in elem.xpath("ns:Dispacciamento", namespaces=namespaces):
        tipo = get_text(node, "ns:TIPO_DISPACCIAMENTO", namespaces)
        if tipo:
            name = disp_names.get(tipo, f"Cod_{tipo}")
            record[f"DISP_{name}"] = True
            record[f"DISP_{name}_VALORE"] = get_text(node, "ns:VALORE_DISP", namespaces)

    # 3. Componenti Regolate (Codici: 01..10)
    reg_names = {"01": "PCV", "02": "PPE", "03": "CCR", "04": "CPR", "05": "GRAD", "06": "QTint", "07": "QTpsv", "09": "QVD_Fissa", "10": "QVD_Variabile"}
    for code, name in reg_names.items():
        record[f"REGOLATA_{name}"] = False
    # un nodo ComponentiRegolate può contenere più CODICE
    for node in elem.xpath("ns:ComponentiRegolate/ns:CODICE", namespaces=namespaces):
        cod = (node.text or "").strip()
        if cod in reg_names:
            record[f"REGOLATA_{reg_names[cod]}"] = True

    # 4. CondizioniContrattuali (Codici: 01..05, 99)
    cond_names = {"01": "Attivazione", "02": "Disattivazione", "03": "Recesso", "04": "Pluriennale", "05": "Oneri_Recesso", "99": "Altro"}
    for code, name in cond_names.items():
        record[f"COND_{name}"] = False
        record[f"COND_{name}_LIMITANTE"] = None
    for node in elem.xpath("ns:CondizioniContrattuali", namespaces=namespaces):
        tipo = get_text(node, "ns:TIPOLOGIA_CONDIZIONE", namespaces)
        if tipo in cond_names:
            name = cond_names[tipo]
            record[f"COND_{name}"] = True
            record[f"COND_{name}_LIMITANTE"] = decode(get_text(node, "ns:LIMITANTE", namespaces), "LIMITANTE")

    # 5. RiferimentiPrezzoEnergia (Codici: 01..15, 99)
    idx_names = {
        "01": "PUN_Trim", "02": "TTF_Trim", "03": "PSV_Trim",
        "04": "Psbil_Bim", "05": "PE_Bim", "07": "Pfor_Bim", "08": "PUN_Bim", "09": "TTF_Bim", "10": "PSV_Bim", "11": "Psbil_Bim",
        "06": "Cmem_Men", "12": "PUN_Men", "13": "TTF_Men", "14": "PSV_Men", "15": "Psbil_Men", "99": "Altro"
    }
    for code in [f"{i:02d}" for i in range(1, 16)] + ["99"]:
        name = idx_names.get(code, f"Cod_{code}")
        record[f"IDX_{name}"] = False
        record[f"IDX_{name}_COEFF"] = None
    for node in elem.xpath("ns:RiferimentiPrezzoEnergia", namespaces=namespaces):
        idx = get_text(node, "ns:IDX_PREZZO_ENERGIA", namespaces)
        if idx:
            name = idx_names.get(idx, f"Cod_{idx}")
            record[f"IDX_{name}"] = True
            record[f"IDX_{name}_COEFF"] = get_text(node, "ns:COEFFICIENTE", namespaces)

    # 6. ProdottiServiziAggiuntivi (Macroaree: 01..06, 99)
    serv_names = {"01": "Caldaia", "02": "Mobility", "03": "Solare", "04": "Fotovoltaico", "05": "Clima", "06": "Polizza", "99": "Altro"}
    for code, name in serv_names.items():
        record[f"SERVIZIO_{name}"] = False
    for node in elem.xpath("ns:ProdottiServiziAggiuntivi", namespaces=namespaces):
        area = get_text(node, "ns:MACROAREA", namespaces)
        if area in serv_names:
            record[f"SERVIZIO_{serv_names[area]}"] = True

    # --- CAMPI MULTIPLI COMPLESSI (Posizionali) ---
    # Schema dinamico: colonne solo per i nodi presenti (i chiamanti uniscono
    # gli schemi con concat diagonale). I limiti sono solo una protezione e
    # chi li supera viene segnalato.
    comp_nodes = elem.xpath("ns:ComponenteImpresa", namespaces=namespaces)
    _avvisa_troncamento(record, "ComponenteImpresa", len(comp_nodes), MAX_COMPONENTI)
    for i, comp in enumerate(comp_nodes[:MAX_COMPONENTI]):
        pfx = f"COMP_IMP_{i+1}"
        tipologia = get_text(comp, "ns:TIPOLOGIA", namespaces)
        macroarea = get_text(comp, "ns:MACROAREA", namespaces)
        record[f"{pfx}_NOME"] = get_text(comp, "ns:NOME", namespaces)
        record[f"{pfx}_DESCRIZIONE"] = get_text(comp, "ns:DESCRIZIONE", namespaces)
        record[f"{pfx}_TIPOLOGIA"] = decode(tipologia, "TIPOLOGIA_COMP")
        record[f"{pfx}_TIPOLOGIA_COD"] = tipologia
        record[f"{pfx}_MACROAREA"] = decode(macroarea, "MACROAREA_COMP")
        record[f"{pfx}_MACROAREA_COD"] = macroarea

        interv_nodes = comp.xpath("ns:IntervalloPrezzi", namespaces=namespaces)
        _avvisa_troncamento(record, f"IntervalloPrezzi nel componente {i+1}",
                            len(interv_nodes), MAX_INTERVALLI)
        for j, interv in enumerate(interv_nodes[:MAX_INTERVALLI]):
            ipfx = f"{pfx}_INT_{j+1}"
            record[f"{ipfx}_FASCIA"] = decode(get_text(interv, "ns:FASCIA_COMPONENTE", namespaces), "FASCIA_COMPONENTE")
            record[f"{ipfx}_CONSUMO_DA"] = get_text(interv, "ns:CONSUMO_DA", namespaces)
            record[f"{ipfx}_CONSUMO_A"] = get_text(interv, "ns:CONSUMO_A", namespaces)
            record[f"{ipfx}_PREZZO"] = get_text(interv, "ns:PREZZO", namespaces)
            record[f"{ipfx}_UNITA"] = decode(get_text(interv, "ns:UNITA_MISURA", namespaces), "UNITA_MISURA")
            record[f"{ipfx}_TIPO_PREZZO"] = decode(get_text(interv, "ns:TIPO_PREZZO", namespaces), "TIPO_PREZZO")
            record[f"{ipfx}_VALIDO_FINO"] = get_text(interv, "ns:PeriodoValidita/ns:VALIDO_FINO", namespaces)
            record[f"{ipfx}_DURATA"] = get_text(interv, "ns:PeriodoValidita/ns:DURATA", namespaces)

    sconto_nodes = elem.xpath("ns:Sconto", namespaces=namespaces)
    _avvisa_troncamento(record, "Sconto", len(sconto_nodes), MAX_SCONTI)
    for i, sc in enumerate(sconto_nodes[:MAX_SCONTI]):
        pfx = f"SCONTO_{i+1}"
        record[f"{pfx}_NOME"] = get_text(sc, "ns:NOME", namespaces)
        record[f"{pfx}_CODICE_COMP"] = decode(get_text(sc, "ns:CODICE_COMPONENTE_FASCIA", namespaces), "CODICE_SCONTO")
        record[f"{pfx}_VALIDITA"] = decode(get_text(sc, "ns:VALIDITA", namespaces), "VALIDITA_SCONTO")
        record[f"{pfx}_IVA"] = decode(get_text(sc, "ns:IVA_SCONTO", namespaces), "IVA_SCONTO")
        # periodo di applicazione: DURATA in mesi, oppure fino a una data / mese
        record[f"{pfx}_DURATA"] = get_text(sc, "ns:PeriodoValidita/ns:DURATA", namespaces)
        record[f"{pfx}_VALIDO_FINO"] = get_text(sc, "ns:PeriodoValidita/ns:VALIDO_FINO", namespaces)
        record[f"{pfx}_MESE_VALIDITA"] = get_text(sc, "ns:PeriodoValidita/ns:MESE_VALIDITA", namespaces)
        record[f"{pfx}_COND_APP"] = decode(get_text(sc, "ns:Condizione/ns:CONDIZIONE_APPLICAZIONE", namespaces), "CONDIZIONE_APP")

        ps_nodes = sc.xpath("ns:PrezziSconto", namespaces=namespaces)
        _avvisa_troncamento(record, f"PrezziSconto nello sconto {i+1}",
                            len(ps_nodes), MAX_PREZZI_SCONTO)
        for j, ps in enumerate(ps_nodes[:MAX_PREZZI_SCONTO]):
            record[f"{pfx}_PREZZO_{j+1}_TIPO"] = decode(get_text(ps, "ns:TIPOLOGIA", namespaces), "TIPOLOGIA_SCONTO")
            record[f"{pfx}_PREZZO_{j+1}_VAL"] = get_text(ps, "ns:PREZZO", namespaces)
            record[f"{pfx}_PREZZO_{j+1}_UNITA"] = decode(get_text(ps, "ns:UNITA_MISURA", namespaces), "UNITA_MISURA")
            # scaglione di consumo a cui si applica lo sconto (0/0 = tutto il consumo)
            record[f"{pfx}_PREZZO_{j+1}_DA"] = get_text(ps, "ns:VALIDO_DA", namespaces)
            record[f"{pfx}_PREZZO_{j+1}_FINO"] = get_text(ps, "ns:VALIDO_FINO", namespaces)

    return record
