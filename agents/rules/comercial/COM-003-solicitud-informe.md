# COM-003: Solicitud de informe a cliente B2B

**Ámbito:** Comercial
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un cliente B2B solicita un informe periódico o específico —reporte de volumen mensual, informe de incidencias, reporte de SLA— se debe preparar y entregar la información solicitada en el formato acordado.

## Condición verificable

Se activa esta regla cuando un cliente B2B (por cualquier canal) solicita **uno o más** de los siguientes informes:

1. Reporte de volumen mensual (pedidos procesados, entregados, devueltos)
2. Informe de incidencias (abiertas, cerradas, por tipo y prioridad)
3. Reporte de cumplimiento de SLA (entregas a tiempo, tasas de error)
4. Informe de costes logísticos del período
5. Reporte personalizado no contemplado en los informes estándar

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Identificar al cliente, el tipo de informe solicitado y el período | Agente | < 15 min |
| 2 | **Si es informe estándar (volumen, incidencias, SLA):** generarlo desde el sistema de reportes | Agente | < 4h |
| 3 | **Si es informe personalizado:** evaluar viabilidad y tiempo requerido | Account manager | < 24h |
| 4 | Si se necesita data adicional de otros departamentos (incidencias de almacén, tracking), solicitarla internamente | Account manager | < 8h |
| 5 | Revisar el informe antes de enviarlo al cliente (verificar accuracy de datos) | Account manager | < 2h |
| 6 | Entregar informe al cliente en el formato acordado (PDF, Excel, dashboard) | Account manager | < 1h tras revisión |
| 7 | Archivar informe y registrar en el historial del cliente | Agente | < 1h tras envío |

## Excepciones

- Si la solicitud requiere desarrollo de un nuevo reporte automatizado, escalar a **Tecnología**
- Si es un cliente premium (>100k€ anuales), priorizar y entregar en <24h

## Métrica asociada

- **Tiempo medio de entrega de informes**
- **Satisfacción del cliente con informes** (CSAT en encuestas)