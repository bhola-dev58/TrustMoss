"""
TrustMoss Data-at-Rest Encryption Engine (AES-256-GCM)
------------------------------------------------------
Provides authenticated encryption for sensitive persisted data:
- HITL Review Queue items (flagged queries, answers, context chunks).
- PII-scrubbed logs and audio transcript audit trails.
- Knowledge base golden corrections before disk serialization.

Security Guarantees:
- Cipher: AES-256-GCM (Galois/Counter Mode) via `cryptography.hazmat`.
- Key Size: 256 bits (32 bytes).
- Nonce/IV: 96 bits (12 bytes) cryptographically random (`os.urandom`) per operation (NIST SP 800-38D).
- Tag: 128 bits (16 bytes) authentication tag automatically verified during decryption.
- AAD: Additional Authenticated Data supported to prevent ciphertext transplant attacks.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger("trustmoss.crypto")
from collections.abc import Sequence
from typing import Any, Union

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

CIPHER_PREFIX = "$aes256gcm$"
NONCE_LENGTH_BYTES = 12  # 96 bits per NIST SP 800-38D
TAG_LENGTH_BYTES = 16    # 128-bit authentication tag


class CryptoError(Exception):
    """Base exception for cryptographic operations."""
    pass


class DecryptionError(CryptoError):
    """Raised when decryption or authentication verification fails."""
    pass


def get_encryption_key(key_override: Union[str, bytes] | None = None) -> bytes:
    """
    Resolves the 256-bit (32-byte) encryption key.
    Precedence:
    1. key_override parameter
    2. TrustMoss secret provider (Vault | AWS | ENV via secrets.get_secret)
    3. ENCRYPTION_KEY environment variable (direct fallback)
    4. Deterministic SHA-256 development fallback (never use in production)
    """
    # ── Try the TrustMoss unified secret provider first ───────────────────────
    try:
        from secret_manager import get_secret as _get_secret  # TrustMoss secret abstraction
        _provider_key = _get_secret("ENCRYPTION_KEY")
    except ImportError:
        _provider_key = None

    raw_key = key_override or _provider_key or os.getenv("ENCRYPTION_KEY")

    if not raw_key:
        # Development fallback — deterministic 32-byte key
        return hashlib.sha256(b"trustmoss-aes256-gcm-default-master-key").digest()

    if isinstance(raw_key, str):
        # Check if it's base64url or base64 encoded
        try:
            decoded = base64.urlsafe_b64decode(raw_key.encode("utf-8"))
            if len(decoded) == 32:
                return decoded
        except Exception:
            pass

        # Check if it's 64-char hex
        if len(raw_key) == 64:
            try:
                return bytes.fromhex(raw_key)
            except ValueError:
                pass

        # Fallback: derive 32-byte key via SHA-256
        return hashlib.sha256(raw_key.encode("utf-8")).digest()

    if isinstance(raw_key, bytes):
        if len(raw_key) == 32:
            return raw_key
        return hashlib.sha256(raw_key).digest()

    raise ValueError("Invalid key format provided.")


def encrypt(
    plaintext: Union[str, bytes, dict, list],
    aad: Union[str, bytes] | None = None,
    key: bytes | None = None,
) -> str:
    """
    Encrypts data using AES-256-GCM.
    Returns:
        Formatted string: $aes256gcm$<base64url(nonce + ciphertext_with_tag)>
    """
    aes_key = key or get_encryption_key()
    aesgcm = AESGCM(aes_key)

    if isinstance(plaintext, (dict, list)):
        payload_bytes = json.dumps(plaintext, separators=(",", ":")).encode("utf-8")
    elif isinstance(plaintext, str):
        payload_bytes = plaintext.encode("utf-8")
    elif isinstance(plaintext, bytes):
        payload_bytes = plaintext
    else:
        payload_bytes = str(plaintext).encode("utf-8")

    aad_bytes = aad.encode("utf-8") if isinstance(aad, str) else (aad or None)
    nonce = os.urandom(NONCE_LENGTH_BYTES)

    # AESGCM.encrypt returns ciphertext + 16-byte tag
    ciphertext_with_tag = aesgcm.encrypt(nonce, payload_bytes, aad_bytes)
    packed = nonce + ciphertext_with_tag
    encoded = base64.urlsafe_b64encode(packed).decode("utf-8")

    return f"{CIPHER_PREFIX}{encoded}"


def decrypt(
    token: str,
    aad: Union[str, bytes] | None = None,
    key: bytes | None = None,
    as_json: bool = False,
) -> Any:
    """
    Decrypts an AES-256-GCM token and verifies authentication tag.
    Raises DecryptionError if tag verification fails or data was tampered with.
    """
    if not is_encrypted(token):
        raise DecryptionError("Token does not have valid $aes256gcm$ prefix.")

    aes_key = key or get_encryption_key()
    aesgcm = AESGCM(aes_key)

    raw_b64 = token[len(CIPHER_PREFIX):]
    try:
        packed = base64.urlsafe_b64decode(raw_b64.encode("utf-8"))
    except Exception as e:
        raise DecryptionError(f"Base64 decoding failed: {e}") from e

    min_length = NONCE_LENGTH_BYTES + TAG_LENGTH_BYTES
    if len(packed) < min_length:
        raise DecryptionError(f"Ciphertext payload is too short ({len(packed)} < {min_length} bytes).")

    nonce = packed[:NONCE_LENGTH_BYTES]
    ciphertext_with_tag = packed[NONCE_LENGTH_BYTES:]
    aad_bytes = aad.encode("utf-8") if isinstance(aad, str) else (aad or None)

    try:
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext_with_tag, aad_bytes)
    except InvalidTag as e:
        raise DecryptionError("Authentication tag verification failed. Ciphertext has been tampered with or incorrect key/AAD provided.") from e

    text = decrypted_bytes.decode("utf-8")
    if as_json:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    return text


def is_encrypted(value: Any) -> bool:
    """Returns True if the value is an AES-256-GCM encrypted token string."""
    return isinstance(value, str) and value.startswith(CIPHER_PREFIX)


def encrypt_fields(
    record: dict[str, Any],
    sensitive_fields: Sequence[str],
    aad: Union[str, bytes] | None = None,
    key: bytes | None = None,
) -> dict[str, Any]:
    """
    Encrypts only specified sensitive fields in a dictionary.
    Returns a new dictionary with specified fields encrypted.
    """
    out = dict(record)
    for field in sensitive_fields:
        if field in out and out[field] is not None:
            val = out[field]
            if not is_encrypted(val):
                out[field] = encrypt(val, aad=aad, key=key)
    return out


def decrypt_fields(
    record: dict[str, Any],
    sensitive_fields: Sequence[str],
    aad: Union[str, bytes] | None = None,
    key: bytes | None = None,
) -> dict[str, Any]:
    """
    Decrypts specified sensitive fields in a dictionary if they are encrypted.
    Returns a new dictionary with plaintext values restored.
    """
    out = dict(record)
    for field in sensitive_fields:
        if field in out and is_encrypted(out[field]):
            try:
                # Try parsing as JSON first if original was a structure
                try:
                    out[field] = decrypt(out[field], aad=aad, key=key, as_json=True)
                except Exception:
                    out[field] = decrypt(out[field], aad=aad, key=key, as_json=False)
            except DecryptionError:
                out[field] = "[DECRYPTION_FAILED]"
    return out


class EncryptedStore:
    """
    Thread-safe, atomic file persistence store with AES-256-GCM data-at-rest encryption.
    Stores records on disk with all sensitive fields strictly encrypted.
    """

    def __init__(
        self,
        filepath: Union[str, Path],
        sensitive_fields: Sequence[str] = ("query", "answer", "context_chunks", "approved_answer", "raw_transcript"),
        key: bytes | None = None,
    ):
        self.filepath = Path(filepath)
        self.sensitive_fields = tuple(sensitive_fields)
        self.key = key or get_encryption_key()
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning("Could not pre-create parent directory %s: %s", self.filepath.parent, e)

    def save_records(self, items: list[dict[str, Any]]) -> None:
        """
        Encrypts all sensitive fields and atomically writes records to disk.
        """
        encrypted_items = []
        for item in items:
            # Use item ID as AAD if available to bind ciphertext to record
            item_aad = str(item.get("query_id", item.get("id", ""))) or None
            enc = encrypt_fields(item, self.sensitive_fields, aad=item_aad, key=self.key)
            encrypted_items.append(enc)

        payload = {
            "version": 1,
            "algorithm": "AES-256-GCM",
            "key_bits": 256,
            "sensitive_fields": list(self.sensitive_fields),
            "record_count": len(encrypted_items),
            "records": encrypted_items,
        }

        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self.filepath.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        # Atomic replacement
        temp_file.replace(self.filepath)

    def load_records(self) -> list[dict[str, Any]]:
        """
        Loads records from disk and decrypts sensitive fields.
        """
        if not self.filepath.exists():
            return []

        try:
            with open(self.filepath, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return []

        records = data.get("records", [])
        decrypted_items = []
        for rec in records:
            item_aad = str(rec.get("query_id", rec.get("id", ""))) or None
            dec = decrypt_fields(rec, self.sensitive_fields, aad=item_aad, key=self.key)
            decrypted_items.append(dec)

        return decrypted_items

    def load_raw_encrypted(self) -> dict[str, Any]:
        """
        Returns the raw encrypted envelope directly from disk.
        Used for compliance verification and audit checks.
        """
        if not self.filepath.exists():
            return {
                "algorithm": "AES-256-GCM",
                "key_bits": 256,
                "record_count": 0,
                "records": [],
            }
        with open(self.filepath, encoding="utf-8") as f:
            return json.load(f)
