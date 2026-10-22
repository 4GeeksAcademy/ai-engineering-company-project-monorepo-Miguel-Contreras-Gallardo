# Auditoría de Serialización — TrackFlow API

**Fecha:** 2026-10-19  
**Versión de la API:** 0.1.0  
**Objetivo:** Revisar cada endpoint de FastAPI para determinar si la respuesta está correctamente serializada mediante un `response_model` tipado con esquemas Pydantic.

---

## 🔐 Autenticación

La API **no expone rutas de autenticación** (registro, login, restablecimiento de contraseña, etc.) en su estado actual. No existe modelo de usuario, ni manejo de tokens JWT/sesiones.

> **Recomendación para cuando se implementen rutas de auth:**
> - **No devolver contraseñas** — ni en texto plano ni hasheadas — en el cuerpo de ninguna respuesta.
> - **Limitar el email en respuestas de auth** — registro, login y restauración de contraseña suelen funcionar mejor cuando devuelven solo lo que el cliente necesita a continuación (un token, un mensaje genérico de confirmación o una proyección segura del usuario sin campos de credenciales).
> - Usar siempre un esquema de respuesta específico (ej. `AuthResponse`, `UserPublic`) en lugar de devolver el objeto ORM `User` en crudo.

---

## Leyenda

| Estado | Significado |
|--------|-------------|
| 🟢 **Contrato de salida definido** | Tiene un `response_model` adecuado, o declara correctamente `204 No Content` cuando la respuesta no debe incluir cuerpo. |
| 🟡 **Parcialmente serializado** | Tiene `response_model` pero es demasiado genérico (ej. `dict`), incompleto, o no coincide exactamente con lo que el cliente necesita. |
| 🔴 **Sin serializar** | No tiene `response_model` definido; devuelve un dict u ORM en crudo. |

---

## Resumen de Resultados

| Estado | Antes | Después |
|--------|:-----:|:-------:|
| 🟢 Ya serializado | 19 | **23** |
| 🟡 Parcialmente serializado | 3 | **0** |
| 🔴 Sin serializar | 1 | **0** |
| **Total endpoints** | **23** | **23** |

✅ **Todos los endpoints están correctamente serializados tras la Fase 2.**

---

## Auditoría por Endpoint

### 🏥 Health (2 endpoints)

| # | Método | Ruta | Propósito | `response_model` | ¿Qué devuelve realmente? | Estado |
|---|--------|------|-----------|------------------|--------------------------|--------|
| 1 | `GET` | `/` | Health check | ✅ `HealthResponse` | Devuelve un `dict`; FastAPI lo valida y serializa conforme a `HealthResponse` | 🟢 |
| 2 | `GET` | `/healthz` | Health check simple | ✅ `HealthResponse` | Instancia de `HealthResponse` | 🟢 |

> **Nota:** Se creó el esquema `HealthResponse` en `app/schemas/health.py` con campos `status`, `service` y `version`. El handler de `/` devuelve un `dict` (no una instancia Pydantic); FastAPI valida ese valor contra el `response_model` y produce la respuesta documentada.

---

### 🚨 Incidencias (`/api/v1/incidents`) — 9 endpoints

