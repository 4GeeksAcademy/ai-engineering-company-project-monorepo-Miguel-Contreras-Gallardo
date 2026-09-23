# 🚨 Plan de Implementación — Gestor de Incidencias de TrackFlow

> **Fecha:** 2026-09-23
> **Propósito:** Diseño completo del sistema de gestión de incidencias para TrackFlow, con trazabilidad total (auditoría).
> **Stakeholder principal:** Operaciones (Almacén, Última Milla, Logística Inversa, CX, Tecnología)

---

## 1. REQUISITOS FUNCIONALES

### RF-01: Registro multicanal
| Canal | Origen | Ejemplo |
|---|---|---|
| 📧 Email | Clientes, transportistas | "El pedido #12345 no ha llegado" |
| 💬 WhatsApp | Clientes, operarios | "Se ha caído una estantería en el pasillo C" |
| 📞 Teléfono | Consumidores finales | "Mi paquete lleva 5 días sin actualización" |
| 🖥️ Portal interno | Empleados (operarios, AMs) | "Discrepancia de inventario en SKU-9876" |
| 🤖 Sistema (automático) | Alertas del sistema | "API de UPS devuelve error 503" |
| 🌐 Portal cliente | Marcas B2B | "Necesito cambiar la dirección de entrega" |

### RF-02: Clasificación
- **Categoría**: Almacén, Última Milla, Logística Inversa, CX, Tecnología, Comercial
- **Prioridad**: 🔴 Crítica (urgencia 24h) · 🟡 Alta (48h) · 🟢 Normal (5d) · ⚪ Baja (10d)
- **Tipo**: Queja, Incidencia técnica, Solicitud de cambio, Alerta automática

### RF-03: Asignación
- Asignación manual por un coordinador
- Asignación automática por área responsable según categoría
- Reasignación entre áreas con registro de motivo

### RF-04: Ciclo de vida (estados)

```
                    ┌──────────┐
                    │ REPORTED │ (recién creada)
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │ TRIAGING │ (clasificación y priorización)
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │ ASSIGNED │ (asignada a responsable/área)
                    └────┬─────┘
                         │
                    ┌────▼──────┐
                    │ IN PROGRES│ (trabajando en la resolución)
                    └────┬──────┘
                         │
                    ┌────▼──────┐
                    │  RESOLVED │ (solución aplicada)
                    └────┬──────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         ┌────▼───┐ ┌────▼────┐ ┌──▼──────┐
         │VERIFIED│ │REOPENED │ │CANCELLED│
         │ (ok)   │ │ (sigue) │ │         │
         └───┬────┘ └────┬────┘ └─────────┘
             │           │
         ┌───▼────┐      │
         │ CLOSED │◄─────┘
         └────────┘
```

### RF-05: Trazabilidad (AUDITORÍA) ⭐ **Requisito crítico**
Cada cambio en una incidencia debe registrar **quién, qué, cuándo y por qué**:

| Campo auditado | ¿Qué se registra? |
|---|---|
| **Estado** | De `X` a `Y` + responsable del cambio |
| **Responsable** | De `A` a `B` + quién lo reasignó |
| **Prioridad** | De `P1` a `P2` + motivo |
| **Categoría** | De `Almacén` a `Tecnología` + motivo |
| **Descripción / solución** | Versión anterior → nueva + autor |
| **Archivo adjunto** | Quién añadió/eliminó qué archivo |

**Estructura del registro de auditoría**:
```
[timestamp] usuario: [nombre] cambió [campo] de [valor_anterior] → [valor_nuevo]
Motivo: "[razón opcional]"
```

### RF-06: Consultas y filtros
- Ver mis incidencias asignadas
- Ver incidencias de mi área
- Buscar por: ID, cliente, transportista, SKU, estado, prioridad, rango de fechas
- Historial completo de auditoría de una incidencia

---

## 2. MODELO DE DATOS

### 2.1 Tabla: `incidents`

