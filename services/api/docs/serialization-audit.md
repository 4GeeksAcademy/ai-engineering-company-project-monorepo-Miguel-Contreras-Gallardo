# Auditoría de Serialización — TrackFlow API

**Fecha:** 2026-10-19  
**Versión de la API:** 0.1.0  
**Objetivo:** Revisar cada endpoint de FastAPI para determinar si la respuesta está correctamente serializada mediante un `response_model` tipado con esquemas Pydantic.

---

## 🔐 Autenticación

La API **no expone rutas de autenticación** (registro, login, restablecimiento de contraseña, etc.) en su estado actual. No existe modelo de usuario ni manejo de tokens JWT/sesiones.

> **Nota:** Cuando se implementen rutas de auth, se deberá prestar especial atención a:
> - No devolver `hashed_password` ni ningún secreto en las respuestas.
> - Valorar si el email debe incluirse en la respuesta de registro/login o si basta con devolver un token y un mensaje de confirmación.
> - Usar siempre un esquema de respuesta específico (ej. `AuthResponse`) en lugar de devolver el objeto ORM `User` en crudo.

---

## Leyenda

| Estado | Significado |
|--------|-------------|
| 🟢 **Ya serializado** | Tiene `response_model` explícito y el esquema es adecuado. |
| 🟡 **Parcialmente serializado** | Tiene `response_model` pero es demasiado genérico, incompleto o no coincide exactamente con lo que el cliente necesita. |
| 🔴 **Sin serializar** | No tiene `response_model` o devuelve un objeto ORM/dict sin tipado. |

---

## Resumen

| Estado | Cantidad |
|--------|----------|
| 🟢 Ya serializado | 20 |
| 🟡 Parcialmente serializado | 2 |
| 🔴 Sin serializar | 1 |
| **Total** | **23** |

---

## Auditoría por Endpoint

### 🏥 Health

| # | Método | Ruta | Propósito | `response_model` | ¿Qué devuelve? | Estado |
|---|--------|------|-----------|-------------------|----------------|--------|
| 1 | `GET` | `/` | Health check | ❌ No tiene | `dict` crudo: `{"status", "service", "version"}` | 🟡 |
| 2 | `GET` | `/healthz` | Health check (simple) | ❌ No tiene | `dict` crudo: `{"status": "ok"}` | 🟡 |

> **Análisis:** Estos endpoints son checks de salud simples. El riesgo de no tener `response_model` es bajo porque devuelven datos fijos y predecibles. Sin embargo, aplicar un esquema `HealthResponse` aportaría consistencia y documentación en OpenAPI.

---

### 🚨 Incidencias (`/api/v1/incidents`)

| # | Método | Ruta | Propósito | `response_model` | ¿Qué devuelve? | Estado |
|---|--------|------|-----------|-------------------|----------------|--------|
| 3 | `POST` | `/api/v1/incidents` | Crear incidencia (RF-01) | ✅ `IncidentResponse` | ORM `Incident` → Pydantic vía `from_attributes` | 🟢 |
| 4 | `GET` | `/api/v1/incidents` | Listar incidencias (RF-06) | ⚠️ `dict` | `dict` con `items` (lista de `IncidentResponse`), `total`, `limit`, `offset` | 🟡 |
| 5 | `GET` | `/api/v1/incidents/stats` | Estadísticas de incidencias | ✅ `IncidentStats` | El servicio devuelve `dict` pero FastAPI lo valida contra el esquema | � |
| 6 | `GET` | `/api/v1/incidents/open-by-severity` | Incidencias abiertas por severidad | ❌ **No tiene** | `dict` crudo del servicio: `{"total_open", "by_priority"}` | 🔴 |
| 7 | `GET` | `/api/v1/incidents/{incident_id}` | Obtener detalle (RF-06) | ✅ `IncidentResponse` | ORM `Incident` → Pydantic vía `from_attributes` | 🟢 |
| 8 | `PATCH` | `/api/v1/incidents/{incident_id}` | Actualizar incidencia (RF-04+05) | ✅ `IncidentResponse` | ORM `Incident` → Pydantic vía `from_attributes` | 🟢 |
| 9 | `GET` | `/api/v1/incidents/{incident_id}/audit` | Historial de auditoría (RF-05) | ✅ `list[AuditLogResponse]` | ORM `IncidentAuditLog` → Pydantic vía `from_attributes` | � |
| 10 | `POST` | `/api/v1/incidents/{incident_id}/assign` | Asignar incidencia a área (RF-03) | ✅ `IncidentResponse` | ORM `Incident` → Pydantic vía `from_attributes` | � |
| 11 | `POST` | `/api/v1/incidents/{incident_id}/transition` | Transicionar estado (RF-04) | ✅ `IncidentResponse` | ORM `Incident` → Pydantic vía `from_attributes` | � |

