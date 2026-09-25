# ALM-001: Rotura de stock

**Ámbito:** Almacén
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un operario no encuentra un producto en su ubicación asignada o el sistema muestra stock negativo, se debe registrar y resolver la incidencia para restablecer la trazabilidad del inventario.

## Condición verificable

Se activa esta regla si **todas** las siguientes condiciones se cumplen:

1. Un operario reporta que un producto no está en su ubicación asignada en el SGA
2. O el sistema de inventario muestra un valor de stock < 0 para ese producto
3. El producto tiene un pedido activo asociado (asignado a picking o pendiente de preparar)

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Registrar incidencia con SKU, ubicación y cantidad esperada vs real | Agente / Operario | Inmediato |
| 2 | Realizar búsqueda física en ubicaciones adyacentes y zona de tránsito | Operario de almacén | < 30 min |
| 3 | Si no se localiza, ejecutar conteo cíclico del producto en todo el almacén | Responsable de almacén | < 2h |
| 4 | Ajustar inventario en SGA si procede (con aprobación de responsable) | Responsable de almacén | < 1h |
| 5 | Notificar resultado al reportador y cerrar incidencia | Agente | < 1h tras resolución |

## Excepciones

- Si la rotura afecta a >10 pedidos, escalar a **Dirección**
- Si requiere cambio en SGA, escalar a **Tecnología**

## Métrica asociada

- **Tasa de discrepancias de inventario** (mensual, por almacén)
- **Tiempo medio de resolución** de roturas de stock