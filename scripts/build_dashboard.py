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

from config.settings import DOCS_DIR, MODEL_DIR, PROCESSED_DIR, QUALITY_DIR, ensure_directories  # noqa: E402
from src.business_insights import calculate_kpis, generate_insights  # noqa: E402
from src.reporting import write_cleaning_decisions, write_executive_summary, write_model_report  # noqa: E402
from src.utils import write_json  # noqa: E402
from src.visualization import build_dashboard_html  # noqa: E402


def main() -> dict[str, object]:
    """Genera HTML, hallazgos y reportes usando solo artefactos procesados."""

    ensure_directories()
    orders = pd.read_parquet(PROCESSED_DIR / "orders_enriched.parquet")
    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
    kpis = calculate_kpis(orders)
    insights = generate_insights(orders)
    profiles = pca = None
    metrics: dict[str, object] = {}
    if (MODEL_DIR / "metrics.json").exists():
        metrics = json.loads((MODEL_DIR / "metrics.json").read_text(encoding="utf-8"))
        profiles = pd.read_csv(MODEL_DIR / "segment_profiles.csv")
        pca = pd.read_csv(MODEL_DIR / "pca_coordinates.csv")
    index_path = DOCS_DIR / "index.html"
    build_dashboard_html(orders, kpis, insights, index_path, profiles, pca, metrics)
    shutil.copyfile(index_path, DOCS_DIR / "dashboard.html")
    write_executive_summary(kpis, insights, DOCS_DIR)
    quality = pd.read_csv(QUALITY_DIR / "data_quality_report.csv")
    write_cleaning_decisions(quality, DOCS_DIR)
    if profiles is not None:
        write_model_report(metrics, profiles, DOCS_DIR)
    write_json({"kpis": kpis, "insights": insights}, ROOT / "outputs" / "reports" / "business_summary.json")
    return {"charts": 12 if profiles is not None else 9, "dashboard": str(index_path), "kpis": kpis}


if __name__ == "__main__":
    main()

