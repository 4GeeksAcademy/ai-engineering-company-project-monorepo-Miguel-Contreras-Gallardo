# TrackFlow — Contexto de Empresa

> **Fuente única de verdad para todos los agentes, servicios y prompts del proyecto.**
> _Última actualización: 2026-09-23_

---

## 1. LA EMPRESA

| Dato | Valor |
|---|---|
| **Nombre** | TrackFlow |
| **Sector** | Logística de última milla y gestión de almacenes |
| **Fundación** | 2009 — Los Ángeles, EE.UU. |
| **Mercados** | Estados Unidos y España |
| **Almacenes** | Los Ángeles (EE.UU.) y Zaragoza (España) |
| **Empleados** | ~130 |
| **Facturación** | ~9M€ anuales |
| **CEO** | Thomas Harry (Los Ángeles) |
| **CTO** | Andrés Kim (Zaragoza) |
| **Unidad Tech** | TrackFlow Tech — liderada por Daniel |

### Propuesta de valor
TrackFlow almacena inventario, prepara y empaqueta pedidos, los envía a través de una red de transportistas y gestiona las devoluciones para marcas de e-commerce. Las marcas se centran en vender; TrackFlow se encarga de la logística.

---

## 2. DEPARTAMENTOS

### 🚚 Operaciones de Almacén
- **Responsable:** Ana Whitfield
- **Equipo:** ~70 operarios + 2 responsables de almacén
- **Problemas:**
  - Dos SGA distintos (LA: software comercial, Zaragoza: hoja de cálculo avanzada)
  - Sin visibilidad de inventario en tiempo real a nivel global
  - Pedidos entrantes por email, formatos distintos según cliente, transcripción manual
  - Picking con listas en papel
  - Discrepancias de inventario frecuentes y detección tardía
- **Necesidades:** API de inventario unificada, pipeline de ingesta de pedidos, dashboard de operaciones, alertas de stock bajo

### 📦 Última Milla y Gestión de Transportistas
- **Responsable:** Carlos Vega
- **Equipo:** 6 coordinadores logísticos
- **Problemas:**
  - Asignación manual de transportista por envío
  - Seguimiento obliga a consultar múltiples portales
  - Sin datos históricos de rendimiento (tasa entrega, incidencias, coste/kg)
- **Transportistas:**
  - EE.UU.: UPS, FedEx, DHL
  - España: MRW, SEUR, DHL + 2 transportistas locales
- **Necesidades:** Motor de selección inteligente de transportista, endpoint unificado de tracking, portal público de seguimiento, dashboard de rendimiento

### 🔄 Logística Inversa
- **Responsable:** Sofía Ramos
- **Equipo:** 5 personas
- **Problemas:**
  - 18-25% del volumen son devoluciones (varía por cliente y país)
  - Revisión 100% manual — sin criterios de aprobación automáticos
  - Inspección subjetiva e inconsistente entre operarios
  - Sin visibilidad de patrones de devolución
- **Necesidades:** Motor de aprobación automática con reglas por cliente, flujo automatizado de recogida, inspección asistida por IA (foto → clasificación), dashboard de patrones

### 📞 Experiencia al Cliente (CX)
- **Responsable:** Valentina Cruz
- **Equipo:** 15 agentes (Los Ángeles y Zaragoza)
- **Canales:** Email, WhatsApp, teléfono
- **Tipos de cliente:** B2B (marcas) y B2C (consumidores finales)
- **Problemas:**
  - Sin sistema unificado de tickets
  - ~80% consultas repetitivas (seguimiento, estado devoluciones)
  - Sin base de conocimiento
  - Sin cobertura fuera de horario de oficina
- **Necesidades:** Agente CX automático, base de conocimiento semántica (RAG), sistema de tickets unificado, dashboard en tiempo real, análisis de sentimiento, soporte multiidioma (español + inglés, opcional)

