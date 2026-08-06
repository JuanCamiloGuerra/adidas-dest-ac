"""Construye la presentación ejecutiva HTML desde artefactos consolidados."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import DOCS_DIR, MODEL_DIR, PROCESSED_DIR, QUANTITY_MODEL_DIR, ensure_directories  # noqa: E402
from src.executive_presentation import build_executive_presentation_html  # noqa: E402


def main() -> Path:
    """Genera la narrativa C-level y devuelve la ruta de salida."""

    ensure_directories()
    orders = pd.read_csv(PROCESSED_DIR / "orders_enriched.csv", low_memory=False)
    profiles = pd.read_csv(MODEL_DIR / "segment_profiles.csv")
    scenarios = pd.read_csv(QUANTITY_MODEL_DIR / "scenario_comparison.csv")
    metrics = json.loads((MODEL_DIR / "metrics.json").read_text(encoding="utf-8"))
    quantity_metrics = json.loads(
        (QUANTITY_MODEL_DIR / "validation_metrics.json").read_text(encoding="utf-8")
    )
    metrics["quantity_r2"] = quantity_metrics["r2"]
    output = DOCS_DIR / "presentacion-ejecutiva.html"
    build_executive_presentation_html(orders, profiles, scenarios, metrics, output)
    print(f"Presentación ejecutiva generada: {output}")
    return output


if __name__ == "__main__":
    main()
