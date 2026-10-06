"""Isola il filtro che azzera il set. Eseguire dalla root:
       python scripts/bisect_filtri.py
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PARQUET = "data/processed/PO_offerte_attive.parquet"
COMMODITY, REGIONE, PROVINCIA = "E", "Lombardia", "015"

# --- 1. Il modulo caricato è quello patchato? -------------------------------
from engine.sas_calculator_fast import FastSASCalculator

print("=" * 70)
print("FILE   :", inspect.getsourcefile(FastSASCalculator))
sig = inspect.signature(FastSASCalculator.filter_offers)
print("FIRMA  :", sig)
for p in ("consumo_annuo", "falsa_multioraria", "richiedi_prezzo_energia"):
    print(f"  {p:<26} {'OK' if p in sig.parameters else 'ASSENTE -> patch non attiva'}")

src = Path(inspect.getsourcefile(FastSASCalculator)).read_text(encoding="utf-8")
n_def = src.count("def filter_offers")
print(f"OCCORRENZE 'def filter_offers': {n_def}"
      + ("  <-- DUPLICATO: vince l'ultima definizione" if n_def > 1 else ""))

try:
    from engine import component_matrix as cm
    print("component_matrix:", cm.__file__)
except ImportError as exc:
    print("component_matrix NON IMPORTABILE:", exc)
    sys.exit(1)

PARQUET = "data/processed/storico_2026_full.parquet"
import pyarrow.parquet as pq
table = pq.read_table(PARQUET)
df = table.to_pandas(categories=[
    'commodity', 'TIPO_OFFERTA', 'TIPO_CLIENTE', 'TIPOLOGIA_FASCE', 
    'REGIONE', 'PROVINCIA', 'COMUNE', 'PIVA_VENDITORE', 'COD_OFFERTA', 'NOME_OFFERTA'
])

# Emulate app.py deduplication
col_piva = 'PIVA_UTENTE' if 'PIVA_UTENTE' in df.columns else 'PIVA_VENDITORE'
col_cod = 'CODICE_OFFERTA' if 'CODICE_OFFERTA' in df.columns else 'COD_OFFERTA'
if 'DATA_FINE' in df.columns:
    dt_fine = df['DATA_FINE'].astype(str).str.split('_').str[0]
    df['DATA_FINE'] = pd.to_datetime(dt_fine, format='%d/%m/%Y', errors='coerce')
    df = df[df['DATA_FINE'] >= pd.Timestamp.today()]
subset = [col_piva, col_cod, 'commodity'] if 'commodity' in df.columns else [col_piva, col_cod]
if 'DATA_RILEVAZIONE' in df.columns:
    df = df.sort_values(['DATA_RILEVAZIONE', col_cod], ascending=[False, True])
df = df.drop_duplicates(subset=subset)

e = df[df["commodity"] == COMMODITY]
print("\n" + "=" * 70)
print(f"Righe totali {len(df)} | commodity={COMMODITY}: {len(e)}")

for col in ("TIPO_OFFERTA", "TIPO_CLIENTE", "TIPOLOGIA_FASCE",
            "REGIONE", "PROVINCIA", "COMUNE"):
    if col in e.columns:
        vc = e[col].astype(str).value_counts(dropna=False)
        print(f"\n--- {col} ({vc.size} valori distinti) ---")
        print(vc.head(10).to_string())

print("\nColonne MACROAREA:",
      [c for c in e.columns if "MACROAREA" in c] or "NESSUNA (patch flattener non applicata)")

# --- 3. Bisezione manuale ---------------------------------------------------
print("\n" + "=" * 70)
print("BISEZIONE")
calc = FastSASCalculator(e)
f = e
NAZ = {"", "nan", "none", "null", "<na>"}


global_mask = pd.Series(True, index=f.index)

def step(mask, etichetta):
    global global_mask
    prima = global_mask.sum()
    if hasattr(mask, "reindex"):
        mask = mask.reindex(f.index).fillna(False)
    global_mask = global_mask & mask
    dopo = global_mask.sum()
    print(f"  {etichetta:<34} {prima:>6} -> {dopo:>6}"
          + ("   <<< AZZERATO" if dopo == 0 and prima > 0 else ""))
    return dopo > 0


ok = True
ok = ok and step(calc._match_multivalore(f["TIPO_OFFERTA"], "Fisso", "TIPO_OFFERTA"),
                 "tipo_offerta=Fisso")
ok = ok and step(calc._match_multivalore(f["TIPO_CLIENTE"], "Domestico", "TIPO_CLIENTE"),
                 "tipo_cliente=Domestico")

if ok:
    v = f["REGIONE"].astype(str).str.strip()
    ok = step(v.str.casefold().isin(NAZ) | (v == "03"), "regione=Lombardia(03)")
if ok:
    v = f["PROVINCIA"].astype(str).str.strip()
    ok = step(v.str.casefold().isin(NAZ) | (v == PROVINCIA), f"provincia={PROVINCIA}")
if ok:
    ok = step(~f["NOME_OFFERTA"].astype(str).str.contains("Sottocosto", case=False, na=False),
              "nome_sottocosto")

# Apply mask once to avoid OOM
f = f[global_mask]

# --- 4. I due filtri nuovi, isolati ---------------------------------------
if ok:
    long = cm.build_long(f, consumo_annuo=2700)
    print(f"\n  build_long -> {len(long)} righe componente")
    if long.empty:
        print("  >>> CAUSA: nessuna componente estratta. I prezzi non sono "
              "parsabili o i nomi colonna COMP_IMP_* non corrispondono.")
    else:
        print("  kind:", long['kind'].value_counts().to_dict())

    tipol = f["TIPOLOGIA_FASCE"].astype(str).map(cm._norm)
    mono = tipol.isin(cm._TIPOLOGIE_MONO)
    print(f"\n  dichiarate MONO: {int(mono.sum())} | non-MONO: {int((~mono).sum())}")

    flags = cm.multiorario_flags(f, long=long)
    print(f"  falsa_multioraria: {int(flags['falsa_multioraria'].sum())}")
    print("  n_fasce_dichiarate:", flags["n_fasce_dichiarate"].value_counts().to_dict())

    en = cm.energia_flags(f, long=long, consumo_annuo=2700)
    ko = ~en["prezzo_energia_ok"].fillna(False)
    print(f"\n  prezzo_energia KO: {int(ko.sum())} su {len(f)}")
    print("  motivi:", en.loc[ko, "motivo"].value_counts().to_dict())
    print("  soglia applicata (mediana):", round(float(en['soglia_applicata'].median()), 5))
    print("  prezzo_volumetrico_totale, descrizione:")
    print(en["prezzo_volumetrico_totale"].describe().round(5).to_string())

# --- 5. filter_offers, con i nuovi filtri progressivamente attivi ---------
# print("\n" + "=" * 70)
# print("filter_offers()")
# combinazioni = [
#     ("tutto spento",      dict(falsa_multioraria="mantieni", richiedi_prezzo_energia=False)),
#     ("solo multiorario",  dict(falsa_multioraria="escludi",  richiedi_prezzo_energia=False)),
#     ("solo energia",      dict(falsa_multioraria="mantieni", richiedi_prezzo_energia=True)),
#     ("entrambi",          dict(falsa_multioraria="escludi",  richiedi_prezzo_energia=True)),
# ]
# for etichetta, kw in combinazioni:
#     c = FastSASCalculator(e)
#     out = c.filter_offers(commodity=COMMODITY, fasce="A Fasce", tipo_offerta="Fisso",
#                           regione=REGIONE, provincia=PROVINCIA, comune=None,
#                           consumo_annuo=2700, **kw)
#     print(f"  {etichetta:<20} -> {len(out):>5} offerte | {c.diagnostica_esclusioni}")
