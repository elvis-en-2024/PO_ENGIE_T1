"""Offerta ipotetica da posizionare nel ranking.

Costruisce una riga nello stesso formato del flattener (colonne COMP_IMP_*,
SCONTO_*, REGOLATA_*, DISP_*, IDX_*), così la SAS è calcolata dal motore con
le stesse regole delle offerte reali. `posiziona` restituisce la posizione nel
ranking e il prezzo che servirebbe per raggiungere una posizione obiettivo.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

PIVA_SIMULATA = "SIMULATA"
COD_SIMULATA = "NUOVA_OFFERTA"

# fasce del form -> (TIPOLOGIA_FASCE, [(chiave prezzo, FASCIA_COMPONENTE)])
FASCE = {
    "Monoraria": ("monorario/F1", [("F0", "monorario/F1")]),
    "Bioraria (F1 / F2+F3)": ("biorario (F1 / F2+F3)", [("F1", "monorario/F1"), ("F23", "F2+F3")]),
    "Trioraria (F1, F2, F3)": ("F1, F2, F3", [("F1", "monorario/F1"), ("F2", "F2"), ("F3", "F3")]),
}
INDICI = {"E": "PUN_Men", "G": "PSV_Men"}


@dataclass
class Sconto:
    nome: str
    valore: float
    unita: str = "€/Anno"               # €/Anno, €, €/kWh, €/Smc, Percentuale
    condizione: str = "Non condizionato"
    validita: str = "Ingresso"          # Ingresso, entro 12 mesi, oltre 12 mesi
    iva: str = "SI"
    durata_mesi: int | None = None

    @property
    def tipo(self) -> str:
        return "Sconto Vendita" if self.unita == "Percentuale" else "Sconto fisso"


@dataclass
class NuovaOfferta:
    commodity: str = "E"                # E, G
    nome: str = "Nuova offerta"
    tipo_offerta: str = "Fisso"         # Fisso, Variabile
    fasce: str = "Monoraria"            # chiave di FASCE (solo luce)
    quota_fissa: float = 0.0            # €/anno commercializzazione
    prezzi: dict = field(default_factory=dict)   # F0/F1/F2/F3/F23 €/kWh o 'G' €/Smc; spread se variabile
    quota_potenza: float = 0.0          # €/kW/anno (luce)
    verde: float = 0.0                  # €/kWh o €/Smc per energia verde (FER), 0 = non prevista
    regolate: tuple = ()                # PCV, PPE, CCR, QVD_Fissa, QVD_Variabile, CPR, GRAD
    cdispd: bool = True                 # dispacciamento del Portale (luce)
    dispbt: bool = False
    sconti: list = field(default_factory=list)

    def riga(self) -> dict:
        """Riga dell'offerta nel formato del flattener."""
        luce = self.commodity == "E"
        r = {
            "commodity": self.commodity, "PIVA_UTENTE": PIVA_SIMULATA, "COD_OFFERTA": COD_SIMULATA,
            "NOME_OFFERTA": self.nome, "TIPO_OFFERTA": self.tipo_offerta, "TIPO_CLIENTE": "Domestico",
            "DOMESTICO_RESIDENTE": "Tutte", "OFFERTA_SINGOLA": "SI",
            "PREZZO_COMPRENSIVO_PERDITE_RETE": "SI",
            "TIPOLOGIA_FASCE": FASCE[self.fasce][0] if luce else None,
            "COND_Attivazione_LIMITANTE": None, "COND_Pluriennale_LIMITANTE": None,
        }
        comp = 0

        def componente(nome, macroarea, macroarea_cod, intervalli):
            nonlocal comp
            comp += 1
            p = f"COMP_IMP_{comp}"
            r.update({f"{p}_NOME": nome, f"{p}_MACROAREA": macroarea, f"{p}_MACROAREA_COD": macroarea_cod,
                      f"{p}_TIPOLOGIA": "STANDARD", f"{p}_TIPOLOGIA_COD": "01"})
            for i, (prezzo, unita, fascia) in enumerate(intervalli, start=1):
                r.update({f"{p}_INT_{i}_PREZZO": str(prezzo), f"{p}_INT_{i}_UNITA": unita,
                          f"{p}_INT_{i}_FASCIA": fascia})

        if self.quota_fissa:
            componente("Quota fissa", "Commercializzazione quota fissa", "01",
                       [(self.quota_fissa, "€/Anno", None)])
        nome_energia = "Spread" if self.tipo_offerta == "Variabile" else "Prezzo energia"
        if luce:
            intervalli = [(self.prezzi.get(k, 0.0), "€/kWh", f) for k, f in FASCE[self.fasce][1]]
            if any(p for p, _, _ in intervalli):
                componente(nome_energia, "Prezzo quota energia", "04", intervalli)
            if self.quota_potenza:
                componente("Quota potenza", "Commercializzazione quota fissa", "01",
                           [(self.quota_potenza, "€/kW", None)])
        elif self.prezzi.get("G"):
            componente(nome_energia, "Prezzo quota energia", "04", [(self.prezzi["G"], "€/Smc", None)])
        if self.verde:
            componente("Energia verde", "FER/Energia Verde", "06",
                       [(self.verde, "€/kWh" if luce else "€/Smc", None)])

        for nome in ("PCV", "PPE", "CCR", "CPR", "GRAD", "QTint", "QTpsv", "QVD_Fissa", "QVD_Variabile"):
            r[f"REGOLATA_{nome}"] = nome in self.regolate
        if luce:
            r["DISP_CdispD"] = self.cdispd
            r["DISP_DispBT"] = self.dispbt
        if self.tipo_offerta == "Variabile":
            r[f"IDX_{INDICI[self.commodity]}"] = True
            r[f"IDX_{INDICI[self.commodity]}_COEFF"] = "1"

        for s, sc in enumerate(self.sconti, start=1):
            p = f"SCONTO_{s}"
            r.update({f"{p}_NOME": sc.nome, f"{p}_COND_APP": sc.condizione, f"{p}_VALIDITA": sc.validita,
                      f"{p}_IVA": sc.iva, f"{p}_DURATA": sc.durata_mesi, f"{p}_CODICE_COMP": None,
                      f"{p}_PREZZO_1_TIPO": sc.tipo, f"{p}_PREZZO_1_VAL": str(sc.valore),
                      f"{p}_PREZZO_1_UNITA": sc.unita, f"{p}_PREZZO_1_DA": "0", f"{p}_PREZZO_1_FINO": "0"})
        return r

    def con_variazione(self, d_energia: float = 0.0, d_fissa: float = 0.0) -> "NuovaOfferta":
        """Copia con tutti i prezzi energia spostati di d_energia e la quota fissa di d_fissa."""
        from dataclasses import replace
        return replace(self, prezzi={k: v + d_energia for k, v in self.prezzi.items()},
                       quota_fissa=self.quota_fissa + d_fissa)