> **Análisis:**
> - **Endpoint 4 (`GET /incidents`):** usa `response_model=dict`, que es demasiado genérico. Aunque internamente construye los `items` con `IncidentResponse.model_validate(i)`, el tipado del `dict` envolvente no está garantizado por FastAPI. Sería mejor crear un esquema `PaginatedIncidentResponse` con campos `items: list[IncidentResponse]`, `total: int`, `limit: int`, `offset: int`.
> - **Endpoint 6 (`GET /incidents/open-by-severity`):** **No tiene `response_model`** — esto significa que FastAPI no valida ni documenta la estructura de la respuesta. La función del servicio devuelve un `dict` crudo. **Riesgo:** cambios en el servicio pueden alterar la respuesta sin que el contrato API lo refleje. **Solución:** crear un esquema Pydantic `OpenBySeverityResponse` con `total_open: int` y `by_priority: dict[str, int]`.

---

### 📦 Artículos (`/artiles`)

| # | Método | Ruta | Propósito | `response_model` | Qué devuelve? | Estado |
|---|--------|------|-----------|-------------------|----------------|--------|
| 12 | `POST` | `/articles/` | Crear artículo | ✅ `ArticleResponse` | ORM `Article` → Pydantic vía `from_attributes` | 🟢 |
| 13 | `GET` | `/articles/` | Listar artículos | ✅ `List[ArticleResponse]` | Lista de ORM `Article` → Pydantic | 🟢 |
| 14 | `GET` | `/articles/{sku}` | Obtener artículo por SKU | ✅ `ArticleResponse` | ORM `Article` → Pydantic | 🟢 |
| 15 | `PUT` | `/articles/{sku}` | Actualizar artículo | ✅ `ArticleResponse` | ORM `Article` → Pydantic | 🟢 |
| 16 | `DELETE` | `/articles/{sku}` | Eliminar (desactivar) artículo | ✅ *(204 No Content)* | `None` — sin cuerpo | 🟢 |
| 17 | `POST` | `/articles/{sku}/lots` | Crear lote | ✅ `LotResponse` | ORM `Lot` → Pydantic | � |
| 18 | `GET` | `/articles/{sku}/lots` | Listar lotes de un artículo | ✅ `List[LotResponse]` | Lista de ORM `Lot` → Pydantic | 🟢 |
| 19 | `GET` | `/articles/{sku}/lots/{lot_code}` | Obtener lote por código | ✅ `LotResponse` | ORM `Lot` → Pydantic | 🟢 |

> **Análisis:** Todos los endpoints de artículos están correctamente serializados. `DELETE` retorna `204 No Content` sin cuerpo, lo cual es la práctica correcta.

---

### 📦 Inventario (`/inventory`)

| # | Método | Ruta | Propósito | `response_model` | ¿Qué devuelve? | Estado |
|---|--------|------|-----------|-------------------|----------------|--------|
| 20 | `POST` | `/inventory/movements` | Registrar movimiento | ✅ `MovementResult` | Instancia de `MovementResult` (Pydatic) | 🟢 |
| 21 | `GET` | `/inventory/movements` | Obtener movimiento por request_key | ✅ `MovementReult` | Instancia de `MovementResult` (Pydantic) | 🟢 |
| 22 | `GET` | `/inventory/stock` | Consultar stock | ✅ `StockQueryRsponse` | Instancia de `StockQueryResponse` (Pydantic) | � |
| 23 | `GET` | `/inventory/reorder` | Señal de reorden | ✅ `ReoderResponse` | Instancia de `ReorderRsponse` (Pydantic) | 🟢 |

> Los endpoints de inventario también están bien serializados, con esquemas Pydantic definidos y usados consistentemente.

---

## 📊 Tabla Resumen

| Categoría | � | � | 🔴 | Total |
|-----------|----|----|-----|------|
| Health | 0 | 2 | 0 | 2 |
| Incidencias | 6 | 1 | 1 | 8 |
| Artículos | 8 | 0 | 0 | 8 |
| Inventario | 4 | 0 | 0 | 4 |
| **Total** | **18** | **3** | **1** | **22** |

Wait — let me recount properly.

Health: 0 🟢, 2 🟡, 0 🔴 = 2
Incidents: 
- 3 🟢 (POST create, GET by id, PATCH update, GET audit, POST assign, POST transition) = actually 6 🟢
- 4 🟡 (GET list with response_model=dict)
- 6 🔴 (GET open-by-severity, no response_model)
- 5 🟢 (GET stats with IncidentStats)
So incidents: 7 🟢, 1 🟡, 1 🔴 = 9 (including stats)

