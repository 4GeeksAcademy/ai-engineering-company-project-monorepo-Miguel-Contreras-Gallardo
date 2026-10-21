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

Estos eventos se emiten desde el navegador del operario y cubren autenticación, rendimiento percibido, errores de frontend, navegación e interacciones del backoffice. Su objetivo es medir la experiencia real del operario y detectar problemas de usabilidad y rendimiento antes de que impacten en la operación.

| ID | Evento | Descripción | Disparador | Tipo |
|---|---|---|---|---|
| F01 | `frontend.auth.login_attempted` | Intento de inicio de sesión | Usuario introduce credenciales y pulsa "Entrar" | Oportunidad |
| F02 | `frontend.auth.login_succeeded` | Inicio de sesión exitoso | Autenticación verificada correctamente | Oportunidad |
| F03 | `frontend.auth.login_failed` | Fallo de autenticación | Credenciales incorrectas o usuario no encontrado | Oportunidad |
| F04 | `frontend.auth.session_expired` | Sesión expirada | Token/sesión supera TTL sin actividad | Oportunidad |
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
  "event_id": "uuid",
  "event_type": "inventory.received",
  "event_version": "1.0",
  "source": "warehouse-service",
  "timestamp": "2026-10-21T14:30:00Z",
  "department": "almacen",
  "warehouse": "LA",
  "trace_id": "uuid-de-correlacion",
  "user_id": "ana.whitfield@trackflow.com",
  "client_id": "uuid-cliente",
  "metadata": { },
  "data": { }
}
```

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `event_id` | string (UUID) | ✅ | Identificador único del evento (idempotencia) |
| `event_type` | string | ✅ | Tipo de evento con namespacing (`dominio.accion`) |
| `event_version` | string | ✅ | Versión del esquema del evento |
| `source` | string | ✅ | Nombre del servicio o componente que emite el evento |
| `timestamp` | string (ISO 8601) | ✅ | Momento en que ocurrió el evento |
| `department` | string | ✅ | Departamento responsable (almacen, ultima_milla, logistica_inversa, cx, comercial, tecnologia, direccion) |
| `warehouse` | string | O | Almacén asociado (LA / Zaragoza) si aplica |
| `trace_id` | string (UUID) | ✅ | ID de correlación para trazar flujos multi-evento |
| `user_id` | string | O | Identificador del usuario/operario que originó el evento |
| `client_id` | string | O | Identificador del cliente (marca) asociado |
| `metadata` | object | O | Metadatos adicionales libre (tags, entorno, versión) |
| `data` | object | ✅ | Payload específico del tipo de evento |

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

- **Versionado de esquemas:** Cambios breaking requieren nueva versión (`event_version`). Se mantienen dos versiones hacia atrás.
- **Registro de esquemas:** Todos los esquemas se definen en `event-schemas.json` y se validan con JSON Schema.
- **Propuesta de cambio:** Todo nuevo evento o modificación debe pasar por revisión del equipo de tecnología y documentarse en este plan.
- **Idempotencia:** Todos los eventos se identifican por `event_id` (UUID). El sistema de ingesta debe rechazar duplicados.

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