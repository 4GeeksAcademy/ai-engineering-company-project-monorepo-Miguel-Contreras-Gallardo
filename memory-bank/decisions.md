# 📐 ADR — Architecture Decision Records

> **Última actualización:** 2026-09-23
> Registro de decisiones arquitectónicas clave del proyecto. Cada ADR sigue el formato: contexto, decisión, consecuencias.

---

## ADR-001: Memory Bank como sistema de trazabilidad

| Campo | Valor |
|---|---|
| **Fecha** | 2026-09-23 |
| **Estado** | ✅ Aceptada |
| **Contexto** | El proyecto no tenía ningún sistema de trazabilidad. No había registro de progreso, decisiones ni contexto activo. |
| **Decisión** | Crear `memory-bank/` en la raíz del repo con 5 documentos: `project-brief.md`, `active-context.md`, `progress.md`, `decisions.md`, `system-patterns.md`. |
| **Consecuencias** | + Trazabilidad completa del proyecto. + Facilita la incorporación de nuevos colaboradores. - Requiere mantener los documentos actualizados en cada sesión. |
| **Alternativas** | Usar solo `/memories/` de Copilot (no está en el repo, no es portable). |

---

## ADR-002: Idioma del proyecto

| Campo | Valor |
|---|---|
| **Fecha** | 2026-09-23 |
| **Estado** | ✅ Aceptada |
| **Contexto** | El usuario se comunica en español y los READMEs están en ambos idiomas. |
| **Decisión** | Trabajar en **español** para toda la documentación de trabajo y el memory-bank. Código fuente en inglés (convención estándar). READMEs bilingües. |
| **Consecuencias** | + Alineado con el usuario. + Código en inglés es interoperable. |

---

## ADR-003: Monorepo con estructura por capas

| Campo | Valor |
|---|---|
| **Fecha** | 2026-09-23 |
| **Estado** | ✅ Aceptada (heredada de la plantilla) |
| **Contexto** | La plantilla de 4Geeks Academy define una estructura por capas (UI, services, data, agents, skills, workflows, infra). |
| **Decisión** | Mantener la estructura propuesta sin modificaciones. Cada carpeta tiene una responsabilidad única. |
| **Consecuencias** | + Separación de concerns clara. + Escalable. - Exige disciplina para no mezclar responsabilidades. |

---

## ADR-004: Stack técnico base

| Campo | Valor |
|---|---|
| **Fecha** | 2026-09-23 |
| **Estado** | ✅ Aceptada |
| **Contexto** | Se necesita definir tecnologías base para empezar a desarrollar. |
| **Decisión** | Adoptar: **FastAPI** (backend), **Python** (agentes/skills), **TypeScript** (tipos compartidos), **Docker** (infra), **n8n** (workflows). |
| **Consecuencias** | + Stack homogéneo (Python-centric). + FastAPI es ideal para APIs de IA. - Pendiente decidir framework de agentes (LangChain vs CrewAI vs LangGraph). |

---

## ADR-005: Refactorización de inicialización de iconos Lucide

| Campo | Valor |
|---|---|
| **Fecha** | 2026-10-18 |
| **Estado** | ✅ Aceptada |
| **Contexto** | Ambos frontends llamaban manualmente a `lucide.createIcons()` en 6 lugares distintos (app.js del website + app.js del backoffice). Era fácil olvidar una llamada y los iconos no se renderizaban. |
| **Decisión** | Extraer un helper compartido `uis/shared/lucide-helper.js` que: (1) se auto-ejecuta en `DOMContentLoaded`, (2) expone `window.refreshIcons()` para actualizaciones dinámicas, (3) se carga via `<script defer>` tras Lucide y antes de cada app.js. |
| **Consecuencias** | + Elimina duplicación de código. + Centraliza la inicialización. - Añade un archivo y una petición HTTP adicional. |
| **Alternativas** | No refactorizar (mantener 6 llamadas directas). Usar MutationObserver (más complejo, overhead innecesario para este caso). |

---

## ADR-006: Estrategia de carga de Google Fonts

| Campo | Valor |
|---|---|
| **Fecha** | 2026-10-18 |
| **Estado** | ✅ Aceptada |
| **Contexto** | Lighthouse reportaba render-blocking por Google Fonts. Se intentó usar `media="print"` con `onload="this.media='all'"`, pero esto regresó FCP y Performance. |
| **Decisión** | Mantener el `<link rel="stylesheet">` original con `display=swap` en la URL de Google Fonts. El patrón `media="print"` introduce latencia extra porque el navegador descarga la fuente dos veces (una con media="print" aplicada y otra al cambiar a media="all"). |
| **Consecuencias** | + FCP se recupera. + Sin regresión de rendimiento. - Las fuentes siguen siendo un recurso render-blocking, pero con `display=swap` el texto se muestra con fuente de respaldo inmediatamente. |

---

## ADR-007: Comprobación de estado de API con AbortController

| Campo | Valor |
|---|---|
| **Fecha** | 2026-10-18 |
| **Estado** | ✅ Aceptada |
| **Contexto** | El backoffice hacía un fetch HEAD a localhost:8000 para comprobar el estado de la API. Cuando la API no está en ejecución (entornos de auditoría, desarrollo frontend aislado), se registraba un `ERR_CONNECTION_REFUSED` en la consola que Lighthouse penalizaba en Best Practices. |
| **Decisión** | Envolver la petición en un `AbortController` con timeout de 1.5s. Si la API no responde, se aborta la petición antes de que el navegador registre el error de conexión. |
| **Consecuencias** | + Cero errores de consola cuando la API no está disponible. + Timeout rápido (1.5s) en lugar de esperar el timeout nativo del navegador (~30s). |

---

## ADR-008: Gestor de Incidencias — arquitectura y trazabilidad

| Campo | Valor |
|---|---|
| **Fecha** | 2026-09-23 |
| **Estado** | ✅ Aceptada |
| **Contexto** | Los stakeholders de operaciones necesitan un sistema para registrar incidencias multicanal, clasificarlas, asignarlas a un área responsable y hacer seguimiento del estado. Requisito crítico: toda transición de estado o cambio de responsable debe quedar registrado con quién, cuándo y por qué. |
| **Decisión** | Construir un servicio de incidencias dentro de `services/api/` con FastAPI + SQLAlchemy + PostgreSQL. El modelo incluye una tabla `incident_audit_log` que registra cada cambio (campo, valor anterior, valor nuevo, responsable, timestamp, motivo). Las transiciones de estado se rigen por una máquina de estados con reglas explícitas. |
| **Consecuencias** | + Trazabilidad total de cada incidencia. + Se puede reconstruir el histórico completo. + Base sólida para futuros agentes de IA que automaticen clasificación/resolución. - Mayor complejidad en las escrituras (doble escritura: entidad + log). - PostgreSQL requerido como dependencia. |
| **Alternativas** | Usar una tabla de eventos genérica (event sourcing) — más potente pero mayor complejidad inicial para el alcance actual. |

---

## Plantilla para nuevas ADR

```markdown
## ADR-NNN: Título de la decisión

| Campo | Valor |
|---|---|
| **Fecha** | YYYY-MM-DD |
| **Estado** | Propuesta / ✅ Aceptada / ❌ Rechazada / 🔄 Reemplazada |
| **Contexto** | ... |
| **Decisión** | ... |
| **Consecuencias** | ... |
| **Alternativas** | ... |
```