# CX-004: Consulta de facturación

**Ámbito:** Experiencia al Cliente (CX)
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un cliente solicita un duplicado de factura, reporta una discrepancia en el importe facturado, o necesita información fiscal de la compra, se debe gestionar la consulta y, si es necesario, derivar a facturación o a Comercial.

## Condición verificable

Se activa esta regla cuando un cliente solicita **uno o más** de los siguientes temas relacionados con facturación:

1. Solicita un duplicado de factura de un pedido anterior
2. Reporta que el importe facturado no coincide con el importe del pedido
3. Reporta que un descuento acordado no se ha aplicado en la factura
4. Detecta un cargo duplicado en su método de pago
5. Solicita información fiscal (CIF/NIF, datos de facturación) para actualizar sus registros
6. Solicita cambio de datos fiscales en su perfil de cliente

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Identificar al cliente, el pedido y el comprobante de pago asociado | Agente | < 10 min |
| 2 | **Si es duplicado de factura:** generar y enviar copia al cliente | Agente | < 30 min |
| 3 | **Si es discrepancia de importe:** comparar el pedido original vs factura emitida | Agente | < 1h |
| 4 | **Si es descuento no aplicado:** verificar condiciones acordadas con Comercial | Agente / Comercial | < 4h |
| 5 | **Si es cargo duplicado:** verificar el procesamiento de pago en el sistema | Agente | < 2h |
| 6 | Si la discrepancia requiere corrección en el sistema de facturación, escalar a **Tecnología** | Agente | < 4h |
| 7 | Notificar al cliente la resolución y, si aplica, el plazo de la corrección | Agente | < 2h tras resolución |

## Excepciones

- Si la discrepancia económica supera los 500€, notificar a **Comercial**
- Si el cliente B2B reclama por facturación incorrecta recurrente, escalar a **Dirección**

## Métrica asociada

- **Tiempo medio de resolución** de consultas de facturación
- **% de consultas de facturación sobre total de contactos**