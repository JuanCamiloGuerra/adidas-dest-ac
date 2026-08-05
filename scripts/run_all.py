"""Ejecuta el proyecto completo en orden reproducible."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import API_BASE_URL, API_MAX_RETRIES, API_TIMEOUT_SECONDS  # noqa: E402
from scripts import (  # noqa: E402
    build_api_guide,
    build_dashboard,
    build_data_dictionary,
    build_notebooks,
    run_etl,
    run_model,
    run_quantity_model,
)
from src.api_client import SportRetailAPIClient  # noqa: E402


def main() -> None:
    """Valida API, procesa datos, entrena, documenta y actualiza Pages."""

    client = SportRetailAPIClient(API_BASE_URL, API_TIMEOUT_SECONDS, API_MAX_RETRIES)
    health = client.health()
    print(f"1/9 API disponible: {health['records']}")
    validation = run_etl.main()
    print(f"2/9 ETL validado: {validation['rows']} líneas")
    build_api_guide.main()
    print("3/9 Guía visual de API y tabla maestra generada")
    # Se crea una versión empresarial antes del modelo y luego se actualiza para
    # integrar ML, manteniendo la secuencia solicitada sin artefactos obsoletos.
    build_dashboard.main()
    print("4/9 Dashboard empresarial generado")
    metrics = run_model.main()
    print(f"5/9 Segmentación entrenada: {metrics['selected_model']}")
    quantity_metrics = run_quantity_model.main()
    print(f"6/9 Escenario quantity: {quantity_metrics['recommended_use']}")
    result = build_dashboard.main()
    print(f"7/9 Dashboard actualizado: {result['charts']} gráficos")
    build_data_dictionary.main()
    build_notebooks.main()
    print("8/9 Diccionario y notebooks ejecutados")
    print("9/9 Reportes y documentación HTML actualizados")


if __name__ == "__main__":
    main()
