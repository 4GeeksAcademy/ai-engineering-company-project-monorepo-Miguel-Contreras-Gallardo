# CX-002: Reclamación de cliente B2C

**Ámbito:** Experiencia al Cliente (CX)
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un cliente B2C presenta una reclamación formal sobre un pedido —no recibido, dañado, incompleto, incorrecto— se debe registrar, investigar y resolver la reclamación de acuerdo con la política correspondiente.

## Condición verificable

Se activa esta regla cuando un cliente B2C reporta **uno o más** de los siguientes problemas:

1. No ha recibido el pedido habiendo pasado la fecha de entrega prometida
2. El pedido llegó con daños visibles en el contenido
3. El pedido está incompleto (faltan productos del pedido original)
4. El pedido contiene productos que no pidió (producto incorrecto)
5. El producto recibido no funciona o no cumple con lo esperado

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Registrar reclamación con detalle del problema, número de pedido y evidencia del cliente | Agente | Inmediato |
| 2 | Clasificar el tipo de reclamación y determinar la causa raíz probable | Agente | < 30 min |
| 3 | **Si es no recibido:** verificar tracking, consultar con Última Milla (ULM-001/ULM-002) | Agente | < 2h |
| 4 | **Si es dañado:** solicitar fotos, consultar con Última Milla (ULM-003) | Agente | < 2h |
| 5 | **Si es incompleto/incorrecto:** consultar con Almacén (ALM-003) | Agente | < 2h |
| 6 | Ofrecer solución al cliente según política: reemvío, reembolso o compensación | Agente | < 4h |
| 7 | Ejecutar la solución acordada y notificar al cliente | Agente | < 8h |
| 8 | Cerrar reclamación tras confirmación de satisfacción del cliente | Agente | < 24h tras solución |

## Excepciones

- Si la reclamación es recurrente del mismo cliente (>3 en 6 meses), escalar a **Comercial** para revisión
- Si el valor de la reclamación supera los 500€, requerir aprobación del responsable de CX
- Si el cliente amenaza con acciones legales o queja pública, escalar a **Dirección** inmediatamente

## Métrica asociada

- **Tiempo medio de resolución** de reclamaciones
- **CSAT (Customer Satisfaction Score)** objetivo >4.0/5.0