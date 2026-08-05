"""Pruebas de generación de la guía visual de la fase 1."""

from __future__ import annotations

from src.api_guide import build_api_guide_html
from src.data_quality import evaluate_quality
from src.transform import build_orders_enriched


def test_api_guide_uses_real_contract_and_master_table(
    tmp_path, api_collections: dict[str, list[dict[str, object]]]
) -> None:
    master, _ = evaluate_quality(build_orders_enriched(**api_collections))
    output = tmp_path / "fase-1.html"
    build_api_guide_html(output_path=output, master=master, **api_collections)
    content = output.read_text(encoding="utf-8")
    assert "Venía con el proyecto" in content
    assert "Lo construimos nosotros" in content
    assert "SportRetailAPIClient" in content
    assert "order_id + line_number" in content
    assert "tabla maestra" in content.lower()
    assert "__ORDER__" not in content
