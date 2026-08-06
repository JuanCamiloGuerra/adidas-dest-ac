"""Crea y ejecuta notebooks explicativos sin depender del estado previo del kernel."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"


def _base_notebook(title: str, purpose: str) -> nbf.NotebookNode:
    notebook = nbf.v4.new_notebook()
    notebook.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
    notebook.metadata.language_info = {"name": "python", "version": f"{sys.version_info.major}.{sys.version_info.minor}"}
    notebook.cells = [
        nbf.v4.new_markdown_cell(f"# {title}\n\n{purpose}\n\n**Reproducibilidad:** ejecutar desde la raíz del repositorio después del paso correspondiente de `scripts/run_all.py`."),
        nbf.v4.new_code_cell("from pathlib import Path\nimport sys\nROOT = Path.cwd().resolve()\nif ROOT.name == 'notebooks': ROOT = ROOT.parent\nif str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))\nprint(f'Proyecto detectado: {ROOT.name}')"),
    ]
    return notebook


def _notebooks() -> dict[str, nbf.NotebookNode]:
    etl = _base_notebook("01 · ETL y calidad", "Evidencia de extracción, normalización, reglas de calidad y reconciliación de persistencia.")
    etl.cells.extend([
        nbf.v4.new_code_cell("import json\nimport pandas as pd\norders = pd.read_parquet(ROOT/'data/processed/orders_enriched.parquet')\nquality = pd.read_csv(ROOT/'data/quality/data_quality_report.csv')\nvalidation = json.loads((ROOT/'data/quality/persistence_validation.json').read_text(encoding='utf-8'))\nvalidation['source_counts'], orders.shape"),
        nbf.v4.new_code_cell("orders[['order_id','user_id','product_id','country','category','quantity','unit_price','revenue','data_quality_flag']].head(10)"),
        nbf.v4.new_code_cell("quality.sort_values('registros_afectados', ascending=False).head(10)"),
        nbf.v4.new_markdown_cell("## Conclusión\n\nLos conteos de API, CSV, Parquet y SQLite reconcilian. Las cantidades nulas se conservan y el valor bruto (`revenue`) correspondiente permanece nulo; los outliers se marcan sin eliminarlos."),
    ])
    visual = _base_notebook("02 · Visualización empresarial", "Cálculo reproducible de KPIs y lectura de los principales impulsores.")
    visual.cells.extend([
        nbf.v4.new_code_cell("import pandas as pd\nfrom src.business_insights import calculate_kpis, generate_insights\norders = pd.read_parquet(ROOT/'data/processed/orders_enriched.parquet')\norders['order_date'] = pd.to_datetime(orders['order_date'])\nkpis = calculate_kpis(orders)\nkpis"),
        nbf.v4.new_code_cell("sales = orders[orders['valid_sales_flag']]\nsales.groupby('country')['revenue'].sum().sort_values(ascending=False).to_frame('revenue')"),
        nbf.v4.new_code_cell("pd.DataFrame(generate_insights(orders))[['title','observation','action']]"),
        nbf.v4.new_markdown_cell("## Conclusión\n\nLa narrativa se centra en escala, concentración y cumplimiento. El HTML final implementa los gráficos y filtros sin backend."),
    ])
    model = _base_notebook("03 · Segmentación de clientes", "Selección metodológica, comparación de algoritmos y perfiles comerciales.")
    model.cells.extend([
        nbf.v4.new_code_cell("import json\nimport pandas as pd\nmetrics = json.loads((ROOT/'outputs/model/metrics.json').read_text(encoding='utf-8'))\ncomparison = pd.read_csv(ROOT/'outputs/model/model_comparison.csv')\nprofiles = pd.read_csv(ROOT/'outputs/model/segment_profiles.csv')\nmetrics"),
        nbf.v4.new_code_cell("comparison.sort_values('silhouette', ascending=False).head(10)"),
        nbf.v4.new_code_cell("profiles[['segment','customers','customer_share','total_revenue','average_orders','average_ticket','predominant_country','predominant_category','recommended_action']]"),
        nbf.v4.new_markdown_cell("## Conclusión\n\nLa segmentación es preferible a predecir el valor bruto (`revenue`) porque `quantity` y `unit_price` reconstruyen matemáticamente el objetivo. El silhouette se interpreta como moderado y los segmentos requieren validación comercial futura."),
    ])
    return {"01_etl.ipynb": etl, "02_visualization.ipynb": visual, "03_model.ipynb": model}


def main() -> None:
    """Escribe y ejecuta los tres notebooks en kernels limpios."""

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    NOTEBOOKS.mkdir(parents=True, exist_ok=True)
    for filename, notebook in _notebooks().items():
        path = NOTEBOOKS / filename
        nbf.write(notebook, path)
        executor = ExecutePreprocessor(timeout=180, kernel_name="python3", allow_errors=False)
        executed, _ = executor.preprocess(notebook, {"metadata": {"path": str(ROOT)}})
        nbf.write(executed, path)
        print(f"Ejecutado: {path.name}")


if __name__ == "__main__":
    main()
