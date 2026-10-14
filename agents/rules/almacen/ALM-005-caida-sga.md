# ALM-005: Caída de SGA (sistema de gestión de almacenes)

**Ámbito:** Almacén (escalable a Tecnología)
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando el Sistema de Gestión de Almacenes (SGA) deja de estar operativo —no responde, se congela, o los operarios no pueden registrar movimientos— se debe activar el protocolo de contingencia y escalar a Tecnología para su restauración.

## Condición verificable

Se activa esta regla si **una o más** de las siguientes condiciones se cumplen:

1. El SGA no responde a las peticiones de los operarios durante > 5 minutos
2. Los operarios no pueden registrar entradas, salidas o movimientos de inventario
3. El sistema muestra errores de conexión o base de datos
4. Una alerta automática de monitorización notifica caída del SGA

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Verificar si la caída afecta a todos los terminales o solo a uno | Agente / Operario | < 5 min |
| 2 | Si es general, activar protocolo de contingencia: operar con hojas de registro físicas | Responsable de almacén | Inmediato |
| 3 | Escalar incidencia a **Tecnología** con detalle del síntoma y alcance | Agente | < 10 min |
| 4 | Informar a operarios del modo de operación alternativo | Responsable de almacén | < 15 min |
| 5 | Cuando Tecnología confirme restauración, verificar que el SGA funciona correctamente | Responsable de almacén | < 15 min tras aviso |
| 6 | Registrar movimientos realizados en papel en el SGA | Operarios | < 2h tras restauración |
| 7 | Cerrar incidencia documentando duración de la caída | Agente | < 1h tras cierre |

## Excepciones

- Si la caída supera los 30 minutos, escalar automáticamente a **Dirección**
- Si hay pérdida de datos confirmada, escalar a **Dirección** inmediatamente

## Métrica asociada

- **Disponibilidad del SGA** (% uptime)
- **Tiempo medio de restauración** (MTTR)