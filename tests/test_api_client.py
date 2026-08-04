"""Pruebas unitarias de paginación sin red."""

from __future__ import annotations

from urllib.parse import urlparse

from src.api_client import SportRetailAPIClient


class FakeResponse:
    status_code = 200
    url = "http://test/items"

    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def json(self) -> dict[str, object]:
        return self.payload


class FakeSession:
    def __init__(self) -> None:
        self.items = [{"id": index} for index in range(11)]
        self.calls = 0

    def get(self, url: str, params: dict[str, int] | None = None, timeout: float = 0) -> FakeResponse:
        assert urlparse(url).path == "/items"
        self.calls += 1
        params = params or {}
        skip, limit = params["skip"], params["limit"]
        page = self.items[skip : skip + limit]
        return FakeResponse({"total": len(self.items), "skip": skip, "limit": limit, "items": page})


def test_pagination_recovers_every_record() -> None:
    session = FakeSession()
    client = SportRetailAPIClient("http://test", session=session)
    result = client.get_paginated("/items", "items", limit=4)
    assert [item["id"] for item in result] == list(range(11))
    assert session.calls == 3

