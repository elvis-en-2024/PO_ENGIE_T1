import logging
import pandas as pd
import numpy as np
import re
from datetime import date
from engine import component_matrix as cm
from engine import forward
from engine import parametri_po
from engine.arera_tariffs import AreraTariffs

ISTAT_REGIONI = {
    'Piemonte': '01', "Valle d'Aosta": '02', 'Lombardia': '03',
    'Trentino-Alto Adige': '04', 'Veneto': '05', 'Friuli-Venezia Giulia': '06',
    'Liguria': '07', 'Emilia-Romagna': '08', 'Toscana': '09', 'Umbria': '10',
    'Marche': '11', 'Lazio': '12', 'Abruzzo': '13', 'Molise': '14',
    'Campania': '15', 'Puglia': '16', 'Basilicata': '17', 'Calabria': '18',
    'Sicilia': '19', 'Sardegna': '20',
}

# Province ISTAT (3 cifre) per regione: servono a capire se un'offerta
# limitata a province o comuni è disponibile in una regione.
_PROVINCE_PER_REGIONE = {
    '01': '001 002 003 004 005 006 096 103', '02': '007',
    '03': '012 013 014 015 016 017 018 019 020 097 098 108', '04': '021 022',
    '05': '023 024 025 026 027 028 029', '06': '030 031 032 093',
    '07': '008 009 010 011', '08': '033 034 035 036 037 038 039 040 099',
    '09': '045 046 047 048 049 050 051 052 053 100', '10': '054 055',
    '11': '041 042 043 044 109', '12': '056 057 058 059 060',
    '13': '066 067 068 069', '14': '070 094', '15': '061 062 063 064 065',
    '16': '071 072 073 074 075 110', '17': '076 077',
    '18': '078 079 080 101 102', '19': '081 082 083 084 085 086 087 088 089',
    '20': '090 091 092 095 104 105 106 107 111 112 113 114 115 116 117 118',
}
REGIONE_DI_PROVINCIA = {p: r for r, ps in _PROVINCE_PER_REGIONE.items() for p in ps.split()}


