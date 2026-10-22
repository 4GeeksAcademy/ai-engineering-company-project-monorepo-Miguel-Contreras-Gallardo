"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [backendStatus, setBackendStatus] = useState("consultando…");
  const [dbStatus, setDbStatus] = useState("");

  useEffect(() => {
    // Detectar si estamos en Codespaces (URL tipo *-3000.app.github.dev)
  const isCodespaces = window.location.hostname.includes("app.github.dev");
  const apiUrl = isCodespaces
    ? window.location.hostname.replace("-3000", "-8001")
    : window.location.hostname;

  fetch(window.location.protocol + "//" + apiUrl + "/status")
      .then((res) => res.json())
      .then((data) => {
        setBackendStatus(data.status);
        setDbStatus(data.database);
      })
      .catch(() => {
        setBackendStatus("error");
        setDbStatus("inaccesible");
      });
  }, []);

  const isOnline = backendStatus === "ok";

  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-neutral-950 text-neutral-100 p-6">
      <div className="max-w-md w-full text-center space-y-8">
        {/* Logo / título */}
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-widest text-neutral-500">
            TrackFlow
          </p>
          <h1 className="text-4xl font-bold tracking-tight">MVP en marcha</h1>
          <p className="text-neutral-400 text-sm">
            Aplicación mínima — frontend conectado al backend
          </p>
        </div>

        {/* Indicador de estado */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-neutral-400">Backend</span>
            <span
              className={`inline-flex items-center gap-1.5 text-sm font-medium ${
                isOnline ? "text-green-400" : "text-red-400"
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  isOnline ? "bg-green-400" : "bg-red-400"
                }`}
              />
              {isOnline ? "online" : "offline"}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-neutral-400">Base de datos</span>
            <span
              className={`inline-flex items-center gap-1.5 text-sm font-medium ${
                dbStatus === "connected" ? "text-green-400" : "text-amber-400"
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  dbStatus === "connected" ? "bg-green-400" : "bg-amber-400"
                }`}
              />
              {dbStatus || "—"}
            </span>
          </div>
        </div>

        <p className="text-xs text-neutral-600">
          {isOnline
            ? "Conexión establecida correctamente ✅"
            : "No se pudo contactar con el backend ❌"}
        </p>
      </div>
    </main>
  );
}