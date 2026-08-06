"""Validación de la narrativa ejecutiva HTML."""

from __future__ import annotations

import json

import pandas as pd

from config.settings import MODEL_DIR, PROCESSED_DIR, QUANTITY_MODEL_DIR
from src.executive_presentation import build_executive_presentation_html


def test_executive_presentation_distinguishes_demand_from_delivered(tmp_path) -> None:
    orders = pd.read_csv(PROCESSED_DIR / "orders_enriched.csv", low_memory=False)
    profiles = pd.read_csv(MODEL_DIR / "segment_profiles.csv")
    scenarios = pd.read_csv(QUANTITY_MODEL_DIR / "scenario_comparison.csv")
    metrics = json.loads((MODEL_DIR / "metrics.json").read_text(encoding="utf-8"))
    quantity = json.loads(
        (QUANTITY_MODEL_DIR / "validation_metrics.json").read_text(encoding="utf-8")
    )
    metrics["quantity_r2"] = quantity["r2"]
    output = tmp_path / "presentacion.html"
    build_executive_presentation_html(orders, profiles, scenarios, metrics, output)
    content = output.read_text(encoding="utf-8")
    assert "Valor bruto de pedidos" in content
    assert "Valor entregado" in content
    assert "Direct Sales requiere intervención" in content
    assert "Plan de 12 meses" in content
    assert "Decisiones solicitadas al comité" in content
    assert ".card{background:#fff;color:#111" in content
    assert ".card.signal{background:var(--signal);color:#000" in content
    assert "table{border-collapse:collapse;width:100%;background:#fff;color:#111" in content
    assert "scroll-snap-type:y proximity" in content
    assert 'class="statement closing-statement"' in content
    assert "__[A-Z" not in content
