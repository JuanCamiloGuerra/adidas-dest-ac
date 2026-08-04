# Decisiones de limpieza

La limpieza prioriza trazabilidad: ninguna observación se elimina automáticamente. Las líneas inválidas se conservan con flags y se excluyen solo de los KPIs de venta cuando precio, cantidad o revenue no permiten una transacción válida.

| Regla | Afectados | Acción | Justificación | Severidad |
|---|---:|---|---|---|
| Línea duplicada | 0 (0.00%) | Conservar y marcar | La clave compuesta debe ser única; no se elimina sin evidencia. | Alta |
| Identificador faltante | 0 (0.00%) | Conservar y marcar | La trazabilidad incompleta impide uniones confiables. | Alta |
| Cantidad nula | 12 (1.64%) | Conservar; revenue queda nulo | Imputar cantidad inventaría ventas no observadas. | Alta |
| Cantidad no positiva | 0 (0.00%) | Conservar y excluir de KPIs | No representa una venta válida sin nota de crédito. | Alta |
| Precio nulo | 0 (0.00%) | Conservar; revenue queda nulo | Se prioriza el precio histórico de la línea. | Alta |
| Precio no positivo | 0 (0.00%) | Conservar y excluir de KPIs | Un precio no positivo requiere revisión de negocio. | Alta |
| País inconsistente | 0 (0.00%) | Normalizar variantes conocidas | Mantiene comparabilidad geográfica sin inventar país. | Media |
| Canal inconsistente | 0 (0.00%) | Normalizar variantes conocidas | Evita fragmentar el análisis comercial. | Media |
| Estado inconsistente | 0 (0.00%) | Normalizar variantes conocidas | Los estados controlan KPIs de cumplimiento. | Media |
| Fecha inválida | 0 (0.00%) | Conservar y marcar | No se imputa una fecha de pedido sin evidencia. | Alta |
| Producto sin correspondencia | 0 (0.00%) | Conservar atributos de línea | La línea sigue siendo evidencia transaccional. | Alta |
| Usuario sin correspondencia | 0 (0.00%) | Conservar y marcar | Evita perder ventas por fallas de dimensión. | Alta |
| Precio distinto al catálogo | 0 (0.00%) | Conservar ambos precios | La línea refleja la venta histórica; el catálogo es referencia. | Baja |
| Revenue extremo por IQR | 44 (6.00%) | Conservar y monitorear | En mayoristas, valores altos pueden ser compras legítimas. | Media |
| Cantidad extrema por IQR | 0 (0.00%) | Conservar y monitorear | No se eliminan outliers automáticamente. | Baja |
| Inventario nulo | 8 (1.09%) | Conservar nulo | No afecta el cálculo histórico de ingresos. | Baja |
| Calificación nula | 18 (2.46%) | Conservar nulo | No se inventa percepción de producto. | Baja |
| Duplicado de catálogo por SKU | 0 (0.00%) | Conservar y marcar | Los IDs son distintos; deduplicar SKU rompería trazabilidad. | Media |

## Supuestos

- El precio histórico es el de la línea del pedido; el precio de catálogo no lo reemplaza.
- Los outliers por IQR son alertas, no errores: un pedido mayorista puede tener cantidades altas legítimas.
- Una cantidad nula no se imputa porque alteraría unidades e ingresos.
- Los duplicados por SKU con IDs diferentes se marcan y conservan para no romper referencias transaccionales.