```sql
CREATE TABLE incidents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           VARCHAR(200) NOT NULL,           -- Título corto descriptivo
    description     TEXT NOT NULL,                    -- Descripción detallada
    channel         VARCHAR(20) NOT NULL,             -- email | whatsapp | phone | portal_interno | sistema | portal_cliente
    channel_ref     VARCHAR(100),                     -- ID del mensaje/llamada original (opcional)

    -- Clasificación
    category        VARCHAR(30) NOT NULL,             -- almacen | ultima_milla | logistica_inversa | cx | tecnologia | comercial
    priority        VARCHAR(10) NOT NULL DEFAULT 'normal', -- critica | alta | normal | baja
    incident_type   VARCHAR(30) NOT NULL DEFAULT 'incidencia', -- queja | incidencia | solicitud | alerta

    -- Asignación
    assigned_area   VARCHAR(30),                      -- Área responsable
    assigned_to     VARCHAR(100),                     -- Email o ID del responsable
    assigned_by     VARCHAR(100),                     -- Quién asignó

    -- Estado
    status          VARCHAR(20) NOT NULL DEFAULT 'reported', -- reported | triaging | assigned | in_progress | resolved | verified | closed | reopened | cancelled

    -- Enlaces a entidades del dominio TrackFlow
    related_entity_type VARCHAR(30),                   -- pedido | envio | devolucion | sku | cliente
    related_entity_id   VARCHAR(100),                  -- ID de la entidad relacionada

    -- Resolución
    resolution      TEXT,                              -- Notas de resolución
    resolved_at     TIMESTAMP,
    resolved_by     VARCHAR(100),

    -- Metadatos
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by      VARCHAR(100) NOT NULL,             -- Quién reportó
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 2.2 Tabla: `incident_audit_log` ⭐ **Trazabilidad**

```sql
CREATE TABLE incident_audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id     UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    changed_by      VARCHAR(100) NOT NULL,             -- Quién hizo el cambio
    changed_at      TIMESTAMP NOT NULL DEFAULT NOW(),  -- Cuándo

    -- Qué cambió
    field_name      VARCHAR(50) NOT NULL,              -- status | assigned_to | priority | category | description | resolution
    old_value       TEXT,                              -- Valor anterior (NULL si es creación)
    new_value       TEXT NOT NULL,                     -- Valor nuevo

    -- Por qué
    reason          TEXT,                              -- Motivo opcional del cambio

    -- Metadatos
    change_type     VARCHAR(20) NOT NULL DEFAULT 'update' -- create | update | reassign | escalate | resolve | reopen
);

-- Índices para consultas rápidas
CREATE INDEX idx_audit_incident ON incident_audit_log(incident_id, changed_at);
CREATE INDEX idx_audit_changed_by ON incident_audit_log(changed_by);
```

### 2.3 Tabla: `incident_comments`

```sql
CREATE TABLE incident_comments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id     UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    author          VARCHAR(100) NOT NULL,
    content         TEXT NOT NULL,
    is_internal     BOOLEAN NOT NULL DEFAULT TRUE,     -- TRUE: solo visible internamente
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 2.4 Tabla: `incident_attachments`

```sql
CREATE TABLE incident_attachments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id     UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    file_name       VARCHAR(255) NOT NULL,
    file_path       VARCHAR(500) NOT NULL,
    file_size       INTEGER,
    mime_type       VARCHAR(100),
    uploaded_by     VARCHAR(100) NOT NULL,
    uploaded_at     TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## 3. ARQUITECTURA DEL SERVICIO

### 3.1 Ubicación en el monorepo

```
services/
  api/
    main.py                    # FastAPI entry point
    routers/
      incidents.py             # CRUD + transiciones de incidencias
      audit.py                 # Endpoint de consulta de auditoría
    models/
      incident.py              # SQLAlchemy / Pydantic models
      audit_log.py
      comment.py
      attachment.py
    schemas/
      incident.py              # Pydantic schemas (request/response)
      audit.py
    services/
      incident_service.py      # Lógica de negocio
      audit_service.py         # Registro de auditoría
    db/
      database.py              # Configuración de BD
      migrations/              # Alembic migrations

data/
  raw/                         # Dataset inicial de incidencias (mock)
  pipelines/                   # Pipeline de ingesta de incidencias desde emails
```

### 3.2 API Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/incidents` | Crear nueva incidencia (desde cualquier canal) |
| `GET` | `/api/v1/incidents` | Listar incidencias (filtros: estado, área, prioridad, fechas) |
| `GET` | `/api/v1/incidents/{id}` | Obtener detalle de una incidencia |
| `PATCH` | `/api/v1/incidents/{id}` | Actualizar incidencia (cambio de estado, asignación, etc.) |
| `DELETE` | `/api/v1/incidents/{id}` | Cancelar/archivar incidencia |
| `GET` | `/api/v1/incidents/{id}/audit` | Obtener historial completo de auditoría |
| `POST` | `/api/v1/incidents/{id}/comments` | Añadir comentario |
| `GET` | `/api/v1/incidents/{id}/comments` | Listar comentarios |
| `POST` | `/api/v1/incidents/{id}/attachments` | Adjuntar archivo |
| `DELETE` | `/api/v1/incidents/{id}/attachments/{att_id}` | Eliminar archivo adjunto |
| `GET` | `/api/v1/incidents/stats` | Estadísticas y KPIs de incidencias |

