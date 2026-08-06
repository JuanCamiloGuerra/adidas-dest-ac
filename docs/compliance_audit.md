# Auditoría de alineación con el requerimiento inicial

Fecha de corte: 5 de agosto de 2026. Esta matriz conecta el requerimiento académico original con evidencia reproducible del repositorio. La auditoría revisa implementación, datos persistidos, documentación, notebooks, HTML y pruebas; no se limita a comprobar que un archivo exista.

## Resultado

**Cumplimiento funcional: completo.** Se verificaron 14 pruebas unitarias sin red, cuatro notebooks ejecutados sin errores, reconciliación exacta de 733 líneas en CSV/Parquet/SQLite, 18 reglas de calidad, ausencia de valores infinitos y seis HTML publicados sin rutas personales. Los datos son sintéticos y las limitaciones analíticas se mantienen expresas.

| Área solicitada | Estado | Evidencia principal | Verificación |
|---|---|---|---|
| Repositorio independiente y reproducible | Cumple | `README.md`, `.gitignore`, `requirements.txt`, rutas relativas en `config/settings.py` | No hay credenciales, JSON fuente ni rutas personales versionadas; dependencias fijadas |
| API REST como fuente oficial | Cumple | `src/api_client.py`, `src/extract.py`, `api/api_server.py` | `/health`, listados paginados y contratos auxiliares se consultan por HTTP; el ETL no abre los JSON del servidor |
| Paginación real y defensiva | Cumple | `SportRetailAPIClient.get_paginated` | Usa `total/skip/limit`, avanza por registros recibidos, limita páginas y detecta cambios de total, páginas vacías, HTTP y JSON inválido |
| Normalización pedido-producto | Cumple | `src/transform.py`, `notebooks/01_etl.ipynb` | Una fila por producto dentro del pedido; clave `order_id + line_number + product_id` sin duplicados |
| Enriquecimiento y reglas comerciales | Cumple | `src/transform.py` | Precio histórico de línea, usuario/producto, `revenue = unit_price × quantity` y segmentos Económico/Medio/Premium |
| Calidad y limpieza trazable | Cumple | `src/data_quality.py`, `data/quality/data_quality_report.csv`, `docs/cleaning_decisions.md` | 18 reglas; outliers y nulos se conservan con flags; no hay imputación silenciosa |
| Persistencia y reconciliación | Cumple | `src/load.py`, `data/processed/`, `persistence_validation.json` | 733 filas y totales idénticos en CSV, Parquet y SQLite; siete índices útiles |
| Dashboard autónomo | Cumple | `docs/index.html`, `src/visualization.py`, `scripts/validate_html.mjs` | Seis filtros y 9 visualizaciones BI principales dentro del rango solicitado de 8–12; 3 vistas de escenarios y 3 de ML son extensiones separadas |
| KPIs e insights cuantificados | Cumple | `src/business_insights.py`, dashboard y resumen | Valor bruto, unidades, pedidos, clientes, tickets, precio, líderes, entregas y comparación temporal; interpretación evita llamar ingreso realizado a todos los estados |
| Resumen ejecutivo Markdown y HTML | Cumple | `docs/executive_summary.md`, `docs/executive_summary.html` | Tres hallazgos priorizados, acciones, riesgos y limitaciones |
| Selección metodológica de ML | Cumple | `src/model_training.py`, `outputs/model/model_comparison.csv`, `docs/model_report.md` | Clustering se justifica frente a regresión con fuga; compara K-Means, jerárquico y GMM para k=2…6 |
| Preparación y evaluación del clustering | Cumple | `src/feature_engineering.py`, `src/model_training.py` | Una fila por cliente, imputación, `log1p`, escalado, one-hot, silhouette, tamaño mínimo, inercia K-Means, reproducibilidad y PCA descriptiva |
| Perfiles y acciones comerciales | Cumple | `outputs/model/segment_profiles.csv`, dashboard, reporte de modelo | Clientes, valor, pedidos, ticket, unidades, recencia, país y categoría predominantes, participación y acción por segmento |
| Random Forest complementario | Cumple con cautela | `src/missing_quantity_model.py`, `docs/missing_quantity_report.md` | Excluye `revenue`, separa por pedido y conserva el resultado solo como escenario porque R² es negativo |
| Notebooks ejecutables | Cumple | `notebooks/01_etl.ipynb`, `02_visualization.ipynb`, `03_model.ipynb` y guía integral | Todas las celdas de código tienen ejecución, no existen salidas de error y la lógica reutilizable permanece en `src/` |
| Automatización | Cumple | `scripts/run_all.py` | Salud → ETL/validación → dashboard → modelos → reportes → notebooks/HTML |
| Pruebas mínimas | Cumple | `tests/` | 14 pruebas: paginación, endpoints, revenue, segmentos, normalización, joins, esquema, nulos, SQLite, HTML, reproducibilidad y no infinitos |
| Documentación integral | Cumple | `README.md`, `docs/methodology.md`, `docs/data_dictionary.md`, reportes y guías HTML | Instalación, comandos, arquitectura, decisiones, resultados, Pages, método, límites y siguientes pasos |
| GitHub Pages | Cumple | `docs/.nojekyll`, `docs/index.html` | Sitio estático con navegación coherente y vínculos relativos entre presentación, API, pipeline, dashboard, escenarios, ML y resumen |

## Reconciliación de resultados publicados

| Control | Resultado validado |
|---|---:|
| Productos / usuarios / pedidos extraídos | 120 / 100 / 200 |
| Líneas de la tabla maestra | 733 |
| Columnas | 48 |
| Pedidos / clientes compradores | 200 / 85 |
| Cantidades nulas conservadas | 12 |
| Unidades conocidas | 45.414 |
| Valor bruto conocido | USD 4.174.258,92 |
| Duplicados de línea / infinitos | 0 / 0 |
| Modelo seleccionado | Jerárquico, 2 segmentos |
| Silhouette / PCA en dos ejes | 0,310 / 50,9% |

## Criterios de interpretación que deben permanecer alineados

- `revenue` es valor bruto de pedidos en todos los estados, no ingreso contable realizado.
- Los descuentos se conservan como atributos observados, pero el contrato no prueba si el precio de línea ya los incorpora; no se descuentan por segunda vez.
- Las 12 cantidades nulas no se sustituyen en la tabla maestra. Los escenarios mínimo, jerárquico y Random Forest son comparadores separados.
- El Random Forest no supera de forma clara la referencia simple y no debe presentarse como una imputación confiable.
- La segmentación es descriptiva y necesita validación temporal y comercial; PCA no demuestra separación perfecta ni causalidad.
- Los datos son sintéticos de una sola anualidad. No permiten afirmar causalidad, estacionalidad multianual, margen o rentabilidad.

## Comando de revalidación

Con la API activa, ejecutar `python scripts/run_all.py`; después ejecutar `python -m pytest -q` y `node scripts/validate_html.mjs`. La publicación es aceptable únicamente si los artefactos regenerados mantienen la reconciliación anterior y el árbol Git contiene solo cambios esperados.