Wait, let me recount:
#3 (POST) - 🟢
#4 (GET list) - 🟡
#5 (GET stats) - 🟢 (IncidentStats is a proper schema)
#6 (GET open-by-severity) - 🔴
#7 (GET by id) - 🟢
#8 (PATCH update) - 🟢
#9 (GET audit) - 🟢
#10 (POST assign) - 🟢
#11 (POST transition) - 🟢

Incidents: 7 🟢, 1 🟡, 1 🔴 = 9

Articles: 8 🟢 = 8
Inventory: 4 🟢 = 4

Total: 7+8+4+0=19 🟢, 1+2=3 🟡 (health 2 + incidents 1), 1 🔴

Hmm, I made some errors in my table draft. Let me just write a clean final version.</think>Let me create the audit file properly:

<｜DSML｜tool_calls>
<｜DSML｜invoke name="create_file">
<｜DSML｜parameter name="content" string="true"># Auditoría de Serialización — TrackFlow API

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
| 🟢 **Ya serializado** | Tiene `response_model` explícito y el esquema es adecuado. |
| 🟡 **Parcialmente serializado** | Tiene `response_model` pero es demasiado genérico (ej. `dict`), incompleto, o no coincide exactamente con lo que el cliente necesita. |
| 🔴 **Sin serializar** | No tiene `response_model` definido; devuelve un dict u ORM en crudo. |

---

## Resumen de Resultados

| Estado | Cantidad |
|--------|----------|
| 🟢 Ya serializado | 19 |
| 🟡 Parcialmente serializado | 3 |
| 🔴 Sin serializar | 1 |
| **Total endpoints** | **23** |

---

## Auditoría por Endpoint

### 🏥 Health (2 endpoints)

| # | Método | Ruta | Propósito | `response_model` | ¿Qué devuelve realmente? | Estado |
|---|--------|------|-----------|------------------|--------------------------|--------|
| 1 | `GET` | `/` | Health check | ❌ No tiene | `dict` crudo: `{"status": "ok", "service": "trackflow-api", "version": "0.1.0"}` | 🟡 |
| 2 | `GET` | `/healthz` | Health check simple | ❌ No tiene | `dict` crudo: `{"status": "ok"}` | 🟡 |

> **Análisis:** Endpoints de salud simples con datos fijos y predecibles. El riesgo de no tener `response_model` es bajo, pero aplicar un esquema `HealthResponse` aportaría consistencia y mejor documentación en OpenAPI.

---

### 🚨 Incidencias (`/api/v1/incidents`) — 9 endpoints

| # | Método | Ruta | Propósito | `response_model` | ¿Qué devuelve realmente? | Estado |
|---|--------|------|-----------|------------------|--------------------------|--------|
| 3 | `POST` | `/api/v1/incidents` | Crear incidencia (RF-01) | ✅ `IncidentResponse` | ORM `Incident` → Pydantic (`from_attributes=True`) | 🟢 |
| 4 | `GET` | `/api/v1/incidents` | Listar incidencias (RF-06) | ⚠️ **`dict`** | `dict` con `items: list[IncidentResponse]`, `total`, `limit`, `offset` | 🟡 |
| 5 | `GET` | `/api/v1/incidents/stats` | Estadísticas de incidencias | ✅ `IncidentStats` | El servicio devuelve `dict`, pero FastAPI lo valida contra `IncidentStats` | 🟢 |
| 6 | `GET` | `/api/v1/incidents/open-by-severity` | Incidencias abiertas por severidad | ❌ **No tiene** | `dict` crudo del servicio: `{"total_open": int, "by_priority": dict}` | 🔴 |
| 7 | `GET` | `/api/v1/incidents/{incident_id}` | Obtener detalle (RF-06) | ✅ `IncidentResponse` | ORM `Incident` → Pydantic (`from_attributes=True`) | 🟢 |
| 8 | `PATCH` | `/api/v1/incidents/{incident_id}` | Actualizar incidencia (RF-04+05) | ✅ `IncidentResponse` | ORM `Incident` → Pydantic (`from_attributes=True`) | 🟢 |
| 9 | `GET` | `/api/v1/incidents/{incident_id}/audit` | Historial de auditoría (RF-05) | ✅ `list[AuditLogResponse]` | ORM `IncidentAuditLog` → Pydantic (`from_attributes=True`) | 🟢 |
| 10 | `POST` | `/api/v1/incidents/{incident_id}/assign` | Asignar incidencia a área (RF-03) | ✅ `IncidentResponse` | ORM `Incident` → Pydantic (`from_attributes=True`) | 🟢 |
| 11 | `POST` | `/api/v1/incidents/{incident_id}/transition` | Transicionar estado (RF-04) | ✅ `IncidentResponse` | ORM `Incident` → Pydantic (`from_attributes=True`) | 🟢 |

