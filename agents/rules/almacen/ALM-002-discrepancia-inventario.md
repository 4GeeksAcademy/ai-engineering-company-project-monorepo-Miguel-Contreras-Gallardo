# ALM-002: Discrepancia de inventario

**Ámbito:** Almacén
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando el conteo físico de un producto no coincide con el registro del sistema, se debe investigar la discrepancia, ajustar el inventario y documentar la causa raíz.

## Condición verificable

Se activa esta regla si **todas** las siguientes condiciones se cumplen:

1. Se realiza un conteo cíclico o inventario físico programado
2. La cantidad física contada difiere del registro del SGA en ≥ 1 unidad
3. La diferencia no se explica por una rotura de stock ya registrada (ALM-001)

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Registrar discrepancia: SKU, ubicación, cantidad SGA, cantidad física, diferencia | Agente / Operario | Inmediato |
| 2 | Realizar doble conteo para confirmar la discrepancia | Segundo operario | < 1h |
| 3 | Investigar causa raíz (error de picking, recepción, merma, robo, daño) | Responsable de almacén | < 4h |
| 4 | Ajustar inventario en SGA tras aprobación del responsable | Responsable de almacén | < 2h tras causa |
| 5 | Si hay daño en mercancía, clasificar producto y gestionar baja | Responsable de almacén | < 8h |
| 6 | Documentar causa raíz y actualizar incidencia | Agente | < 1h tras resolución |

## Excepciones

- Si la discrepancia tiene valor estimado >1000€, escalar a **Dirección**
- Si se detecta patrón recurrente en mismo SKU, escalar a **Tecnología** para revisión de proceso

## Métrica asociada

- **Tasa de discrepancias de inventario** (mensual, por almacén)
- **Stock obsoleto o dañado** detectado vs reportado