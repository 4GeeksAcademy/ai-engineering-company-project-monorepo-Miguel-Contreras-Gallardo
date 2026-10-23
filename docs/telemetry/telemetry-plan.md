# 📡 Plan de Telemetría — TrackFlow

> **Versión:** 1.0  
> **Fecha:** 2026-10-21  
> **Proyecto:** TrackFlow — Plataforma de Automatización e IA  
> **Ubicación:** `docs/telemetry/telemetry-plan.md`

---

## 1. OBJETIVO

Definir el sistema de telemetría centralizada para TrackFlow que permita capturar, almacenar y analizar eventos de todos los departamentos, reemplazando la ausencia actual de telemetría (caídas detectadas por WhatsApp, datos con 1-2 días de retraso, informes consolidados manualmente).

El sistema debe proporcionar:
- Visibilidad en tiempo real del estado de la operación
- Alertas automáticas ante desviaciones
- Datos históricos para análisis de rendimiento y tendencias
- Fuente única de verdad para los dashboards ejecutivos y departamentales

---

## 2. MÉTRICAS OBLIGATORIAS

A continuación se listan las **métricas obligatorias** que TrackFlow debe medir, derivadas del briefing de la compañía y los objetivos estratégicos.

| ID | Métrica | Descripción | Objetivo | Departamento | Fórmula |
|---|---|---|---|---|---|
| **M01** | Tasa de entrega a tiempo | Porcentaje de envíos entregados en la fecha prometida | >97% | Última Milla | `(envíos a tiempo / total envíos) × 100` |
| **M02** | Tiempo medio de picking | Tiempo promedio desde que se asigna un pedido hasta que se completa el picking | <15 min | Almacén | `sum(tiempo_picking) / count(pedidos)` |
| **M03** | Tasa de devoluciones | Porcentaje del volumen de pedidos que resulta en devolución | 18-25% (ref.) | Logística Inversa | `(devoluciones / total envíos) × 100` |
| **M04** | Tasa de resolución automática CX | Porcentaje de consultas de CX resueltas sin intervención humana | >60% | CX | `(tickets resueltos por IA / total tickets) × 100` |
| **M05** | Frescura de datos (CEO) | Retraso máximo entre que ocurre un evento y se refleja en el informe ejecutivo | Tiempo real (<5 min) | Dirección | `timestamp_consulta - timestamp_evento` |
| **M06** | Coste por kg enviado | Coste medio de envío por kilogramo, desglosado por transportista y ruta | Sin target (benchmark) | Última Milla | `sum(coste_envío) / sum(peso_kg)` |
| **M07** | Tiempo de deploy | Tiempo desde que se aprueba un cambio hasta que está en producción | <1 día | Tecnología | `timestamp_producción - timestamp_aprobación` |
| **M08** | Tasa de incidencias resueltas SLA | Porcentaje de incidencias resueltas dentro del SLA acordado | >95% | Tecnología / Operaciones | `(incidencias dentro SLA / total incidencias) × 100` |
| **M09** | Rotura de stock | Número de veces que un SKU agota su inventario disponible en un almacén | 0 | Almacén | `count(eventos stock_cero)` |
| **M10** | Satisfacción de cliente B2B | Scoring de renovación basado en satisfacción con la operación logística | >8/10 | Comercial | `promedio(satisfacción_cliente)` |

### 2.1 Trazabilidad y condiciones de cálculo

`CONTEXT.md` no contiene una tabla normativa M01–M10. Sus necesidades y problemas sustentan las métricas operativas; `memory-bank/project-brief.md` §1.6 sí enumera explícitamente M01–M07. M08–M10 son ampliaciones de este plan derivadas de necesidades de incidencias/auditoría, renovaciones y control de roturas; no deben atribuirse como KPIs literales del briefing. Antes de publicar cada KPI, validar que la fuente transaccional cubra el universo completo y no solo los eventos incluidos en este plan.

| KPI | Fuente y cálculo operativo | Estado de cobertura telemétrica / dato pendiente |
|---|---|---|
| M01 | Cohorte de envíos elegibles creada en el período; numerador: envíos entregados antes o en la promesa; denominador: todos los envíos elegibles de esa cohorte, incluidos tardíos y aún no entregados al cierre. Definir zona horaria, exclusiones y ventana de maduración. | `shipment_delivered` da el resultado para entregados, pero no formaliza el denominador ni la cohorte; `shipment.created` es conceptual/no instrumentable sin schema. **Incompleto** hasta integrar la fuente autoritativa de envíos y estados pendientes. |
| M02 | Promedio de `completedAt - assignedAt` por pedido completado en el período; definir cómo tratar pausas, cancelaciones y pedidos reabiertos. | El schema formal registra `startedAt`, `completedAt` y `pickingTimeMinutes`, no `assignedAt`. El KPI actual dice desde asignación y el texto del evento desde inicio: escoger un único hito y alinear fórmula, schema y emisor. **Inconsistente**. |
| M03 | Devoluciones atribuibles a envíos de una cohorte / total de envíos de esa misma cohorte, con ventana de atribución posterior a la entrega declarada. | `return_completed` es numerador potencial; falta denominador de envíos y ventana comparable. `return.requested` conceptual no sustituye la confirmación de devolución. **Incompleto** hasta unir con envíos. |
| M04 | Tickets elegibles creados en una cohorte; numerador: los resueltos automáticamente sin intervención humana dentro de la ventana de resolución; denominador: todos los tickets elegibles, incluidos escalados y no resueltos. | `ticket_auto_resolved` aporta numerador; `ticket.created` es conceptual/no formal. Definir tratamiento de recontactos, reaperturas, bots y tickets excluidos. **Incompleto** hasta registrar el universo de tickets. |
| M05 | En cada consulta/generación, `consultedAt - sourceEventTimestamp` (o timestamp del dato fuente más antiguo, si “frescura” se refiere al conjunto); conservar unidad, fuente y percentil/peor caso por ventana. | `dataFreshnessSeconds` está en el evento formal, pero la semántica de timestamp base, instante de consulta y agregación no está fijada. El campo `timestamp` del envelope es ocurrencia del evento, no necesariamente timestamp de consulta. **Parcial**; definir contrato y validar contra el pipeline de datos. |
| M06 | Coste liquidado/facturado del envío en moneda normalizada / peso facturable real en kg, sumar costes y pesos para el promedio ponderado; agrupar por transportista y ruta en una cohorte declarada. | `shipment_carrier_assigned` solo ofrece `estimatedCost` y `weightKg`; no prueba coste real ni ruta. **No calculable como KPI real** sin fuente de liquidación/factura, moneda, peso facturable y ruta. No etiquetar estimaciones como coste realizado. |
| M07 | `productionAt - approvedAt` por cambio desplegado; definir aprobador/instante de aprobación, zona horaria y tratamiento de rollback/fallo. | `deployment_completed.durationMinutes` mide duración de despliegue, no necesariamente tiempo desde aprobación; `deployment_started` es conceptual. **Incompleto** hasta capturar/consultar aprobación y producción con una clave de cambio correlacionable. |
| M08 | Incidencias elegibles resueltas antes o en su deadline SLA / todas las incidencias cuyo SLA vence en la cohorte; para incidencias aún abiertas, contar incumplimiento al vencer. | `incident_sla_breached` registra incumplimientos, no el universo ni las resoluciones a tiempo. `api_error_breached`, `api_latency_recorded` y `frontend_error_recorded` son señales técnicas y no incidencias de negocio. **No calculable solo con telemetría actual**: integrar creación, resolución y deadline de la fuente de incidencias. |
| M09 | Contar transiciones de stock disponible positivo a cero por combinación de SKU y almacén (y cliente cuando la propiedad se pueda resolver), no cada lectura/heartbeat. | `stock_depleted` puede representar la transición; el emisor debe aplicar edge-triggered y rearmar solo tras recuperación a >0. `direct_stock_edit_rejected` no es rotura ni debe alimentar el conteo. El ledger de inventario puede calcular stock por lote+almacén, pero el contrato exige `skuId` y `clientId` UUID, ubicación limitada a `LA`/`Zaragoza` y hay múltiples lotes; el servicio actual usa SKU textual, no asocia cliente y no garantiza exclusividad concurrente para una transición SKU+almacén. **No emitible de forma fiable desde el backoffice/servicio actual** hasta definir IDs y correspondencia de almacenes, el alcance del stock agregado (por lote o SKU) y una deduplicación transaccional para concurrencia/reintentos. |
| M10 | Promedio de respuestas válidas de una encuesta B2B definida (escala 0–10), por cliente/cohorte/ventana; informar tasa de respuesta. Separar satisfacción observada de score predictivo de renovación. | `client_health_score_updated.healthScore` y subscores son proxies; no son automáticamente una encuesta de satisfacción. `ticket.satisfaction_rated` se refiere a CX y no necesariamente a satisfacción logística B2B. **No equivalente** hasta definir encuesta, población, fórmula del health score y fuente de respuestas. |

