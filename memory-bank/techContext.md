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
| Frontend corporativo | Web (separado en `uis/website`) | Sitio corporativo |
| Iconos | Lucide (CDN v0.468.0) | Helper compartido en `uis/shared/lucide-helper.js` |
| Fuentes | Google Fonts (DM Sans + IBM Plex Mono) | `display=swap` en URL |
| Serving estático | serve ^14.2.0 | npm package en `uis/` |

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

## Infraestructura Docker

El proyecto incluye un stack Docker completo para desarrollo local y producción:
- **docker-compose.yml** en raíz del repo (servicios: `postgres`, `api`, `uis`)
- `backend/Dockerfile` — Dockerfile alternativo independiente (Python 3.13-slim + uv)
- Red propia `trackflow-net` para comunicación entre contenedores
- Volumen `trackflow_pgdata` para persistencia de PostgreSQL

### Servicios
| Servicio | Contenedor | Puerto | Dockerfile |
|---|---|---|---|
| PostgreSQL 16 | `trackflow-db` | 5432 | Imagen oficial `postgres:16-alpine` |
| API FastAPI | `trackflow-api` | 8000 | `services/Dockerfile` (Python 3.12-slim + uv) |
| UIs (website + backoffice) | `trackflow-uis` | 3000, 3001 | `uis/Dockerfile` (Node 20-alpine + serve) |

### Alternativos
| Archivo | Propósito |
|---|---|
| `backend/Dockerfile` | Dockerfile alternativo para backend (Python 3.13-slim + uv) |
| `.env.example` | Plantilla de variables de entorno (11 variables documentadas) |

### Despliegue en producción
```bash
# En VPS (Ubuntu 22.04)
docker-compose up --build -d
```

**Producción:** `207.154.214.100` vía Nginx reverse proxy:
- `http://207.154.214.100` → Website (localhost:3000)
- `http://207.154.214.100/backoffice` → Backoffice (localhost:3001)
- `http://207.154.214.100/api` → API (localhost:8000)

## Repositorio

Estructura de monorepo con:
- `services/api/` — Backend del Inventory Manager
- `specs/inventory-manager/` — Spec, plan y tareas
- `uis/backoffice/` — Frontend web
- `agents/` — Agentes de IA
- `skills/` — Skills reutilizables
- `infra/` — Infraestructura
- `packages/` — Paquetes compartidos