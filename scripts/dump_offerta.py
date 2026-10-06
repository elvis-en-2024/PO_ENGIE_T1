from __future__ import annotations
import argparse
import gzip
from pathlib import Path
from lxml import etree

NS = '{http://www.acquirenteunico.it/schemas/SII_AU/OffertaRetail/01}'

def iter_raw_files(root: Path, commodity: str | None, date_hint: str | None):
    pattern = f"**/PO_Offerte_{commodity or '*'}_MLIBERO_*.xml*"
    files = sorted([f for f in root.rglob(pattern) if not f.name.endswith('.yaml')], reverse=True)
    if date_hint:
        d = date_hint.replace("-", "")
        files = [f for f in files if d in f.name] or files
    return files

def open_maybe_gz(path: Path):
    return gzip.open(path, "rb") if path.suffix == ".gz" else path.open("rb")

files = iter_raw_files(Path("data/raw"), "E", None)
if not files:
    raise SystemExit("Nessun XML in data/raw")

for path in files:
    with open_maybe_gz(path) as fh:
        for _, node in etree.iterparse(fh, tag=f"{NS}offerta"):
            cod = node.findtext(f".//{NS}COD_OFFERTA")
            if cod and cod.strip() == "022119ESFML01XXMONO2026DOME129EE":
                print(f"=== {path} ===\n")
                print("--- ComponenteImpresa presenti nell'XML ---")
                for k, comp in enumerate(node.findall(f".//{NS}ComponenteImpresa"), 1):
                    print(f"[{k}] NOME={comp.findtext(f'{NS}NOME')} "
                          f"MACROAREA={comp.findtext(f'{NS}MACROAREA')} "
                          f"TIPOLOGIA={comp.findtext(f'{NS}TIPOLOGIA')}")
                    for j, iv in enumerate(comp.findall(f"{NS}IntervalloPrezzi"), 1):
                        print(f"    INT_{j}: PREZZO={iv.findtext(f'{NS}PREZZO')} "
                              f"UM={iv.findtext(f'{NS}UNITA_MISURA')} "
                              f"FASCIA={iv.findtext(f'{NS}FASCIA_COMPONENTE')} "
                              f"DA={iv.findtext(f'{NS}CONSUMO_DA')} "
                              f"A={iv.findtext(f'{NS}CONSUMO_A')}")
                node.clear()
                raise SystemExit()
            node.clear()
