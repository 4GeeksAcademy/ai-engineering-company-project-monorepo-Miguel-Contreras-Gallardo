# 📊 Auditoría Inicial — Lighthouse & Análisis de Código

> **Fecha:** 2026-10-18
> **Proyecto:** TrackFlow
> **Frontends auditados:** `uis/website/` (sitio corporativo) · `uis/backoffice/` (panel de operaciones)
> **Entorno:** `serve` (producción) en localhost:3000 y localhost:3001
> **Herramienta:** Lighthouse v12+ · Chromium 149 headless

---

## 1. Resultados Lighthouse

### 1.1 Website corporativo (`http://localhost:3000`)

| Modo | Rendimiento | Accesibilidad | Buenas Prácticas | SEO |
|---|---|---|---|---|
| **Escritorio** | 99 | 87 | 100 | 91 |
| **Móvil** | 94 | 91 | 100 | 91 |

### 1.2 Backoffice (`http://localhost:3001`)

| Modo | Rendimiento | Accesibilidad | Buenas Prácticas | SEO |
|---|---|---|---|---|
| **Escritorio** | 92 | 95 | 96 | 82 |
| **Móvil** | 71 | 95 | 96 | 82 |

### 1.3 Observaciones

- **Website**: Rendimiento excelente en ambos modos. La puntuación de SEO (91) se debe a que `robots.txt` y `llms.txt` existen pero Lighthouse detecta que podrían mejorarse las meta-etiquetas sociales (Open Graph / Twitter Cards).
- **Backoffice móvil (71)**: La puntuación baja se debe a que no está diseñado responsive para móvil en todas sus vistas (el backoffice es una herramienta interna de operaciones, pensada para escritorio).
- **Backoffice SEO (82)**: Al ser una herramienta interna, las metas sociales no aplican. Lighthouse penaliza por no tener `meta description` y etiquetas Open Graph, que no son necesarias para un backoffice.
- **Accesibilidad (website 87)**: El contraste de algunos textos decorativos y la falta de `aria-label` en ciertos iconos afectan la puntuación. Candidato a mejora.

---

## 2. Análisis de Código — Oportunidades de Refactorización

### 🟡 Caso 1: Inicialización de Lucide Icons (patrón repetido en ambos frontends)

**Dónde aparece:**

- `uis/website/app.js` — Llamado en `DOMContentLoaded` y después de cada toggle de menú móvil (2 lugares).
- `uis/backoffice/app.js` — Llamado después de `renderDashboard()`, `renderTable()`, `checkApiStatus()`, `openEditArticle()`, `openNewArticle()` y otras funciones que inyectan HTML dinámico (al menos 5 lugares).

**Por qué es candidato a refactorización:**

Cada vez que se inyecta HTML que contiene `<i data-lucide="..."></i>`, hay que llamar a `lucide.createIcons()` para que Lucide reemplace esos marcadores por SVG. Esto ocurre de forma dispersa y manual en ambos frontends. Si se olvida una llamada, los iconos no se renderizan.

**Cómo quedaría la abstracción compartida:**

```js
// shared/lucide-utils.js
// Función helper que refresca los iconos Lucide de forma segura
export function refreshIcons(root = document) {
  if (typeof lucide !== "undefined" && lucide.createIcons) {
    lucide.createIcons({ root });
  }
}

// Wrapper para inyectar HTML y refrescar iconos automáticamente
export function injectHTML(container, html, root = container) {
  container.innerHTML = html;
  refreshIcons(root);
}
```

**Beneficio:** Elimina llamadas manuales dispersas. Si se usa `injectHTML()`, los iconos se refrescan automáticamente. Si se añade un nuevo tipo de icono en el futuro, no hay que acordarse de llamar a `createIcons()`.

---

### 🟡 Caso 2: Datos de empresa duplicados (equipo directivo y departamentos)

**Dónde aparece:**

