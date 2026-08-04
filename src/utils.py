"""Utilidades compartidas para logging y serialización.

Entradas: objetos de Python, rutas y nombres de logger.
Salidas: logs consistentes y archivos JSON auditables.
Dependencias: biblioteca estándar.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def configure_logging(log_path: Path | None = None) -> logging.Logger:
    """Configura logging idempotente para consola y, opcionalmente, archivo."""

    logger = logging.getLogger("sportretail")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger


class EnhancedJSONEncoder(json.JSONEncoder):
    """Serializa tipos NumPy/Pandas sin convertir números en texto."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return None if np.isnan(obj) else float(obj)
        if isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        if isinstance(obj, (pd.Timestamp,)):
            return obj.isoformat()
        return super().default(obj)


def write_json(payload: Any, path: Path) -> None:
    """Escribe JSON UTF-8 con formato legible y reemplazo atómico simple."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, cls=EnhancedJSONEncoder),
        encoding="utf-8",
    )
    temporary.replace(path)

