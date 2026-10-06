"""Caricamento del golden dataset a tempo di collection (serve a parametrize)."""
from __future__ import annotations

import csv
from pathlib import Path

GOLDEN_CSV = Path(__file__).parent / "golden" / "sas_expected.csv"

TRUTHY = {"1", "si", "sì", "yes", "true", "y", "x"}


def is_true(value: str | None) -> bool:
    return str(value or "").strip().lower() in TRUTHY


def to_float(value: str | None, default: float | None = None) -> float | None:
    txt = str(value or "").strip().replace(",", ".")
    if not txt:
        return default
    return float(txt)


def load_golden_cases() -> list[dict]:
    if not GOLDEN_CSV.exists():
        return []
    with GOLDEN_CSV.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return [
            {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            for row in reader
            if row.get("case_id") and not row["case_id"].lstrip().startswith("#")
        ]


def case_ids(cases: list[dict]) -> list[str]:
    return [c["case_id"] for c in cases]
