"""Confronto SAS tra due versioni di motore + dati, sugli scenari dell'app.

    python scripts/diff_sas.py --rif 2026-08-24 \
        --vecchio-commit 52b40fd --vecchio-dati data/processed/storico_2026_full.parquet.bak

Il lato "vecchio" gira in un sottoprocesso con il codice estratto dal commit
indicato (git archive in .tmp/), il lato "nuovo" con il codice corrente.
Output: data/processed/diff_sas.csv, una riga per (scenario, offerta).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from io import BytesIO
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

# nome, commodity, consumi, potenza, fasce, regione, tipo_offerta
SCENARI = [
    ("E_mono_2700_Lombardia_fisso", "E", {"F1": 2700}, 3.0, "Monorario", "Lombardia", "Fisso"),
    ("E_fasce_2700_Lombardia_fisso", "E", {"F1": 891, "F2": 837, "F3": 972}, 3.0, "A Fasce", "Lombardia", "Fisso"),
    ("E_mono_2700_Sicilia_variabile", "E", {"F1": 2700}, 3.0, "Monorario", "Sicilia", "Variabile"),
    ("G_1400_Lombardia_fisso", "G", {"F1": 1400}, 0, None, "Lombardia", "Fisso"),
    ("G_1400_Sicilia_fisso", "G", {"F1": 1400}, 0, None, "Sicilia", "Fisso"),
    ("G_1400_Lazio_variabile", "G", {"F1": 1400}, 0, None, "Lazio", "Variabile"),
]


def _snapshot(path: str, rif: str):
    if Path(path).is_dir():  # storico partizionato: stessa lettura dell'app
        from datetime import date
        from storage import daily_store as ds
        return ds.leggi_finestra(date.fromisoformat(rif), giorni=8, root=Path(path))
    import duckdb
    con = duckdb.connect()
    con.execute("SET memory_limit = '2GB'; SET preserve_insertion_order = false")
    # filtro sulla finestra prima della window function: evita di ordinare tutto lo storico
    return con.execute(f"""
        SELECT * FROM read_parquet('{Path(path).as_posix()}', union_by_name = true)
        WHERE DATA_RILEVAZIONE::DATE BETWEEN DATE '{rif}' - INTERVAL 7 DAY AND DATE '{rif}'
        QUALIFY ROW_NUMBER() OVER (PARTITION BY PIVA_UTENTE, COD_OFFERTA
                                   ORDER BY DATA_RILEVAZIONE DESC) = 1
    """).df()


def calcola(dati: str, rif: str) -> list[dict]:
    """Eseguito con il motore importabile da sys.path."""
    import warnings
    warnings.filterwarnings("ignore")
    from engine.sas_calculator_fast import FastSASCalculator

    calc = FastSASCalculator(_snapshot(dati, rif))
    righe = []
    for nome, c, cons, pot, fasce, reg, tipo in SCENARI:
        f = calc.filter_offers(commodity=c, tipo_offerta=tipo, fasce=fasce,
                               regione=reg, provincia=None, comune=None,
                               consumo_annuo=sum(cons.values()),
                               falsa_multioraria="mantieni")
        try:
            res = calc.calculate_sas(f, cons, potenza=pot, regione=reg)
        except TypeError:
            res = calc.calculate_sas(f, cons, potenza=pot)
        for r in res.itertuples():
            righe.append({"scenario": nome, "PIVA": r.PIVA_VENDITORE,
                          "COD_OFFERTA": r.COD_OFFERTA, "NOME_OFFERTA": r.NOME_OFFERTA,
                          "SAS": r.SAS, "rank": r.Index + 1})
    return righe


def _estrai_commit(commit: str) -> Path:
    dest = Path(tempfile.mkdtemp(prefix=f"engine_{commit}_", dir=BASE / ".tmp"))
    tar = subprocess.run(["git", "archive", commit, "engine", "parse"],
                         cwd=BASE, capture_output=True, check=True).stdout
    tarfile.open(fileobj=BytesIO(tar)).extractall(dest)
    return dest


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rif", required=True)
    ap.add_argument("--vecchio-commit", default="52b40fd")
    ap.add_argument("--vecchio-dati", default="data/processed/storico_2026_full.parquet.bak")
    ap.add_argument("--nuovi-dati", default="data/storage/storico")
    ap.add_argument("--out", default="data/processed/diff_sas.csv")
    ap.add_argument("--_lato", help=argparse.SUPPRESS)
    ap.add_argument("--_json", help=argparse.SUPPRESS)
    args = ap.parse_args()

    if args._lato:  # sottoprocesso: motore già in testa a sys.path
        # su file e non su stdout: il motore vecchio stampa a video
        Path(args._json).write_text(json.dumps(calcola(args._lato, args.rif)), encoding="utf-8")
        return

    import pandas as pd

    def lato(codice: Path, dati: str) -> pd.DataFrame:
        js = codice / "risultato.json" if codice != BASE else BASE / ".tmp" / "diff_nuovo.json"
        cmd = [sys.executable, "-c",
               f"import sys; sys.path.insert(0, r'{codice}'); sys.path.insert(1, r'{BASE / 'scripts'}');"
               f"sys.argv = ['diff_sas', '--rif', '{args.rif}', '--_lato', r'{dati}', '--_json', r'{js}'];"
               "import diff_sas; diff_sas.main()"]
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        out = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True,
                             encoding="utf-8", errors="replace", env=env)
        if out.returncode:
            raise RuntimeError(out.stderr[-3000:])
        return pd.DataFrame(json.loads(js.read_text(encoding="utf-8")))

    old = lato(_estrai_commit(args.vecchio_commit), args.vecchio_dati)
    new = lato(BASE, args.nuovi_dati)
    chiave = ["scenario", "PIVA", "COD_OFFERTA"]
    d = old.merge(new, on=chiave, how="outer", suffixes=("_old", "_new"), indicator=True)
    d["NOME_OFFERTA"] = d["NOME_OFFERTA_new"].fillna(d["NOME_OFFERTA_old"])
    d["delta"] = d["SAS_new"] - d["SAS_old"]
    d["delta_pct"] = 100 * d["delta"] / d["SAS_old"]
    d["esito"] = d["_merge"].map({"both": "in entrambi", "left_only": "solo vecchio",
                                  "right_only": "solo nuovo"})
    d = d[chiave + ["NOME_OFFERTA", "SAS_old", "SAS_new", "delta", "delta_pct",
                    "rank_old", "rank_new", "esito"]]
    d.sort_values(["scenario", "rank_new"]).to_csv(BASE / args.out, index=False)

    g = d.groupby("scenario")
    riepilogo = pd.DataFrame({
        "offerte_old": g["SAS_old"].count(), "offerte_new": g["SAS_new"].count(),
        "solo_nuovo": g["esito"].apply(lambda s: (s == "solo nuovo").sum()),
        "solo_vecchio": g["esito"].apply(lambda s: (s == "solo vecchio").sum()),
        "variate_>1%": g["delta_pct"].apply(lambda s: (s.abs() > 1).sum()),
        "delta_mediano": g["delta"].median().round(2),
    })
    print(riepilogo.to_string())
    print(f"\nDettaglio: {args.out}")


if __name__ == "__main__":
    main()
