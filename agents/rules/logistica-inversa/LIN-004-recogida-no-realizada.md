# LIN-004: Recogida de devolución no realizada

**Ámbito:** Logística Inversa
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un transportista no se presenta a recoger una devolución en la ventana acordada, o la recogida no se puede completar por dirección incorrecta u otra causa, se debe reprogramar y resolver la incidencia.

## Condición verificable

Se activa esta regla si **una o más** de las siguientes condiciones se cumplen:

1. El transportista no se presentó en la ventana de recogida acordada con el cliente
2. El cliente reporta que la recogida fue cancelada sin aviso
3. La dirección de recogida proporcionada es incorrecta o incompleta
4. Han transcurrido >48h desde la emisión del RMA sin que el transportista haya recogido
5. El transportista reporta que no pudo realizar la recogida (cliente ausente, domicilio cerrado)

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Registrar incidencia: RMA, transportista, ventana programada y motivo de fallo | Agente | Inmediato |
| 2 | Contactar al transportista para reprogramar recogida en la ventana más próxima disponible | Coordinador logístico | < 2h |
| 3 | Notificar al cliente la nueva ventana de recogida y confirmar disponibilidad | Agente / CX | < 2h |
| 4 | Si el cliente no está disponible, acordar nueva fecha | Agente | < 4h |
| 5 | Si la dirección es incorrecta, solicitar dirección actualizada al cliente | Agente / CX | < 2h |
| 6 | Reprogramar hasta un máximo de 3 intentos; si fallan todos, escalar | Coordinador logístico | < 5 días |
| 7 | Cerrar incidencia cuando la recogida se complete exitosamente | Agente | < 1h tras confirmación |

## Excepciones

- Si fallan 3 intentos de recogida consecutivos, escalar a **Última Milla** para cambio de transportista
- Si el cliente B2B reporta 3 recogidas fallidas en un mes, escalar a **Comercial**

## Métrica asociada

- **Tasa de recogidas fallidas por transportista**
- **Tiempo medio de resolución** de recogidas no realizadas