### 3.3 Lógica de auditoría (cambios de estado)

Cada `PATCH` en `/api/v1/incidents/{id}` debe:

1. Leer el estado actual de la BD
2. Aplicar la transición solicitada **solo si es válida** (ej: de `resolved` → `closed` sí, de `reported` → `closed` no)
3. Registrar en `incident_audit_log`:
   - `field_name`: `status`
   - `old_value`: estado anterior
   - `new_value`: estado nuevo
   - `changed_by`: usuario autenticado
   - `reason`: motivo proporcionado (obligatorio para ciertas transiciones)
   - `change_type`: `update` | `reassign` | `resolve` | `reopen`
4. Actualizar `incidents.updated_at`

**Reglas de transición de estado:**
```
reported     → triaging         (inicio de clasificación)
triaging     → assigned         (asignado a un responsable)
assigned     → in_progress      (empieza la resolución)
in_progress  → resolved         (solución aplicada)
resolved     → verified         (verificado por el reportador)
resolved     → reopened         (no conforme con la solución)
verified     → closed           ✅
verified     → reopened         (el problema persiste)
reopened     → in_progress      (se retoma)
*            → cancelled        (se descarta la incidencia)
```

---

## 4. PLAN DE IMPLEMENTACIÓN (FASES)

### 🟢 Fase 1 — Core + Auditoría (MVP) → **Prioridad: AHORA**

| Tarea | Duración estimada | Dependencias |
|---|---|---|
| 1.1 Crear estructura `services/api/` con FastAPI | — | Ninguna |
| 1.2 Modelos SQLAlchemy + migraciones Alembic | — | 1.1 |
| 1.3 Endpoint `POST /incidents` con creación y auditoría inicial | — | 1.2 |
| 1.4 Endpoint `PATCH /incidents/{id}` con máquina de estados + auditoría ⭐ | — | 1.3 |
| 1.5 Endpoint `GET /incidents/{id}/audit` (historial) | — | 1.4 |
| 1.6 Endpoint `GET /incidents` con filtros básicos | — | 1.4 |
| 1.7 Semilla de datos mock para pruebas | — | 1.2 |

**Criterios de aceptación Fase 1:**
- ✅ Puedo crear una incidencia y queda registrado quién, cuándo y el estado inicial
- ✅ Cada cambio de estado deja traza en `incident_audit_log` con `old_value`, `new_value`, `changed_by`, `changed_at`
- ✅ Puedo consultar el historial completo de cualquier incidencia
- ✅ Las transiciones de estado inválidas son rechazadas

### 🟡 Fase 2 — Canales de entrada + Clasificación

| Tarea | Duración | Dependencias |
|---|---|---|
| 2.1 Endpoint de incidencias desde email (webhook/API) | — | Fase 1 |
| 2.2 Clasificación automática por palabras clave (categoría + prioridad) | — | Fase 1 |
| 2.3 Sistema de comentarios + attachments | — | 2.1 |
| 2.4 Dashboard básico de incidencias (Streamlit o FastAPI + HTML) | — | Fase 1 |

### 🟠 Fase 3 — Integración con el ecosistema TrackFlow

| Tarea | Duración | Dependencias |
|---|---|---|
| 3.1 Vincular incidencias a pedidos, envíos, devoluciones | — | Fase 1 + API inventario |
| 3.2 Alertas automáticas desde el sistema (telemetría) | — | Fase 1 |
| 3.3 Portal de incidencias para clientes B2B | — | Fase 2 |

### 🔴 Fase 4 — IA y automatización

| Tarea | Duración | Dependencias |
|---|---|---|
| 4.1 Agente que clasifica y prioriza automáticamente (NLP) | — | Fase 2 |
| 4.2 Recomendación de solución basada en incidencias similares | — | Fase 3 |
| 4.3 Dashboard predictivo (incidencias por área, tendencias) | — | Fase 2 |

---

## 5. EJEMPLO DE TRAZA COMPLETA (end-to-end)

**Caso:** Operario detecta falta de stock en SKU-1234 en Zaragoza y lo reporta.

