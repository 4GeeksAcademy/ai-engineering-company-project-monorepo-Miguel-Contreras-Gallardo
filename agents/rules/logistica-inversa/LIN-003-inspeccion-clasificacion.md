# LIN-003: Inspección y clasificación de producto devuelto

**Ámbito:** Logística Inversa
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un producto devuelto llega al almacén, se debe inspeccionar y clasificar según su estado para determinar si es apto para reventa, necesita reparación, debe reciclarse o descartarse.

## Condición verificable

Se activa esta regla cuando un producto con RMA válido es recibido físicamente en el almacén de logística inversa para su inspección.

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Registrar recepción física del producto en el sistema asociado al RMA | Operario | < 1h tras recepción |
| 2 | Inspeccionar el producto según la lista de verificación:<br>• ¿Embalaje original presente y en buen estado?<br>• ¿Producto completo (manuales, accesorios)?<br>• ¿Signos de uso, desgaste o daño?<br>• ¿Funciona correctamente (si aplica)?<br>• ¿Etiquetas originales presentes? | Operario | < 2h |
| 3 | Clasificar según resultado: | Operario | < 2h |
| | **Grado A** — Como nuevo, apto para reventa inmediata | | |
| | **Grado B** — Con desgaste menor, apto para reventa con descuento | | |
| | **Grado C** — Necesita reparación, enviar a taller | | |
| | **Grado D** — No apto para reventa, reciclar | | |
| | **Grado E** — Descarte (daño irreversible, seguridad) | | |
| 4 | Si hay disputa de responsabilidad (cliente dice que llegó dañado vs daño causado por cliente), registrar evidencia | Responsable de Logística Inversa | < 4h |
| 5 | Actualizar inventario con el producto clasificado y su grado | Operario | < 1h tras clasificación |
| 6 | Notificar resultado al cliente (reembolso/reemvío según política) | Agente | < 2h tras clasificación |

## Excepciones

- Si la clasificación es inconsistente entre dos operarios, el responsable decide el grado final
- Si es Grado D o E, requerir aprobación del responsable para descarte
- Si se detecta clasificación incorrecta recurrente, escalar a responsable para reentrenamiento

## Métrica asociada

- **Productos recuperados para reventa** (% sobre total de devoluciones)
- **Tasa de reembolso vs reemvío**