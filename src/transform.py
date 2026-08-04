"""Normalización y enriquecimiento de pedidos mayoristas.

Entradas: colecciones JSON obtenidas por la API.
Salidas: DataFrame con una fila por combinación pedido-producto.
Dependencias: pandas y numpy.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


COUNTRY_MAP = {
    "colombia": "Colombia",
    "méxico": "México",
    "mexico": "México",
    "argentina": "Argentina",
    "chile": "Chile",
    "perú": "Perú",
    "peru": "Perú",
}
CHANNEL_MAP = {
    "direct sales": "Direct Sales",
    "distributor": "Distributor",
    "e-commerce b2b": "E-commerce B2B",
    "b2b e-commerce": "E-commerce B2B",
}
STATUS_MAP = {
    "confirmed": "confirmed",
    "shipped": "shipped",
    "delivered": "delivered",
    "cancelled": "cancelled",
    "canceled": "cancelled",
}


def _clean_text(series: pd.Series) -> pd.Series:
    """Normaliza espacios externos y vacíos sin alterar acentos ni nombres propios."""

    return series.astype("string").str.strip().replace({"": pd.NA})


def normalize_carts(carts: list[dict[str, Any]]) -> pd.DataFrame:
    """Explota arreglos de productos conservando trazabilidad de pedido y usuario."""

    rows: list[dict[str, Any]] = []
    for cart in carts:
        products = cart.get("products") or []
        for line_number, product in enumerate(products, start=1):
            rows.append(
                {
                    "order_id": cart.get("id"),
                    "user_id": cart.get("userId"),
                    "order_date": cart.get("orderDate"),
                    "order_status": cart.get("status"),
                    "channel": cart.get("channel"),
                    "reported_total_products": cart.get("totalProducts"),
                    "line_number": line_number,
                    "product_id": product.get("id"),
                    "line_product_name": product.get("title"),
                    "line_category": product.get("category"),
                    "unit_price": product.get("price"),
                    "quantity": product.get("quantity"),
                    "line_discount_percentage": product.get("discountPercentage"),
                }
            )
    return pd.DataFrame(rows)


def _prepare_products(products: list[dict[str, Any]]) -> pd.DataFrame:
    """Prepara atributos de catálogo y señala duplicados de negocio por SKU."""

    frame = pd.DataFrame(products).rename(
        columns={
            "id": "product_id",
            "title": "catalog_product_name",
            "price": "catalog_price",
            "discountPercentage": "catalog_discount_percentage",
            "stock": "inventory",
        }
    )
    frame = frame.drop_duplicates(subset=["product_id"], keep="first").copy()
    frame["catalog_duplicate_flag"] = frame.duplicated(subset=["sku"], keep=False)
    return frame


def _prepare_users(users: list[dict[str, Any]]) -> pd.DataFrame:
    """Prepara la dimensión cliente con nombres analíticos consistentes."""

    frame = pd.DataFrame(users).rename(
        columns={
            "id": "user_id",
            "firstName": "first_name",
            "lastName": "last_name",
            "retailerType": "retailer_type",
        }
    )
    frame = frame.drop_duplicates(subset=["user_id"], keep="first").copy()
    frame["customer_name"] = (
        _clean_text(frame["first_name"]).fillna("") + " " + _clean_text(frame["last_name"]).fillna("")
    ).str.strip()
    return frame


def build_orders_enriched(
    products: list[dict[str, Any]], users: list[dict[str, Any]], carts: list[dict[str, Any]]
) -> pd.DataFrame:
    """Construye la tabla maestra sin eliminar registros atípicos o incompletos."""

    lines = normalize_carts(carts)
    product_dim = _prepare_products(products)
    user_dim = _prepare_users(users)
    expected_lines = len(lines)
    enriched = lines.merge(product_dim, on="product_id", how="left", validate="many_to_one", indicator="_product_join")
    enriched = enriched.merge(user_dim, on="user_id", how="left", validate="many_to_one", indicator="_user_join")
    if len(enriched) != expected_lines:
        raise ValueError("Los joins modificaron indebidamente el número de líneas")

    enriched["product_name"] = _clean_text(enriched["line_product_name"]).fillna(
        _clean_text(enriched["catalog_product_name"])
    )
    enriched["category"] = _clean_text(enriched["line_category"]).fillna(_clean_text(enriched["category"]))
    for column in ["country", "city", "retailer_type", "brand", "sku", "channel", "order_status"]:
        enriched[column] = _clean_text(enriched[column])
    enriched["country_original"] = enriched["country"]
    enriched["channel_original"] = enriched["channel"]
    enriched["status_original"] = enriched["order_status"]
    enriched["country"] = enriched["country"].str.casefold().map(COUNTRY_MAP).fillna(enriched["country"])
    enriched["channel"] = enriched["channel"].str.casefold().map(CHANNEL_MAP).fillna(enriched["channel"])
    enriched["order_status"] = (
        enriched["order_status"].str.casefold().map(STATUS_MAP).fillna(enriched["order_status"].str.casefold())
    )

    for column in ["unit_price", "quantity", "catalog_price", "inventory", "rating", "reviews"]:
        enriched[column] = pd.to_numeric(enriched[column], errors="coerce")
    enriched["discount_percentage"] = pd.to_numeric(
        enriched["line_discount_percentage"], errors="coerce"
    ).fillna(pd.to_numeric(enriched["catalog_discount_percentage"], errors="coerce"))
    # El precio de la línea es histórico; el catálogo se conserva solo como referencia.
    enriched["revenue"] = enriched["unit_price"] * enriched["quantity"]
    enriched["price_segment"] = np.select(
        [enriched["unit_price"] < 50, enriched["unit_price"].between(50, 200, inclusive="both"), enriched["unit_price"] > 200],
        ["Económico", "Medio", "Premium"],
        default="Sin clasificar",
    )
    enriched["order_date"] = pd.to_datetime(enriched["order_date"], errors="coerce")
    enriched["year"] = enriched["order_date"].dt.year.astype("Int64")
    enriched["quarter"] = enriched["order_date"].dt.quarter.astype("Int64")
    enriched["month"] = enriched["order_date"].dt.month.astype("Int64")
    enriched["month_name"] = enriched["order_date"].dt.month.map(
        {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
    )
    enriched["year_month"] = enriched["order_date"].dt.to_period("M").astype("string")
    enriched["delivered_flag"] = (enriched["order_status"] == "delivered").astype("int8")
    enriched["canceled_flag"] = (enriched["order_status"] == "cancelled").astype("int8")
    enriched["product_match_flag"] = enriched["_product_join"].eq("both")
    enriched["user_match_flag"] = enriched["_user_join"].eq("both")
    enriched["price_difference"] = enriched["unit_price"] - enriched["catalog_price"]
    enriched["price_difference_pct"] = enriched["price_difference"] / enriched["catalog_price"].replace(0, np.nan)
    # Los datos de contacto no aportan al objetivo analítico y se excluyen del
    # artefacto publicable, incluso siendo sintéticos, por minimización de datos.
    return enriched.drop(columns=["_product_join", "_user_join", "email", "phone", "address", "first_name", "last_name"])
