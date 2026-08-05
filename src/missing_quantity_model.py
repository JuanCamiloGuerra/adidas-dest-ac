"""Escenarios auditables para cantidades faltantes.

Entradas: tabla maestra de líneas de pedido.
Salidas: predicciones experimentales, métricas, importancia y sensibilidad.
El modelo nunca sobrescribe ``quantity`` ni utiliza ``revenue`` al entrenar.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from config.settings import RANDOM_STATE

MIN_WHOLESALE_QUANTITY = 5
REFERENCE_PERCENTILE = 0.90
MIN_REFERENCE_COUNT = 3

CATEGORICAL_FEATURES = [
    "order_id", "user_id", "product_id", "order_status", "channel",
    "product_name", "category", "brand", "sku", "price_segment", "country",
    "city", "retailer_type", "quarter", "month_name", "year_month",
]
NUMERIC_FEATURES = [
    "reported_total_products", "line_number", "unit_price",
    "line_discount_percentage", "catalog_price", "catalog_discount_percentage",
    "discount_percentage", "inventory", "rating", "reviews", "age", "year",
    "month", "delivered_flag", "canceled_flag", "price_difference",
    "price_difference_pct",
]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
EXCLUDED_LEAKAGE_COLUMNS = ["quantity", "revenue", "valid_sales_flag", "data_quality_flag"]

ESTIMATION_HIERARCHY = [
    ("Mismo usuario y producto", ["user_id", "product_id"]),
    ("Mismo usuario, categoría y marca", ["user_id", "category", "brand"]),
    ("Mismo usuario y categoría", ["user_id", "category"]),
    ("Mismo producto", ["product_id"]),
    ("Misma categoría y marca", ["category", "brand"]),
    ("Misma categoría", ["category"]),
    ("Distribución global", []),
]


def _preprocessor() -> ColumnTransformer:
    categorical = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("one_hot", OneHotEncoder(handle_unknown="ignore", sparse_output=True)),
    ])
    numeric = Pipeline([("imputer", SimpleImputer(strategy="median"))])
    return ColumnTransformer([
        ("categorical", categorical, CATEGORICAL_FEATURES),
        ("numeric", numeric, NUMERIC_FEATURES),
    ])


def _pipeline() -> Pipeline:
    return Pipeline([
        ("preprocessor", _preprocessor()),
        ("model", RandomForestRegressor(
            n_estimators=400,
            min_samples_leaf=4,
            max_features="sqrt",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )),
    ])


def build_retrospective_scenarios(df: pd.DataFrame) -> pd.DataFrame:
    """Crea mínimos y máximos jerárquicos sin alterar columnas originales."""

    result = df.copy()
    missing = result["quantity"].isna()
    maximum_observed = int(result["quantity"].dropna().max())
    result["quantity_scenario_min"] = result["quantity"]
    result["quantity_scenario_max"] = result["quantity"]
    result["quantity_estimation_method"] = "Dato original"
    result["quantity_reference_count"] = pd.NA
    result["quantity_reference_p90"] = np.nan
    result.loc[missing, "quantity_scenario_min"] = MIN_WHOLESALE_QUANTITY

    valid = result["quantity"].notna() & result["quantity"].gt(0)
    for index, row in result.loc[missing].iterrows():
        for method, columns in ESTIMATION_HIERARCHY:
            mask = valid.copy()
            for column in columns:
                mask &= result[column].isna() if pd.isna(row[column]) else result[column].eq(row[column])
            values = result.loc[mask, "quantity"]
            if len(values) >= MIN_REFERENCE_COUNT:
                p90 = float(values.quantile(REFERENCE_PERCENTILE))
                estimate = int(np.clip(np.ceil(p90), MIN_WHOLESALE_QUANTITY, maximum_observed))
                result.loc[index, ["quantity_scenario_max", "quantity_estimation_method",
                                   "quantity_reference_count", "quantity_reference_p90"]] = [
                    estimate, method, len(values), p90,
                ]
                break
        else:
            raise ValueError(f"No fue posible estimar la línea {index}")

    result["quantity_scenario_min"] = result["quantity_scenario_min"].astype("Int64")
    result["quantity_scenario_max"] = result["quantity_scenario_max"].astype("Int64")
    result["quantity_reference_count"] = result["quantity_reference_count"].astype("Int64")
    result["revenue_scenario_min"] = result["unit_price"] * result["quantity_scenario_min"]
    result["revenue_scenario_max"] = result["unit_price"] * result["quantity_scenario_max"]
    return result


def train_missing_quantity_model(df: pd.DataFrame) -> dict[str, Any]:
    """Valida por pedido y predice solo las cantidades originalmente nulas."""

    required = set(FEATURES + ["quantity", "revenue", "unit_price"])
    missing_columns = sorted(required.difference(df.columns))
    if missing_columns:
        raise ValueError(f"Faltan columnas para el modelo: {missing_columns}")
    if not df["quantity"].isna().any():
        raise ValueError("No existen cantidades nulas para estimar")

    model_data = df[FEATURES + ["quantity"]].copy()
    for identifier in ["order_id", "user_id", "product_id"]:
        model_data[identifier] = model_data[identifier].astype("Int64").astype("string")

    known = model_data["quantity"].notna()
    unknown = ~known
    x_known = model_data.loc[known, FEATURES]
    y_known = model_data.loc[known, "quantity"].astype(float)
    x_unknown = model_data.loc[unknown, FEATURES]
    groups = df.loc[known, "order_id"]

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=RANDOM_STATE)
    train_pos, test_pos = next(splitter.split(x_known, y_known, groups=groups))
    validation = _pipeline()
    validation.fit(x_known.iloc[train_pos], y_known.iloc[train_pos])
    predicted_test = validation.predict(x_known.iloc[test_pos])
    median = float(y_known.iloc[train_pos].median())
    baseline_test = np.full(len(test_pos), median)

    metrics = {
        "model": "RandomForestRegressor",
        "status": "experimental",
        "target": "quantity",
        "known_rows": int(known.sum()),
        "missing_rows": int(unknown.sum()),
        "train_rows": int(len(train_pos)),
        "validation_rows": int(len(test_pos)),
        "mae": float(mean_absolute_error(y_known.iloc[test_pos], predicted_test)),
        "rmse": float(np.sqrt(mean_squared_error(y_known.iloc[test_pos], predicted_test))),
        "r2": float(r2_score(y_known.iloc[test_pos], predicted_test)),
        "baseline_median": median,
        "baseline_mae": float(mean_absolute_error(y_known.iloc[test_pos], baseline_test)),
        "baseline_rmse": float(np.sqrt(mean_squared_error(y_known.iloc[test_pos], baseline_test))),
        "random_state": RANDOM_STATE,
        "grouped_split": "order_id",
        "leakage_columns_excluded": EXCLUDED_LEAKAGE_COLUMNS,
    }
    metrics["recommended_use"] = (
        "scenario_only" if metrics["r2"] <= 0 or metrics["rmse"] >= metrics["baseline_rmse"]
        else "candidate_for_further_validation"
    )

    final_model = clone(validation).fit(x_known, y_known)
    raw = final_model.predict(x_unknown)
    transformed = final_model.named_steps["preprocessor"].transform(x_unknown)
    tree_predictions = np.column_stack([
        tree.predict(transformed) for tree in final_model.named_steps["model"].estimators_
    ])
    maximum_observed = int(y_known.max())
    estimated = np.rint(np.clip(raw, MIN_WHOLESALE_QUANTITY, maximum_observed)).astype(int)

    prediction_columns = [
        "order_id", "user_id", "order_date", "product_id", "product_name",
        "category", "brand", "unit_price", "quantity", "revenue",
    ]
    predictions = df.loc[unknown, prediction_columns].copy()
    predictions["quantity_rf_raw"] = raw
    predictions["quantity_rf_estimated"] = estimated
    predictions["quantity_rf_tree_std"] = tree_predictions.std(axis=1)
    predictions["quantity_rf_tree_p10"] = np.percentile(tree_predictions, 10, axis=1)
    predictions["quantity_rf_tree_p90"] = np.percentile(tree_predictions, 90, axis=1)
    predictions["revenue_rf_estimated"] = predictions["unit_price"] * estimated

    names = final_model.named_steps["preprocessor"].get_feature_names_out()
    importance = pd.DataFrame({
        "transformed_feature": names,
        "importance": final_model.named_steps["model"].feature_importances_,
    }).sort_values("importance", ascending=False, ignore_index=True)

    scenarios = build_retrospective_scenarios(df)
    rf_revenue_total = float(df["revenue"].sum() + predictions["revenue_rf_estimated"].sum())
    original = float(df["revenue"].sum())
    comparison = pd.DataFrame({
        "scenario": ["Original conocido", "Mínimo mayorista", "Random Forest experimental", "Máximo jerárquico"],
        "revenue_total": [original, float(scenarios["revenue_scenario_min"].sum()),
                          rf_revenue_total, float(scenarios["revenue_scenario_max"].sum())],
    })
    comparison["difference_vs_original"] = comparison["revenue_total"] - original
    comparison["change_vs_original_pct"] = comparison["difference_vs_original"] / original * 100

    return {
        "metrics": metrics,
        "predictions": predictions.reset_index(names="source_row_index"),
        "feature_importance": importance,
        "scenario_comparison": comparison,
        "model": final_model,
    }