- `uis/website/index.html` — El equipo directivo está hardcodeado en HTML (sección `#team`, ~10 líneas con iniciales, nombre y cargo). Los servicios/departamentos también están en HTML (sección `#services`).
- `uis/backoffice/app.js` — `COMPANY_DATA` contiene el mismo equipo directivo y los mismos departamentos en un array de JavaScript.

**Por qué es candidato a refactorización:**

La información de la empresa (equipo directivo, departamentos) es la misma en ambos frontends, pero está duplicada en dos formatos distintos (HTML y JS). Cualquier cambio — un nuevo miembro del equipo, un cambio de cargo o departamento — requiere modificar ambos frontends manualmente. Esto es fuente de errores de sincronización.

**Cómo quedaría la abstracción compartida:**

```json
// uis/shared/company-data.json
{
  "team": [
    { "initials": "TH", "name": "Thomas Harry", "role": "CEO · Los Ángeles" },
    { "initials": "AK", "name": "Andrés Kim", "role": "CTO · Zaragoza" },
    { "initials": "AW", "name": "Ana Whitfield", "role": "Operaciones de Almacén" },
    { "initials": "CV", "name": "Carlos Vega", "role": "Última Milla" },
    { "initials": "SR", "name": "Sofía Ramos", "role": "Logística Inversa" },
    { "initials": "VC", "name": "Valentina Cruz", "role": "Atención al Cliente" },
    { "initials": "MT", "name": "Miguel Torres", "role": "Comercial y Clientes" }
  ],
  "departments": [
    { "name": "Operaciones de Almacén", "lead": "Ana Whitfield",
      "desc": "Supervisa los almacenes de LA y Zaragoza (~70 operarios). Gestión de pedidos, picking y empaquetado." },
    { "name": "Última Milla", "lead": "Carlos Vega",
      "desc": "Coordina 8 transportistas (UPS, FedEx, DHL, MRW, SEUR). Seguimiento de entregas e incidencias." },
    { "name": "Logística Inversa", "lead": "Sofía Ramos",
      "desc": "Gestiona devoluciones (18-25% del volumen). Aprobación, recogida, inspección y reacondicionamiento." },
    { "name": "Atención al Cliente", "lead": "Valentina Cruz",
      "desc": "15 agentes en LA y Zaragoza. Consultas B2B y B2C por email, WhatsApp y teléfono." },
    { "name": "Comercial y Clientes", "lead": "Miguel Torres",
      "desc": "Account managers + desarrollo de negocio. Cartera de clientes marca y renovaciones anuales." },
    { "name": "Tecnología", "lead": "Andrés Kim (CTO)",
      "desc": "7 personas en Zaragoza. Arquitectura, data engineering y sistemas. TrackFlow Tech." }
  ]
}
```

```js
// Ejemplo de consumo desde el backoffice (app.js)
async function loadCompanyData() {
  try {
    const response = await fetch("/company-data.json");
    return await response.json();
  } catch {
    // Fallback inline data si el JSON no está disponible
    return COMPANY_DATA;
  }
}
```

**Beneficio:** Una sola fuente de verdad (`company-data.json`) para los datos de la empresa. El website puede cargarlo con `fetch()` y el backoffice puede importarlo directamente. Cualquier cambio en la plantilla se refleja en ambos frontends automáticamente.

---

## 3. Archivos generados

Los informes HTML, JSON y capturas están en `audit/before/`:

| Archivo | Descripción |
|---|---|
| `website-desktop.report.html` / `.json` | Lighthouse Website — Escritorio |
| `website-mobile.report.html` / `.json` | Lighthouse Website — Móvil |
| `backoffice-desktop.report.html` / `.json` | Lighthouse Backoffice — Escritorio |
| `backoffice-mobile.report.html` / `.json` | Lighthouse Backoffice — Móvil |
| `website-desktop.png` | Captura del informe (escritorio) |
| `website-mobile.png` | Captura del informe (móvil) |
| `backoffice-desktop.png` | Captura del informe (escritorio) |
| `backoffice-mobile.png` | Captura del informe (móvil) |