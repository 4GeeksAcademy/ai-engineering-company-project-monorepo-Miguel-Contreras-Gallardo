# COM-006: Asignación de prioridad en incidencias comerciales

**Ámbito:** Comercial
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Regla para clasificar la prioridad de cualquier incidencia comercial según el valor del cliente, la urgencia contractual y el riesgo de negocio.

## Condición verificable

Se evalúa esta regla para **toda** incidencia registrada en el ámbito comercial. Asignar la prioridad según la siguiente tabla:

| Prioridad | Condiciones verificables (cumplir **una o más**) |
|---|---|
| **Crítica** | • Cliente comunica no renovación o baja inminente<br>• Crisis de servicio que afecta a un cliente >200k€ anuales<br>• Incumplimiento de SLA contractual con penalización económica |
| **Alta** | • Reclamación económica >1000€ (facturación, compensaciones)<br>• Disputa contractual activa<br>• Cliente B2B >100k€ anuales con queja<br>• Riesgo de baja detectado por health score <3.0 |
| **Normal** | • Solicitud de informe estándar<br>• Modificación contractual menor<br>• Consulta de factura sin discrepancia confirmada |
| **Baja** | • Solicitud de información comercial<br>• Propuesta de mejora del cliente<br>• Newsletter o comunicación general |

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Evaluar la incidencia contra las condiciones de cada nivel de prioridad | Agente | < 10 min tras registro |
| 2 | Asignar el nivel de prioridad más alto que cumpla condiciones | Agente | < 10 min |
| 3 | Si es **Crítica**, notificar inmediatamente al responsable de Comercial y a **Dirección** | Agente | Inmediato |
| 4 | Si es **Alta**, notificar al account manager asignado | Agente | < 30 min |
| 5 | Registrar prioridad en el sistema de incidencias | Agente | < 10 min |

## Excepciones

- Si hay duda entre dos niveles, asignar siempre el de mayor prioridad
- Si es un cliente estratégico (top 5 por facturación), subir automáticamente un nivel

## Métrica asociada

- **Distribución de incidencias por prioridad**
- **Tiempo medio de respuesta a reclamaciones B2B**