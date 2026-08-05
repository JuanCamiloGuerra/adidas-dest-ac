# SportRetail LAM — BI, ETL y segmentación comercial

Solución integral para analizar el desempeño de un distribuidor mayorista ficticio de artículos deportivos en Colombia, México, Argentina, Chile y Perú. Incluye extracción REST paginada, calidad, tabla analítica, dashboard HTML autónomo, resumen ejecutivo, segmentación de clientes, notebooks y pruebas.

[Abrir dashboard publicado](https://juancamiloguerra.github.io/adidas-dest-ac/) · [Resumen ejecutivo](https://juancamiloguerra.github.io/adidas-dest-ac/executive_summary.html)

## Preguntas de negocio

- ¿Cómo funciona el negocio y qué mercados, canales y categorías generan ingresos?
- ¿Qué clientes y productos impulsan el desempeño y dónde existe concentración?
- ¿Qué riesgos de cumplimiento o calidad requieren atención?
- ¿Cómo segmentar minoristas para diseñar acciones comerciales diferenciadas?

## Resultados de la ejecución validada

| Indicador | Resultado |
|---|---:|
| Productos extraídos | 120 |
| Usuarios extraídos | 100 |
| Pedidos extraídos | 200 |
| Líneas en `orders_enriched` | 733 |
| Rango de fechas | 2024-01-02 a 2024-12-28 |
| Ingresos | USD 4.174.258,92 |
| Unidades | 45.414 |
| Clientes compradores | 85 |
| Visualizaciones | 15 en tres vistas interactivas |
| Modelo oficial | Clustering jerárquico, 2 segmentos |
| Silhouette | 0,310 |
| Modelo experimental | Random Forest para `quantity` nula; uso solo como escenario |
| Pruebas | 9 definidas |

Los resultados no se inventaron: se materializan en `data/quality/persistence_validation.json`, `outputs/reports/business_summary.json` y `outputs/model/metrics.json`.

## Hallazgos principales

1. **Colombia genera 27,0% del ingreso** (USD 1.129.080). Conviene proteger cuentas clave y desarrollar el segundo mercado, Perú, con metas trimestrales.
2. **E-commerce B2B concentra 37,8%** (USD 1.578.625). La mezcla ganadora de surtido y ticket debe probarse en Distributor, el canal de menor contribución.
3. **Footwear aporta 47,8%** (USD 1.997.353). La disponibilidad de la categoría tiene efecto desproporcionado y puede habilitar venta cruzada con Accessories.

Otros riesgos: los 10 mayores clientes concentran 26,9%; 46,5% de los pedidos figuran como entregados y 13,5% como cancelados. El último mes crece 13,6% frente al anterior, pero una sola anualidad no permite afirmar estacionalidad.

## Arquitectura

```text
API REST local
    ↓ health + paginación validada
Extracción HTTP → snapshots locales ignorados por Git
    ↓ normalización pedido-producto + joins many-to-one
Calidad y tabla orders_enriched
    ↓
CSV + Parquet + SQLite
    ↓                         ↘
KPIs + hallazgos + Plotly          Features cliente + clustering
    ↓                         ↙
docs/index.html autónomo + documentación + notebooks
```

## Estructura

```text
adidas-dest-ac/
├── api/                 # generador y servidor reproducibles
├── config/              # rutas relativas y parámetros
├── src/                 # cliente, ETL, calidad, BI, ML y HTML
├── scripts/             # ETL, dashboard, modelos y orquestación
├── notebooks/           # notebooks técnicos y guía integral ejecutada
├── data/
│   ├── raw/             # respuestas HTTP locales, no versionadas
│   ├── processed/       # CSV, Parquet y SQLite
│   └── quality/         # reglas y reconciliación
├── docs/                 # GitHub Pages, resumen y metodología
├── outputs/model/        # features, comparaciones, perfiles y artefacto
├── outputs/quantity_model/ # predicciones y sensibilidad de quantity nula
└── tests/                # pruebas unitarias sin red
```

## Tecnologías y versión

Validado con **Python 3.12.1** (compatible con Python 3.9+). Pandas/NumPy procesan datos; Requests consume REST; PyArrow y SQLAlchemy persisten; Plotly produce HTML; scikit-learn entrena; nbformat/nbconvert ejecutan notebooks; pytest valida; FastAPI/Uvicorn/Faker reproducen la API. Todas las versiones están fijadas en `requirements.txt`.

## Instalación en PowerShell

```powershell
git clone https://github.com/JuanCamiloGuerra/adidas-dest-ac.git
Set-Location adidas-dest-ac
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Si PowerShell bloquea la activación, puede ejecutar directamente `.\.venv\Scripts\python.exe` en los comandos siguientes.

## Generar datos y ejecutar la API

Terminal 1:

```powershell
Set-Location api
python generate_data.py
python api_server.py
```

La API queda en `http://127.0.0.1:8000`; la documentación en `http://127.0.0.1:8000/docs`.

Terminal 2:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Debe devolver `status: ok` y conteos de productos, usuarios y pedidos. La API incluye `/products`, `/products/{id}`, `/products/categories/list`, `/users`, `/users/{id}`, `/users/{id}/carts`, `/carts`, `/carts/{id}` y `/health`.

## Ejecutar por componente

Desde la raíz del repositorio y con la API activa:

```powershell
python scripts/run_etl.py
python scripts/run_model.py
python scripts/run_quantity_model.py
python scripts/build_dashboard.py
python scripts/build_notebooks.py
```

La guía principal para estudiar y sustentar el proyecto es
[`notebooks/guia_integral_para_entender_proyecto_sportretail.ipynb`](notebooks/guia_integral_para_entender_proyecto_sportretail.ipynb). Parte de la tabla consolidada y explica calidad, escenarios, análisis comercial, inferencia, modelos, conclusiones y límites hasta antes del dashboard.

**Dashboard de la guía, sin ejecutar código:** [abrir SportRetail LAM en GitHub Pages](https://juancamiloguerra.github.io/adidas-dest-ac/).

Ejecución completa:

```powershell
python scripts/run_all.py
python -m pytest
```

`run_all.py` valida la API, ejecuta ETL y persistencia, genera una vista empresarial, entrena el modelo, integra ML, actualiza documentos y ejecuta notebooks.

## Abrir el dashboard

- Publicado: <https://juancamiloguerra.github.io/adidas-dest-ac/>
- Local: abrir `docs/index.html` con doble clic.
- Alternativa PowerShell: `Start-Process .\docs\index.html`.

El HTML contiene Plotly, JavaScript y datos embebidos; no necesita Python, Jupyter, API, CDN ni servidor una vez generado. Los filtros de país, canal, categoría, segmento, estado y periodo recalculan los gráficos en el navegador.

## Datos y calidad

La fuente oficial del pipeline es HTTP. Los JSON de `api/data` sirven exclusivamente al servidor; `src/extract.py` nunca los abre. La tabla conserva una fila por pedido-producto y usa el precio histórico de la línea. Cantidades nulas no se imputan; outliers por IQR se conservan; dominios se normalizan; joins se validan. Se excluyen email, teléfono y dirección del dataset publicable por minimización.

Véase [decisiones de limpieza](docs/cleaning_decisions.md), [reporte de calidad](data/quality/data_quality_report.csv) y [diccionario](docs/data_dictionary.md).

## Modelo

La opción principal es segmentación de clientes. Predecir revenue antes de confirmar el pedido no es metodológicamente sólido con estas variables: incluir `quantity` y `unit_price` reconstruye exactamente el objetivo; excluirlas reduce la utilidad. Se comparan K-Means, jerárquico y Gaussian Mixture para 2–6 grupos con `random_state=42` donde aplica, silhouette, tamaño mínimo e interpretabilidad.

El modelo elegido es jerárquico con dos segmentos: 72 socios estratégicos (84,7%) y 13 clientes de reactivación prioritaria (15,3%). Silhouette 0,310 indica separación moderada. La PCA explica 50,9% en dos ejes y no se presenta como prueba de separación perfecta. Detalles en [model_report.md](docs/model_report.md).

### Escenario experimental de cantidades faltantes

El proyecto también formaliza un Random Forest para estimar las 12 líneas con `quantity` nula. Se entrena solo con cantidades conocidas, excluye `revenue` para impedir fuga y separa entrenamiento y validación por `order_id`. Su R² es -0,009 y su RMSE (34,39) no supera la mediana (34,23); por ello se conserva como análisis de sensibilidad, nunca como imputación certificada. La tabla maestra permanece intacta. Detalles en [missing_quantity_report.md](docs/missing_quantity_report.md).

## Documentación y outputs

- `docs/index.html`: dashboard y entrada de Pages.
- `docs/executive_summary.html|md`: resumen de una página.
- `docs/methodology.md`: arquitectura, ETL, calidad, visualización y ML.
- `docs/data_dictionary.md`: variable, tipo, fuente, regla, valores, nulos y uso.
- `docs/model_report.md`: selección, resultados y limitaciones.
- `docs/missing_quantity_report.md`: diseño, validación y límites del Random Forest experimental.
- `data/processed/orders_enriched.*`: CSV, Parquet y SQLite.
- `outputs/model/`: features, comparación, segmentos, PCA y modelo.
- `outputs/quantity_model/`: métricas, predicciones, importancia, escenarios y modelo experimental.

## GitHub Pages

Pages está configurado desde la rama `main`, carpeta `/docs`. `docs/.nojekyll` evita transformaciones innecesarias. Para regenerar, ejecute `python scripts/run_all.py`, verifique `python -m pytest`, haga commit y push; Pages desplegará el nuevo `docs/index.html`.

## Limitaciones y próximos pasos

- Datos sintéticos de 2024; no permiten estimar tendencia multianual ni causalidad.
- No existen costos, margen, devoluciones, metas ni eventos promocionales.
- La entrega de 46,5% es un estado observado, no una tasa final de servicio sin corte operacional.
- Los segmentos necesitan validación en periodos futuros y pruebas comerciales controladas.
- Siguiente paso: incorporar margen, inventario histórico y recurrencia multianual; medir uplift de acciones por segmento y monitorear drift.

## Licencia

MIT. Los datos y nombres son sintéticos; no se incluyen documentos originales ni credenciales.
