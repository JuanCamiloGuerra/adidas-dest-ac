"""Fixtures sintéticos pequeños para pruebas sin API activa."""

from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def api_collections() -> dict[str, list[dict[str, object]]]:
    products = [
        {"id": 1, "title": "Producto A", "category": "Footwear", "brand": "Marca", "price": 49.99, "discountPercentage": 5, "stock": 10, "rating": 4.0, "reviews": 3, "sku": "SKU-1"},
        {"id": 2, "title": "Producto B", "category": "Apparel", "brand": "Marca", "price": 200, "discountPercentage": 0, "stock": None, "rating": None, "reviews": 2, "sku": "SKU-2"},
        {"id": 3, "title": "Producto C", "category": "Equipment", "brand": "Marca", "price": 201, "discountPercentage": 2, "stock": 5, "rating": 4.8, "reviews": 6, "sku": "SKU-3"},
    ]
    users = [{"id": 7, "firstName": "Ana", "lastName": "López", "email": "a@example.com", "age": 30, "country": " Colombia ", "city": "Bogotá", "phone": "1", "address": "X", "retailerType": "Independent"}]
    carts = [{"id": 10, "userId": 7, "totalProducts": 3, "orderDate": "2024-01-15", "status": "delivered", "channel": "Direct Sales", "products": [
        {"id": 1, "title": "Producto A", "price": 49.99, "quantity": 2, "category": "Footwear", "discountPercentage": 5},
        {"id": 2, "title": "Producto B", "price": 200, "quantity": 3, "category": "Apparel", "discountPercentage": 0},
        {"id": 3, "title": "Producto C", "price": 201, "quantity": 1, "category": "Equipment", "discountPercentage": 2},
    ]}]
    return {"products": products, "users": users, "carts": carts}


@pytest.fixture
def customer_features() -> pd.DataFrame:
    rows = []
    for index in range(24):
        high = index >= 12
        rows.append({
            "user_id": index + 1, "customer_name": f"Cliente {index+1}", "country": "Colombia" if index % 2 else "Chile",
            "retailer_type": "Chain" if high else "Independent", "order_count": 8 + index % 3 if high else 1 + index % 2,
            "total_revenue": 30000 + index * 200 if high else 2500 + index * 80,
            "average_order_revenue": 4000 + index * 20 if high else 1200 + index * 10, "units": 500 + index if high else 50 + index,
            "average_days_between_orders": 20 + index % 5 if high else 90 + index, "recency_days": index % 10 if high else 40 + index,
            "category_count": 5 if high else 2, "top_category": "Footwear" if high else "Apparel", "top_channel": "Distributor" if high else "Direct Sales",
            "dominant_price_segment": "Premium" if high else "Medio", "premium_revenue_share": .6 if high else .05,
            "category_concentration_hhi": .25 if high else .7,
        })
    return pd.DataFrame(rows)

