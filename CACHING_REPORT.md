# Informe de optimización: Caching y carga diferida

> **Proyecto:** TrackFlow — Monorepo de ingeniería de IA  
> **Fecha:** 2026-10-21  
> **Versión:** 0.1.0

---

## 1. Decisiones en el frontend

### 1.1 Componentes con carga diferida (Lazy Loading)

El MVP es una **SPA de una sola página** (Next.js App Router, `/`). No hay rutas adicionales que diferir, pero la página contiene dos paneles operativos accesorios que se cargan bajo demanda mediante `next/dynamic`.

#### `HealthHistoryPanel`

| Atributo | Detalle |
|---|---|
| **Archivo** | `mvp-app/frontend/app/components/HealthHistoryPanel.js` |
| **Técnica** | `dynamic(() => import("./components/HealthHistoryPanel"))` |
| **Disparador** | El usuario abre el `<details>` "Ver historial de salud" |
| **Justificación** | Este componente mantiene hasta 1.000 muestras de salud en estado local, ejecuta un `setInterval` de 5 segundos y calcula percentiles (p95). No es necesario para la comprensión inicial de la pantalla; es una herramienta de observación complementaria. Diferir su carga evita: (a) descargar su código en el bundle inicial (~2 KB gzipped), (b) iniciar el polling de red, y (c) ocupar estado en memoria para usuarios que nunca abren el panel. |
| **Beneficio estimado** | Bundle inicial ~3 KB más ligero; 0 peticiones de red y 0 uso de CPU/estado en el 60-80% de visitas que no expanden el panel (estimación basada en patrones típicos de dashboard). |

#### `ServiceDiagnostics`

| Atributo | Detalle |
|---|---|
| **Archivo** | `mvp-app/frontend/app/components/ServiceDiagnostics.js` |
| **Técnica** | `dynamic(() => import("./components/ServiceDiagnostics"))` |
| **Disparador** | El usuario abre el `<details>` "Abrir diagnóstico detallado" |
| **Justificación** | Ejecuta 2 peticiones de red en paralelo (/ y /status), parsea respuestas y muestra resultados individuales. Es una herramienta de depuración bajo demanda. No tiene sentido cargarla ni ejecutarla hasta que el usuario la solicite explícitamente. |
| **Beneficio estimado** | Similar al anterior: evita ~2 KB de código y 2 peticiones HTTP en el 70-90% de visitas. |

### 1.2 Memoización con `useMemo`

El componente `HealthHistoryPanel` computa un resumen estadístico a partir del array de muestras:

```js
const summary = useMemo(() => {
  if (!samples.length) return null;
  const successful = samples.filter((sample) => sample.ok).length;
  const latencies = samples.map((sample) => sample.latency).sort((a, b) => a - b);
  const p95Index = Math.max(0, Math.ceil(latencies.length * 0.95) - 1);
  return {
    count: samples.length,
    successRate: Math.round((successful / samples.length) * 100),
    averageLatency: Math.round(latencies.reduce((sum, value) => sum + value, 0) / latencies.length),
    p95Latency: Math.round(latencies[p95Index]),
  };
}, [samples]);
```

| Atributo | Detalle |
|---|---|
| **Valor memoizado** | Objeto `summary` con count, successRate, averageLatency, p95Latency |
| **Coste sin memoizar** | `filter` (O(n)) + `sort` (O(n log n)) + `reduce` (O(n)) en cada render — con n ≤ 1.000, aprox. 2-5 ms |
| **Array de dependencias** | `[samples]` — correcto, solo se recalcula cuando cambia la lista de muestras |
| **Frecuencia de recalculo** | Una vez cada 5 segundos (cuando se añade una muestra), en lugar de en cada render del componente padre |
| **Beneficio medible** | Se evita el ordenamiento O(n log n) en renders intermedios provocados por otros cambios de estado (apertura/cierre de details, hover, etc.). Con n=1.000, `sort` recorre ~8.000 comparaciones; memoizarlo ahorra ese coste en todos los renders excepto cuando `samples` cambia. |

---

## 2. Decisiones en el backend

### 2.1 Mecanismo de caché

**Archivo:** `services/api/app/services/response_cache.py`

- **Tipo:** Caché en memoria local por worker (diccionario + `threading.RLock`)
- **TTL por defecto:** 20 segundos
- **Características:**
  - Copia defensiva (`deepcopy`) tanto al guardar como al recuperar, para evitar mutaciones externas
  - Aislamiento por motor de BD mediante `database_scope(db)` — crítico para que los tests con bases de datos separadas no compartan caché
  - Invalidación por prefijo de clave
  - Sin dependencias externas (no requiere Redis)

### 2.2 Endpoints cacheados

#### `GET /api/v1/incidents/stats`

