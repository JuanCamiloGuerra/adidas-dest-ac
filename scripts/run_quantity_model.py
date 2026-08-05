"""Ejecuta el escenario experimental para ``quantity`` nula."""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import PROCESSED_DIR, QUANTITY_MODEL_DIR, ensure_directories  # noqa: E402
from src.missing_quantity_model import train_missing_quantity_model  # noqa: E402
from src.utils import write_json  # noqa: E402


def main() -> dict[str, object]:
    """Genera artefactos auditables sin modificar la tabla maestra."""

    ensure_directories()
    csv_path = PROCESSED_DIR / "orders_enriched.csv"
    orders = pd.read_csv(csv_path, parse_dates=["order_date"], low_memory=False)
    result = train_missing_quantity_model(orders)

    write_json(result["metrics"], QUANTITY_MODEL_DIR / "validation_metrics.json")
    result["predictions"].to_csv(
        QUANTITY_MODEL_DIR / "missing_quantity_predictions.csv", index=False, encoding="utf-8"
    )
    result["scenario_comparison"].to_csv(
        QUANTITY_MODEL_DIR / "scenario_comparison.csv", index=False, encoding="utf-8"
    )
    result["feature_importance"].to_csv(
        QUANTITY_MODEL_DIR / "feature_importance.csv", index=False, encoding="utf-8"
    )
    joblib.dump(result["model"], QUANTITY_MODEL_DIR / "random_forest_quantity.joblib")
    return result["metrics"]


if __name__ == "__main__":
    main()
