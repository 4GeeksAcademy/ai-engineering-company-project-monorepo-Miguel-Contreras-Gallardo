# TrackFlow API — Dockerfile
# Servicio FastAPI con Python + uv (backend)

FROM python:3.13-slim

WORKDIR /app

# Instalar uv (gestor de paquetes rápido)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copiar dependencias primero (caching)
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copiar código fuente
COPY . .

# Puerto de la API
EXPOSE 8000

# Arrancar Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]