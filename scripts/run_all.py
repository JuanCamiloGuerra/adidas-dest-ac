"""Ejecuta el proyecto completo en orden reproducible."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import API_BASE_URL, API_MAX_RETRIES, API_TIMEOUT_SECONDS  # noqa: E402
from scripts import build_dashboard, build_data_dictionary, build_notebooks, run_etl, run_model  # noqa: E402
from src.api_client import SportRetailAPIClient  # noqa: E402


def main() -> None:
    """Valida API, procesa datos, entrena, documenta y actualiza Pages."""

    client = SportRetailAPIClient(API_BASE_URL, API_TIMEOUT_SECONDS, API_MAX_RETRIES)
    health = client.health()
    print(f"1/7 API disponible: {health['records']}")
    validation = run_etl.main()
    print(f"2/7 ETL validado: {validation['rows']} líneas")
    # Se crea una versión empresarial antes del modelo y luego se actualiza para
    # integrar ML, manteniendo la secuencia solicitada sin artefactos obsoletos.
    build_dashboard.main()
    print("3/7 Dashboard empresarial generado")
    metrics = run_model.main()
    print(f"4/7 Modelo entrenado: {metrics['selected_model']}")
    result = build_dashboard.main()
    print(f"5/7 Dashboard actualizado: {result['charts']} gráficos")
    build_data_dictionary.main()
    build_notebooks.main()
    print("6/7 Diccionario y notebooks ejecutados")
    print("7/7 Reportes y docs/index.html actualizados")


if __name__ == "__main__":
    main()
