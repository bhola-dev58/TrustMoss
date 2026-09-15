"""
TrustMoss GDPR Compliance & Data Lifecycle Retention Engine (Task 4.3)
----------------------------------------------------------------------
Implements automated TTL-based log retention, data lifecycle management,
and GDPR Article 15 & 17 compliance:

- GDPR Article 17 (Right to Erasure / "Right to be Forgotten"):
  Programmatic erasure of user-associated data across voice transcripts,
  HITL audit records, and PII logs.
- GDPR Article 15 & 20 (Right of Access & Data Portability):
  Structured machine-readable data export for data subjects.
- Automated TTL (Time-To-Live) Lifecycle Engine:
  Categorized retention limits with automated purge routines:
  - Voice Transcripts: default 7 days (604,800 sec)
  - PII / Audit Logs: default 30 days (2,592,000 sec)
  - HITL Review Records: default 90 days (7,776,000 sec)
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger("trustmoss.retention")


# ---------------------------------------------------------------------------
# Default Retention TTL Configuration (in seconds)
# ---------------------------------------------------------------------------
DEFAULT_TRANSCRIPT_TTL_SEC = int(os.getenv("RETENTION_TRANSCRIPTS_TTL_SEC", str(7 * 24 * 3600)))   # 7 days
DEFAULT_AUDIT_TTL_SEC = int(os.getenv("RETENTION_AUDIT_TTL_SEC", str(30 * 24 * 3600)))            # 30 days
DEFAULT_HITL_TTL_SEC = int(os.getenv("RETENTION_HITL_TTL_SEC", str(90 * 24 * 3600)))              # 90 days


class DataCategory:
    TRANSCRIPT = "transcript"
    AUDIT_LOG = "audit_log"
    HITL_RECORD = "hitl_record"
    PII_RECORD = "pii_record"


class RetentionRecord:
    """Represents a lifecycle-managed record subject to GDPR and TTL rules."""

    def __init__(
        self,
        record_id: str,
        subject_id: str,
        category: str,
        data: Dict[str, Any],
        ttl_seconds: int,
        created_at: Optional[datetime] = None,
    ):
        self.record_id = record_id
        self.subject_id = subject_id
        self.category = category
        self.data = data
        self.created_at = created_at or datetime.now(timezone.utc)
        self.expires_at = self.created_at + timedelta(seconds=ttl_seconds)

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "subject_id": self.subject_id,
            "category": self.category,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "is_expired": self.is_expired,
            "data": self.data,
        }


class RetentionManager:
    """
    Centralized GDPR Lifecycle and TTL Retention Manager.
    Governs data lifespans, automated purges, and Article 17 erasure requests.
    """

    def __init__(
        self,
        transcript_ttl: int = DEFAULT_TRANSCRIPT_TTL_SEC,
        audit_ttl: int = DEFAULT_AUDIT_TTL_SEC,
        hitl_ttl: int = DEFAULT_HITL_TTL_SEC,
    ):
        self.policy = {
            DataCategory.TRANSCRIPT: transcript_ttl,
            DataCategory.AUDIT_LOG: audit_ttl,
            DataCategory.HITL_RECORD: hitl_ttl,
            DataCategory.PII_RECORD: audit_ttl,
        }
        self._records: Dict[str, RetentionRecord] = {}
        self._erasure_audit_log: List[Dict[str, Any]] = []
        self._purge_history: List[Dict[str, Any]] = []

    def get_ttl_for_category(self, category: str) -> int:
        return self.policy.get(category, DEFAULT_AUDIT_TTL_SEC)

    def register_record(
        self,
        record_id: str,
        subject_id: str,
        category: str,
        data: Dict[str, Any],
        custom_ttl_seconds: Optional[int] = None,
        created_at: Optional[datetime] = None,
    ) -> RetentionRecord:
        """Enrolls a data record under lifecycle retention tracking."""
        ttl = custom_ttl_seconds or self.get_ttl_for_category(category)
        rec = RetentionRecord(
            record_id=record_id,
            subject_id=subject_id,
            category=category,
            data=data,
            ttl_seconds=ttl,
            created_at=created_at,
        )
        self._records[record_id] = rec
        return rec

    def purge_expired(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Scans all managed records and permanently purges any that have exceeded their TTL.
        Returns detailed telemetry report of the purge execution.
        """
        now = datetime.now(timezone.utc)
        to_delete = []

        for rec_id, rec in self._records.items():
            if category and rec.category != category:
                continue
            if now >= rec.expires_at:
                to_delete.append(rec_id)

        purged_count = len(to_delete)
        for rec_id in to_delete:
            del self._records[rec_id]

        report = {
            "timestamp": now.isoformat(),
            "purged_count": purged_count,
            "category_filter": category or "all",
            "active_records_remaining": len(self._records),
        }
        self._purge_history.append(report)
        logger.info("Data lifecycle purge completed: removed %d expired records.", purged_count)
        return report

    def execute_erasure(self, subject_id: str, requested_by: str = "subject") -> Dict[str, Any]:
        """
        Implements GDPR Article 17 ('Right to Erasure' / 'Right to be Forgotten').
        Permanently purges all data associated with the subject_id across all categories.
        """
        now = datetime.now(timezone.utc)
        to_delete = [
            rec_id for rec_id, rec in self._records.items()
            if rec.subject_id == subject_id
        ]

        deleted_by_category: Dict[str, int] = {}
        for rec_id in to_delete:
            cat = self._records[rec_id].category
            deleted_by_category[cat] = deleted_by_category.get(cat, 0) + 1
            del self._records[rec_id]

        audit_entry = {
            "action": "GDPR_ARTICLE_17_ERASURE",
            "subject_id": subject_id,
            "requested_by": requested_by,
            "executed_at": now.isoformat(),
            "total_records_erased": len(to_delete),
            "breakdown": deleted_by_category,
        }
        self._erasure_audit_log.append(audit_entry)
        logger.info("GDPR Article 17 erasure executed for subject '%s': erased %d records.", subject_id, len(to_delete))

        return {
            "status": "success",
            "subject_id": subject_id,
            "message": f"All data for subject '{subject_id}' has been permanently purged.",
            "records_erased": len(to_delete),
            "breakdown": deleted_by_category,
            "timestamp": now.isoformat(),
        }

    def export_subject_data(self, subject_id: str) -> Dict[str, Any]:
        """
        Implements GDPR Article 15 ('Right of Access') & Article 20 ('Data Portability').
        Returns all active records associated with the subject in portable JSON format.
        """
        matched = [
            rec.to_dict() for rec in self._records.values()
            if rec.subject_id == subject_id and not rec.is_expired
        ]

        return {
            "subject_id": subject_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_records": len(matched),
            "records": matched,
            "gdpr_articles": ["Article 15 (Right of Access)", "Article 20 (Data Portability)"],
        }

    def get_telemetry(self) -> Dict[str, Any]:
        """Returns comprehensive GDPR compliance and retention telemetry."""
        now = datetime.now(timezone.utc)
        active_count = 0
        expired_pending_purge = 0
        categories_count: Dict[str, int] = {}

        for rec in self._records.values():
            if now >= rec.expires_at:
                expired_pending_purge += 1
            else:
                active_count += 1
                categories_count[rec.category] = categories_count.get(rec.category, 0) + 1

        return {
            "active_records": active_count,
            "expired_pending_purge": expired_pending_purge,
            "categories": categories_count,
            "policies_days": {
                "transcripts": self.policy[DataCategory.TRANSCRIPT] // 86400,
                "audit_logs": self.policy[DataCategory.AUDIT_LOG] // 86400,
                "hitl_records": self.policy[DataCategory.HITL_RECORD] // 86400,
            },
            "policies_seconds": self.policy,
            "total_erasures_executed": len(self._erasure_audit_log),
            "total_purge_cycles": len(self._purge_history),
            "compliance_standards": ["GDPR Art. 15", "GDPR Art. 17", "NIST Privacy Framework"],
        }


# Global retention manager singleton for the API gateway
retention_manager = RetentionManager()
