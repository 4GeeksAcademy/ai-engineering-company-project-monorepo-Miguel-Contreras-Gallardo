# ALM-004: Recepción de mercancía

**Ámbito:** Almacén
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando se recibe mercancía de un proveedor y se detectan diferencias entre lo recibido y lo esperado (exceso, faltante o producto no solicitado), se debe documentar y resolver la incidencia antes de integrar el inventario.

## Condición verificable

Se activa esta regla si **una o más** de las siguientes condiciones se cumplen:

1. La cantidad recibida difiere de la cantidad del albarán de compra (exceso o faltante)
2. Se recibe un producto que no figura en el pedido de compra
3. La mercancía recibida presenta daños visibles en el embalaje exterior
4. No se dispone de documentación de envío (albarán, factura) para la mercancía recibida

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Registrar incidencia: pedido de compra, SKU, cantidad esperada, cantidad recibida | Agente / Operario | Inmediato |
| 2 | Fotografiar la mercancía y la documentación disponible | Operario | < 15 min |
| 3 | Notificar al proveedor sobre la discrepancia (abrir reclamación) | Responsable de almacén | < 2h |
| 4 | Separar la mercancía en cuarentena hasta resolución | Operario | Inmediato |
| 5 | Recibir instrucción del proveedor: aceptar exceso, devolver, destruir | Responsable de almacén | < 48h |
| 6 | Actualizar inventario solo tras instrucción del proveedor | Responsable de almacén | < 2h tras instrucción |
| 7 | Cerrar incidencia documentando la resolución | Agente | < 1h tras resolución |

## Excepciones

- Si el proveedor es crítico para la operación, escalar a **Dirección**
- Si la mercancía dañada requiere peritaje, escalar a **Logística Inversa**

## Métrica asociada

- **Tasa de recepciones con incidencia** (% sobre total de recepciones)