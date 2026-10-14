# COM-002: Modificación de contrato

**Ámbito:** Comercial
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un cliente B2B solicita modificar las condiciones de su contrato —cambio en volumen, renovación, nuevo servicio— se debe evaluar la solicitud, negociar si procede y actualizar el contrato.

## Condición verificable

Se activa esta regla cuando un cliente B2B solicita **una o más** de las siguientes modificaciones:

1. Cambio en las condiciones contractuales (volumen, precio, plazos de pago)
2. Renovación del contrato (vencimiento próximo o ya vencido)
3. Nueva línea de servicio (expansión a otro país, nuevo tipo de logística)
4. Reducción del alcance del contrato (eliminar servicios, reducir volumen contratado)
5. Modificación de los SLA acordados
6. Solicitud de rescisión anticipada del contrato

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Registrar la solicitud de modificación con detalle de lo que solicita el cliente | Agente | Inmediato |
| 2 | Evaluar el impacto: volumen actual, histórico de incidencias, rentabilidad del cliente | Account manager | < 24h |
| 3 | Preparar propuesta de modificación (mejora, contraoferta o aceptación) | Account manager | < 48h |
| 4 | Si la modificación implica cambio de precio o condiciones económicas, requerir aprobación de **Dirección** | Account manager / Dirección | < 72h |
| 5 | Presentar propuesta al cliente y negociar si es necesario | Account manager | < 5 días |
| 6 | Si hay acuerdo: actualizar contrato en el sistema y notificar a operaciones (Almacén, Última Milla) si aplica | Account manager | < 24h tras acuerdo |
| 7 | Cerrar incidencia con el nuevo contrato registrado | Agente | < 1h tras actualización |

## Excepciones

- Si la modificación implica cambios en la operación (nuevo almacén, nuevo transportista), involucrar a los departamentos afectados
- Si el cliente solicita rescisión, activar protocolo de retención y escalar a **Dirección**

## Métrica asociada

- **Tasa de renovación** a 90 y 30 días vista
- **Tiempo medio de procesamiento** de modificaciones contractuales