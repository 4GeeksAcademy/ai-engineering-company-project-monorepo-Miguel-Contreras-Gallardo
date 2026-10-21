"use client";

import { useEffect, useMemo, useState } from "react";

const MAX_SAMPLES = 1000;
const POLL_INTERVAL_MS = 5000;

function getStatusUrl() {
  const host = window.location.hostname;
  const apiHost = host.includes("app.github.dev") ? host.replace("-3000", "-8001") : host;
  return `${window.location.protocol}//${apiHost}/status`;
}

export default function HealthHistoryPanel() {
  const [samples, setSamples] = useState([]);

  useEffect(() => {
    let disposed = false;
    const collectSample = async () => {
      const startedAt = performance.now();
      try {
        const response = await fetch(getStatusUrl(), { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        await response.json();
        if (!disposed) {
          setSamples((current) => [...current, { ok: true, latency: performance.now() - startedAt }].slice(-MAX_SAMPLES));
        }
      } catch {
        if (!disposed) {
          setSamples((current) => [...current, { ok: false, latency: performance.now() - startedAt }].slice(-MAX_SAMPLES));
        }
      }
    };

    collectSample();
    const interval = window.setInterval(collectSample, POLL_INTERVAL_MS);
    return () => {
      disposed = true;
      window.clearInterval(interval);
    };
  }, []);

  // Sorting up to 1,000 observations for the percentile is O(n log n), so only
  // recalculate the diagnostic summary when the sample history changes.
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

  return (
    <section className="mt-6 rounded-xl border border-neutral-800 bg-neutral-900 p-5 text-left" aria-live="polite">
      <h2 className="text-lg font-semibold">Historial de salud (últimas {MAX_SAMPLES} muestras)</h2>
      <p className="mt-1 text-sm text-neutral-400">Una consulta cada 5 segundos; se conserva solo en esta sesión del navegador.</p>
      {summary ? (
        <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Metric label="Muestras" value={summary.count} />
          <Metric label="Disponibilidad" value={`${summary.successRate}%`} />
          <Metric label="Latencia media" value={`${summary.averageLatency} ms`} />
          <Metric label="Latencia p95" value={`${summary.p95Latency} ms`} />
        </dl>
      ) : <p className="mt-4 text-sm text-neutral-400">Recopilando la primera muestra…</p>}
    </section>
  );
}

function Metric({ label, value }) {
  return <div><dt className="text-xs uppercase tracking-wide text-neutral-500">{label}</dt><dd className="mt-1 text-xl font-semibold">{value}</dd></div>;
}
