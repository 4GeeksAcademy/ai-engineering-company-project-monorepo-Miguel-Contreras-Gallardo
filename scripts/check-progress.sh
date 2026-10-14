#!/usr/bin/env bash
# check-progress.sh — Verifica el progreso del Inventory Manager
# Uso: bash scripts/check-progress.sh

set -e

echo "=== TrackFlow Inventory Manager — Progress Check ==="
echo ""

# Verificar archivos de configuración
echo "📁 Configuration files:"
for f in CONTEXT.md memory-bank/projectbrief.md memory-bank/techContext.md memory-bank/progress.md AGENTS.md; do
    if [ -f "$f" ]; then
        echo "  ✅ $f"
    else
        echo "  ❌ $f — MISSING"
    fi
done

echo ""

# Verificar directorios .agents
echo "🤖 .agents/ rules:"
for f in .agents/rules-index.md .agents/rules-python.md .agents/rules-postgres.md .agents/rules-testing.md .agents/rules-git.md; do
    if [ -f "$f" ]; then
        echo "  ✅ $f"
    else
        echo "  ❌ $f — MISSING"
    fi
done

echo ""

# Verificar skill
echo "🧠 Skills:"
for f in skills/inventory-tasks/SKILL.md skills/inventory-tasks/examples/T05-implementation.md skills/inventory-tasks/resources/task-reference.md; do
    if [ -f "$f" ]; then
        echo "  ✅ $f"
    else
        echo "  ❌ $f — MISSING"
    fi
done

echo ""

# Verificar archivos del servicio API
echo "⚙️  API Service files:"
for f in services/api/app/main.py services/api/app/config.py services/api/app/db/__init__.py services/api/app/db/base.py services/api/app/db/models.py services/api/app/routers/__init__.py services/api/app/routers/inventory.py services/api/app/services/inventory.py; do
    if [ -f "$f" ]; then
        echo "  ✅ $f"
    else
        echo "  ❌ $f — MISSING"
    fi
done

echo ""

# Verificar specs
echo "📋 Specs:"
for f in specs/inventory-manager/spec.md specs/inventory-manager/plan.md specs/inventory-manager/tasks.md; do
    if [ -f "$f" ]; then
        echo "  ✅ $f"
    else
        echo "  ❌ $f — MISSING"
    fi
done

echo ""
echo "=== Check complete ==="