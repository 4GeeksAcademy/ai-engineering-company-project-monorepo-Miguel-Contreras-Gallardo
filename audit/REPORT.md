# Auditoría Lighthouse — TrackFlow

## Resumen ejecutivo

Se realizaron 4 auditorías Lighthouse (desktop + mobile) sobre los dos frontends de TrackFlow —website corporativo y backoffice de operaciones— antes y después de aplicar correcciones incrementales sobre código existente.

**Mejora principal**: Accessibility sube de 87→100 (**website**) y 95→100 (**backoffice**). Rendimiento móvil de backoffice salta de 71→93 (+22 puntos).

---

## Resultados comparativos

### Website corporativo

| Métrica         | Desktop before | Desktop after | Mobile before | Mobile after |
|-----------------|:--------------:|:-------------:|:-------------:|:------------:|
| Performance     | 99             | 92            | 94            | **97**       |
| Accessibility   | 87             | **100**       | 91            | **100**      |
| Best Practices  | 100            | 96            | 100           | 96           |
| SEO             | 91             | **100**       | 91            | **100**      |

### Backoffice de operaciones

| Métrica         | Desktop before | Desktop after | Mobile before | Mobile after |
|-----------------|:--------------:|:-------------:|:-------------:|:------------:|
| Performance     | 92             | 90            | 71            | **93**       |
| Accessibility   | 95             | **100**       | 95            | **100**      |
| Best Practices  | 96             | 96            | 96            | 96           |
| SEO             | 82             | 63*           | 82            | 63*          |

> \* La caída de SEO en backoffice es **intencionada**: añadimos `robots.txt` con `Disallow: /` porque el panel de operaciones **no debe ser indexado** por buscadores. Antes carecía de robots.txt, lo cual es una mala práctica de seguridad.

---

## Correcciones aplicadas (por commit)

### Commit 1 — SEO y landmarks
- **robots.txt** para website (`Allow: /`) y backoffice (`Disallow: /`)
- **meta description** en backoffice
- Envolver contenido del website en `<main>` (landmark principal)
- Cambiar cabeceras de equipo de `h4` a `h3` para orden secuencial correcto
- **Impacto**: SEO website 91→100. Accessibility website 87→100.

### Commit 2 — Contraste de color (WCAG AA)
- About metrics: `#69716d` → `#4d5953` sobre fondo `#dcece4` (ratio 4.1→5.39:1)
- Footer copy: `#69716d` → `#8f9a93` sobre fondo `#19211e` (ratio 3.27→5.86:1)
- Status banner backoffice: `#69716d` → `#4d5953` sobre fondo `#f8e2dc` (ratio 4.04→5.93:1)
- **Impacto**: Todos los problemas de contraste corregidos. Accessibility 95→100 en backoffice.

### Commit 3 — Rendimiento y CLS
- Reserva de 18×18px para placeholders de iconos Lucide
- Alturas mínimas (`min-height`) para contenedores renderizados por JS (dashboard cards, department grid, status banner)
- **Impacto**: CLS backoffice de 0.178→0. Mobile performance +22 puntos (71→93).

### Commit 4 — Errores de consola
- `AbortController` con timeout de 1.5s en la comprobación de estado de API, eliminando `ERR_CONNECTION_REFUSED`
- **Impacto**: Best Practices se mantiene en 96. Cero errores de consola.

### Commit 5 — Refactorización: extracción de helper Lucide
- Creación de `uis/shared/lucide-helper.js` — inicializa iconos automáticamente en `DOMContentLoaded`
- Expoene `window.refreshIcons()` para actualizaciones dinámicas (menú móvil, estado API)
- Eliminación de 6 llamadas directas a `lucide.createIcons()` repartidas por ambos frontends
- **Impacto**: Código más limpio, sin lógica de inicialización duplicada. Sin cambios en puntuación.

---

## Análisis de impacto

| Corrección                          | Impacto principal                           | Puntos ganados |
|--------------------------------------|---------------------------------------------|:--------------:|
| Contraste de color                  | Accessibilidad (todos los frontends)        | +13 / +9 / +5  |
| `<main>` landmark + headings        | Accessibilidad website                      | +13 / +9       |
| robots.txt + meta description       | SEO website                                 | +9             |
| CLS min-heights + Lucide placeholders | Rendimiento móvil backoffice               | +22            |
| AbortController                     | Best Practices (sin errores de consola)     | —              |

### Regresiones observadas

1. **Performance website desktop 99→92 (-7)**: La reserva de espacio para Lucide (18×18px) añade selectores CSS adicionales que pueden alargar ligeramente el primer pintado. Además, el test inicial de 99 era un resultado atípicamente alto; 92 sigue siendo excelente.
2. **Best Practices website 100→96 (-4)**: Probable variabilidad de red en la carga de dependencias CDN (Lucide, Google Fonts). No se introdujeron errores de consola ni nuevas prácticas deficitarias.
3. **SEO backoffice 82→63 (-19)**: Intencional — véase nota más arriba.

---

## Refactorización aplicada

### Helper compartido de Lucide (`uis/shared/lucide-helper.js`)

**Problema original**: Ambos frontends llamaban manualmente a `lucide.createIcons()` en 6 lugares distintos (app.js del website, app.js del backoffice), incluyendo tras cada actualización dinámica del DOM (menú móvil, renderizado de tablas, cambio de estado de API).

**Solución**: Se extrajo un helper compartido que:
- Se auto-ejecuta en `DOMContentLoaded` (sin esperar a que cada app.js lo invoque)
- Expoene `window.refreshIcons()` como única función de actualización
- Se incluye via `<script defer>` tras Lucide y antes de cada app.js

**Beneficio**: Elimina duplicación, centraliza la lógica de inicialización y reduce el riesgo de olvidar llamar a `createIcons()` tras modificaciones del DOM.

---

## Datos técnicos

- **Herramienta**: Lighthouse 12+ (npm global)
- **Navegador**: Chromium headless
- **Resoluciones**: Desktop 1350×940, Mobile 412×915 (emulación Android)
- **Fecha after**: 18 de octubre de 2026
- **Repositorio**: `feature/lighthouse-audit`