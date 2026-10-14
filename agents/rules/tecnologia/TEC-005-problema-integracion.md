# TEC-005: Problema de integración con transportista o API externa

**Ámbito:** Tecnología
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando una integración con un transportista (UPS, FedEx, DHL, MRW, SEUR) o con un proveedor externo falla —conexión caída, webhook no entregado, API externa no responde— se debe diagnosticar y restaurar la integración.

## Condición verificable

Se activa esta regla si **una o más** de las siguientes condiciones se cumplen:

1. La conexión con la API de un transportista falla o devuelve errores (timeout, 5xx, autenticación)
2. Un webhook esperado no se recibe en >1h de lo esperado
3. La sincronización de tracking con transportistas no se actualiza
4. La generación de etiquetas de envío falla por error de integración
5. Un cambio en la API del transportista rompe la integración existente

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Registrar la incidencia con detalle del transportista/proveedor y el error observado | Ingeniero / Agente | Inmediato |
| 2 | Verificar si el problema es general (todos los transportistas) o específico de uno | Ingeniero | < 15 min |
| 3 | Consultar el estado del servicio del transportista (status page, documentación) | Ingeniero | < 30 min |
| 4 | Si el problema es del transportista (API externa caída): escalar al soporte del transportista | Ingeniero | < 1h |
| 5 | Si el problema es interno (configuración, código): diagnosticar y aplicar fix | Ingeniero | < 2h |
| 6 | Notificar a **Última Milla** del estado de la integración y posible impacto en envíos | Agente | < 30 min |
| 7 | Verificar que la integración funciona correctamente tras el fix | Ingeniero | < 1h tras fix |
| 8 | Si el transportista tiene una incidencia abierta, hacer seguimiento hasta resolución | Ingeniero | Cada 24h |
| 9 | Cerrar incidencia tras confirmación de operatividad | Agente | < 1h tras verificación |

## Excepciones

- Si la integración caída afecta a >50 pedidos/día, escalar a **Dirección**
- Si el transportista no resuelve en >48h, escalar a **Dirección** para evaluar alternativas

## Métrica asociada

- **Disponibilidad de integraciones con transportistas**
- **Tiempo medio de resolución** de incidencias de integración