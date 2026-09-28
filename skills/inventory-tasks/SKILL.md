# Skill: Inventory Tasks — TrackFlow Inventory Manager

## Descripción

Esta skill define el proceso para implementar tareas del **Inventory Manager de TrackFlow** siguiendo el plan técnico y la especificación. Úsala cuando necesites completar tareas del archivo `specs/inventory-manager/tasks.md`.

## Cuándo usarla

- Para implementar una o más tareas del Inventory Manager (T01-T15)
- Para crear migraciones de base de datos
- Para implementar endpoints REST del servicio de inventario
- Para escribir tests de integración y concurrencia
- Cuando necesites entender el flujo de trabajo: spec → plan → implementación → test

## Inputs requeridos

1. **Tarea(s) a implementar** — IDs de tarea del archivo tasks.md (ej: T05, T06)
2. **Contexto**: spec, plan y progress del memory-bank

## Proceso

### Fase 1: Comprensión
1. Lee `specs/inventory-manager/spec.md` para los criterios de aceptación
2. Lee `specs/inventory-manager/plan.md` para las decisiones técnicas
3. Lee `specs/inventory-manager/tasks.md` para la tarea concreta
4. Lee `memory-bank/progress.md` para saber el estado actual
5. Lee `memory-bank/techContext.md` para el contexto técnico

### Fase 2: Implementación
1. Crea o modifica archivos según lo especificado
2. Sigue las reglas de:
   - `.agents/rules-python.md` — estilo Python/FastAPI
   - `.agents/rules-postgres.md` — reglas PostgreSQL
   - `.agents/rules-testing.md` — reglas de testing
3. Cada archivo nuevo debe tener type hints, docstrings y validación

### Fase 3: Testing
1. Escribe tests primero si es TDD, o después de implementar
2. Tests de integración contra PostgreSQL (no SQLite)
3. Verifica casos borde y concurrentes

### Fase 4: Verificación
1. Ejecuta `pytest` para verificar que pasan
2. Verifica manualmente la lógica con los criterios de aceptación
3. Actualiza `memory-bank/progress.md`

## Output esperado

- Código implementado con type hints y docstrings
- Tests que cubren la funcionalidad y sus casos borde
- `memory-bank/progress.md` actualizado
- Commit con mensaje descriptivo

## Ejemplo de uso

```bash
# 1. Leer contexto
cat specs/inventory-manager/tasks.md | grep "T05"

# 2. Implementar validación en schemas
# services/api/app/schemas/inventory.py

# 3. Tests
pytest services/api/tests/test_inventory.py -v

# 4. Commit
git add -A && git commit -m "feat(inventory): add input validation for movements"
```

## Recursos

- [Spec](specs/inventory-manager/spec.md) — Criterios de aceptación
- [Plan técnico](specs/inventory-manager/plan.md) — Decisiones de diseño
- [Tareas](specs/inventory-manager/tasks.md) — Lista de tareas con verificación
- [Reglas Python](/.agents/rules-python.md) — Estilo y convenciones
- [Reglas PostgreSQL](/.agents/rules-postgres.md) — Reglas de base de datos