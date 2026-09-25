# ULM-003: Daño en transporte

**Ámbito:** Última Milla
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un paquete llega a su destino con daños visibles o evidencia de mal manejo durante el transporte, se debe documentar el daño, gestionar la reclamación con el transportista y coordinar la reposición o compensación al cliente.

## Condición verificable

Se activa esta regla si **una o más** de las siguientes condiciones se cumplen:

1. El cliente reporta que el paquete llegó con daños externos o internos
2. El transportista entrega el paquete con evidencia de golpes, aplastamiento o rotura
3. El conductor reporta daño detectado durante la carga o tránsito
4. El contenido del paquete está dañado aunque el embalaje exterior parezca intacto

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Registrar incidencia con evidencia fotográfica del daño (paquete + contenido) | Agente / Cliente | Inmediato |
| 2 | Solicitar al cliente fotografías detalladas si el daño se detectó en destino | CX / Agente | < 1h |
| 3 | Abrir reclamación con el transportista adjuntando evidencia | Coordinador logístico | < 2h |
| 4 | Determinar si procede reemvío inmediato o reembolso según política del cliente | Coordinador logístico | < 4h |
| 5 | Ejecutar reemvío urgente o procesar reembolso | Coordinador logístico | < 8h |
| 6 | Gestionar compensación con transportista (reembolso por daño) | Coordinador logístico | < 15 días |
| 7 | Cerrar incidencia tras reposición confirmada y cliente satisfecho | Agente | < 1h tras confirmación |

## Excepciones

- Si el daño es recurrente (>3 en mismo mes con mismo transportista), escalar a **Dirección**
- Si el cliente B2B exige compensación adicional, escalar a **Comercial**

## Métrica asociada

- **Tasa de daños por transportista**
- **Coste medio por incidencia de daño**