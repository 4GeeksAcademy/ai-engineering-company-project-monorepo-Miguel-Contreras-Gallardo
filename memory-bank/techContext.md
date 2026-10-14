# Tech Context — TrackFlow Monorepo

## Stack principal

| Capa | Tecnología | Versión/Notas |
|------|-----------|---------------|
| Lenguaje backend | Python 3.11+ | Tipado, async |
| Framework API | FastAPI | OpenAPI automático |
| Base de datos | PostgreSQL 15+ | Transaccional, row-level locking |
| ORM | SQLAlchemy 2.0+ | Async support |
| Migraciones | Alembic | Versionada |
| Testing | pytest + httpx | Test client async |
| Frontend backoffice | Web (separado en `uis/backoffice`) | Consume API REST |

## Decisiones técnicas (del plan)

### Persistencia
- PostgreSQL como única fuente de verdad — ni cache ni tabla de saldo materializado
- Transacciones con `SELECT ... FOR UPDATE` para serializar escrituras por lote
- Movimientos son solo inserción — sin UPDATE/DELETE sobre `movements`
- Clave de solicitud única (`request_key`) para idempotencia en reintentos
- Enteros para unidades — sin saldos fraccionarios

### Arquitectura del servicio (services/api)
```
app/
├── config.py          # Configuración (DB, CORS, etc.)
├── main.py            # FastAPI app entrypoint
├── db/
│   ├── base.py        # Configuración SQLAlchemy
│   └── models.py      # Modelos ORM
├── models/            # Schemas/domain models
├── routers/           # Endpoints REST
│   ├── articles.py
│   └── inventory.py
├── schemas/           # Pydantic schemas
│   └── inventory.py
└── services/          # Lógica de dominio
    └── inventory.py
```

### Concurrencia
- Bloqueo de fila del lote antes de calcular saldo
- Dos salidas concurrentes del mismo lote: máximo una se confirma si el saldo no alcanza para ambas
- Idempotencia vía `request_key` con restricción UNIQUE en PostgreSQL

### Reglas de stock
- `stock = SUM(entradas) - SUM(salidas)` — derivado del diario, nunca almacenado
- Salidas requieren `stock >= quantity` — verificación atómica
- Ajustes: cantidad positiva + dirección (`aumentar`/`reducir`)

## Repositorio

Estructura de monorepo con:
- `services/api/` — Backend del Inventory Manager
- `specs/inventory-manager/` — Spec, plan y tareas
- `uis/backoffice/` — Frontend web
- `agents/` — Agentes de IA
- `skills/` — Skills reutilizables
- `infra/` — Infraestructura
- `packages/` — Paquetes compartidos