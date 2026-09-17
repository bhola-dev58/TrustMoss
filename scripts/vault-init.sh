#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
#  scripts/vault-init.sh — TrustMoss Vault Secret Seed Script (Dev Mode)
#
#  Seeds all TrustMoss application secrets into HashiCorp Vault KV v2.
#
#  Usage:
#    # After `docker compose up -d` with Vault running:
#    VAULT_ADDR=http://localhost:8200 VAULT_TOKEN=dev-root-token bash scripts/vault-init.sh
#
#  What this does:
#    1. Enables the KV v2 secret engine at path "secret/"
#    2. Writes all TrustMoss secrets to secret/trustmoss
#    3. Verifies the write by reading back the secrets
#
#  ⚠️  This script is for LOCAL DEVELOPMENT ONLY.
#      In production: use Vault's AppRole auth, not a root token.
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
VAULT_TOKEN="${VAULT_TOKEN:-dev-root-token}"
VAULT_SECRET_PATH="${VAULT_SECRET_PATH:-trustmoss}"
VAULT_MOUNT="${VAULT_MOUNT:-secret}"

export VAULT_ADDR VAULT_TOKEN

echo "════════════════════════════════════════════════════"
echo "  TrustMoss Vault Init — Dev Mode Secret Seeding"
echo "  Vault: ${VAULT_ADDR}"
echo "  Path:  ${VAULT_MOUNT}/${VAULT_SECRET_PATH}"
echo "════════════════════════════════════════════════════"

# ── Wait for Vault to be ready ────────────────────────────────────────────────
echo ""
echo "→ Waiting for Vault to be ready..."
MAX_ATTEMPTS=30
ATTEMPT=0
until vault status -address="${VAULT_ADDR}" > /dev/null 2>&1; do
    ATTEMPT=$((ATTEMPT + 1))
    if [ "$ATTEMPT" -ge "$MAX_ATTEMPTS" ]; then
        echo "ERROR: Vault did not become ready in time. Is it running?"
        echo "  Run: docker compose up -d vault"
        exit 1
    fi
    echo "  Waiting... (${ATTEMPT}/${MAX_ATTEMPTS})"
    sleep 2
done
echo "  Vault is ready ✓"

# ── Enable KV v2 secret engine (idempotent) ───────────────────────────────────
echo ""
echo "→ Enabling KV v2 secret engine at ${VAULT_MOUNT}/..."
vault secrets enable \
    -address="${VAULT_ADDR}" \
    -version=2 \
    -path="${VAULT_MOUNT}" \
    kv 2>/dev/null || echo "  (KV engine already enabled — skipping)"

# ── Seed TrustMoss secrets ────────────────────────────────────────────────────
# Values are read from the local .env file if it exists,
# otherwise placeholder values are used (safe for dev only).
echo ""
echo "→ Seeding secrets to ${VAULT_MOUNT}/data/${VAULT_SECRET_PATH}..."

# Load .env file if present
ENV_FILE="./apps/api/.env"
if [ -f "$ENV_FILE" ]; then
    # shellcheck source=/dev/null
    set -a; source "$ENV_FILE"; set +a
    echo "  Loaded credentials from ${ENV_FILE}"
else
    echo "  WARNING: ${ENV_FILE} not found — using placeholder values"
    echo "  Copy apps/api/.env.example to apps/api/.env and fill in real values first."
fi

vault kv put \
    -address="${VAULT_ADDR}" \
    "${VAULT_MOUNT}/${VAULT_SECRET_PATH}" \
    "GROQ_API_KEY=${GROQ_API_KEY:-dev-stub-groq-key}" \
    "GROQ_MODEL=${GROQ_MODEL:-llama-3.1-8b-instant}" \
    "MOSS_API_KEY=${MOSS_API_KEY:-dev-stub-moss-key}" \
    "MOSS_API_URL=${MOSS_API_URL:-http://localhost:9999}" \
    "LIVEKIT_URL=${LIVEKIT_URL:-wss://dev.livekit.cloud}" \
    "LIVEKIT_API_KEY=${LIVEKIT_API_KEY:-devkey}" \
    "LIVEKIT_API_SECRET=${LIVEKIT_API_SECRET:-devsecret}" \
    "ENCRYPTION_KEY=${ENCRYPTION_KEY:-0000000000000000000000000000000000000000000000000000000000000000}" \
    "JWT_SECRET_KEY=${JWT_SECRET_KEY:-dev-jwt-secret-key-not-for-production}"

echo "  Secrets written ✓"

# ── Verify by reading back ────────────────────────────────────────────────────
echo ""
echo "→ Verifying secrets (listing keys only — values redacted)..."
vault kv get \
    -address="${VAULT_ADDR}" \
    -format=json \
    "${VAULT_MOUNT}/${VAULT_SECRET_PATH}" \
    | python3 -c "
import json, sys
data = json.load(sys.stdin)
keys = list(data['data']['data'].keys())
print(f'  Stored {len(keys)} secret(s): {keys}')
"

echo ""
echo "════════════════════════════════════════════════════"
echo "  Vault seeding complete!"
echo ""
echo "  To use Vault as secret provider, set in docker-compose.yml:"
echo "    - SECRET_PROVIDER=vault"
echo "    - VAULT_ADDR=http://vault:8200"
echo "    - VAULT_TOKEN=dev-root-token"
echo ""
echo "  Or export locally:"
echo "    export SECRET_PROVIDER=vault"
echo "    export VAULT_ADDR=${VAULT_ADDR}"
echo "    export VAULT_TOKEN=${VAULT_TOKEN}"
echo "════════════════════════════════════════════════════"