Los estados **incompleto**, **inconsistente** y **no calculable** son bloqueos explícitos de analítica, no permiso para aproximar silenciosamente el KPI. Los cálculos se deben contrastar periódicamente con las fuentes de negocio.

---

## 3. ENTIDADES DEL SISTEMA DE INVENTARIO

Las entidades clave del dominio de inventario sobre las que se emitirán eventos de telemetría:

| Entidad | Descripción | Atributos clave |
|---|---|---|
| **Cliente (Marca)** | Empresa de e-commerce que contrata TrackFlow | id, nombre, pais, contrato_id, scoring_renovacion |
| **SKU** | Unidad de stock keeping | id, nombre, peso_kg, dimensiones_cm, categoria, valor_unitario |
| **Almacén** | Centro logístico (LA / Zaragoza) | id, ubicacion, sga_tipo, capacidad |
| **Inventario** | Stock de un SKU en un almacén | sku_id, almacen_id, cantidad_disponible, stock_minimo, stock_seguridad |
| **Pedido** | Solicitud de envío de una marca | id, cliente_id, fecha_creacion, estado, canal_entrada, lineas[] |
| **LíneaPedido** | Producto dentro de un pedido | id, pedido_id, sku_id, cantidad, precio_unitario |
| **Lote** | Lote asociado a un artículo | id, articulo_id, codigo, fecha_creacion |
| **Envío** | Unidad logística hacia consumidor | id, pedido_id, transportista_id, numero_tracking, estado, destino, peso_kg, urgente |
| **TrackingEvent** | Evento de seguimiento | envio_id, timestamp, estado, ubicacion, transportista |
| **Devolución** | Producto devuelto por consumidor | id, envio_id, motivo, estado_aprobacion, estado_inspeccion, fecha_solicitud |
| **Inspección** | Evaluación del producto devuelto | devolucion_id, operario_id, fotos[], clasificacion_ia, dictamen |
| **Transportista** | Empresa de mensajería | id, nombre, pais_operacion, tarifas[], metricas_rendimiento |
| **Ticket** | Consulta de CX | id, origen, cliente_tipo, estado, resuelto_por_ia, agente_id |
| **Incidencia** | Desviación operativa con auditoría | id, titulo, categoria, prioridad, estado, area_asignada, audit_log[] |

---

## 4. RESTRICCIONES DE NEGOCIO

Las siguientes restricciones condicionan cómo y qué eventos de telemetría deben capturarse:

### 4.1 Inventario
- **R-INV-01:** TrackFlow no produce ni vende productos — solo los almacena y gestiona su logística. Los eventos de inventario deben reflejar exclusivamente movimientos reales.
- **R-INV-02:** El inventario es propiedad de las marcas clientes. La telemetría debe distinguir eventos por cliente.
- **R-INV-03:** Cada almacén opera de forma independiente; no hay traspaso automático entre almacenes. Los eventos de stock se emiten por almacén.
- **R-INV-04:** Stock mínimo configurable por SKU y cliente. Las alertas de reorden se emiten cuando el stock cae por debajo del mínimo.

### 4.2 Envíos y Transportistas
- **R-ENV-01:** 8 transportistas con cobertura en EE.UU. y España, cada uno con API de tracking propia. Se deben unificar los eventos de tracking.
- **R-ENV-02:** La asignación de transportista debe considerar destino, peso, urgencia y coste. La telemetría debe capturar la decisión y sus factores.
- **R-ENV-03:** Los envíos urgentes tienen prioridad en la asignación. El evento debe incluir flag `urgente`.

### 4.3 Devoluciones
- **R-DEV-01:** Tasa de devolución del 18-25%. Se debe monitorizar la tasa por cliente y motivo.
- **R-DEV-02:** La aprobación depende de motivo, cliente, valor del producto y tiempo desde compra. Cada decisión debe auditarse.
- **R-DEV-03:** Tras inspección, el producto se reacondiciona o desecha. El evento debe incluir el dictamen final.

### 4.4 Atención al Cliente
- **R-CX-01:** Dos perfiles (B2B y B2C) con necesidades distintas. Los eventos de CX deben etiquetar el tipo de cliente.
- **R-CX-02:** Idiomas: español (Zaragoza) e inglés (Los Ángeles). El evento debe incluir el idioma.

### 4.5 Comercial
- **R-COM-01:** Contratos anuales con marcas. Renovación basada en satisfacción. Se deben emitir eventos de salud de cuenta.

---

## 5. CATÁLOGO DE EVENTOS

La columna **Tipo** clasifica cada evento según su origen:

- **Obligatorio** — Evento derivado directamente del BRIEFING (`CONTEXT.md`). Su necesidad está explícitamente justificada por los KPIs, problemas o necesidades documentadas de la compañía. Responde a los 10 objetivos estratégicos (M01–M10).
- **Oportunidad identificada** — Evento propuesto a partir del análisis exploratorio del código existente (backoffice, website, API). No está explícitamente en el briefing, pero aporta valor diagnóstico, de rendimiento o de experiencia de usuario.

### 5.1 Eventos de Inventario / Almacén

| Evento | Descripción | Disparador | Métricas asociadas | Tipo |
|---|---|---|---|---|
| `inventory.received` | Entrada de mercancía a almacén | Confirmación de recepción de proveedor | M02, M09 | **Obligatorio** |
| `inventory.shipped` | Salida de mercancía por pedido | Confirmación de picking + envío | M02, M09 | **Obligatorio** |
| `inventory.adjusted` | Ajuste de inventario manual | Operario realiza ajuste | M09 | **Obligatorio** |
| `inventory.stock_low` | Stock por debajo del mínimo | Evaluación periódica de niveles | M09 | **Obligatorio** |
| `inventory.stock_critical` | Stock crítico (riesgo de rotura) | Evaluación periódica | M09 | **Obligatorio** |
| `inventory.stock_out` | Stock agotado (rotura) | Intento de salida sin stock | M09 | **Obligatorio** |
| `order.received` | Pedido entrante de una marca | Recepción de pedido (email/API) | M02 | **Obligatorio** |
| `order.picking_started` | Inicio de picking de un pedido | Operario escanea primera línea | M02 | **Obligatorio** |
| `order.picking_completed` | Finalización de picking | Última línea escaneada | M02 | **Obligatorio** |

### 5.2 Eventos de Última Milla / Transportistas

| Evento | Descripción | Disparador | Métricas asociadas | Tipo |
|---|---|---|---|---|
| `shipment.created` | Envío creado y listo para asignar | Finalización de empaquetado | M01, M06 | **Obligatorio** |
| `shipment.carrier_assigned` | Transportista asignado al envío | Ejecución del motor de selección | M01, M06 | **Obligatorio** |
| `shipment.in_transit` | Envío recogido por transportista | API del transportista | M01 | **Obligatorio** |
| `shipment.delivered` | Envío entregado al consumidor | API del transportista | M01 | **Obligatorio** |
| `shipment.delivery_failed` | Intento de entrega fallido | API del transportista | M01, M06 | **Obligatorio** |
| `shipment.delayed` | Envío con retraso respecto a fecha prometida | Comparación cronograma vs real | M01 | **Obligatorio** |
| `tracking.event_received` | Evento de tracking desde API de transportista | Polling/webhook de transportista | M01 | **Obligatorio** |
| `carrier.performance_updated` | Métricas de rendimiento de transportista recalculadas | Procesamiento batch diario | M06 | **Obligatorio** |

