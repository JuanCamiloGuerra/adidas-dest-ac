# Metodología técnica

## Arquitectura

La solución sigue un flujo reproducible: API REST local → cliente HTTP paginado → normalización y enriquecimiento → reglas de calidad → CSV/Parquet/SQLite → analítica y segmentación → HTML estático. `config/` centraliza rutas relativas; `src/` contiene lógica reutilizable; `scripts/` orquesta; `tests/` valida contratos sin requerir la API.

## Extracción y paginación

El pipeline valida primero `/health`. `SportRetailAPIClient.get_paginated` consulta `/products`, `/users` y `/carts` con `limit=37`, lee `total`, valida `skip`, incrementa el desplazamiento por el número real recibido y termina solo al reconciliar el total. Incluye timeout, reintentos limitados para fallos transitorios, estados HTTP, estructura JSON, páginas vacías prematuras, cambio de total y límite de páginas. Los endpoints singulares y `/docs` se comprobaron en la auditoría.

## Normalización y enriquecimiento

Cada producto dentro de un pedido se convierte en una línea con `order_id`, `user_id` y `line_number`. Los joins con usuarios y productos son `many_to_one`; se verifica que no multipliquen filas. El precio de la línea se conserva como histórico y el catálogo queda como comparador. Se excluyen email, teléfono y dirección por minimización de datos.

## Transformaciones

`revenue = unit_price × quantity`. El segmento es Económico por debajo de 50, Medio entre 50 y 200 inclusive y Premium por encima de 200. Se normalizan variantes conocidas de país, canal y estado; las fechas inválidas quedan nulas. Se derivan año, trimestre, mes, `year_month`, flags de entrega/cancelación, diferencias de precio y trazabilidad de joins.

## Calidad y limpieza

Se evalúan 18 reglas sobre duplicados, IDs, cantidades, precios, dominios, fechas, joins, diferencias de precio, outliers e incompletitud de producto. Los outliers se detectan por IQR, se cuantifican y se conservan: el contexto mayorista hace plausible una compra elevada. Una cantidad nula no se imputa porque inventaría unidades y valor bruto. `valid_sales_flag` permite excluir líneas no válidas de KPIs sin borrarlas.

El campo técnico `revenue = unit_price × quantity` representa valor bruto de la línea en todos los estados. Para hablar de ingreso realizado se filtran pedidos entregados y todavía se requiere evidencia de facturación, pago y devoluciones.

## Persistencia

La tabla se guarda en UTF-8 CSV, Parquet y SQLite. SQLite crea índices para pedido, usuario, producto, fecha, país, categoría y canal. Se reconcilian filas, columnas, claves, unidades y revenue entre memoria y los tres formatos.

## Visualización

El dashboard embebe Plotly, datos y JavaScript. Sus seis filtros operan en el navegador y recalculan KPIs y nueve vistas empresariales; tres visualizaciones adicionales presentan ML. No existen CDN, rutas `C:\`, servidor Python ni dependencia de la API después de generar el HTML.

## Machine Learning

Se seleccionó segmentación de clientes. Predecir revenue antes de confirmación no es defendible con las variables disponibles: `quantity` y `unit_price` reconstruyen el objetivo, y excluirlas elimina información esencial. Se agregan variables RFM ampliadas, amplitud/concentración de categorías y preferencias; se imputan medianas/modas, se aplica `log1p`, estandarización y one-hot. Se comparan K-Means, jerárquico y Gaussian Mixture entre 2 y 6 grupos. La selección prioriza silhouette y evita segmentos menores al 8% cuando es posible. PCA es solo una proyección descriptiva.

Como componente complementario se formalizó un Random Forest para `quantity` nula. Los identificadores se tratan como categorías, las demás variables categóricas usan one-hot y los predictores numéricos se imputan con mediana. `revenue` se excluye explícitamente y la validación agrupa por pedido. Debido a que R² es negativo y el RMSE no mejora la mediana, el resultado se guarda únicamente como escenario experimental y no modifica `orders_enriched`.

## Pruebas

Pytest valida paginación completa, normalización, revenue, fronteras de segmento, joins, columnas, calidad, SQLite, HTML, reproducibilidad y ausencia de infinitos. Las respuestas HTTP se simulan para no depender permanentemente de la API.

## Limitaciones

Los datos son sintéticos y cubren 2024; no incluyen costo, margen, devoluciones, metas ni causalidad comercial. Los segmentos deben validarse fuera de muestra y revisarse con cada nuevo periodo.
