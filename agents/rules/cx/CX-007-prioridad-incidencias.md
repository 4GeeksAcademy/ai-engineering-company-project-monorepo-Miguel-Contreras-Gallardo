# CX-007: Asignación de prioridad en incidencias de CX

**Ámbito:** Experiencia al Cliente (CX)
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Regla para clasificar la prioridad de cualquier incidencia de CX según el tipo de cliente, la urgencia y el impacto en la satisfacción.

## Condición verificable

Se evalúa esta regla para **toda** incidencia registrada en el ámbito de CX. Asignar la prioridad según la siguiente tabla:

| Prioridad | Condiciones verificables (cumplir **una o más**) |
|---|---|
| **Crítica** | • Cliente B2B con parada de operaciones o crisis de servicio<br>• Queja pública en redes sociales o medios<br>• Reclamación formal con amenaza de acciones legales<br>• Cliente B2B >200k€ anuales amenaza con irse |
| **Alta** | • Cliente B2C con pedido no recibido >7 días<br>• Reclamación de daño con valor >200€<br>• Queja escalada por segunda vez sobre el mismo asunto<br>• Cliente B2B con queja que afecta a sus clientes finales |
| **Normal** | • Consulta de seguimiento de pedido estándar<br>• Estado de devolución o reembolso<br>• Solicitud de factura duplicada |
| **Baja** | • Consulta general de política o proceso<br>• Solicitud de información comercial<br>• Sugerencia de mejora o feedback espontáneo |

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Evaluar la consulta/incidencia contra las condiciones de cada nivel de prioridad | Agente | < 5 min tras recepción |
| 2 | Asignar el nivel de prioridad más alto que cumpla condiciones | Agente | < 5 min |
| 3 | Si es **Crítica**, notificar inmediatamente al responsable de CX y a Dirección | Agente | Inmediato |
| 4 | Si es **Alta**, notificar al responsable de CX | Agente | < 15 min |
| 5 | Registrar prioridad en el sistema de incidencias | Agente | < 10 min |

## Excepciones

- Si hay duda entre dos niveles, asignar siempre el de mayor prioridad
- Si el cliente es B2B, subir automáticamente un nivel de prioridad

## Métrica asociada

- **Distribución de contactos por prioridad**
- **Tiempo medio de primera respuesta** por prioridad