> **Análisis detallado:**
>
> **Endpoint 4 — `GET /api/v1/incidents` (🟡):** Usa `response_model=dict`, que es demasiado genérico. Aunque internamente construye los `items` con `IncidentResponse.model_validate(i)`, el contrato OpenAPI mostrará solo `dict` sin estructura. **Recomendación:** Crear un esquema `PaginatedIncidentResponse` con campos tipados:
> ```python
> class PaginatedIncidentResponse(BaseModel):
>     items: list[IncidentResponse]
>     total: int
>     limit: int
>     offset: int
> ```
>
> **Endpoint 6 — `GET /api/v1/incidents/open-by-severity` (🔴):** Carece por completo de `response_model`. El servicio devuelve un `dict` Python con `total_open` y `by_priority`. **Riesgo:** cambios en el servicio pueden alterar la respuesta sin que el contrato API lo refleje. **Recomendación:** Crear esquema:
> ```python
> class OpenBySeverityResponse(BaseModel):
>     total_open: int
>     by_priority: dict[str, int]
> ```

---

### 📦 Artículos (`/articles`) — 8 endpoints

| # | Método | Ruta | Propósito | `response_model` | ¿Qué devuelve realmente? | Estado |
|---|--------|------|-----------|------------------|--------------------------|--------|
| 12 | `POST` | `/articles/` | Crear artículo | ✅ `ArticleResponse` | ORM `Article` → Pydantic (`from_attributes=True`) | 🟢 |
| 13 | `GET` | `/articles/` | Listar artículos | ✅ `List[ArticleResponse]` | Lista de ORM `Article` → Pydantic | 🟢 |
| 14 | `GET` | `/articles/{sku}` | Obtener artículo por SKU | ✅ `ArticleResponse` | ORM `Article` → Pydantic | 🟢 |
| 15 | `PUT` | `/articles/{sku}` | Actualizar artículo | ✅ `ArticleResponse` | ORM `Article` → Pydantic | 🟢 |
| 16 | `DELETE` | `/articles/{sku}` | Eliminar (desactivar) artículo | ✅ *(204 No Content)* | `None` — sin cuerpo en la respuesta | 🟢 |
| 17 | `POST` | `/articles/{sku}/lots` | Crear lote para un artículo | ✅ `LotResponse` | ORM `Lot` → Pydantic (`from_attributes=True`) | 🟢 |
| 18 | `GET` | `/articles/{sku}/lots` | Listar lotes de un artículo | ✅ `List[LotResponse]` | Lista de ORM `Lot` → Pydantic | 🟢 |
| 19 | `GET` | `/articles/{sku}/lots/{lot_code}` | Obtener lote por código | ✅ `LotResponse` | ORM `Lot` → Pydantic (`from_attributes=True`) | 🟢 |

> **Análisis:** Todos los endpoints de artículos están correctamente serializados. El `DELETE` retorna `204 No Content` sin cuerpo, que es la práctica correcta.

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
| Health | 0 | 2 | 0 | 2 |
| Incidencias | 7 | 1 | 1 | 9 |
| Artículos | 8 | 0 | 0 | 8 |
| Inventario | 4 | 0 | 0 | 4 |
| **Total** | **19** | **3** | **1** | **23** |

---

## 🏁 Acciones Recomendadas

### Prioridad Alta — 🔴 Sin serializar

| Endpoint | Acción |
|----------|--------|
| `GET /api/v1/incidents/open-by-severity` | Añadir `response_model=OpenBySeverityResponse` con un esquema Pydantic que tipifique `total_open` y `by_priority`. |

### Prioridad Media — 🟡 Parcialmente serializado

| Endpoint | Acción |
|----------|--------|
| `GET /api/v1/incidents` | Reemplazar `response_model=dict` por `PaginatedIncidentResponse` con campos tipados. |
| `GET /` | Crear `HealthResponse` para consistencia y documentación OpenAPI. |
| `GET /healthz` | Crear `HealthResponse` o reutilizar el mismo esquema. |

### Consideraciones Generales

- **IncidentResponse** incluye `audit_log: list[AuditLogResponse]` que se carga con `lazy="selectin"`. Esto puede generar consultas N+1 en listados. Se recomienda revisar si el audit log debe incluirse siempre en las respuestas de detalle o si sería mejor cargarlo bajo demanda.
- Todos los esquemas Pydantic usan `model_config = {"from_attributes": True}` correctamente para la serialización desde ORM.
- No se detectan fugas de campos sensibles (contraseñas, tokens, etc.) porque no existen modelos de usuario ni auth en la API actual.