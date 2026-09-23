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