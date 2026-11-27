# Evaluación del modelo de pronóstico de TrackFlow

## Alcance y contexto

Se evaluó `revenue_eur` de la fila `market = "consolidated"` del dataset
mensual de TrackFlow. La partición final conserva los primeros ocho años para
entrenamiento y los dos últimos para prueba. La validación cruzada usa
`TimeSeriesSplit(n_splits=5)`, sin barajar datos.

El contrato de entrada conserva exactamente los campos `month`,
`revenue_eur`, `shipments_processed`, `avg_revenue_per_shipment_eur` y
`market`. `revenue_eur` es el objetivo; `shipments_processed` representa los
envíos procesados por Los Ángeles y Zaragoza, y
`avg_revenue_per_shipment_eur` es el ingreso medio por envío. El modelo usa
solo las filas `market = "consolidated"`, como exige el briefing, y no inventa
IDs de entidades que no existen en este dataset mensual.

Cada fold conserva el orden de `month`: el último mes de entrenamiento es
anterior al primer mes de validación. Los lags (`revenue_lag_1`, `3`, `6`, `12`)
y las ventanas (`revenue_rolling_mean_3`, `6`, `12`) se recalculan solo con el
prefijo histórico que termina en el último mes de validación del fold. Por
tanto, ninguna ventana puede leer una observación futura. Verificaciones
explícitas: chronology=`True` y
feature_leakage=`True`.

## Resultados de validación cruzada

| Métrica | Entrenamiento (media ± desviación estándar) | Validación (media ± desviación estándar) |
|---|---:|---:|
| MAE (EUR) | 14121.14 ± 5241.40 | 54162.85 ± 15238.55 |
| RMSE (EUR) | 20089.29 ± 7732.63 | 71086.84 ± 18183.98 |

La curva de aprendizaje está en `data/eval/learning_curve.png` y muestra el
error RMSE de entrenamiento y validación conforme crece la ventana temporal.

## Métrica preferida para negocio

MAE refleja mejor el costo operativo típico para Thomas y Ana: expresa en EUR
el desvío mensual promedio, sin sobrerreaccionar a los picos de noviembre y
diciembre. RMSE se conserva como diagnóstico porque penaliza más los errores
grandes durante esos picos, que pueden afectar la planificación de almacén,
pero no debe ser la única métrica de decisión.

## Métricas del conjunto de prueba

El conjunto de prueba contiene los 24 meses de 2024-01 a
2025-12. El MSE es
`10988063645.22 EUR²` (1.09% del cuadrado del ingreso mensual promedio del entrenamiento); PSI=9.2454; Gini=0.8976;
K2 Score (R²)=0.6246.

## Diagnóstico

**Clasificación: overfitting.**

La clasificación se apoya en la brecha media entre RMSE de entrenamiento y
validación y en la tendencia de ambas líneas de la curva de aprendizaje; no se
basa en un único fold. Acción correctiva concreta: Reducir la varianza del Random Forest aumentando `min_samples_leaf` y limitar `max_depth`; el gap train-validación indica que los árboles están aprendiendo ruido de meses concretos.
