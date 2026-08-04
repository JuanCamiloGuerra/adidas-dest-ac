"""Entrenamiento y evaluación honesta de segmentación de clientes.

Entradas: variables agregadas por cliente.
Salidas: asignaciones, perfiles, PCA, métricas y artefacto reproducible.
Dependencias: scikit-learn, pandas, numpy y joblib.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.metrics import silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from config.settings import RANDOM_STATE


NUMERIC_FEATURES = [
    "order_count",
    "total_revenue",
    "average_order_revenue",
    "units",
    "average_days_between_orders",
    "recency_days",
    "category_count",
    "premium_revenue_share",
    "category_concentration_hhi",
]
CATEGORICAL_FEATURES = ["country", "retailer_type", "top_category", "top_channel", "dominant_price_segment"]


def _preprocessor() -> ColumnTransformer:
    """Define imputación, logaritmo monetario, escalamiento y one-hot."""

    log_features = ["total_revenue", "average_order_revenue", "units"]
    regular_features = [column for column in NUMERIC_FEATURES if column not in log_features]
    log_pipeline = Pipeline(
        [("imputer", SimpleImputer(strategy="median")), ("log1p", FunctionTransformer(np.log1p)), ("scale", StandardScaler())]
    )
    regular_pipeline = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    categorical_pipeline = Pipeline(
        [("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]
    )
    return ColumnTransformer(
        [("log_numeric", log_pipeline, log_features), ("numeric", regular_pipeline, regular_features), ("categorical", categorical_pipeline, CATEGORICAL_FEATURES)],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def _segment_name(row: pd.Series, medians: pd.Series) -> str:
    """Asigna un nombre comercial comprensible a partir del perfil observado."""

    if row["total_revenue"] >= medians["total_revenue"] and row["order_count"] >= medians["order_count"]:
        return "Socios estratégicos"
    if row["average_order_revenue"] >= medians["average_order_revenue"]:
        return "Compradores de alto ticket"
    if row["recency_days"] > medians["recency_days"] and row["order_count"] <= medians["order_count"]:
        return "Reactivación prioritaria"
    return "Desarrollo de potencial"


def train_segmentation(features: pd.DataFrame, model_dir: Path) -> dict[str, Any]:
    """Compara K-Means, jerárquico y GMM; selecciona por calidad e interpretabilidad."""

    if len(features) < 12:
        raise ValueError("Se requieren al menos 12 clientes para una segmentación defendible")
    model_dir.mkdir(parents=True, exist_ok=True)
    preprocessor = _preprocessor()
    matrix = preprocessor.fit_transform(features)
    max_k = min(6, len(features) - 1)
    comparisons: list[dict[str, Any]] = []
    candidate_labels: dict[tuple[str, int], np.ndarray] = {}
    for k in range(2, max_k + 1):
        estimators = {
            "KMeans": KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=20),
            "Jerárquico": AgglomerativeClustering(n_clusters=k, linkage="ward"),
            "GaussianMixture": GaussianMixture(n_components=k, random_state=RANDOM_STATE, n_init=5),
        }
        for name, estimator in estimators.items():
            labels = estimator.fit_predict(matrix)
            counts = np.bincount(labels)
            score = float(silhouette_score(matrix, labels)) if len(np.unique(labels)) > 1 else -1.0
            smallest_share = float(counts.min() / len(labels))
            inertia = float(estimator.inertia_) if hasattr(estimator, "inertia_") else None
            comparisons.append(
                {"algorithm": name, "clusters": k, "silhouette": score, "smallest_cluster_share": smallest_share, "inertia": inertia}
            )
            candidate_labels[(name, k)] = labels
    comparison = pd.DataFrame(comparisons)
    # Exigimos al menos 8% por segmento para evitar microgrupos poco accionables.
    eligible = comparison[comparison["smallest_cluster_share"].ge(0.08)].copy()
    if eligible.empty:
        eligible = comparison.copy()
    selected_row = eligible.sort_values(["silhouette", "smallest_cluster_share"], ascending=False).iloc[0]
    algorithm = str(selected_row["algorithm"])
    k = int(selected_row["clusters"])
    labels = candidate_labels[(algorithm, k)]
    assigned = features.copy()
    assigned["cluster"] = labels
    raw_profiles = assigned.groupby("cluster")[NUMERIC_FEATURES].mean()
    medians = assigned[NUMERIC_FEATURES].median()
    names = {cluster: _segment_name(profile, medians) for cluster, profile in raw_profiles.iterrows()}
    # Los nombres pueden coincidir; el sufijo mantiene identidad sin fingir perfiles distintos.
    seen: dict[str, int] = {}
    unique_names: dict[int, str] = {}
    for cluster, name in names.items():
        seen[name] = seen.get(name, 0) + 1
        unique_names[cluster] = name if seen[name] == 1 else f"{name} {seen[name]}"
    assigned["segment"] = assigned["cluster"].map(unique_names)
    action_map = {
        "Socios estratégicos": "Retención ejecutiva, acuerdos de surtido y plan conjunto de crecimiento.",
        "Compradores de alto ticket": "Aumentar frecuencia con reposición programada y beneficios por recurrencia.",
        "Reactivación prioritaria": "Campaña de reactivación con contacto comercial y diagnóstico de abandono.",
        "Desarrollo de potencial": "Venta cruzada gradual y educación sobre categorías complementarias.",
    }
    profile = (
        assigned.groupby(["cluster", "segment"], as_index=False)
        .agg(
            customers=("user_id", "nunique"),
            total_revenue=("total_revenue", "sum"),
            average_revenue=("total_revenue", "mean"),
            average_orders=("order_count", "mean"),
            average_ticket=("average_order_revenue", "mean"),
            average_units=("units", "mean"),
            average_recency_days=("recency_days", "mean"),
            average_category_count=("category_count", "mean"),
            premium_share=("premium_revenue_share", "mean"),
        )
    )
    profile["customer_share"] = profile["customers"] / profile["customers"].sum()
    profile["recommended_action"] = profile["segment"].str.replace(r" \d+$", "", regex=True).map(action_map)
    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    coords = pca.fit_transform(matrix)
    pca_frame = assigned[["user_id", "customer_name", "segment"]].copy()
    pca_frame["pca_1"] = coords[:, 0]
    pca_frame["pca_2"] = coords[:, 1]
    bundle = {"preprocessor": preprocessor, "algorithm": algorithm, "clusters": k, "labels": labels}
    joblib.dump(bundle, model_dir / "customer_segmentation.joblib")
    assigned.to_csv(model_dir / "customer_segments.csv", index=False, encoding="utf-8")
    comparison.to_csv(model_dir / "model_comparison.csv", index=False, encoding="utf-8")
    profile.to_csv(model_dir / "segment_profiles.csv", index=False, encoding="utf-8")
    pca_frame.to_csv(model_dir / "pca_coordinates.csv", index=False, encoding="utf-8")
    return {
        "algorithm": algorithm,
        "clusters": k,
        "silhouette": float(selected_row["silhouette"]),
        "smallest_cluster_share": float(selected_row["smallest_cluster_share"]),
        "pca_explained_variance": [float(value) for value in pca.explained_variance_ratio_],
        "comparison": comparison,
        "assignments": assigned,
        "profiles": profile,
        "pca": pca_frame,
    }
