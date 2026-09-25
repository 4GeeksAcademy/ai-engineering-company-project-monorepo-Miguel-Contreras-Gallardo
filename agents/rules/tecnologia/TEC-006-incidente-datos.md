# TEC-006: Incidente de datos

**Ámbito:** Tecnología
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando se detectan datos corruptos, inconsistencias entre sistemas, migraciones fallidas o pérdida de información, se debe evaluar el impacto, restaurar la integridad de los datos y prevenir recurrencias.

## Condición verificable

Se activa esta regla si **una o más** de las siguientes condiciones se cumplen:

1. Se detectan datos corruptos en la base de datos (valores nulos inesperados, relaciones rotas)
2. Hay inconsistencia entre dos sistemas que deberían estar sincronizados (SGA vs BD de inventario)
3. Una migración de datos falla o se completa con errores
4. Un proceso ETL produce resultados incorrectos
5. Se identifica pérdida de datos (registros borrados, tablas truncadas, backup corrupto)
6. Se detectan duplicados en registros críticos (pedidos, clientes, productos)

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Registrar la incidencia con detalle del sistema, los datos afectados y el tipo de anomalía | Ingeniero | Inmediato |
| 2 | Clasificar severidad: crítica (pérdida de datos), alta (inconsistencia), normal (corrupción menor) | Ingeniero | < 30 min |
| 3 | Si es crítica: detener procesos que escriben en la BD afectada y notificar a **Dirección** | Ingeniero | Inmediato |
| 4 | Restaurar desde backup si hay pérdida de datos confirmada | Ingeniero / DBA | < 2h para crítica |
| 5 | Si es inconsistencia: identificar causa raíz (bug en código, sincronización fallida, error manual) | Ingeniero | < 4h |
| 6 | Ejecutar script de corrección de datos (con revisión y aprobación previa) | Ingeniero | < 8h |
| 7 | Verificar que la integridad de datos se ha restaurado | Ingeniero | < 2h tras corrección |
| 8 | Implementar medidas preventivas (validaciones, alertas, tests) | Ingeniero | < 1 semana |
| 9 | Cerrar incidencia | Agente | < 1h tras verificación |

## Excepciones

- Si los datos afectados son de clientes, notificar a **Comercial** y evaluar impacto legal
- Si la causa raíz es un bug en código, activar TEC-002 para el fix funcional

## Métrica asociada

- **Número de incidentes de datos** por mes
- **Tiempo medio de resolución** de incidentes de datos