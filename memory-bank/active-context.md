# 🎯 Active Context — Sesión Actual

> **Última actualización:** 2026-10-22
> **Sesión:** Fase 2 — Diseño del Event Envelope estándar de telemetría
> **Documentos relacionados:** `project-brief.md` (contexto global) · `progress.md` (histórico) · `decisions.md` (ADRs) · `docs/telemetry/telemetry-plan.md` · `docs/telemetry/event-schemas.json` · `docs/telemetry/event-envelope.md`

---

## 📌 Objetivo de la Sesión

Diseñar el **Event Envelope estándar** de TrackFlow (Fase 2 del sistema de telemetría) con:
- Envelope de 8 campos obligatorios (`eventId`, `timestamp` ISO 8601, `sessionId`, `userId`, `event_type`, `schemaVersion`, `requestId`, `properties`)
- Taxonomía `entidad_accion` con verbos consistentes en pasado
- Esquemas de los 10 eventos obligatorios (M01–M10) con allowlist de propiedades
- 12 eventos adicionales cubriendo 4 categorías (autenticación, rendimiento, errores, navegación)
- Allowlist estricto por evento para prevenir fugas accidentales de datos

---

## ✅ Progreso de esta sesión

- [x] Análisis completo de la documentación de telemetría existente (`telemetry-plan.md`, `event-schemas.json`)
- [x] **📨 Diseño del Event Envelope estándar** (`docs/telemetry/event-envelope.md`) ✅
  - [x] Envelope de 8 campos obligatorios con validación
  - [x] Convención de nombrado `entidad_accion` con 15 verbos admitidos
  - [x] **10 eventos obligatorios** (M01–M10) con esquemas completos y ejemplos
    - `shipment_delivered` (M01), `order_picking_completed` (M02), `return_completed` (M03)
    - `ticket_auto_resolved` (M04), `executive_report_generated` (M05), `shipment_carrier_assigned` (M06)
    - `deployment_completed` (M07), `incident_sla_breached` (M08), `stock_depleted` (M09)
    - `client_health_score_updated` (M10)
  - [x] **12 eventos adicionales** en 4 categorías:
    - **Autenticación (3):** `login_succeeded`, `login_failed`, `session_expired`
    - **Rendimiento (3):** `api_latency_recorded`, `api_rate_limited`, `deployment_duration_recorded`
    - **Errores (4):** `api_error_breached`, `data_validation_failed`, `integration_failed`, `direct_stock_edit_rejected`
    - **Navegación (2):** `section_viewed`, `feature_used`
  - [x] Allowlist explícito por evento (claves permitidas en `properties`)
  - [x] Mapa evento → métrica obligatoria
  - [x] Reglas de validación, gobierno y evolución de esquemas
  - [x] Apéndice de transición desde esquemas legacy (snake_case → camelCase)
- [x] Referencia cruzada actualizada en `telemetry-plan.md` → sección 10 (Gobierno)

---

## 🚀 Próxima Acción

> **Próxima acción:** Fase 3 — Pipeline de ingesta de eventos (POST /api/v1/telemetry/events + validador de allowlist + idempotencia).

---

## 📋 Próximos Pasos (Priorizados)

| Prioridad | Tarea | Dónde |
|---|---|---|
| 🟡 P1 | ~~Fase 1 Gestor Incidencias~~ ✅ | `services/api/` |
| 🟡 P1 | ~~System prompts (7 deptos)~~ ✅ | `agents/rules/` |
| 🟡 P1 | ~~Fase 2 — Event Envelope~~ ✅ | `docs/telemetry/event-envelope.md` |
| 🟡 P1 | **Fase 3 — Pipeline de ingesta de eventos** | `services/api/` |
| 🟢 P2 | Configurar docker-compose.yml (PostgreSQL + API) | Raíz del repo |
| 🟢 P2 | Migrar a PostgreSQL + Alembic migrations | `services/api/` |
| 🟢 P2 | Pipeline de ingesta de pedidos | `data/` |
| 🟢 P2 | API de inventario unificado | Backend |
| 🟢 P2 | Base de conocimiento para RAG (CX) | IA |
| 🔵 P3 | Agente orquestador multi-departamento | Visión final |
  - **🧪 Asignación dedicada POST /{id}/assign** → auto-reported→triaging→assigned + audit (RF-03)
  - **🔄 Transición explícita POST /{id}/transition** → ciclo completo validado (RF-04)
  - **Ciclo completo verificado:** reported → assigned → in_progress → resolved → verified → closed → reopened → triaging → assigned → in_progress → resolved → verified → closed ✅
  - **17 eventos de auditoría** registrados en el ciclo completo ✅
  - 14 tests funcionales todos OK
- [x] **System prompts creados en `agents/rules/` (x7 departamentos)** ✅
  - 01-almacen.md · 02-ultima-milla.md · 03-logistica-inversa.md
  - 04-cx.md · 05-comercial.md · 06-tecnologia.md · 07-direccion.md
- [x] Fix duplicados en roadmap de project-brief.md
- [x] Sincronización con `/memories/repo/`
- [x] **Audit trail embebido en ficha de incidencia** ✅
  - `IncidentResponse.audit_log[]` con todos los cambios de estado/responsable
  - Cada evento incluye: `changed_at` (marca temporal), `changed_by` (autor), `field_name`, `old_value`, `new_value`, `change_type`
  - Filtros por `status` (estado), `priority` (severidad), `assigned_area` verificados
- [x] **Endpoint `GET /open-by-severity`** — incidencias abiertas por prioridad ✅
- [x] **Dashboard visual** en `uis/dashboard-open-by-severity.html` ✅
  - Chart.js doughnut + KPIs + auto-refresh 30s
  - Sirve desde `/ui/dashboard-open-by-severity.html`
  - CORS configurado en FastAPI

---

## 🚀 Siguiente Acción Inmediata

> **Próxima acción:** Configurar `docker-compose.yml` con PostgreSQL + API para entorno local.

> **Siguiente (P1):** Migrar a PostgreSQL + Alembic migrations.

---

## 📋 Próximos Pasos (Priorizados)

| Prioridad | Tarea | Dónde |
|---|---|---|
| 🟡 P1 | ~~**Fase 1 Gestor Incidencias**~~ ✅ **HECHO** | `services/api/` |
| 🟡 P1 | Configurar `docker-compose.yml` (PostgreSQL + API) | Raíz del repo |
| 🟡 P1 | System prompts en `agents/rules/` (7 deptos) | `agents/` |
| 🟡 P1 | Migrar a PostgreSQL + Alembic migrations | `services/api/` |
| 🟢 P2 | Pipeline de ingesta de pedidos | `data/` |
| 🟢 P2 | API de inventario unificado | Backend |
| 🟢 P2 | Base de conocimiento para RAG (CX) | IA |
| 🔵 P3 | Agente orquestador multi-departamento | Visión final |