# 🎯 Active Context — Sesión Actual

> **Última actualización:** 2026-11-18
> **Sesión:** Preparación de forecasting de ventas TrackFlow
> **Documentos relacionados:** `CONTEXT.md` · `pyproject.toml` · `uv.lock` · `data/raw/` · briefing/dataset pendientes de localizar

---

## 📌 Objetivo de la Sesión

Preparar el entorno para crear un modelo de forecasting con el dataset histórico real de TrackFlow, sin fabricar datos ni inferir columnas o estacionalidad que no estén documentadas.

---

## ✅ Progreso de esta sesión

- [x] Leído `CONTEXT.md` completo para verificar el contexto general de TrackFlow.
- [x] Instalado `uv 0.13.9` con el instalador oficial de Astral y verificado en el `PATH`. `pyproject.toml` ya existía, así que no se ejecutó `uv init`.
- [x] Ejecutado `uv add --optional forecasting --no-sync scikit-learn pandas matplotlib`; `uv lock --check` pasó. No se usaron `pip` ni `pipenv`.
- [ ] `uv sync --locked --extra forecasting --no-build` no pudo instalar `scikit-learn==1.9.1`: no hay wheel compatible con el entorno Alpine/musl actual.
- [ ] La política de exclusión de la organización impide consultar `data/raw/`. No se encontró `CONTEXT-trackflow.md` y no se proporcionó el enlace al repositorio de referencia. No se generaron datos ni se escribió código de forecasting.
---

## 🚀 Siguiente Acción Inmediata

> **Próxima acción:** disponer de una fuente autorizada del ejercicio con el CSV histórico original y el briefing específico de TrackFlow. Leer el briefing completo antes de escribir código de forecasting.

> **Antes de comenzar:** inspeccionar `git status` y preservar los cambios locales no relacionados.

---

## 📋 Próximos Pasos (Priorizados)

| Prioridad | Tarea | Dónde |
|---|---|---|
| 🟢 P2 | Pipeline de ingesta de pedidos | `data/` |
| 🟢 P2 | Base de conocimiento para RAG (CX) | IA |
| 🟢 P2 | Restricción roles DB solo INSERT/SELECT (T03) | `services/api/` |
| 🔵 P3 | Agente orquestador multi-departamento | Visión final |

### Continuidad forecasting (2026-11-18)

1. Usar `data/raw/trackflow_sales.csv` solo si el acceso está autorizado, o el dataset oficial autorizado del ejercicio en `content/contexts/sales-forecasting/trackflow/trackflow_sales.csv`. No generar, simular ni reconstruir datos.
2. Leer `CONTEXT-trackflow.md` completo antes de escribir código. Verificar el significado y esquema de las columnas, el rango de fechas y la estacionalidad descrita.
3. En un entorno Linux con glibc y wheels compatibles, ejecutar `uv sync --locked --extra forecasting`.
4. Tratar nulos y vacíos, separar los primeros 8 años para entrenamiento y los 2 más recientes para prueba, y ajustar el preprocesamiento solo con los datos de entrenamiento. Escalar solo si alguna transformación lo requiere; Random Forest no necesita escalado por sí mismo.
5. Entrenar Random Forest con `scikit-learn` y documentar la elección según el tamaño observado del dataset, la explicabilidad y el tiempo de ajuste disponible. Reservar la prueba para comprobar el resultado, sin usarla para entrenar ni ajustar el modelo.