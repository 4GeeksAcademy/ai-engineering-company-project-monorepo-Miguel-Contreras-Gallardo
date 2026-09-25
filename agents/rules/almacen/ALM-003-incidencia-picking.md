# ALM-003: Incidencia de picking

**Ámbito:** Almacén
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un pedido preparado contiene errores en el proceso de picking (producto equivocado, cantidad incorrecta, etiqueta dañada o picking incompleto), se debe registrar, corregir y documentar para evitar recurrencias.

## Condición verificable

Se activa esta regla si **una o más** de las siguientes condiciones se cumplen:

1. El sistema de control de calidad detecta producto equivocado en la caja preparada
2. El picking está incompleto: faltan líneas del pedido respecto al albarán
3. La etiqueta del producto o del envío está dañada, ilegible o desprendida
4. Un operario reporta que no pudo completar el picking por error de ubicación

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Registrar incidencia: pedido, SKU esperado, SKU real o cantidad faltante | Agente / Operario | Inmediato |
| 2 | Detener el envío del pedido si aún está en almacén | Operario | Inmediato |
| 3 | Reponer/corregir el producto correcto en el pedido | Operario de picking | < 30 min |
| 4 | Si el pedido ya salió del almacén, notificar a **Última Milla** para retención | Agente | < 15 min |
| 5 | Identificar causa: etiqueta errónea, ubicación incorrecta, error humano | Responsable de almacén | < 2h |
| 6 | Corregir causa raíz (reetiquetar, reubicar, reentrenar) | Responsable de almacén | < 8h |
| 7 | Cerrar incidencia y documentar lección | Agente | < 1h tras resolución |

## Excepciones

- Si el error de picking afecta a un pedido B2B, notificar a **Comercial**
- Si el cliente final ya ha sido impactado, notificar a **CX**

## Métrica asociada

- **Pedidos picking perfecto** (% sin incidencias)