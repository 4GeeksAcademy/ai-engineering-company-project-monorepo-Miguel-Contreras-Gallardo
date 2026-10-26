# 📨 Event Envelope — Diseño estándar Fase 2

> **Versión:** 1.0  
> **Fecha:** 2026-10-22  
> **Proyecto:** TrackFlow — Plataforma de Automatización e IA  
> **Ubicación:** `docs/telemetry/event-envelope.md`  
> **Fase:** 2 — Diseño del Event Envelope

---

## 1. Estándar del Event Envelope

Todo evento de telemetría en TrackFlow **debe** cumplir con la siguiente envoltura estándar. Los campos marcados como obligatorios son responsabilidad del emisor; si faltan, el evento será rechazado en la ingesta.

### 1.1 Campos obligatorios del envelope

| # | Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| 1 | `eventId` | `string` (UUIDv4) | ✅ | Identificador único del evento. Garantiza idempotencia en toda la plataforma. |
| 2 | `timestamp` | `string` (ISO 8601) | ✅ | Momento exacto (UTC) en que ocurrió el evento, con resolución de milisegundos. Formato: `2026-10-22T14:30:00.000Z` |
| 3 | `sessionId` | `string` (UUIDv4) | ✅* | Identificador aleatorio de sesión, sin identidad codificada. Obligatorio cuando existe sesión; para procesos sin sesión humana, usar un UUIDv4 efímero de ejecución y evitar reutilizarlo entre flujos. |
| 4 | `userId` | `string` | ✅ | Identificador seudónimo del actor que originó el evento (operario, sistema, cliente). Usar un ID interno opaco o un HMAC con clave protegida y rotación; no usar email, nombre, IP ni otro identificador directo. Para procesos automáticos, usar un ID de servicio no personal, por ejemplo `urn:service:inventory-monitor`. |
| 5 | `event_type` | `string` | ✅ | Tipo de evento según la taxonomía `entidad_accion`. Ver convención en §2. |
| 6 | `schemaVersion` | `string` (semver) | ✅ | Versión del esquema del evento (solo major.minor). Ej: `1.0`, `2.1`. Cambios breaking incrementan major. |
| 7 | `requestId` | `string` (UUIDv4) | ✅ | ID de correlación opaco que agrupa eventos del mismo flujo; no incluir identificadores personales o datos de negocio en su contenido. |
| 8 | `properties` | `object` | ✅ | Payload específico del tipo de evento. Solo puede contener las claves definidas en su **allowlist** (§5). Cualquier clave no listada será rechazada. |

### 1.2 Ejemplo completo

