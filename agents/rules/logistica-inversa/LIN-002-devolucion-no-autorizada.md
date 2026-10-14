# LIN-002: Devolución no autorizada

**Ámbito:** Logística Inversa
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un producto es devuelto sin un número de RMA válido, o fuera de la ventana de devolución permitida, se debe gestionar como devolución no autorizada siguiendo el protocolo de rechazo o aceptación excepcional.

## Condición verificable

Se activa esta regla si **una o más** de las siguientes condiciones se cumplen:

1. El producto llega al almacén sin un número de RMA asociado
2. El producto se devuelve con un RMA que ha expirado (>30 días desde emisión)
3. El producto se devuelve fuera de la ventana de devolución contratada
4. El producto devuelto no coincide con el SKU autorizado en el RMA

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Registrar la recepción del producto como "No autorizada" en el sistema | Agente / Operario | Inmediato |
| 
| 2 | Separar el producto en zona de cuarentena de devoluciones no autorizadas | Operario | < 1h |
| 3 | Intentar contactar al cliente para determinar origen de la devolución | Agente / CX | < 24h |
| 4 | Evaluar si procede aceptación excepcional (cliente B2B, valor estratégico) | Responsable de Logística Inversa | < 48h |
| 5 | Si se rechaza: notificar al cliente que el producto está disponible para recogida o se destruirá en 15 días | Agente | < 48h |
| 6 | Si se acepta excepcionalmente: emitir RMA retroactivo y procesar devolución según LIN-003 | Responsable de Logística Inversa | < 48h |
| 7 | Cerrar incidencia con la resolución documentada | Agente | < 1h tras resolución |

## Excepciones

- Si el cliente es B2B estratégico (>100k€ anuales), escalar a **Comercial** antes de rechazar
- Si se detecta patrón del mismo cliente devolviendo sin RMA, activar alerta de fraude (LIN-005)

## Métrica asociada

- **Tasa de devoluciones no autorizadas** (% sobre total de devoluciones)