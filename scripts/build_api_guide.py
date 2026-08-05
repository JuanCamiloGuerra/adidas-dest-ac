"""Genera la guía visual de la fase 1 desde artefactos reales del proyecto."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import DOCS_DIR, PROCESSED_DIR, ensure_directories  # noqa: E402
from src.api_guide import build_api_guide_html  # noqa: E402


def _load_collection(name: str) -> list[dict[str, object]]:
    """Lee la colección JSON que alimenta la API local."""

    path = ROOT / "api" / "data" / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}. Ejecute: python api/generate_data.py")
    return json.loads(path.read_text(encoding="utf-8"))[name]


def main() -> Path:
    """Construye el HTML autónomo y devuelve su ruta."""

    ensure_directories()
    master_path = PROCESSED_DIR / "orders_enriched.csv"
    if not master_path.exists():
        raise FileNotFoundError(f"No existe {master_path}. Ejecute: python scripts/run_etl.py")
    output = DOCS_DIR / "fase-1-api-tabla-maestra.html"
    build_api_guide_html(
        _load_collection("products"),
        _load_collection("users"),
        _load_collection("carts"),
        pd.read_csv(master_path, low_memory=False),
        output,
    )
    print(f"Guía de fase 1 generada: {output}")
    return output


if __name__ == "__main__":
    main()
