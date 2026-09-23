# 📋 Project Brief — TrackFlow AI Platform

> **Última actualización:** 2026-09-23
> **Proyecto:** Plataforma de Automatización e IA para TrackFlow (4Geeks Academy — AI Engineering)
> **Este documento es la fuente única de contexto del proyecto. Léalo siempre antes de empezar a trabajar.**

---

## 🏢 1. CONTEXTO DE PRODUCTO Y NEGOCIO

### 1.1 La Empresa

**TrackFlow** es una empresa de logística de última milla y gestión de almacenes fundada en 2009 en **Los Ángeles, EE.UU.** Opera en dos mercados (EE.UU. y España) con almacenes en **Los Ángeles** y **Zaragoza**. Cuenta con ~130 empleados y factura ~9M€ anuales.

**CEO:** Thomas Harry (Los Ángeles) · **CTO:** Andrés Kim (Zaragoza)

### 1.2 Propuesta de Valor

TrackFlow almacena inventario, prepara y empaqueta pedidos, los envía a través de una red de transportistas y gestiona las devoluciones para marcas de e-commerce. Las marcas se centran en vender; TrackFlow se encarga de que los productos lleguen al cliente.

### 1.3 Estructura Organizativa y Problemas

| Departamento | Responsable | Equipo | Problema principal |
|---|---|---|---|
| 🚚 Operaciones de Almacén | Ana Whitfield | ~70 operarios + 2 jefes de almacén | Sin visibilidad de inventario en tiempo real. Dos SGA distintos (LA: software comercial, Zaragoza: hoja de cálculo). Picking en papel. Pedidos entrantes por email transcritos manualmente. |
| 📦 Última Milla y Transportistas | Carlos Vega | 6 coordinadores logísticos | Asignación manual de transportista por envío. Tracking en múltiples portales. 8 transportistas (UPS, FedEx, DHL, MRW, SEUR + locales). Sin datos históricos de rendimiento. |
| 🔄 Logística Inversa | Sofía Ramos | 5 personas | 18-25% del volumen son devoluciones. Revisión 100% manual. Inspección subjetiva e inconsistente. Sin visibilidad de patrones de devolución. |
| 📞 Experiencia al Cliente (CX) | Valentina Cruz | 15 agentes (LA + Zaragoza) | 80% consultas repetitivas. Sin sistema de tickets unificado. Sin base de conocimiento. Sin cobertura fuera de horario. B2B y B2C sin diferenciación. |
| 🤝 Comercial y Relación Clientes | Miguel Torres | 4 account managers + 4 biz dev | Sin CRM. Informes a clientes mensuales hechos a mano. Sin visibilidad de riesgo de renovación. Contratos anuales. |
| 💻 Tecnología | Andrés Kim | 7 personas (Zaragoza) | Arquitectura patchwork. Sin telemetría centralizada. Deploys de 1-2 semanas. Caídas detectadas por WhatsApp. |
| 👔 Dirección Ejecutiva | Thomas Harry | — | Informe semanal consolidado manualmente (horas cada domingo). Datos con 1-2 días de retraso. |

### 1.4 Entidades del Dominio (Modelo de Datos Conceptual)

```
Cliente (Marca) → Contrato → Pedido → Envío → TrackingEvent
                                            → Devolución → Inspección
                                LíneaPedido → SKU → Inventario (por almacén)

Transportista → Tarifa → Ruta
Cliente (Consumidor Final) → Consulta → Ticket
                                            → Incidencia
Operario / Sistema / Cliente B2B ──────────→ Incidencia
```

| Entidad | Descripción | Atributos clave |
|---|---|---|
| `Cliente (Marca)` | Empresa de e-commerce que contrata TrackFlow | id, nombre, pais, contrato, scoring_renovacion |
| `SKU` | Unidad de stock | id, nombre, peso, dimensiones, categoria |
| `Almacén` | Centro logístico | id, ubicacion (LA/Zaragoza), SGA_tipo |
| `Inventario` | Stock de un SKU en un almacén | sku_id, almacen_id, cantidad, stock_minimo |
| `Pedido` | Solicitud de envío de un cliente | id, cliente_id, estado, fecha, líneas |
| `Envío` | Unidad logística hacia un destinatario | id, pedido_id, transportista_id, tracking_num, estado, destino |
| `TrackingEvent` | Evento de seguimiento de un envío | envio_id, timestamp, estado, ubicacion |
| `Devolución` | Producto devuelto por el consumidor | id, envio_id, motivo, estado_aprobacion, estado_inspeccion |
| `Transportista` | Empresa de mensajería | id, nombre, pais, tarifas, metricas_rendimiento |
| `Ticket` | Consulta de CX | id, origen (email/whatsapp/tel), cliente_tipo, estado, resolucion_automatica |
| `Incidencia` | 🆕 Desviación operativa que requiere seguimiento, resolución y auditoría | id, título, canal, categoría, prioridad, estado, área_asignada, audit_log[] |

