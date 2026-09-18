#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
#  TrustMoss — Automated Zero-Conflict Local Launcher
#  Automatically detects and clears conflicting processes on ports 8000 & 3000,
#  then starts the full TrustMoss microservice topology with health checks.
# ═══════════════════════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "🔍 Checking for port conflicts on 8000 (Gateway) and 3000 (Web UI)..."

# Check if port 8000 is occupied by a background container in default Docker context
if ss -tulpn 2>/dev/null | grep -q ":8000 "; then
    echo "⚠️  Port 8000 is occupied. Stopping conflicting background container..."
    docker --context default stop ai-code-debugger-backend-1 2>/dev/null || true
    fuser -k 8000/tcp 2>/dev/null || true
fi

# Check if port 3000 is occupied by a background container in default Docker context
if ss -tulpn 2>/dev/null | grep -q ":3000 "; then
    echo "⚠️  Port 3000 is occupied. Stopping conflicting background container..."
    docker --context default stop techtalk_app 2>/dev/null || true
    fuser -k 3000/tcp 2>/dev/null || true
fi

echo "🧹 Cleaning up any orphaned TrustMoss containers..."
docker compose down --remove-orphans 2>/dev/null || true

echo "🚀 Starting TrustMoss microservices stack..."
docker compose up -d

echo ""
echo "✅ All TrustMoss microservices launched successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🌐 Web Operations Console : http://localhost:3000"
echo "  🛡️  Trust Gateway API Docs : http://localhost:8000/docs"
echo "  🩺 Gateway Health Probe   : http://localhost:8000/health"
echo "  🔒 HashiCorp Vault UI     : http://localhost:8200"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "To inspect containers: docker compose ps"
echo "To stop containers:    docker compose down"
