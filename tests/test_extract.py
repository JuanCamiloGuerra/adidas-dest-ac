"""Pruebas del uso integral del contrato REST sin depender de red."""

from __future__ import annotations

from typing import Any

from src.extract import extract_all


class ContractClient:
    """Cliente simulado que registra cada endpoint utilizado por el ETL."""

    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self.collections = collections
        self.calls: list[str] = []
        self.product_id = collections["products"][0]["id"]
        self.cart_id = collections["carts"][0]["id"]
        self.user_id = collections["carts"][0]["userId"]

    def health(self) -> dict[str, Any]:
        self.calls.append("/health")
        return {"status": "ok", "records": {}}

    def get_paginated(self, endpoint: str, key: str, limit: int) -> list[dict[str, Any]]:
        self.calls.append(endpoint)
        return self.collections[key]

    def get_json(self, endpoint: str) -> dict[str, Any]:
        self.calls.append(endpoint)
        responses = {
            "/products/categories/list": {"categories": ["Footwear"]},
            f"/products/{self.product_id}": {"id": self.product_id},
            f"/users/{self.user_id}": {"id": self.user_id},
            f"/users/{self.user_id}/carts": {"userId": self.user_id, "total": 1, "carts": []},
            f"/carts/{self.cart_id}": {"id": self.cart_id},
        }
        return responses[endpoint]


def test_extract_uses_collections_and_reference_endpoints(
    tmp_path, api_collections: dict[str, list[dict[str, Any]]]
) -> None:
    client = ContractClient(api_collections)
    extracted = extract_all(client, tmp_path, page_size=37)
    assert extracted == api_collections
    assert set(client.calls) == {
        "/health", "/products", "/users", "/carts",
        "/products/categories/list", "/products/1", "/users/7",
        "/users/7/carts", "/carts/10",
    }
