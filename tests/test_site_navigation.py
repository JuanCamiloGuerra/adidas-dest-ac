"""Pruebas de la navegación compartida y la guía Markdown."""

from __future__ import annotations

import json

from src.markdown_guide import build_markdown_guide
from src.site_navigation import NAV_ITEMS, navigation_html


def test_navigation_has_approved_order_and_dashboard_hashes() -> None:
    labels = [label for _, label, _, _ in NAV_ITEMS]
    assert labels == [
        "Presentación ejecutiva",
        "Fase 1",
        "Markdown",
        "Dashboard",
        "Escenarios",
        "Decisiones y ML",
        "Resumen",
    ]
    markup = navigation_html("scenarios")
    assert 'href="index.html#scenarios"' in markup
    assert 'data-dashboard-page="scenarios"' in markup


def test_markdown_guide_uses_global_navigation(tmp_path) -> None:
    notebook = tmp_path / "guide.ipynb"
    notebook.write_text(
        json.dumps(
            {
                "cells": [
                    {"cell_type": "markdown", "source": ["# Título\n", "\n", "Explicación **visible**."]},
                    {"cell_type": "code", "source": ["print('no publicar')"]},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    output = tmp_path / "markdown.html"
    build_markdown_guide(notebook, output)
    rendered = output.read_text(encoding="utf-8")
    assert "Presentación ejecutiva" in rendered
    assert '<a class="global-nav__link active" href="markdown.html">Markdown</a>' in rendered
    assert "Explicación <strong>visible</strong>" in rendered
    assert "no publicar" not in rendered
