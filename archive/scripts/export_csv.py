import polars as pl
from pathlib import Path

parquet_path = Path("data/storage/dim_offerta.parquet")
csv_path = Path("data/storage/dim_offerta.csv")

if parquet_path.exists():
    df = pl.read_parquet(parquet_path)
    df.write_csv(csv_path)
    print(f"File Parquet letto con successo! Contiene {df.height} righe e {df.width} colonne.")
    print(f"File salvato in formato leggibile su: {csv_path}")
else:
    print("File parquet non trovato.")