### 5.3 Eventos de Logística Inversa / Devoluciones

| Evento | Descripción | Disparador | Métricas asociadas | Tipo |
|---|---|---|---|---|
| `return.requested` | Solicitud de devolución iniciada | Consumidor solicita devolución | M03 | **Obligatorio** |
| `return.approved` | Devolución aprobada (automática o manual) | Motor de reglas de aprobación | M03 | **Obligatorio** |
| `return.rejected` | Devolución rechazada | Motor de reglas de aprobación | M03 | **Obligatorio** |
| `return.pickup_scheduled` | Recogida del paquete asignada | Coordinación con transportista | M03 | **Obligatorio** |
| `return.received_at_warehouse` | Producto recibido en almacén | Escaneo de recepción | M03 | **Obligatorio** |
| `return.inspected` | Inspección completada con dictamen | Operario o IA finaliza inspección | M03 | **Obligatorio** |
| `return.reconditioned` | Producto reacondicionado y reingresado a inventario | Finalización de reacondicionamiento | M03 | **Obligatorio** |
| `return.discarded` | Producto desechado | Dictamen de inspección | M03 | **Obligatorio** |

### 5.4 Eventos de CX / Atención al Cliente

| Evento | Descripción | Disparador | Métricas asociadas | Tipo |
|---|---|---|---|---|
| `ticket.created` | Nuevo ticket de CX creado | Consulta entrante (email/WhatsApp/tel) | M04 | **Obligatorio** |
| `ticket.classified` | Ticket clasificado automáticamente por categoría | Clasificación IA | M04 | **Obligatorio** |
| `ticket.auto_resolved` | Ticket resuelto automáticamente por IA | Respuesta automática exitosa | M04 | **Obligatorio** |
| `ticket.escalated` | Ticket escalado a agente humano | IA no pudo resolver | M04 | **Obligatorio** |
| `ticket.resolved_by_agent` | Ticket resuelto por agente humano | Agente cierra ticket | M04 | **Obligatorio** |
| `ticket.satisfaction_rated` | Cliente califica la atención recibida | Encuesta post-interacción | M10 | **Obligatorio** |

### 5.5 Eventos de Comercial / Clientes

| Evento | Descripción | Disparador | Métricas asociadas | Tipo |
|---|---|---|---|---|
| `client.contract_created` | Nuevo contrato con marca registrado | Firma de contrato | M10 | **Obligatorio** |
| `client.contract_renewal_approaching` | Contrato próximo a renovar (90/30 días) | Evaluación programada | M10 | **Obligatorio** |
| `client.contract_renewed` | Contrato renovado | Confirmación de renovación | M10 | **Obligatorio** |
| `client.contract_churned` | Contrato no renovado (pérdida de cliente) | Vencimiento sin renovación | M10 | **Obligatorio** |
| `client.health_score_updated` | Scoring de salud de cliente recalculado | Evaluación periódica | M10 | **Obligatorio** |
| `report.monthly_generated` | Informe mensual de rendimiento generado | Programación automática | M10 | **Obligatorio** |

### 5.6 Eventos de Tecnología / Infraestructura

| Evento | Descripción | Disparador | Métricas asociadas | Tipo |
|---|---|---|---|---|
| `system.service_health_changed` | Cambio en estado de salud de un servicio | Check de health endpoint | M08 | **Obligatorio** |
| `system.deployment_started` | Inicio de despliegue de nueva versión | Trigger de CI/CD | M07 | **Obligatorio** |
| `system.deployment_completed` | Despliegue completado exitosamente | CI/CD finaliza | M07 | **Obligatorio** |
| `system.deployment_failed` | Despliegue fallido | CI/CD detecta error | M07 | **Obligatorio** |
| `system.error_rate_breach` | Tasa de error de API supera umbral | Monitorización de endpoints | M08 | **Obligatorio** |
| `system.latency_breach` | Latencia de endpoint supera umbral | Monitorización de rendimiento | M08 | **Obligatorio** |
| `system.resource_critical` | Recurso (CPU/memoria/disco) en nivel crítico | Monitorización de infraestructura | M08 | **Obligatorio** |

### 5.7 Eventos de Dirección / Ejecutivos

| Evento | Descripción | Disparador | Métricas asociadas | Tipo |
|---|---|---|---|---|
| `executive.weekly_report_generated` | Informe semanal automático generado | Programación (lunes 7:00 AM) | M05 | **Obligatorio** |
| `executive.alert_triggered` | Alerta por desviación en KPI crítico | Evaluación de umbrales | M05, M08 | **Obligatorio** |
| `executive.kpi_breach` | KPI por debajo del umbral mínimo aceptable | Evaluación periódica de KPIs | Todas | **Obligatorio** |

### 5.8 Eventos de Frontend / UI (Backoffice)

Estos eventos describen señales de autenticación, rendimiento percibido, errores de frontend, navegación e interacciones del backoffice. Solo se emiten cuando existe un productor real. La UI actual no contiene login: los hooks centralizados `trackflow:login_failed` y `trackflow:session_expired` quedan disponibles para el futuro proveedor de autenticación y no se simulan desde navegación. El backoffice vanilla captura Web Vitals mediante `PerformanceObserver`, sin depender de Next.js.

| ID | Evento | Descripción | Disparador | Tipo |
|---|---|---|---|---|
| F01 | `frontend.auth.login_attempted` | Intento de inicio de sesión | Usuario introduce credenciales y pulsa "Entrar" | Oportunidad |
| F02 | `frontend.auth.login_succeeded` | Inicio de sesión exitoso | Autenticación verificada correctamente | Oportunidad |
| F03 | `frontend.auth.login_failed` (`login_failed`) | Fallo de autenticación con razón categórica (`invalid_credentials` / `network_error`) | Hook global `trackflow:login_failed` del proveedor de autenticación | Oportunidad; hook central disponible, sin formulario en la UI |
| F04 | `frontend.auth.session_expired` (`session_expired`) | Sesión autenticada expirada, razón `session_expired` | Hook global `trackflow:session_expired` del proveedor de autenticación | Oportunidad; hook central disponible, sin autenticación real en la UI |
| F05 | `frontend.auth.logout` | Cierre de sesión voluntario | Usuario cierra sesión explícitamente | Oportunidad |
| F06 | `frontend.api_request_completed` | Petición a API completada | Cada llamada `fetch()` desde el backoffice, con duración y código HTTP | **Obligatorio** (M08) |
| F07 | `frontend.api_request_failed` | Petición a API fallida (red/5xx) | `fetch()` lanza error de red o respuesta 5xx | **Obligatorio** (M08) |
| F08 | `frontend.slow_request_detected` | Petición lenta detectada | Duración de petición supera umbral configurable (>3s) | **Obligatorio** (M08) |
| F09 | `frontend.domain_load_time` | Tiempo de carga completo del backoffice | Evento `DOMContentLoaded` o `load` del navegador | Oportunidad |
| F10 | `frontend.api_connection_lost` | Conexión con la API interrumpida | Fallo consecutivo de health check desde el frontend | **Obligatorio** (M08) |
| F11 | `frontend.uncaught_error` | Error JavaScript no capturado | Evento `window.onerror` del navegador | Oportunidad |
| F12 | `frontend.unhandled_promise_rejection` | Promesa rechazada sin manejo | Evento `window.onunhandledrejection` | Oportunidad |
| F13 | `frontend.http_validation_error` | Error de validación HTTP (422) desde la API | Respuesta 422 con `body.detail` | Oportunidad |
| F14 | `frontend.toast_displayed` | Toast de error mostrado al operario | Llamada a `showToast(message, isError=true)` | Oportunidad |
| F15 | `frontend.view_changed` | Cambio de vista en el backoffice | Ejecución de `switchView(viewId)` | Oportunidad |
| F16 | `frontend.feature_used` | Uso de una funcionalidad concreta | Click en botón de acción (refresh, nuevo artículo, movimiento, lote, editar, dar de baja) | Oportunidad |
| F17 | `frontend.flow_abandoned` | Diálogo modal abierto y cerrado sin completar | Apertura de modal (`showModal()`) seguida de cierre sin submit | Oportunidad |
| F18 | `frontend.article_search_performed` | Búsqueda de artículos en la tabla | Evento `input` en el campo de búsqueda | Oportunidad |
| F19 | `frontend.nav_item_disabled_clicked` | Click en sección deshabilitada (Pedidos / Envíos) | Click en `.nav-item.disabled` | Oportunidad |
| F20 | `web_vital_recorded` | Web Vital (TTFB, FCP, LCP, CLS o INP) con valor, rating y ruta estática sanitizada | `PerformanceObserver`; métricas finales al ocultar/salir de página | Oportunidad; instrumentado en el backoffice vanilla |
| F20 | `frontend.movement_form_opened` | Formulario de movimiento abierto | Click en "Nuevo movimiento" | Oportunidad |
| F21 | `frontend.movement_registration_cancelled` | Registro de movimiento cancelado | Diálogo de movimiento cerrado sin guardar | Oportunidad |
| F22 | `frontend.article_deactivation_confirmed` | Confirmación de baja de artículo | Confirmación en `window.confirm()` + DELETE exitoso | Oportunidad |

