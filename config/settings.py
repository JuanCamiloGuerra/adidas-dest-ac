"""Configuración reproducible basada en rutas relativas.

Entradas: variables de entorno opcionales para URL, timeout y paginación.
Salidas: constantes de rutas y parámetros compartidos por el pipeline.
Dependencias: pathlib y os de la biblioteca estándar.
"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
QUALITY_DIR = DATA_DIR / "quality"
DOCS_DIR = PROJECT_ROOT / "docs"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
MODEL_DIR = OUTPUTS_DIR / "model"
QUANTITY_MODEL_DIR = OUTPUTS_DIR / "quantity_model"
REPORTS_DIR = OUTPUTS_DIR / "reports"
LOGS_DIR = OUTPUTS_DIR / "logs"

API_BASE_URL = os.getenv("SPORTRETAIL_API_URL", "http://127.0.0.1:8000").rstrip("/")
API_TIMEOUT_SECONDS = float(os.getenv("SPORTRETAIL_API_TIMEOUT", "10"))
API_PAGE_SIZE = int(os.getenv("SPORTRETAIL_API_PAGE_SIZE", "37"))
API_MAX_RETRIES = int(os.getenv("SPORTRETAIL_API_MAX_RETRIES", "3"))
RANDOM_STATE = 42

REQUIRED_COLUMNS = [
    "order_id",
    "user_id",
    "country",
    "product_id",
    "product_name",
    "category",
    "price_segment",
    "quantity",
    "unit_price",
    "revenue",
]


def ensure_directories() -> None:
    """Crea los directorios de salida sin depender del directorio de ejecución."""

    for path in [RAW_DIR, PROCESSED_DIR, QUALITY_DIR, DOCS_DIR, MODEL_DIR, QUANTITY_MODEL_DIR, REPORTS_DIR, LOGS_DIR]:
        path.mkdir(parents=True, exist_ok=True)
