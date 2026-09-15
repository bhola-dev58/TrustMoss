"""
Unit and Integration Tests for GDPR Compliance & Data Lifecycle Retention Engine (Task 4.3)
"""

import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.main import app as gateway_app
from apps.api.retention import (
    DataCategory,
    RetentionManager,
    retention_manager,
)
from apps.api import voice_gateway
from services.evaluation_service import app as eval_app, _hitl_queue, _encrypted_store


class TestRetentionManagerCore(unittest.TestCase):
    def setUp(self):
        # Create an isolated retention manager for testing
        self.mgr = RetentionManager(
            transcript_ttl=10,  # 10s
            audit_ttl=20,       # 20s
            hitl_ttl=30,        # 30s
        )

    def test_register_and_ttl_expiration(self):
        now = datetime.now(timezone.utc)
        # Register an already-expired record (created 60s ago with 10s TTL)
        past_time = now - timedelta(seconds=60)
        rec_expired = self.mgr.register_record(
            record_id="rec-old-01",
            subject_id="user-alice",
            category=DataCategory.TRANSCRIPT,
            data={"text": "Old voice transcript"},
            custom_ttl_seconds=10,
            created_at=past_time,
        )
        self.assertTrue(rec_expired.is_expired)

        # Register a fresh record
        rec_fresh = self.mgr.register_record(
            record_id="rec-fresh-01",
            subject_id="user-alice",
            category=DataCategory.TRANSCRIPT,
            data={"text": "Fresh voice transcript"},
            custom_ttl_seconds=3600,
        )
        self.assertFalse(rec_fresh.is_expired)

        # Execute purge
        purge_report = self.mgr.purge_expired()
        self.assertEqual(purge_report["purged_count"], 1)
        self.assertEqual(purge_report["active_records_remaining"], 1)

        # Verify old record is gone and fresh remains
        self.assertNotIn("rec-old-01", self.mgr._records)
        self.assertIn("rec-fresh-01", self.mgr._records)

    def test_gdpr_article_17_right_to_erasure(self):
        # Register records for two different users
        self.mgr.register_record("r1", "user-alice", DataCategory.TRANSCRIPT, {"text": "alice audio"})
        self.mgr.register_record("r2", "user-alice", DataCategory.AUDIT_LOG, {"query": "alice query"})
        self.mgr.register_record("r3", "user-bob", DataCategory.TRANSCRIPT, {"text": "bob audio"})

        # Erase user-alice
        report = self.mgr.execute_erasure(subject_id="user-alice", requested_by="compliance_officer")
        self.assertEqual(report["status"], "success")
        self.assertEqual(report["records_erased"], 2)
        self.assertEqual(report["breakdown"][DataCategory.TRANSCRIPT], 1)
        self.assertEqual(report["breakdown"][DataCategory.AUDIT_LOG], 1)

        # Verify alice is completely gone, but bob remains
        self.assertNotIn("r1", self.mgr._records)
        self.assertNotIn("r2", self.mgr._records)
        self.assertIn("r3", self.mgr._records)

    def test_gdpr_article_15_data_export(self):
        self.mgr.register_record("r-exp-1", "user-charlie", DataCategory.TRANSCRIPT, {"text": "charlie turn"})
        self.mgr.register_record("r-exp-2", "user-charlie", DataCategory.AUDIT_LOG, {"query": "charlie search"})

        export = self.mgr.export_subject_data("user-charlie")
        self.assertEqual(export["subject_id"], "user-charlie")
        self.assertEqual(export["total_records"], 2)
        self.assertIn("Article 15 (Right of Access)", export["gdpr_articles"][0])

    def test_telemetry(self):
        self.mgr.register_record("t1", "user-1", DataCategory.TRANSCRIPT, {"t": 1})
        telemetry = self.mgr.get_telemetry()
        self.assertEqual(telemetry["active_records"], 1)
        self.assertIn("GDPR Art. 17", telemetry["compliance_standards"])


