"""Construcción de variables de cliente para segmentación.

Entradas: tabla de líneas de pedido enriquecida.
Salidas: una fila por cliente con conducta de compra y atributos de perfil.
Dependencias: pandas y numpy.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.business_insights import valid_sales


def _dominant_value(group: pd.DataFrame, column: str) -> str:
    """Devuelve el valor con mayor revenue y resuelve empates alfabéticamente."""

    weighted = group.groupby(column, dropna=False)["revenue"].sum().sort_index().sort_values(ascending=False, kind="stable")
    return str(weighted.index[0]) if len(weighted) else "Sin dato"


def build_customer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega comportamiento RFM ampliado y preferencias comerciales."""

    sales = valid_sales(df)
    max_date = sales["order_date"].max()
    rows: list[dict[str, object]] = []
    for user_id, group in sales.groupby("user_id"):
        order_values = group.groupby("order_id")["revenue"].sum()
        category_values = group.groupby("category")["revenue"].sum()
        total_revenue = group["revenue"].sum()
        premium_revenue = group.loc[group["price_segment"].eq("Premium"), "revenue"].sum()
        concentration = float((category_values / total_revenue).pow(2).sum()) if total_revenue else 0.0
        dates = group[["order_id", "order_date"]].drop_duplicates().sort_values("order_date")["order_date"]
        frequency_days = float(dates.diff().dt.days.dropna().mean()) if len(dates) > 1 else np.nan
        rows.append(
            {
                "user_id": int(user_id),
                "customer_name": group["customer_name"].dropna().iloc[0] if group["customer_name"].notna().any() else f"Cliente {user_id}",
                "country": group["country"].dropna().iloc[0] if group["country"].notna().any() else "Sin dato",
                "retailer_type": group["retailer_type"].dropna().iloc[0] if group["retailer_type"].notna().any() else "Sin dato",
                "order_count": int(group["order_id"].nunique()),
                "total_revenue": float(total_revenue),
                "average_order_revenue": float(order_values.mean()),
                "units": float(group["quantity"].sum()),
                "average_days_between_orders": frequency_days,
                "recency_days": int((max_date - group["order_date"].max()).days),
                "category_count": int(group["category"].nunique()),
                "top_category": _dominant_value(group, "category"),
                "top_channel": _dominant_value(group, "channel"),
                "dominant_price_segment": _dominant_value(group, "price_segment"),
                "premium_revenue_share": float(premium_revenue / total_revenue) if total_revenue else 0.0,
                "category_concentration_hhi": concentration,
            }
        )
    return pd.DataFrame(rows).sort_values("user_id").reset_index(drop=True)

