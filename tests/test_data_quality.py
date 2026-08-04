"""Pruebas de flags, deduplicación lógica y persistencia SQLite."""

from __future__ import annotations

import sqlite3

import numpy as np

from src.data_quality import evaluate_quality
from src.load import persist_orders
from src.transform import build_orders_enriched


def test_quality_marks_null_quantity_without_dropping(api_collections: dict[str, list[dict[str, object]]]) -> None:
    api_collections["carts"][0]["products"][0]["quantity"] = None
    frame = build_orders_enriched(**api_collections)
    checked, report = evaluate_quality(frame)
    assert len(checked) == 3
    assert checked.loc[checked["quantity"].isna(), "data_quality_flag"].str.contains("Cantidad nula").all()
    assert report.loc[report["regla_evaluada"].eq("Cantidad nula"), "registros_afectados"].item() == 1


def test_sqlite_persistence_and_no_infinite_values(tmp_path, api_collections: dict[str, list[dict[str, object]]]) -> None:
    frame, _ = evaluate_quality(build_orders_enriched(**api_collections))
    result = persist_orders(frame, tmp_path)
    assert result["rows"] == 3
    numeric = frame.select_dtypes(include="number")
    assert not np.isinf(numeric.astype(float).to_numpy()).any()
    with sqlite3.connect(tmp_path / "sportretail.db") as connection:
        assert connection.execute("SELECT COUNT(*) FROM orders_enriched").fetchone()[0] == 3
