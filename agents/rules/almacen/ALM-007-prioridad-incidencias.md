# ALM-007: Asignación de prioridad en incidencias de almacén

**Ámbito:** Almacén
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Regla para clasificar la prioridad de cualquier incidencia de almacén según su impacto operativo. La prioridad determina el tiempo de respuesta y los recursos asignados.

## Condición verificable

Se evalúa esta regla para **toda** incidencia registrada en el ámbito de almacén. Asignar la prioridad según la siguiente tabla:

| Prioridad | Condiciones verificables (cumplir **una o más**) |
|---|---|
| **Crítica** | • Parada total del almacén (no se puede preparar ningún pedido)<br>• Imposibilidad de servir pedidos por falta de stock crítico<br>• Riesgo inminente de no cumplir cutoff (ALM-006 activada) |
| **Alta** | • Discrepancia que afecta a pedidos en curso (ya asignados a picking)<br>• Daño significativo en mercancía con valor estimado >500€<br>• Error de picking detectado antes de que el pedido salga del almacén |
| **Normal** | • Discrepancia de inventario sin pedidos activos asociados<br>• Picking incorrecto ya detectado y corregido sin impacto al cliente<br>• Recepción con diferencias menores (<5% del pedido) |
| **Baja** | • Consulta de procedimiento operativo<br>• Mejora continua o sugerencia de proceso<br>• Documentación o actualización de registros |

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Evaluar la incidencia contra las condiciones de cada nivel de prioridad | Agente | < 5 min tras registro |
| 2 | Asignar el nivel de prioridad más alto que cumpla condiciones | Agente | < 5 min |
| 3 | Si es **Crítica**, notificar inmediatamente al responsable de almacén y activar ALM-006 si aplica | Agente | Inmediato |
| 4 | Registrar prioridad asignada en el sistema de incidencias | Agente | < 10 min |
| 5 | Re-evaluar prioridad si cambian las condiciones (ej. un pedido en curso se detiene) | Agente | Cada 4h para críticas |

## Excepciones

- Si hay duda entre dos niveles, asignar siempre el de mayor prioridad
- Si el reportador insiste en prioridad mayor, escalar a responsable de almacén

## Métrica asociada

- **Distribución de incidencias por prioridad**
- **Tiempo medio de respuesta por prioridad**