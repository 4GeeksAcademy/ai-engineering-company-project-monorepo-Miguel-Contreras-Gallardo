/* Backoffice telemetry capture. The only public API is window.track(). */
(function initializeTelemetry(global) {
  "use strict";

  const SCHEMA_VERSION = "1.0";
  const BATCH_INTERVAL_MS = 10_000;
  const MAX_BATCH_SIZE = 20;
  const MAX_RETRIES = 3;
  const RETRY_BASE_DELAY_MS = 1_000;
  const queue = [];

  let sessionId;
  let userId = "urn:service:backoffice";
  let debounceTimer;
  let inFlight;
  let inFlightBatch;
  let authenticatedSessionCreatedAt;

  const reportedVitals = new Set();
  const vitalValues = {
    clsSessionValue: 0,
    clsSessionStart: undefined,
    clsLastShift: undefined,
    clsMax: 0,
    LCP: undefined,
    interactions: new Map(),
  };
  const supportedAuthFailureReasons = new Set(["invalid_credentials", "network_error"]);

  function getEndpoint() {
    const runtimeConfig = global.__TRACKFLOW_CONFIG__ || {};
    const metaEndpoint = global.document
      ?.querySelector('meta[name="NEXT_PUBLIC_TELEMETRY_ENDPOINT"]')
      ?.content;
    const buildTimeEndpoint = typeof process !== "undefined"
      ? process.env?.NEXT_PUBLIC_TELEMETRY_ENDPOINT
      : undefined;

    return buildTimeEndpoint
      || global.NEXT_PUBLIC_TELEMETRY_ENDPOINT
      || runtimeConfig.NEXT_PUBLIC_TELEMETRY_ENDPOINT
      || metaEndpoint
      || "http://localhost:8000/telemetry/events";
  }

  function createUuid() {
    if (global.crypto?.randomUUID) return global.crypto.randomUUID();
    const bytes = new Uint8Array(16);
    global.crypto.getRandomValues(bytes);
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    const hex = [...bytes].map((byte) => byte.toString(16).padStart(2, "0"));
    return `${hex.slice(0, 4).join("")}-${hex.slice(4, 6).join("")}-${hex.slice(6, 8).join("")}-${hex.slice(8, 10).join("")}-${hex.slice(10).join("")}`;
  }

  function beginAuthenticatedSession(authenticatedUserId) {
    if (typeof authenticatedUserId !== "string" || !authenticatedUserId.trim()) return;
    userId = authenticatedUserId.trim();
    sessionId = createUuid();
    authenticatedSessionCreatedAt = new Date().toISOString();
  }

  function getPageRoute() {
    const activeView = global.document?.querySelector?.(".view.active")?.id;
    if (activeView === "view-inventory") return "/inventory";
    if (activeView === "view-company") return "/company";
    if (activeView === "view-dashboard") return "/";
    return "/other";
  }

  function rateVital(name, value) {
    if (name === "CLS") return value <= 0.1 ? "good" : value <= 0.25 ? "needs-improvement" : "poor";
    const good = name === "INP" ? 200 : name === "LCP" ? 2_500 : name === "FCP" ? 1_800 : 800;
    const poor = name === "INP" ? 500 : name === "LCP" ? 4_000 : name === "FCP" ? 3_000 : 1_800;
    return value <= good ? "good" : value <= poor ? "needs-improvement" : "poor";
  }

  function reportVital(name, value, navigationType) {
    if (reportedVitals.has(name) || !Number.isFinite(value) || value < 0) return;
    reportedVitals.add(name);
    track("web_vital_recorded", {
      metricName: name,
      metricValue: name === "CLS" ? Number(value.toFixed(4)) : Math.round(value),
      metricRating: rateVital(name, value),
      pageRoute: getPageRoute(),
      ...(navigationType ? { navigationType } : {}),
      recordedAt: new Date().toISOString(),
    });
  }

  function initializeWebVitals() {
    if (typeof global.PerformanceObserver !== "function" || !global.performance) return;

    try {
      const navigation = global.performance.getEntriesByType?.("navigation")?.[0];
      const knownNavigationTypes = {
        navigate: "navigate",
        reload: "reload",
        back_forward: "back-forward",
        "back-forward": "back-forward",
        "back-forward-cache": "back-forward-cache",
        prerender: "prerender",
      };
      const navigationType = knownNavigationTypes[navigation?.type] || "other";
      if (navigation && Number.isFinite(navigation.responseStart)) {
        reportVital("TTFB", navigation.responseStart, navigationType);
      }

      const processEntries = (entries) => {
        for (const entry of entries) {
          if (entry.entryType === "paint" && entry.name === "first-contentful-paint") {
            reportVital("FCP", entry.startTime, navigationType);
          } else if (entry.entryType === "largest-contentful-paint") {
            vitalValues.LCP = entry.startTime;
          } else if (entry.entryType === "layout-shift" && !entry.hadRecentInput) {
            const timestamp = entry.startTime || 0;
            const startsNewSession = vitalValues.clsLastShift === undefined
              || timestamp - vitalValues.clsLastShift > 1_000
              || timestamp - vitalValues.clsSessionStart > 5_000;
            if (startsNewSession) {
              vitalValues.clsSessionStart = timestamp;
              vitalValues.clsSessionValue = 0;
            }
            vitalValues.clsSessionValue += entry.value || 0;
            vitalValues.clsLastShift = timestamp;
            vitalValues.clsMax = Math.max(vitalValues.clsMax, vitalValues.clsSessionValue);
          } else if (entry.entryType === "event" && entry.interactionId > 0) {
            vitalValues.interactions.set(
              entry.interactionId,
              Math.max(vitalValues.interactions.get(entry.interactionId) || 0, entry.duration || 0),
            );
          }
        }
      };
      const observer = new global.PerformanceObserver((list) => processEntries(list.getEntries()));
      for (const type of ["paint", "largest-contentful-paint", "layout-shift", "event"]) {
        try {
          observer.observe({ type, buffered: true, durationThreshold: 40 });
        } catch (_) {
          // Older browsers may not support all entry types/options.
        }
      }
      global.__trackflowVitalsObserver = observer;
      global.__trackflowReportWebVitals = () => {
        if (typeof observer.takeRecords === "function") processEntries(observer.takeRecords());
        if (vitalValues.LCP !== undefined) reportVital("LCP", vitalValues.LCP, navigationType);
        if (vitalValues.clsMax > 0) reportVital("CLS", vitalValues.clsMax, navigationType);
        if (vitalValues.interactions.size) {
          const interactionDurations = [...vitalValues.interactions.values()].sort((a, b) => b - a);
          const p98Index = Math.max(0, Math.ceil(interactionDurations.length * 0.02) - 1);
          reportVital("INP", interactionDurations[p98Index], navigationType);
        }
      };
    } catch (_) {
      // Performance APIs are optional; telemetry must never break the backoffice.
    }
  }

  function captureLoginFailure(event) {
    const reason = event.detail?.reason;
    if (!supportedAuthFailureReasons.has(reason)) return;
    track("login_failed", {
      failureReason: reason,
      attemptAt: new Date().toISOString(),
      sourceApp: "backoffice",
    });
  }

  function captureSessionExpired() {
    if (!authenticatedSessionCreatedAt) return;
    const expiredAt = new Date();
    const createdAt = new Date(authenticatedSessionCreatedAt);
    track("session_expired", {
      expiredAt: expiredAt.toISOString(),
      createdAt: authenticatedSessionCreatedAt,
      inactivityMinutes: Math.max(0, Math.floor((expiredAt.getTime() - createdAt.getTime()) / 60_000)),
      reason: "session_expired",
    });
    authenticatedSessionCreatedAt = undefined;
    userId = "urn:service:backoffice";
    sessionId = createUuid();
  }

  function scheduleFlush() {
    global.clearTimeout(debounceTimer);
    debounceTimer = global.setTimeout(() => {
      debounceTimer = undefined;
      void flushQueue();
    }, BATCH_INTERVAL_MS);
  }

  function delay(milliseconds) {
    return new Promise((resolve) => global.setTimeout(resolve, milliseconds));
  }

  async function sendBatchWithRetries(batch) {
    for (let attempt = 0; attempt <= MAX_RETRIES; attempt += 1) {
      try {
        const response = await global.fetch(getEndpoint(), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ events: batch }),
          keepalive: true,
        });
        if (!response.ok) throw new Error(`Telemetry endpoint returned ${response.status}`);
        return true;
      } catch (error) {
        if (attempt === MAX_RETRIES) {
          console.warn("Telemetry batch discarded after retries", error);
          return false;
        }
        await delay(RETRY_BASE_DELAY_MS * (2 ** attempt));
      }
    }
    return false;
  }

  async function flushQueue() {
    global.clearTimeout(debounceTimer);
    debounceTimer = undefined;
    if (inFlight) {
      await inFlight;
      if (queue.length) return flushQueue();
      return;
    }
    if (!queue.length) return;

    const batch = queue.splice(0, MAX_BATCH_SIZE);
    inFlightBatch = batch;
    inFlight = sendBatchWithRetries(batch);
    await inFlight;
    inFlight = undefined;
    inFlightBatch = undefined;

    if (queue.length) {
      if (queue.length >= MAX_BATCH_SIZE) void flushQueue();
      else scheduleFlush();
    }
  }

  function flushWithBeacon() {
    global.clearTimeout(debounceTimer);
    debounceTimer = undefined;
    if ((!queue.length && !inFlightBatch) || typeof global.navigator?.sendBeacon !== "function") {
      if (queue.length) void flushQueue();
      return;
    }

    const batch = [...(inFlightBatch || []), ...queue];
    const body = new Blob([JSON.stringify({ events: batch })], { type: "application/json" });
    if (global.navigator.sendBeacon(getEndpoint(), body)) {
      queue.splice(0, queue.length);
    } else {
      void flushQueue();
    }
  }

  function track(eventType, properties) {
    if (typeof eventType !== "string" || !eventType.trim()) return;
    if (!properties || typeof properties !== "object" || Array.isArray(properties)) return;

    if (!sessionId) sessionId = createUuid();
    queue.push({
      eventId: createUuid(),
      timestamp: new Date().toISOString(),
      sessionId,
      userId,
      event_type: eventType,
      schemaVersion: SCHEMA_VERSION,
      requestId: createUuid(),
      properties,
    });

    if (queue.length >= MAX_BATCH_SIZE) void flushQueue();
    else scheduleFlush();
  }

  global.addEventListener("trackflow:login", (event) => {
    beginAuthenticatedSession(event.detail?.userId);
  });
  global.addEventListener("trackflow:logout", () => {
    userId = "urn:service:backoffice";
    sessionId = createUuid();
    authenticatedSessionCreatedAt = undefined;
  });
  global.document?.addEventListener("visibilitychange", () => {
    if (global.document.visibilityState === "hidden") {
      global.__trackflowReportWebVitals?.();
      flushWithBeacon();
    }
  });
  global.addEventListener("pagehide", () => {
    global.__trackflowReportWebVitals?.();
    flushWithBeacon();
  });
  global.addEventListener("trackflow:login_failed", captureLoginFailure);
  global.addEventListener("trackflow:session_expired", captureSessionExpired);

  global.track = track;
  initializeWebVitals();
})(window);