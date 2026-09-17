# TrustMoss — Secrets Management Architecture

> **Specification:** Enterprise Secret Provider — Phase 8  
> **Provider Options:** HashiCorp Vault | AWS Secrets Manager | Environment Variables  
> **Status:** Production-ready abstraction layer (Task 8.1–8.3 complete)

---

## Overview

TrustMoss implements a **unified secret abstraction layer** (`apps/api/secrets.py`) that transparently resolves credentials from three provider tiers, selected automatically at startup:

```
Priority: SECRET_PROVIDER env var (explicit) → Vault auto-detect → AWS auto-detect → ENV
```

| Provider | When Active | Use Case |
| :--- | :--- | :--- |
| `vault` | `VAULT_ADDR` + `VAULT_TOKEN` set | Local dev with Docker Compose, staging |
| `aws` | `AWS_SECRET_NAME` set | AWS-hosted production |
| `env` | Default (neither above set) | CI pipelines, simple local dev |

---

## Secret Inventory

All secrets used by TrustMoss:

| Secret Key | Description | Required | Rotation Frequency |
| :--- | :--- | :--- | :--- |
| `GROQ_API_KEY` | Groq LLM API authentication | ✅ Yes | Monthly |
| `GROQ_MODEL` | Groq model name (non-sensitive) | No | On model upgrade |
| `MOSS_API_KEY` | Moss retrieval engine API key | ✅ Yes | Monthly |
| `MOSS_API_URL` | Moss service endpoint | ✅ Yes | On infra change |
| `LIVEKIT_URL` | LiveKit WebRTC server URL | ✅ Yes | On infra change |
| `LIVEKIT_API_KEY` | LiveKit API authentication | ✅ Yes | Quarterly |
| `LIVEKIT_API_SECRET` | LiveKit signing secret | ✅ Yes | Quarterly |
| `ENCRYPTION_KEY` | AES-256-GCM master key (64-char hex) | ✅ Yes | Annually + on breach |
| `JWT_SECRET_KEY` | JWT signing secret (HS256) | ✅ Yes | Quarterly |

---

## Provider Setup Guides

### Option A — Environment Variables (Local Dev / CI)

Default — no additional setup required.

```bash
# Copy the template and fill in your values
cp apps/api/.env.example apps/api/.env
# Edit apps/api/.env with real credentials
```

**Generate a secure ENCRYPTION_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

### Option B — HashiCorp Vault (Docker Compose Dev Mode)

```bash
# 1. Start all services (includes Vault on port 8200)
docker compose up -d

# 2. Seed TrustMoss secrets into Vault
VAULT_ADDR=http://localhost:8200 \
VAULT_TOKEN=dev-root-token \
bash scripts/vault-init.sh

# 3. Enable Vault provider by uncommenting in docker-compose.yml:
#    - SECRET_PROVIDER=vault
#    - VAULT_ADDR=http://vault:8200
#    - VAULT_TOKEN=dev-root-token

# 4. Restart the gateway to pick up the new provider
docker compose restart trustmoss-gateway
```

**Vault UI:** Open http://localhost:8200 (token: `dev-root-token`)  
**Secret path:** `secret/trustmoss`

> **⚠️ Dev mode only.** Vault dev mode does not persist data. Secrets are lost on container restart. Always re-run `vault-init.sh` after restart.

---

### Option C — AWS Secrets Manager (Production)

```bash
# 1. Create the secret in AWS
aws secretsmanager create-secret \
  --name trustmoss/production \
  --secret-string '{
    "GROQ_API_KEY": "your-real-groq-key",
    "ENCRYPTION_KEY": "your-64-char-hex-key",
    "LIVEKIT_API_KEY": "your-lk-key",
    "LIVEKIT_API_SECRET": "your-lk-secret",
    "JWT_SECRET_KEY": "your-jwt-secret"
  }' \
  --region us-east-1

# 2. Set env vars (ECS task definition or EC2 instance role)
export SECRET_PROVIDER=aws
export AWS_SECRET_NAME=trustmoss/production
export AWS_REGION=us-east-1

# 3. Ensure the runtime has IAM permission:
#    Action: secretsmanager:GetSecretValue
#    Resource: arn:aws:secretsmanager:us-east-1:*:secret:trustmoss/production-*
```

---

## GitHub Actions Secrets Setup (Task 8.3)

Configure these in: **GitHub repo → Settings → Secrets and variables → Actions → New repository secret**

| GitHub Secret Name | Maps To | Required For |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | `GROQ_API_KEY` | Integration tests (real LLM calls) |
| `MOSS_API_KEY` | `MOSS_API_KEY` | Integration tests (real retrieval) |
| `ENCRYPTION_KEY` | `ENCRYPTION_KEY` | Crypto integration tests |
| `LIVEKIT_API_KEY` | `LIVEKIT_API_KEY` | Voice gateway integration tests |
| `LIVEKIT_API_SECRET` | `LIVEKIT_API_SECRET` | Voice gateway integration tests |
| `JWT_SECRET_KEY` | `JWT_SECRET_KEY` | Auth integration tests |
| `DOCKER_USERNAME` | Docker Hub login | `release.yml` (optional) |
| `DOCKER_TOKEN` | Docker Hub PAT | `release.yml` (optional) |

> **Unit tests** (the 121-test suite in CI) use **stub values** and do NOT require these secrets.  
> **Integration tests** (future Phase 9) will require real credentials injected from GitHub Secrets.

---

## Secret Rotation Procedure

```bash
# 1. Generate a new key
NEW_ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# 2. Update in Vault (dev)
vault kv patch secret/trustmoss ENCRYPTION_KEY="$NEW_ENCRYPTION_KEY"

# OR update in AWS (production)
aws secretsmanager update-secret \
  --secret-id trustmoss/production \
  --secret-string "$(aws secretsmanager get-secret-value \
    --secret-id trustmoss/production \
    --query SecretString \
    --output text | python3 -c "
import json, sys
s = json.load(sys.stdin)
s['ENCRYPTION_KEY'] = '$NEW_ENCRYPTION_KEY'
print(json.dumps(s))
")"

# 3. Invalidate in-process cache (zero-downtime rotation)
# Call: POST /api/admin/secrets/refresh  (future endpoint)
# Or simply restart the gateway container
docker compose restart trustmoss-gateway
```

---

## Implementation Files

| File | Purpose |
| :--- | :--- |
| [`apps/api/secrets.py`](../apps/api/secrets.py) | Unified secret provider with Vault/AWS/ENV backends |
| [`apps/api/tests/test_secrets.py`](../apps/api/tests/test_secrets.py) | 15 unit tests for all provider paths |
| [`scripts/vault-init.sh`](../scripts/vault-init.sh) | Vault dev mode seed script |
| [`docker-compose.yml`](../docker-compose.yml) | Vault service definition (port 8200) |
| [`apps/api/.env.example`](../apps/api/.env.example) | Full env var template including secrets config |
| [`.github/SECRETS_SETUP.md`](../github/SECRETS_SETUP.md) | GitHub repo secrets configuration guide |
