"""Persistencia y reconciliación de la tabla analítica.

Entradas: DataFrame enriquecido y directorio de datos procesados.
Salidas: CSV, Parquet, SQLite y métricas de validación.
Dependencias: pandas, SQLAlchemy y sqlite3.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text

from config.settings import REQUIRED_COLUMNS


def validate_master(df: pd.DataFrame) -> dict[str, Any]:
    """Comprueba esquema, integridad y totales antes y después de persistir."""

    missing = sorted(set(REQUIRED_COLUMNS).difference(df.columns))
    if missing:
        raise ValueError(f"Faltan columnas obligatorias: {missing}")
    if df.empty:
        raise ValueError("orders_enriched no puede estar vacía")
    if df.duplicated(subset=["order_id", "line_number", "product_id"]).any():
        raise ValueError("Existen duplicados en la clave de línea")
    expected = df["unit_price"] * df["quantity"]
    mismatch = ~((df["revenue"].isna() & expected.isna()) | df["revenue"].round(8).eq(expected.round(8)))
    if mismatch.any():
        raise ValueError("Revenue no coincide con unit_price * quantity")
    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "duplicate_lines": int(df.duplicated(subset=["order_id", "line_number", "product_id"]).sum()),
        "quantity_sum": float(df["quantity"].sum(skipna=True)),
        "revenue_sum": float(df["revenue"].sum(skipna=True)),
        "missing_order_id": int(df["order_id"].isna().sum()),
        "missing_user_id": int(df["user_id"].isna().sum()),
        "missing_product_id": int(df["product_id"].isna().sum()),
        "dtypes": {column: str(dtype) for column, dtype in df.dtypes.items()},
    }


def persist_orders(df: pd.DataFrame, processed_dir: Path) -> dict[str, Any]:
    """Guarda tres formatos, crea índices SQLite y reconcilia totales."""

    processed_dir.mkdir(parents=True, exist_ok=True)
    validation = validate_master(df)
    csv_path = processed_dir / "orders_enriched.csv"
    parquet_path = processed_dir / "orders_enriched.parquet"
    db_path = processed_dir / "sportretail.db"
    # Cada formato recibe el tipo más útil: fecha ISO legible en CSV y
    # datetime nativo en Parquet/SQLite para consultas y filtros temporales.
    df.to_csv(csv_path, index=False, encoding="utf-8", date_format="%Y-%m-%d")
    df.to_parquet(parquet_path, index=False)
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    df.to_sql("orders_enriched", engine, if_exists="replace", index=False)
    with engine.begin() as connection:
        for column in ["order_id", "user_id", "product_id", "order_date", "country", "category", "channel"]:
            connection.execute(text(f'CREATE INDEX IF NOT EXISTS "idx_orders_{column}" ON orders_enriched ("{column}")'))
    reloaded_csv = pd.read_csv(csv_path)
    reloaded_parquet = pd.read_parquet(parquet_path)
    with sqlite3.connect(db_path) as connection:
        sqlite_rows = connection.execute("SELECT COUNT(*) FROM orders_enriched").fetchone()[0]
        sqlite_totals = connection.execute(
            "SELECT SUM(quantity), SUM(revenue) FROM orders_enriched"
        ).fetchone()
    for label, rows in [("CSV", len(reloaded_csv)), ("Parquet", len(reloaded_parquet)), ("SQLite", sqlite_rows)]:
        if rows != len(df):
            raise ValueError(f"El conteo de {label} no coincide con memoria")
    if abs(float(sqlite_totals[0]) - validation["quantity_sum"]) > 1e-6 or abs(float(sqlite_totals[1]) - validation["revenue_sum"]) > 1e-6:
        raise ValueError("Los totales SQLite no reconcilian")
    project_root = processed_dir.parents[1]
    validation["paths"] = {
        "csv": csv_path.relative_to(project_root).as_posix(),
        "parquet": parquet_path.relative_to(project_root).as_posix(),
        "sqlite": db_path.relative_to(project_root).as_posix(),
    }
    return validation
