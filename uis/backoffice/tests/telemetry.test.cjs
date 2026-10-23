const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const serviceSource = fs.readFileSync(
  path.join(__dirname, "../src/services/telemetry.js"),
  "utf8",
);

function createTelemetryWindow({ failAttempts = 0, withVitals = false } = {}) {
  const listeners = new Map();
  const timers = new Map();
  const fetchCalls = [];
  const beaconCalls = [];
  const retryDelays = [];
  let uuid = 0;
  let timerId = 0;
  const document = {
    visibilityState: "visible",
    querySelector: (selector) => selector.startsWith("meta[")
      ? { content: "https://telemetry.test/events" }
      : ({ id: "view-inventory" }),
    addEventListener: (name, callback) => listeners.set(`document:${name}`, callback),
  };
  const window = {
    crypto: { randomUUID: () => `uuid-${++uuid}` },
    fetch: async (...args) => {
      fetchCalls.push(args);
      if (fetchCalls.length <= failAttempts) throw new Error("temporary network failure");
      return { ok: true, status: 200 };
    },
    navigator: {
      sendBeacon: (url, body) => {
        beaconCalls.push({ url, body });
        return true;
      },
    },
    document,
    addEventListener: (name, callback) => listeners.set(name, callback),
    setTimeout: (callback, milliseconds) => {
      const id = ++timerId;
      timers.set(id, callback);
      retryDelays.push(milliseconds);
      return id;
    },
    clearTimeout: (id) => timers.delete(id),
  };

  if (withVitals) {
    const observers = [];
    window.performance = {
      getEntriesByType: () => [{ type: "navigate", responseStart: 120 }],
    };
    window.PerformanceObserver = class {
      constructor(callback) {
        this.callback = callback;
        this.records = [];
        observers.push(this);
      }
      observe() {}
      takeRecords() {
        const records = this.records;
        this.records = [];
        return records;
      }
      emit(entries) {
        this.callback({ getEntries: () => entries });
      }
    };
    window.__testObservers = observers;
  }

  vm.runInNewContext(serviceSource, { window, Blob, console, Date });

  return {
    window,
    listeners,
    timers,
    fetchCalls,
    beaconCalls,
    retryDelays,
    runTimer(id) {
      const callback = timers.get(id);
      timers.delete(id);
      callback?.();
    },
    async flushMicrotasks() {
      await new Promise((resolve) => setImmediate(resolve));
    },
  };
}

test("track creates the envelope and sends after the 10-second timer", async () => {
  const telemetry = createTelemetryWindow();

  telemetry.window.track("section_viewed", { sectionId: "dashboard" });
  const timerId = [...telemetry.timers.keys()][0];
  telemetry.runTimer(timerId);
  await telemetry.flushMicrotasks();

  assert.equal(telemetry.fetchCalls.length, 1);
  const [url, options] = telemetry.fetchCalls[0];
  assert.equal(url, "https://telemetry.test/events");
  const body = JSON.parse(options.body);
  assert.equal(body.events.length, 1);
  assert.equal(body.events[0].event_type, "section_viewed");
  assert.equal(body.events[0].schemaVersion, "1.0");
  assert.match(body.events[0].eventId, /^uuid-/);
  assert.match(body.events[0].requestId, /^uuid-/);
  assert.match(body.events[0].sessionId, /^uuid-/);
  assert.equal(body.events[0].userId, "urn:service:backoffice");
  assert.deepEqual(body.events[0].properties, { sectionId: "dashboard" });
});

test("track flushes when the queue reaches 20 events", async () => {
  const telemetry = createTelemetryWindow();

  for (let index = 0; index < 20; index += 1) {
    telemetry.window.track("feature_used", { featureId: `feature-${index}` });
  }
  await telemetry.flushMicrotasks();

  assert.equal(telemetry.fetchCalls.length, 1);
  assert.equal(JSON.parse(telemetry.fetchCalls[0][1].body).events.length, 20);
});

