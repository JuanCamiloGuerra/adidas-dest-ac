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
    """Extrae productos, usuarios y pedidos con paginación validada."""

    client.health()
    collections = {
        "products": client.get_paginated("/products", "products", limit=page_size),
        "users": client.get_paginated("/users", "users", limit=page_size),
        "carts": client.get_paginated("/carts", "carts", limit=page_size),
    }
    raw_dir.mkdir(parents=True, exist_ok=True)
    for name, records in collections.items():
        # Estos snapshots son evidencia de la respuesta HTTP, no lecturas directas
        # de los JSON suministrados con el caso.
        write_json({"source": "REST API", "count": len(records), name: records}, raw_dir / f"{name}.json")
    return collections