### 1.5 Flujos de Proceso de Negocio Clave

**① Recepción de Pedido → Despacho**
```
Email cliente → Parseo automático → Asignación almacén → Picking → Empaquetado → 
Asignación transportista → Generación etiqueta → Recogida → En tránsito
```

**② Devolución**
```
Solicitud consumidor → Aprobación automática (reglas) → Etiqueta devolución → 
Recogida transportista → Inspección (IA asiste) → Reacondicionar / Desechar → 
Reingreso inventario
```

**③ Consulta Cliente**
```
Consulta (email/WhatsApp/tel) → Clasificación automática → 
  - Seguimiento: respuesta automática con tracking
  - Devolución: estado + instrucciones
  - Otra: escalado a agente humano
```

### 1.6 KPIs y Métricas de Éxito del Negocio

| KPI | Objetivo | Situación actual |
|---|---|---|
| Tasa entrega a tiempo | >97% | Sin datos estructurados |
| Tiempo picking por pedido | <15 min | Sin medición |
| Tasa devoluciones | 18-25% (referencia) | Sin análisis de causa raíz |
| Resolución automática CX | >60% | 0% (todo manual) |
| Frescura datos informe CEO | Tiempo real | 1-2 días de retraso |
| Coste por kg enviado | Sin target | Sin datos por transportista |
| Tiempo deploy nueva feature | <1 día | 1-2 semanas |

---

## 🧠 2. STACK TECNOLÓGICO

| Capa | Tecnología | Estado |
|---|---|---|
| Backend API | **Python — FastAPI** | 📌 Por implementar |
| Frontend | Por definir | ❓ Pendiente decisión |
| Agentes IA | LangChain / CrewAI / LangGraph | ❓ Pendiente decisión |
| Skills/Capacidades | Módulos Python reutilizables | 📌 Template SKILL.md vacío |
| Orquestación workflows | **n8n** | 📌 Sin implementar |
| Datos | CSV → Pipelines → Procesado → Evaluación | 📌 Sin implementar |
| Infraestructura | **Docker / docker-compose** | 📌 Sin implementar |
| Tipos TypeScript | TypeScript (`@repo/shared-types`) | ✅ Esqueleto creado (`Id`, `BaseEntity`) |
| Tipos Python | Carpeta `shared/` (raíz) | 📁 Solo READMEs — pendiente definir relación con `packages/shared/` |
| Control de versiones | Git + GitHub | ✅ Rama activa: `feature/incident-manager` |

### Entorno de desarrollo (Devcontainer)
El proyecto incluye un contenedor de desarrollo preconfigurado en `.devcontainer/`:
- **Imagen:** `mcr.microsoft.com/devcontainers/universal:2`
- **Gestor paquetes Python:** `uv` (configurado en post-create.sh con `uv sync`)
- **Extensiones VS Code:** Python, Pylance, Jupyter, Docker, ESLint, Prettier, ErrorLens, GitLens, 4Geeks Student
- **⚠️ Pendiente:** Crear `pyproject.toml` para que `uv sync` funcione correctamente

### Dependencias pendientes de decidir
- Framework de agentes: LangChain vs CrewAI vs LangGraph
- Frontend: Streamlit, Gradio, React, Next.js...
- Base de datos: PostgreSQL, SQLite...
- CRM: Integración con API externa vs construcción propia

---

## 🏛️ 3. ESTRUCTURA DEL MONOREPO

| Carpeta | Propósito | Estado actual |
|---|---|---|
| `agents/` | Agentes de IA + tools + rules | 📁 Template + READMEs |
| `services/` | Backend FastAPI centralizado | 📁 Solo READMEs — pendiente Fase 1 Incidencias |
| `uis/` | Interfaces de usuario | 📁 Solo READMEs |
| `data/` | raw/ → pipelines/ → process/ → eval/ | 📁 Solo READMEs |
| `skills/` | Capacidades reutilizables | 📁 Template + script ejemplo |
| `workflows/` | Flujos n8n | 📁 Solo READMEs |
| `mcps/` | Servidores MCP | 📁 Solo READMEs |
| `packages/shared/` | Tipos TypeScript compartidos | ⚡ `index.ts` con tipos base |
| `memory-bank/` | Trazabilidad del proyecto ⭐ | ✅ Activo (6 docs, incluido plan incidencias) |
| `infra/`, `scripts/`, `internal/` | Operaciones | 📁 Solo READMEs |
| `docs/` | Documentación | 📁 Solo READMEs |