test("login event sets the authenticated user and a new in-memory session", async () => {
  const telemetry = createTelemetryWindow();

  telemetry.listeners.get("trackflow:login")({ detail: { userId: "user_opaque_1" } });
  telemetry.window.track("section_viewed", { sectionId: "inventory" });
  telemetry.runTimer([...telemetry.timers.keys()][0]);
  await telemetry.flushMicrotasks();

  const event = JSON.parse(telemetry.fetchCalls[0][1].body).events[0];
  assert.equal(event.userId, "user_opaque_1");
  assert.match(event.sessionId, /^uuid-/);
});

test("Web Vitals are emitted once with a normalized page route", async () => {
  const telemetry = createTelemetryWindow({ withVitals: true });
  const observer = telemetry.window.__testObservers[0];
  observer.emit([{ entryType: "paint", name: "first-contentful-paint", startTime: 600 }]);
  observer.records.push(
    { entryType: "largest-contentful-paint", startTime: 1_900 },
    { entryType: "layout-shift", value: 0.05, hadRecentInput: false },
    { entryType: "event", interactionId: 1, duration: 90 },
  );
  telemetry.window.__trackflowReportWebVitals();
  telemetry.window.__trackflowReportWebVitals();
  telemetry.window.document.visibilityState = "hidden";
  telemetry.listeners.get("document:visibilitychange")();

  const body = JSON.parse(await telemetry.beaconCalls[0].body.text());
  const events = body.events.filter((event) => event.event_type === "web_vital_recorded");
  assert.deepEqual(events.map((event) => event.properties.metricName).sort(), ["CLS", "FCP", "INP", "LCP", "TTFB"]);
  for (const event of events) {
    assert.equal(event.properties.pageRoute, "/inventory");
    assert.ok(!("url" in event.properties));
  }
  assert.equal(events.find((event) => event.properties.metricName === "TTFB").properties.navigationType, "navigate");
});

test("auth hooks accept only controlled reasons and omit credential data", async () => {
  const telemetry = createTelemetryWindow();
  telemetry.listeners.get("trackflow:login_failed")({ detail: { reason: "invalid_credentials", email: "private@example.test", password: "secret" } });
  telemetry.listeners.get("trackflow:login_failed")({ detail: { reason: "other", email: "private@example.test" } });
  telemetry.listeners.get("trackflow:login")({ detail: { userId: "opaque-user" } });
  telemetry.listeners.get("trackflow:session_expired")();
  telemetry.runTimer([...telemetry.timers.keys()][0]);
  await telemetry.flushMicrotasks();

  const events = JSON.parse(telemetry.fetchCalls[0][1].body).events;
  assert.deepEqual(events.map((event) => event.event_type), ["login_failed", "session_expired"]);
  assert.deepEqual(Object.keys(events[0].properties).sort(), ["attemptAt", "failureReason", "sourceApp"]);
  assert.equal(events[0].properties.failureReason, "invalid_credentials");
  assert.deepEqual(Object.keys(events[1].properties).sort(), ["createdAt", "expiredAt", "inactivityMinutes", "reason"]);
  assert.ok(events[1].properties.inactivityMinutes >= 0);
  assert.equal(events[1].properties.reason, "session_expired");
  assert.equal(events[1].userId, "opaque-user");
});

test("visibilitychange sends pending events using sendBeacon", async () => {
  const telemetry = createTelemetryWindow();

  telemetry.window.track("section_viewed", { sectionId: "dashboard" });
  telemetry.window.document.visibilityState = "hidden";
  telemetry.listeners.get("document:visibilitychange")();

  assert.equal(telemetry.beaconCalls.length, 1);
  assert.equal(telemetry.beaconCalls[0].url, "https://telemetry.test/events");
  const body = JSON.parse(await telemetry.beaconCalls[0].body.text());
  assert.equal(body.events[0].event_type, "section_viewed");
  assert.equal(telemetry.fetchCalls.length, 0);
});

