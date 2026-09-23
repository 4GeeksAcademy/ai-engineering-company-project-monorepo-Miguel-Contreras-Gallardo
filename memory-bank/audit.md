# 🔍 Auditoría del Repositorio — Discrepancias

> **Fecha:** 2026-09-23
> **Propósito:** Documentar las diferencias entre lo que documentamos en el memory-bank / resumen y lo que realmente existe en el repositorio.
> **Método:** Auditoría manual de archivos, estructura, git y configuraciones.

---

## 📊 Resumen Ejecutivo

| Tipo | Cantidad |
|---|---|
| 🔴 Discrepancias críticas | 3 |
| 🟡 Discrepancias menores | 4 |
| 📝 Omisiones en documentación | 3 |
| ✅ Coincidencias correctas | 8 |

---

## 🔴 Discrepancias Críticas

### D01 — Rama `feature/incident-manager` no documentada

| Aspecto | Documentado | Realidad |
|---|---|---|
| **Rama actual** | No se menciona ninguna rama específica en memory-bank | `feature/incident-manager` |
| **Ramas existentes** | No documentadas | `main`, `feature/incident-manager`, `origin/main` |
| **Historial** | No documentado | 3 commits: "Initial commit" → "eleccion de empresa" → nuestro commit |
| **Impacto** | 🟡 Medio — El nombre de la rama sugiere que originalmente se planteó como un "incident manager". Esto puede generar confusión sobre el alcance real del proyecto. |
| **Acción** | Decidir si renombrar la rama a algo más representativo (ej: `feature/trackflow-platform`) o documentar la existencia de esta rama histórica. |

---

### D02 — Devcontainer ya tiene `uv` como gestor de paquetes, pero está mal configurado

| Aspecto | Documentado | Realidad |
|---|---|---|
| **Gestor paquetes Python** | 🔴 P0 pendiente según project-brief | ❗ **Ya está configurado** en `.devcontainer/post-create.sh`: `pip install uv` y `uv sync` |
| **Archivo de configuración** | Pendiente de crear | ❌ **No existe** `pyproject.toml` ni `requirements.txt` → `uv sync` fallaría |
| **Extensiones VS Code** | No documentado | ✅ Ya configuradas: Python, Pylance, Jupyter, Docker, ESLint, Prettier, ErrorLens, GitLens |
| **Impacto** | 🔴 Alto — El project-brief marca como P0 pendiente algo que YA está parcialmente configurado, pero roto (falta el archivo de dependencias). |
| **Acción** | Actualizar project-brief: el gestor NO es un pendiente real, solo falta crear el archivo `pyproject.toml`. |

---

### D03 — `company-choice.md` desconectado de la documentación

| Aspecto | Documentado | Realidad |
|---|---|---|
| **Existencia** | No se menciona en memory-bank ni en project-brief | ✅ Existe en raíz con la elección de TrackFlow y la visión del agente orquestador |
| **Contenido** | No referenciado | Contiene la justificación de elegir TrackFlow y la idea del "director de orquesta" |
| **Impacto** | 🔴 Alto — Este archivo es la **fuente original de la visión del proyecto** pero no está enlazado desde ningún lado. Cualquier persona que lea el memory-bank se pierde esta visión fundacional. |
| **Acción** | Añadir referencia a `company-choice.md` en `project-brief.md` como documento fundacional. |

---

## 🟡 Discrepancias Menores

### D04 — `README.md` dice que `CONTEXT.md` es un placeholder

| Aspecto | Documentado | Realidad |
|---|---|---|
| **README original** | El README.md dice: "`CONTEXT.md` is a placeholder and must be replaced with your assigned company context" | ✅ Ya lo reemplazamos con TrackFlow |
| **Impacto** | 🟡 Bajo — La documentación README está desactualizada. No afecta funcionalidad pero confunde. |
| **Acción** | Actualizar README.md para reflejar que CONTEXT.md ya contiene el contexto de TrackFlow. |

---

### D05 — `skills/_template/SKILL.md` está vacío

| Aspecto | Documentado | Realidad |
|---|---|---|
| **Template de skill** | "Template disponible" en project-brief | ❌ El archivo `skills/_template/SKILL.md` existe pero está **completamente vacío** (0 bytes) |
| **Impacto** | 🟡 Bajo — El template no es funcional hasta que tenga contenido. No afecta al proyecto porque no se usa aún. |
| **Acción** | Poblar `SKILL.md` con una plantilla de documentación de skill (o marcar como "por implementar"). |

---

### D06 — `agents/rules/` no existe como carpeta física