class FastSASCalculator:
    def __init__(self, df: pd.DataFrame, arera: AreraTariffs = None,
                 tariffs_path: str = None, parametri='auto'):
        """
        arera:         istanza gia costruita (usata dai test / da chi orchestra).
        tariffs_path:  path alternativo al JSON tariffe.
        Se entrambi None -> comportamento storico (path di default).
        parametri:     {'E': dict, 'G': dict} dei parametri del Portale
                       (engine.parametri_po) per la parte regolata. 'auto' =
                       ultimi file scaricati, solo se arera/tariffs_path non
                       sono indicati; None = solo JSON.
        """
        self.df = df.copy()
        produzione = parametri == 'auto' and arera is None and tariffs_path is None
        if parametri == 'auto':
            parametri = ({c: parametri_po.carica(c) for c in ('E', 'G')}
                         if produzione else None)
        self.parametri = parametri or {}
        # imposte gas per regione rilevate dal Portale; altrimenti dal JSON
        self.imposte_gas = parametri_po.carica_imposte_gas() if produzione else {}
        # offerte variabili: forward GME con le regole del Portale; altrimenti
        # stime PUN/PSV del JSON. PPE e CCR rilevati dal dettaglio offerta.
        self.oggi = date.today()
        self.forward = forward.stima(self.oggi) if produzione else None
        self.componenti = forward.carica_componenti() if produzione else {}
        if arera is not None:
            self.arera = arera
        elif tariffs_path is not None:
            self.arera = AreraTariffs(tariffs_path)
        else:
            # con i parametri del Portale del trimestre corrente il JSON serve
            # solo per stime PUN/PSV e imposte gas: niente blocco trimestrale
            oggi = date.today()
            aggiornati = all(p and parametri_po.stesso_trimestre(p['_data'], oggi)
                             for p in (self.parametri.get('E'), self.parametri.get('G')))
            self.arera = AreraTariffs(verifica_trimestre=not aggiornati)
        
    _SEPARATORI = re.compile(r"[,;/|]")

    _CODICI = {
        'TIPO_OFFERTA': {'fisso': '01', 'variabile': '02', 'flat': '03', 'mista': '04'},
        'TIPO_CLIENTE': {'domestico': '01', 'altri usi': '02',
                         'condominio uso domestico (gas)': '03',
                         'condominio uso domestico': '03'},
    }

    def _match_multivalore(self, serie: pd.Series, atteso: str, campo: str) -> pd.Series:
        att = atteso.strip().casefold()
        cod = self._CODICI.get(campo, {}).get(att)
        ammessi = {att} | ({cod} if cod else set())

        if serie.empty:
            # Una Series vuota di dtype object usata come maschera viene
            # interpretata da pandas come lista di colonne: forzare bool.
            return pd.Series(False, index=serie.index, dtype=bool)
        tokens = (serie.astype(str)
                  .str.casefold()
                  .str.split(self._SEPARATORI)
                  .apply(lambda xs: {t.strip() for t in xs if t.strip()}
                         if isinstance(xs, list) else set()))
        return tokens.apply(lambda s: bool(s & ammessi)).astype(bool)

    _NULLI = {'', 'nan', 'none', 'null', '<na>'}

    @classmethod
    def _token_zona(cls, f: pd.DataFrame, col: str) -> pd.Series:
        if col not in f.columns:
            return pd.Series([frozenset()] * len(f), index=f.index)
        return f[col].apply(lambda v: frozenset() if pd.isna(v) else frozenset(
            t.strip() for t in str(v).split('|') if t.strip().casefold() not in cls._NULLI))

    def _disponibile_in_zona(self, f: pd.DataFrame, regione=None, provincia=None,
                             comune=None) -> pd.Series:
        """Le zone dell'offerta si sommano: vale in tutte le regioni, province
        e comuni elencati (es. due regioni più qualche comune di una terza).
        Nazionale solo se REGIONE, PROVINCIA e COMUNE sono tutti vuoti.
        Con il solo filtro regione basta che l'offerta copra una parte della
        regione."""
        com = str(comune).zfill(6) if comune else None
        prov = str(provincia).zfill(3) if provincia else (com[:3] if com else None)
        reg = ISTAT_REGIONI.get(regione) if regione else REGIONE_DI_PROVINCIA.get(prov)

        def ok(r, p, c):
            if not (r or p or c):
                return True
            if reg in r:
                return True
            if com:
                return com in c or prov in p
            if prov:
                return prov in p or any(x[:3] == prov for x in c)
            return (any(REGIONE_DI_PROVINCIA.get(x) == reg for x in p)
                    or any(REGIONE_DI_PROVINCIA.get(x[:3]) == reg for x in c))

        zone = zip(*(self._token_zona(f, c) for c in ('REGIONE', 'PROVINCIA', 'COMUNE')))
        return pd.Series([ok(*z) for z in zone], index=f.index, dtype=bool)

    def filter_offers(self, commodity='E', tipo_offerta='Fisso',
                      tipo_cliente='Domestico', fasce='A Fasce',
                      regione='Lombardia', provincia='015', comune=None,
                      consumo_annuo=None,
                      falsa_multioraria='escludi',
                      richiedi_prezzo_energia=True,
                      macroaree_energia=None,
                      tol_multiorario=1e-6,
                      solo_offerte_singole=True,
                      potenza=None, residente=None):
        import logging
        logger = logging.getLogger(__name__)

        if falsa_multioraria not in ('escludi', 'riclassifica', 'mantieni'):
            raise ValueError(f"falsa_multioraria non valido: {falsa_multioraria!r}")

        f = self.df
        n0 = len(f)
        self.diagnostica_esclusioni = {}
        self._offerte_scartate = None

        def _drop(mask_keep, etichetta):
            nonlocal f
            prima = len(f)
            f = f[mask_keep]
            persi = prima - len(f)
            if persi:
                self.diagnostica_esclusioni[etichetta] = persi
            return f

        _drop(f['commodity'] == commodity, 'commodity')

        if tipo_offerta and tipo_offerta != 'Tutte':
            _drop(self._match_multivalore(f['TIPO_OFFERTA'], tipo_offerta, 'TIPO_OFFERTA'),
                  f'tipo_offerta={tipo_offerta}')

        if tipo_cliente and tipo_cliente != 'Tutti':
            _drop(self._match_multivalore(f['TIPO_CLIENTE'], tipo_cliente, 'TIPO_CLIENTE'),
                  f'tipo_cliente={tipo_cliente}')

        regione = None if regione == 'Tutte' else regione
        if regione and regione not in ISTAT_REGIONI:
            raise KeyError(f"Regione '{regione}' non mappata sui codici ISTAT.")
        if regione or provincia or comune:
            etichetta = f"zona={'/'.join(str(x) for x in (regione, provincia, comune) if x)}"
            _drop(self._disponibile_in_zona(f, regione, provincia, comune), etichetta)

        _drop(~f['NOME_OFFERTA'].astype(str).str.contains('Sottocosto', case=False, na=False),
              'nome_sottocosto')

        if solo_offerte_singole and 'OFFERTA_SINGOLA' in f.columns:
            # OFFERTA_SINGOLA=NO: sottoscrivibile solo insieme all'altra commodity
            _drop(f['OFFERTA_SINGOLA'].astype(str).str.strip().str.upper() != 'NO',
                  'offerta_non_singola')

        # limiti dichiarati dall'offerta (vuoto = nessun limite)
        def _entro(col_min, col_max, valore):
            lo = pd.to_numeric(f.get(col_min), errors='coerce') if col_min in f.columns else None
            hi = pd.to_numeric(f.get(col_max), errors='coerce') if col_max in f.columns else None
            ok = pd.Series(True, index=f.index)
            if lo is not None:
                ok &= lo.isna() | (lo <= valore)
            if hi is not None:
                ok &= hi.isna() | (hi <= 0) | (valore <= hi)
            return ok

        if consumo_annuo is not None:
            _drop(_entro('CONSUMO_MIN', 'CONSUMO_MAX', consumo_annuo), 'limiti_consumo')
        if potenza is not None and commodity == 'E':
            _drop(_entro('POTENZA_MIN', 'POTENZA_MAX', potenza), 'limiti_potenza')
        if residente is not None and 'DOMESTICO_RESIDENTE' in f.columns:
            escluso = 'NON Residente' if residente else 'Residente'
            _drop(f['DOMESTICO_RESIDENTE'].astype(str).str.strip() != escluso,
                  'domestico_residente')

        if f.empty:
            return f

        long = cm.build_long(f, consumo_annuo=consumo_annuo)
        flags_mo = cm.multiorario_flags(f, long=long, tol=tol_multiorario)
        self.ultima_price_matrix = cm.price_matrix(f, long=long)
        self.ultimi_flags_multiorario = flags_mo

        if commodity == 'E' and fasce and fasce != 'Tutte' and 'TIPOLOGIA_FASCE' in f.columns:
            tipol = f['TIPOLOGIA_FASCE'].astype(str).map(cm._norm)
            dichiarata_mono = tipol.isin(cm._TIPOLOGIE_MONO)
            falsa = flags_mo['falsa_multioraria'].reindex(f.index).fillna(False)

            if fasce in ('A Fasce', 'Biorario', 'Multiorario'):
                if falsa_multioraria in ('escludi', 'riclassifica'):
                    keep = ~dichiarata_mono & ~falsa
                else:
                    # come il Portale (verificato 01/10/2026): nella ricerca a fasce
                    # niente monorarie dichiarate, ma le false multiorarie restano
                    keep = ~dichiarata_mono
                if fasce == 'Biorario':
                    # 'F1, F2, F3' è trioraria, non entra nel ranking biorario
                    keep &= tipol.str.contains('biorario', regex=False)
                _drop(keep, f'fasce={fasce}')
            elif fasce == 'Monorario':
                keep = dichiarata_mono.copy()
                if falsa_multioraria == 'riclassifica':
                    keep |= falsa
                _drop(keep, 'fasce=Monorario')
            else:
                raise ValueError(f"Valore 'fasce' non gestito: {fasce!r}")

            if falsa_multioraria != 'mantieni':
                self.diagnostica_esclusioni['false_multiorarie'] = int(falsa.sum())

        if richiedi_prezzo_energia and not f.empty:
            en = cm.energia_flags(f, long=long, macroaree_energia=macroaree_energia,
                                  consumo_annuo=consumo_annuo)
            en = en.reindex(f.index)
            ko = ~en['prezzo_energia_ok'].fillna(False)
            # offerte variabili: l'energia è l'indice (PUN/PSV), in XML c'è solo lo spread
            ko &= ~f['TIPO_OFFERTA'].astype(str).str.contains('variabile', case=False, na=False)
            if ko.any():
                col_cod = 'CODICE_OFFERTA' if 'CODICE_OFFERTA' in f.columns else 'COD_OFFERTA'
                self._offerte_scartate = pd.DataFrame({
                    'COD_OFFERTA': f.loc[ko, col_cod],
                    'NOME_OFFERTA': f.loc[ko, 'NOME_OFFERTA'],
                    'prezzo_volumetrico': en.loc[ko, 'prezzo_volumetrico_totale'].round(5),
                    'soglia': en.loc[ko, 'soglia_applicata'].round(5),
                    'motivo': en.loc[ko, 'motivo'],
                })
                logger.warning(
                    "%d offerte senza prezzo energia identificabile.",
                    int(ko.sum())
                )
            _drop(~ko, 'prezzo_energia_assente')
            self.ultimi_flags_energia = en

        if n0 and len(f) / n0 < 0.02:
            logger.error(
                "filter_offers ha ridotto %d offerte a %d (%.2f%%). "
                "Esclusioni per filtro: %s.",
                n0, len(f), 100 * len(f) / max(n0, 1), self.diagnostica_esclusioni,
            )
        if f.empty and n0:
            colpevole = max(self.diagnostica_esclusioni,
                            key=self.diagnostica_esclusioni.get)
            logger.error("Nessuna offerta superstite. Filtro più selettivo: '%s' "
                         "(%d escluse).", colpevole, self.diagnostica_esclusioni[colpevole])

        logger.info("filter_offers: %d -> %d offerte. Esclusioni: %s",
                    n0, len(f), self.diagnostica_esclusioni)
        return f

    @property
    def offerte_scartate(self) -> pd.DataFrame:
        return getattr(self, '_offerte_scartate', None)

    def _costi_componenti(self, df: pd.DataFrame, consumi: dict, potenza,
                          perdite_da_aggiungere: np.ndarray):
        """Quote fisse e volumetriche annue delle ComponenteImpresa.

        Usa la stessa vista long dei filtri (component_matrix): un prezzo per
        (componente, fascia), scaglione scelto sul consumo annuo. Le fasce non
        risolvibili (F4-F6, Peak) si applicano all'intero consumo.
        """
        cons = {b: float(consumi.get(b, 0) or 0) for b in cm.BANDE}
        tot = sum(cons.values())
        n = len(df)
        fix, vol = np.zeros(n), np.zeros(n)

        long = cm.build_long(df.reset_index(drop=True), consumo_annuo=tot)
        if long.empty:
            return fix, vol
        rows = long['row'].to_numpy(dtype=int)
        prezzo = long['prezzo'].to_numpy(dtype=float)
        kind = long['kind'].to_numpy()

        is_kwh = kind == cm.KIND_KWH
        prezzo = np.where(is_kwh & perdite_da_aggiungere[rows],
                          prezzo * (1 + self.arera.PARAMETRI['perdite_rete_ee']), prezzo)

        bande = [cm.resolve_bande(f, t) for f, t in
                 zip(long['fascia'], long['tipologia_fasce'])]
        cons_kwh = np.array([sum(cons[b] for b in bb) if bb else tot for bb in bande])
        quota_vol = np.select([is_kwh, kind == cm.KIND_SMC], [cons_kwh, tot], 0.0)
        quota_fix = np.select([kind == cm.KIND_FISSO, kind == cm.KIND_KW],
                              [1.0, float(potenza or 0.0)], 0.0)

        np.add.at(vol, rows, prezzo * quota_vol)
        np.add.at(fix, rows, prezzo * quota_fix)
        return fix, vol

    @staticmethod
    def _coefficiente_indici(df: pd.DataFrame) -> np.ndarray:
        """Somma dei COEFFICIENTE degli indici dichiarati (RiferimentiPrezzoEnergia).
        Tutti gli indici di una commodity usano lo stesso forward; coefficiente
        assente = 1, nessun indice dichiarato = 1."""
        tot = np.zeros(len(df))
        for col in df.columns:
            if not col.startswith('IDX_') or col.endswith('_COEFF'):
                continue
            dichiarato = df[col].astype(str).str.strip().str.lower().isin(['true', '1']).to_numpy()
            c = pd.to_numeric(df.get(f'{col}_COEFF', pd.Series([None]*len(df))).astype(str)
                              .str.replace(',', '.'), errors='coerce').fillna(1.0).to_numpy()
            tot += np.where(dichiarato, c, 0.0)
        return np.where(tot > 0, tot, 1.0)

    def calculate_sas(self, filtered_df: pd.DataFrame, consumi: dict, potenza: float,
                      is_dual_fuel: bool = False, is_domiciliazione: bool = False, 
                      regione: str = 'Lombardia', residente: bool = True,
                      is_bolletta_web: bool = False):

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
        sconti_post_iva = np.zeros(len(df))
        sconti_pre_iva = np.zeros(len(df))

        is_ee = (df['commodity'] == 'E').to_numpy()
        is_gas = (df['commodity'] == 'G').to_numpy()
        
        comprensivo_s = df.get('PREZZO_COMPRENSIVO_PERDITE_RETE', pd.Series(['SI']*len(df))).fillna('SI').astype(str).str.strip().str.upper()
        comprensivo = np.where(comprensivo_s.isin(['NAN', 'nan', '<NA>', 'NONE', '']), 'SI', comprensivo_s)
        
        tipo_offerta_variabile = df.get('TIPO_OFFERTA', pd.Series(['Fisso']*len(df))).astype(str).str.strip().str.lower().str.contains('variabile').to_numpy()
        
        # variabili con i forward: perdite solo sul forward, lo spread le
        # comprende già (Regole per il calcolo della spesa, rev. 3.01)
        perdite_comp = is_ee & (comprensivo != 'SI')
        if self.forward:
            perdite_comp &= ~tipo_offerta_variabile
        fix_comp, vol_comp = self._costi_componenti(
            df, consumi, potenza, perdite_da_aggiungere=perdite_comp)
        costo_fix += fix_comp
        costo_vol += vol_comp

        for s in range(1, 16):
            nome_sconto_col = f'SCONTO_{s}_NOME'
            if nome_sconto_col not in df.columns:
                continue
                
            has_sconto = df[nome_sconto_col].notna().to_numpy()
            cond_app = df.get(f'SCONTO_{s}_COND_APP', pd.Series(['']*len(df))).astype(str).str.strip().to_numpy()
            codice_comp = df.get(f'SCONTO_{s}_CODICE_COMP', pd.Series(['']*len(df))).astype(str).to_numpy()
            validita = df.get(f'SCONTO_{s}_VALIDITA', pd.Series(['']*len(df))).fillna('').astype(str).to_numpy()
            
            applica_sconto = has_sconto.copy()
            applica_sconto &= ~((cond_app == 'Altro') & (not is_dual_fuel))

            cond_s = pd.Series(cond_app).str.lower()
            cond_sdd_mask = cond_s.str.contains('sdd|domiciliazione|rid|conto corrente', na=False).to_numpy()
            applica_sconto &= ~(cond_sdd_mask & (not is_domiciliazione))
            # come il Portale: sconti per bolletta elettronica solo se richiesta
            cond_web_mask = cond_s.str.contains('fatturazione elettronica|bolletta web', na=False).to_numpy()
            applica_sconto &= ~(cond_web_mask & (not is_bolletta_web))
            
            val_ok = np.isin(validita, ['Ingresso', 'entro 12 mesi', 'nan', '', 'None', 'Sempre'])
            applica_sconto &= val_ok
            # IVA_SCONTO = NO: il Portale sottrae lo sconto dalla spesa già ivata
            iva_no = (df.get(f'SCONTO_{s}_IVA', pd.Series(['']*len(df))).astype(str)
                      .str.strip().str.upper() == 'NO').to_numpy()
            # sconto applicato per DURATA mesi: quota dell'anno (consumi uniformi)
            durata = pd.to_numeric(df.get(f'SCONTO_{s}_DURATA', pd.Series([None]*len(df))),
                                   errors='coerce').to_numpy(dtype=float)
            quota_anno = np.where(durata > 0, np.minimum(durata, 12) / 12, 1.0)

            for p in range(1, 6):
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
                sc_fix = np.where(sconto_attivo & (is_anno | is_fisso), s_val, 0)

                # consumo a cui si applica lo sconto: fascia indicata, poi
                # scaglione VALIDO_DA..VALIDO_FINO (0/0 = nessun limite)
                q = np.select([codice_comp == 'F1', codice_comp == 'F2', codice_comp == 'F3',
                               codice_comp == 'F2+F3'], [F1, F2, F3, F23], TOT_CONS).astype(float)
                da = pd.to_numeric(df.get(f'SCONTO_{s}_PREZZO_{p}_DA', pd.Series([None]*len(df))),
                                   errors='coerce').fillna(0).to_numpy()
                fino = pd.to_numeric(df.get(f'SCONTO_{s}_PREZZO_{p}_FINO', pd.Series([None]*len(df))),
                                     errors='coerce').fillna(0).to_numpy()
                q = np.where(fino > 0, np.clip(np.minimum(q, fino) - da, 0, None), q)

                is_kwh = s_unita_s.str.contains('kWh').fillna(False).to_numpy()
                is_smc = s_unita_s.str.contains('Smc').fillna(False).to_numpy()
                sc_vol = np.where(sconto_attivo & (is_kwh | is_smc), s_val * q, 0)

                # percentuale sulle componenti volumetriche dell'offerta
                is_perc = (s_unita_s.str.strip().str.lower() == 'percentuale').to_numpy() & (s_tipo == 'Sconto Vendita')
                sc_vol = sc_vol + np.where(sconto_attivo & is_perc, s_val / 100 * vol_comp, 0)
                sc_vol = sc_vol * quota_anno
                sc_fix = np.where(is_anno, sc_fix * quota_anno, sc_fix)  # una tantum intero

                costo_fix -= np.where(iva_no, 0, sc_fix)
                costo_vol -= np.where(iva_no, 0, sc_vol)
                sconti_pre_iva += np.where(iva_no, 0, sc_fix + sc_vol)
                sconti_post_iva += np.where(iva_no, sc_fix + sc_vol, 0)

        ele_conf = self.arera.ELE['residente' if residente else 'non_residente']
        par = self.arera.PARAMETRI
        par_e = self.parametri.get('E')
        par_g = self.parametri.get('G')
        cdispd_def = par_e['cdispd'] if par_e else ele_conf['cdispd']
        dispbt_fix = par_e['dispbt_d'] if par_e else par['dispbt']
        perdite = par_e['lambda'] if par_e else par['perdite_rete_ee']

        cdispd_col = df.get('DISP_CdispD_VALORE', pd.Series([cdispd_def]*len(df))).astype(str).str.replace(',', '.')
        cdispd = pd.to_numeric(cdispd_col, errors='coerce').fillna(cdispd_def).to_numpy()
        # valore dichiarato 0 = non indicato: il Portale applica il proprio CdispD
        cdispd = np.where(cdispd > 0, cdispd, cdispd_def)

        pun_base = par['pun_stima']
        pun_effettivo = np.where(comprensivo != 'SI', pun_base * (1 + perdite), pun_base)

        def _dichiarata(voce, default):
            # con pandas 3 astype(str) lascia NaN i mancanti: vuoto = non dichiarata
            s = df.get(f'DISP_{voce}', pd.Series([default]*len(df))).fillna('').astype(str).str.strip().str.lower()
            return ~s.isin(['false', '0', 'no', 'f', 'nan', 'none', '', '<na>']).to_numpy()

        disp_dispbt = _dichiarata('DispBT', True)
        if par_e:
            # ogni voce di dispacciamento dichiarata, al valore dell'offerta o del Portale
            voci = {}
            for voce in parametri_po.VOCI_DISP_KWH:
                valore = pd.to_numeric(
                    df.get(f'DISP_{voce}_VALORE', pd.Series([None]*len(df))).astype(str)
                    .str.replace(',', '.'), errors='coerce').to_numpy(dtype=float)
                voci[voce] = (_dichiarata(voce, voce == 'CdispD'), valore)
            disp = parametri_po.dispacciamento_ele(par_e, TOT_CONS, voci)
            costo_vol += np.where(is_ee, disp, 0)
        else:
            disp_cdispd = _dichiarata('CdispD', True)
            costo_vol += np.where(is_ee & disp_cdispd, cdispd * TOT_CONS, 0)
        costo_fix += np.where(is_ee & disp_dispbt, dispbt_fix, 0)

        # ComponentiRegolate dichiarate dall'offerta: il Portale le somma alla
        # vendita (PCV dai suoi parametri; PPE non pubblicato, da configurare)
        def _regolata(nome):
            s = df.get(f'REGOLATA_{nome}', pd.Series([False]*len(df)))
            return s.astype(str).str.strip().str.lower().isin(['true', '1']).to_numpy()

        if par_e:
            altri_usi = df.get('TIPO_CLIENTE', pd.Series(['']*len(df))).astype(str) \
                .str.contains('altri usi', case=False).to_numpy()
            pcv = np.where(altri_usi, par_e['pcv_a'], par_e['pcv_c'])
            costo_fix += np.where(is_ee & _regolata('PCV'), pcv, 0)
        regolata_ppe = is_ee & _regolata('PPE')
        if regolata_ppe.any():
            ppe = self.componenti.get('ppe', par.get('ppe'))
            if ppe is None:
                logging.getLogger(__name__).warning("PPE non rilevato (scripts/rileva_componenti_portale.py): "
                               "%d offerte senza la componente", regolata_ppe.sum())
            else:
                costo_vol += np.where(regolata_ppe, ppe * TOT_CONS, 0)
        if par_g:
            costo_fix += np.where(is_gas & _regolata('QVD_Fissa'), par_g['qvd_f_d'], 0)
            for nome, valore in (('QVD_Variabile', par_g['qvd_v_d']), ('CPR', par_g['cpr']),
                                 ('GRAD', par_g['grad']),
                                 # a zero nel dettaglio offerta del Portale (01/10/2026)
                                 ('QTint', par.get('qtint', 0.0)), ('QTpsv', par.get('qtpsv', 0.0))):
                costo_vol += np.where(is_gas & _regolata(nome), valore * TOT_CONS, 0)
        # consumi gas mese per mese del periodo di stima (profili del Portale)
        quote_mesi = forward.profilo_gas(regione, self.oggi)
        regolata_ccr = is_gas & _regolata('CCR')
        if regolata_ccr.any():
            ccr_trim = forward.ccr_trimestri(self.componenti, self.oggi)
            ccr = forward.pesa_trimestri(ccr_trim, quote_mesi) if ccr_trim else par.get('ccr')
            if ccr is None:
                logging.getLogger(__name__).warning("CCR non rilevato (scripts/rileva_componenti_portale.py): "
                                                    "%d offerte senza la componente", regolata_ccr.sum())
            else:
                costo_vol += np.where(regolata_ccr, ccr * TOT_CONS, 0)

        if self.forward:
            # Regole del Portale: media forward dei 4 trimestri x (1 + lambda),
            # F0 per le monorarie, F1 e F23 per le offerte a fasce; gas mese
            # per mese sul profilo. Ogni indice dichiarato pesa il suo coefficiente.
            fwd = self.forward['ee']
            mono = df.get('TIPOLOGIA_FASCE', pd.Series(['']*len(df))).astype(str) \
                .str.contains('onorari', case=False, na=False).to_numpy(dtype=bool)
            spesa_pun = np.where(mono, fwd['F0'] * TOT_CONS,
                                 fwd['F1'] * F1 + fwd['F23'] * F23) * (1 + perdite)
            spesa_psv = sum(w * p for w, p in zip(quote_mesi, self.forward['gas_mesi'])) * TOT_CONS
            coeff = self._coefficiente_indici(df)
            costo_vol += np.where(is_ee & tipo_offerta_variabile, coeff * spesa_pun, 0)
            costo_vol += np.where(is_gas & tipo_offerta_variabile, coeff * spesa_psv, 0)
        else:
            costo_vol += np.where(is_ee & tipo_offerta_variabile, pun_effettivo * TOT_CONS, 0)
            costo_vol += np.where(is_gas & tipo_offerta_variabile, par['psv_stima'] * TOT_CONS, 0)

        p_val = potenza if potenza is not None else 0.0
        costo_venditore = costo_fix + costo_vol

        if par_e:
            # reti, oneri e accisa come il Portale (accisa con soglie mensili)
            voci_ee = parametri_po.voci_ele(par_e, TOT_CONS, p_val, residente)
            regolati_ee = sum(voci_ee.values())
            iva_ee = par_e['iva_c']
        else:
            tot_reti_oneri_ele = (
                ele_conf['dist_fix'] + ele_conf['oneri_fix'] +
                (ele_conf['trasp_pot'] + ele_conf['oneri_pot']) * p_val +
                (ele_conf['trasp_vol'] + ele_conf['oneri_vol']) * TOT_CONS
            )
            if residente and p_val <= 3.0:
                accisa_ee = par['accisa_ee'] * np.maximum(0, TOT_CONS - par['accisa_ee_franchigia'])
            else:
                accisa_ee = par['accisa_ee'] * TOT_CONS
            regolati_ee = tot_reti_oneri_ele + accisa_ee
            iva_ee = par['iva_ee']
            # JSON di riserva: rete e oneri non separabili
            voci_ee = {'rete': tot_reti_oneri_ele, 'oneri': 0.0, 'imposte': accisa_ee}

        imponibile_ee = costo_venditore + regolati_ee
        sas_ele = imponibile_ee * (1 + iva_ee)
        voci_gas = {'rete': 0.0, 'oneri': 0.0, 'imposte': 0.0}

        if par_g and regione in parametri_po.AMBITO_GAS_BY_REGIONE:
            # come il dettaglio offerta del Portale: IVA ridotta sui soli costi
            # volumetrici (imposte comprese) dei primi 480 Smc, ordinaria sulle
            # quote fisse e sul resto
            entro = min(TOT_CONS, parametri_po.SOGLIA_IVA_GAS)
            if regione in self.imposte_gas:
                al = self.imposte_gas[regione]
                imposte = lambda c: (parametri_po.importo_tiers(al['accisa'], c)
                                     + parametri_po.importo_tiers(al['addizionale'], c))
            else:
                _, territorio = self.arera.resolve_zona_gas(regione, strict=False)
                add = self.arera.GAS_ADDIZIONALE.get(regione, self.arera.GAS_ADDIZIONALE["DEFAULT"])
                imposte = lambda c: c * (self.arera.get_gas_accisa_avg(territorio, c) + add)
            fisso = costo_fix + parametri_po.regolati_gas_fisso(par_g, regione)
            vol = costo_vol + parametri_po.regolati_gas_vol(par_g, regione, TOT_CONS) + imposte(TOT_CONS)
            vol_ridotta = (costo_vol * (entro / TOT_CONS if TOT_CONS > 0 else 0)
                           + parametri_po.regolati_gas_vol(par_g, regione, entro) + imposte(entro))
            iva_rid, iva_ord = par_g['iva_f1'], par_g['iva_f3']
            sas_gas = (fisso * (1 + iva_ord) + vol_ridotta * (1 + iva_rid)
                       + (vol - vol_ridotta) * (1 + iva_ord))
            vg = parametri_po.voci_gas(par_g, regione, TOT_CONS)
            voci_gas = {'rete': vg['rete_fisso'] + vg['rete_vol'],
                        'oneri': vg['oneri_fisso'] + vg['oneri_vol'],
                        'imposte': imposte(TOT_CONS)}
        else:
            gas_fix_arera, gas_vol_arera = self.arera.get_gas_costi_regolati(regione, TOT_CONS, include_taxes=True, strict=False)
            tot_arera_gas = gas_fix_arera + (gas_vol_arera * TOT_CONS)
            imponibile_gas = costo_fix + costo_vol + tot_arera_gas
            sas_gas = imponibile_gas * (1 + self.arera.get_iva_gas(TOT_CONS))
            voci_gas = {'rete': tot_arera_gas, 'oneri': 0.0, 'imposte': 0.0}

        sas_lorda = np.where(is_ee, sas_ele, sas_gas)
        sas_finale = sas_lorda - sconti_post_iva

        # composizione della spesa come nel dettaglio offerta del Portale
        voce = lambda k: np.where(is_ee, voci_ee[k], voci_gas[k])
        df['VENDITA'] = np.round(costo_venditore + sconti_pre_iva, 2)
        df['SCONTI'] = np.round(-sconti_pre_iva, 2)            # soggetti a IVA
        df['SCONTI_NO_IVA'] = np.round(-sconti_post_iva, 2)    # sottratti dopo l'IVA
        df['RETE'] = np.round(voce('rete'), 2)
        df['ONERI'] = np.round(voce('oneri'), 2)
        df['IMPOSTE'] = np.round(voce('imposte'), 2)
        df['IVA'] = np.round(sas_lorda - costo_venditore - voce('rete') - voce('oneri') - voce('imposte'), 2)
        df['SPESA_MATERIA_PRIMA'] = np.round(costo_venditore, 2)
        df['QUOTA_FISSA'] = np.round(costo_fix, 2)
        df['PREZZO_UNITARIO'] = np.where(TOT_CONS > 0, np.round(costo_vol / max(TOT_CONS, 1), 4), 0.0)
        df['SAS'] = np.round(sas_finale, 2)

        col_piva = 'PIVA_UTENTE' if 'PIVA_UTENTE' in df.columns else 'PIVA_VENDITORE'
        col_cod = 'CODICE_OFFERTA' if 'CODICE_OFFERTA' in df.columns else 'COD_OFFERTA'

        out_cols = [col_piva, col_cod, 'NOME_OFFERTA', 'SPESA_MATERIA_PRIMA', 'QUOTA_FISSA', 'PREZZO_UNITARIO', 'SAS',
                    'VENDITA', 'SCONTI', 'RETE', 'ONERI', 'IMPOSTE', 'IVA', 'SCONTI_NO_IVA']
        
        if 'COND_Attivazione_LIMITANTE' in df.columns: out_cols.append('COND_Attivazione_LIMITANTE')
        if 'COND_Pluriennale_LIMITANTE' in df.columns: out_cols.append('COND_Pluriennale_LIMITANTE')
            
        res_df = df[out_cols].copy()
        res_df = res_df.rename(columns={col_piva: 'PIVA_VENDITORE', col_cod: 'COD_OFFERTA'})
        
        if len(res_df) > 0:
            res_df = res_df.sort_values('SAS').reset_index(drop=True)
            
        return res_df
