"""Ejecuta extracción HTTP, transformación, calidad y persistencia."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import (  # noqa: E402
    API_BASE_URL,
    API_MAX_RETRIES,
    API_PAGE_SIZE,
    API_TIMEOUT_SECONDS,
    LOGS_DIR,
    PROCESSED_DIR,
    QUALITY_DIR,
    RAW_DIR,
    ensure_directories,
)
from src.api_client import SportRetailAPIClient  # noqa: E402
from src.data_quality import evaluate_quality  # noqa: E402
from src.extract import extract_all  # noqa: E402
from src.load import persist_orders  # noqa: E402
from src.transform import build_orders_enriched  # noqa: E402
from src.utils import configure_logging, write_json  # noqa: E402


def main() -> dict[str, object]:
    """Orquesta el ETL y retorna una reconciliación serializable."""

    ensure_directories()
    logger = configure_logging(LOGS_DIR / "pipeline.log")
    client = SportRetailAPIClient(API_BASE_URL, API_TIMEOUT_SECONDS, API_MAX_RETRIES, logger)
    extracted = extract_all(client, RAW_DIR, API_PAGE_SIZE)
    orders = build_orders_enriched(extracted["products"], extracted["users"], extracted["carts"])
    orders, quality_report = evaluate_quality(orders)
    quality_report.to_csv(QUALITY_DIR / "data_quality_report.csv", index=False, encoding="utf-8")
    validation = persist_orders(orders, PROCESSED_DIR)
    validation["source_counts"] = {key: len(value) for key, value in extracted.items()}
    write_json(validation, QUALITY_DIR / "persistence_validation.json")
    logger.info("ETL finalizado: %s líneas, revenue=%.2f", len(orders), validation["revenue_sum"])
    return validation


if __name__ == "__main__":
    main()

