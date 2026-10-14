# LIN-006: Asignación de prioridad en incidencias de logística inversa

**Ámbito:** Logística Inversa
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Regla para clasificar la prioridad de cualquier incidencia de logística inversa según el valor, riesgo y urgencia de la devolución.

## Condición verificable

Se evalúa esta regla para **toda** incidencia registrada en el ámbito de logística inversa. Asignar la prioridad según la siguiente tabla:

| Prioridad | Condiciones verificables (cumplir **una o más**) |
|---|---|
| **Crítica** | • Fraude detectado o sospecha de fraude confirmada (LIN-005 activada)<br>• Devolución con valor del producto >1000€<br>• Cliente B2B bloqueado por devolución en disputa |
| **Alta** | • Reclamación de cliente escalada por CX<br>• Disputa de responsabilidad activa (cliente vs transportista)<br>• Devolución con valor entre 500€ y 1000€ |
| **Normal** | • Devolución rutinaria dentro de política<br>• Inspección pendiente de clasificar<br>• Recogida a reprogramar por primera vez |
| **Baja** | • Consulta de política de devoluciones<br>• Mejora de proceso de inspección<br>• Informe de patrones sin urgencia |

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Evaluar la incidencia contra las condiciones de cada nivel de prioridad | Agente | < 10 min tras registro |
| 2 | Asignar el nivel de prioridad más alto que cumpla condiciones | Agente | < 10 min |
| 3 | Si es **Crítica**, notificar inmediatamente al responsable de Logística Inversa | Agente | Inmediato |
| 4 | Registrar prioridad en el sistema de incidencias | Agente | < 10 min |

## Excepciones

- Si hay duda entre dos niveles, asignar el de mayor prioridad
- Si el producto pertenece a un cliente B2B estratégico, subir un nivel

## Métrica asociada

- **Distribución de incidencias por prioridad**
- **Tiempo medio del ciclo de devolución**