### 5.9 Eventos de Website Corporativo

Eventos emitidos desde la web pública de TrackFlow (no requiere autenticación). Miden interacción de visitantes y leads comerciales.

| ID | Evento | Descripción | Disparador | Tipo |
|---|---|---|---|---|
| W01 | `website.contact_form_submitted` | Formulario de contacto enviado | Submit del formulario de contacto | **Obligatorio** (M10) |
| W02 | `website.section_viewed` | Sección de la web visualizada | Sección entra en el viewport (IntersectionObserver) | Oportunidad |
| W03 | `website.navigation_clicked` | Click en enlace de navegación | Click en cualquier enlace del menú principal | Oportunidad |

---

## 6. ESQUEMA DE EVENTOS COMÚN

Todos los eventos de telemetría comparten una **envoltura estándar** con campos comunes:

```json
{
  "eventId": "a1b2c3d4-e5f6-4a7b-9c0d-1e2f3a4b5c6d",
  "timestamp": "2026-10-22T14:30:00.000Z",
  "sessionId": "23de1bfd-7863-5f1d-9d2c-d6f91f9233d5",
  "userId": "usr_7f4d9e2a1b8c",
  "event_type": "shipment_delivered",
  "schemaVersion": "1.0",
  "requestId": "a2bdcd21-db67-550c-85ca-5f1759fbfa4e",
  "properties": {
    "shipmentId": "9a8b7c6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d",
    "carrierName": "UPS",
    "deliveredAt": "2026-10-23T14:20:00.000Z",
    "promisedDate": "2026-10-24T18:00:00.000Z",
    "onTime": true,
    "delayDays": 0
  }
}
```

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `eventId` | string (UUIDv4) | ✅ | Identificador único del evento (idempotencia) |
| `timestamp` | string (ISO 8601 UTC) | ✅ | Momento en que ocurrió el evento, con milisegundos |
| `sessionId` | string (UUIDv4) | ✅* | Sesión aleatoria; UUID efímero para procesos sin sesión humana |
| `userId` | string | ✅ | Actor opaco/HMAC o URN de servicio; nunca email, nombre ni IP |
| `event_type` | string | ✅ | Tipo `entidad_accion` en snake_case, según registro formal |
| `schemaVersion` | string (`major.minor`) | ✅ | Versión del esquema del evento |
| `requestId` | string (UUIDv4) | ✅ | Correlación opaca del flujo |
| `properties` | object | ✅ | Payload cerrado al allowlist del evento, sin claves adicionales |

Los campos legacy `event_id`, `event_version`, `source`, `department`, `warehouse`, `trace_id`, `user_id`, `client_id`, `metadata` y `data` no pertenecen al envelope actual. Si se reciben durante una migración, se transforman mediante un adaptador explícito; no se mezclan con la forma normalizada ni se conserva `user_id` sin pseudonimización.

---

## 7. FLUJOS DE TELEMETRÍA POR PROCESO DE NEGOCIO

### 7.1 Flujo: Pedido → Despacho

```
Cliente envía pedido
  → order.received
  → inventory.adjusted (reserva de stock)
  → order.picking_started
  → order.picking_completed (mide M02)
  → shipment.created
  → shipment.carrier_assigned (mide M06)
  → shipment.in_transit
  → tracking.event_received (múltiples)
  → shipment.delivered (mide M01)
     ╰→ shipment.delivery_failed (si aplica)
```

### 7.2 Flujo: Devolución

```
Consumidor solicita devolución
  → return.requested
  → return.approved / return.rejected
  → return.pickup_scheduled
  → return.received_at_warehouse
  → return.inspected
  → return.reconditioned → inventory.received (reingreso)
  → return.discarded
```

### 7.3 Flujo: Consulta CX

```
Cliente envía consulta
  → ticket.created
  → ticket.classified
  → ticket.auto_resolved (mide M04)
     ╰→ ticket.escalated → ticket.resolved_by_agent
  → ticket.satisfaction_rated (mide M10)
```

---

## 8. IMPLEMENTACIÓN TÉCNICA

### 8.1 Stack Propuesto

| Componente | Tecnología | Propósito |
|---|---|---|
| **Transporte** | Apache Kafka / Redis Streams | Bus de eventos en tiempo real |
| **Almacenamiento** | PostgreSQL (event store) + ClickHouse (analíticas) | Persistencia y consultas analíticas |
| **Stream Processing** | Apache Flink / Kafka Streams | Agregaciones en tiempo real |
| **API** | FastAPI (servicio existente) | Endpoint de ingesta de eventos |
| **Dashboard** | Grafana + Metabase | Visualización de KPIs |

### 8.2 Backend de Eventos

```
POST /api/v1/telemetry/events  → Ingesta de evento individual
POST /api/v1/telemetry/events/batch  → Ingesta batch de eventos
GET  /api/v1/telemetry/metrics/{metric_id}  → Consulta de métrica agregada
GET  /api/v1/telemetry/events?type=...&from=...&to=...  → Consulta de eventos
```

### 8.3 Política de Retención

| Tipo de dato | Retención | Almacenamiento |
|---|---|---|
| Eventos crudos (últimos 7 días) | 7 días | ClickHouse (caliente) |
| Eventos crudos (histórico) | 1 año | ClickHouse (tibio) + S3 (frío) |
| Agregaciones por hora | 3 meses | PostgreSQL |
| Agregaciones por día | 2 años | PostgreSQL |
| Agregaciones por mes | Indefinido | PostgreSQL |

---

## 9. ALERTAS Y UMBRALES

| Alerta | Condición | Canal | Destinatario |
|---|---|---|---|
| Stock bajo | `stock ≤ stock_minimo` | Slack + Dashboard | Ana Whitfield (Almacén) |
| Rotura de stock | `stock = 0` | Slack + WhatsApp | Ana Whitfield (Almacén) |
| Entrega retrasada | `fecha_estimada < fecha_actual` | Slack | Carlos Vega (Última Milla) |
| Tasa error API >5% | `errores_5xx / total_requests > 0.05` | PagerDuty + Slack | Andrés Kim (Tecnología) |
| SLA de incidencias | `% resueltas dentro SLA < 95%` | Slack | Andrés Kim (Tecnología) |
| Freshness datos | Último evento hace >5 min | Slack | Thomas Harry (Dirección) |
| Resolución CX baja | `tasa_resolucion_automatica < 60%` | Slack mensual | Valentina Cruz (CX) |
| Scoring cliente bajo | `health_score < 5` | Slack | Miguel Torres (Comercial) |

---

## 10. GOBIERNO Y EVOLUCIÓN

- **Versionado de esquemas:** Cambios breaking requieren nueva versión (`event_version` / `schemaVersion`). Se mantienen dos versiones hacia atrás.
- **Registro de esquemas:** Todos los esquemas se definen en `event-schemas.json` (legacy) y se validan con JSON Schema.
- **Nuevo envelope estándar (Fase 2):** Consulte `event-envelope.md` para el diseño detallado del nuevo envelope con campos obligatorios (`eventId`, `timestamp`, `sessionId`, `userId`, `event_type`, `schemaVersion`, `requestId`, `properties`) y allowlists de propiedades por evento.
- **Propuesta de cambio:** Todo nuevo evento o modificación debe pasar por revisión del equipo de tecnología y documentarse en este plan.
- **Idempotencia:** Todos los eventos se identifican por `eventId` (UUID) en el nuevo formato, o `event_id` (UUID) en legacy. El sistema de ingesta debe rechazar duplicados.

