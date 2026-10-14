# TEC-004: Incidente de seguridad

**Ámbito:** Tecnología
**Versión:** 1.0
**Última revisión:** 2026-09-25

---

## Descripción

Cuando se detecta un intento de acceso no autorizado, una brecha de datos o una anomalía en los logs de seguridad, se debe activar el protocolo de respuesta a incidentes de seguridad inmediatamente.

## Condición verificable

Se activa esta regla si **una o más** de las siguientes condiciones se cumplen:

1. Se detecta un intento de acceso no autorizado a sistemas internos (múltiples intentos de login fallidos, acceso desde IP no reconocida)
2. Se confirma o sospecha una brecha de datos (exfiltración, acceso a datos de clientes sin autorización)
3. Hay una anomalía en logs de seguridad escaneada por herramientas de monitorización
4. Se reporta un ataque de denegación de servicio (DDoS) o fuerza bruta
5. Un certificado SSL/TLS ha expirado o es inválido
6. Se detecta malware, ransomware o actividad sospechosa en servidores

## Forma de aplicación

| Paso | Acción | Responsable | Plazo |
|---|---|---|---|
| 1 | Clasificar la gravedad del incidente: baja (intento aislado), media (patrón sospechoso), alta (brecha confirmada), crítica (brecha con datos de clientes) | Ingeniero | < 10 min |
| 2 | **Si es crítica o alta:** aislar los sistemas afectados (desconectar de red si es necesario) | Ingeniero | < 15 min |
| 3 | Notificar inmediatamente a **Dirección** (CTO y CEO) | Agente | < 10 min |
| 4 | Recopilar evidencia: logs, capturas, registros de acceso, líneas de tiempo | Ingeniero | < 2h |
| 5 | Si hay brecha de datos de clientes, notificar a **Comercial** y evaluar obligaciones legales de notificación | Ingeniero / Dirección | < 24h |
| 6 | Implementar medidas correctivas: rotar credenciales, parchear vulnerabilidad, reforzar firewall | Ingeniero | < 4h para crítica |
| 7 | Realizar análisis forense completo y documentar | Ingeniero | < 1 semana |
| 8 | Informar a los afectados (internos, clientes, autoridades si aplica) siguiendo指示 de Dirección | Dirección | Según legislación |
| 9 | Cerrar incidencia tras confirmación de que el riesgo ha sido mitigado | Agente | Tras aprobación de Dirección |

## Excepciones

- **No escalar a nadie fuera de dirección sin autorización explícita** — la comunicación externa la gestiona Dirección
- Si hay implicaciones legales o regulatorias, contactar a asesoría legal externa

## Métrica asociada

- **Número de incidentes de seguridad** por mes
- **Tiempo de detección** (MTTD)
- **Tiempo de resolución** (MTTR) de incidentes de seguridad