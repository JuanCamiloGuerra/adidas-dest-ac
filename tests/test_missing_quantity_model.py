"""Pruebas del escenario experimental de cantidades faltantes."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.missing_quantity_model import train_missing_quantity_model


def _orders_with_missing_quantity(
    api_collections: dict[str, list[dict[str, object]]]
) -> pd.DataFrame:
    """Amplía la fixture para disponer de varios pedidos y un objetivo nulo."""

    from src.data_quality import evaluate_quality
    from src.transform import build_orders_enriched

    base, _ = evaluate_quality(build_orders_enriched(**api_collections))
    frames = []
    for order_offset in range(20):
        copy = base.copy()
        copy["order_id"] = 100 + order_offset
        copy["quantity"] = copy["quantity"] + order_offset % 5
        copy["revenue"] = copy["unit_price"] * copy["quantity"]
        frames.append(copy)
    orders = pd.concat(frames, ignore_index=True)
    orders.loc[0, ["quantity", "revenue"]] = np.nan
    return orders


def test_quantity_model_preserves_source_and_excludes_revenue(
    api_collections: dict[str, list[dict[str, object]]]
) -> None:
    orders = _orders_with_missing_quantity(api_collections)
    original_quantity = orders["quantity"].copy()
    original_revenue = orders["revenue"].copy()
    result = train_missing_quantity_model(orders)

    pd.testing.assert_series_equal(orders["quantity"], original_quantity)
    pd.testing.assert_series_equal(orders["revenue"], original_revenue)
    assert "revenue" in result["metrics"]["leakage_columns_excluded"]
    assert len(result["predictions"]) == int(orders["quantity"].isna().sum())
    assert result["predictions"]["quantity_rf_estimated"].ge(5).all()


def test_quantity_model_is_reproducible(
    api_collections: dict[str, list[dict[str, object]]]
) -> None:
    orders = _orders_with_missing_quantity(api_collections)
    first = train_missing_quantity_model(orders)
    second = train_missing_quantity_model(orders)
    assert np.allclose(
        first["predictions"]["quantity_rf_raw"],
        second["predictions"]["quantity_rf_raw"],
    )
    assert np.isclose(first["metrics"]["rmse"], second["metrics"]["rmse"])
