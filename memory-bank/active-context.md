# 🎯 Active Context — Sesión Actual

> **Última actualización:** 2026-10-14
> **Sesión:** Infraestructura Docker + Website corporativo + Despliegue a producción
> **Documentos relacionados:** `project-brief.md` (contexto global) · `progress.md` (histórico) · `decisions.md` (ADRs)

---

## 📌 Objetivo de la Sesión

Crear infraestructura Docker completa para el monorepo TrackFlow, implementar sitio web corporativo y backoffice mejorado, y desplegar todo el stack a producción en un VPS.

---

## ✅ Progreso de esta sesión

### Docker Infrastructure
- [x] `docker-compose.yml` — Orquestación PostgreSQL 16 + API FastAPI + UIs
- [x] `services/Dockerfile` — Python 3.12-slim + uv + Uvicorn
- [x] `uis/Dockerfile` — Node 20-alpine + serve
- [x] `uis/start.sh` — Script para servir website (:3000) y backoffice (:3001)
- [x] `scripts/deploy.sh` — Despliegue automatizado al VPS
- [x] `.env` — Variables de entorno para PostgreSQL y API

### Website + Backoffice (PR #3)
- [x] Sitio web corporativo (`uis/website/`) mergeado desde `feature/agent-memory-bank`
- [x] Backoffice mejorado (`uis/backoffice/`) mergeado

### Despliegue Producción
- [x] Stack probado localmente en Windows
- [x] Docker instalado en VPS `207.154.214.100` (Ubuntu 22.04)
- [x] Contenedores: `trackflow-db` (healthy), `trackflow-api`, `trackflow-uis`
- [x] Nginx reverse proxy configurado en puerto 80
- [x] **PR #4** creado (`feature/docker-infrastructure` → `main`)

---

## 🚀 Siguiente Acción Inmediata

> **Próxima acción:** Hacer merge del PR #4 y continuar con tareas de Backend/Datos pendientes.

---

## 📋 Próximos Pasos (Priorizados)

| Prioridad | Tarea | Dónde |
|---|---|---|
| 🟢 P2 | Pipeline de ingesta de pedidos | `data/` |
| 🟢 P2 | Base de conocimiento para RAG (CX) | IA |
| 🟢 P2 | Restricción roles DB solo INSERT/SELECT (T03) | `services/api/` |
| 🔵 P3 | Agente orquestador multi-departamento | Visión final |