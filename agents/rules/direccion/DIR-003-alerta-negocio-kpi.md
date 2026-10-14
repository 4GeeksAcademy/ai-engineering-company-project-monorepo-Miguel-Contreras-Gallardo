# DIR-003: Alerta de negocio — desviación grave de KPI

**Ámbito:** Dirección
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un KPI estratégico se desvía más del 10% respecto al objetivo, se detecta una brecha de ingresos, o se identifica un riesgo de pérdida de cliente estratégico, se debe activar el análisis ejecutivo y coordinar acciones correctivas.

## Condición verificable

Se activa esta regla si **una o más** de las siguientes condiciones se cumplen:

1. Un KPI del dashboard ejecutivo muestra desviación >10% respecto al objetivo mensual
2. Se detecta una brecha de ingresos >5% respecto al forecast del mes
3. Un cliente B2B con facturación >200k€ anuales comunica riesgo de baja
4. La tasa de incidencias global supera el 10% de los pedidos del mes
5. La tasa de entrega a tiempo cae por debajo del 90% (target >95%)
6. El uptime de sistemas cae por debajo del 99.5% en el mes

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Registrar la alerta con detalle del KPI, valor actual, objetivo y desviación | Agente | Inmediato |
| 2 | Realizar análisis de causa raíz: ¿es estacional, estructural, puntual? | Dirección | < 24h |
| 3 | Evaluar el impacto económico y operativo de la desviación | Dirección | < 48h |
| 4 | Convocar al responsable del departamento asociado al KPI para plan de acción | Dirección | < 48h |
| 5 | Definir plan correctivo con hitos medibles y responsables asignados | Dirección / Dpto. | < 1 semana |
| 6 | Hacer seguimiento semanal del plan hasta que el KPI vuelva a objetivo | Dirección | Semanal |
| 7 | Si la desviación no se corrige en 30 días, evaluar cambios estructurales | Dirección | < 30 días |
| 8 | Cerrar alerta cuando el KPI se mantenga en objetivo durante 2 semanas consecutivas | Agente | Tras verificación |

## Excepciones

- Si la desviación afecta a la capacidad de cumplir compromisos con clientes, comunicar a **Comercial**
- Si la causa raíz es un problema tecnológico, activar TEC-003 o TEC-001 según corresponda

## Métrica asociada

- **KPIs con desviación >10%** (número y tendencia)
- **Tiempo medio de corrección de desviaciones**