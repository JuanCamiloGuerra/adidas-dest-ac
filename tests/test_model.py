"""Pruebas de reproducibilidad del clustering y generación HTML."""

from __future__ import annotations

import pandas as pd

from src.model_training import train_segmentation
from src.visualization import build_dashboard_html


def test_model_is_reproducible(tmp_path, customer_features: pd.DataFrame) -> None:
    first = train_segmentation(customer_features, tmp_path / "first")
    second = train_segmentation(customer_features, tmp_path / "second")
    assert first["algorithm"] == second["algorithm"]
    assert first["clusters"] == second["clusters"]
    assert first["assignments"]["cluster"].tolist() == second["assignments"]["cluster"].tolist()
    assert {"predominant_country", "predominant_category"}.issubset(first["profiles"].columns)


def test_static_html_is_generated(tmp_path, api_collections: dict[str, list[dict[str, object]]]) -> None:
    from src.business_insights import calculate_kpis, generate_insights
    from src.data_quality import evaluate_quality
    from src.transform import build_orders_enriched

    orders, _ = evaluate_quality(build_orders_enriched(**api_collections))
    target = tmp_path / "index.html"
    build_dashboard_html(orders, calculate_kpis(orders), generate_insights(orders), target)
    content = target.read_text(encoding="utf-8")
    assert target.exists()
    assert "Plotly" in content and "const RAW=" in content
    assert "C:\\Users\\" not in content
