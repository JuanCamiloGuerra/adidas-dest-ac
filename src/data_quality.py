"""Evaluación de calidad con reglas cuantificadas y trazables.

Entradas: tabla maestra antes de persistir.
Salidas: tabla con flags por registro y reporte agregado de reglas.
Dependencias: pandas y numpy.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd


Rule = tuple[str, Callable[[pd.DataFrame], pd.Series], str, str, str]


def _outlier_mask(series: pd.Series) -> pd.Series:
    """Identifica extremos por IQR sin concluir que sean errores."""

    valid = series.dropna()
    if valid.empty:
        return pd.Series(False, index=series.index)
    q1, q3 = valid.quantile([0.25, 0.75])
    iqr = q3 - q1
    upper = q3 + 1.5 * iqr
    lower = q1 - 1.5 * iqr
    return (series < lower) | (series > upper)


def evaluate_quality(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aplica reglas, conserva todos los registros y agrega `data_quality_flag`."""

    working = df.copy()
    valid_countries = {"Colombia", "México", "Argentina", "Chile", "Perú"}
    valid_channels = {"Direct Sales", "Distributor", "E-commerce B2B"}
    valid_statuses = {"confirmed", "shipped", "delivered", "cancelled"}
    duplicate_key = working.duplicated(subset=["order_id", "line_number", "product_id"], keep=False)
    rules: list[Rule] = [
        ("Línea duplicada", lambda x: duplicate_key, "Conservar y marcar", "La clave compuesta debe ser única; no se elimina sin evidencia.", "Alta"),
        ("Identificador faltante", lambda x: x[["order_id", "user_id", "product_id"]].isna().any(axis=1), "Conservar y marcar", "La trazabilidad incompleta impide uniones confiables.", "Alta"),
        ("Cantidad nula", lambda x: x["quantity"].isna(), "Conservar; revenue queda nulo", "Imputar cantidad inventaría ventas no observadas.", "Alta"),
        ("Cantidad no positiva", lambda x: x["quantity"].notna() & x["quantity"].le(0), "Conservar y excluir de KPIs", "No representa una venta válida sin nota de crédito.", "Alta"),
        ("Precio nulo", lambda x: x["unit_price"].isna(), "Conservar; revenue queda nulo", "Se prioriza el precio histórico de la línea.", "Alta"),
        ("Precio no positivo", lambda x: x["unit_price"].notna() & x["unit_price"].le(0), "Conservar y excluir de KPIs", "Un precio no positivo requiere revisión de negocio.", "Alta"),
        ("País inconsistente", lambda x: ~x["country"].isin(valid_countries) | x["country"].isna(), "Normalizar variantes conocidas", "Mantiene comparabilidad geográfica sin inventar país.", "Media"),
        ("Canal inconsistente", lambda x: ~x["channel"].isin(valid_channels) | x["channel"].isna(), "Normalizar variantes conocidas", "Evita fragmentar el análisis comercial.", "Media"),
        ("Estado inconsistente", lambda x: ~x["order_status"].isin(valid_statuses) | x["order_status"].isna(), "Normalizar variantes conocidas", "Los estados controlan KPIs de cumplimiento.", "Media"),
        ("Fecha inválida", lambda x: x["order_date"].isna(), "Conservar y marcar", "No se imputa una fecha de pedido sin evidencia.", "Alta"),
        ("Producto sin correspondencia", lambda x: ~x["product_match_flag"], "Conservar atributos de línea", "La línea sigue siendo evidencia transaccional.", "Alta"),
        ("Usuario sin correspondencia", lambda x: ~x["user_match_flag"], "Conservar y marcar", "Evita perder ventas por fallas de dimensión.", "Alta"),
        ("Precio distinto al catálogo", lambda x: x["price_difference"].abs().gt(0.01), "Conservar ambos precios", "La línea refleja la venta histórica; el catálogo es referencia.", "Baja"),
        ("Revenue extremo por IQR", lambda x: _outlier_mask(x["revenue"]), "Conservar y monitorear", "En mayoristas, valores altos pueden ser compras legítimas.", "Media"),
        ("Cantidad extrema por IQR", lambda x: _outlier_mask(x["quantity"]), "Conservar y monitorear", "No se eliminan outliers automáticamente.", "Baja"),
        ("Inventario nulo", lambda x: x["inventory"].isna(), "Conservar nulo", "No afecta el cálculo histórico de ingresos.", "Baja"),
        ("Calificación nula", lambda x: x["rating"].isna(), "Conservar nulo", "No se inventa percepción de producto.", "Baja"),
        ("Duplicado de catálogo por SKU", lambda x: x["catalog_duplicate_flag"].fillna(False), "Conservar y marcar", "Los IDs son distintos; deduplicar SKU rompería trazabilidad.", "Media"),
    ]
    report_rows: list[dict[str, object]] = []
    masks: dict[str, pd.Series] = {}
    for name, mask_fn, action, justification, severity in rules:
        mask = mask_fn(working).fillna(False).astype(bool)
        masks[name] = mask
        affected = int(mask.sum())
        report_rows.append(
            {
                "regla_evaluada": name,
                "registros_revisados": len(working),
                "registros_afectados": affected,
                "porcentaje_afectado": round(affected / len(working) * 100, 2) if len(working) else 0.0,
                "accion_aplicada": action,
                "justificacion": justification,
                "severidad": severity,
            }
        )
    issue_names = np.array(list(masks), dtype=object)
    mask_matrix = np.column_stack([masks[name].to_numpy() for name in issue_names]) if masks else np.empty((len(working), 0))
    working["data_quality_flag"] = [
        "OK" if not row.any() else " | ".join(issue_names[row].tolist()) for row in mask_matrix
    ]
    working["valid_sales_flag"] = (
        working["quantity"].gt(0)
        & working["unit_price"].gt(0)
        & working["revenue"].notna()
        & working["order_id"].notna()
    )
    report = pd.DataFrame(report_rows)
    return working, report

