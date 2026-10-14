# Resources — Inventory Tasks

## Referencia rápida de tareas

| Tarea | INV | Descripción | Archivos afectados |
|-------|-----|-------------|-------------------|
| T01 | 005 | Migración articles/warehouses/lots | migrations/ |
| T02 | 002 | Migración movements | migrations/ |
| T03 | 001 | Restricción roles DB | SQL scripts |
| T04 | 001 | Consulta SQL de saldo | `app/db/` |
| T05 | 008 | Validación entrada movimientos | `app/schemas/`, `app/routers/` |
| T06 | 002 | Registro transaccional entradas | `app/services/` |
| T07 | 003 | Salida con verificación saldo | `app/services/` |
| T08 | 004 | Rechazo stock insuficiente | `app/services/` |
| T09 | 004 | Bloqueo fila PostgreSQL | `app/services/` |
| T10 | 005 | Rechazo SKU/lote inexistente | `app/services/` |
| T11 | 006 | Consulta stock con filtros | `app/routers/`, `app/services/` |
| T12 | 007 | Distinguir inexistente de cero | `app/services/` |
| T13 | 009 | Idempotencia request_key | `app/services/` |
| T14 | 009 | Conflicto clave reutilizada | `app/services/` |
| T15 | 010 | Instantánea consistente | Tests |

## Criterios de aceptación por tarea

Ver `specs/inventory-manager/spec.md` -> Criterios de aceptación (INV-001 a INV-012).

## Tabla de routing API

| Método | Endpoint | Función | Tarea relacionada |
|--------|----------|---------|-------------------|
| POST | `/api/v1/movements` | Registrar movimiento | T05-T10, T13-T14 |
| GET | `/api/v1/stock` | Consultar stock | T11-T12 |

## Flujo de implementación recomendado

```
T01 → T02 → T04 → T05 → T06 → T07 → T08 → T09 → T10 → T11 → T12 → T13 → T14 → T15 → T03
```

Donde T01-T04 son prerequisitos de persistencia, T05-T10 son registro de movimientos, T11-T15 son consulta e idempotencia.