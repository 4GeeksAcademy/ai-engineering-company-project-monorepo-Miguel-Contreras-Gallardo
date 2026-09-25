# ULM-004: Error de transportista

**Ámbito:** Última Milla
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un transportista comete un error operativo en la entrega —reparto en dirección incorrecta, conductor no se presenta, documentación errónea— se debe gestionar la corrección y registrar la incidencia para seguimiento de calidad.

## Condición verificable

Se activa esta regla si **una o más** de las siguientes condiciones se cumplen:

1. El cliente reporta que el transportista intentó entregar en una dirección incorrecta
2. El conductor no se presentó en la ventana de entrega acordada sin aviso previo
3. La documentación de envío (albarán, factura, etiqueta) contiene errores atribuibles al transportista
4. El transportista rechaza la recogida de un envío programado (overbooking)
5. El transportista entrega sin recoger firma o prueba de entrega

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Registar incidencia: detalle del error, transportista, número de envhío | Agente | Inmediato |
| 2 | Contactar al transportista para correción inmediata (reenvío, nueva visita) | Coordinador logístico | < 1h |
| 3 | Reprogramar entrega con ventana confirmada con el cliente | Coordinador logístico | < 2h |
| 4 | Si el error es documental, solicitar correción de documentación al transportista | Coordinador logístico | < 4h |
| 5 | Registrar la incidencia en la evaluación mensual del transportista | Coordinador logístico | < 24h |
| 6 | Cerrar incidencia cuando la entrega se complete satisfactoriamente | Agente | < 1h tras entrega |

## Excepciones

- Si el mismo transportista acumula >3 errores en un mes, escalar a **Dirección**
- Si el error afecta a la facturación del cliente, notificar a **Comercial**

## Métrica asociada

- **Tasa de incidencias por transportista**
- **Errores documentales por operador**