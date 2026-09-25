# TEC-002: Bug o error funcional

**Ámbito:** Tecnología
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando se detecta un bug en el software —un cálculo incorrecto, un endpoint que devuelve error, una lógica de negocio errónea— se debe registrar, diagnosticar y corregir el error.

## Condición verificable

Se activa esta regla si **una o más** de las siguientes condiciones se cumplen:

1. Un endpoint de la API devuelve un error 4xx o 5xx inesperado
2. Un cálculo (costes, impuestos, tarifas, descuentos) produce un resultado incorrecto verificado
3. Una funcionalidad existente deja de funcionar tras un despliegue
4. Un usuario reporta un comportamiento inconsistente en el sistema (frontend o backend)
5. Los tests automatizados detectan una regresión

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Registrar bug con detalle: pasos para reproducir, entorno, impacto, evidencia | Ingeniero / Agente | Inmediato |
| 2 | Clasificar severidad:<br>• **Crítico**: bloquea operaciones, sin workaround<br>• **Alto**: funcionalidad degradada, workaround costoso<br>• **Normal**: error sin bloqueo, workaround disponible<br>• **Bajo**: error cosmético, mejora | Ingeniero | < 30 min |
| 3 | Si es crítico: notificar a **Dirección** (CTO) y detener despliegues si aplica | Ingeniero | < 15 min |
| 4 | Diagnosticar causa raíz (revisar código, logs, trazas) | Ingeniero | < 4h para crítico |
| 5 | Desarrollar e implementar fix en entorno de desarrollo | Ingeniero | < 8h para crítico |
| 6 | Desplegar fix siguiendo procedimiento de release (pasar tests, code review) | Ingeniero | < 2h tras fix |
| 7 | Verificar que el fix resuelve el bug en producción | Ingeniero | < 1h tras deploy |
| 8 | Cerrar incidencia y documentar lección aprendida | Agente | < 1h tras verificación |

## Excepciones

- Si el bug afecta a datos de clientes (integridad, visibilidad), escalar a **Dirección** y a **Comercial**
- Si el bug es recurrente (misma causa apareció antes), escalar para análisis de proceso

## Métrica asociada

- **Incidentes por severidad**
- **Tiempo medio de resolución** por severidad
- **Incidentes recurrentes** (problemas que se repiten)