class TestVoiceGatewayRetentionIntegration(unittest.TestCase):
    def test_voice_turn_registration_and_erasure(self):
        res = voice_gateway.process_voice_turn(
            room_name="gdpr-test-room",
            participant_identity="patient-jane-doe",
            transcript="Check on prescription dosage for Jane Doe",
            top_k=2,
        )
        self.assertIn("verdict", res)

        # Check session recorded participant
        sess = voice_gateway.get_voice_session("gdpr-test-room")
        self.assertIsNotNone(sess)
        self.assertEqual(sess["participant_identity"], "patient-jane-doe")

        # Erase patient-jane-doe
        purged = voice_gateway.erase_voice_session_data("patient-jane-doe")
        self.assertGreaterEqual(purged, 1)
        self.assertIsNone(voice_gateway.get_voice_session("gdpr-test-room"))


class TestEvaluationServiceGDPR(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(eval_app)
        self.temp_dir = tempfile.mkdtemp()
        _encrypted_store.filepath = Path(self.temp_dir) / "eval_gdpr_hitl.enc.json"
        _hitl_queue.clear()

    def test_evaluation_retention_purge_and_erasure(self):
        # Insert test items directly
        now = datetime.now(timezone.utc)
        past_iso = (now - timedelta(days=95)).isoformat()
        future_iso = (now + timedelta(days=80)).isoformat()

        _hitl_queue.extend([
            {
                "query_id": "q-expired-1",
                "subject_id": "sub-expired",
                "query": "Old expired question",
                "answer": "Old answer",
                "expires_at": past_iso,
                "status": "pending_review",
            },
            {
                "query_id": "q-active-1",
                "subject_id": "sub-active",
                "query": "Active question",
                "answer": "Active answer",
                "expires_at": future_iso,
                "status": "pending_review",
            },
        ])
        _encrypted_store.save_records(_hitl_queue)

        # 1. Trigger purge
        purge_res = self.client.post("/retention/purge")
        self.assertEqual(purge_res.status_code, 200)
        self.assertEqual(purge_res.json()["purged_count"], 1)
        self.assertEqual(purge_res.json()["remaining_count"], 1)

        # 2. Trigger Article 17 erasure on active item
        erasure_res = self.client.post("/retention/erasure", json={"subject_id": "sub-active"})
        self.assertEqual(erasure_res.status_code, 200)
        self.assertEqual(erasure_res.json()["erased_count"], 1)
        self.assertEqual(erasure_res.json()["remaining_count"], 0)

        # 3. Status
        status_res = self.client.get("/retention/status")
        self.assertEqual(status_res.status_code, 200)
        self.assertEqual(status_res.json()["total_records"], 0)


class TestGatewayGDPRComplianceEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(gateway_app)

    def test_health_reports_gdpr_compliance(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("compliance", data)
        comp = data["compliance"]
        self.assertEqual(comp["gdpr_article_17_erasure"], "active")
        self.assertEqual(comp["gdpr_article_15_access"], "active")
        self.assertEqual(comp["ttl_retention_engine"], "active")
        self.assertIn("retention_days", comp)

    def test_gdpr_erasure_endpoint(self):
        # Register a record first in global retention_manager
        retention_manager.register_record(
            record_id="rec-test-erasure",
            subject_id="client-delete-me",
            category=DataCategory.AUDIT_LOG,
            data={"test": "data"},
        )

        res = self.client.post(
            "/api/compliance/gdpr/erasure",
            json={"subject_id": "client-delete-me", "requested_by": "compliance_test"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["subject_id"], "client-delete-me")
        self.assertIn("Article 17", data["gdpr_article"])
        self.assertGreaterEqual(data["summary"]["retention_records_erased"], 1)

    def test_gdpr_export_endpoint(self):
        retention_manager.register_record(
            record_id="rec-test-export",
            subject_id="client-export-me",
            category=DataCategory.TRANSCRIPT,
            data={"turn": "hello voice agent"},
        )

        res = self.client.get("/api/compliance/gdpr/export/client-export-me")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["subject_id"], "client-export-me")
        self.assertGreaterEqual(data["total_records"], 1)

    def test_retention_policy_endpoint(self):
        res = self.client.get("/api/compliance/retention/policy")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("active_records", data)
        self.assertIn("policies_days", data)
        self.assertIn("compliance_standards", data)

    def test_retention_purge_endpoint(self):
        res = self.client.post("/api/compliance/retention/purge")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("purge_report", data)
