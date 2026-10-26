"use client";

import { useEffect, useState } from "react";

const checks = [
  { name: "Web server", path: "/", expected: "MVP en marcha" },
  { name: "API health", path: "/status", expected: "status: ok" },
];

function endpointFor(path) {
  if (path === "/") return `${window.location.protocol}//${window.location.host}/`;
  const host = window.location.hostname;
  const apiHost = host.includes("app.github.dev") ? host.replace("-3000", "-8001") : host;
  return `${window.location.protocol}//${apiHost}${path}`;
}

export default function ServiceDiagnostics() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  async function runChecks() {
    setLoading(true);
    const nextResults = await Promise.all(checks.map(async (check) => {
      try {
        const response = await fetch(endpointFor(check.path), { cache: "no-store" });
        if (!response.ok) return { ...check, ok: false, detail: `HTTP ${response.status}` };
        const body = check.path === "/status" ? await response.json() : await response.text();
        const ok = check.path === "/status" ? body.status === "ok" : body.includes("MVP en marcha");
        return { ...check, ok, detail: ok ? check.expected : "Respuesta inesperada" };
      } catch (error) {
        return { ...check, ok: false, detail: error.message };
      }
    }));
    setResults(nextResults);
    setLoading(false);
  }

  useEffect(() => { runChecks(); }, []);

  return (
    <section className="mt-5 rounded-xl border border-neutral-800 bg-neutral-900 p-5 text-left">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold">Diagnóstico de servicios</h2>
          <p className="text-sm text-neutral-400">Comprobación detallada bajo demanda.</p>
        </div>
        <button type="button" onClick={runChecks} disabled={loading} className="rounded-lg border border-neutral-700 px-3 py-2 text-sm hover:bg-neutral-800 disabled:opacity-50">
          {loading ? "Comprobando…" : "Volver a comprobar"}
        </button>
      </div>
      <ul className="mt-4 space-y-3">
        {results.map((result) => (
          <li key={result.name} className="flex items-center justify-between gap-3 text-sm">
            <span>{result.name}</span>
            <span className={result.ok ? "text-green-400" : "text-red-400"}>{result.ok ? "Correcto" : "Error"} · {result.detail}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
