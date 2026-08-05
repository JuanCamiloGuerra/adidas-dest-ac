# Random Forest experimental para cantidades faltantes

## Objetivo

Estimar un escenario posible para las 12 líneas con `quantity` nula y cuantificar su efecto sobre revenue sin modificar la tabla maestra. Este componente es complementario; la segmentación jerárquica continúa siendo el modelo oficial del proyecto.

## Diseño

- Variable objetivo: `quantity`.
- Entrenamiento: 721 líneas con cantidad conocida.
- Validación: separación por `order_id`, evitando líneas del mismo pedido en ambos conjuntos.
- Categóricas: imputación por moda y One-Hot Encoding.
- Numéricas: imputación por mediana.
- Identificadores: tratados como etiquetas.
- Fuga excluida: `revenue`, flags de validez y campos derivados del objetivo.
- Algoritmo: 400 árboles, `min_samples_leaf=4`, `max_features="sqrt"`, semilla 42.

## Validación

| Métrica | Random Forest | Mediana de entrenamiento |
|---|---:|---:|
| MAE | 29,58 | 29,90 |
| RMSE | 34,39 | 34,23 |
| R² | -0,009 | No aplica |

El modelo no demuestra generalización superior a una regla simple. Sus predicciones no deben utilizarse en KPIs certificados.

## Sensibilidad de revenue

| Escenario | Revenue | Cambio frente al conocido |
|---|---:|---:|
| Original conocido | 4.174.258,92 | 0,00% |
| Mínimo mayorista | 4.179.686,22 | +0,13% |
| Random Forest experimental | 4.242.768,18 | +1,64% |
| Máximo jerárquico | 4.268.800,58 | +2,26% |

## Artefactos

- `outputs/quantity_model/validation_metrics.json`
- `outputs/quantity_model/missing_quantity_predictions.csv`
- `outputs/quantity_model/scenario_comparison.csv`
- `outputs/quantity_model/feature_importance.csv`
- `outputs/quantity_model/random_forest_quantity.joblib`

## Decisión

Se conserva como experimento reproducible y evidencia de una evaluación honesta. La mejora prioritaria no es cambiar de algoritmo, sino incorporar variables que expliquen demanda: tamaño del cliente, promociones históricas, inventario al ordenar, calendario, contrato y presupuesto.