---

## 11. APÉNDICE: MAPA DE EVENTOS → MÉTRICAS

```
M01 (Tasa entrega a tiempo) ← shipment.created, shipment.carrier_assigned, shipment.in_transit, shipment.delivered, shipment.delivery_failed, shipment.delayed, tracking.event_received
M02 (Tiempo picking)        ← order.received, order.picking_started, order.picking_completed, inventory.received, inventory.shipped
M03 (Tasa devoluciones)     ← return.requested, return.approved, return.rejected, return.pickup_scheduled, return.received_at_warehouse, return.inspected, return.reconditioned, return.discarded
M04 (Resolución CX)         ← ticket.created, ticket.classified, ticket.auto_resolved, ticket.escalated, ticket.resolved_by_agent
M05 (Frescura datos)        ← executive.weekly_report_generated, executive.alert_triggered, executive.kpi_breach
M06 (Coste/kg enviado)      ← shipment.created, shipment.carrier_assigned, carrier.performance_updated, shipment.delivery_failed
M07 (Tiempo deploy)         ← system.deployment_started, system.deployment_completed, system.deployment_failed
M08 (Incidencias SLA)       ← system.service_health_changed, system.error_rate_breach, system.latency_breach, system.resource_critical, frontend.api_request_completed, frontend.api_request_failed, frontend.slow_request_detected, frontend.api_connection_lost
M09 (Rotura stock)          ← inventory.stock_out, inventory.stock_low, inventory.stock_critical
M10 (Satisfacción B2B)      ← client.contract_created, client.contract_renewal_approaching, client.contract_renewed, client.contract_churned, client.health_score_updated, ticket.satisfaction_rated, report.monthly_generated, website.contact_form_submitted
```

---

## 12. FASE 3 — ESTRATEGIA DE ENTREGA

### 12.1 Alcance y criterio

Esta decisión cubre tanto los **24 eventos con esquema y allowlist explícitos** en `docs/telemetry/event-schemas.json` como **todos los eventos del catálogo conceptual de §5**. Las filas conceptuales son decisiones de entrega, no autorización para emitirlos en producción: cada evento debe incorporarse al registro con esquema y allowlist antes de implementarse.

- **Stream:** procesar el evento al llegar, con objetivo de disponibilidad para decisiones/alertas en menos de 1 minuto. Se elige cuando un retraso puede prolongar una interrupción, empeorar una excepción operativa, afectar una decisión en curso o impedir una respuesta de seguridad.
- **Batch/microbatch:** agrupar y procesar en ventanas (1 minuto para telemetría técnica agregable; cada hora o día para métricas de tendencia y reportes). Se elige cuando la decisión se toma sobre una tendencia o periodo consolidado y el procesamiento inmediato no cambia la respuesta operativa.
- El modo describe **cuándo se procesa**, no si se persiste el evento. Los eventos críticos se conservan individualmente; los eventos repetitivos de medición pueden agregarse antes de persistir, según las reglas de throttle. Los eventos de negocio necesarios para reconstruir el flujo no se muestrean.

### 12.2 Decisión por evento definido

**Hipótesis y criterio de inclusión para cada fila:** la justificación individual se interpreta como hipótesis operativa falsable: *si esta señal llega por el canal y ventana indicados, el rol nombrado podrá tomar la decisión descrita antes de que venza su oportunidad de actuar*. Para validarla, instrumentar temporalmente `event timestamp`, `ingestion timestamp` y un identificador opaco de la acción/resultado operativo; comparar latencia señal→acción con el SLA o la siguiente cadencia de decisión definida por el área. La hipótesis queda respaldada cuando el evento precede y permite la acción; si no existe una acción observable, la señal no cambia una decisión, o el retraso excede la ventana, retirar/replantear el evento o su modo. Esto aplica fila por fila a las dos tablas de esta sección; no es una afirmación de impacto ya medido. Stream tiene objetivo <1 min; batch se valida contra la cadencia declarada en su fila. Las filas que solo aportan analítica exploratoria deben demostrar uso en una decisión de producto/operación durante la revisión acordada o eliminarse.

| Evento | Entrega | Justificación basada en la decisión que alimenta |
|---|---|---|
| `shipment_delivered` | Stream | Permite actualizar inmediatamente la entrega a tiempo y resolver excepciones con el transportista antes de que la demora afecte al cliente. |
| `order_picking_completed` | Stream | Cierra el ciclo de picking; una demora frente al objetivo de 15 minutos requiere intervención del supervisor en el turno, no al día siguiente. |
| `return_completed` | Stream | La recepción física habilita inspección y decisión de reacondicionar/reintegrar inventario; retrasar el aviso retiene producto y alarga el ciclo de devolución. |
| `ticket_auto_resolved` | Stream | Confirma una resolución automatizada y permite detectar en el momento una caída del ratio de automatización o una resolución anómala para escalar casos. |
| `executive_report_generated` | Batch diario | El reporte consolida un periodo; Dirección decide sobre tendencias y frescura declarada en el propio evento, no sobre la llegada instantánea de cada ejecución. El envío del reporte puede notificarse aparte si falla. |
| `shipment_carrier_assigned` | Stream | La asignación es una decisión operativa en curso basada en urgencia, coste y destino; disponibilidad inmediata permite corregir asignaciones inviables antes de despachar. |
| `deployment_completed` | Stream | Tecnología necesita conocer al terminar el deploy si el health check pasó para revertir o investigar antes de que la degradación afecte más operaciones. |
| `incident_sla_breached` | Stream | El evento representa un SLA ya incumplido; notificar de inmediato permite escalar la incidencia y limitar el impacto. |
| `stock_depleted` | Stream | La rotura de stock puede bloquear pedidos nuevos; almacén debe reponer, reasignar o avisar a CX sin esperar al siguiente informe. |
| `client_health_score_updated` | Batch diario | Es un score derivado de señales agregadas; la gestión de cuenta actúa sobre tendencias y niveles de riesgo, no sobre cada variación intradía. Una evaluación diaria es suficiente para abrir seguimiento. |
| `login_succeeded` | Batch (5 minutos) | El acceso normal no requiere intervención inmediata; los conteos por aplicación/periodo sirven para capacidad y auditoría con menor volumen. No se usa esta ruta para bloquear accesos. |
| `login_failed` | Stream | Un pico de fallos puede indicar abuso o indisponibilidad de autenticación; seguridad/soporte debe poder investigarlo pronto. El control de acceso se aplica sin esperar al pipeline de telemetría. |
| `session_expired` | Batch (5 minutos) | Una expiración individual no suele requerir acción operativa; la distribución por motivo ayuda a encontrar problemas de TTL o UX sin generar alertas por cada sesión. |
| `api_latency_recorded` | Batch/microbatch (1 minuto) | Una medición por petición es de alta frecuencia; las decisiones de capacidad se basan en percentiles por endpoint/ventana. Se conservan excepciones de latencia alta y se agregan las normales. |
| `web_vital_recorded` | Batch/microbatch (1 minuto) | Las mediciones de rendimiento percibido se comparan por métrica y ruta estática en ventanas; una medición individual no requiere intervención operativa inmediata. El navegador reporta un valor final disponible por métrica y la ingesta actual no agrega ni persiste. |
| `api_rate_limited` | Stream | El cliente o el equipo de guardia debe detectar el rechazo pronto para ajustar consumo o investigar abuso. La agregación por cliente/endpoint evita alertar por cada rechazo repetido. |
| `deployment_duration_recorded` | Batch diario | Es una medición retrospectiva para la tendencia del tiempo de deploy (M07); no requiere acción mientras el deploy está activo. Los fallos se notifican por eventos de fallo separados. |
| `api_error_breached` | Stream | El umbral indica una degradación que requiere investigar/revertir ahora; procesarlo al cierre de un lote retrasaría la mitigación. |
| `data_validation_failed` | Batch/microbatch (1 minuto) | Un error aislado se responde al solicitante en la petición; Operaciones necesita ver patrones por endpoint/schema, no recibir una alerta por cada payload inválido. Se preservan contadores y muestras sanitizadas. |
| `integration_failed` | Stream | La caída de una integración externa puede detener tracking, devoluciones u otros flujos; el equipo debe iniciar retry/escalado antes de acumular trabajo pendiente. |
| `section_viewed` | Batch (15 minutos) | La navegación alimenta análisis de uso y no una decisión transaccional; consolidar vistas por sección reduce volumen sin retrasar una respuesta operativa. |
| `feature_used` | Batch (15 minutos) | La adopción de funcionalidades es una métrica de producto/operación agregada; no requiere reaccionar a cada clic individual. |
| `direct_stock_edit_rejected` | Stream | La edición directa rechazada protege la integridad del inventario; el evento oportuno permite detectar intentos repetidos y orientar al operario al flujo de movimientos autorizado. |

