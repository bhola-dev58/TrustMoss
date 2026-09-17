"""
secrets.py — TrustMoss Unified Secret Provider
===============================================
Transparent secret resolution layer supporting three providers:

  1. HashiCorp Vault  — production / staging (VAULT_ADDR + VAULT_TOKEN env vars present)
  2. AWS Secrets Mgr  — AWS-hosted production   (AWS_SECRET_NAME env var present)
  3. Environment vars — local dev / Docker Compose / CI fallback (default)

Usage (drop-in replacement for os.getenv):

    from secrets import get_secret, get_required_secret

    groq_key  = get_secret("GROQ_API_KEY")           # returns None if missing
    enc_key   = get_required_secret("ENCRYPTION_KEY") # raises RuntimeError if missing

Provider selection:
    Set SECRET_PROVIDER=vault | aws | env  to override auto-detection.
    Auto-detection order: vault → aws → env
"""

from __future__ import annotations

import logging
import os
from enum import Enum
from typing import Optional

logger = logging.getLogger("trustmoss.secrets")


# ─────────────────────────────────────────────────────────────────────────────
# Provider Enum
# ─────────────────────────────────────────────────────────────────────────────

class SecretProvider(str, Enum):
    VAULT = "vault"
    AWS   = "aws"
    ENV   = "env"


# ─────────────────────────────────────────────────────────────────────────────
# Provider Detection
# ─────────────────────────────────────────────────────────────────────────────

def _detect_provider() -> SecretProvider:
    """
    Auto-detect the active secret provider.
    Explicit SECRET_PROVIDER env var always wins.
    """
    explicit = os.getenv("SECRET_PROVIDER", "").lower().strip()
    if explicit == SecretProvider.VAULT:
        return SecretProvider.VAULT
    if explicit == SecretProvider.AWS:
        return SecretProvider.AWS
    if explicit == SecretProvider.ENV:
        return SecretProvider.ENV

    # Auto-detect: Vault takes priority if configured
    if os.getenv("VAULT_ADDR") and os.getenv("VAULT_TOKEN"):
        return SecretProvider.VAULT

    # Auto-detect: AWS if a secret name is configured
    if os.getenv("AWS_SECRET_NAME"):
        return SecretProvider.AWS

    return SecretProvider.ENV


# Module-level provider (resolved once at import time)
_PROVIDER: SecretProvider = _detect_provider()


# ─────────────────────────────────────────────────────────────────────────────
# Vault Provider
# ─────────────────────────────────────────────────────────────────────────────

# In-memory cache: avoids repeated Vault API calls within the same process
_vault_cache: dict[str, str] = {}


def _get_from_vault(key: str) -> Optional[str]:
    """
    Fetch a secret from HashiCorp Vault KV v2.
    Path: secret/trustmoss → field: <key>

    Requires: pip install hvac
    """
    if key in _vault_cache:
        return _vault_cache[key]

    vault_addr  = os.getenv("VAULT_ADDR", "http://vault:8200")
    vault_token = os.getenv("VAULT_TOKEN", "")
    vault_path  = os.getenv("VAULT_SECRET_PATH", "trustmoss")
    vault_mount = os.getenv("VAULT_MOUNT", "secret")

    try:
        import hvac  # type: ignore
    except ImportError:
        logger.warning(
            "hvac package not installed. Install with: pip install hvac. "
            "Falling back to environment variable for key=%s", key
        )
        return os.getenv(key)

    try:
        client = hvac.Client(url=vault_addr, token=vault_token)
        if not client.is_authenticated():
            logger.error("Vault authentication failed — token may be expired or invalid.")
            return os.getenv(key)

        response = client.secrets.kv.v2.read_secret_version(
            path=vault_path,
            mount_point=vault_mount,
        )
        secrets_data: dict = response["data"]["data"]

        # Cache all fetched secrets from this path to avoid N+1 Vault calls
        _vault_cache.update(secrets_data)
        logger.info("Fetched %d secret(s) from Vault path=%s/%s", len(secrets_data), vault_mount, vault_path)

        return secrets_data.get(key)

    except Exception as exc:  # noqa: BLE001
        logger.error("Vault secret fetch failed for key=%s: %s. Falling back to env.", key, exc)
        return os.getenv(key)


# ─────────────────────────────────────────────────────────────────────────────
# AWS Secrets Manager Provider
# ─────────────────────────────────────────────────────────────────────────────

_aws_cache: dict[str, str] = {}


def _get_from_aws(key: str) -> Optional[str]:
    """
    Fetch a secret from AWS Secrets Manager.
    Expects the secret to be a JSON blob: {"GROQ_API_KEY": "...", "ENCRYPTION_KEY": "..."}

    Requires: pip install boto3
    """
    if key in _aws_cache:
        return _aws_cache[key]

    secret_name = os.getenv("AWS_SECRET_NAME", "trustmoss/production")
    region      = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))

    try:
        import boto3  # type: ignore
        import json as _json
        from botocore.exceptions import ClientError  # type: ignore
    except ImportError:
        logger.warning(
            "boto3 not installed. Install with: pip install boto3. "
            "Falling back to environment variable for key=%s", key
        )
        return os.getenv(key)

    try:
        client   = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
        secrets_data: dict = _json.loads(response["SecretString"])

        # Cache all fields from this secret
        _aws_cache.update(secrets_data)
        logger.info(
            "Fetched %d secret(s) from AWS Secrets Manager secret=%s region=%s",
            len(secrets_data), secret_name, region
        )

        return secrets_data.get(key)

    except Exception as exc:  # noqa: BLE001
        logger.error("AWS Secrets Manager fetch failed for key=%s: %s. Falling back to env.", key, exc)
        return os.getenv(key)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Resolve a secret by key using the configured provider.

    Returns:
        The secret value as a string, or `default` if not found.

    Provider order (auto-detected at startup):
        VAULT → AWS → ENV
    """
    if _PROVIDER == SecretProvider.VAULT:
        value = _get_from_vault(key)
    elif _PROVIDER == SecretProvider.AWS:
        value = _get_from_aws(key)
    else:
        value = os.getenv(key)

    if value is None:
        logger.debug("Secret key=%s not found in provider=%s — returning default.", key, _PROVIDER)
        return default

    return value


def get_required_secret(key: str) -> str:
    """
    Resolve a secret by key. Raises RuntimeError if not found.

    Use this for secrets that MUST be present for the service to function
    (e.g. ENCRYPTION_KEY, JWT_SECRET_KEY) — fail-fast at startup rather
    than producing a cryptic error deep in a request handler.

    Raises:
        RuntimeError: If the secret is not found in any provider.
    """
    value = get_secret(key)
    if not value:
        raise RuntimeError(
            f"[TrustMoss] Required secret '{key}' is not configured. "
            f"Provider: {_PROVIDER}. "
            f"Set {key} in your .env file, Vault path secret/{os.getenv('VAULT_SECRET_PATH', 'trustmoss')}, "
            f"or AWS Secrets Manager secret '{os.getenv('AWS_SECRET_NAME', 'trustmoss/production')}'."
        )
    return value


def active_provider() -> SecretProvider:
    """Return the currently active secret provider (for observability/health checks)."""
    return _PROVIDER


def invalidate_cache() -> None:
    """
    Clear the in-process secret cache.
    Call this after secret rotation to force a fresh fetch on next access.
    """
    global _vault_cache, _aws_cache
    _vault_cache.clear()
    _aws_cache.clear()
    logger.info("Secret cache invalidated — next access will re-fetch from %s.", _PROVIDER)
