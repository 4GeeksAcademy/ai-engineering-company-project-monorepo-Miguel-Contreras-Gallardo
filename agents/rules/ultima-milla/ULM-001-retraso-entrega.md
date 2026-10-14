# ULM-001: Retraso en entrega

**Ámbito:** Última Milla
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un pedido no se entrega en la fecha prometida al cliente o el tracking no se actualiza durante más de 24 horas, se debe investigar, notificar al cliente y reprogramar la entrega.

## Condición verificable

Se activa esta regla si **una o más** de las siguientes condiciones se cumplen:

1. La fecha de entrega prometida ha vencido y el pedido no figura como entregado
2. El tracking del pedido no muestra ninguna actualización en las últimas 24 horas
3. El transportista confirma retraso por capacidad, ruta o incidencia interna
4. El cliente o CX reporta que el pedido no ha llegado en la fecha prevista

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Registrar incidencia con número de pedido, transportista, fecha prometida y última actualización de tracking | Agente | Inmediato |
| 2 | Contactar al transportista para obtener estado real y nueva ETA | Coordinador logístico | < 1h |
| 3 | Comunicar nueva fecha estimada al cliente (vía CX para B2C, directo para B2B) | Agente / CX | < 2h |
| 4 | Si el retraso excede 48h sobre fecha prometida, activar opción de reemvío urgente | Coordinador logístico | < 4h |
| 5 | Si el cliente rechaza la nueva fecha, escalar para gestión de compensación | Agente | < 2h |
| 6 | Actualizar tracking interno y notificar resolución a CX o Comercial según corresponda | Agente | < 1h tras resolución |

## Excepciones

- Si el retraso afecta a un cliente B2B con SLA contractual, notificar a **Comercial**
- Si hay más de 10 pedidos con retraso del mismo transportista, escalar a **Dirección**

## Métrica asociada

- **Tasa de entrega a tiempo** (On-Time Delivery Rate)
- **Tiempo medio de resolución** de retrasos