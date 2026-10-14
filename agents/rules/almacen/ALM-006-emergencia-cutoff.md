# ALM-006: Emergencia operativa — riesgo de cutoff

**Ámbito:** Almacén
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando existe riesgo de no cumplir con la hora de corte (cutoff) del transportista para la salida de pedidos, se debe activar una alerta para priorizar recursos y evitar retrasos en las entregas.

## Condición verificable

Se activa esta regla si **todas** las siguientes condiciones se cumplen:

1. Queda menos de 2 horas para el cutoff del transportista establecido
2. Hay pedidos preparados pendientes de facturación, etiquetado o carga
3. La capacidad actual del almacén no permite completar la carga antes del cutoff

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Declarar emergencia operativa con detalle de pedidos afectados | Responsable de almacén | Inmediato |
| 2 | Asignar recursos adicionales (operarios de otras zonas) para completar la carga | Responsable de almacén | < 15 min |
| 3 | Notificar a **Última Milla** sobre posible retraso en la salida | Agente | < 15 min |
| 4 | Si se confirma que no se alcanzará el cutoff, coordinar nueva ventana con transportista | Última Milla | < 1h |
| 5 | Notificar a **CX** si hay pedidos B2C o B2B afectados por el retraso | Agente | < 1h |
| 6 | Documentar causa y acciones tomadas | Responsable de almacén | < 2h post-evento |

## Excepciones

- Si hay riesgo de no cumplir cutoff durante 2 días consecutivos, escalar a **Dirección**
- Si el cutoff pertenece a un cliente B2B premium, escalar a **Comercial**

## Métrica asociada

- **% de pedidos enviados antes del cutoff**
- **Tiempo medio de activación de emergencia**