"""Genera variables de cliente y entrena la segmentación principal."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import MODEL_DIR, PROCESSED_DIR, ensure_directories  # noqa: E402
from src.feature_engineering import build_customer_features  # noqa: E402
from src.model_training import train_segmentation  # noqa: E402
from src.utils import write_json  # noqa: E402


def main() -> dict[str, object]:
    """Carga la tabla persistida, entrena y guarda resultados reproducibles."""

    ensure_directories()
    orders = pd.read_parquet(PROCESSED_DIR / "orders_enriched.parquet")
    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
    features = build_customer_features(orders)
    features.to_csv(MODEL_DIR / "customer_features.csv", index=False, encoding="utf-8")
    result = train_segmentation(features, MODEL_DIR)
    metrics = {
        "selected_model": result["algorithm"],
        "clusters": result["clusters"],
        "silhouette": result["silhouette"],
        "smallest_cluster_share": result["smallest_cluster_share"],
        "pca_explained_variance": result["pca_explained_variance"],
        "customers_modeled": len(features),
        "random_state": 42,
    }
    write_json(metrics, MODEL_DIR / "metrics.json")
    return metrics


if __name__ == "__main__":
    main()