test("failed sends retry three times with exponential backoff", async () => {
  const telemetry = createTelemetryWindow({ failAttempts: 3 });

  telemetry.window.track("section_viewed", { sectionId: "dashboard" });
  telemetry.runTimer([...telemetry.timers.keys()][0]);
  await telemetry.flushMicrotasks();
  assert.equal(telemetry.fetchCalls.length, 1);
  assert.equal(telemetry.retryDelays.at(-1), 1_000);

  for (let attempt = 0; attempt < 3; attempt += 1) {
    const retryTimerId = [...telemetry.timers.keys()][0];
    assert.ok(retryTimerId);
    telemetry.runTimer(retryTimerId);
    await telemetry.flushMicrotasks();
    if (attempt < 2) {
      assert.equal(telemetry.retryDelays.at(-1), 2_000 * (2 ** attempt));
    }
  }

  assert.equal(telemetry.fetchCalls.length, 4);
});

test("the schema registry has unique event types and exact allowlists", () => {
  const registry = JSON.parse(fs.readFileSync(
    path.join(__dirname, "../../../docs/telemetry/event-schemas.json"),
    "utf8",
  )).event_schemas;
  const eventTypes = Object.keys(registry);

  assert.equal(new Set(eventTypes).size, eventTypes.length);
  for (const [eventType, schema] of Object.entries(registry)) {
    assert.ok(Array.isArray(schema.allowlist), `${eventType} needs an allowlist`);
    assert.ok(Array.isArray(schema.required), `${eventType} needs required keys`);
    assert.ok(schema.required.every((key) => schema.allowlist.includes(key), `${eventType} requires keys inside its allowlist`));
    assert.deepEqual(Object.keys(schema.properties).sort(), [...schema.allowlist].sort(), `${eventType} properties must equal its allowlist`);
  }
});

test("frontend technical event schema permits only sanitized fields", () => {
  const registry = JSON.parse(fs.readFileSync(
    path.join(__dirname, "../../../docs/telemetry/event-schemas.json"),
    "utf8",
  )).event_schemas;
  const schema = registry.frontend_error_recorded;

  assert.deepEqual(schema.allowlist, ["errorCategory", "sourceApp", "occurredAt", "endpoint"]);
  assert.deepEqual(schema.required, ["errorCategory", "sourceApp", "occurredAt"]);
  assert.ok(!schema.allowlist.includes("message"));
  assert.ok(!schema.allowlist.includes("stack"));
});

test("Web Vitals and authentication schemas use controlled privacy-safe allowlists", () => {
  const registry = JSON.parse(fs.readFileSync(
    path.join(__dirname, "../../../docs/telemetry/event-schemas.json"),
    "utf8",
  )).event_schemas;

  assert.deepEqual(registry.web_vital_recorded.allowlist, [
    "metricName", "metricValue", "metricRating", "pageRoute", "navigationType", "recordedAt",
  ]);
  assert.deepEqual(registry.web_vital_recorded.properties.pageRoute.enum, ["/", "/inventory", "/company", "/other"]);
  assert.deepEqual(registry.login_failed.properties.failureReason.enum, ["invalid_credentials", "network_error"]);
  assert.ok(!registry.login_failed.allowlist.includes("email"));
  assert.ok(!registry.login_failed.allowlist.includes("password"));
});

test("frontend instrumentation emits registered static event types only", () => {
  const registry = JSON.parse(fs.readFileSync(
    path.join(__dirname, "../../../docs/telemetry/event-schemas.json"),
    "utf8",
  )).event_schemas;
  const appSource = fs.readFileSync(path.join(__dirname, "../app.js"), "utf8");
  const trackCalls = [...appSource.matchAll(/window\.track\("([a-z_]+)"\s*,\s*\{([^{}]*)\}/gs)];

  assert.ok(trackCalls.length > 0);
  for (const [, eventType, propertySource] of trackCalls) {
    assert.ok(registry[eventType], `${eventType} must be registered`);
    const literalKeys = [...propertySource.matchAll(/^\s*([A-Za-z][A-Za-z0-9]*):/gm)]
      .map(([, key]) => key);
    for (const key of literalKeys) {
      assert.ok(registry[eventType].allowlist.includes(key), `${eventType}.${key} must be allowed`);
    }
  }
});