| Aspecto | Documentado | Realidad |
|---|---|---|
| **Carpeta rules** | System-patterns.md dice: "Cada departamento tendrá system prompt en `agents/rules/`" | ❌ La carpeta no aparece en el listado. `agents/rules/` no existe físicamente |
| **Impacto** | 🟡 Medio — Se documenta una carpeta que no existe. Puede causar confusión. |
| **Acción** | Crear `agents/rules/` o actualizar la documentación si se decide otra ubicación. |

---

### D07 — No hay `shared/` con contenido real

| Aspecto | Documentado | Realidad |
|---|---|---|
| **Carpeta shared/** | Existe en la estructura del monorepo | ✅ Existe pero solo contiene `README.es.md` y `README.md` |
| **packages/shared/** | Tipos TypeScript base | ✅ `index.ts` con `Id` y `BaseEntity` — correcto |
| **Impacto** | 🟡 Bajo — Hay DOS carpetas "shared" (`shared/` y `packages/shared/`). Puede confundir. La documentación no aclara esta dualidad. |
| **Acción** | Decidir si `shared/` es para Python y `packages/shared/` para TypeScript, y documentarlo. |

---

## 📝 Omisiones en Documentación

### O01 — Devcontainer no documentado

| Aspecto | Detalle |
|---|---|
| **Qué falta** | El proyecto tiene un **entorno de desarrollo containerizado** completo con `.devcontainer/devcontainer.json` y `post-create.sh` |
| **Contenido relevante** | Usa imagen `mcr.microsoft.com/devcontainers/universal:2`, soporte Docker bind mount, extensiones VS Code preinstaladas, y `uv` como gestor de paquetes Python |
| **Acción** | Añadir sección "Entorno de desarrollo" en `project-brief.md` o en `active-context.md` |

---

### O02 — Git Workflow no definido

| Aspecto | Detalle |
|---|---|
| **Qué falta** | No hay documentación sobre cómo se gestionan las ramas, commits, PRs. Existe una rama `feature/incident-manager` que sugiere Git Flow o similar. |
| **Acción** | Decidir y documentar la estrategia de branching (Git Flow, GitHub Flow, trunk-based) en `system-patterns.md` |

---

### O03 — Extensiones VS Code preconfiguradas no documentadas

| Aspecto | Detalle |
|---|---|
| **Qué falta** | El devcontainer ya tiene extensiones útiles preinstaladas (ErrorLens, GitLens, ESLint, Prettier, Python, Docker, Jupyter) que deberían documentarse como parte del stack |
| **Acción** | Mencionar en `project-brief.md` dentro de la sección de stack técnico |

---

## ✅ Coincidencias Correctas (lo que está bien documentado)

| # | Aspecto | Documentación | Realidad |
|---|---|---|---|
| 1 | `.gitignore` vacío | P0 pendiente | ✅ Vacío |
| 2 | `services/` sin implementar | Solo READMEs | ✅ Solo READMEs |
| 3 | `uis/` sin implementar | Solo READMEs | ✅ Solo READMEs |
| 4 | `agents/rules/` sin prompts | Pendiente | ✅ Vacío (pero carpeta no existe, ver D06) |
| 5 | `agents/tools/` sin herramientas | Pendiente | ✅ Solo READMEs |
| 6 | `data/` subcarpetas vacías | Solo READMEs | ✅ Solo READMEs |
| 7 | `workflows/` sin implementar | Solo READMEs | ✅ Solo READMEs |
| 8 | `infra/` sin docker-compose | P1 pendiente | ✅ Solo READMEs |

---

## 🎯 Resumen de Acciones

| Prioridad | Acción | Documento a actualizar |
|---|---|---|
| 🔴 | Decidir futuro de rama `feature/incident-manager` (renombrar o documentar) | `project-brief.md` |
| 🔴 | Crear `pyproject.toml` para que `uv sync` funcione | Archivo nuevo + `project-brief.md` |
| 🔴 | Enlazar `company-choice.md` como documento fundacional | `project-brief.md` |
| 🟡 | Actualizar README.md (ya no es placeholder) | `README.md` |
| 🟡 | Poblar `skills/_template/SKILL.md` o marcarlo como pendiente | `skills/_template/SKILL.md` |
| 🟡 | Crear `agents/rules/` o corregir documentación | `agents/rules/` + `system-patterns.md` |
| 🟡 | Documentar dualidad `shared/` vs `packages/shared/` | `project-brief.md` |
| 📝 | Añadir sección de entorno de desarrollo (devcontainer) | `project-brief.md` |
| 📝 | Definir estrategia de branching | `system-patterns.md` |
| 📝 | Documentar extensiones VS Code preconfiguradas | `project-brief.md` |

---

*Documento generado tras auditoría manual del repositorio — 2026-09-23*