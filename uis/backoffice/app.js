const API_URL = "http://localhost:8000";
const API_SLOW_REQUEST_MS = Number(window.__TRACKFLOW_CONFIG__?.API_SLOW_REQUEST_MS) || 3_000;

const state = {
  articles: [],
  stockBySku: new Map(),
  reorderSkus: new Set(),
};

const elements = {};

// Install before bootstrapping DOM handlers so initialization errors are captured.
installFrontendErrorHandlers();

// ---- Company data from CONTEXT.md ----
const COMPANY_DATA = {
  departments: [
    { name: "Operaciones de Almacén", lead: "Ana Whitfield", desc: "Supervisa los almacenes de LA y Zaragoza (~70 operarios). Gestión de pedidos, picking y empaquetado." },
    { name: "Última Milla", lead: "Carlos Vega", desc: "Coordina 8 transportistas (UPS, FedEx, DHL, MRW, SEUR). Seguimiento de entregas e incidencias." },
    { name: "Logística Inversa", lead: "Sofía Ramos", desc: "Gestiona devoluciones (18-25% del volumen). Aprobación, recogida, inspección y reacondicionamiento." },
    { name: "Atención al Cliente", lead: "Valentina Cruz", desc: "15 agentes en LA y Zaragoza. Consultas B2B y B2C por email, WhatsApp y teléfono." },
    { name: "Comercial y Clientes", lead: "Miguel Torres", desc: "Account managers + desarrollo de negocio. Cartera de clientes marca y renovaciones anuales." },
    { name: "Tecnología", lead: "Andrés Kim (CTO)", desc: "7 personas en Zaragoza. Arquitectura, data engineering y sistemas. TrackFlow Tech." },
  ],
  team: [
    { initials: "TH", name: "Thomas Harry", role: "CEO · Los Ángeles" },
    { initials: "AK", name: "Andrés Kim", role: "CTO · Zaragoza" },
    { initials: "AW", name: "Ana Whitfield", role: "Operaciones de Almacén" },
    { initials: "CV", name: "Carlos Vega", role: "Última Milla" },
    { initials: "SR", name: "Sofía Ramos", role: "Logística Inversa" },
    { initials: "VC", name: "Valentina Cruz", role: "Atención al Cliente" },
    { initials: "MT", name: "Miguel Torres", role: "Comercial y Clientes" },
  ],
};

// ---- View navigation ----
function switchView(viewId) {
  document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
  document.querySelectorAll(".nav-item[data-view]").forEach((n) => n.classList.remove("active"));

  const view = document.getElementById(`view-${viewId}`);
  if (view) view.classList.add("active");

  const navItem = document.querySelector(`.nav-item[data-view="${viewId}"]`);
  if (navItem) navItem.classList.add("active");
}

function renderDashboard() {
  // Live date
  const now = new Date();
  document.getElementById("live-date").textContent = now.toLocaleDateString("es-ES", {
    weekday: "long", year: "numeric", month: "long", day: "numeric",
  });

  // Department grid
  const deptGrid = document.getElementById("dept-grid");
  deptGrid.innerHTML = COMPANY_DATA.departments
    .map(
      (d) => `
    <article class="dept-card">
      <h3>${d.name}</h3>
      <span class="dept-lead">${d.lead}</span>
      <p>${d.desc}</p>
    </article>`
    )
    .join("");

  // API status (try to connect)
  checkApiStatus();
}

async function checkApiStatus() {
  const banner = document.getElementById("api-status-banner");
  const text = document.getElementById("api-status-text");
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 1500);
  try {
    await api("/articles/");
    state.apiWasUnavailable = false;
    banner.className = "status-banner online";
    banner.querySelector("svg").setAttribute("data-lucide", "cloud");
    text.textContent = "Conectado correctamente a la API de inventario";
    refreshIcons();
  } catch {
    if (!state.apiWasUnavailable) {
      trackFrontendError("api_connection_lost");
      state.apiWasUnavailable = true;
    }
    banner.className = "status-banner";
    banner.querySelector("svg").setAttribute("data-lucide", "cloud-off");
    text.textContent = "API no disponible. El backoffice funciona con datos locales. Inicia la API en services/api.";
    refreshIcons();
  }
}