### 12.2.1 Eventos conceptuales del catálogo §5

La decisión es por evento; **stream** significa que una señal accionable llega a Operaciones/soporte con rapidez, mientras que los datos para tendencia se consolidan en la ventana indicada. Cuando un evento se origina en una ejecución periódica, se procesa en stream si detecta un estado que requiere actuación, pero el cálculo que lo genera conserva su periodicidad descrita en §5.

| Evento del catálogo §5 | Entrega | Justificación basada en la decisión que alimenta |
|---|---|---|
| `inventory.received` | Stream | La disponibilidad física de stock permite liberar pedidos retenidos y resolver discrepancias durante el turno. |
| `inventory.shipped` | Stream | La salida confirmada actualiza el stock operativo que se consulta para aceptar y preparar nuevos pedidos. |
| `inventory.adjusted` | Stream | Un ajuste cambia el saldo de referencia y debe ser visible enseguida para evitar decisiones de picking sobre stock desactualizado. |
| `inventory.stock_low` | Stream | Almacén necesita tiempo para reponer o priorizar compras antes de llegar a una rotura que bloquee pedidos. |
| `inventory.stock_critical` | Stream | La proximidad a rotura exige priorizar reposición o reasignación antes de que el stock llegue a cero. |
| `inventory.stock_out` | Stream | El agotamiento bloquea salidas y requiere respuesta inmediata de Almacén/CX para gestionar pedidos afectados. |
| `order.received` | Stream | La recepción inicia el compromiso operativo y debe entrar en la cola de preparación sin esperar una consolidación. |
| `order.picking_started` | Stream | El inicio marca el reloj del KPI de picking y permite al supervisor detectar pedidos en curso que superan el objetivo. |
| `order.picking_completed` | Stream | El cierre del picking actualiza la cola de despacho y permite intervenir en el mismo turno ante tiempos excesivos. |
| `shipment.created` | Stream | El paquete listo requiere asignación de transportista y despacho; retrasarlo afecta la fecha prometida. |
| `shipment.carrier_assigned` | Stream | La decisión aún puede corregirse antes de entregar el paquete al transportista si la opción no satisface urgencia/coste/destino. |
| `shipment.in_transit` | Stream | La confirmación permite detectar envíos que no fueron recogidos y mantener al cliente informado durante el ciclo activo. |
| `shipment.delivered` | Stream | Actualiza M01 y permite cerrar consultas o excepciones de entrega mientras el caso aún es reciente. |
| `shipment.delivery_failed` | Stream | Un intento fallido requiere coordinar reintento y comunicación al cliente antes de que se acumule el retraso. |
| `shipment.delayed` | Stream | La desviación frente a la promesa permite a coordinadores contactar al transportista y prevenir una incidencia prolongada. |
| `tracking.event_received` | Stream | Los cambios de estado alimentan el seguimiento y la detección de demoras durante el transporte; se deduplican sin cambio de estado. |
| `carrier.performance_updated` | Batch diario | Es un recálculo de tendencia para comparar coste y rendimiento; no cambia una asignación ya en curso con cada actualización. |
| `return.requested` | Stream | La solicitud inicia plazos y autorización de recogida; una demora pospone el reembolso y la resolución al consumidor. |
| `return.approved` | Stream | La decisión habilita recogida y logística inversa; debe comunicarse al consumidor y al flujo operativo en el momento. |
| `return.rejected` | Stream | El rechazo requiere comunicar la resolución y motivo al consumidor sin demora. |
| `return.pickup_scheduled` | Stream | La fecha de recogida debe estar disponible para el consumidor y para coordinar al transportista. |
| `return.received_at_warehouse` | Stream | El escaneo habilita inspección y evita que el producto quede sin procesar en el almacén. |
| `return.inspected` | Stream | El dictamen determina reacondicionamiento o descarte y debe liberar la siguiente acción física enseguida. |
| `return.reconditioned` | Stream | El reingreso modifica inventario disponible para pedidos; retrasar el evento mantiene stock utilizable oculto. |
| `return.discarded` | Stream | La baja evita que producto no recuperable vuelva a ofrecerse como disponible y cierra su tratamiento operativo. |
| `ticket.created` | Stream | La consulta debe entrar en la cola de atención dentro del SLA, especialmente fuera de horario con automatización. |
| `ticket.classified` | Stream | La categoría y prioridad encaminan el ticket al flujo o agente que puede resolverlo. |
| `ticket.auto_resolved` | Stream | Confirma la resolución de CX y permite detectar en el turno una caída o anomalía de la automatización. |
| `ticket.escalated` | Stream | Un caso que la IA no resolvió requiere asignación humana sin demora para cumplir el SLA de respuesta. |
| `ticket.resolved_by_agent` | Stream | Cierra el ciclo de SLA y libera la cola del agente; la resolución debe reflejarse en el estado operativo. |
| `ticket.satisfaction_rated` | Batch diario | Una valoración individual no exige intervención inmediata; la gestión de CX analiza tendencias y alertas consolidadas. |
| `client.contract_created` | Batch diario | El alta contractual es estable y se incorpora a reporting/comercial; no requiere respuesta minuto a minuto del pipeline analítico. |
| `client.contract_renewal_approaching` | Batch diario | La regla de 90/30 días es programada y el equipo comercial organiza seguimiento en una cadencia diaria. |
| `client.contract_renewed` | Batch diario | La renovación se registra en CRM/reporting y no cambia una operación física activa. |
| `client.contract_churned` | Stream | La pérdida confirmada requiere actualizar previsiones y asignar seguimiento ejecutivo/comercial cuanto antes. |
| `client.health_score_updated` | Batch diario | El score resume señales agregadas; el account manager actúa sobre tendencia y umbral, no sobre cada oscilación intradía. |
| `report.monthly_generated` | Batch diario | La generación es programada y su consumo es periódico; solo un fallo de generación necesita una señal operativa inmediata. |
| `system.service_health_changed` | Stream | Un cambio a estado degradado/interrumpido necesita alertar a guardia para reducir el tiempo de caída detectada hoy por canales manuales. |
| `system.deployment_started` | Stream | Permite correlacionar degradaciones con un cambio activo y preparar rollback si la salud empeora. |
| `system.deployment_completed` | Stream | El equipo verifica el resultado y la salud antes de que la versión degradada afecte a más operaciones. |
| `system.deployment_failed` | Stream | El fallo requiere diagnóstico/rollback inmediato para no prolongar una entrega incompleta. |
| `system.error_rate_breach` | Stream | Una tasa de error sobre umbral exige mitigación durante la incidencia, no al siguiente informe. |
| `system.latency_breach` | Stream | La latencia degradada afecta consultas y operaciones activas; Tecnología debe investigar antes de acumular esperas. |
| `system.resource_critical` | Stream | CPU, memoria o disco críticos pueden provocar caída; la intervención temprana reduce indisponibilidad. |
| `executive.weekly_report_generated` | Batch semanal (lunes 07:00) | El informe consolida la semana y su destinatario lo revisa en la cadencia ya definida; frescura individual se mantiene vía dashboard. |
| `executive.alert_triggered` | Stream | Una alerta de KPI crítico representa una desviación que requiere que Dirección/área actúe antes del siguiente ciclo de reporte. |
| `executive.kpi_breach` | Stream | El umbral incumplido debe escalarse para decidir mitigación, en vez de esperar al informe periódico. |
| `frontend_error_recorded` (categorías `api_http_error`, `api_validation_error`, `slow_api_request`, `api_connection_lost`, `uncaught_exception`, `unhandled_rejection`, `api_network_error`) | Stream para error/caída/lentitud; deduplicar alertas y agregar tendencia por minuto | Un fallo observado puede bloquear una tarea; la señal formal usa categoría controlada y omite mensaje/stack. No representa las rutas conceptuales de autenticación ni el evento `api_error_breached` agregado. |
| `api_latency_recorded` | Batch/microbatch (1 minuto) para percentiles; emisión individual provisional en el capturador actual | Capacidad y latencias se evalúan por endpoint y percentiles. El cliente actual mide respuestas HTTP del backoffice; fallos de red no tienen status HTTP y no producen este evento. Esta telemetría no calcula M08. |
| `frontend.toast_displayed` | Batch (15 minutos) | Un toast individual es feedback local; la frecuencia y tipo agregados revelan fricción sin alertar por cada mensaje. |
| `frontend.view_changed` | Batch (15 minutos) | La navegación se usa para adopción y análisis UX; no alimenta una decisión transaccional urgente. |
| `frontend.feature_used` | Batch (15 minutos) | La adopción se revisa agregada; una acción de negocio confirmada sigue registrada en su evento transaccional de dominio. |
| `frontend.flow_abandoned` | Batch (15 minutos) | La tasa de abandono guía mejoras de UX por patrón; cada abandono aislado no requiere intervención inmediata. |
| `frontend.article_search_performed` | Batch (15 minutos) | Las búsquedas solo informan sobre descubribilidad de catálogo; guardar términos o esperar cada pulsación no es necesario para operar. |
| `frontend.nav_item_disabled_clicked` | Batch (15 minutos) | La interacción revela demanda por capacidades no disponibles y sirve para priorización de producto, no para una decisión en curso. |
| `frontend.movement_form_opened` | Batch (15 minutos) | La apertura mide intención/adopción; el movimiento confirmado se conserva por su evento transaccional y no depende de esta señal. |
| `frontend.movement_registration_cancelled` | Batch (15 minutos) | Las cancelaciones se investigan como patrón UX; una cancelación no confirmada no requiere escalado inmediato. |
| `frontend.article_deactivation_confirmed` | Stream | La baja altera disponibilidad del catálogo que usan operarios; los consumidores deben enterarse antes de nuevas operaciones. |
| `website.contact_form_submitted` | Stream | Es un lead entrante que Comercial debe atender con prontitud para no perder oportunidad de seguimiento. |
| `website.section_viewed` | Batch (15 minutos) | La navegación pública es analítica de interés y no cambia una decisión logística ni de soporte. |
| `website.navigation_clicked` | Batch (15 minutos) | Los clics agregados permiten evaluar contenido y navegación; no hay acción operativa que requiera procesar cada clic al instante. |

