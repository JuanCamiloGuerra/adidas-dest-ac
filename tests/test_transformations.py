"""Pruebas de normalización, revenue, segmentos e integridad de joins."""

from __future__ import annotations

import pytest

from config.settings import REQUIRED_COLUMNS
from src.transform import build_orders_enriched, normalize_carts


def test_normalization_creates_one_row_per_product(api_collections: dict[str, list[dict[str, object]]]) -> None:
    normalized = normalize_carts(api_collections["carts"])
    assert len(normalized) == 3
    assert normalized["order_id"].nunique() == 1


def test_revenue_segments_and_joins(api_collections: dict[str, list[dict[str, object]]]) -> None:
    result = build_orders_enriched(**api_collections)
    assert len(result) == 3
    assert set(REQUIRED_COLUMNS).issubset(result.columns)
    assert result["revenue"].tolist() == pytest.approx([99.98, 600.0, 201.0])
    assert result["price_segment"].tolist() == ["Económico", "Medio", "Premium"]
    assert result["product_match_flag"].all() and result["user_match_flag"].all()