### 🤝 Comercial y Relación con Clientes
- **Responsable:** Miguel Torres
- **Equipo:** 4 account managers + 4 desarrollo de negocio
- **Problemas:**
  - Sin CRM — cuentas en hojas de cálculo personales e hilos de email
  - Informes a clientes mensuales consolidados a mano
  - Sin visibilidad de riesgo de renovación (contratos anuales)
- **Necesidades:** Integración con CRM, informes PDF automáticos, dashboard de salud de cliente con scoring de renovación, alertas a 90 y 30 días, agente comercial para prospección

### 💻 Tecnología
- **Responsable:** Andrés Kim
- **Equipo:** 7 personas (Zaragoza)
- **Problemas:**
  - Arquitectura: dos SGA distintos + ERP (2010) + scripts Python sin documentar
  - Bases de datos en dos proveedores cloud distintos
  - Sin telemetría centralizada
  - Caídas detectadas por WhatsApp
  - Deploys: 1-2 semanas
- **Necesidades:** Telemetría y logging centralizados, pipeline de datos unificado, monitorización con alertas automáticas, agente de documentación técnica, automatización de operaciones

### 📊 Dirección Ejecutiva
- **CEO:** Thomas Harry (Los Ángeles)
- **Problemas:**
  - Informe semanal consolidado manualmente por cada director (3-4h los domingos)
  - Datos con 1-2 días de antigüedad el lunes
  - Sin visión unificada del negocio por país
- **Necesidades:** Dashboard ejecutivo global en tiempo real, informe semanal automático (lunes 7:00 AM), comparativas por país, alertas por umbrales, asistente IA por lenguaje natural

---

## 3. ENTIDADES DEL DOMINIO Y MODELO DE DATOS

```
Cliente (Marca) → Contrato → Pedido → Envío → TrackingEvent
                                            → Devolución → Inspección
                                LíneaPedido → SKU → Inventario (por almacén)

Transportista → Tarifa → Ruta
Consumidor Final → Consulta → Ticket
                                            → Incidencia
Operario / Sistema / Cliente B2B ──────────→ Incidencia
```

| Entidad | Descripción | Campos clave |
|---|---|---|
| **Cliente (Marca)** | Empresa de e-commerce que contrata TrackFlow | id, nombre, pais, contrato_id, scoring_renovacion, fecha_alta |
| **SKU** | Unidad de stock keeping | id, nombre, peso_kg, dimensiones_cm, categoria, valor_unitario |
| **Almacén** | Centro logístico | id, ubicacion (LA/Zaragoza), sga_tipo (comercial/hoja_calculo), capacidad |
| **Inventario** | Stock de un SKU en un almacén | sku_id, almacen_id, cantidad_disponible, stock_minimo, stock_seguridad |
| **Pedido** | Solicitud de envío de una marca | id, cliente_id, fecha_creacion, estado, canal_entrada (email/api), lineas[] |
| **LíneaPedido** | Producto individual dentro de un pedido | id, pedido_id, sku_id, cantidad, precio_unitario |
| **Envío** | Unidad logística hacia un consumidor | id, pedido_id, transportista_id, numero_tracking, estado, destino, peso_kg, urgente |
| **TrackingEvent** | Evento de seguimiento de un envío | envio_id, timestamp, estado, ubicacion, transportista |
| **Devolución** | Producto devuelto por el consumidor | id, envio_id, motivo, estado_aprobacion, estado_inspeccion, fecha_solicitud |
| **Inspección** | Evaluación del producto devuelto | devolucion_id, operario_id, fotos[], clasificacion_ia, dictamen (reacondicionar/desechar) |
| **Transportista** | Empresa de mensajería | id, nombre, pais_operacion, tarifas[], metricas_rendimiento |
| **Ticket** | Consulta de CX | id, origen (email/whatsapp/tel), cliente_tipo (B2B/B2C), estado, resuelto_por_ia, agente_id |
| **Incidencia** | 🆕 Desviación operativa que requiere seguimiento y resolución con auditoría | id, titulo, descripcion, canal, categoria, prioridad, estado, area_asignada, responsable, fechas, audit_log[] |

