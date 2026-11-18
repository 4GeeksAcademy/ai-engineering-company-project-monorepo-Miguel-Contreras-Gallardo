# Carpeta `scripts`

Esta carpeta contiene **scripts auxiliares** del monorepo: automatizaciones de desarrollo, utilidades de mantenimiento, tareas repetitivas (setup, lint, migraciones, generación de datos, etc.) y tooling interno.

- **Propósito principal**: agrupar herramientas de soporte que no pertenecen a una app/agente/pipeline específico, pero facilitan el trabajo del equipo.
- **Recomendación**: documenta cada script (qué hace, parámetros, requisitos, ejemplos de uso) y procura que sean reproducibles (y seguros) en distintos entornos.

## Forecasting de ventas

`forecast_sales.py` carga `data/raw/trackflow_sales.csv`, convierte valores vacíos
en nulos, elimina filas incompletas y usa únicamente las filas `consolidated`.
Divide temporalmente los datos: 2016–2023 para entrenamiento y 2024–2025 para
prueba. Las variables causales usan calendario, retardos y medias móviles
calculadas solo con valores anteriores.

Se eligió `RandomForestRegressor` porque hay solo 120 observaciones mensuales,
permite relaciones no lineales, es rápido de ajustar y ofrece una opción
razonablemente interpretable. No se escala: los árboles no requieren escalado
para comparar magnitudes.

El script reporta:

- **MSE**: error cuadrático medio en EUR²; penaliza más los errores grandes.
- **PSI**: cambio de distribución entre ingresos de entrenamiento y prueba.
- **Gini**: capacidad de ordenar meses según su contribución relativa.
- **K2 Score**: en esta implementación, el coeficiente de determinación R².

Un MSE bajo no basta: puede ocultar cambios de distribución, mala ordenación de
los meses o un ajuste pobre relativo a la variabilidad real. Por eso se
reportan también PSI, Gini y K2.

Ejecutar con:

```bash
python scripts/forecast_sales.py
```