| # | Método | Ruta | Propósito | `response_model` | ¿Qué devuelve realmente? | Estado |
|---|--------|------|-----------|------------------|--------------------------|--------|
| 3 | `POST` | `/api/v1/incidents` | Crear incidencia (RF-01) | ✅ `IncidentResponse` | ORM `Incident` → Pydantic (`from_attributes=True`) | 🟢 |
| 4 | `GET` | `/api/v1/incidents` | Listar incidencias (RF-06) | ✅ `PaginatedIncidentResponse` | `PaginatedIncidentResponse` con `items: list[IncidentResponse]` + paginación | 🟢 |
| 5 | `GET` | `/api/v1/incidents/stats` | Estadísticas de incidencias | ✅ `IncidentStats` | El servicio devuelve `dict`, pero FastAPI lo valida contra `IncidentStats` | 🟢 |
| 6 | `GET` | `/api/v1/incidents/open-by-severity` | Incidencias abiertas por severidad | ✅ `OpenBySeverityResponse` | El servicio devuelve un `dict`; FastAPI lo valida y serializa conforme a `OpenBySeverityResponse` (`total_open`, `by_priority`) | 🟢 |
| 7 | `GET` | `/api/v1/incidents/{incident_id}` | Obtener detalle (RF-06) | ✅ `IncidentResponse` | ORM `Incident` → Pydantic (`from_attributes=True`) | 🟢 |
| 8 | `PATCH` | `/api/v1/incidents/{incident_id}` | Actualizar incidencia (RF-04+05) | ✅ `IncidentResponse` | ORM `Incident` → Pydantic (`from_attributes=True`) | 🟢 |
| 9 | `GET` | `/api/v1/incidents/{incident_id}/audit` | Historial de auditoría (RF-05) | ✅ `list[AuditLogResponse]` | ORM `IncidentAuditLog` → Pydantic (`from_attributes=True`) | 🟢 |
| 10 | `POST` | `/api/v1/incidents/{incident_id}/assign` | Asignar incidencia a área (RF-03) | ✅ `IncidentResponse` | ORM `Incident` → Pydantic (`from_attributes=True`) | 🟢 |
| 11 | `POST` | `/api/v1/incidents/{incident_id}/transition` | Transicionar estado (RF-04) | ✅ `IncidentResponse` | ORM `Incident` → Pydantic (`from_attributes=True`) | 🟢 |

> **Cambios realizados en Fase 2:**
> - **Endpoint 4:** `response_model=dict` → `response_model=PaginatedIncidentResponse` (nuevo esquema con `items`, `total`, `limit`, `offset`).
> - **Endpoint 6:** Sin `response_model` → `response_model=OpenBySeverityResponse` (nuevo esquema con `total_open`, `by_priority`).

---

### 📦 Artículos (`/articles`) — 8 endpoints

| # | Método | Ruta | Propósito | `response_model` | ¿Qué devuelve realmente? | Estado |
|---|--------|------|-----------|------------------|--------------------------|--------|
| 12 | `POST` | `/articles/` | Crear artículo | ✅ `ArticleResponse` | ORM `Article` → Pydantic (`from_attributes=True`) | 🟢 |
| 13 | `GET` | `/articles/` | Listar artículos | ✅ `List[ArticleResponse]` | Lista de ORM `Article` → Pydantic | 🟢 |
| 14 | `GET` | `/articles/{sku}` | Obtener artículo por SKU | ✅ `ArticleResponse` | ORM `Article` → Pydantic | 🟢 |
| 15 | `PUT` | `/articles/{sku}` | Actualizar artículo | ✅ `ArticleResponse` | ORM `Article` → Pydantic | 🟢 |
| 16 | `DELETE` | `/articles/{sku}` | Eliminar (desactivar) artículo | ✅ *(204 No Content; sin `response_model`)* | `None` — sin cuerpo en la respuesta | 🟢 |
| 17 | `POST` | `/articles/{sku}/lots` | Crear lote para un artículo | ✅ `LotResponse` | ORM `Lot` → Pydantic (`from_attributes=True`) | 🟢 |
| 18 | `GET` | `/articles/{sku}/lots` | Listar lotes de un artículo | ✅ `List[LotResponse]` | Lista de ORM `Lot` → Pydantic | 🟢 |
| 19 | `GET` | `/articles/{sku}/lots/{lot_code}` | Obtener lote por código | ✅ `LotResponse` | ORM `Lot` → Pydantic (`from_attributes=True`) | 🟢 |

> **Análisis:** Los endpoints de artículos tienen un contrato de salida definido. El `DELETE` es la excepción: no declara `response_model` porque retorna `204 No Content` sin cuerpo, que es la práctica correcta.

