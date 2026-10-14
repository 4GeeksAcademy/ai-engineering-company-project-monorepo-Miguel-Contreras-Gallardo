# TrackFlow API — Dockerfile
# Servicio FastAPI con Python + uv

FROM python:3.12-slim

WORKDIR /app

# Instalar uv (gestor de paquetes rápido)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copiar dependencias primero (caching)
COPY api/requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copiar código fuente
COPY api/ .

# Puerto de la API
EXPOSE 8000

# Arrancar Uvicorn con recarga en desarrollo
CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]