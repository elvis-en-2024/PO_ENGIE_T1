import polars as pl
from pathlib import Path
from datetime import date, timedelta
import logging
import hashlib
import json
import os

from model.schema import DIM_OFFERTA_SCHEMA, OPEN_END_DATE

logger = logging.getLogger(__name__)

class SCD2Manager:
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.dim_path = self.storage_dir / "dim_offerta.parquet"
        
    def _compute_hash(self, row: dict) -> str:
        # payload ignora i campi di sistema e di gestione per il calcolo dell'hash
        payload = {k: v for k, v in row.items() if k not in ["offerta_id", "commodity", "valid_from", "valid_to", "is_current", "n_giorni_pubblicazione", "sk_offerta_versione"]}
        encoded = json.dumps(payload, sort_keys=True, default=str).encode('utf-8')
        return hashlib.sha256(encoded).hexdigest()

    def process_daily_batch(self, daily_records: list[dict], process_date: date, commodity: str) -> dict:
        """
        Implementazione robusta del merge SCD2 Type 2 per Polars.
        Identifica record Invariati, Nuovi, Modificati e Cessati.
        """
        logger.info(f"Elaborazione SCD2 ({commodity}) per {process_date}")
        
        today_rows = []
        for r in daily_records:
            oid = f"{r.get('PIVA_UTENTE','')}_{r.get('COD_OFFERTA','')}_{commodity}"
            content_hash = self._compute_hash(r)
            
            flat_r = dict(r)
            flat_r["offerta_id"] = oid
            flat_r["content_hash"] = content_hash
            flat_r["sk_offerta_versione"] = f"{oid}_{content_hash}"
            flat_r["valid_from"] = process_date
            flat_r["valid_to"] = date.fromisoformat(OPEN_END_DATE)
            flat_r["is_current"] = True
            flat_r["n_giorni_pubblicazione"] = 1
            flat_r["commodity"] = commodity
            today_rows.append(flat_r)
        # Normalizziamo tutti i valori a stringa per evitare errori di type inference misti in Polars
        str_rows = []
        for r in today_rows:
            str_rows.append({k: str(v) if v is not None else None for k, v in r.items()})
            
        df_today = pl.DataFrame(str_rows, infer_schema_length=10000)
        if df_today.height == 0:
            return {"status": "empty_input"}

        # Rimuoviamo la dipendenza statica dallo schema
        # Polars gestirà automaticamente le colonne mancanti con how="diagonal"

        if not self.dim_path.exists():
            df_today.write_parquet(self.dim_path)
            logger.info("Primo caricamento massivo effettuato.")
            return {"inserted_new": df_today.height, "closed": 0, "modified": 0, "unchanged": 0}

        df_full = pl.read_parquet(self.dim_path)
        
        # Allineamento dinamico colonne in caso di evoluzione schema
        for col in df_today.columns:
            if col not in df_full.columns:
                df_full = df_full.with_columns(pl.lit(None).alias(col))
        for col in df_full.columns:
            if col not in df_today.columns:
                df_today = df_today.with_columns(pl.lit(None).alias(col))
        
        df_today = df_today.select(df_full.columns)
        
        # Estraiamo i correnti per la commodity in esame
        df_active = df_full.filter((pl.col("is_current") == True) & (pl.col("commodity") == commodity))
        df_historical = df_full.filter((pl.col("is_current") == False) | (pl.col("commodity") != commodity))

        if df_active.height == 0:
            df_final = pl.concat([df_full, df_today], how="vertical_relaxed")
            df_final.write_parquet(self.dim_path)
            return {"inserted_new": df_today.height}

        # LOGICA DI MERGE: Usiamo outer join
        join_df = df_active.join(df_today, on="offerta_id", how="outer", suffix="_new")
        
        # 1. Chiusi (Presenti ieri, assenti oggi)
        closed_mask = join_df["valid_from_new"].is_null()
        df_closed = join_df.filter(closed_mask).select(df_active.columns)
        if df_closed.height > 0:
            df_closed = df_closed.with_columns([
                pl.lit(False).alias("is_current"),
                pl.lit(process_date - timedelta(days=1)).alias("valid_to")
            ])

        # 2. Nuovi Assoluti (Assenti ieri, presenti oggi)
        new_mask = join_df["valid_from"].is_null()
        df_new = join_df.filter(new_mask).select([pl.col(c + "_new").alias(c) if c != "offerta_id" else pl.col(c) for c in df_active.columns])
        
        # Entrambi presenti: Invariati vs Modificati
        both_mask = join_df["valid_from"].is_not_null() & join_df["valid_from_new"].is_not_null()
        df_both = join_df.filter(both_mask)
        
        # 3. Invariati (Hash uguale)
        unchanged_mask = df_both["content_hash"] == df_both["content_hash_new"]
        df_unchanged = df_both.filter(unchanged_mask).select(df_active.columns)
        if df_unchanged.height > 0:
            df_unchanged = df_unchanged.with_columns(
                pl.col("n_giorni_pubblicazione") + 1
            )
            
        # 4. Modificati (Hash diverso)
        modified_mask = df_both["content_hash"] != df_both["content_hash_new"]
        df_modified_old = df_both.filter(modified_mask).select(df_active.columns).with_columns([
            pl.lit(False).alias("is_current"),
            pl.lit(process_date - timedelta(days=1)).alias("valid_to")
        ])
        df_modified_new = df_both.filter(modified_mask).select([pl.col(c + "_new").alias(c) if c != "offerta_id" else pl.col(c) for c in df_active.columns])

        # Riassemblaggio del DataFrame Finale
        components = [df_historical, df_closed, df_new, df_unchanged, df_modified_old, df_modified_new]
        components = [c for c in components if c.height > 0]
        
        df_final = pl.concat(components, how="vertical_relaxed")
        
        # Salvataggio sicuro (temp file -> rename)
        tmp_path = self.dim_path.with_suffix('.tmp.parquet')
        df_final.write_parquet(tmp_path)
        os.replace(tmp_path, self.dim_path)
        
        stats = {
            "inserted_new": df_new.height,
            "closed": df_closed.height,
            "unchanged": df_unchanged.height,
            "modified": df_modified_new.height,
            "date": str(process_date)
        }
        return stats
