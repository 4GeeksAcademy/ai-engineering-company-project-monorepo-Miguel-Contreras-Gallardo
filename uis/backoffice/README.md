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

## Stack

- HTML semántico con vistas intercambiables
- CSS con variables de diseño, grid y estados visuales
- JavaScript vanilla con navegación SPA-like
- Lucide icons vía CDN
- Consume API REST en `/api/v1/` endpoints