---

### 📊 Inventario (`/inventory`) — 4 endpoints

| # | Método | Ruta | Propósito | `response_model` | ¿Qué devuelve realmente? | Estado |
|---|--------|------|-----------|------------------|--------------------------|--------|
| 20 | `POST` | `/inventory/movements` | Registrar movimiento | ✅ `MovementResult` | Instancia de `MovementResult` (Pydantic) | 🟢 |
| 21 | `GET` | `/inventory/movements` | Obtener movimiento por `request_key` | ✅ `MovementResult` | Instancia de `MovementResult` (Pydantic) | 🟢 |
| 22 | `GET` | `/inventory/stock` | Consultar stock | ✅ `StockQueryResponse` | Instancia de `StockQueryResponse` (Pydantic) | 🟢 |
| 23 | `GET` | `/inventory/reorder` | Señal de reorden | ✅ `ReorderResponse` | Instancia de `ReorderResponse` (Pydantic) | 🟢 |

> **Análisis:** Todos los endpoints de inventario están bien serializados, con esquemas Pydantic definidos y usados consistentemente. El servicio construye explícitamente las instancias de los esquemas de respuesta.

---

## 📊 Tabla Resumen por Categoría

| Categoría | 🟢 Ya serializado | 🟡 Parcialmente serializado | 🔴 Sin serializar | Total |
|-----------|:-----------------:|:---------------------------:|:------------------:|:-----:|
| Health | 2 | 0 | 0 | 2 |
| Incidencias | 9 | 0 | 0 | 9 |
| Artículos | 8 | 0 | 0 | 8 |
| Inventario | 4 | 0 | 0 | 4 |
| **Total** | **23** | **0** | **0** | **23** |

---

## ✅ Estado Final — Fase 2 Completada

Todos los endpoints están correctamente serializados. Los cambios realizados:

| Endpoint | Cambio |
|----------|--------|
| `GET /` | Añadido `response_model=HealthResponse` |
| `GET /healthz` | Añadido `response_model=HealthResponse` |
| `GET /api/v1/incidents` | `response_model=dict` → `response_model=PaginatedIncidentResponse` |
| `GET /api/v1/incidents/open-by-severity` | Sin `response_model` → `response_model=OpenBySeverityResponse` |

### Esquemas creados

| Esquema | Archivo | Campos |
|---------|---------|--------|
| `HealthResponse` | `app/schemas/health.py` | `status`, `service`, `version` |
| `PaginatedIncidentResponse` | `app/schemas/incident.py` | `items: list[IncidentResponse]`, `total`, `limit`, `offset` |
| `OpenBySeverityResponse` | `app/schemas/incident.py` | `total_open`, `by_priority: dict[str, int]` |

### Decisiones de serialización documentadas

- **IncidentResponse** incluye `audit_log: list[AuditLogResponse]` (objeto anidado completo) porque el cliente de detalle de incidencia necesita ver el historial completo. Se carga con `lazy="selectin"` — tener en cuenta posible N+1 en listados.
- Los endpoints de escritura (`POST`, `PUT`, `PATCH`) usan esquemas de entrada separados (`IncidentCreate`, `IncidentUpdate`, `IncidentAssign`, `IncidentTransition`) que solo aceptan los campos modificables, sin reutilizar el esquema de respuesta como entrada.
- No se exponen claves foráneas en bruto: los modelos ORM se serializan a través de esquemas Pydantic con `from_attributes=True`.
- No hay rutas de autenticación en la API actual.

### Consideraciones futuras

- Si se implementan rutas de auth, crear esquemas de respuesta específicos (`AuthResponse`, `UserPublic`) que nunca incluyan `hashed_password`.
- Para login/registro, valorar si el email debe incluirse en la respuesta o si basta con un token. `GET /auth/me` sí puede devolver el email del propio llamante.