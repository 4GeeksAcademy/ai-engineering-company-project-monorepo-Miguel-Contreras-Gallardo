# AGENTS.md — Reglas para asistentes de IA en TrackFlow

Este archivo define las **reglas de sesión, commit y desarrollo** que todos los agentes de IA deben seguir al trabajar en este repositorio.

---

## Reglas de sesión

### 1. Contexto obligatorio
Antes de comenzar cualquier tarea, debes leer:
- `CONTEXT.md` — Briefing completo de la empresa
- `memory-bank/projectbrief.md` — Resumen ejecutivo del proyecto activo
- `memory-bank/techContext.md` — Decisiones técnicas y stack
- `memory-bank/progress.md` — Estado actual de las tareas

### 2. Planificación
- Siempre crea un **todo list** (`manage_todo_list`) antes de empezar trabajo multi-paso
- Marca las tareas como `in-progress` antes de ejecutarlas y `completed` al terminarlas
- Una tarea `in-progress` a la vez

### 3. Commits
Cada commit debe:
- Ser **atómico** — un cambio lógico por commit
- Tener un mensaje descriptivo en **inglés**
- Seguir el formato: `tipo(ámbito): descripción`

  Tipos permitidos: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`
  
  Ejemplos:
  - `feat(inventory): add stock query with warehouse filter`
  - `fix(movements): prevent negative stock on concurrent writes`
  - `docs(memory-bank): add project brief and tech context`

### 4. Pull Requests
- Crear PR contra `main` al completar un conjunto de tareas relacionadas
- El PR debe incluir descripción con: qué se hizo, por qué, y cómo se verificó
- Enlazar las tareas completadas en la descripción

### 5. Lenguaje
- **Código**: todo en inglés (nombres de variables, funciones, clases, mensajes de commit)
- **Documentación técnica**: puede ser en español o inglés según el público
- **Comentarios en código**: en inglés
- **READMEs**: bilingüe (español + inglés) cuando sea posible

---

## Reglas de desarrollo

### Estilo de código
- Python: seguir PEP 8, usar type hints, docstrings en inglés
- FastAPI: usar Pydantic para validación de entrada/salida
- SQLAlchemy: modelos con typing y relaciones explícitas
- Tests: pytest con test client async para FastAPI

### Base de datos
- No exponer UPDATE/DELETE sobre `movements`
- Todo saldo se deriva del diario — nunca almacenar columna de stock editable
- Usar `SELECT ... FOR UPDATE` para serializar escrituras concurrentes
- Idempotencia vía `request_key` con UNIQUE constraint

### Dependencias
- `services/api/requirements.txt` — dependencias de producción
- `services/api/requirements-dev.txt` — dependencias de desarrollo (testing, linting)
- No instalar paquetes globales — usar el virtualenv del proyecto

---

## Reglas de commit (formato)

```
tipo(ámbito): mensaje imperativo en inglés

Cuerpo opcional explicando el qué y el por qué.
```

| Tipo | Uso |
|------|-----|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `docs` | Documentación |
| `refactor` | Cambio de código sin cambiar funcionalidad |
| `test` | Añadir o modificar tests |
| `chore` | Tareas de mantenimiento (deps, config, etc.) |
| `perf` | Mejora de rendimiento |

Ejemplos:
```
feat(inventory): add movement registration endpoint with idempotency
fix(movements): prevent double insertion on concurrent requests
docs(memory-bank): add project brief and tech context files
test(inventory): add integration tests for stock query
```