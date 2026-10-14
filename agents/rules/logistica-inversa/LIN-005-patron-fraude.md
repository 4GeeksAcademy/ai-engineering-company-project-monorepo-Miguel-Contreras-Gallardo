# LIN-005: Patrón de fraude en devoluciones

**Ámbito:** Logística Inversa
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando se detectan patrones anómalos en las devoluciones que sugieren posible fraude (devoluciones recurrentes del mismo cliente, devoluciones sin pedido asociado, productos sustituidos), se debe investigar y escalar para proteger al negocio.

## Condición verificable

Se activa esta regla si **una o más** de las siguientes condiciones se cumplen:

1. Un mismo cliente ha realizado ≥3 devoluciones en los últimos 30 días
2. Un cliente devuelve un producto sin un pedido de compra asociado en el sistema
3. El producto devuelto no coincide con el SKU del RMA emitido (producto sustituido)
4. El cliente tiene un historial de devoluciones que excede el 50% de sus compras
5. Se detecta la misma dirección de envío utilizada por múltiples cuentas para devoluciones recurrentes
6. Un cliente solicita devolución de un producto que ya fue devuelto previamente (devolución en bucle)

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Marcar la devolución como "Sospechosa de fraude" y pausar el procesamiento | Agente | Inmediato |
| 2 | No emitir reembolso ni reemvío hasta completar investigación | Agente | Hasta investigación |
| 3 | Recopilar evidencia: histórico de devoluciones, pedidos, valor total, dirección, IP, método de pago | Responsable de Logística Inversa | < 24h |
| 4 | Evaluar el riesgo: bajo (patrón accidental), medio (sospecha razonable), alto (fraude claro) | Responsable de Logística Inversa | < 48h |
| 5 | Si es **riesgo medio o alto**, escalar a **Dirección** para decisión | Responsable de Logística Inversa | < 48h |
| 6 | Si se confirma fraude: bloquear al cliente, no procesar reembolso, notificar a dirección | Agente | Tras decisión |
| 7 | Si se descarta fraude: reanudar procesamiento normal de la devolución | Agente | Tras decisión |

## Excepciones

- Si el valor acumulado de las devoluciones sospechosas supera los 2000€, escalar a **Dirección** inmediatamente
- Si se sospecha fraude organizado (múltiples cuentas, misma IP/dirección), escalar a **Dirección**

## Métrica asociada

- **Tasa de fraude detectado** (% sobre devoluciones)
- **Valor económico protegido por detección de fraude**