La implementación actual del backoffice emite `api_latency_recorded` en cada respuesta HTTP, `frontend_error_recorded` para fallos/lentitud/errores JS y `web_vital_recorded` para métricas disponibles. La agregación/microbatch descrita en este plan es el destino del pipeline, no una capacidad del stub de ingesta ni una promesa de persistencia. Los eventos se envían desde el cliente; la deduplicación de alertas y las tendencias agregadas corresponden al consumidor posterior. Las mediciones Web Vitals solo están disponibles cuando la API del navegador expone las entradas correspondientes y se reportan al ocultarse/cambiar de página.

### 12.4 Límite de instrumentación del backoffice disponible

El backoffice actual implementa navegación, gestión de artículos/lotes y registro de movimientos de inventario. Emite `section_viewed`, `feature_used`, `api_latency_recorded`, `frontend_error_recorded` y `web_vital_recorded` únicamente a partir de acciones, APIs y entradas de rendimiento observadas. Los hooks de auth están preparados pero no se emiten sin integración con un proveedor de autenticación real. No dispone de flujos ni fuentes autoritativas para completar los payloads de `shipment_delivered` (M01), `order_picking_completed` (M02), `return_completed` (M03), `ticket_auto_resolved` (M04), `executive_report_generated` (M05), `shipment_carrier_assigned` (M06), `deployment_completed` (M07), `incident_sla_breached` (M08), `stock_depleted` (M09) o `client_health_score_updated` (M10). En particular, stock bajo/reorden no equivale a stock agotado; no se debe inferir una rotura desde la UI ni inventar IDs de negocio. Cada KPI requiere instrumentación en el servicio transaccional/monitor correspondiente y resolver las limitaciones de cobertura de §2.1 antes de publicarse.

### 12.3 Throttle, debounce y control de volumen

Las reglas se aplican sin retrasar ni descartar el primer hecho accionable. Claves de agregación deben usar IDs seudónimos/de entidad, nunca email, IP o payload libre.

| Fuente/evento | Regla | Protección de la señal |
|---|---|---|
| `api_latency_recorded` (por request) | El emisor actual captura una medición individual por respuesta HTTP; el pipeline destino agrega ventanas de 1 minuto por `serviceName` + ruta normalizada + método + clase de estado y calcula conteos/percentiles. | El endpoint actual es un stub sin persistencia ni agregación. Fallos de red sin status HTTP se reportan como `frontend_error_recorded`, no como latencia con status inventado. |
| `data_validation_failed` | Agrupar durante 1 minuto por endpoint + código/categoría de validación + versión de esquema. Mantener contador exacto y hasta 5 ejemplos estructurales sanitizados por grupo; no almacenar valores rechazados. | Un error crítico de contrato puede emitir alerta inmediata por regla de severidad; no agrupar el rechazo que recibe el cliente. |
| `api_rate_limited` | Stream con deduplicación de alertas de 1 minuto por cliente seudónimo + endpoint; conservar contador y primer/último timestamp de la ventana. | Registrar cada rechazo en contadores, pero alertar solo una vez por ventana; no afectar la respuesta 429. |
| `login_failed` | Stream; alerta agrupada por cuenta seudónima + aplicación en ventana móvil de 5 minutos. No enviar notificación individual por cada intento. | Conservar conteo y primera/última ocurrencia; no usar IP sin evaluación de seguridad/retención. El bloqueo de autenticación es independiente. |
| `section_viewed` | En navegador, debounce de 1 segundo al entrar en viewport y emitir solo tras ≥1 segundo visible; como máximo una vista por sección y sesión cada 30 segundos. | Cambios reales de sección no se retrasan en la interfaz; una vista posterior tras salir y regresar cuenta de nuevo. |
| `feature_used` | No debounce de acciones confirmadas. Deduplicar el mismo `eventId`; descartar doble click técnico del mismo control dentro de 500 ms si no produjo dos operaciones. | Si hubo dos operaciones de negocio exitosas, conservar ambos eventos. |
| `api_latency_recorded` | El navegador emite por cada respuesta HTTP; el procesamiento futuro debe agregar por minuto y conservar denominadores exactos. | No registrar latencia sin respuesta/status; la métrica de error de negocio/SLA no se deriva automáticamente de latencia frontend. |
| `frontend_error_recorded` | Capturar el hecho por ocurrencia; deduplicar solo notificaciones/alertas por categoría y endpoint normalizado en ventana de 1 minuto, manteniendo contadores en el consumidor. | Un tipo nuevo, recuperación seguida de caída o cambio de severidad vuelve a alertar; no se adjuntan mensajes, stacks ni URL completa. |
| `web_vital_recorded` | Una medición por nombre de métrica y carga de página; acumular CLS, conservar el LCP más reciente y derivar INP de interacciones observadas. Emitir métricas finales al ocultar/salir de la página. | Solo emitir métrica, valor, rating, tipo de navegación y ruta allowlisted (`/`, `/inventory`, `/company`, `/other`); nunca URL completa, query o hash. Las APIs no soportadas se omiten. |
| `frontend.article_search_performed` | Debounce de 300 ms tras la última pulsación; emitir como máximo una búsqueda por consulta estabilizada, con límite de una por sesión/consulta normalizada cada 2 s. | No capturar ni persistir el texto/consulta; registrar solo conteo, longitud en bandas o categoría permitida. La búsqueda de UI no se retrasa por la telemetría. |
| Health checks (`system.service_health_changed`, `frontend.api_connection_lost`) | Evaluar checks con intervalo operativo configurado, pero emitir solo transición de estado y resumen de disponibilidad por minuto; no emitir cada heartbeat sano. | Abrir alerta en caída confirmada; notificar recuperación como nueva transición. Los checks de servicio no se eliminan del monitor fuente. |
| `frontend.domain_load_time`, `frontend.toast_displayed`, `frontend.view_changed`, `frontend.movement_form_opened`, `frontend.movement_registration_cancelled`, `frontend.nav_item_disabled_clicked` | Batch de 15 minutos por tipo de evento, vista/categoría y aplicación; límite de una repetición idéntica por sesión cada 5 s. | Mantener conteos por sesión para medir adopción; no registrar contenido del toast ni texto libre. |
| `website.section_viewed` | Aplicar el mismo debounce/visibilidad mínima de 1 s que `section_viewed`; una vista por sección y sesión cada 30 s. | No bloquear renderizado o navegación; evitar contar scroll oscilante como vistas repetidas. |
| `website.navigation_clicked` | Agrupar en batch de 15 minutos por sección y destino categorizado; máximo una repetición por enlace/sesión cada 2 s. | No almacenar URL con parámetros ni identificadores; navegación y formulario siguen funcionando sin esperar la telemetría. |
| `executive.alert_triggered`, `executive.kpi_breach`, `system.*_breach`, `system.resource_critical` | Suprimir alertas repetidas del mismo KPI/servicio/recurso mientras el incidente permanezca abierto; emitir resumen cada 5 minutos. | Conservar inicio, cambios de severidad, recuperación y contadores. Un nuevo incidente tras recuperación vuelve a alertar. |
| `stock_depleted` | Emitir por transición de stock positivo a cero (edge-triggered), como máximo una vez por SKU + almacén + cliente hasta que el stock se recupere por encima de cero. | Reemitir al volver a cero tras recuperación; los movimientos de inventario siguen siendo la fuente de auditoría. |
| `integration_failed` / `api_error_breached` | Conservar el evento de inicio y los cambios de estado; suprimir alertas repetidas mientras siga abierto, con resumen cada 5 minutos. | Emitir de nuevo en recuperación y en una nueva caída; conservar contadores y duración del incidente. |
| Tracking repetido (`tracking.event_received`, catálogo §5) | Deduplicar por transportista + ID de evento del transportista; agrupar polling sin cambios de estado. Límite de alerta por envío/estado cada 5 minutos. | No suprimir transiciones de tracking ni entrega/fallo; preservar timestamp de origen y recepción. |

