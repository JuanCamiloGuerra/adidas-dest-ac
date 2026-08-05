"""Construye el dashboard autónomo y sus documentos ejecutivos."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import (  # noqa: E402
    DOCS_DIR, MODEL_DIR, PROCESSED_DIR, QUALITY_DIR, QUANTITY_MODEL_DIR, ensure_directories,
)
from src.business_insights import calculate_kpis, generate_insights  # noqa: E402
from src.reporting import write_cleaning_decisions, write_executive_summary, write_model_report  # noqa: E402
from src.utils import write_json  # noqa: E402
from src.visualization import build_dashboard_html  # noqa: E402
from src.missing_quantity_model import build_retrospective_scenarios  # noqa: E402


def main() -> dict[str, object]:
    """Genera HTML, hallazgos y reportes usando solo artefactos procesados."""

    ensure_directories()
    # CSV evita exigir un motor Parquet en el entorno que solo reconstruye HTML.
    orders = pd.read_csv(PROCESSED_DIR / "orders_enriched.csv", low_memory=False)
    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
    orders = build_retrospective_scenarios(orders)
    kpis = calculate_kpis(orders)
    insights = generate_insights(orders)
    profiles = pca = None
    metrics: dict[str, object] = {}
    if (MODEL_DIR / "metrics.json").exists():
        metrics = json.loads((MODEL_DIR / "metrics.json").read_text(encoding="utf-8"))
        profiles = pd.read_csv(MODEL_DIR / "segment_profiles.csv")
        pca = pd.read_csv(MODEL_DIR / "pca_coordinates.csv")
    scenario_comparison = None
    quantity_metrics: dict[str, object] = {}
    orders["quantity_rf_estimated"] = orders["quantity"]
    orders["revenue_rf_estimated"] = orders["revenue"]
    if (QUANTITY_MODEL_DIR / "validation_metrics.json").exists():
        quantity_metrics = json.loads((QUANTITY_MODEL_DIR / "validation_metrics.json").read_text(encoding="utf-8"))
        predictions = pd.read_csv(QUANTITY_MODEL_DIR / "missing_quantity_predictions.csv")
        scenario_comparison = pd.read_csv(QUANTITY_MODEL_DIR / "scenario_comparison.csv")
        indexed = predictions.set_index("source_row_index")
        orders.loc[indexed.index, "quantity_rf_estimated"] = indexed["quantity_rf_estimated"]
        orders.loc[indexed.index, "revenue_rf_estimated"] = indexed["revenue_rf_estimated"]
    index_path = DOCS_DIR / "index.html"
    build_dashboard_html(
        orders, kpis, insights, index_path, profiles, pca, metrics,
        scenario_comparison, quantity_metrics,
    )
    shutil.copyfile(index_path, DOCS_DIR / "dashboard.html")
    write_executive_summary(kpis, insights, DOCS_DIR)
    quality = pd.read_csv(QUALITY_DIR / "data_quality_report.csv")
    write_cleaning_decisions(quality, DOCS_DIR)
    if profiles is not None:
        write_model_report(metrics, profiles, DOCS_DIR)
    write_json({"kpis": kpis, "insights": insights}, ROOT / "outputs" / "reports" / "business_summary.json")
    return {"charts": 15 if profiles is not None else 12, "dashboard": str(index_path), "kpis": kpis}


if __name__ == "__main__":
    main()
