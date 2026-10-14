# TEC-003: Problema de rendimiento

**Ámbito:** Tecnología
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando un sistema o funcionalidad presenta lentitud, timeouts, alto consumo de recursos o cuellos de botella, se debe diagnosticar el origen del problema de rendimiento y aplicar optimizaciones.

## Condición verificable

Se activa esta regla si **una o más** de las siguientes condiciones se cumplen:

1. El tiempo de respuesta de un endpoint de la API supera los 2 segundos (target)
2. Los usuarios reportan lentitud en el sistema (SGA, portal, backoffice)
3. El consumo de CPU, memoria o disco supera el 80% durante >15 minutos
4. Hay timeouts en conexiones a base de datos o APIs externas
5. Las alertas de monitorización muestran degradación en métricas de rendimiento (p95, p99)

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Registrar el problema de rendimiento con métricas actuales y línea base | Ingeniero | Inmediato |
| 2 | Identificar el componente afectado (API, BD, frontend, integración externa) | Ingeniero | < 30 min |
| 3 | Diagnosticar causa: revisar queries lentas, uso de recursos, cuellos de botella, contención | Ingeniero | < 2h |
| 4 | Aplicar optimización inmediata si es posible (índice, caché, escalado horizontal, timeout) | Ingeniero | < 4h |
| 5 | Si la optimización requiere cambio de infraestructura, planificar con **Dirección** (CTO) | Ingeniero / CTO | < 1 semana |
| 6 | Verificar que las métricas de rendimiento vuelven a valores aceptables tras la optimización | Ingeniero | < 1h tras fix |
| 7 | Documentar la causa raíz y la solución aplicada | Ingeniero | < 24h |
| 8 | Cerrar incidencia | Agente | < 1h tras documentación |

## Excepciones

- Si el problema afecta a la operación de almacén (SGA lento), escalar a **Almacén** para contingencia
- Si el problema persiste >24h sin mejora, escalar a **Dirección** (CTO)

## Métrica asociada

- **Tiempo de respuesta medio** de la API
- **Disponibilidad de servicios** (uptime)
- **Uso de recursos** (% CPU, memoria, disco)