# TEC-008: Asignación de prioridad en incidencias de tecnología

**Ámbito:** Tecnología
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Regla para clasificar la prioridad de cualquier incidencia técnica según el impacto en la operación, la severidad del error y el número de usuarios afectados.

## Condición verificable

Se evalúa esta regla para **toda** incidencia registrada en el ámbito de tecnología. Asignar la prioridad según la siguiente tabla:

| Prioridad | Condiciones verificables (cumplir **una o más**) |
|---|---|
| **Crítica** | • Caída total de un sistema (API, SGA, BD) que afecta a las operaciones<br>• Pérdida de datos confirmada o sospechada<br>• Brecha de seguridad activa o confirmada<br>• Bug que bloquea completamente a un departamento |
| **Alta** | • Degradación significativa de servicio (lentitud, timeouts) que afecta a múltiples usuarios<br>• Bug que bloquea una funcionalidad crítica con workaround costoso<br>• Integración con transportista caída que afecta a envíos<br>• Despliegue fallido que requiere rollback |
| **Normal** | • Bug funcional sin bloqueo (workaround disponible)<br>• Problema de rendimiento sin impacto crítico inmediato<br>• Incidente de datos con alcance limitado y corregible<br>• Solicitud de cambio menor |
| **Baja** | • Mejora de rendimiento no urgente<br>• Deuda técnica (refactor, documentación)<br>• Actualización de documentación o runbooks |

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Evaluar la incidencia contra las condiciones de cada nivel de prioridad | Ingeniero / Agente | < 10 min tras detección |
| 2 | Asignar el nivel de prioridad más alto que cumpla condiciones | Ingeniero / Agente | < 10 min |
| 3 | Si es **Crítica**, notificar inmediatamente al CTO y a Dirección | Agente | Inmediato |
| 4 | Si es **Alta**, notificar al equipo de tecnología y al responsable del sistema afectado | Agente | < 15 min |
| 5 | Registrar prioridad en el sistema de incidencias | Agente | < 10 min |
| 6 | Re-evaluar prioridad cada 4h para incidencias críticas y cada 24h para altas | Ingeniero | Según frecuencia |

## Excepciones

- Si hay duda entre dos niveles, asignar siempre el de mayor prioridad
- Si el sistema afectado es el SGA o la API principal, subir automáticamente un nivel

## Métrica asociada

- **Distribución de incidentes por severidad**
- **Tiempo de detección** (MTTD)
- **Tiempo de resolución** (MTTR) por severidad