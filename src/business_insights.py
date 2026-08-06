"""Cálculo de KPIs y hallazgos ejecutivos basados en datos observados.

Entradas: tabla maestra validada.
Salidas: diccionario de indicadores y lista de recomendaciones cuantificadas.
Dependencias: pandas.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


def valid_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Limita KPIs a líneas con cantidad y precio positivos, sin borrar la fuente."""

    if "valid_sales_flag" in df:
        return df[df["valid_sales_flag"].astype(bool)].copy()
    return df[df["quantity"].gt(0) & df["unit_price"].gt(0) & df["revenue"].notna()].copy()


def _leader(frame: pd.DataFrame, dimension: str) -> tuple[str, float]:
    values = frame.groupby(dimension, dropna=False)["revenue"].sum().sort_values(ascending=False)
    if values.empty:
        return "Sin datos", 0.0
    return str(values.index[0]), float(values.iloc[0])


def calculate_kpis(df: pd.DataFrame) -> dict[str, Any]:
    """Calcula KPIs sobre ventas válidas y cumplimiento a nivel pedido."""

    sales = valid_sales(df)
    order_revenue = sales.groupby("order_id")["revenue"].sum()
    country, country_revenue = _leader(sales, "country")
    channel, channel_revenue = _leader(sales, "channel")
    category, category_revenue = _leader(sales, "category")
    total_revenue = float(sales["revenue"].sum())
    order_status = df[["order_id", "order_status"]].drop_duplicates("order_id")
    delivered_rate = float(order_status["order_status"].eq("delivered").mean()) if len(order_status) else 0.0
    monthly = sales.groupby("year_month")["revenue"].sum().sort_index()
    monthly_change = float(monthly.pct_change().iloc[-1]) if len(monthly) > 1 and monthly.iloc[-2] else None
    return {
        "total_revenue": total_revenue,
        "units_sold": float(sales["quantity"].sum()),
        "orders": int(sales["order_id"].nunique()),
        "customers": int(sales["user_id"].nunique()),
        "average_order_revenue": float(order_revenue.mean()),
        "average_unit_price": float((sales["revenue"].sum() / sales["quantity"].sum()) if sales["quantity"].sum() else 0),
        "leading_country": country,
        "leading_country_share": country_revenue / total_revenue if total_revenue else 0,
        "leading_channel": channel,
        "leading_channel_share": channel_revenue / total_revenue if total_revenue else 0,
        "leading_category": category,
        "leading_category_share": category_revenue / total_revenue if total_revenue else 0,
        "delivered_order_rate": delivered_rate,
        "latest_month_change": monthly_change,
        "formula_notes": {
            "total_revenue": "Valor bruto: suma de unit_price × quantity para líneas válidas de todos los estados.",
            "units_sold": "Suma de quantity para líneas válidas.",
            "orders": "Conteo distinto de order_id con al menos una línea válida.",
            "customers": "Conteo distinto de user_id con al menos una línea válida.",
            "average_order_revenue": "Ingreso total dividido por pedidos distintos.",
            "average_unit_price": "Ingreso total dividido por unidades vendidas.",
            "delivered_order_rate": "Pedidos entregados divididos por pedidos totales, a nivel pedido.",
        },
    }


def generate_insights(df: pd.DataFrame) -> list[dict[str, str]]:
    """Genera hallazgos cuantificados con implicación y acción recomendada."""

    sales = valid_sales(df)
    total = sales["revenue"].sum()
    by_country = sales.groupby("country")["revenue"].sum().sort_values(ascending=False)
    by_channel = sales.groupby("channel")["revenue"].sum().sort_values(ascending=False)
    by_category = sales.groupby("category")["revenue"].sum().sort_values(ascending=False)
    by_customer = sales.groupby(["user_id", "customer_name", "country"], dropna=False)["revenue"].sum().sort_values(ascending=False)
    monthly = sales.groupby("year_month")["revenue"].sum().sort_index()
    order_status = df[["order_id", "order_status"]].drop_duplicates("order_id")
    delivered = order_status["order_status"].eq("delivered").mean()
    cancelled = order_status["order_status"].eq("cancelled").mean()
    top_country_share = by_country.iloc[0] / total
    top_channel_share = by_channel.iloc[0] / total
    top_category_share = by_category.iloc[0] / total
    top10_share = by_customer.head(10).sum() / total
    latest_change = monthly.pct_change().iloc[-1] if len(monthly) > 1 else 0.0
    second_country = by_country.index[1] if len(by_country) > 1 else "otros mercados"
    return [
        {
            "title": "Concentración geográfica",
            "observation": f"{by_country.index[0]} genera {top_country_share:.1%} del valor bruto de pedidos (${by_country.iloc[0]:,.0f}).",
            "importance": "La exposición al mercado líder condiciona el crecimiento regional.",
            "implication": "Una desaceleración local tendría impacto material sobre el total.",
            "action": f"Proteger cuentas clave en {by_country.index[0]} y desarrollar {second_country} con metas de participación trimestrales.",
        },
        {
            "title": "Canal que sostiene el negocio",
            "observation": f"{by_channel.index[0]} concentra {top_channel_share:.1%} del valor bruto de pedidos (${by_channel.iloc[0]:,.0f}).",
            "importance": "La mezcla de canales determina cobertura, costo comercial y escalabilidad.",
            "implication": "Existe oportunidad de replicar las prácticas del canal líder sin depender exclusivamente de él.",
            "action": f"Analizar surtido y ticket de {by_channel.index[0]} y transferir las combinaciones ganadoras a {by_channel.index[-1]}.",
        },
        {
            "title": "Categoría tractora",
            "observation": f"{by_category.index[0]} aporta {top_category_share:.1%} del valor bruto de pedidos (${by_category.iloc[0]:,.0f}).",
            "importance": "El surtido líder es el principal motor de monetización.",
            "implication": "Disponibilidad e inventario en esta categoría tienen efecto desproporcionado.",
            "action": f"Priorizar disponibilidad de {by_category.index[0]} y diseñar venta cruzada con {by_category.index[-1]}.",
        },
        {
            "title": "Concentración de clientes",
            "observation": f"Los 10 clientes con mayor valor de pedidos representan {top10_share:.1%} del total bruto.",
            "importance": "La concentración revela tanto valor de cuentas clave como riesgo de dependencia.",
            "implication": "Retener estas cuentas es prioritario, pero la cartera debe ampliarse.",
            "action": "Asignar planes de cuenta a los clientes principales y activar crecimiento en segmentos de potencial medio.",
        },
        {
            "title": "Cumplimiento de pedidos",
            "observation": f"{delivered:.1%} de los pedidos están entregados y {cancelled:.1%} cancelados.",
            "importance": "Los pedidos no entregados representan revenue operativo aún expuesto.",
            "implication": "Mejorar conversión de confirmados/enviados puede elevar ingreso realizado sin captar demanda nueva.",
            "action": "Crear seguimiento semanal por estado, país y canal; investigar causas de cancelación antes de definir metas.",
        },
        {
            "title": "Cierre del periodo",
            "observation": f"El valor bruto de pedidos del último mes cambió {latest_change:+.1%} frente al mes anterior.",
            "importance": "La variación mensual sirve como alerta, pero una sola anualidad no define estacionalidad.",
            "implication": "No debe extrapolarse como tendencia estructural.",
            "action": "Monitorear una serie histórica más larga y contrastar la variación con pedidos, unidades y calendario comercial.",
        },
    ]