Para evitar alertas en cascada, cada regla tendrá un límite de notificaciones, pero no un límite que descarte eventos transaccionales. `eventId` garantiza idempotencia; la ventana de throttle no sustituye esa deduplicación.

### 12.4 Riesgos, eventos descartados y datos excluidos

| Riesgo / exclusión | Decisión y motivo | Mitigación / señal conservada |
|---|---|---|
| Ráfagas de tracking, latencia y errores | El polling de transportistas y las mediciones por request pueden multiplicar el volumen y el costo de almacenamiento/procesamiento. | Deduplicar estados sin cambio, microbatch de métricas y conservar todas las transiciones relevantes, errores y breaches. Medir volumen y costo por fuente. |
| Retardo o pérdida de conectividad | Una entrega en stream puede quedar temporalmente offline, especialmente navegador/transportista. | Reintentos con backoff, cola local acotada y persistente para emisores backend, `eventId` idempotente, timestamp de ocurrencia y métrica de lag. Expirar con DLQ y revisión; no ocultar eventos perdidos. |
| Relojes desincronizados y eventos fuera de orden | Sistemas y carriers pueden reportar timestamps tardíos o incorrectos. | Mantener hora del evento y hora de ingesta, validar skew, ordenar por entidad cuando sea posible y permitir corrección/replay controlado. |
| Reintentos duplicados | Reintentos de red pueden inflar KPIs y alertas. | Idempotencia por `eventId` y deduplicación de clave externa para tracking; reportar duplicados rechazados. |
| Métricas de score (cliente/CX) | Un score puede ocultar cambios internos o disparar acciones por ruido. | Batch diario, registrar versión/frescura y umbrales; no tomar decisiones contractuales automáticas solo con telemetría. |
| **Descartado: pulsaciones/teclas, texto de formularios y consultas de búsqueda** | No se necesitan para KPIs; revelarían credenciales, datos de pedidos o información comercial y elevarían costo/retención. | Capturar solo resultado/categoría y duración cuando sean necesarios; nunca guardar contenido escrito. |
| **Descartado: grabación de sesión, capturas de pantalla y DOM completo** | Costo elevado y captura incidental de datos personales, credenciales o datos de clientes; no justificado por decisiones actuales. | Eventos discretos `section_viewed`/`feature_used` con allowlist. |
| **Excluido: contraseñas, tokens, cookies, cabeceras de autorización, cuerpos HTTP y datos de tarjeta** | Secretos y datos financieros sensibles no son necesarios para analítica y no deben entrar en telemetría. | Redacción en el emisor y en la ingesta; rechazar claves fuera del allowlist. La redacción es defensa adicional, no sustituto de no capturarlos. |
| **Excluido o transformado: email/nombre de operario, email intentado, IP, dirección exacta, firma de entrega y texto libre de incidencias/tickets** | PII directa o identificadores de alto riesgo. La identificación personal no es necesaria para métricas agregadas y aumenta exposición, costo de controles y obligaciones de privacidad. | Usar solo ID opaco/HMAC del actor cuando haga falta; nunca email/nombre/IP en envelope o propiedades. No persistir firma/dirección/texto; excluir también las claves no aprobadas de los allowlists antes de producción. |
| `trackingNumber`, `clientName` y nombres de SKU | Pueden identificar indirectamente a personas, marcas o actividad comercial; no son necesarios en dashboards agregados. | Excluir los valores directos y la clave `trackingNumber` de telemetría persistida. Para clientes/SKU, usar IDs internos opacos seudónimos con acceso controlado solo si el join es necesario; eliminar nombres de ejemplos y feeds/dashboards. |
| **Descartado: cada heartbeat de health check y cada snapshot periódico de stock sin cambio** | Generan alto volumen sin alimentar una decisión nueva; el estado actual y los cambios son suficientes para alertar y calcular roturas. | Emitir transiciones, breaches, deltas y snapshots agregados con periodicidad definida; conservar el historial de movimientos como auditoría. |
| PII descrita en esquemas existentes (`operatorId`, `attemptedEmail`, `ipAddress`) | Los campos aparecen como claves compatibles en esquemas heredados y no deben interpretarse como autorización para persistir sus valores directos. | Emitir el actor solo como ID opaco/HMAC; omitir email e IP del envelope y de las propiedades de evento. Las señales antiabuso se basan en motivos/contadores agregados; cualquier investigación que requiera identificadores queda fuera de telemetría y necesita aprobación, acceso y retención propios. Rechazar eventos que contengan esos campos. |
| Esquemas de eventos desactualizados con datos indirectos o libres | Allowlist de `trackingNumber`, nombres de cliente/SKU o títulos/responsables libres puede revelar datos comerciales o PII aunque no incluya email/IP. | Eliminar `trackingNumber`, nombres comerciales y campos de texto/persona de las allowlists productivas; conservar solo IDs opacos y categorías controladas. `additionalProperties: false` no basta si las claves sensibles siguen explícitamente permitidas. |
| Pérdida de representatividad al agregar/muestrear | Puede sesgar percentiles, adopción o tasas si se pierden denominadores. | Versionar las reglas, incluir conteos de población y muestreo, retener íntegros eventos de negocio y comparar agregados con métricas de origen en revisiones periódicas. |

La telemetría no sustituye auditorías transaccionales, trazas de seguridad ni el soporte al cliente. Ningún dato excluido se debe incorporar en `properties` por conveniencia: cualquier excepción exige necesidad documentada, evaluación de privacidad/seguridad, retención y acceso aprobados, y actualización del esquema/allowlist antes de emitirlo.