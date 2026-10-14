# Reglas para git y Pull Requests

## Commits
- Commits **atómicos**: un cambio lógico por commit
- Mensajes en **inglés**, formato imperativo
- Formato: `tipo(ámbito): descripción`
  - `feat(inventory): add movement registration endpoint`
  - `fix(movements): prevent negative stock on concurrent access`
  - `docs(memory-bank): add project brief and tech context`
  - `test(inventory): add integration tests for stock query`

## Pull Requests
- Crear PR contra `main`
- Título descriptivo: `feat: implement inventory movement registration service`
- Descripción debe incluir:
  - **Qué** se hizo
  - **Por qué** (referencia a spec/tasks)
  - **Cómo** se verificó (tests ejecutados, resultados)
- Enlazar tareas completadas de `specs/inventory-manager/tasks.md`
- Mantener PRs pequeños y enfocados (ideal < 400 líneas cambiadas)

## Ramas
- Formato: `feature/[nombre]` para nuevas funcionalidades
- Formato: `fix/[descripcion]` para correcciones
- Formato: `docs/[descripcion]` para documentación
- Una rama por conjunto lógico de cambios

## Antes de commitear
1. Verificar que los tests pasan: `cd services/api && pytest`
2. Verificar que no hay errores de lint: `ruff check .`
3. Revisar que no hay código comentado o prints de debug