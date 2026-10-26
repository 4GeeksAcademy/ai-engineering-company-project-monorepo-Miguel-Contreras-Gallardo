# TrackFlow Backoffice

Panel operativo interno con tres vistas:

- **Dashboard** — Pantalla de inicio con datos de la empresa, departamentos y estado de la API
- **Inventario** — Gestión de artículos, lotes y movimientos con señal de reorden (consumiendo API REST)
- **Empresa** — Información de TrackFlow (equipo directivo, datos clave) extraída de la documentación interna

## Datos de empresa visibles en la interfaz

Los datos del dashboard y la vista Empresa se cargan directamente del archivo `COMPANY_DATA` en `app.js`, extraídos del briefing corporativo (`CONTEXT.md`):

- Equipo directivo con nombres y roles
- Departamentos con responsables
- Métricas clave (130+ empleados, 9M€ facturación, 2 almacenes, 8 transportistas)

## Ejecución local

Con la API disponible en `http://localhost:8000`:

```bash
python -m http.server 5173
```

Ejecutar el comando desde esta carpeta y abrir `http://localhost:5173`.

## Telemetría

El servicio `src/services/telemetry.js` expone `window.track(eventType, properties)` y envía eventos en lotes al endpoint configurado. En esta aplicación HTML/JS estática, configura `NEXT_PUBLIC_TELEMETRY_ENDPOINT` mediante `window.__TRACKFLOW_CONFIG__` o el meta tag del `index.html` (el valor local predeterminado apunta al endpoint temporal de FastAPI).

Cuando se incorpore autenticación, el login debe comunicar al servicio el ID seudónimo del usuario autenticado (nunca email/nombre) con `window.dispatchEvent(new CustomEvent("trackflow:login", { detail: { userId: "<opaque-user-id>" } }))`. El servicio genera una sesión UUID nueva en memoria. Para logout, emitir `window.dispatchEvent(new Event("trackflow:logout"))`.

El servicio también expone hooks centrales para el futuro proveedor de autenticación: `trackflow:login_failed` con `detail.reason` estrictamente igual a `invalid_credentials` o `network_error`, y `trackflow:session_expired` sin datos de usuario. El servicio ignora razones no admitidas y no reenvía propiedades arbitrarias del evento. Nunca incluir email, contraseña, token, mensaje de error ni datos libres. La UI actual no tiene formulario ni sesión autenticada real, por lo que estos eventos no se generan hasta conectar una fuente real.

El capturador vanilla equivale al patrón `reportWebVitals` de Next.js mediante `PerformanceObserver`: mide TTFB, FCP, LCP, CLS e INP cuando el navegador los soporta, emite una sola medición final disponible por métrica y página y envía al ocultar/salir de la página. `pageRoute` solo puede ser `/`, `/inventory`, `/company` o `/other`; no se usa `location.href` ni se adjuntan query strings o hashes. Las mediciones no son KPIs de negocio y el endpoint actual no las persiste.

La interfaz instrumenta las vistas existentes (`dashboard`, `inventory`, `company`), las interacciones de inventario, latencia de llamadas a la API, errores técnicos sanitizados y Web Vitals. Las rutas de API se normalizan antes de medirlas (sin query strings ni SKU) y los errores no incluyen mensaje ni stack. El umbral para la señal de petición lenta es `window.__TRACKFLOW_CONFIG__.API_SLOW_REQUEST_MS` (3.000 ms por defecto). La emisión de telemetría no persiste los eventos todavía: el endpoint local responde con el conteo recibido.

Este backoffice no es productor de eventos de envíos, picking, devoluciones, CX, informes, despliegues, SLA de negocio, stock agotado ni salud de cliente. Esos KPIs deben instrumentarse en sus fuentes transaccionales/monitor autoritativo; no se deben simular desde las pantallas de inventario.

## Stack

- HTML semántico con vistas intercambiables
- CSS con variables de diseño, grid y estados visuales
- JavaScript vanilla con navegación SPA-like
- Lucide icons vía CDN
- Consume API REST en `/api/v1/` endpoints
