import json
import os
import logging
import unicodedata
import warnings
from datetime import datetime


class UnknownRegionError(ValueError):
    """Regione non presente nella mappatura zone gas / territori accisa."""


def _norm_regione(nome: str) -> str:
    """Normalizza il nome regione: accenti, apostrofi, trattini, case, spazi."""
    s = unicodedata.normalize("NFKD", str(nome)).encode("ascii", "ignore").decode()
    s = s.lower().replace("'", " ").replace("\u2019", " ").replace("-", " ")
    return " ".join(s.split())


# Zone tariffarie gas ARERA (6 zone) — copertura completa 20 regioni
GAS_ZONE_BY_REGIONE = {
    "valle d aosta":          "Nord Occidentale",
    "piemonte":               "Nord Occidentale",
    "liguria":                "Nord Occidentale",
    "lombardia":              "Nord Occidentale",
    "trentino alto adige":    "Nord Orientale",
    "veneto":                 "Nord Orientale",
    "friuli venezia giulia":  "Nord Orientale",
    "emilia romagna":         "Nord Orientale",
    "toscana":                "Centrale",
    "umbria":                 "Centrale",
    "marche":                 "Centrale",
    "abruzzo":                "Centro-Sud Orientale",
    "molise":                 "Centro-Sud Orientale",
    "puglia":                 "Centro-Sud Orientale",
    "basilicata":             "Centro-Sud Orientale",
    "lazio":                  "Centro-Sud Occidentale",
    "campania":               "Centro-Sud Occidentale",
    "calabria":               "Meridionale",
    "sicilia":                "Meridionale",
    # Sardegna: storicamente esclusa dalle zone metano ARERA (rete in sviluppo).
    # Convenzione di progetto: assimilata a Meridionale. Da rivedere se si
    # gestiscono forniture GNL/aria propanata.
    "sardegna":               "Meridionale",
}

# Territorio ai fini dell'accisa sul gas naturale per uso civile.
# "Sud" = territori ex art. 1 DPR 218/1978 (aliquote ridotte).
#
# ATTENZIONE — semplificazione nota: il Lazio è incluso nell'art. 1 solo per
# le province di Latina e Frosinone e per alcuni comuni. Qui è classificato
# "Nord" (aliquota piena). La versione precedente del codice lo mappava a
# "Sud", sottostimando l'accisa sulla maggior parte del territorio regionale.
ACCISA_TERRITORIO_BY_REGIONE = {
    "valle d aosta": "Nord", "piemonte": "Nord", "liguria": "Nord",
    "lombardia": "Nord", "trentino alto adige": "Nord", "veneto": "Nord",
    "friuli venezia giulia": "Nord", "emilia romagna": "Nord",
    "toscana": "Nord", "umbria": "Nord", "marche": "Nord", "lazio": "Nord",
    "abruzzo": "Sud", "molise": "Sud", "campania": "Sud", "puglia": "Sud",
    "basilicata": "Sud", "calabria": "Sud", "sicilia": "Sud", "sardegna": "Sud",
}

# Limite minimo che deve avere l'ultimo scaglione di uno schema a tiers
# perché il volume residuo non venga silenziosamente perso.
OPEN_TIER_MIN_LIMIT = 1_000_000

# Parametri di stima usati dalla SAS. Valori di default = costanti storiche
# del calcolatore; vanno sovrascritti dalla sezione PARAMETRI del JSON a ogni
# aggiornamento trimestrale.
PARAMETRI_DEFAULT = {
    "pun_stima": 0.15704,        # €/kWh, prezzo energia per offerte variabili EE
    "psv_stima": 0.606612,       # €/Smc, prezzo gas per offerte variabili gas
    "dispbt": -10.7718,          # €/anno, componente DispBT (domestico BT)
    "accisa_ee": 0.0227,         # €/kWh
    "accisa_ee_franchigia": 1800,  # kWh esenti per residenti con potenza <= 3 kW
    "iva_ee": 0.10,
    "iva_gas_soglie": [[480, 0.10], [OPEN_TIER_MIN_LIMIT * 1000, 0.22]],
    "perdite_rete_ee": 0.10,     # maggiorazione prezzi energia non comprensivi di perdite
}