```json
{
  "eventId": "a1b2c3d4-e5f6-4a7b-9c0d-1e2f3a4b5c6d",
  "timestamp": "2026-10-22T10:00:00.000Z",
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

### 1.3 Reglas de validación

1. **Idempotencia:** Si se recibe un `eventId` ya registrado, se ignora (no es error). El emisor puede reintentar sin riesgo.
2. **Timestamp:** No se aceptan eventos con `timestamp` futuro (> 5 min de skew) ni con más de 24 h de antigüedad.
3. **Allowlist estricto:** El validador inspecciona `properties` y rechaza cualquier clave no listada en el allowlist del `event_type`. Esto previene fugas accidentales de datos (PII, credenciales, información interna). El allowlist no autoriza por sí mismo persistir PII: aplican las exclusiones de §12.4 de `telemetry-plan.md`; valores de operario solo como ID opaco/HMAC, nunca email o IP.
4. **Campos obligatorios:** Si falta cualquiera de los 8 campos del envelope, el evento se rechaza con `422 Unprocessable Entity`.
5. **IDs de sesión:** Si no existe una sesión de usuario, el emisor genera un UUIDv4 aleatorio y efímero; no reutilizar valores descriptivos ni colocar emails, nombres, IDs de pedido o información equivalente en `sessionId`/`requestId`.
6. **Datos de propiedades:** Las exclusiones de privacidad de §12.4 de `telemetry-plan.md` prevalecen sobre cualquier allowlist antigua. Por ejemplo, `operatorId` solo admite un ID opaco/HMAC y claves de email/IP, firmas, texto libre, direcciones exactas y nombres de clientes/SKU no se deben emitir en telemetría persistida.

> **Alcance de instrumentación:** solo los `event_type` registrados en `event-schemas.json` tienen esquema formal y pueden emitirse. Esta formalidad no significa que todas las fuentes estén conectadas: el backoffice implementado emite los eventos enumerados en su README, incluyendo `web_vital_recorded` con rutas allowlisted; los hooks `login_failed` y `session_expired` solo producirán eventos al conectarse a un proveedor de autenticación real. Las métricas de negocio requieren su productor transaccional autoritativo. `stock_received` se conserva aquí como ejemplo conceptual, no instrumentable; antes de producción debe añadirse al registro maestro con su esquema y allowlist. La misma regla aplica a todos los eventos conceptuales de §5 del plan.

---

## 2. Convención de nombrado: `entidad_accion`

Cada `event_type` sigue la taxonomía `entidad_accion` con **verbos en pasado** (inglés) para mantener consistencia entre equipos.

### 2.1 Verbos admitidos

| Verbo | Significado | Ejemplo |
|---|---|---|
| `_created` | Entidad nueva creada en el sistema | `inbound_order_created` |
| `_received` | Recepción física o digital de una entidad | `stock_received` |
| `_completed` | Proceso finalizado correctamente | `order_picking_completed` |
| `_failed` | Intento de proceso que terminó en error | `login_failed` |
| `_triggered` | Alerta o umbral que se dispara | `stock_low_triggered` |
| `_rejected` | Acción solicitada pero denegada | `direct_stock_edit_rejected` |
| `_expired` | Recurso temporal que ha caducado | `session_expired` |
| `_recorded` | Medición o métrica registrada | `api_latency_recorded` |
| `_updated` | Actualización de estado o valor | `client_health_score_updated` |
| `_depleted` | Recurso agotado (stock = 0) | `stock_depleted` |
| `_breached` | Umbral de seguridad/rendimiento excedido | `incident_sla_breached` |
| `_assigned` | Asignación de recurso o responsable | `shipment_carrier_assigned` |
| `_viewed` | Visualización de sección o recurso | `section_viewed` |
| `_used` | Funcionalidad utilizada por el usuario | `feature_used` |
| `_limited` | Recurso restringido por límite de uso | `api_rate_limited` |

### 2.2 Reglas

- **Siempre minúsculas** y separador `_` (guion bajo)
- **Sin espacios, sin puntos, sin guiones**
- La entidad puede ser compuesta: `inbound_order`, `stock_threshold`, `direct_stock_edit`
- El verbo siempre en pasado y al final: `{entidad}_{verbo_en_pasado}`

---

## 3. Catálogo de eventos

El catálogo se organiza en dos grupos:

- **Eventos obligatorios (§4):** derivados directamente del BRIEFING (`CONTEXT.md`) y asociados a las métricas M01–M10.
- **Eventos adicionales (§5):** extraídos del catálogo de telemetría, cubriendo al menos 3 categorías distintas (autenticación, rendimiento, errores, navegación).

Cada evento incluye:
- `event_type` — según taxonomía `entidad_accion`
- `description` — qué representa
- `category` — agrupación funcional
- `metrics` — IDs de métricas obligatorias que alimenta
- `allowlist` — **lista explícita de claves permitidas** en `properties`
- `example` — evento completo de ejemplo

---

## 4. Eventos obligatorios (M01–M10)

> Todos los ejemplos representan identificadores de negocio con IDs opacos/UUID de prueba. No incluir valores reales ni datos personales en `userId`, `sessionId` o `requestId`; los campos excluidos por §12.4 del plan no se pueden reintroducir por medio de una allowlist.

### 4.1 M01 — `shipment_delivered`

Entrega exitosa de un envío al consumidor final. Es el evento clave para calcular la tasa de entrega a tiempo.

- **Category:** `ultima_milla`
- **Metrics:** M01

**Properties:**

| Campo | Tipo | Req. | Descripción | PII | Sanitización |
|---|---|---|---|---|---|
| `shipmentId` | `string` (UUIDv4) | ✅ | ID único del envío en TrackFlow | 🟢 No | — |
| `carrierName` | `string` | ✅ | Nombre del transportista (UPS, FedEx, MRW…) | 🟢 No | — |
| `deliveredAt` | `string` (ISO 8601) | ✅ | Momento exacto de la entrega | 🟢 No | — |
| `promisedDate` | `string` (ISO 8601) | ❌ | Fecha prometida al consumidor (para calcular onTime) | 🟢 No | — |
| `deliverySignature` | `string` | ❌ | Firma/nombre de la persona que recibió el paquete | 🔴 Directa | **Excluir del envelope y de telemetría.** Si hace falta comprobar la entrega, emitir solo `signaturePresent: boolean` tras validación en el sistema fuente. |
| `onTime` | `boolean` | ✅ | `true` si se entregó antes o en la fecha prometida | 🟢 No | — |
| `delayDays` | `integer` | ❌ | Días de retraso respecto a la fecha prometida (0 si onTime) | 🟢 No | — |

> **Allowlist:** `shipmentId`, `carrierName`, `deliveredAt`, `promisedDate`, `onTime`, `delayDays`

**Ejemplo:**

```json
{
  "eventId": "b5c6d7e8-9f0a-1b2c-3d4e-5f6a7b8c9d0e",
  "timestamp": "2026-10-23T14:20:00.000Z",
  "sessionId": "2f9af977-37d8-517b-92ad-be0a1ea93b4a",
  "userId": "urn:service:telemetry-emitter",
  "event_type": "shipment_delivered",
  "schemaVersion": "1.0",
  "requestId": "f321b2ef-75e1-5e4d-b131-b129e58ebdce",
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

---

### 4.2 M02 — `order_picking_completed`

Finalización del picking de un pedido. El tiempo entre `picking_started` y este evento permite calcular M02.

- **Category:** `almacen`
- **Metrics:** M02

**Properties:**

| Campo | Tipo | Req. | Descripción | PII | Sanitización |
|---|---|---|---|---|---|
| `orderId` | `string` (UUIDv4) | ✅ | ID único del pedido en TrackFlow | 🟢 No | — |
| `warehouseLocation` | `string` | ✅ | Almacén donde se realizó el picking (`LA` / `Zaragoza`) | 🟢 No | — |
| `operatorId` | `string` | ✅ | ID seudónimo del operario | 🟡 Seudónimo | Usar ID opaco o HMAC con clave protegida/rotada; no enviar ni persistir email o nombre. |
| `startedAt` | `string` (ISO 8601) | ✅ | Momento de inicio del picking | 🟢 No | — |
| `completedAt` | `string` (ISO 8601) | ✅ | Momento de finalización del picking | 🟢 No | — |
| `pickingTimeMinutes` | `number` | ✅ | Tiempo total de picking en minutos (calculado) | 🟢 No | — |
| `itemsPicked` | `integer` | ❌ | Número total de unidades pickingadas | 🟢 No | — |
| `linesCompleted` | `integer` | ❌ | Número de líneas de pedido completadas | 🟢 No | — |

> **Allowlist:** `orderId`, `warehouseLocation`, `operatorId` (ID opaco/HMAC), `startedAt`, `completedAt`, `pickingTimeMinutes`, `itemsPicked`, `linesCompleted`

**Ejemplo:**

```json
{
  "eventId": "d1e2f3a4-5b6c-7d8e-9f0a-1b2c3d4e5f6a",
  "timestamp": "2026-10-21T10:17:30.000Z",
  "sessionId": "0615dca8-2305-5640-84e6-8ca0454d2506",
  "userId": "urn:service:telemetry-emitter",
  "event_type": "order_picking_completed",
  "schemaVersion": "1.0",
  "requestId": "3b136955-1398-5721-b9ed-8a22b35eb37f",
  "properties": {
    "orderId": "f8e7d6c5-b4a3-2c1d-0e9f-8a7b6c5d4e3f",
    "warehouseLocation": "LA",
    "operatorId": "usr_hmac_7f4d9e2a1b8c",
    "startedAt": "2026-10-21T10:05:00.000Z",
    "completedAt": "2026-10-21T10:17:30.000Z",
    "pickingTimeMinutes": 12.5,
    "itemsPicked": 45,
    "linesCompleted": 3
  }
}
```

---

### 4.3 M03 — `return_completed`

Devolución recibida físicamente en el almacén y lista para inspección. Es el punto de medida del volumen de devoluciones.

- **Category:** `logistica_inversa`
- **Metrics:** M03

**Properties:**

| Campo | Tipo | Req. | Descripción | PII | Sanitización |
|---|---|---|---|---|---|
| `returnId` | `string` (UUIDv4) | ✅ | ID único de la devolución en TrackFlow | 🟢 No | — |
| `shipmentId` | `string` (UUIDv4) | ✅ | ID del envío original asociado | 🟢 No | — |
| `clientId` | `string` (UUIDv4) | ✅ | ID de la marca (cliente B2B) propietaria del producto | 🟢 No | — |
| `clientCountry` | `string` | ✅ | País del cliente (`US` / `ES`) | 🟢 No | — |
| `warehouseLocation` | `string` | ✅ | Almacén donde se recibió la devolución | 🟢 No | — |
| `receivedAt` | `string` (ISO 8601) | ✅ | Momento de recepción física | 🟢 No | — |
| `receivedBy` | `string` | ❌ | ID seudónimo del operario que registró la recepción | 🟡 Seudónimo | Si es imprescindible, usar ID opaco/HMAC; nunca email ni nombre. |
| `packageCondition` | `string` | ❌ | Estado del paquete al llegar (`good`, `damaged`, `open`) | 🟢 No | — |
| `productValue` | `number` | ❌ | Valor del producto en EUR en el momento de la devolución | 🟢 No | — |
| `reasonCategory` | `string` | ❌ | Categoría del motivo de devolución | 🟢 No | — |

> **Allowlist:** `returnId`, `shipmentId`, `clientId`, `clientCountry`, `warehouseLocation`, `receivedAt`, `packageCondition`, `productValue`, `reasonCategory`
>
> `receivedBy` no forma parte del esquema ni del allowlist; si se necesita atribución, usar el `userId` opaco/HMAC del envelope.

**Ejemplo:**

```json
{
  "eventId": "e3f4a5b6-7c8d-9e0f-1a2b-3c4d5e6f7a8b",
  "timestamp": "2026-10-24T09:00:00.000Z",
  "sessionId": "b6877cb2-6380-5588-b871-d7995f115b7a",
  "userId": "usr_hmac_7f4d9e2a1b8c",
  "event_type": "return_completed",
  "schemaVersion": "1.0",
  "requestId": "4976f958-208d-560d-b726-f0af3339ab09",
  "properties": {
    "returnId": "3f4a5b6c-7d8e-9f0a-1b2c-3d4e5f6a7b8c",
    "shipmentId": "9a8b7c6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d",
    "clientId": "550e8400-e29b-41d4-a716-446655440001",
    "clientCountry": "US",
    "warehouseLocation": "LA",
    "receivedAt": "2026-10-24T09:00:00.000Z",
        "packageCondition": "good",
    "productValue": 89.99,
    "reasonCategory": "defective"
  }
}
```

---

### 4.4 M04 — `ticket_auto_resolved`

Ticket resuelto automáticamente por la IA sin intervención humana. Es el evento que mide directamente M04.

- **Category:** `cx`
- **Metrics:** M04
- **PII level:** 🟡 Medio — el `userId` del envelope es seudónimo; canal e idioma son metadatos contextuales y no deben contener identificadores directos.

**Properties:**

| Campo | Tipo | Req. | Descripción | PII | Sanitización |
|---|---|---|---|---|---|
| `ticketId` | `string` (UUIDv4) | ✅ | ID único del ticket en TrackFlow | 🟢 No | — |
| `clientType` | `string` | ✅ | Tipo de cliente (`B2B` / `B2C`) | 🟢 No | — |
| `channel` | `string` | ✅ | Canal de origen (`email`, `whatsapp`, `phone`) | 🟢 No | — |
| `language` | `string` | ❌ | Idioma detectado (`en`, `es`) | 🟢 No | — |
| `category` | `string` | ❌ | Categoría asignada por la IA | 🟢 No | — |
| `resolutionType` | `string` | ✅ | Tipo de resolución automática aplicada | 🟢 No | — |
| `resolvedAt` | `string` (ISO 8601) | ✅ | Momento de resolución | 🟢 No | — |
| `resolutionTimeSeconds` | `integer` | ❌ | Tiempo desde creación hasta resolución | 🟢 No | — |
| `autoApproved` | `boolean` | ❌ | `true` si se resolvió sin revisión humana | 🟢 No | — |
| `confidenceScore` | `number` | ❌ | Nivel de confianza de la IA en la resolución (0–1) | 🟢 No | — |

> **Allowlist:** `ticketId`, `clientType`, `channel`, `language`, `category`, `resolutionType`, `resolvedAt`, `resolutionTimeSeconds`, `autoApproved`, `confidenceScore`

**Ejemplo:**

```json
{
  "eventId": "a6b7c8d9-0e1f-2a3b-4c5d-6e7f8a9b0c1d",
  "timestamp": "2026-10-21T09:00:35.000Z",
  "sessionId": "4dae0a4d-bfc1-510c-8e2a-59633078e0d6",
  "userId": "usr_hmac_7f4d9e2a1b8c",
  "event_type": "ticket_auto_resolved",
  "schemaVersion": "1.0",
  "requestId": "72846cc2-ba08-5add-ab6d-ab82be9cf435",
  "properties": {
    "ticketId": "5a6b7c8d-9e0f-1a2b-3c4d-5e6f7a8b9c0d",
    "clientType": "B2C",
    "channel": "email",
    "language": "en",
    "category": "tracking",
    "resolutionType": "tracking_info",
    "resolvedAt": "2026-10-21T09:00:35.000Z",
    "resolutionTimeSeconds": 35,
    "autoApproved": true,
    "confidenceScore": 0.97
  }
}
```

---

### 4.5 M05 — `executive_report_generated`

Informe ejecutivo generado automáticamente. La diferencia entre `timestamp` del evento y el momento de los datos que contiene mide M05.

- **Category:** `direccion`
- **Metrics:** M05
- **PII level:** 🟢 Bajo — solo metadatos de negocio, sin datos personales

**Properties:**

| Campo | Tipo | Req. | Descripción | PII | Sanitización |
|---|---|---|---|---|---|
| `reportId` | `string` | ✅ | ID único del reporte generado | 🟢 No | — |
| `reportType` | `string` | ✅ | Tipo de reporte (`weekly_executive`, `monthly_executive`, etc.) | 🟢 No | — |
| `periodStart` | `string` (date) | ✅ | Inicio del período cubierto | 🟢 No | — |
| `periodEnd` | `string` (date) | ✅ | Fin del período cubierto | 🟢 No | — |
| `generatedAt` | `string` (ISO 8601) | ✅ | Marca de tiempo de generación | 🟢 No | — |
| `dataFreshnessSeconds` | `integer` | ✅ | Tiempo entre el dataset más reciente y el momento de generación (mide M05) | 🟢 No | — |
| `metricsIncluded` | `array[string]` | ❌ | Lista de métricas incluidas en el reporte | 🟢 No | — |
| `department` | `string` | ❌ | Departamento destinatario | 🟢 No | — |

> **Allowlist:** `reportId`, `reportType`, `periodStart`, `periodEnd`, `generatedAt`, `dataFreshnessSeconds`, `metricsIncluded`, `department`

**Ejemplo:**

```json
{
  "eventId": "c7d8e9f0-1a2b-3c4d-5e6f-7a8b9c0d1e2f",
  "timestamp": "2026-10-22T07:00:00.000Z",
  "sessionId": "d99b9501-4466-59b9-8d9f-18aac4cbf621",
  "userId": "urn:service:telemetry-emitter",
  "event_type": "executive_report_generated",
  "schemaVersion": "1.0",
  "requestId": "45844f70-9105-556c-b111-15c9c5247ea5",
  "properties": {
    "reportId": "rpt_weekly_2026_w43",
    "reportType": "weekly_executive",
    "periodStart": "2026-10-15",
    "periodEnd": "2026-10-21",
    "generatedAt": "2026-10-22T07:00:00.000Z",
    "dataFreshnessSeconds": 45,
    "metricsIncluded": ["M01","M02","M03","M04","M05","M06","M07","M08","M09","M10"],
    "department": "direccion"
  }
}
```

---

### 4.6 M06 — `shipment_carrier_assigned`

Transportista asignado al envío por el motor de selección inteligente. Incluye el coste estimado, clave para M06.

- **Category:** `ultima_milla`
- **Metrics:** M06
- **PII level:** 🟢 Bajo — no hay PII directa, solo direcciones y valores de envío

**Properties:**

| Campo | Tipo | Req. | Descripción | PII | Sanitización |
|---|---|---|---|---|---|
| `shipmentId` | `string` (UUIDv4) | ✅ | ID único del envío en TrackFlow | 🟢 No | — |
| `carrierId` | `string` (UUIDv4) | ✅ | ID del transportista seleccionado | 🟢 No | — |
| `carrierName` | `string` | ✅ | Nombre del transportista | 🟢 No | — |
| `carrierCountry` | `string` | ✅ | País de origen del transportista | 🟢 No | — |
| `assignmentReason` | `string` | ❌ | Razón de la selección del transportista | 🟢 No | — |
| `estimatedCost` | `number` | ✅ | Coste estimado total del envío (EUR) | 🟢 No | — |
| `estimatedCostPerKg` | `number` | ❌ | Coste estimado por kg (EUR/kg) — métrica M06 | 🟢 No | — |
| `estimatedDeliveryDate` | `string` (ISO 8601) | ❌ | Fecha estimada de entrega | 🟢 No | — |
| `weightKg` | `number` | ❌ | Peso total del envío en kg | 🟢 No | — |
| `urgent` | `boolean` | ❌ | `true` si el envío es urgente | 🟢 No | — |
| `destinationCountry` | `string` | ❌ | País de destino del envío | 🟢 No | — |

> **Allowlist:** `shipmentId`, `carrierId`, `carrierName`, `carrierCountry`, `assignmentReason`, `estimatedCost`, `estimatedCostPerKg`, `estimatedDeliveryDate`, `weightKg`, `urgent`, `destinationCountry`

**Ejemplo:**

```json
{
  "eventId": "f3a4b5c6-7d8e-9f0a-1b2c-3d4e5f6a7b8c",
  "timestamp": "2026-10-21T10:32:00.000Z",
  "sessionId": "9a76e54d-40e9-56c3-826c-31935a2df5a3",
  "userId": "urn:service:telemetry-emitter",
  "event_type": "shipment_carrier_assigned",
  "schemaVersion": "1.0",
  "requestId": "f321b2ef-75e1-5e4d-b131-b129e58ebdce",
  "properties": {
    "shipmentId": "9a8b7c6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d",
    "carrierId": "c1d2e3f4-5678-90ab-cdef-1234567890ab",
    "carrierName": "UPS",
    "carrierCountry": "US",
    "assignmentReason": "best_cost_for_weight_destination",
    "estimatedCost": 18.75,
    "estimatedCostPerKg": 0.83,
    "estimatedDeliveryDate": "2026-10-24T18:00:00.000Z",
    "weightKg": 22.5,
    "urgent": false,
    "destinationCountry": "US"
  }
}
```

---

### 4.7 M07 — `deployment_completed`

Despliegue de nueva versión finalizado exitosamente. La diferencia entre `startedAt` de `deployment_started` y `completedAt` mide M07.

- **Category:** `tecnologia`
- **Metrics:** M07
- **PII level:** 🟡 Medio — `deployedBy` puede ser seudónimo; solo ID opaco/HMAC, nunca email o nombre.

**Properties:**

| Campo | Tipo | Req. | Descripción | PII | Sanitización |
|---|---|---|---|---|---|
| `deploymentId` | `string` (UUIDv4) | ✅ | ID único del despliegue | 🟢 No | — |
| `serviceName` | `string` | ✅ | Nombre del servicio desplegado | 🟢 No | — |
| `version` | `string` (semver) | ✅ | Versión desplegada | 🟢 No | — |
| `previousVersion` | `string` (semver) | ❌ | Versión anterior (rollback si es menor) | 🟢 No | — |
| `environment` | `string` | ✅ | Entorno destino (`production`, `staging`) | 🟢 No | — |
| `completedAt` | `string` (ISO 8601) | ✅ | Momento de finalización | 🟢 No | — |
| `durationMinutes` | `integer` | ✅ | Duración total en minutos (mide M07) | 🟢 No | — |
| `healthCheckPassed` | `boolean` | ✅ | `true` si las health checks post-deploy pasaron | 🟢 No | — |
| `deployedBy` | `string` | ❌ | ID seudónimo del desarrollador que inició el deploy | 🟡 Seudónimo | Si es imprescindible, usar ID opaco/HMAC; no enviar ni persistir email o nombre. |
| `commitSha` | `string` | ❌ | SHA del commit desplegado | 🟢 No | — |

> **Allowlist:** `deploymentId`, `serviceName`, `version`, `previousVersion`, `environment`, `completedAt`, `durationMinutes`, `healthCheckPassed`, `deployedBy`, `commitSha`

**Ejemplo:**

```json
{
  "eventId": "a2b3c4d5-6e7f-8a9b-0c1d-2e3f4a5b6c7d",
  "timestamp": "2026-10-21T02:15:00.000Z",
  "sessionId": "95c24c64-e0a2-5f44-ad41-b712ce6fcfdb",
  "userId": "usr_hmac_7f4d9e2a1b8c",
  "event_type": "deployment_completed",
  "schemaVersion": "1.0",
  "requestId": "157a827e-c219-5932-891d-e469ca988ff2",
  "properties": {
    "deploymentId": "7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d",
    "serviceName": "inventory-api",
    "version": "2.5.0",
    "previousVersion": "2.4.1",
    "environment": "production",
    "completedAt": "2026-10-21T02:15:00.000Z",
    "durationMinutes": 15,
    "healthCheckPassed": true,
    "deployedBy": "usr_hmac_7f3d9e2a1b8c",
    "commitSha": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b"
  }
}
```

---

### 4.8 M08 — `incident_sla_breached`

Incidencia que ha superado el SLA acordado sin resolverse. Este evento se emite cuando el tiempo de resolución supera el umbral.

- **Category:** `tecnologia`
- **Metrics:** M08
- **PII level:** 🟢 Bajo — el esquema no admite título libre ni email de escalado; el `userId` del envelope debe ser opaco/no personal.

**Properties:**

| Campo | Tipo | Req. | Descripción | PII | Sanitización |
|---|---|---|---|---|---|
| `incidentId` | `string` (UUID opaco) | ✅ | ID de la incidencia en el sistema de ticketing; no usar título ni identificadores externos con PII | 🟢 No | — |
| `priority` | `string` | ✅ | Prioridad (`critical`, `high`, `medium`, `low`) | 🟢 No | — |
| `assignedArea` | `string` | ❌ | Área responsable de vocabulario controlado | 🟢 No | — |
| `slaDeadline` | `string` (ISO 8601) | ✅ | Fecha límite del SLA | 🟢 No | — |
| `breachedAt` | `string` (ISO 8601) | ✅ | Momento en que se superó el SLA | 🟢 No | — |
| `overdueHours` | `number` | ✅ | Horas de retraso acumuladas | 🟢 No | — |
| `currentStatus` | `string` | ❌ | Estado controlado (`open`, `in_progress`, `pending`, `resolved`, `closed`) | 🟢 No | — |

> **Allowlist:** `incidentId`, `priority`, `assignedArea`, `slaDeadline`, `breachedAt`, `overdueHours`, `currentStatus`

**Ejemplo:**

```json
{
  "eventId": "d8e9f0a1-2b3c-4d5e-6f7a-8b9c0d1e2f3a",
  "timestamp": "2026-10-21T15:00:00.000Z",
  "sessionId": "130a8db3-0c17-5863-ba01-543d1043af36",
  "userId": "urn:service:telemetry-emitter",
  "event_type": "incident_sla_breached",
  "schemaVersion": "1.0",
  "requestId": "df1678fc-b9a4-572c-98a5-411e863735b8",
  "properties": {
    "incidentId": "2c7b4a19-8e63-4f20-9d51-6a3b8c0e2f74",
    "priority": "critical",
    "assignedArea": "tecnologia",
    "slaDeadline": "2026-10-21T12:00:00.000Z",
    "breachedAt": "2026-10-21T15:00:00.000Z",
    "overdueHours": 3,
    "currentStatus": "in_progress"
  }
}
```

---

### 4.9 M09 — `stock_depleted`

> Este contrato describe el evento objetivo; **el servicio de inventario actual no lo emite**. El ledger calcula saldo por lote y almacén, pero SKU es texto, no existe relación de cliente B2B, y la ubicación no está normalizada al enum de este esquema. La emisión requiere resolver esos IDs/dimensiones y asegurar la transición positiva→cero con serialización/idempotencia transaccional. No inferir este evento desde consultas de reorden ni desde el navegador.

Rotura de stock: un SKU ha agotado su inventario disponible en un almacén. Es el evento que mide M09.

- **Category:** `almacen`
- **Metrics:** M09
- **PII level:** 🟡 Medio — `clientId` es un identificador seudónimo de negocio; no incluir `clientName`.

**Properties:**

| Campo | Tipo | Req. | Descripción | PII | Sanitización |
|---|---|---|---|---|---|
| `skuId` | `string` (UUIDv4) | ✅ | ID único del SKU | 🟢 No | — |
| `warehouseLocation` | `string` | ✅ | Almacén donde ocurrió la rotura | 🟢 No | — |
| `currentStock` | `integer` | ✅ | Stock actual (0 en el momento de la rotura) | 🟢 No | — |
| `stockMinimum` | `integer` | ✅ | Stock mínimo configurado para el SKU | 🟢 No | — |
| `clientId` | `string` (UUIDv4) | ✅ | ID del cliente B2B propietario del SKU | 🟢 No | — |
| `affectedOrdersCount` | `integer` | ❌ | Número de pedidos afectados por la rotura | 🟢 No | — |
| `outSince` | `string` (ISO 8601) | ❌ | Momento desde el que el stock es 0 | 🟢 No | — |

> **Allowlist:** `skuId`, `warehouseLocation`, `currentStock`, `stockMinimum`, `clientId`, `affectedOrdersCount`, `outSince`

**Ejemplo:**

```json
{
  "eventId": "a8b9c0d1-2e3f-4a5b-6c7d-8e9f0a1b2c3d",
  "timestamp": "2026-10-21T08:30:00.000Z",
  "sessionId": "10fb1e47-3bbb-5a3a-8545-b32109a49519",
  "userId": "urn:service:telemetry-emitter",
  "event_type": "stock_depleted",
  "schemaVersion": "1.0",
  "requestId": "622bbf09-d0fc-56bc-9c10-ae1a39d83783",
  "properties": {
    "skuId": "b2c3d4e5-6789-01ab-cdef-2345678901bc",
    "warehouseLocation": "LA",
    "currentStock": 0,
    "stockMinimum": 300,
    "clientId": "550e8400-e29b-41d4-a716-446655440003",
    "affectedOrdersCount": 8,
    "outSince": "2026-10-21T08:25:00.000Z"
  }
}
```

---

### 4.10 M10 — `client_health_score_updated`

Scoring de salud de un cliente B2B recalculado. Es el evento que mide la satisfacción y predice renovación (M10).

- **Category:** `comercial`
- **Metrics:** M10
- **PII level:** 🟡 Medio — `clientId` es un identificador seudónimo de negocio; el score agregado no es PII directa. No incluir `clientName`.

**Properties:**

| Campo | Tipo | Req. | Descripción | PII | Sanitización |
|---|---|---|---|---|---|
| `clientId` | `string` (UUIDv4) | ✅ | ID único del cliente B2B | 🟢 No | — |
| `clientCountry` | `string` | ❌ | País del cliente | 🟢 No | — |
| `healthScore` | `number` | ✅ | Puntuación global de salud (0–10) | 🟢 No | — |
| `previousScore` | `number` | ❌ | Puntuación en la evaluación anterior | 🟢 No | — |
| `scoreOnTimeDelivery` | `number` | ❌ | Subscore: entregas a tiempo (0–10) | 🟢 No | — |
| `scoreReturnRate` | `number` | ❌ | Subscore: tasa de devoluciones (0–10) | 🟢 No | — |
| `scoreCxSatisfaction` | `number` | ❌ | Subscore: satisfacción CX (0–10) | 🟢 No | — |
| `scoreVolumeTrend` | `number` | ❌ | Subscore: tendencia de volumen (0–10) | 🟢 No | — |
| `riskLevel` | `string` | ✅ | Nivel de riesgo (`low`, `medium`, `high`, `critical`) | 🟢 No | — |
| `evaluatedAt` | `string` (ISO 8601) | ✅ | Momento de la evaluación | 🟢 No | — |

> **Allowlist:** `clientId`, `clientCountry`, `healthScore`, `previousScore`, `scoreOnTimeDelivery`, `scoreReturnRate`, `scoreCxSatisfaction`, `scoreVolumeTrend`, `riskLevel`, `evaluatedAt`

**Ejemplo:**

```json
{
  "eventId": "d9e0f1a2-3b4c-5d6e-7f8a-9b0c1d2e3f4a",
  "timestamp": "2026-10-21T06:00:00.000Z",
  "sessionId": "e0da9e78-822e-5f32-b284-612182b692d8",
  "userId": "urn:service:telemetry-emitter",
  "event_type": "client_health_score_updated",
  "schemaVersion": "1.0",
  "requestId": "f32a100c-3102-5c88-a766-3a32ec2bb405",
  "properties": {
    "clientId": "550e8400-e29b-41d4-a716-446655440001",
    "clientCountry": "US",
    "healthScore": 8.5,
    "previousScore": 8.2,
    "scoreOnTimeDelivery": 8.8,
    "scoreReturnRate": 7.5,
    "scoreCxSatisfaction": 9.0,
    "scoreVolumeTrend": 8.7,
    "riskLevel": "low",
    "evaluatedAt": "2026-10-21T06:00:00.000Z"
  }
}
```

---

## 5. Eventos adicionales (8+, 3+ categorías)

### 5.1 Categoría: Autenticación

> Los eventos de autenticación no contienen email ni IP. En `login_failed`, se conservan únicamente motivo, hora, aplicación y contador; cualquier investigación con identificadores ocurre fuera de telemetría bajo política de seguridad separada.

Eventos del ciclo de autenticación de usuarios en el backoffice y sistemas internos. El capturador del backoffice no los emite hasta que exista una fuente real de autenticación conectada.

---

#### 5.1.1 `login_succeeded`

Inicio de sesión exitoso tras verificar credenciales.

- **Category:** `autenticacion`
- **Metrics:** —
- **PII level:** 🔴 Alto — no contiene email ni IP; `userId` es seudónimo

**Properties:**

| Campo | Tipo | Req. | Descripción | PII | Sanitización |
|---|---|---|---|---|---|
| `authMethod` | `string` | ❌ | Método de autenticación (`password`, `sso`, `mfa`, `api_token`) | 🟢 No | — |
| `loginAt` | `string` (ISO 8601) | ✅ | Momento del inicio de sesión | 🟢 No | — |
| `sourceApp` | `string` | ❌ | Aplicación de origen (`backoffice`, `website`, `api`) | 🟢 No | — |

> **Allowlist:** `authMethod`, `loginAt`, `sourceApp`

```json
{
  "eventId": "e9f0a1b2-3c4d-5e6f-7a8b-9c0d1e2f3a4b",
  "timestamp": "2026-10-22T08:00:00.000Z",
  "sessionId": "29acba5a-2056-5605-ab02-3badbf36e22c",
  "userId": "usr_hmac_7f4d9e2a1b8c",
  "event_type": "login_succeeded",
  "schemaVersion": "1.0",
  "requestId": "6f33efea-1632-54b8-8548-b0bf4d136153",
  "properties": {    "authMethod": "password",
    "loginAt": "2026-10-22T08:00:00.000Z",
    "sourceApp": "backoffice"
  }
}
```

---

#### 5.1.2 `login_failed`

Intento de inicio de sesión fallido con motivo categórico, sin identidad de cuenta ni datos libres.

- **Category:** `autenticacion`
- **Metrics:** —
- **PII level:** 🟢 Bajo — solo motivo categórico, hora y aplicación; no contiene email, usuario ni IP

**Properties:**

| Campo | Tipo | Req. | Descripción | PII | Sanitización |
|---|---|---|---|---|---|
| `failureReason` | `string` | ✅ | Razón categórica del fallo (`invalid_credentials`, `network_error`) | 🟢 No | No incluir usuario, email, contraseña, token ni texto libre. |
| `attemptAt` | `string` (ISO 8601) | ✅ | Momento del intento | 🟢 No | — |
| `sourceApp` | `string` | ❌ | Aplicación de origen | 🟢 No | — |
| `attemptCount` | `integer` | ❌ | Número de intentos fallidos consecutivos acumulados | 🟢 No | — |

> **Allowlist:** `failureReason`, `attemptAt`, `sourceApp`, `attemptCount`

```json
{
  "eventId": "f0a1b2c3-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "timestamp": "2026-10-22T08:01:00.000Z",
  "sessionId": "29acba5a-2056-5605-ab02-3badbf36e22c",
  "userId": "usr_unknown",
  "event_type": "login_failed",
  "schemaVersion": "1.0",
  "requestId": "ae827906-da4b-5a63-b750-a762d23ca9ed",
  "properties": {
    "failureReason": "invalid_credentials",
    "attemptAt": "2026-10-22T08:01:00.000Z",
    "sourceApp": "backoffice",
    "attemptCount": 3
  }
}
```

---

#### 5.1.3 `session_expired`

Sesión de usuario caducada, reportada por el proveedor de autenticación.

- **Category:** `autenticacion`
- **Metrics:** —
- **PII level:** 🟢 Bajo en properties — el envelope puede contener el ID opaco de usuario autenticado

**Properties:**

| Campo | Tipo | Req. | Descripción | PII | Sanitización |
|---|---|---|---|---|---|
| `expiredAt` | `string` (ISO 8601) | ✅ | Momento de expiración | 🟢 No | — |
| `createdAt` | `string` (ISO 8601) | ✅ | Momento de creación de la sesión | 🟢 No | — |
| `inactivityMinutes` | `integer` | ❌ | Minutos de inactividad antes de expirar | 🟢 No | — |
| `reason` | `string` | ❌ | Razón categórica de expiración (`session_expired`) | 🟢 No | No incluir detalles del token ni texto libre. |

> **Allowlist:** `expiredAt`, `createdAt`, `inactivityMinutes`, `reason`

```json
{
  "eventId": "a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "timestamp": "2026-10-22T12:30:00.000Z",
  "sessionId": "29acba5a-2056-5605-ab02-3badbf36e22c",
  "userId": "usr_hmac_7f4d9e2a1b8c",
  "event_type": "session_expired",
  "schemaVersion": "1.0",
  "requestId": "a8ca447b-0384-5c6a-8d41-44c0b611ef1c",
  "properties": {    "expiredAt": "2026-10-22T12:30:00.000Z",
    "createdAt": "2026-10-22T08:00:00.000Z",
    "inactivityMinutes": 35,
    "reason": "session_expired"
  }
}
```

---

### 5.2 Categoría: Rendimiento

Eventos de monitorización del rendimiento de APIs, servicios y tiempos de respuesta.

---

#### 5.2.1 `api_latency_recorded`

Medición de latencia de un endpoint de API. Se emite en cada petición o como muestra agregada en ventanas de tiempo.

- **Category:** `rendimiento`
- **Metrics:** M08
- **PII level:** 🟡 Medio — `clientId` es un identificador seudónimo y la ruta debe estar normalizada sin IDs ni query params.

**Properties:**

| Campo | Tipo | Req. | Descripción | PII | Sanitización |
|---|---|---|---|---|---|
| `serviceName` | `string` | ✅ | Nombre del servicio (e.g. `inventory-api`) | 🟢 No | — |
| `endpoint` | `string` | ✅ | Ruta del endpoint (ruta normalizada, sin query params ni IDs) | 🟡 Indirecta | Si la ruta contiene IDs (ej. `/users/{id}`), normalizar a patrón antes de enviar |
| `httpMethod` | `string` | ✅ | Método HTTP (`GET`, `POST`, etc.) | 🟢 No | — |
| `latencyMs` | `integer` | ✅ | Latencia medida en milisegundos | 🟢 No | — |
| `statusCode` | `integer` | ✅ | Código de respuesta HTTP | 🟢 No | — |
| `clientId` | `string` | ❌ | Identificador del cliente que hace la petición | 🟢 No | — |

> **Allowlist:** `serviceName`, `endpoint`, `httpMethod`, `latencyMs`, `statusCode`, `clientId`

```json
{
  "eventId": "b2c3d4e5-6f7a-8b9c-0d1e-2f3a4b5c6d7e",
  "timestamp": "2026-10-22T10:00:00.000Z",
  "sessionId": "25e7a3d7-6d37-5d2a-aef5-b6b3d7821224",
  "userId": "urn:service:telemetry-emitter",
  "event_type": "api_latency_recorded",
  "schemaVersion": "1.0",
  "requestId": "a481059c-ffa7-536b-bb2f-90aa419d16ae",
  "properties": {
    "serviceName": "inventory-api",
    "endpoint": "/api/v1/inventory/stock",
    "httpMethod": "GET",
    "latencyMs": 345,
    "statusCode": 200,
    "clientId": "client_opaque_01"
  }
}
```

---

#### 5.2.2 `api_rate_limited`

Petición rechazada porque el cliente o usuario ha superado el límite de tasa configurado.

- **Category:** `rendimiento`
- **Metrics:** —
- **PII level:** 🟢 Bajo — solo identificadores técnicos, sin PII

**Properties:**

| Campo | Tipo | Req. | Descripción | PII | Sanitización |
|---|---|---|---|---|---|
| `clientId` | `string` | ❌ | Identificador del cliente (API key name, app ID) | 🟢 No | — |
| `endpoint` | `string` | ✅ | Ruta del endpoint rate-limited | 🟢 No | — |
| `httpMethod` | `string` | ❌ | Método HTTP | 🟢 No | — |
| `limitPerMinute` | `integer` | ✅ | Límite configurado de peticiones por minuto | 🟢 No | — |
| `retryAfterSeconds` | `integer` | ✅ | Segundos recomendados antes de reintentar | 🟢 No | — |
| `rejectedAt` | `string` (ISO 8601) | ✅ | Momento del rechazo | 🟢 No | — |
| `quotaUsed` | `integer` | ❌ | Cuota usada en la ventana de tiempo | 🟢 No | — |

> **Allowlist:** `clientId`, `endpoint`, `httpMethod`, `limitPerMinute`, `retryAfterSeconds`, `rejectedAt`, `quotaUsed`

```json
{
  "eventId": "c3d4e5f6-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
  "timestamp": "2026-10-22T10:05:00.000Z",
  "sessionId": "25e7a3d7-6d37-5d2a-aef5-b6b3d7821224",
  "userId": "urn:service:telemetry-emitter",
  "event_type": "api_rate_limited",
  "schemaVersion": "1.0",
  "requestId": "f34e1a2f-ed7f-5c22-ac70-319c1d5556a5",
  "properties": {    "clientId": "client_opaque_01",
    "endpoint": "/api/v1/inventory/movements",
    "httpMethod": "POST",
    "limitPerMinute": 60,
    "retryAfterSeconds": 30,
    "rejectedAt": "2026-10-22T10:05:00.000Z",
    "quotaUsed": 61
  }
}
```

---

#### 5.2.3 `deployment_duration_recorded`

Métrica de duración de despliegue registrada al completarse. Complementa a `deployment_completed` con el dato agregado.

- **Category:** `rendimiento`
- **Metrics:** M07
- **PII level:** 🟢 Bajo — solo metadatos técnicos

**Properties:**

| Campo | Tipo | Req. | Descripción | PII | Sanitización |
|---|---|---|---|---|---|
| `deploymentId` | `string` (UUIDv4) | ✅ | ID único del despliegue | 🟢 No | — |
| `serviceName` | `string` | ✅ | Nombre del servicio desplegado | 🟢 No | — |
| `version` | `string` (semver) | ❌ | Versión desplegada | 🟢 No | — |
| `environment` | `string` | ❌ | Entorno destino | 🟢 No | — |
| `durationMinutes` | `integer` | ✅ | Duración total en minutos | 🟢 No | — |
| `deployHour` | `integer` | ❌ | Hora del día en que se desplegó (0–23) | 🟢 No | — |
| `dayOfWeek` | `string` | ❌ | Día de la semana | 🟢 No | — |

> **Allowlist:** `deploymentId`, `serviceName`, `version`, `environment`, `durationMinutes`, `deployHour`, `dayOfWeek`

```json
{
  "eventId": "d4e5f6a7-8b9c-0d1e-2f3a-4b5c6d7e8f9a",
  "timestamp": "2026-10-21T02:15:00.000Z",
  "sessionId": "95c24c64-e0a2-5f44-ad41-b712ce6fcfdb",
  "userId": "urn:service:telemetry-emitter",
  "event_type": "deployment_duration_recorded",
  "schemaVersion": "1.0",
  "requestId": "157a827e-c219-5932-891d-e469ca988ff2",
  "properties": {
    "deploymentId": "7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d",
    "serviceName": "inventory-api",
    "version": "2.5.0",
    "environment": "production",
    "durationMinutes": 15,
    "deployHour": 2,
    "dayOfWeek": "Wednesday"
  }
}
```

---

### 5.3 Categoría: Errores

Eventos de errores, excepciones y fallos en componentes del sistema.

---

#### 5.3.1 `api_error_breached`

Tasa de error de un endpoint que supera el umbral configurado (ej. >5% de 5xx en una ventana de 5 minutos).

- **Category:** `errores`
- **Metrics:** M08
- **PII level:** 🟢 Bajo — solo métricas técnicas agregadas

**Properties:**

| Campo | Tipo | Req. | Descripción | PII | Sanitización |
|---|---|---|---|---|---|
| `serviceName` | `string` | ✅ | Nombre del servicio monitorizado | 🟢 No | — |
| `endpoint` | `string` | ✅ | Ruta del endpoint (normalizada) | 🟢 No | — |
| `httpMethod` | `string` | ❌ | Método HTTP | 🟢 No | — |
| `errorRate` | `number` | ✅ | Tasa de error observada (0–1) | 🟢 No | — |
| `threshold` | `number` | ✅ | Umbral configurado (0–1) | 🟢 No | — |
| `windowMinutes` | `integer` | ✅ | Ventana de tiempo de la medición | 🟢 No | — |
| `totalRequests` | `integer` | ✅ | Total de peticiones en la ventana | 🟢 No | — |
| `errorCount` | `integer` | ✅ | Número de errores en la ventana | 🟢 No | — |
| `breachedAt` | `string` (ISO 8601) | ✅ | Momento en que se superó el umbral | 🟢 No | — |

> **Allowlist:** `serviceName`, `endpoint`, `httpMethod`, `errorRate`, `threshold`, `windowMinutes`, `totalRequests`, `errorCount`, `breachedAt`

```json
{
  "eventId": "e5f6a7b8-9c0d-1e2f-3a4b-5c6d7e8f9a0b",
  "timestamp": "2026-10-21T04:00:00.000Z",
  "sessionId": "df334488-8e41-5ab9-a57d-8ced0993b8c5",
  "userId": "urn:service:telemetry-emitter",
  "event_type": "api_error_breached",
  "schemaVersion": "1.0",
  "requestId": "159c069a-e694-597c-9146-a0f6533c627c",
  "properties": {
    "serviceName": "inventory-api",
    "endpoint": "/api/v1/inventory/stock",
    "httpMethod": "GET",
    "errorRate": 0.08,
    "threshold": 0.05,
    "windowMinutes": 5,
    "totalRequests": 1200,
    "errorCount": 96,
    "breachedAt": "2026-10-21T04:00:00.000Z"
  }
}
```

---

#### 5.3.2 `data_validation_failed`

Petición a la API que falla validación de esquema (HTTP 422) o regla de negocio. Ayuda a detectar problemas en clientes o integraciones.

- **Category:** `errores`
- **Metrics:** —
- **PII level:** 🟡 Medio — los detalles de validación deben ser códigos estructurales, sin valores ni mensajes libres

**Properties:**

| Campo | Tipo | Req. | Descripción | PII | Sanitización |
|---|---|---|---|---|---|
| `clientId` | `string` | ❌ | Identificador del cliente que envió la petición inválida | 🟢 No | — |
| `endpoint` | `string` | ✅ | Ruta del endpoint que rechazó la petición | 🟢 No | — |
| `httpMethod` | `string` | ❌ | Método HTTP | 🟢 No | — |
| `validationErrors` | `array[object]` | ✅ | Lista estructural de errores (campo permitido + código) | 🟢 No | No incluir valores del payload ni mensajes libres |
| `payloadStructure` | `string` | ❌ | Nombre de la estructura esperada | 🟢 No | — |
| `rejectedAt` | `string` (ISO 8601) | ✅ | Momento del rechazo | 🟢 No | — |
| `validationSchemaVersion` | `string` (semver) | ❌ | Versión del esquema de payload que rechazó la petición. No confundir con `schemaVersion` del envelope. | 🟢 No | — |

> **Allowlist:** `clientId`, `endpoint`, `httpMethod`, `validationErrors`, `payloadStructure`, `rejectedAt`, `validationSchemaVersion`

```json
{
  "eventId": "f6a7b8c9-0d1e-2f3a-4b5c-6d7e8f9a0b1c",
  "timestamp": "2026-10-22T11:15:00.000Z",
  "sessionId": "74804a58-4b7f-55ac-88e0-0e961bf1ce12",
  "userId": "urn:service:telemetry-emitter",
  "event_type": "data_validation_failed",
  "schemaVersion": "1.0",
  "requestId": "a042b49a-48f5-58c8-aacf-4e2b782247d6",
  "properties": {    "clientId": "client_opaque_01",
    "endpoint": "/api/v1/inventory/movements",
    "httpMethod": "POST",
    "validationErrors": [
      {"field": "quantity", "code": "positive_integer_required"},
      {"field": "skuId", "code": "required"}
    ],
    "payloadStructure": "movement_create",
    "rejectedAt": "2026-10-22T11:15:00.000Z",
    "validationSchemaVersion": "1.0"
  }
}
```

---

#### 5.3.3 `integration_failed`

Fallo en la comunicación con un sistema externo (API de transportista, SGA, ERP, proveedor cloud).

- **Category:** `errores`
- **Metrics:** —
- **PII level:** 🟢 Bajo — solo metadatos de integración, sin datos de cliente

**Properties:**

| Campo | Tipo | Req. | Descripción | PII | Sanitización |
|---|---|---|---|---|---|
| `integrationName` | `string` | ✅ | Nombre interno de la integración | 🟢 No | — |
| `partnerName` | `string` | ❌ | Nombre del partner externo | 🟢 No | — |
| `endpoint` | `string` | ❌ | Identificador de ruta/integración de catálogo; no es URL | 🟢 No | No incluir host, query params, credenciales ni tokens |
| `httpStatus` | `integer` | ❌ | Código de respuesta HTTP del externo | 🟢 No | — |
| `failureReason` | `string` | ✅ | Código controlado (`timeout`, `upstream_unavailable`, `connection_refused`, `authentication_failed`, `rate_limited`, `invalid_response`, `unknown`) | 🟢 No | No incluir mensajes libres del proveedor |
| `failedAt` | `string` (ISO 8601) | ✅ | Momento del fallo | 🟢 No | — |
| `retryCount` | `integer` | ❌ | Número de reintentos realizados | 🟢 No | — |
| `circuitBreakerStatus` | `string` | ❌ | Estado del circuit breaker (`closed`, `open`, `half_open`) | 🟢 No | — |

> **Allowlist:** `integrationName`, `partnerName`, `endpoint`, `httpStatus`, `failureReason`, `failedAt`, `retryCount`, `circuitBreakerStatus`

```json
{
  "eventId": "a7b8c9d0-1e2f-3a4b-5c6d-7e8f9a0b1c2d",
  "timestamp": "2026-10-22T09:30:00.000Z",
  "sessionId": "d4d75b45-6d8f-59f2-a086-f7f1c143e6e4",
  "userId": "urn:service:telemetry-emitter",
  "event_type": "integration_failed",
  "schemaVersion": "1.0",
  "requestId": "e7e10489-5bb7-5167-9931-f874bb1e0caa",
  "properties": {
    "integrationName": "carrier-tracking-ups",
    "partnerName": "UPS",
    "endpoint": "carrier_tracking_details",
    "httpStatus": 503,
    "failureReason": "upstream_unavailable",
    "failedAt": "2026-10-22T09:30:00.000Z",
    "retryCount": 3,
    "circuitBreakerStatus": "open"
  }
}
```

---

### 5.4 Categoría: Navegación

Eventos de interacción del usuario con las interfaces (backoffice y web corporativa).

---

#### 5.4.1 `section_viewed`

Sección del backoffice o página de la web corporativa visualizada por el usuario. Se emite cuando una sección entra en el viewport o es navegada explícitamente.

- **Category:** `navegacion`
- **Metrics:** —
- **PII level:** 🟡 Medio — `userId` seudónimo; `sectionName` podría revelar información de navegación del usuario

**Properties:**

| Campo | Tipo | Req. | Descripción | PII | Sanitización |
|---|---|---|---|---|---|
| `sectionId` | `string` | ✅ | ID único de la sección | 🟢 No | — |
| `sectionName` | `string` | ❌ | Nombre descriptivo de la sección | 🟢 No | — |
| `sourceApp` | `string` | ❌ | Aplicación de origen | 🟢 No | — |
| `viewedAt` | `string` (ISO 8601) | ✅ | Momento de visualización | 🟢 No | — |
| `referrerSection` | `string` | ❌ | Sección desde la que se navegó | 🟢 No | — |
| `durationSeconds` | `integer` | ❌ | Tiempo que el usuario permaneció en la sección | 🟢 No | — |

> **Allowlist:** `sectionId`, `sectionName`, `sourceApp`, `viewedAt`, `referrerSection`, `durationSeconds`

```json
{
  "eventId": "b8c9d0e1-2f3a-4b5c-6d7e-8f9a0b1c2d3e",
  "timestamp": "2026-10-22T08:05:00.000Z",
  "sessionId": "93cfff02-9aca-534e-ac63-d562f6321ec8",
  "userId": "usr_hmac_7f4d9e2a1b8c",
  "event_type": "section_viewed",
  "schemaVersion": "1.0",
  "requestId": "d5e6fec6-21e2-53fb-ba82-b4673b53f01b",
  "properties": {
    "sectionId": "movements-dashboard",
    "sectionName": "movements",
    "sourceApp": "backoffice",
    "viewedAt": "2026-10-22T08:05:00.000Z",
    "referrerSection": "articles-dashboard",
    "durationSeconds": 45
  }
}
```

---

#### 5.4.2 `feature_used`

Funcionalidad concreta del backoffice utilizada por el operario. Permite medir adopción de funcionalidades y detectar infrautilización.

- **Category:** `navegacion`
- **Metrics:** —
- **PII level:** 🟡 Medio — `userId` seudónimo presente en el envelope

**Properties:**

| Campo | Tipo | Req. | Descripción | PII | Sanitización |
|---|---|---|---|---|---|
| `featureId` | `string` | ✅ | ID único de la funcionalidad | 🟢 No | — |
| `featureName` | `string` | ❌ | Nombre descriptivo de la funcionalidad | 🟢 No | — |
| `actionType` | `string` | ❌ | Tipo de acción (`click`, `drag`, `submit`, `export`, etc.) | 🟢 No | — |
| `usedAt` | `string` (ISO 8601) | ✅ | Momento de uso | 🟢 No | — |
| `contextSection` | `string` | ❌ | Sección desde la que se usó la funcionalidad | 🟢 No | — |
| `outcome` | `string` | ❌ | Resultado (`success`, `error`, `cancelled`) | 🟢 No | — |

> **Allowlist:** `featureId`, `featureName`, `actionType`, `usedAt`, `contextSection`, `outcome`

```json
{
  "eventId": "c9d0e1f2-3a4b-5c6d-7e8f-9a0b1c2d3e4f",
  "timestamp": "2026-10-22T08:10:00.000Z",
  "sessionId": "93cfff02-9aca-534e-ac63-d562f6321ec8",
  "userId": "usr_hmac_7f4d9e2a1b8c",
  "event_type": "feature_used",
  "schemaVersion": "1.0",
  "requestId": "9df42855-4ce3-56f4-9d7d-a7f68303d2f7",
  "properties": {
    "featureId": "article-create",
    "featureName": "article_create",
    "actionType": "click",
    "usedAt": "2026-10-22T08:10:00.000Z",
    "contextSection": "articles-dashboard",
    "outcome": "success"
  }
}
```

---

#### 5.4.3 `direct_stock_edit_rejected`

Intento de edición directa del stock de un artículo rechazado por el sistema. El inventario solo se modifica vía movimientos (ledger inmutable). Este evento se emite cuando alguien intenta un `PUT` o `PATCH` sobre el campo `currentStock`.

- **Category:** `errores`
- **Metrics:** M09
- **PII level:** 🟡 Medio — `userId` seudónimo; no emitir nombres de SKU/producto por privacidad comercial.

**Properties:**

| Campo | Tipo | Req. | Descripción | PII | Sanitización |
|---|---|---|---|---|---|
| `articleId` | `string` (UUIDv4) | ✅ | ID del artículo cuyo stock se intentó modificar | 🟢 No | — |
| `warehouseLocation` | `string` | ❌ | Almacén donde se intentó la edición | 🟢 No | — |
| `attemptedStockValue` | `integer` | ❌ | Valor de stock que se intentó asignar | 🟢 No | — |
| `rejectionReason` | `string` | ✅ | Motivo del rechazo (código predefinido) | 🟢 No | — |
| `rejectedAt` | `string` (ISO 8601) | ✅ | Momento del rechazo | 🟢 No | — |
| `sourceApp` | `string` | ❌ | Aplicación desde la que se intentó la edición | 🟢 No | — |

> **Allowlist:** `articleId`, `warehouseLocation`, `attemptedStockValue`, `rejectionReason`, `rejectedAt`, `sourceApp`

```json
{
  "eventId": "d0e1f2a3-4b5c-6d7e-8f9a-0b1c2d3e4f5a",
  "timestamp": "2026-10-22T14:00:00.000Z",
  "sessionId": "36d81673-8761-5531-bc0a-33d73aaecf3a",
  "userId": "usr_hmac_8f9e7d6c5b4a3c2d1e0f",
  "event_type": "direct_stock_edit_rejected",
  "schemaVersion": "1.0",
  "requestId": "9e3314c7-fbfb-55c6-91c8-7bee51ee9e6c",
  "properties": {
    "articleId": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
    "warehouseLocation": "Zaragoza",
    "attemptedStockValue": 999,
    "rejectionReason": "direct_stock_edit_not_allowed_use_movements",
    "rejectedAt": "2026-10-22T14:00:00.000Z",
    "sourceApp": "backoffice"
  }
}
```

---

## 6. Mapa evento → métrica obligatoria

| ID | Métrica | Evento(s) clave | Departamento |
|---|---|---|---|
| **M01** | Tasa entrega a tiempo | `shipment_delivered` (+ `shipment_delivery_failed`) | Última Milla |
| **M02** | Tiempo medio de picking | `order_picking_completed` | Almacén |
| **M03** | Tasa de devoluciones | `return_completed` (+ `return_requested`) | Logística Inversa |
| **M04** | Resolución automática CX | `ticket_auto_resolved` | CX |
| **M05** | Frescura de datos | `executive_report_generated` | Dirección |
| **M06** | Coste por kg enviado | `shipment_carrier_assigned` | Última Milla |
| **M07** | Tiempo de deploy | `deployment_completed` | Tecnología |
| **M08** | Incidencias resueltas SLA | `incident_sla_breached` (+ `api_error_breached`, `api_latency_recorded` como señales técnicas no equivalentes a incidencia) | Tecnología |
| **M09** | Rotura de stock | `stock_depleted` (+ `direct_stock_edit_rejected`) | Almacén |
| **M10** | Satisfacción cliente B2B | `client_health_score_updated` | Comercial |

---

## 7. Validación y gobierno

### 7.1 Validación del allowlist

Todo evento que atraviesa el pipeline de telemetría pasa por un validador que:

1. Comprueba que los 8 campos del envelope están presentes
2. Resuelve el `event_type` contra el registro maestro de eventos
3. Verifica que cada clave en `properties` existe en el allowlist de ese `event_type`
4. Si hay claves no permitidas → **evento rechazado** (código `ERR-ALLOWLIST-001`)
5. Si faltan claves requeridas → **evento rechazado** (código `ERR-REQUIRED-001`)

### 7.2 Registro maestro

El registro maestro de eventos se mantiene en `docs/telemetry/event-schemas.json` (esquemas JSON) y se valida con un script CI que:

- Comprueba que no haya dos `event_type` con el mismo nombre
- Verifica que todos los eventos referenciados desde `telemetry-plan.md` tienen un allowlist definido
- Genera un reporte de cobertura: qué eventos cubren qué métricas

### 7.3 Evolución de esquemas

| Cambio | Acción | `schemaVersion` |
|---|---|---|
| Añadir clave opcional al allowlist | Solo documentación | Patch (1.0 → 1.1) |
| Añadir clave requerida al allowlist | Revisión + migración | Minor (1.0 → 1.1) |
| Eliminar o renombrar clave | Cambio breaking | Major (1.0 → 2.0) |
| Nuevo `event_type` | Alta en catálogo + CI | — |

---

## 8. Resumen de eventos

| # | `event_type` | Categoría | Métrica | ¿Obligatorio? |
|---|---|---|---|---|
| 1 | `shipment_delivered` | última milla | M01 | ✅ Sí |
| 2 | `order_picking_completed` | almacén | M02 | ✅ Sí |
| 3 | `return_completed` | logística inversa | M03 | ✅ Sí |
| 4 | `ticket_auto_resolved` | cx | M04 | ✅ Sí |
| 5 | `executive_report_generated` | dirección | M05 | ✅ Sí |
| 6 | `shipment_carrier_assigned` | última milla | M06 | ✅ Sí |
| 7 | `deployment_completed` | tecnología | M07 | ✅ Sí |
| 8 | `incident_sla_breached` | tecnología | M08 | ✅ Sí |
| 9 | `stock_depleted` | almacén | M09 | ✅ Sí |
| 10 | `client_health_score_updated` | comercial | M10 | ✅ Sí |
| 11 | `login_succeeded` | **autenticación** | — | ➕ Adicional |
| 12 | `login_failed` | **autenticación** | — | ➕ Adicional |
| 13 | `session_expired` | **autenticación** | — | ➕ Adicional |
| 14 | `api_latency_recorded` | **rendimiento** | M08 | ➕ Adicional |
| 15 | `api_rate_limited` | **rendimiento** | — | ➕ Adicional |
| 16 | `deployment_duration_recorded` | **rendimiento** | M07 | ➕ Adicional |
| 17 | `api_error_breached` | **errores** | M08 | ➕ Adicional |
| 18 | `data_validation_failed` | **errores** | — | ➕ Adicional |
| 19 | `integration_failed` | **errores** | — | ➕ Adicional |
| 20 | `section_viewed` | **navegación** | — | ➕ Adicional |
| 21 | `feature_used` | **navegación** | — | ➕ Adicional |
| 22 | `direct_stock_edit_rejected` | **errores** | M09 | ➕ Adicional |
| 23 | `frontend_error_recorded` | **errores** | — | ➕ Adicional |

---

## 9. Apéndice: Transición desde esquemas anteriores

El envelope legacy (`event-schemas.json`) usaba campos `snake_case` y namespacing con punto (`inventory.received`). La Fase 2 introduce un nuevo envelope normalizado. Durante la transición:

1. **Nuevos eventos** usan exclusivamente el nuevo formato (`eventId`, `timestamp`, `sessionId`, `userId`, `event_type`, `schemaVersion`, `requestId`, `properties`).
2. **Eventos legacy** se mantienen operativos durante 90 días desde la publicación de este documento.
3. Un adaptador en el pipeline de ingesta traduce eventos legacy al nuevo formato aplicando:
   - `eventId` ← `event_id`
   - `timestamp` ← `timestamp`
  - `sessionId` ← UUIDv4 aleatorio y efímero si no existe (no usar un valor determinista/descriptivo)
  - `userId` ← `user_id` solo tras validarlo y convertirlo a ID opaco/HMAC; para sistema, `urn:service:legacy-adapter`
   - `event_type` ← conversión de `dominio.accion` a `entidad_accion` (ej. `inventory.received` → `stock_received`)
   - `schemaVersion` ← `event_version`
   - `requestId` ← `trace_id`
   - `properties` ← `data`

---

*Fin del documento — Fase 2: Diseño del Event Envelope completada.*
