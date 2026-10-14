# DIR-006: Asignación de prioridad en incidencias de dirección

**Ámbito:** Dirección
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Regla para clasificar la prioridad de cualquier incidencia que llegue a nivel de dirección, según su impacto estratégico, operativo y reputacional.

## Condición verificable

Se evalúa esta regla para **toda** incidencia gestionada por dirección. Asignar la prioridad según la siguiente tabla:

| Prioridad | Condiciones verificables (cumplir **una o más**) |
|---|---|
| **Crítica** | • Crisis activa con impacto en >100 pedidos o >50.000€<br>• Caída total de sistemas en ambos países (DIR-001)<br>• Brecha de seguridad activa con datos de clientes (TEC-004)<br>• Riesgo legal inminente (demanda, sanción regulatoria)<br>• Queja pública viral en medios o redes sociales (DIR-004) |
| **Alta** | • Desviación de KPI >10% que afecta a resultados mensuales (DIR-003)<br>• Cliente >200k€ anuales en riesgo de baja (COM-004)<br>• Conflicto entre departamentos no resuelto (DIR-002)<br>• Incidencia que requiere decisión ejecutiva con impacto >50.000€ |
| **Normal** | • Incidencia que requiere decisión ejecutiva sin urgencia inmediata<br>• Informe semanal automático<br>• Análisis de tendencia o propuesta de mejora |
| **Baja** | • Consulta estratégica sin urgencia<br>• Análisis de tendencia a largo plazo<br>• Mejora de procesos internos de dirección |

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Evaluar la incidencia contra las condiciones de cada nivel de prioridad | Agente | < 15 min tras recepción |
| 2 | Asignar el nivel de prioridad más alto que cumpla condiciones | Agente | < 15 min |
| 3 | Si es **Crítica**, notificar inmediatamente al CEO y al CTO | Agente | Inmediato |
| 4 | Si es **Alta**, notificar al equipo de dirección | Agente | < 1h |
| 5 | Registrar prioridad en el sistema de incidencias | Agente | < 15 min |

## Excepciones

- Si hay duda entre dos niveles, asignar siempre el de mayor prioridad
- Si la incidencia afecta a la relación con un cliente estratégico (top 3 por facturación), subir un nivel

## Métrica asociada

- **Distribución de incidencias de dirección por prioridad**
- **Tiempo medio de respuesta ejecutiva** por prioridad