# CX-003: Consulta de devolución

**Ámbito:** Experiencia al Cliente (CX)
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un cliente pregunta sobre el proceso de devolución —cómo devolver un producto, cuándo recibirá el reembolso, estado de su RMA— se debe proporcionar la información actualizada y resolver las dudas del cliente.

## Condición verificable

Se activa esta regla cuando un cliente pregunta sobre **uno o más** de los siguientes temas:

1. "¿Cómo puedo devolver un producto?" — solicitud de información sobre el proceso
2. "¿Cuándo me reembolsarán?" — estado del reembolso de una devolución en curso
3. "¿Cuál es el estado de mi RMA?" — seguimiento de una devolución ya autorizada
4. "¿Por qué no ha pasado el transportista?" — seguimiento de recogida (LIN-004)
5. "¿Puedo cambiar este producto por otro?" — solicitud de cambio

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Identificar al cliente y localizar el pedido/RMA en el sistema | Agente | < 5 min |
| 2 | **Si solicita información de proceso:** explicar política de devolución según cliente y país | Agente | < 15 min |
| 3 | **Si pregunta por reembolso:** verificar estado de la inspección en Logística Inversa | Agente | < 1h |
| 4 | **Si pregunta por recogida:** verificar estado con Logística Inversa (LIN-004) | Agente | < 1h |
| 5 | **Si la devolución está bloqueada:** escalar a **Logística Inversa** para desbloqueo | Agente | < 2h |
| 6 | Proporcionar respuesta al cliente con estado real y fecha estimada de resolución | Agente | < 2h |
| 7 | Si el cliente solicita cambio en lugar de devolución, evaluar viabilidad con Logística Inversa | Agente | < 4h |

## Excepciones

- Si la devolución lleva >48h sin resolución, escalar a Logística Inversa con prioridad
- Si el cliente B2B solicita modificación de la política de devolución, escalar a **Comercial**

## Métrica asociada

- **Tiempo medio de respuesta** a consultas de devolución
- **Tasa de resolución en primer contacto** (FCR)