class AreraTariffs:
    def __init__(self, config_path="data/config/arera_tariffs.json", verifica_trimestre=True):
        """verifica_trimestre=False declassa a warning il blocco sulle tariffe
        di un trimestre passato (usato quando la parte regolata arriva dai
        parametri giornalieri del Portale)."""
        self._verifica_trimestre = verifica_trimestre
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
        self.PARAMETRI = {**PARAMETRI_DEFAULT, **data.get('PARAMETRI', {})}
        mancanti = set(PARAMETRI_DEFAULT) - set(data.get('PARAMETRI', {}))
        if mancanti:
            logging.warning("arera_tariffs: PARAMETRI non configurati, uso i "
                            "default storici per %s", sorted(mancanti))

        self.GAS_ZONES = {
            '01': 'Nord Occidentale',
            '02': 'Nord Orientale',
            '03': 'Centrale',
            '04': 'Centro-Sud Orientale',
            '05': 'Centro-Sud Occidentale',
            '06': 'Meridionale'
        }
        
        self._validate_tariffs()

    def _validate_tariffs(self):
        # 1. Verifica dell'aggiornamento temporale (Hard Stop)
        now = datetime.now()
        current_quarter = f"Q{(now.month - 1) // 3 + 1}"
        current_year = now.year
        
        val_q = self.metadata.get('validity_quarter')
        val_y = self.metadata.get('validity_year')
        
        if val_q != current_quarter or val_y != current_year:
            # Siamo in un trimestre diverso da quello configurato. Controlliamo il grace period (primi 5 giorni del mese)
            grace_period = 5
            is_new_quarter_start = (now.month - 1) % 3 == 0 and now.day <= grace_period
            
            error_msg = (
                f"\n{'='*60}\n"
                f"ERRORE CRITICO: Tariffe ARERA obsolete!\n"
                f"Il sistema si aspetta le tariffe per {current_quarter} {current_year}, "
                f"ma il file data/config/arera_tariffs.json è configurato per {val_q} {val_y}.\n"
                f"Aggiornare immediatamente il file JSON per evitare calcoli errati della Spesa Annua Stimata.\n"
                f"{'='*60}\n"
            )
            
            if not self._verifica_trimestre:
                logging.warning("arera_tariffs.json è del %s %s: parte regolata dai "
                                "parametri del Portale, dal JSON solo stime PUN/PSV e "
                                "imposte gas.", val_q, val_y)
            elif is_new_quarter_start:
                logging.warning(error_msg.replace("ERRORE CRITICO", "WARNING (GRACE PERIOD)"))
            else:
                raise ValueError(error_msg)

        # 2. Validazione formale dei parametri obbligatori
        required_ele_keys = ['dist_fix', 'oneri_fix', 'trasp_pot', 'oneri_pot', 'trasp_vol', 'oneri_vol', 'cdispd']
        for tipo in ['residente', 'non_residente']:
            if tipo not in self.ELE:
                raise ValueError(f"Manca la configurazione ELE per {tipo}")
            for key in required_ele_keys:
                val = self.ELE[tipo].get(key)
                if val is None or val < 0:
                    raise ValueError(f"Parametro ELE '{key}' per {tipo} mancante o negativo: {val}")
        
        for zona in self.GAS_ZONES.values():
            if zona not in self.GAS_FIX or self.GAS_FIX[zona] < 0:
                raise ValueError(f"Parametro GAS_FIX mancante o negativo per la zona: {zona}")
            if zona not in self.GAS_VOL:
                raise ValueError(f"Parametro GAS_VOL mancante per la zona: {zona}")

        # 3. Validazione schemi a scaglioni
        for nome_blocco, blocco in (("GAS_VOL", self.GAS_VOL),
                                    ("GAS_ACCISE", self.GAS_ACCISE)):
            for chiave, tiers in blocco.items():
                if isinstance(tiers, (float, int)):
                    continue
                limits = [t[0] for t in tiers]
                if limits != sorted(limits):
                    raise ValueError(
                        f"{nome_blocco}['{chiave}']: limiti non ordinati: {limits}"
                    )
                if limits[-1] < OPEN_TIER_MIN_LIMIT:
                    raise ValueError(
                        f"{nome_blocco}['{chiave}']: ultimo scaglione chiuso a "
                        f"{limits[-1]}. Consumi superiori non verrebbero tariffati. "
                        f"Impostare un limite >= {OPEN_TIER_MIN_LIMIT}."
                    )

        # 4. Copertura mappatura regioni
        zone_mancanti = set(GAS_ZONE_BY_REGIONE.values()) - set(self.GAS_FIX)
        if zone_mancanti:
            raise ValueError(f"Zone gas mappate ma assenti da GAS_FIX: {zone_mancanti}")

    def resolve_zona_gas(self, regione, strict=True):
        """Restituisce (zona_tariffaria, territorio_accisa) per la regione."""
        key = _norm_regione(regione)
        zona = GAS_ZONE_BY_REGIONE.get(key)
        territorio = ACCISA_TERRITORIO_BY_REGIONE.get(key)

        if zona is None or territorio is None:
            msg = (
                f"Regione '{regione}' (normalizzata: '{key}') non presente nella "
                f"mappatura zone gas. Regioni note: "
                f"{sorted(GAS_ZONE_BY_REGIONE)}"
            )
            if strict:
                raise UnknownRegionError(msg)
            warnings.warn(f"{msg} — fallback su Nord Occidentale / Nord",
                          RuntimeWarning, stacklevel=2)
            return "Nord Occidentale", "Nord"

        if zona not in self.GAS_FIX:
            raise KeyError(
                f"Zona '{zona}' (regione '{regione}') assente da GAS_FIX "
                f"nel file di configurazione ARERA."
            )
        return zona, territorio

    def get_gas_costi_regolati(self, regione, consumo_annuo,
                               include_taxes=True, strict=True):
        zona, territorio = self.resolve_zona_gas(regione, strict=strict)
        fix_arera = self.GAS_FIX[zona]
        vol_arera = self.get_gas_vol_avg(zona, consumo_annuo)
        if include_taxes:
            accisa = self.get_gas_accisa_avg(territorio, consumo_annuo)
            addizionale = self.GAS_ADDIZIONALE.get(
                regione, self.GAS_ADDIZIONALE["DEFAULT"]
            )
            return fix_arera, vol_arera + accisa + addizionale
        return fix_arera, vol_arera

    @staticmethod
    def _avg_from_tiers(tiers, consumo_annuo):
        """Media ponderata a scaglioni. Nessun fallback silenzioso."""
        if consumo_annuo <= 0:
            return 0.0
        if isinstance(tiers, (float, int)):
            return float(tiers)

        totale = 0.0
        rimanente = float(consumo_annuo)
        prev_limit = 0.0
        for limit, rate in tiers:
            scaglione = limit - prev_limit
            if rimanente > scaglione:
                totale += scaglione * rate
                rimanente -= scaglione
                prev_limit = limit
            else:
                totale += rimanente * rate
                rimanente = 0.0
                break

        if rimanente > 1e-9:
            raise ValueError(
                f"Scaglioni non esaustivi: {rimanente:.2f} unità non tariffate "
                f"su un consumo di {consumo_annuo}. L'ultimo scaglione deve "
                f"avere un limite >= {OPEN_TIER_MIN_LIMIT}."
            )
        return totale / consumo_annuo

    def get_gas_vol_avg(self, zona, consumo_annuo):
        if zona not in self.GAS_VOL:
            raise KeyError(f"Zona gas '{zona}' assente da GAS_VOL.")
        return self._avg_from_tiers(self.GAS_VOL[zona], consumo_annuo)

    def get_gas_accisa_avg(self, territorio, consumo_annuo):
        if territorio not in self.GAS_ACCISE:
            raise KeyError(f"Territorio accisa '{territorio}' assente da GAS_ACCISE.")
        return self._avg_from_tiers(self.GAS_ACCISE[territorio], consumo_annuo)

    def get_ele_accisa_avg(self, residente, consumo_annuo):
        aliquota = self.PARAMETRI["accisa_ee"]
        franchigia = self.PARAMETRI["accisa_ee_franchigia"]
        if not residente:
            return aliquota
        if consumo_annuo <= franchigia:
            return 0.0

        tot_accisa = (consumo_annuo - franchigia) * aliquota
        return tot_accisa / consumo_annuo if consumo_annuo > 0 else 0.0

    def get_iva_gas(self, consumo_annuo):
        """Aliquota IVA media gas sul consumo (10% fino a 480 Smc, 22% oltre)."""
        if consumo_annuo <= 0:
            return self.PARAMETRI["iva_gas_soglie"][0][1]
        return self._avg_from_tiers(self.PARAMETRI["iva_gas_soglie"], consumo_annuo)
