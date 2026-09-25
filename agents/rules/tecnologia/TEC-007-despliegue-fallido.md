# TEC-007: Despliegue fallido

**Ámbito:** Tecnología
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un despliegue en producción falla —release con errores, migración de base de datos fallida, rollback necesario— se debe activar el protocolo de rollback, evaluar el impacto y estabilizar el sistema.

## Condición verificable

Se activa esta regla si **una o más** de las siguientes condiciones se cumplen:

1. El despliegue de una nueva versión causa errores en producción (5xx, funcionalidad rota)
2. La migración de base de datos asociada al despliegue falla (timeout, error de esquema)
3. Los tests post-despliegue (smoke tests) fallan
4. Se detecta un bug crítico inmediatamente después del despliegue (TEC-002 activado)
5. El rendimiento empeora significativamente tras el despliegue (TEC-003 activado)

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Confirmar que el despliegue ha fallado y evaluar impacto en usuarios/sistemas | Ingeniero | < 5 min |
| 2 | Activar rollback inmediato a la versión anterior estable | Ingeniero | < 15 min |
| 3 | Si la migración de BD falló parcialmente, ejecutar rollback de migración o restaurar desde backup | Ingeniero / DBA | < 30 min |
| 4 | Verificar que el sistema funciona correctamente con la versión anterior (smoke tests) | Ingeniero | < 30 min tras rollback |
| 5 | Notificar a los departamentos afectados que el despliegue se ha revertido | Agente | < 15 min |
| 6 | Analizar causa del fallo: error en código, migración mal formada, problema de configuración, dependencia rota | Ingeniero | < 4h |
| 7 | Documentar lecciones aprendidas y ajustar proceso de despliegue (más tests, canary, feature flags) | Ingeniero | < 24h |
| 8 | Reprogramar nuevo despliegue con el fix aplicado | Ingeniero | Según severidad |
| 9 | Cerrar incidencia tras despliegue exitoso | Agente | < 1h tras éxito |

## Excepciones

- Si el rollback no es posible (cambios irreversibles en BD), escalar a **Dirección** (CTO) inmediatamente
- Si el despliegue fallido afecta a datos de clientes, escalar a **Dirección** y a **Comercial**

## Métrica asociada

- **Tasa de despliegues exitosos** (% sin necesidad de rollback)
- **Tiempo medio de detección de fallo post-despliegue**