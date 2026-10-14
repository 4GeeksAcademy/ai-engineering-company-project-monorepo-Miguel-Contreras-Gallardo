# ULM-005: Incidencia administrativa con transportista

**Ámbito:** Última Milla
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando surgen incidencias administrativas con transportistas relacionadas con documentación incorrecta, rechazos de recogida, overbooking o discrepancias en tarifas, se debe documentar y resolver la discrepancia.

## Condición verificable

Se activa esta regla si **una o más** de las siguientes condiciones se cumplen:

1. El transportista rechaza una recogida programada alegando overbooking o falta de capacidad
2. La documentación de envío (factura, albarán, etiqueta aduanera) contiene errores atribuibles al proceso
3. La tarifa facturada no coincide con la tarifa contratada para ese servicio
4. El transportista devuelve el paquete por documentación incorrecta
5. El transportista solicita información adicional para completar el envío

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Registrar incidencia con tipo de error y documentación asociada | Agente | Inmediato |
| 2 | Contactar al transportista para clarificar o subsanar el error documental | Coordinador logístico | < 2h |
| 3 | Si es overbooking, buscar alternativa con otro transportista (cambio de transportista) | Coordinador logístico | < 2h |
| 4 | Si es discrepancia de tarifa, revisar contrato y reclamar al transportista | Coordinador logístico | < 48h |
| 5 | Documentar la resolución y actualizar procedimientos si aplica | Coordinador logístico | < 24h tras resolución |
| 6 | Cerrar incidencia | Agente | < 1h tras resolución |

## Excepciones

- Si el overbooking afecta a >20 pedidos en un día, escalar a **Dirección**
- Si la discrepancia de tarifa supera los 500€, escalar a **Dirección**

## Métrica asociada

- **Número de incidencias administrativas por transportista**
- **Tiempo medio de resolución de incidencias administrativas**