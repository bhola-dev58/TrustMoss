"""
Re-export TrustMoss GDPR & Data Retention Engine for Microservices.
"""

from apps.api.retention import (
    DataCategory,
    DEFAULT_TRANSCRIPT_TTL_SEC,
    DEFAULT_AUDIT_TTL_SEC,
    DEFAULT_HITL_TTL_SEC,
    RetentionRecord,
    RetentionManager,
    retention_manager,
)

__all__ = [
    "DataCategory",
    "DEFAULT_TRANSCRIPT_TTL_SEC",
    "DEFAULT_AUDIT_TTL_SEC",
    "DEFAULT_HITL_TTL_SEC",
    "RetentionRecord",
    "RetentionManager",
    "retention_manager",
]
