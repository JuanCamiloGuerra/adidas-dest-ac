# Reporte del modelo — Segmentación de clientes

## Pregunta de negocio

¿Cómo agrupar minoristas por comportamiento de compra para diseñar estrategias diferenciadas?

## Selección metodológica

Se eligió clustering porque una regresión de `revenue` tendría alto riesgo de leakage: el objetivo está definido por `unit_price × quantity` y la cantidad final no es necesariamente conocida antes de confirmar el pedido. En la comunicación ejecutiva, `revenue` se interpreta como **valor bruto de pedidos**, no como ingreso realizado.

Se compararon K-Means, clustering jerárquico y Gaussian Mixture entre 2 y 6 grupos. El resultado seleccionado es **Jerárquico con 2 segmentos**, `random_state=42` cuando aplica, silhouette de **0.310** y segmento mínimo de **15.3%**.

## Variables y preprocesamiento

Pedidos, valor bruto (`revenue`), ticket, unidades, frecuencia, recencia, amplitud y concentración de categorías, participación Premium, país, tipo de minorista, categoría/canal/segmento dominante. Se imputa mediana en numéricas, moda en categóricas, `log1p` en variables monetarias/unidades, estandarización y one-hot encoding.

## Perfiles

| Segmento | Clientes | Participación | Valor bruto | Pedidos prom. | Ticket prom. | País predominante | Categoría predominante | Acción |
|---|---:|---:|---:|---:|---:|---|---|---|
| Socios estratégicos | 72 | 84.7% | USD 4,080,103 | 2.6 | USD 22,913 | Colombia | Footwear | Retención ejecutiva, acuerdos de surtido y plan conjunto de crecimiento. |
| Reactivación prioritaria | 13 | 15.3% | USD 94,156 | 1.2 | USD 6,615 | Chile | Accessories | Campaña de reactivación con contacto comercial y diagnóstico de abandono. |

## Limitaciones

- Datos sintéticos y solo un año: los segmentos no se consideran estables sin validación futura.
- Silhouette mide cohesión/separación, no valor causal ni éxito comercial.
- La PCA explica 50.9% en dos componentes y se usa solo como proyección.
- Los nombres de segmento son interpretaciones de perfiles medios; deben validarse con ventas.

## Recomendación

Pilotear acciones por segmento durante un trimestre y medir retención, frecuencia, ticket y margen antes de automatizar decisiones.
