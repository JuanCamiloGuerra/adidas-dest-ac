"""Servidor REST local y paginado para el caso SportRetail LAM.

Entradas: JSON generados en ``api/data``.
Salidas: endpoints HTTP documentados con OpenAPI.
Dependencias: FastAPI y Uvicorn.
"""

from __future__ import annotations

import json
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Query

from generate_data import build_all

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
if not all((DATA / f"{name}.json").exists() for name in ["products", "users", "carts"]):
    build_all()


def _load(name: str) -> list[dict[str, object]]:
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))[name]


PRODUCTS, USERS, CARTS = _load("products"), _load("users"), _load("carts")
app = FastAPI(title="SportRetail LAM API", version="1.0.0", description="API mock mayorista para el caso de BI")


def _page(items: list[dict[str, object]], skip: int, limit: int, key: str) -> dict[str, object]:
    subset = items[skip : skip + limit]
    return {"total": len(items), "skip": skip, "limit": limit, "count": len(subset), key: subset}


@app.get("/health")
def health() -> dict[str, object]:
    return {"status": "ok", "records": {"products": len(PRODUCTS), "users": len(USERS), "carts": len(CARTS)}}


@app.get("/products/categories/list")
def categories() -> dict[str, list[str]]:
    return {"categories": sorted({str(item["category"]) for item in PRODUCTS})}


@app.get("/products")
def products(limit: int = Query(30, ge=1, le=200), skip: int = Query(0, ge=0), category: str | None = None, brand: str | None = None) -> dict[str, object]:
    items = PRODUCTS
    if category:
        items = [item for item in items if str(item["category"]).casefold() == category.casefold()]
    if brand:
        items = [item for item in items if str(item["brand"]).casefold() == brand.casefold()]
    return _page(items, skip, limit, "products")


@app.get("/products/{product_id}")
def product(product_id: int) -> dict[str, object]:
    return next((item for item in PRODUCTS if item["id"] == product_id), None) or _not_found("Producto", product_id)


@app.get("/users")
def users(limit: int = Query(30, ge=1, le=200), skip: int = Query(0, ge=0), country: str | None = None, retailerType: str | None = None) -> dict[str, object]:
    items = USERS
    if country:
        items = [item for item in items if str(item["country"]).casefold() == country.casefold()]
    if retailerType:
        items = [item for item in items if str(item["retailerType"]).casefold() == retailerType.casefold()]
    return _page(items, skip, limit, "users")


@app.get("/users/{user_id}/carts")
def user_carts(user_id: int) -> dict[str, object]:
    items = [item for item in CARTS if item["userId"] == user_id]
    if not items:
        raise HTTPException(404, f"Sin pedidos para usuario {user_id}")
    return {"userId": user_id, "total": len(items), "carts": items}


@app.get("/users/{user_id}")
def user(user_id: int) -> dict[str, object]:
    return next((item for item in USERS if item["id"] == user_id), None) or _not_found("Usuario", user_id)


@app.get("/carts")
def carts(limit: int = Query(30, ge=1, le=300), skip: int = Query(0, ge=0), userId: int | None = None, status: str | None = None, channel: str | None = None) -> dict[str, object]:
    items = CARTS
    if userId:
        items = [item for item in items if item["userId"] == userId]
    if status:
        items = [item for item in items if str(item["status"]).casefold() == status.casefold()]
    if channel:
        items = [item for item in items if str(item["channel"]).casefold() == channel.casefold()]
    return _page(items, skip, limit, "carts")


@app.get("/carts/{cart_id}")
def cart(cart_id: int) -> dict[str, object]:
    return next((item for item in CARTS if item["id"] == cart_id), None) or _not_found("Pedido", cart_id)


def _not_found(entity: str, identifier: int) -> None:
    raise HTTPException(404, f"{entity} {identifier} no encontrado")


if __name__ == "__main__":
    uvicorn.run("api_server:app", host="127.0.0.1", port=8000, reload=False)

