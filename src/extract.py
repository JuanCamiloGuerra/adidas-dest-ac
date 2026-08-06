"""Extracción oficial de datos mediante HTTP.

Entradas: cliente de API configurado.
Salidas: diccionario de colecciones y snapshots JSON obtenidos por REST.
Dependencias: api_client y utils.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.api_client import SportRetailAPIClient
from src.utils import write_json


def extract_all(client: SportRetailAPIClient, raw_dir: Path, page_size: int) -> dict[str, list[dict[str, Any]]]:
    """Extrae colecciones y valida los contratos de consulta detallada."""

    client.health()
    collections = {
        "products": client.get_paginated("/products", "products", limit=page_size),
        "users": client.get_paginated("/users", "users", limit=page_size),
        "carts": client.get_paginated("/carts", "carts", limit=page_size),
    }
    if not all(collections.values()):
        raise ValueError("La API devolvió una colección principal vacía")

    # Los tres listados alimentan la tabla. Estas consultas representativas
    # verifican además los contratos auxiliares publicados por la API sin
    # multiplicar cientos de llamadas que duplicarían los mismos datos.
    product_id = collections["products"][0]["id"]
    cart_id = collections["carts"][0]["id"]
    user_id = collections["carts"][0]["userId"]
    contract_samples = {
        "categories": client.get_json("/products/categories/list"),
        "product_detail": client.get_json(f"/products/{product_id}"),
        "user_detail": client.get_json(f"/users/{user_id}"),
        "user_carts": client.get_json(f"/users/{user_id}/carts"),
        "cart_detail": client.get_json(f"/carts/{cart_id}"),
    }
    if not isinstance(contract_samples["categories"].get("categories"), list):
        raise ValueError("El endpoint de categorías no cumple el contrato esperado")
    if contract_samples["product_detail"].get("id") != product_id:
        raise ValueError("El detalle de producto no coincide con el listado")
    if contract_samples["user_detail"].get("id") != user_id:
        raise ValueError("El detalle de usuario no coincide con el pedido")
    if contract_samples["user_carts"].get("userId") != user_id:
        raise ValueError("Los pedidos por usuario no coinciden con el usuario solicitado")
    if contract_samples["cart_detail"].get("id") != cart_id:
        raise ValueError("El detalle de pedido no coincide con el listado")
    raw_dir.mkdir(parents=True, exist_ok=True)
    for name, records in collections.items():
        # Estos snapshots son evidencia de la respuesta HTTP, no lecturas directas
        # de los JSON suministrados con el caso.
        write_json({"source": "REST API", "count": len(records), name: records}, raw_dir / f"{name}.json")
    return collections
