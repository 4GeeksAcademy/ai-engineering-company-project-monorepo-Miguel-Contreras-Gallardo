# TrackFlow API — Dockerfile
# Servicio FastAPI con Python + uv

FROM python:3.12-slim

WORKDIR /app

# Instalar uv (gestor de paquetes rápido)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copiar dependencias primero (caching)
COPY services/api/requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copiar código fuente
COPY services/api/ .
COPY services/telemetry/ /app/services/telemetry/
COPY services/reporting/ /app/services/reporting/
COPY data/pipelines/ /app/data/pipelines/
COPY data/process/reporting/ /app/data/process/reporting/

# Puerto de la API
EXPOSE 8000

# Arrancar Uvicorn con recarga en desarrollo
CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]