```
1. POST /incidents → se crea:
   - title: "Discrepancia stock SKU-1234 Zaragoza"
   - status: "reported"
   - created_by: "juan.perez@trackflow.com"
   
   🔍 Auditoría registra automáticamente:
   [2026-09-23 10:15:03] juan.perez@trackflow.com creó la incidencia con status=reported

2. PATCH /incidents/{id} (status: triaging) → coordinador empieza a clasificar

   🔍 Auditoría registra:
   [2026-09-23 10:30:12] ana.whitfield@trackflow.com cambió status de reported → triaging
   Motivo: "Inicio de clasificación - posible error de inventario"

3. PATCH /incidents/{id} (status: assigned, assigned_to: "carlos.lopez", assigned_area: "almacen_zgz")

   🔍 Auditoría registra (2 cambios):
   [2026-09-23 10:35:00] ana.whitfield@trackflow.com cambió status de triaging → assigned
   [2026-09-23 10:35:00] ana.whitfield@trackflow.com cambió assigned_to de null → carlos.lopez@trackflow.com
   Motivo: "Asignado al responsable de inventario de Zaragoza"
   
4. PATCH /incidents/{id} (status: in_progress)

   🔍 Auditoría registra:
   [2026-09-23 11:00:45] carlos.lopez@trackflow.com cambió status de assigned → in_progress

5. PATCH /incidents/{id} (status: resolved, resolution: "Se realizó recuento físico. 
   Diferencia de 3 unidades corregida en el sistema.")

   🔍 Auditoría registra:
   [2026-09-23 14:20:33] carlos.lopez@trackflow.com cambió status de in_progress → resolved
   Motivo: "Recuento físico completado, stock actualizado"

6. PATCH /incidents/{id} (status: verified)

   🔍 Auditoría registra:
   [2026-09-23 16:00:12] juan.perez@trackflow.com cambió status de resolved → verified
   Motivo: "Verificado en sistema, stock correcto ahora"

7. PATCH /incidents/{id} (status: closed)

   🔍 Auditoría registra:
   [2026-09-23 16:05:00] ana.whitfield@trackflow.com cambió status de verified → closed
```

**Resultado: 7 registros de auditoría que reconstruyen la vida completa de la incidencia.**

---

## 6. REGLAS DE NEGOCIO ESPECÍFICAS

### 6.1 Transiciones prohibidas
| Transición | Motivo |
|---|---|
| `reported` → `resolved` | Saltarse la clasificación y asignación |
| `reported` → `closed` | No se puede cerrar sin pasar por resolución |
| `triaging` → `resolved` | Debe asignarse antes de resolver |
| `closed` → cualquier estado | Una vez cerrada, no se reabre (crear nueva) |

### 6.2 Campos obligatorios por transición
| Transición | Campo obligatorio |
|---|---|
| `→ assigned` | `assigned_to` + `assigned_area` |
| `→ resolved` | `resolution` |
| `→ cancelled` | `reason` (motivo de cancelación) |
| `→ reopened` | `reason` (por qué se reabre) |
| Cualquier reasignación | `reason` (motivo del cambio de responsable) |

### 6.3 SLA por prioridad
| Prioridad | Tiempo máximo en `reported` | Tiempo máximo a `resolved` |
|---|---|---|
| 🔴 Crítica | 1 hora | 24 horas |
| 🟡 Alta | 4 horas | 48 horas |
| 🟢 Normal | 24 horas | 5 días laborables |
| ⚪ Baja | 48 horas | 10 días laborables |

---

## 7. TECNOLOGÍA PROPUESTA PARA ESTE SERVICIO

| Componente | Tecnología | Justificación |
|---|---|---|
| Framework API | **FastAPI** | Stack acordado (ADR-004), async, validación con Pydantic |
| ORM | **SQLAlchemy** | Estándar en Python para mapeo de BD |
| Migraciones | **Alembic** | Control de versiones del esquema de BD |
| Base de datos | **PostgreSQL** | Integridad referencial, UUID, consultas complejas |
| Validación | **Pydantic v2** | Schemas request/response |
| Auth básica | **API Key + JWT** | Para identificar quién hace cada cambio |
| Testing | **pytest + httpx** | Tests de API |

---

## 8. PREGUNTAS PENDIENTES PARA EL STAKEHOLDER

1. ¿Quién puede crear incidencias? ¿Solo operarios o también clientes finales?
2. ¿Hay distintos roles? (ej: reportador ≠ coordinador ≠ resolvedor)
3. ¿Necesitamos notificaciones cuando cambia el estado? (email, WhatsApp)
4. SLA: ¿diferenciamos por cliente/marca o solo por prioridad?
5. ¿Integración con el ERP existente o sistema de tickets actual?

---

## 9. REFERENCIAS

- `memory-bank/project-brief.md` — Contexto general del proyecto
- `memory-bank/decisions.md` — ADR-004: Stack técnico base
- `memory-bank/system-patterns.md` — Patrón del agente orquestador
- `memory-bank/audit.md` — Discrepancias detectadas (D02: pyproject.toml necesario)
- `CONTEXT.md` — Contexto de TrackFlow (departamentos, entidades del dominio)