# LIN-001: Solicitud de devolución (RMA)

**Ámbito:** Logística Inversa
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un cliente solicita una devolución (por producto defectuoso, cambio de talla, insatisfacción, etc.), se debe evaluar la solicitud contra las reglas de negocio y emitir un número de autorización de devolución (RMA) si procede.

## Condición verificable

Se activa esta regla cuando un cliente (B2C o B2B) solicita formalmente la devolución de un producto a través de cualquier canal (CX, portal, email, teléfono).

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Verificar que la solicitud cumple **todas** las condiciones de aceptación:<br>• ¿El producto aplica para devolución según política del cliente/marca?<br>• ¿La solicitud está dentro de la ventana de devolución (ej. 30 días)?<br>• ¿El cliente está autorizado (no tiene historial de fraude)?<br>• ¿El producto está en condiciones devolubles (no usado, etiquetas)? | Agente | < 30 min |
| 2 | Si **todas** las condiciones se cumplen: emitir RMA y etiqueta de devolución | Agente | < 1h |
| 3 | Si **alguna** condición no se cumple: notificar al cliente la razón del rechazo y ofrecer alternativas | Agente | < 1h |
| 4 | Coordinar recogida con transportista según LIN-004 (si procede) | Agente / Logística inversa | < 2h |
| 5 | Registrar solicitud en el sistema de devoluciones con número de RMA | Agente | < 1h |

## Excepciones

- Si el producto es de alto valor (>1000€), requerir aprobación del responsable de Logística Inversa
- Si el cliente B2B solicita devolución fuera de ventana, escalar a **Comercial**
- Si hay sospecha de fraude, activar LIN-005 y no emitir RMA hasta investigación

## Métrica asociada

- **Tasa de devolución** (% sobre ventas, por cliente y producto)
- **Tiempo medio de emisión de RMA**