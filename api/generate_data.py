"""Genera el conjunto sintético reproducible de SportRetail LAM.

Entradas: tamaños opcionales de productos, usuarios y pedidos.
Salidas: JSON en ``api/data`` consumidos exclusivamente por el servidor REST.
Dependencias: Faker y biblioteca estándar.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from faker import Faker

SEED = 42
COUNTRIES = ["Colombia", "México", "Argentina", "Chile", "Perú"]
CITIES = {
    "Colombia": ["Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena"],
    "México": ["Ciudad de México", "Guadalajara", "Monterrey", "Puebla", "Tijuana"],
    "Argentina": ["Buenos Aires", "Córdoba", "Rosario", "Mendoza", "Tucumán"],
    "Chile": ["Santiago", "Valparaíso", "Concepción", "Antofagasta", "Temuco"],
    "Perú": ["Lima", "Arequipa", "Trujillo", "Cusco", "Piura"],
}
CATEGORIES = {
    "Footwear": ["Running Shoes", "Basketball Shoes", "Training Shoes", "Slides", "Football Boots", "Tennis Shoes"],
    "Apparel": ["Performance T-Shirt", "Training Shorts", "Track Jacket", "Compression Tights", "Football Jersey", "Sports Bra"],
    "Accessories": ["Sport Backpack", "Water Bottle", "Cap", "Headband", "Gym Bag", "Sport Socks"],
    "Equipment": ["Resistance Bands", "Jump Rope", "Yoga Mat", "Foam Roller", "Training Gloves", "Agility Ladder"],
    "Team Sports": ["Football", "Basketball", "Volleyball", "Tennis Racket", "Goalkeeper Gloves", "Shin Guards"],
}
PRICE_RANGES = {"Footwear": (55, 280), "Apparel": (20, 130), "Accessories": (10, 90), "Equipment": (15, 110), "Team Sports": (12, 160)}
BRANDS = ["SportRetail Pro", "AthletX", "CoreFit", "SpeedMax", "UrbanSport", "PowerEdge"]
RETAILER_TYPES = ["Department Store", "Sports Chain", "Independent", "Online Retailer", "Superstore"]
FAKERS = {country: Faker(["es_CO", "es_MX", "es_AR", "es_CL", "es_ES"][index]) for index, country in enumerate(COUNTRIES)}


def generate_products(n: int = 120) -> list[dict[str, object]]:
    """Crea catálogo con nulos y duplicados intencionales para control de calidad."""

    products: list[dict[str, object]] = []
    product_id = 1
    for category, items in CATEGORIES.items():
        low, high = PRICE_RANGES[category]
        for item in items:
            for variant in range(1, (n // 30) + 2):
                brand = random.choice(BRANDS)
                price = round(random.uniform(low, high), 2)
                discount = round(random.uniform(0, 25), 1)
                stock = random.randint(0, 500)
                rating = round(random.uniform(2.5, 5.0), 1)
                reviews = random.randint(10, 800)
                if random.random() < 0.04:
                    stock = None
                if random.random() < 0.03:
                    rating = None
                products.append({
                    "id": product_id,
                    "title": f"{brand} {item} v{variant}",
                    "category": category,
                    "brand": brand,
                    "price": price,
                    "discountPercentage": discount,
                    "stock": stock,
                    "rating": rating,
                    "reviews": reviews,
                    "sku": f"SR-{category[:3].upper()}-{product_id:04d}",
                })
                product_id += 1
                if product_id > n + 1:
                    break
            if product_id > n + 1:
                break
    for _ in range(3):
        duplicate = random.choice(products[:20]).copy()
        duplicate["id"] = product_id
        products.append(duplicate)
        product_id += 1
    return products[:n]


def generate_users(n: int = 100) -> list[dict[str, object]]:
    """Crea minoristas balanceados por país con perfiles comerciales."""

    assigned = COUNTRIES * (n // len(COUNTRIES) + 1)
    random.shuffle(assigned)
    assigned = assigned[:n]
    users = []
    for index, country in enumerate(assigned, 1):
        fake = FAKERS[country]
        city = random.choice(CITIES[country])
        age = random.randint(22, 55)
        email = fake.email() if random.random() > 0.03 else None
        users.append({
            "id": index,
            "firstName": fake.first_name(),
            "lastName": fake.last_name(),
            "email": email,
            "age": age,
            "country": country,
            "city": city,
            "phone": fake.phone_number(),
            "address": fake.street_address(),
            "retailerType": random.choice(RETAILER_TYPES),
        })
    return users


def generate_carts(users: list[dict[str, object]], products: list[dict[str, object]], n: int = 200) -> list[dict[str, object]]:
    """Crea pedidos mayoristas con precio histórico en cada línea."""

    carts = []
    for cart_id in range(1, n + 1):
        user = random.choice(users)
        n_products = random.randint(1, 6)
        selected = random.sample(products, min(n_products, len(products)))
        lines = []
        for product in selected:
            quantity = random.randint(5, 120)
            if random.random() < 0.02:
                quantity = None
            lines.append({
                "id": product["id"], "title": product["title"], "price": product["price"],
                "quantity": quantity,
                "category": product["category"], "discountPercentage": product["discountPercentage"],
            })
        carts.append({
            "id": cart_id, "userId": user["id"], "totalProducts": len(lines), "products": lines,
            "orderDate": f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "status": random.choices(["confirmed", "shipped", "delivered", "cancelled"], weights=[20, 25, 45, 10])[0],
            "channel": random.choice(["Direct Sales", "Distributor", "E-commerce B2B"]),
        })
    return carts


def build_all() -> dict[str, list[dict[str, object]]]:
    """Reinicia semillas y escribe los tres recursos de la API."""

    random.seed(SEED)
    Faker.seed(SEED)
    payload = {"products": generate_products(), "users": generate_users()}
    payload["carts"] = generate_carts(payload["users"], payload["products"])
    output_dir = Path(__file__).resolve().parent / "data"
    output_dir.mkdir(exist_ok=True)
    for key, records in payload.items():
        (output_dir / f"{key}.json").write_text(
            json.dumps({key: records, "total": len(records), "skip": 0, "limit": len(records)}, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"{key}: {len(records)} registros")
    return payload


if __name__ == "__main__":
    build_all()