def ranking_con(calc, concorrenti: pd.DataFrame, offerta: NuovaOfferta, **kw) -> pd.DataFrame:
    """Ranking delle offerte concorrenti filtrate più l'offerta simulata."""
    df = pd.concat([concorrenti, pd.DataFrame([offerta.riga()])], ignore_index=True)
    return calc.calculate_sas(df, **kw)


def _sas(calc, offerta: NuovaOfferta, **kw) -> float:
    res = calc.calculate_sas(pd.DataFrame([offerta.riga()]), **kw)
    return float(res.iloc[0]["SAS"])


def posiziona(calc, concorrenti: pd.DataFrame, offerta: NuovaOfferta,
              obiettivi=(1, 3, 10), **kw) -> dict:
    """Posizione dell'offerta e variazioni di prezzo per raggiungere gli obiettivi.

    La SAS è lineare nei prezzi (a scaglioni IVA e accisa fissi), quindi la
    pendenza si misura con due calcoli: + 0,01 €/unità sull'energia e
    + 10 €/anno sulla quota fissa."""
    res = ranking_con(calc, concorrenti, offerta, **kw)
    mia = res.index[res["COD_OFFERTA"] == COD_SIMULATA][0]
    sas = float(res.loc[mia, "SAS"])
    altri = res[res["COD_OFFERTA"] != COD_SIMULATA]["SAS"].to_numpy()

    k_energia = (_sas(calc, offerta.con_variazione(d_energia=0.01), **kw) - sas) / 0.01
    k_fissa = (_sas(calc, offerta.con_variazione(d_fissa=10.0), **kw) - sas) / 10.0
    target = {}
    for pos in obiettivi:
        if pos > len(altri):
            continue
        # SAS da battere: quella dell'attuale pos-esima offerta concorrente
        soglia = np.sort(altri)[pos - 1] - 0.01
        delta = soglia - sas
        target[pos] = {
            "sas_obiettivo": round(soglia, 2),
            "delta_sas": round(delta, 2),
            "d_energia": delta / k_energia if k_energia > 0 and delta < 0 else 0.0,
            "d_fissa": delta / k_fissa if k_fissa > 0 and delta < 0 else 0.0,
        }
    return {"ranking": res, "posizione": int(mia) + 1, "totale": len(res), "sas": sas,
            "primo": float(altri.min()) if len(altri) else None, "obiettivi": target,
            "sensibilita": {"energia": k_energia, "fissa": k_fissa}}
