# COM-004: Queja de cliente B2B con riesgo de baja

**Ámbito:** Comercial
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un cliente B2B expresa insatisfacción con el servicio, reporta incidencias recurrentes o comunica riesgo de no renovación, se debe gestionar la queja, realizar análisis de salud del cliente y activar las acciones de retención necesarias.

## Condición verificable

Se activa esta regla si **una o más** de las siguientes condiciones se cumplen:

1. El cliente B2B comunica explícitamente que no renovará el contrato
2. El cliente reporta insatisfacción con incidencias recurrentes en las últimas semanas
3. El health score del cliente (calculado automáticamente) cae por debajo de 3.0/5.0
4. El cliente solicita una reunión con dirección para hablar de su insatisfacción
5. El cliente ha tenido ≥3 incidencias críticas o altas en los últimos 30 días
6. El cliente tiene facturas impagadas que sugiere riesgo en la relación

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Registrar la queja con el detalle completo y escalar como "Riesgo de baja" | Agente | Inmediato |
| 2 | Realizar análisis de salud del cliente: histórico de incidencias, SLA, volumen, rentabilidad | Account manager | < 24h |
| 3 | Preparar un plan de retención: acciones correctivas, compensaciones, mejoras operativas | Account manager | < 48h |
| 4 | Coordinar con los departamentos implicados (Almacén, Última Milla, CX) las acciones | Account manager | < 48h |
| 5 | Presentar el plan al cliente, escuchar su feedback y ajustar si es necesario | Account manager | < 72h |
| 6 | Si el cliente tiene contrato >200k€ anuales, involucrar a **Dirección** en la reunión | Account manager / Dirección | < 72h |
| 7 | Hacer seguimiento semanal de la satisfacción del cliente hasta recuperar health score >3.5 | Account manager | Semanal |
| 8 | Cerrar incidencia si el cliente confirma continuidad o si se formaliza la baja | Agente | Tras resolución |

## Excepciones

- Si el valor del contrato es >200k€ anuales, involucrar a **Dirección** desde el paso 1
- Si el cliente ya ha iniciado proceso de baja con otro proveedor, escalar a **Dirección** para decisión ejecutiva

## Métrica asociada

- **Churn rate** (% de clientes que no renuevan)
- **Health score por cliente** (compuesto: incidencias, SLA, volumen, satisfacción)