---

## 🌱 4. ESTADO ACTUAL DEL PROYECTO (Fase 0)

### ¿Qué está hecho?
- ✅ Análisis completo del briefing de TrackFlow
- ✅ Elección de TrackFlow como empresa (`company-choice.md`)
- ✅ Rama `feature/incident-manager` creada a partir de `main`
- ✅ Estructura del monorepo creada (plantilla 4Geeks)
- ✅ `CONTEXT.md` — Fuente única de verdad de TrackFlow
- ✅ `memory-bank/` con trazabilidad completa (6 documentos: project-brief, active-context, progress, decisions, system-patterns, audit)
- ✅ **`incident-manager-plan.md`** — Plan completo del gestor de incidencias (modelo datos, estados, auditoría, API, fases) 🆕
- ✅ `.devcontainer/` con entorno containerizado (imagen universal, `uv`, extensiones)
- ✅ Tipos base en `packages/shared/types/index.ts`
- ✅ Template de agente (`agents/_template/agent.py`)
- ✅ Template de skill (`skills/_template/` — aunque SKILL.md vacío)
- ✅ Script ejemplo de data analysis (`skills/data-analysis/scripts/pandas_clean.py`)

### ¿Qué falta? (Roadmap)
| Prioridad | Tarea | Impacto | Notas |
|---|---|---|---|
| 🔴 P0 | Crear `pyproject.toml` para que `uv sync` funcione | Reproducibilidad | El devcontainer ya ejecuta `uv sync` pero falla (D02) |
| 🔴 P0 | Decidir futuro de rama `feature/incident-manager` | Gobernanza | D01: nombre vs alcance del proyecto |
| 🔴 P0 | Configurar `.gitignore` | Seguridad | Archivo no existe actualmente |
| 🔴 P0 | Poblar `skills/_template/SKILL.md` | Consistencia | Template vacío (0 bytes, D05) |
| 🟡 P1 | **Fase 1 Gestor Incidencias:** FastAPI + SQLAlchemy + PostgreSQL + audit trail 🆕 | Backend | Primer servicio real, priorizado tras P0 |
| 🟡 P1 | Crear carpeta `agents/rules/` + system prompts (x7 deptos) | Base agentes | D06: documentado pero carpeta no existe |
| 🟡 P1 | Configurar `docker-compose.yml` con PostgreSQL + API | Entorno local | Necesario para la Fase 1 |
| 🟢 P2 | Pipeline de ingesta de pedidos | Datos |
| 🟢 P2 | API de inventario unificado | Primer endpoint real |
| 🟢 P2 | Base de conocimiento para RAG (CX) | Agente CX |
| 🔵 P3 | Agente orquestador multi-departamento | Visión final |

### Documentos fundacionales del proyecto
| Documento | Propósito | Estado |
|---|---|---|
| `company-choice.md` | Justificación de elección de TrackFlow + visión del agente orquestador | ✅ Original del alumno |
| `CONTEXT-trackflow-briefing.md` | Briefing original proporcionado por 4Geeks | ✅ Histórico |
| `CONTEXT.md` | Fuente única de verdad normalizada para agentes y servicios | ✅ Creado y commitado |
| `memory-bank/` | Trazabilidad del proyecto | ✅ Activo |

### Notas de auditoría
> Existe un documento `memory-bank/audit.md` con el análisis detallado de discrepancias entre la documentación y la realidad del repositorio. Se recomienda revisarlo antes de cada sesión para priorizar correcciones.

### Alineación con hitos del curso
| Hito | Módulo | Cómo se aplica a TrackFlow |
|---|---|---|
| Web | HTML/CSS/JS | Landing corporativa + portal tracking público |
| Programación | Python | Lógica de negocio, pipelines, API |
| Backend | FastAPI | API centralizada de inventario, pedidos, tracking |
| Telemetría | Monitoreo | Dashboards operativos + alertas |
| RAG | Búsqueda semántica | Base de conocimiento CX + agente de consultas |
| Agentes | Frameworks IA | Agente orquestador + agentes departamentales |
| Workflows | n8n | Automatización multi-sistema |
| Tiempo real | WebSockets | Tracking en vivo, dashboards en tiempo real |