---

## 4. REGLAS DE NEGOCIO Y RESTRICCIONES

### 4.1 Inventario
- TrackFlow no produce ni vende productos — solo los almacena y gestiona su logística
- El inventario es propiedad de las marcas clientes
- Cada almacén opera de forma independiente; no hay traspaso automático entre almacenes
- Stock mínimo: configurable por SKU y por cliente

### 4.2 Envíos y Transportistas
- 8 transportistas con cobertura en EE.UU. y España
- La asignación debe considerar: destino, peso, urgencia y coste
- Cada transportista tiene su propio sistema de tracking (8 APIs distintas)
- Los envíos urgentes tienen prioridad en la asignación

### 4.3 Devoluciones
- Tasa de devolución: 18-25% del volumen
- La aprobación depende de: motivo, cliente, valor del producto, tiempo desde la compra
- Tras inspección, el producto puede: reacondicionarse (reingresa a inventario) o desecharse
- Cada cliente puede tener reglas de aprobación personalizadas

### 4.4 Atención al Cliente
- Dos perfiles de cliente muy distintos: marcas (B2B) y consumidores finales (B2C)
- Las consultas B2B suelen ser sobre volúmenes, contratos y operativa
- Las consultas B2C son sobre seguimiento de envíos y devoluciones
- Idiomas: español (Zaragoza) e inglés (Los Ángeles)

### 4.5 Comercial
- Contratos anuales con las marcas
- Renovación basada en satisfacción del cliente con la operación logística
- Informes mensuales de rendimiento a clientes (actualmente manuales)

---

## 5. INFRAESTRUCTURA TECNOLÓGICA ACTUAL

| Componente | Descripción |
|---|---|
| **SGA Los Ángeles** | Software comercial de gestión de almacenes |
| **SGA Zaragoza** | Hoja de cálculo avanzada (Excel/Google Sheets) |
| **ERP Corporativo** | Sistema de principios de 2010 |
| **Integraciones** | Scripts Python punto a punto, sin documentar |
| **Bases de datos** | Dos proveedores cloud distintos |
| **Telemetría** | No existe. Caídas detectadas por WhatsApp |
| **Despliegues** | Manuales, 1-2 semanas por funcionalidad |

### Stack objetivo (TrackFlow Tech)
- Backend: Python + FastAPI
- Frontend: Por definir
- Agentes IA: Por definir (LangChain / CrewAI / LangGraph)
- Orquestación: n8n
- Infra: Docker / docker-compose
- Tracking: Integración con 8 APIs de transportistas

---

## 6. OBJETIVOS DEL PROYECTO

1. **Unificar** la visibilidad de inventario entre los dos almacenes
2. **Automatizar** la asignación de transportistas y el seguimiento de envíos
3. **Agilizar** el proceso de devoluciones con reglas automáticas e IA
4. **Resolver** el 80% de consultas de CX automáticamente
5. **Centralizar** la telemetría y monitorización de toda la operación
6. **Proporcionar** inteligencia de negocio en tiempo real al CEO

---

## 7. GLOSARIO

| Término | Definición |
|---|---|
| **Última milla** | Tramo final de la entrega desde el centro logístico hasta el destinatario |
| **SGA** | Sistema de Gestión de Almacenes (WMS en inglés) |
| **SKU** | Stock Keeping Unit — identificador único de producto |
| **Picking** | Proceso de recogida de productos de las estanterías para preparar un pedido |
| **Logística inversa** | Proceso de gestión de devoluciones |
| **RAG** | Retrieval-Augmented Generation — búsqueda semántica + generación de respuesta |
| **MCP** | Model Context Protocol — protocolo para conectar modelos con herramientas externas |
| **n8n** | Plataforma de orquestación y automatización de workflows |
| **Transportista** | Empresa de mensajería que realiza la entrega física |

---

_4Geeks Academy — AI Engineering Track · Proyecto Transversal_
_Documento de contexto de empresa — usar como fuente única de verdad para todos los agentes y servicios_