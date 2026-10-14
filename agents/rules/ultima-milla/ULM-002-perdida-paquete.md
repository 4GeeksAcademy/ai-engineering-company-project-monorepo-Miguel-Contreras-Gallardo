# ULM-002: Pérdida de paquete

**Ámbito:** Última Milla
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un paquete se extravía durante el tránsito —el tracking muestra entregado pero el cliente no lo recibió, o el transportista no localiza el paquete— se debe activar el protocolo de búsqueda y reclamación.

## Condición verificable

Se activa esta regla si **una o más** de las siguientes condiciones se cumplen:

1. El tracking del transportista marca "entregado" pero el cliente confirma no haberlo recibido
2. El transportista reporta que el paquete no se localiza en su centro de distribución o ruta
3. Han transcurrido >48h desde la última actualización de tracking sin movimiento
4. El paquete fue escaneado como "cargado" pero no como "entregado" ni "en ruta" después de 72h

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Registrar incidencia con número de tracking, transportista, fecha de envío y último escaneo | Agente | Inmediato |
| 2 | Abrir reclamación formal ante el transportista con todos los detalles de envío | Coordinador logístico | < 2h |
| 3 | Obtener número de reclamación del transportista y registrar en el sistema | Coordinador logístico | < 4h |
| 4 | Activar reemvío urgente del pedido si es posible (mismo contenido) | Coordinador logístico | < 4h |
| 5 | Notificar al cliente a través de CX (B2C) o Comercial (B2B) con el plan de acción | Agente | < 2h |
| 6 | Dar seguimiento a la reclamación hasta resolución (reembolso o compensación) | Coordinador logístico | < 15 días |
| 7 | Cerrar incidencia tras reposición o compensación confirmada | Agente | < 1h tras confirmación |

## Excepciones

- Si el paquete tiene valor declarado >1000€, notificar a **Dirección**
- Si el transportista rechaza la reclamación, escalar a **Dirección** para decisión

## Métrica asociada

- **Tasa de pérdidas por transportista**
- **Coste medio por pérdida** (reemvío + compensación)