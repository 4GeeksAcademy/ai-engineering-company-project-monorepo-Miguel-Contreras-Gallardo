# ULM-006: Asignación de prioridad en incidencias de última milla

**Ámbito:** Última Milla
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Regla para clasificar la prioridad de cualquier incidencia de última milla según su impacto en las entregas y en los clientes.

## Condición verificable

Se evalúa esta regla para **toda** incidencia registrada en el ámbito de última milla. Asignar la prioridad según la siguiente tabla:

| Prioridad | Condiciones verificables (cumplir **una o más**) |
|---|---|
| **Crítica** | • Parada total de envíos (todos los transportistas bloqueados)<br>• Cutoff inminente incumplido que afecta a >50 pedidos<br>• Transportista no se presenta a recoger sin previo aviso |
| **Alta** | • Paquete perdido o dañado de alto valor (>500€)<br>• Retraso que impacta SLA de cliente B2B contratado<br>• Error de transportista que afecta a un pedido B2B |
| **Normal** | • Retraso sin impacto en SLA contratado<br>• Error administrativo con transportista (documentación)<br>• Paquete dañado de bajo valor (<100€) |
| **Baja** | • Consulta de tarifas o rutas<br>• Mejora de proceso logístico<br>• Documentación o reporte |

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Evaluar la incidencia contra las condiciones de cada nivel de prioridad | Agente | < 5 min tras registro |
| 2 | Asignar el nivel de prioridad más alto que cumpla condiciones | Agente | < 5 min |
| 3 | Si es **Crítica**, notificar inmediatamente al responsable de Última Milla y a Dirección | Agente | Inmediato |
| 4 | Si es **Alta**, notificar al coordinador logístico correspondiente | Agente | < 15 min |
| 5 | Registrar prioridad en el sistema de incidencias | Agente | < 10 min |
| 6 | Re-evaluar prioridad si hay cambios (ej. el cliente escala la queja) | Agente | Cada 8h para críticas |

## Excepciones

- Si hay duda entre dos niveles, asignar siempre el de mayor prioridad
- Si la incidencia afecta a un cliente B2B premium, subir un nivel de prioridad

## Métrica asociada

- **Distribución de incidencias por prioridad**
- **Tiempo medio de respuesta por prioridad**