function renderCompanyView() {
  const teamGrid = document.getElementById("team-grid");
  teamGrid.innerHTML = COMPANY_DATA.team
    .map(
      (m) => `
    <div class="team-card-bo">
      <div class="avatar">${m.initials}</div>
      <h4>${m.name}</h4>
      <span>${m.role}</span>
    </div>`
    )
    .join("");
}

// ---- Inventory (existing code enhanced) ----

async function api(path, options = {}) {
  const method = String(options.method || "GET").toUpperCase();
  const startedAt = performance.now();
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    });
  } catch (error) {
    trackFrontendError("api_network_error");
    throw error;
  }
  const latencyMs = Math.round(performance.now() - startedAt);
  trackApiLatency(path, method, latencyMs, response.status);
  if (!response.ok) {
    trackFrontendError(response.status === 422 ? "api_validation_error" : "api_http_error");
  }
  if (!response.ok) {
    let message = `Error ${response.status}`;
    try {
      const body = await response.json();
      message = Array.isArray(body.detail)
        ? body.detail.map((item) => item.msg).join("; ")
        : body.detail || message;
    } catch (_) {
      // Keep the HTTP status when the server does not return JSON.
    }
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

function trackApiLatency(path, method, latencyMs, statusCode) {
  const normalizedPath = normalizeApiEndpoint(path);
  if (!normalizedPath) return;
  window.track("api_latency_recorded", {
    serviceName: "inventory-api",
    endpoint: normalizedPath,
    httpMethod: ["GET", "POST", "PUT", "PATCH", "DELETE"].includes(method) ? method : "GET",
    latencyMs: Math.max(0, latencyMs),
    statusCode,
  });
  if (latencyMs > API_SLOW_REQUEST_MS) {
    trackFrontendError("slow_api_request");
  }
}

function normalizeApiEndpoint(path) {
  const pathname = String(path).split("?", 1)[0];
  if (/^\/articles\/?$/.test(pathname)) return "/api/v1/articles";
  if (/^\/articles\/[^/]+\/?$/.test(pathname)) return "/api/v1/articles/item";
  if (/^\/articles\/[^/]+\/lots\/?$/.test(pathname)) return "/api/v1/articles/item/lots";
  if (/^\/inventory\/stock\/?$/.test(pathname)) return "/api/v1/inventory/stock";
  if (/^\/inventory\/reorder\/?$/.test(pathname)) return "/api/v1/inventory/reorder";
  if (/^\/inventory\/movements\/?$/.test(pathname)) return "/api/v1/inventory/movements";
  return null;
}

function trackFrontendError(errorCategory) {
  window.track("frontend_error_recorded", {
    errorCategory,
    sourceApp: "backoffice",
    occurredAt: new Date().toISOString(),
  });
}

function trackFeature(featureId, featureName, actionType = "click", outcome) {
  window.track("feature_used", {
    featureId,
    featureName,
    actionType,
    usedAt: new Date().toISOString(),
    contextSection: state.currentView === "inventory" ? "inventory" : "dashboard",
    ...(outcome ? { outcome } : {}),
  });
}

function installFrontendErrorHandlers() {
  window.addEventListener("error", (event) => {
    trackFrontendError("uncaught_exception");
  });
  window.addEventListener("unhandledrejection", () => {
    trackFrontendError("unhandled_rejection");
  });
}

async function loadDashboard() {
  setConnection("loading");
  try {
    const [articles, reorder] = await Promise.all([
      api("/articles/"),
      api("/inventory/reorder"),
    ]);
    state.articles = articles;
    state.reorderSkus = new Set(reorder.items.map((item) => item.sku));

    const activeArticles = articles.filter((article) => article.active);
    const stockResults = await Promise.all(
      activeArticles.map(async (article) => {
        const stock = await api(`/inventory/stock?sku=${encodeURIComponent(article.sku)}`);
        return [article.sku, stock.total];
      }),
    );
    state.stockBySku = new Map(stockResults);
    updateMetrics(activeArticles);
    renderTable();
    setConnection("online");
  } catch (error) {
    setConnection("offline");
    elements.body.innerHTML = `<tr><td colspan="6" class="empty-state">${escapeHtml(error.message)}</td></tr>`;
    showToast(error.message, true);
  }
}

function updateMetrics(activeArticles) {
  const totalStock = [...state.stockBySku.values()].reduce((sum, stock) => sum + stock, 0);
  document.querySelector("#metric-articles").textContent = activeArticles.length;
  document.querySelector("#metric-reorder").textContent = state.reorderSkus.size;
  document.querySelector("#metric-stock").textContent = new Intl.NumberFormat("es-ES").format(totalStock);
}

function renderTable() {
  const term = elements.search.value.trim().toLocaleLowerCase("es");
  const filtered = state.articles.filter((article) =>
    `${article.sku} ${article.name}`.toLocaleLowerCase("es").includes(term),
  );

  if (!filtered.length) {
    elements.body.innerHTML = '<tr><td colspan="6" class="empty-state">No hay artículos para mostrar.</td></tr>';
    return;
  }

  elements.body.innerHTML = filtered.map((article) => {
    const stock = state.stockBySku.get(article.sku) ?? 0;
    const needsReorder = article.active && state.reorderSkus.has(article.sku);
    return `<tr>
      <td class="article-cell"><strong>${escapeHtml(article.name)}</strong><span>${escapeHtml(article.sku)}</span></td>
      <td><span class="status ${article.active ? "active" : "inactive"}">${article.active ? "Activo" : "Baja"}</span></td>
      <td class="numeric"><strong>${new Intl.NumberFormat("es-ES").format(stock)}</strong></td>
      <td class="numeric">${new Intl.NumberFormat("es-ES").format(article.reorder_point)}</td>
      <td><span class="status ${needsReorder ? "reorder" : "healthy"}">${needsReorder ? "Reponer" : article.active ? "Correcto" : "Sin seguimiento"}</span></td>
      <td><div class="row-actions">
        <button class="icon-button" data-edit="${escapeHtml(article.sku)}" title="Editar artículo" aria-label="Editar ${escapeHtml(article.sku)}"><i data-lucide="pencil"></i></button>
        ${article.active ? `<button class="icon-button danger" data-delete="${escapeHtml(article.sku)}" title="Dar de baja" aria-label="Dar de baja ${escapeHtml(article.sku)}"><i data-lucide="archive"></i></button>` : ""}
      </div></td>
    </tr>`;
  }).join("");

  elements.body.querySelectorAll("[data-edit]").forEach((button) => button.addEventListener("click", () => openEditArticle(button.dataset.edit)));
  elements.body.querySelectorAll("[data-delete]").forEach((button) => button.addEventListener("click", () => deactivateArticle(button.dataset.delete)));
  refreshIcons();
}

function openNewArticle() {
  elements.articleForm.reset();
  document.querySelector("#article-mode").value = "create";
  document.querySelector("#article-dialog-title").textContent = "Nuevo artículo";
  document.querySelector("#article-sku").disabled = false;
  document.querySelector("#article-reorder").value = 0;
  document.querySelector("#article-active-field").hidden = true;
  elements.articleDialog.showModal();
}

function openEditArticle(sku) {
  const article = state.articles.find((item) => item.sku === sku);
  if (!article) return;
  document.querySelector("#article-mode").value = "edit";
  document.querySelector("#article-dialog-title").textContent = "Editar artículo";
  document.querySelector("#article-sku").value = article.sku;
  document.querySelector("#article-sku").disabled = true;
  document.querySelector("#article-name").value = article.name;
  document.querySelector("#article-description").value = article.description || "";
  document.querySelector("#article-reorder").value = article.reorder_point;
  document.querySelector("#article-active").checked = article.active;
  document.querySelector("#article-active-field").hidden = false;
  elements.articleDialog.showModal();
}

async function saveArticle(event) {
  event.preventDefault();
  const mode = document.querySelector("#article-mode").value;
  const sku = document.querySelector("#article-sku").value.trim();
  const payload = {
    name: document.querySelector("#article-name").value.trim(),
    description: document.querySelector("#article-description").value.trim() || null,
    reorder_point: Number(document.querySelector("#article-reorder").value),
  };
  if (mode === "create") payload.sku = sku;
  else payload.active = document.querySelector("#article-active").checked;

  try {
    await api(mode === "create" ? "/articles/" : `/articles/${encodeURIComponent(sku)}`, {
      method: mode === "create" ? "POST" : "PUT",
      body: JSON.stringify(payload),
    });
    window.track("feature_used", {
      featureId: mode === "create" ? "article-create" : "article-edit",
      featureName: mode === "create" ? "article_create" : "article_edit",
      actionType: "submit",
      usedAt: new Date().toISOString(),
      contextSection: "inventory",
      outcome: "success",
    });
    elements.articleDialog.close();
    showToast(mode === "create" ? "Artículo creado" : "Artículo actualizado");
    await loadDashboard();
  } catch (error) {
    window.track("feature_used", {
      featureId: mode === "create" ? "article-create" : "article-edit",
      featureName: mode === "create" ? "article_create" : "article_edit",
      actionType: "submit",
      usedAt: new Date().toISOString(),
      contextSection: "inventory",
      outcome: "error",
    });
    showToast(error.message, true);
  }
}

async function deactivateArticle(sku) {
  if (!window.confirm(`¿Dar de baja el artículo ${sku}? El historial se conservará.`)) {
    trackFeature("article-deactivation", "article_edit", "click", "cancelled");
    return;
  }
  try {
    await api(`/articles/${encodeURIComponent(sku)}`, { method: "DELETE" });
    window.track("feature_used", {
      featureId: "article-deactivation",
      featureName: "article_edit",
      actionType: "submit",
      usedAt: new Date().toISOString(),
      contextSection: "inventory",
      outcome: "success",
    });
    showToast("Artículo dado de baja; historial conservado");
    await loadDashboard();
  } catch (error) {
    window.track("feature_used", {
      featureId: "article-deactivation",
      featureName: "article_edit",
      actionType: "submit",
      usedAt: new Date().toISOString(),
      contextSection: "inventory",
      outcome: "error",
    });
    showToast(error.message, true);
  }
}

function openMovement() {
  const activeArticles = state.articles.filter((article) => article.active);
  const skuSelect = document.querySelector("#movement-sku");
  skuSelect.innerHTML = activeArticles.map((article) => `<option value="${escapeHtml(article.sku)}">${escapeHtml(article.sku)} · ${escapeHtml(article.name)}</option>`).join("");
  elements.movementForm.reset();
  syncAdjustmentField();
  elements.movementDialog.showModal();
  loadLots();
}

async function loadLots() {
  const sku = document.querySelector("#movement-sku").value;
  const lotSelect = document.querySelector("#movement-lot");
  if (!sku) {
    lotSelect.innerHTML = '<option value="">Sin artículos activos</option>';
    return;
  }
  try {
    const lots = await api(`/articles/${encodeURIComponent(sku)}/lots`);
    lotSelect.innerHTML = lots.length
      ? lots.map((lot) => `<option value="${escapeHtml(lot.code)}">${escapeHtml(lot.code)}</option>`).join("")
      : '<option value="">Crea un lote para continuar</option>';
  } catch (error) {
    showToast(error.message, true);
  }
}

function syncAdjustmentField() {
  const isAdjustment = document.querySelector("#movement-type").value === "ajuste";
  document.querySelector("#adjustment-direction-field").hidden = !isAdjustment;
  document.querySelector("#movement-direction").required = isAdjustment;
}

async function saveMovement(event) {
  event.preventDefault();
  const type = document.querySelector("#movement-type").value;
  const payload = {
    sku: document.querySelector("#movement-sku").value,
    warehouse_id: document.querySelector("#movement-warehouse").value,
    lot_code: document.querySelector("#movement-lot").value,
    type,
    quantity: Number(document.querySelector("#movement-quantity").value),
    adjustment_direction: type === "ajuste" ? document.querySelector("#movement-direction").value : null,
    reason: document.querySelector("#movement-reason").value.trim(),
    request_key: crypto.randomUUID(),
  };
  try {
    const result = await api("/inventory/movements", { method: "POST", body: JSON.stringify(payload) });
    window.track("feature_used", {
      featureId: "movement-create",
      featureName: "movement_create",
      actionType: "submit",
      usedAt: new Date().toISOString(),
      contextSection: "inventory",
      outcome: "success",
    });
    elements.movementDialog.close();
    showToast(`Movimiento registrado · stock ${result.resulting_stock}`);
    await loadDashboard();
  } catch (error) {
    window.track("feature_used", {
      featureId: "movement-create",
      featureName: "movement_create",
      actionType: "submit",
      usedAt: new Date().toISOString(),
      contextSection: "inventory",
      outcome: "error",
    });
    showToast(error.message, true);
  }
}

async function saveLot(event) {
  event.preventDefault();
  const sku = document.querySelector("#movement-sku").value;
  const code = document.querySelector("#lot-code").value.trim();
  try {
    await api(`/articles/${encodeURIComponent(sku)}/lots`, { method: "POST", body: JSON.stringify({ code }) });
    elements.lotDialog.close();
    elements.lotForm.reset();
    await loadLots();
    document.querySelector("#movement-lot").value = code;
    showToast("Lote creado");
  } catch (error) {
    showToast(error.message, true);
  }
}

function setConnection(status) {
  const dot = document.querySelector("#connection-dot");
  dot.className = `connection-dot ${status === "loading" ? "" : status}`;
  document.querySelector("#connection-label").textContent = status === "online" ? "API conectada" : status === "offline" ? "API sin conexión" : "Conectando";
}

function showToast(message, isError = false) {
  elements.toast.textContent = message;
  elements.toast.className = `toast visible${isError ? " error" : ""}`;
  window.clearTimeout(showToast.timeout);
  showToast.timeout = window.setTimeout(() => { elements.toast.className = "toast"; }, 3200);
}

function escapeHtml(value) {
  const node = document.createElement("span");
  node.textContent = String(value);
  return node.innerHTML;
}

// ---- Bootstrap ----
window.addEventListener("DOMContentLoaded", () => {
  Object.assign(elements, {
    body: document.querySelector("#inventory-body"),
    search: document.querySelector("#search-input"),
    articleDialog: document.querySelector("#article-dialog"),
    articleForm: document.querySelector("#article-form"),
    movementDialog: document.querySelector("#movement-dialog"),
    movementForm: document.querySelector("#movement-form"),
    lotDialog: document.querySelector("#lot-dialog"),
    lotForm: document.querySelector("#lot-form"),
    toast: document.querySelector("#toast"),
  });

  // View navigation
  document.querySelectorAll(".nav-item[data-view]").forEach((item) => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const view = item.dataset.view;
      switchView(view);
      const sectionName = ({ dashboard: "dashboard", inventory: "inventory", company: "other" })[view] || "other";
      window.track("section_viewed", {
        sectionId: view,
        sectionName,
        sourceApp: "backoffice",
        viewedAt: new Date().toISOString(),
        ...(state.currentView ? { referrerSection: state.currentView } : {}),
      });
      if (state.currentView && state.viewStartedAt) {
        window.track("section_viewed", {
          sectionId: state.currentView,
          sectionName: ({ dashboard: "dashboard", inventory: "inventory", company: "other" })[state.currentView] || "other",
          sourceApp: "backoffice",
          viewedAt: new Date(state.viewStartedAt).toISOString(),
          durationSeconds: Math.max(0, Math.floor((Date.now() - state.viewStartedAt) / 1_000)),
        });
      }
      state.currentView = view;
      state.viewStartedAt = Date.now();
      if (view === "dashboard") renderDashboard();
      if (view === "company") renderCompanyView();
      if (view === "inventory") loadDashboard();
    });
  });

  // Inventory events
  document.querySelector("#refresh-button").addEventListener("click", () => {
    trackFeature("inventory-refresh", "other");
    loadDashboard();
  });
  document.querySelector("#new-article-button").addEventListener("click", () => {
    trackFeature("article-create", "article_create");
    openNewArticle();
  });
  document.querySelector("#new-movement-button").addEventListener("click", () => {
    trackFeature("movement-create", "movement_create");
    openMovement();
  });
  document.querySelector("#new-lot-button").addEventListener("click", () => {
    trackFeature("lot-create", "other");
    elements.lotDialog.showModal();
  });
  document.querySelector("#movement-sku").addEventListener("change", loadLots);
  document.querySelector("#movement-type").addEventListener("change", syncAdjustmentField);
  elements.search.addEventListener("input", () => {
    trackFeature("article-search", "other", "view");
    renderTable();
  });
  elements.articleForm.addEventListener("submit", saveArticle);
  elements.movementForm.addEventListener("submit", saveMovement);
  elements.lotForm.addEventListener("submit", saveLot);
  document.querySelectorAll("[data-close]").forEach((button) => {
    button.addEventListener("click", () => document.querySelector(`#${button.dataset.close}`).close());
  });

  refreshIcons();

  // Start on dashboard view
  switchView("dashboard");
  window.track("section_viewed", {
    sectionId: "dashboard",
    sectionName: "dashboard",
    sourceApp: "backoffice",
    viewedAt: new Date().toISOString(),
  });
  state.currentView = "dashboard";
  state.viewStartedAt = Date.now();
  renderDashboard();
});
