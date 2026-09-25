# TEC-001: Caída de sistema

**Ámbito:** Tecnología
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un sistema crítico (API, SGA, base de datos, portal de tracking) deja de responder o está degradado, se debe activar el protocolo de respuesta inmediata para restaurar el servicio y minimizar el impacto operativo.

## Condición verificable

Se activa esta regla si **una o más** de las siguientes condiciones se cumplen:

1. Una alerta automática de monitorización notifica que un servicio no responde
2. Un usuario reporta que un sistema está inaccesible o devuelve errores 5xx
3. Las pruebas de latitud/salud del sistema muestran tiempo de respuesta >10s o error
4. La base de datos no responde a consultas o replica con errores
5. El portal de tracking o backoffice muestra error de conexión

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Confirmar la caída y determinar el alcance (sistema afectado, usuarios afectados) | Ingeniero / Agente | < 5 min |
| 2 | Clasificar severidad: **Crítica** (caída total) o **Alta** (degradación parcial) | Ingeniero | < 5 min |
| 3 | Notificar a los departamentos afectados (Almacén si es SGA, CX si es portal de tracking, etc.) | Agente | < 10 min |
| 4 | Iniciar diagnóstico: revisar logs, métricas, estado de servicios, releases recientes | Ingeniero | < 15 min |
| 5 | Aplicar resolución: reiniciar servicio, hacer rollback, escalar a proveedor cloud si aplica | Ingeniero | < 30 min para crítica |
| 6 | Verificar que el servicio se ha restablecido completamente | Ingeniero | < 15 min tras fix |
| 7 | Si la caída supera los 30 min, escalar a **Dirección** (CTO) | Agente | A los 30 min |
| 8 | Documentar causa raíz y acciones en post-mortem | Ingeniero | < 24h tras resolución |
| 9 | Cerrar incidencia y notificar a afectados | Agente | < 1h tras post-mortem |

## Excepciones

- Si hay pérdida de datos confirmada, escalar inmediatamente a **Dirección**
- Si la caída afecta a las operaciones de almacén en ambos países, escalar a **Dirección**

## Métrica asociada

- **Disponibilidad de servicios** (Uptime % — target >99.9%)
- **Tiempo de resolución** (MTTR)