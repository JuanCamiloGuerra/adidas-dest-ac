"""Generación de documentos ejecutivos y técnicos desde resultados reales.

Entradas: KPIs, hallazgos, calidad, validación y métricas del modelo.
Salidas: Markdown y HTML listos para repositorio y GitHub Pages.
Dependencias: pandas y biblioteca estándar.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.site_navigation import navigation_css, navigation_html


def _money(value: float) -> str:
    return f"USD {value:,.0f}"


def write_executive_summary(kpis: dict[str, Any], insights: list[dict[str, str]], docs_dir: Path) -> None:
    """Escribe un resumen de una página para liderazgo comercial."""

    findings = "\n".join(
        f"### {index}. {item['title']}\n\n{item['observation']} {item['importance']} **Recomendación:** {item['action']}\n"
        for index, item in enumerate(insights[:3], 1)
    )
    markdown = f"""# SportRetail LAM — Resumen ejecutivo

## Objetivo

Evaluar el desempeño mayorista regional, localizar los motores de valor de pedidos y convertir los patrones observados en acciones comerciales.

## Escala analizada

- Valor bruto de pedidos: **{_money(kpis['total_revenue'])}**
- Pedidos: **{kpis['orders']:,}**
- Clientes: **{kpis['customers']:,}**
- Unidades: **{kpis['units_sold']:,.0f}**
- Pedidos entregados: **{kpis['delivered_order_rate']:.1%}**

{findings}
## Limitaciones

Datos sintéticos de 2024, sin costos, margen, metas ni historial multianual. Los outliers mayoristas se conservan y se marcan; las relaciones son descriptivas, no causales.
El campo `revenue` incluye todos los estados del pedido; solo debe interpretarse como ingreso realizado cuando exista evidencia de entrega, facturación y pago.
"""
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "executive_summary.md").write_text(markdown, encoding="utf-8")
    finding_cards = "".join(
        f"<article><span>0{i}</span><h2>{item['title']}</h2><p>{item['observation']} {item['importance']}</p><p><strong>Acción:</strong> {item['action']}</p></article>"
        for i, item in enumerate(insights[:3], 1)
    )
    html = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Resumen ejecutivo | SportRetail LAM</title><style>
body{{margin:0;background:#f1f1ef;color:#111;font-family:Arial,sans-serif}}main{{max-width:1100px;margin:auto;padding:40px 24px}}.summary-hero{{background:#050505;color:#fff;padding:42px}}.summary-hero h1{{font-size:48px;margin:8px 0;letter-spacing:-.05em}}.summary-hero p{{color:#e2e2e2}}.eyebrow{{color:#d7ff3f;text-transform:uppercase;letter-spacing:.13em;font-size:11px;font-weight:bold}}.metrics{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:16px 0}}.metric,article{{background:#fff;color:#111;padding:18px;border-top:4px solid #111}}.metric strong{{display:block;font-size:22px;margin-top:8px}}.findings{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}article span{{font-weight:bold;color:#5f5f5f}}article h2{{font-size:22px}}article p{{line-height:1.5;color:#333}}.limits{{margin-top:18px;background:#fff;color:#111;border:1px solid #aaa;padding:18px;line-height:1.5}}@media(max-width:800px){{.metrics,.findings{{grid-template-columns:1fr 1fr}}}}@media(max-width:520px){{.metrics,.findings{{grid-template-columns:1fr}}}}
{navigation_css()}</style></head><body>{navigation_html("summary")}<main><header class="summary-hero"><span class="eyebrow">SportRetail LAM · 2024</span><h1>Resumen ejecutivo</h1><p>Desempeño mayorista regional y prioridades de acción.</p></header><section class="metrics"><div class="metric">Valor bruto de pedidos<strong>{_money(kpis['total_revenue'])}</strong></div><div class="metric">Pedidos<strong>{kpis['orders']:,}</strong></div><div class="metric">Clientes<strong>{kpis['customers']:,}</strong></div><div class="metric">Unidades<strong>{kpis['units_sold']:,.0f}</strong></div><div class="metric">Entregados<strong>{kpis['delivered_order_rate']:.1%}</strong></div></section><section class="findings">{finding_cards}</section><section class="limits"><strong>Limitaciones.</strong> El valor bruto incluye todos los estados y no equivale necesariamente a ingreso realizado. Datos sintéticos de un año, sin costos ni metas; los resultados son descriptivos y no demuestran causalidad.</section></main></body></html>"""
    (docs_dir / "executive_summary.html").write_text(html, encoding="utf-8")


