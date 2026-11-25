# Carpeta `scripts`

Esta carpeta contiene **scripts auxiliares** del monorepo: automatizaciones de desarrollo, utilidades de mantenimiento, tareas repetitivas (setup, lint, migraciones, generación de datos, etc.) y tooling interno.

- **Propósito principal**: agrupar herramientas de soporte que no pertenecen a una app/agente/pipeline específico, pero facilitan el trabajo del equipo.
- **Recomendación**: documenta cada script (qué hace, parámetros, requisitos, ejemplos de uso) y procura que sean reproducibles (y seguros) en distintos entornos.

## Forecasting de ventas

`forecast_sales.py` carga `data/raw/trackflow_sales.csv`, valida las columnas
documentadas de TrackFlow, convierte valores vacíos en nulos, elimina filas
incompletas y usa únicamente las filas `consolidated`. Divide temporalmente los
datos en los primeros 8 años para entrenamiento y los 2 más recientes para
prueba. Las variables causales usan calendario, retardos y medias móviles
calculadas solo con valores anteriores.

Se eligió `RandomForestRegressor` porque hay solo 120 observaciones mensuales,
permite relaciones no lineales, es rápido de ajustar y ofrece una opción
razonablemente interpretable sin una búsqueda de hiperparámetros costosa. Las
variables se escalan con `StandardScaler` dentro de un `Pipeline`; el escalador
se ajusta exclusivamente con entrenamiento y evita comparaciones erróneas entre
magnitudes.

El script reporta:

- **MSE**: error cuadrático medio en EUR²; penaliza más los errores grandes.
- **PSI**: cambio de distribución entre ingresos de entrenamiento y prueba.
- **Gini**: capacidad de ordenar meses según su contribución relativa.
- **K2 Score**: en esta implementación, el coeficiente de determinación R².

Un MSE bajo no basta: puede ocultar cambios de distribución, mala ordenación de
los meses o un ajuste pobre relativo a la variabilidad real. Por eso se
reportan también PSI, Gini y K2.

Además, se genera `data/process/trackflow_sales_forecast.png`, con los valores
reales de los 2 años de prueba, la predicción y una banda P10-P90 calculada a
partir de las predicciones de los árboles del bosque.

Ejecutar con:

```bash
python scripts/forecast_sales.py
```
