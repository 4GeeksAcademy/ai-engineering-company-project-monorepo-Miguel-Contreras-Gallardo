# CX-001: Consulta de seguimiento de pedido

**Ámbito:** Experiencia al Cliente (CX)
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un cliente (B2C o B2B) pregunta por el estado de su pedido porque el tracking no se actualiza, falta información o simplemente quiere confirmar la entrega, se debe proporcionar la información disponible y, si es necesario, investigar con el departamento correspondiente.

## Condición verificable

Se activa esta regla si el cliente solicita información sobre el estado de su pedido a través de cualquier canal (email, WhatsApp, teléfono) y **una o más** de las siguientes condiciones se cumplen:

1. El cliente dice no haber recibido actualización de tracking en >24h
2. El cliente pregunta "¿dónde está mi pedido?" o similar
3. El cliente pregunta "¿cuándo llega mi pedido?" o similar
4. El tracking proporcionado por el transportista no es accesible o muestra error

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Identificar al cliente (email, número de pedido) y localizar el pedido en el sistema | Agente | < 5 min |
| 2 | Consultar tracking actual en el portal del transportista | Agente | < 5 min |
| 3 | Si el tracking es correcto y la fecha se mantiene: proporcionar estado y ETA al cliente | Agente | < 15 min |
| 4 | Si el tracking no se actualiza >24h o muestra anomalía: investigar internamente | Agente | < 1h |
| 5 | Si se detecta retraso o pérdida, escalar a **Última Milla** (ULM-001 o ULM-002) | Agente | < 1h |
| 6 | Si el error está en el almacén (no preparado), escalar a **Almacén** | Agente | < 1h |
| 7 | Responder al cliente con la información disponible y el plan de acción, comprometiendo próxima actualización | Agente | < 2h para B2C, < 1h para B2B |
| 8 | Dar seguimiento hasta resolución | Agente | Cada 24h |

## Excepciones

- Si el cliente B2B solicita un informe detallado de tracking, derivar a **Comercial**
- Si el cliente reporta que el portal de tracking no funciona, escalar a **Tecnología**

## Métrica asociada

- **Tiempo medio de primera respuesta** a consultas de seguimiento
- **Tasa de resolución en primer contacto** (FCR)