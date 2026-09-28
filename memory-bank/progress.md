# Progress — TrackFlow Inventory Manager

## Estado general

| Área | Estado | Notas |
|------|--------|-------|
| Spec | ✅ Completada | Ver `specs/inventory-manager/spec.md` |
| Plan técnico | ✅ Completado | Ver `specs/inventory-manager/plan.md` |
| Tareas | 🟡 15/18 completadas | T01-T15 pendientes de implementar |
| Migraciones DB | 🟡 Pendiente | T01, T02 |
| Servicio API | 🟡 Parcial | Structure exists, logic pending |
| Backoffice | ✅ Completado | T16-T18 implementados |
| Testing | 🟡 Pendiente | Tests por escribir |
| Concurrencia | 🟡 Pendiente | T09 (row-level locking) |
| Idempotencia | 🟡 Pendiente | T13, T14 |

## Tareas completadas (T16-T18)
- [x] T16 — CRUD de artículos (alta, listado, edición, baja lógica)
- [x] T17 — Registro de movimientos (entrada, salida, ajuste)
- [x] T18 — Señal de reorden en backoffice

## Tareas pendientes (T01-T15)

### Persistencia
- [ ] T01 — Migración de articles, warehouses, lots
- [ ] T02 — Migración de movements con request_key
- [ ] T03 — Restricción de roles: solo INSERT/SELECT en movements
- [ ] T04 — Consulta SQL de saldo agregado

### Registro de movimientos
- [ ] T05 — Validación de entrada (tipo, cantidad, almacén)
- [ ] T06 — Registro transaccional de entradas
- [ ] T07 — Salida con verificación de saldo
- [ ] T08 — Rechazo por stock insuficiente
- [ ] T09 — Serialización con bloqueo de fila PostgreSQL
- [ ] T10 — Rechazo de SKU/lote inexistente

### Consulta e idempotencia
- [ ] T11 — Consulta de stock con filtros
- [ ] T12 — Distinguir recursos inexistentes de saldo cero
- [ ] T13 — Idempotencia por request_key
- [ ] T14 — Conflicto por clave reutilizada con datos distintos
- [ ] T15 — Instantánea consistente de movimientos

## Próximos pasos
1. Implementar migraciones (T01, T02)
2. Configurar PostgreSQL para desarrollo
3. Implementar servicio de inventario con concurrencia
4. Escribir tests de integración
5. Completar endpoints REST