"""Genera el diccionario de datos desde el esquema materializado."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

DERIVED = {
    "customer_name", "product_name", "country_original", "channel_original", "status_original",
    "discount_percentage", "revenue", "price_segment", "year", "quarter", "month", "month_name",
    "year_month", "delivered_flag", "canceled_flag", "product_match_flag", "user_match_flag",
    "price_difference", "price_difference_pct", "data_quality_flag", "valid_sales_flag",
}
CART_FIELDS = {
    "order_id", "user_id", "order_date", "order_status", "channel", "reported_total_products",
    "line_number", "product_id", "line_product_name", "line_category", "unit_price", "quantity",
    "line_discount_percentage",
}
PRODUCT_FIELDS = {
    "catalog_product_name", "category", "brand", "catalog_price", "catalog_discount_percentage",
    "inventory", "rating", "reviews", "sku", "catalog_duplicate_flag",
}
USER_FIELDS = {"age", "country", "city", "retailer_type"}
DEFINITIONS = {
    "order_id": "Identificador del pedido.", "user_id": "Identificador del minorista.",
    "product_id": "Identificador del producto vendido.", "line_number": "Posición del producto dentro del pedido.",
    "unit_price": "Precio histórico registrado en la línea.", "quantity": "Unidades solicitadas en la línea.",
    "revenue": "Valor bruto de la línea para cualquier estado; no equivale necesariamente a ingreso realizado.", "price_segment": "Banda comercial según precio unitario.",
    "catalog_price": "Precio actual del catálogo, conservado para comparación.",
    "discount_percentage": "Descuento de la línea o, si falta, del catálogo.",
    "data_quality_flag": "Lista de reglas de calidad activadas por la línea.",
    "valid_sales_flag": "Indica si precio, cantidad, revenue e ID permiten incluir la línea en KPIs.",
    "category_concentration_hhi": "No forma parte de orders_enriched; se calcula en customer_features.",
}
RULES = {
    "revenue": "unit_price × quantity; nulo si alguno es nulo.",
    "price_segment": "Económico < 50; Medio entre 50 y 200 inclusive; Premium > 200.",
    "year": "Año de order_date.", "quarter": "Trimestre calendario de order_date.",
    "month": "Mes numérico de order_date.", "month_name": "Nombre español del mes.",
    "year_month": "Periodo YYYY-MM derivado de order_date.",
    "delivered_flag": "1 cuando order_status = delivered; 0 en otro caso.",
    "canceled_flag": "1 cuando order_status = cancelled; 0 en otro caso.",
    "product_match_flag": "True si el join por product_id encontró catálogo.",
    "user_match_flag": "True si el join por user_id encontró usuario.",
    "price_difference": "unit_price - catalog_price.",
    "price_difference_pct": "price_difference / catalog_price; nulo si catálogo es cero.",
    "valid_sales_flag": "quantity > 0, unit_price > 0, revenue no nulo y order_id presente.",
}


def _source(column: str) -> str:
    if column in CART_FIELDS:
        return "GET /carts"
    if column in PRODUCT_FIELDS:
        return "GET /products"
    if column in USER_FIELDS:
        return "GET /users"
    return "Derivada en ETL"


def _values(series: pd.Series) -> str:
    non_null = series.dropna()
    unique = non_null.nunique()
    if unique <= 12:
        return ", ".join(str(value) for value in sorted(non_null.astype(str).unique())) or "Sin valores"
    if pd.api.types.is_numeric_dtype(non_null):
        return f"Rango observado: {non_null.min():.2f} a {non_null.max():.2f}"
    return f"{unique} valores observados"


def main() -> None:
    """Escribe una fila por variable con metadatos y tratamiento de nulos."""

    frame = pd.read_parquet(ROOT / "data" / "processed" / "orders_enriched.parquet")
    rows = []
    for column in frame.columns:
        nulls = int(frame[column].isna().sum())
        definition = DEFINITIONS.get(column, column.replace("_", " ").capitalize() + ".")
        rule = RULES.get(column, "Copia del endpoint con trim/normalización cuando corresponde." if column not in DERIVED else "Derivada durante transformación; ver src/transform.py.")
        null_treatment = "No aplica; sin nulos observados." if nulls == 0 else f"Se conserva; {nulls} nulos observados y se activa flag cuando corresponde."
        rows.append(f"| `{column}` | `{frame[column].dtype}` | {_source(column)} | {definition} | {rule} | {_values(frame[column])} | {null_treatment} | Análisis, trazabilidad o control de calidad. |")
    content = """# Diccionario de datos — `orders_enriched`

La granularidad es una línea por combinación pedido-producto. Los posibles valores y rangos corresponden a la ejecución actual obtenida por HTTP.

| Variable | Tipo | Fuente | Definición | Regla de cálculo | Posibles valores | Tratamiento de nulos | Uso analítico |
|---|---|---|---|---|---|---|---|
""" + "\n".join(rows) + "\n"
    (ROOT / "docs" / "data_dictionary.md").write_text(content, encoding="utf-8")
    print(f"Diccionario generado: {len(rows)} variables")


if __name__ == "__main__":
    main()
