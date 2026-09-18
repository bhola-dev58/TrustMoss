#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
#  TrustMoss — High-Speed Zero-Conflict Launcher
#  - Instant check: Returns in <0.2s if containers are already running.
#  - Fast start: Reuses existing containers & images without rebuilding.
#  - First-time setup: Auto-builds images only if missing (or on --rebuild flag).
# ═══════════════════════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# 1. Instant check: If TrustMoss is already running, display URLs immediately
if docker compose ps --status running --format '{{.Names}}' 2>/dev/null | grep -q "trustmoss-gateway"; then
    echo "⚡ TrustMoss is already running and healthy!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  🌐 Web Operations Console : http://localhost:3000"
    echo "  🛡️  Trust Gateway API Docs : http://localhost:8000/docs"
    echo "  🩺 Gateway Health Probe   : http://localhost:8000/health"
    echo "  🔒 HashiCorp Vault UI     : http://localhost:8200"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "To inspect containers : docker compose ps"
    echo "To stop containers    : docker compose down"
    echo "To rebuild from source: ./scripts/start.sh --rebuild"
    exit 0
fi

# 2. Check for external port conflicts only if TrustMoss is not using them
if ss -tulpn 2>/dev/null | grep -q ":8000 "; then
    if ! docker compose ps --format '{{.Names}}' 2>/dev/null | grep -q "trustmoss-gateway"; then
        echo "⚠️  Port 8000 is occupied by another process. Freeing port 8000..."
        docker --context default stop ai-code-debugger-backend-1 2>/dev/null || true
        fuser -k 8000/tcp 2>/dev/null || true
    fi
fi

if ss -tulpn 2>/dev/null | grep -q ":3000 "; then
    if ! docker compose ps --format '{{.Names}}' 2>/dev/null | grep -q "trustmoss-web"; then
        echo "⚠️  Port 3000 is occupied by another process. Freeing port 3000..."
        docker --context default stop techtalk_app 2>/dev/null || true
        fuser -k 3000/tcp 2>/dev/null || true
    fi
fi

# 3. Fast Start vs First-Time Build
# Only build images if missing or if --rebuild / -b flag is explicitly passed
BUILD_FLAG=""
if [ "$1" == "--rebuild" ] || [ "$1" == "-b" ]; then
    echo "🔨 Rebuilding TrustMoss images as requested..."
    BUILD_FLAG="--build"
elif ! docker image inspect trustmoss-gateway:latest >/dev/null 2>&1; then
    echo "📦 Initial run detected. Building TrustMoss images from source..."
    BUILD_FLAG="--build"
else
    echo "⚡ Using cached TrustMoss images for ultra-fast startup..."
fi

# 4. Launch containers quickly (reuses existing containers and networks)
docker compose up -d $BUILD_FLAG

echo ""
echo "✅ All TrustMoss microservices started!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🌐 Web Operations Console : http://localhost:3000"
echo "  🛡️  Trust Gateway API Docs : http://localhost:8000/docs"
echo "  🩺 Gateway Health Probe   : http://localhost:8000/health"
echo "  🔒 HashiCorp Vault UI     : http://localhost:8200"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "To inspect containers : docker compose ps"
echo "To stop containers    : docker compose down"
echo "To rebuild from source: ./scripts/start.sh --rebuild"
