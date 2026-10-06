import pandas as pd
pd.set_option("display.max_colwidth", 80)

import pyarrow.parquet as pq
import pyarrow as pa

table = pq.read_table("data/processed/storico_2026_full.parquet")
# Convert string columns to categorical
import pandas as pd
df = table.to_pandas(categories=[
    'commodity', 'TIPO_OFFERTA', 'TIPO_CLIENTE', 'TIPOLOGIA_FASCE', 
    'REGIONE', 'PROVINCIA', 'COMUNE', 'PIVA_VENDITORE', 'COD_OFFERTA', 'NOME_OFFERTA'
])
e = df[df["commodity"] == "E"]
print(f"Elettrico: {len(e)} righe\n")

for col in ("TIPO_OFFERTA", "TIPO_CLIENTE", "TIPOLOGIA_FASCE",
            "REGIONE", "PROVINCIA", "COMUNE"):
    if col in e.columns:
        print(f"--- {col} ---")
        print(e[col].astype(str).value_counts(dropna=False).head(15), "\n")

comp = [c for c in e.columns if c.startswith("COMP_IMP_") and c.endswith("_PREZZO")]
print("Colonne prezzo componente:", len(comp))
sub = e[comp].apply(pd.to_numeric, errors="coerce")
print("Righe con almeno un prezzo != 0:", int((sub.fillna(0) != 0).any(axis=1).sum()))
print("\nColonne MACROAREA presenti:",
      [c for c in e.columns if "MACROAREA" in c] or "NESSUNA (patch flattener non applicata)")