def write_cleaning_decisions(quality: pd.DataFrame, docs_dir: Path) -> None:
    """Documenta cada regla, su volumen y la razón de tratamiento."""

    rows = "\n".join(
        f"| {r.regla_evaluada} | {r.registros_afectados:,} ({r.porcentaje_afectado:.2f}%) | {r.accion_aplicada} | {r.justificacion} | {r.severidad} |"
        for r in quality.itertuples()
    )
    text = f"""# Decisiones de limpieza

La limpieza prioriza trazabilidad: ninguna observación se elimina automáticamente. Las líneas inválidas se conservan con flags y se excluyen solo de los KPIs de venta cuando precio, cantidad o revenue no permiten una transacción válida.

| Regla | Afectados | Acción | Justificación | Severidad |
|---|---:|---|---|---|
{rows}

## Supuestos

- El precio histórico es el de la línea del pedido; el precio de catálogo no lo reemplaza.
- Los outliers por IQR son alertas, no errores: un pedido mayorista puede tener cantidades altas legítimas.
- Una cantidad nula no se imputa porque alteraría unidades y valor bruto de pedidos.
- Los duplicados por SKU con IDs diferentes se marcan y conservan para no romper referencias transaccionales.
"""
    (docs_dir / "cleaning_decisions.md").write_text(text, encoding="utf-8")


def write_model_report(metrics: dict[str, Any], profiles: pd.DataFrame, docs_dir: Path) -> None:
    """Documenta selección, evaluación, perfiles y limitaciones del modelo."""

    rows = "\n".join(
        f"| {r.segment} | {r.customers} | {r.customer_share:.1%} | {_money(r.total_revenue)} | {r.average_orders:.1f} | {_money(r.average_ticket)} | {r.predominant_country} | {r.predominant_category} | {r.recommended_action} |"
        for r in profiles.itertuples()
    )
    text = f"""# Reporte del modelo — Segmentación de clientes

## Pregunta de negocio

¿Cómo agrupar minoristas por comportamiento de compra para diseñar estrategias diferenciadas?

## Selección metodológica

Se eligió clustering porque una regresión de `revenue` tendría alto riesgo de leakage: el objetivo está definido por `unit_price × quantity` y la cantidad final no es necesariamente conocida antes de confirmar el pedido. En la comunicación ejecutiva, `revenue` se interpreta como **valor bruto de pedidos**, no como ingreso realizado.

Se compararon K-Means, clustering jerárquico y Gaussian Mixture entre 2 y 6 grupos. El resultado seleccionado es **{metrics['selected_model']} con {metrics['clusters']} segmentos**, `random_state=42` cuando aplica, silhouette de **{metrics['silhouette']:.3f}** y segmento mínimo de **{metrics['smallest_cluster_share']:.1%}**.

## Variables y preprocesamiento

Pedidos, valor bruto (`revenue`), ticket, unidades, frecuencia, recencia, amplitud y concentración de categorías, participación Premium, país, tipo de minorista, categoría/canal/segmento dominante. Se imputa mediana en numéricas, moda en categóricas, `log1p` en variables monetarias/unidades, estandarización y one-hot encoding.

## Perfiles

| Segmento | Clientes | Participación | Valor bruto | Pedidos prom. | Ticket prom. | País predominante | Categoría predominante | Acción |
|---|---:|---:|---:|---:|---:|---|---|---|
{rows}

## Limitaciones

- Datos sintéticos y solo un año: los segmentos no se consideran estables sin validación futura.
- Silhouette mide cohesión/separación, no valor causal ni éxito comercial.
- La PCA explica {sum(metrics['pca_explained_variance']):.1%} en dos componentes y se usa solo como proyección.
- Los nombres de segmento son interpretaciones de perfiles medios; deben validarse con ventas.

## Recomendación

Pilotear acciones por segmento durante un trimestre y medir retención, frecuencia, ticket y margen antes de automatizar decisiones.
"""
    (docs_dir / "model_report.md").write_text(text, encoding="utf-8")
