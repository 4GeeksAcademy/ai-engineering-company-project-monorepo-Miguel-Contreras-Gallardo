#!/usr/bin/env bash
# TrackFlow — Deploy script
# Uso: ./scripts/deploy.sh
# Requisitos: acceso SSH al VPS, docker-compose en el VPS
# Despliega el stack completo de TrackFlow en producción.

set -euo pipefail

VPS="root@207.154.214.100"
REPO_URL="https://github.com/4GeeksAcademy/ai-engineering-company-project-monorepo-Miguel-Contreras-Gallardo.git"
BRANCH="feature/docker-infrastructure"

echo "========================================"
echo "  TrackFlow — Deploy a producción"
echo "  VPS: $VPS"
echo "  Rama: $BRANCH"
echo "========================================"

ssh "$VPS" << 'SSHSESSION'
  set -e

  REPO_DIR="/opt/trackflow"

  # Instalar Docker si no existe
  if ! command -v docker &> /dev/null; then
    echo "-> Instalando Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
  fi

  # Instalar Docker Compose plugin si no existe
  if ! docker compose version &>/dev/null; then
    echo "-> Instalando Docker Compose plugin..."
    apt-get update && apt-get install -y docker-compose-plugin
  fi

  # Clonar o actualizar repo
  if [ -d "$REPO_DIR" ]; then
    echo "-> Actualizando repo..."
    cd "$REPO_DIR"
    git fetch origin
    git checkout "$BRANCH" 2>/dev/null || git checkout -b "$BRANCH" origin/"$BRANCH"
    git pull origin "$BRANCH"
  else
    echo "-> Clonando repo..."
    git clone --branch "$BRANCH" "$REPO_URL" "$REPO_DIR"
    cd "$REPO_DIR"
  fi

  # Crear .env si no existe
  if [ ! -f ".env" ]; then
    echo "-> Creando .env..."
    cat > .env << 'ENVEOF'
POSTGRES_USER=trackflow
POSTGRES_PASSWORD=change_this_password
POSTGRES_DB=trackflow
POSTGRES_PORT=5432
API_PORT=8000
DEBUG=false
WEBSITE_PORT=3000
BACKOFFICE_PORT=3001
ENVEOF
    echo "⚠️  REVISA y cambia las contraseñas en .env antes de continuar"
  fi

  # Detener contenedores anteriores y levantar nuevos
  echo "-> Desplegando contenedores..."
  docker compose down
  docker compose pull
  docker compose up --build -d

  # Verificar
  echo ""
  echo "-> Estado de los contenedores:"
  docker compose ps
  echo ""
  echo "✅ Deploy completado"
SSHSESSION

echo "========================================"
echo "  ¡Deploy realizado!"
echo "========================================"
