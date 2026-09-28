# Project Brief — TrackFlow Inventory Manager

## Empresa

**TrackFlow** es una empresa de logística de última milla y gestión de almacenes fundada en 2009 en Los Ángeles, Estados Unidos. Opera en dos mercados — Estados Unidos y España — con almacenes en Los Ángeles y Zaragoza. Cuenta con ~130 empleados y factura ~9M€ anuales.

## Problema

TrackFlow carece de una vista unificada de inventario entre sus dos almacenes. Los sistemas actuales (SGA comercial en LA, hoja de cálculo avanzada en Zaragoza) no se comunican. Los pedidos entrantes llegan por email en formatos distintos y se transcriben manualmente. No hay visibilidad en tiempo real del stock global.

## Solución

**Inventory Manager** — un servicio backend unificado que:

- Centraliza el catálogo de artículos, almacenes y lotes
- Registra movimientos de entrada, salida y ajuste de forma inmutable
- Deriva el stock exclusivamente del diario de movimientos (nunca editable directamente)
- Expone una API REST para consulta y registro
- Incluye un backoffice operativo con señal visual de reorden

## Stack técnico

- **Backend**: Python + FastAPI + PostgreSQL
- **Frontend**: Backoffice web (separado en `uis/backoffice`)
- **Base de datos**: PostgreSQL como fuente de verdad con transacciones y bloqueo de filas
- **ORM/DB**: SQLAlchemy + Alembic para migraciones

## Departamentos involucrados

- **Operaciones de Almacén** — Ana Whitfield — uso principal del sistema
- **Tecnología** — Andrés Kim (CTO) — equipo que mantiene el servicio
- **Última Milla** — Carlos Vega — consumidor de datos de inventario

## Estado actual

Servicio API implementado parcialmente con migraciones, modelos, routers y servicios. Ver `services/api/` y `specs/inventory-manager/` para detalles.

## Enlaces

- [Spec](specs/inventory-manager/spec.md)
- [Plan técnico](specs/inventory-manager/plan.md)
- [Tareas](specs/inventory-manager/tasks.md)
- [API Service](services/api/)
- [Backoffice](uis/backoffice/)