# COM-005: Alta de nuevo cliente B2B (onboarding)

**Ámbito:** Comercial
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un nuevo cliente B2B contrata los servicios de TrackFlow, se debe coordinar el proceso de onboarding completo incluyendo la integración técnica, la configuración operativa y la documentación contractual.

## Condición verificable

Se activa esta regla cuando **todas** las siguientes condiciones se cumplen:

1. Se ha firmado un nuevo contrato con un cliente B2B
2. El cliente no ha sido configurado previamente en los sistemas de TrackFlow
3. Se requiere integración técnica, operativa o ambas

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Registrar al nuevo cliente en el sistema CRM con datos contractuales | Account manager | < 24h tras firma |
| 2 | Configurar al cliente en el sistema de operaciones (SGA, facturación, tracking) | Account manager / Tecnología | < 48h |
| 3 | Si requiere integración técnica (API): coordinar con **Tecnología** la documentación y pruebas | Account manager | < 1 semana |
| 4 | Configurar reglas de negocio específicas: políticas de devolución, ventanas de entrega, SLAs | Account manager | < 48h |
| 5 | Asignar account manager y equipo de soporte al cliente | Responsable Comercial | < 24h |
| 6 | Realizar sesión de onboarding con el cliente: explicar proceso, canales de contacto, reporting | Account manager | < 1 semana |
| 7 | Verificar que el primer pedido se procesa sin incidencias | Account manager | < 24h tras primer pedido |
| 8 | Cerrar incidencia de alta tras confirmación de operatividad del cliente | Agente | Tras paso 7 |

## Excepciones

- Si la integración técnica es compleja (>1 semana), escalar a **Tecnología** para planificación
- Si el cliente requiere funcionalidades no existentes, escalar a **Dirección** para decisión de desarrollo

## Métrica asociada

- **Tiempo medio de onboarding** (firma → primer pedido procesado)
- **Tasa de incidencias en primeros 30 días** de nuevos clientes