# 🎯 Active Context — Sesión Actual

> **Última actualización:** 2026-10-22
> **Sesión:** Telemetría — Event Envelope, captura en backoffice y stub de ingesta
> **Documentos relacionados:** `project-brief.md` (contexto global) · `progress.md` (histórico) · `decisions.md` (ADRs) · `docs/telemetry/telemetry-plan.md` · `docs/telemetry/event-schemas.json` · `docs/telemetry/event-envelope.md`

---

## 📌 Objetivo de la Sesión

Implementar el stub de ingesta de telemetría, el servicio window.track en el backoffice con buffer y sendBeacon, e instrumentar navegación, interacciones y señales técnicas con allowlists estrictas.

---

## ✅ Progreso de esta sesión

- [x] **Stub de ingesta de telemetría** (`services/api/app/routers/telemetry.py`) ✅
- [x] **Schemas Pydantic** (`services/api/app/schemas/telemetry.py`) con envelope estándar ✅
- [x] Tests del endpoint (`services/api/tests/test_telemetry.py`) ✅
- [x] **Servicio `window.track`** en `uis/backoffice/src/services/telemetry.js` con buffer, batch, retry, sendBeacon ✅
- [x] Tests del servicio (`uis/backoffice/tests/telemetry.test.cjs`) ✅
- [x] **Instrumentación del backoffice** en `uis/backoffice/app.js`:
  - [x] Wrapper `api()` con latencia y errores
  - [x] Vista sección en navegación SPA
  - [x] Interacciones de inventario (crear, editar, desactivar artículo, movimiento, lote, buscar)
  - [x] Web Vitals (TTFB, FCP, LCP, CLS, INP) vía PerformanceObserver
  - [x] Errores globales con categorías controladas
- [x] `config.py` actualizado con `telemetry_endpoint` opcional

---

## 🚀 Siguiente Acción Inmediata

> **Próxima acción:** Revisar PR #5 y mergear feature/lighthouse-audit → main.

> **Siguiente (P1):** Configurar `docker-compose.yml` con PostgreSQL + API para entorno local.

---

## 📋 Próximos Pasos (Priorizados)

| Prioridad | Tarea | Dónde |
|---|---|---|
| 🟢 P2 | Pipeline de ingesta de pedidos | `data/` |
| 🟢 P2 | Base de conocimiento para RAG (CX) | IA |
| 🟢 P2 | Restricción roles DB solo INSERT/SELECT (T03) | `services/api/` |
| 🔵 P3 | Agente orquestador multi-departamento | Visión final |