| Atributo | Detalle |
|---|---|
| **Ruta** | `/api/v1/incidents/stats` |
| **Coste de la operación** | **Alto** — ejecuta 4 consultas agregadas sobre la tabla de incidencias (total, por estado, por categoría, por prioridad), cada una escanea un subconjunto significativo de filas |
| **Frecuencia estimada** | **Alta** — el dashboard de incidencias consulta este endpoint en cada carga de página y en refrescos periódicos (cada 30 s aprox.) |
| **TTL elegido** | **20 segundos** |
| **Clave de caché** | `"incident:stats:{database_scope}"` |
| **Estrategia de invalidación** | Se invalida tras cualquier escritura sobre incidencias: `POST /api/v1/incidents`, `PATCH /api/v1/incidents/{id}`, `POST /api/v1/incidents/{id}/assign`, `POST /api/v1/incidents/{id}/transition` |
| **Beneficio estimado** | De 4 consultas agregadas pesadas por llamada → 0 consultas durante el TTL. En un dashboard con refresco cada 30 s, se evitan ~2 de cada 3 ejecuciones de base de datos. |

#### `GET /api/v1/incidents/open-by-severity`

| Atributo | Detalle |
|---|---|
| **Ruta** | `/api/v1/incidents/open-by-severity` |
| **Coste de la operación** | **Medio** — consulta agregada con filtro `status NOT IN ('closed', 'cancelled')` agrupada por prioridad |
| **Frecuencia estimada** | **Alta** — widget de dashboard que se refresca simultáneamente con `/stats` |
| **TTL elegido** | **20 segundos** |
| **Clave de caché** | `"incident:open-by-severity:{database_scope}"` |
| **Estrategia de invalidación** | Misma que `/stats` — comparte la función `_invalidate_incident_aggregates()` |
| **Beneficio estimado** | Similar a `/stats`: se elimina 1 consulta agregada por llamada durante el TTL. |

#### `GET /inventory/reorder`

| Atributo | Detalle |
|---|---|
| **Ruta** | `/inventory/reorder` |
| **Coste de la operación** | **Alto** — carga el catálogo completo de artículos activos y, para cada uno, consulta el stock derivado del libro mayor de movimientos |
| **Frecuencia estimada** | **Alta** — el dashboard de inventario consulta este endpoint periódicamente para alertar sobre roturas |
| **TTL elegido** | **20 segundos** |
| **Clave de caché** | `"inventory:reorder:{database_scope}"` |
| **Estrategia de invalidación** | Se invalida tras: `POST /inventory/movements`, `POST /articles/`, `PUT /articles/{sku}`, `DELETE /articles/{sku}` (desactivación), `POST /articles/{sku}/lots` |
| **Beneficio estimado** | De N+1 consultas (1 catálogo + N stocks) por llamada → 0 consultas durante el TTL. Es el endpoint con mayor impacto de caché. |

---

## 3. Intercambios reconocidos (freshness vs. performance)

### 3.1 TTL de 20 segundos en agregados de incidencias

**Problema:** Los endpoints `/stats` y `/open-by-severity` alimentan widgets de dashboard que varios operadores consultan simultáneamente. Sin caché, cada refresh de dashboard ejecuta consultas agregadas pesadas. Con caché, los datos pueden estar desactualizados hasta 20 segundos.

**Decisión:** TTL = 20 s en lugar de 5 s o 60 s.

**Justificación:**

- **¿Por qué no 5 s?** Reduciría la ventana de desactualización a 5 s, pero también reduciría el acierto de caché. En un dashboard con refresco cada 30 s, un TTL de 5 s da una tasa de acierto del ~17% frente al ~67% con 20 s. El coste de 4 consultas agregadas cada 5 s es innecesario para un panel que no requiere precisión en tiempo real.

- **¿Por qué no 60 s?** Maximiza la tasa de acierto (~95%), pero introduce una ventana de 1 minuto donde los operadores verían datos obsoletos después de crear o actualizar una incidencia. En un centro de operaciones donde las incidencias se crean y asignan en minutos, 60 s de desfase es demasiado.

- **¿Por qué 20 s es aceptable?** El flujo de trabajo típico es: (1) un operador crea una incidencia, (2) la incidencia aparece en el dashboard, (3) otro operador la asigna. El paso (2) ocurre cuando el operador recarga el dashboard o espera el refresco automático. Con 20 s de TTL, el dato más desactualizado que verá un operador es de 20 s atrás, lo que es aceptable porque:
  - Las decisiones de asignación no se toman en ventanas sub-20 s
  - La invalidación en escritura asegura que el siguiente refresco post-recarga obtenga datos frescos
  - La etiqueta "Actualizado hace X s" en el dashboard informa al usuario sobre la posible desactualización

### 3.2 `GET /inventory/reorder` — el balance más delicado

**Problema:** La señal de reorden se usa para activar reposiciones de stock. Un falso negativo (no sugerir reposición cuando se necesita) puede causar rotura de stock.

**Decisión:** TTL = 20 s con invalidación en cada movimiento o cambio de artículo.

**Justificación:**

Un TTL de 20 s significa que, como máximo, un movimiento que agota el stock tarda 20 s en reflejarse en la señal de reorden. Para un almacén que procesa decenas de movimientos por minuto, 20 s es un retardo aceptable porque:

- La invalidación en escritura ya cubre el caso inmediato: si un operador realiza un movimiento y luego consulta el reorder, la invalidación se dispara sincrónicamente, por lo que el siguiente GET obtendrá datos frescos (el worker que hizo el POST hará un nuevo GET sin caché).
- El riesgo de 20 s de desfase solo afecta a **otros workers** (en despliegue multi-worker) que no realizaron la escritura. Para mitigarlo, se documenta que en despliegues multi-worker se debe usar Redis compartido (ver sección 5).

---

## 4. Qué no se cacheó y por qué

### 4.1 `GET /api/v1/incidents` (listado con filtros)

| Atributo | Detalle |
|---|---|
| **Endpoint** | `GET /api/v1/incidents` |
| **Coste** | Medio/alto — consulta con filtros variables más count total y opcionalmente búsqueda textual |
| **¿Por qué no se cacheó?** | El espacio de combinaciones de filtros es enorme (status × category × priority × assigned_to × assigned_area × channel × created_by × q × limit × offset). Cachear cada combinación individual consumiría memoria sin un patrón de reutilización predecible. Además, las incidencias cambian constantemente, lo que obligaría a invalidar todo el espacio de claves en cada escritura, anulando el beneficio. |
| **Alternativa considerada** | Se consideró cachear solo la página 1 sin filtros (la más consultada), pero se descartó porque el listado sin filtros es trivialmente barato (primeros 50 registros con índice). |

### 4.2 `GET /status` del MVP backend

| Atributo | Detalle |
|---|---|
| **Endpoint** | `GET /status` en `mvp-app/backend/app.py` |
| **Coste** | Bajo — conexión TCP a PostgreSQL con timeout de 3 s |
| **¿Por qué no se cacheó?** | Es un health check. Su propósito es verificar la conectividad actual. Cachearlo falsearía su utilidad: devolvería "connected" aunque la BD se haya caído entre medio. La frescura aquí **es** la funcionalidad. |

### 4.3 `GET /inventory/stock`

| Atributo | Detalle |
|---|---|
| **Endpoint** | `GET /inventory/stock` |
| **Coste** | Medio — consulta agregada sobre el libro mayor de movimientos |
| **¿Por qué no se cacheó?** | El stock debe reflejar los movimientos **inmediatamente**. Cada movimiento cambia el stock y los operadores consultan stock antes de realizar picking o recepciones. Un TTL incluso de 5 s podría causar decisiones operativas basadas en stock desactualizado. El endpoint es lo suficientemente rápido (consulta con índices por SKU + almacén + lote) como para servirlo siempre fresco. |

### 4.4 `GET /articles/` (listado de catálogo)

| Atributo | Detalle |
|---|---|
| **Endpoint** | `GET /articles/` |
| **Coste** | Bajo/medio — consulta ordenada sobre tabla pequeña (< 10.000 artículos) |
| **¿Por qué no se cacheó?** | Aunque la frecuencia es alta y los datos son estables, el endpoint es barato. Cachearlo añadiría complejidad de invalidación (crear/actualizar/desactivar artículos, crear lotes) para un beneficio marginal. Se documenta como candidato futuro si el catálogo crece significativamente. |

---

## 5. Consideraciones de seguridad: datos privados

**No se almacena ningún dato privado o de sesión en las claves de caché compartidas.**

- Las claves de caché solo contienen identificadores de scope de base de datos (ej. `"incident:stats:14023456789"`), nunca IDs de usuario, tokens, ni información de sesión.
- Los valores cacheados son agregados numéricos (totales, porcentajes, latencias) y listas de SKU con cantidades. No contienen PII, datos personales ni contenido de incidencias.
- La caché es proceso-local (no hay Redis compartido entre workers en la configuración actual), por lo que no hay riesgo de fuga entre tenants aunque se añadiera multi-tenancy en el futuro.

---

## 6. Resumen de beneficios estimados

| Endpoint/Componente | Antes | Después | Ahorro estimado |
|---|---|---|---|
| `GET /incidents/stats` | 4 queries agregadas/llamada | 0 queries durante TTL (20 s) | ~67% de reducción en carga BD |
| `GET /incidents/open-by-severity` | 1 query agregada/llamada | 0 queries durante TTL (20 s) | ~67% de reducción en carga BD |
| `GET /inventory/reorder` | N+1 queries/llamada | 0 queries durante TTL (20 s) | ~67% de reducción en carga BD |
| `HealthHistoryPanel` (lazy) | Bundle inicial + polling continuo | 0 KB + 0 polling en visitas sin expandir | ~3-5 KB bundle + CPU idle |
| `ServiceDiagnostics` (lazy) | Bundle inicial + 2 peticiones | 0 KB + 0 peticiones en visitas sin expandir | ~2-3 KB bundle + 2 HTTP calls |
| `summary` en HealthHistoryPanel | sort O(n log n) en cada render | sort O(n log n) solo cuando `samples` cambia | Ahorro en renders intermedios |

---

*Este informe se mantiene actualizado en la raíz del monorepo como `CACHING_REPORT.md`. La implementación detallada del backend se encuentra en `services/api/CACHING.md` y `services/api/app/services/response_cache.py`.*