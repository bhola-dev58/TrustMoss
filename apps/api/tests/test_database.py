"""
test_database.py — Unit tests for TrustMoss Async Database Layer (Phase 9).

Tests cover:
  - Default / uninitialized state and graceful degradation
  - In-memory fallback behavior when PostgreSQL is offline
  - In-memory fallback behavior when Redis is offline
  - Health check endpoint payload structure
  - insert_trust_event() graceful degradation and mocked execution
  - get_trust_events() graceful degradation and query execution
  - insert_audit_log() graceful degradation
  - Startup & shutdown lifecycle routines
"""

import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure apps/api and root are on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import database


class TestDatabaseLayerGracefulDegradation(unittest.IsolatedAsyncioTestCase):
    """Verifies that the database layer degrades gracefully when DBs are offline."""

    async def asyncSetUp(self):
        database._pg_pool = None
        database._redis_client = None

    async def test_initial_availability_flags(self):
        self.assertFalse(database.is_postgres_available())
        self.assertFalse(database.is_redis_available())
        self.assertIsNone(database.get_redis())

    async def test_health_check_offline(self):
        status = await database.health_check()
        self.assertIn("postgresql", status)
        self.assertIn("redis", status)
        self.assertIn("unavailable", status["postgresql"])
        self.assertIn("unavailable", status["redis"])

    async def test_get_pg_conn_yields_none_when_uninitialized(self):
        async with database.get_pg_conn() as conn:
            self.assertIsNone(conn)

    async def test_insert_trust_event_offline(self):
        event_id = await database.insert_trust_event(
            session_id="test-sess",
            query_id="test-query",
            query_text="What is TrustMoss?",
            answer_text="TrustMoss is an enterprise reliability gateway.",
            verdict="PASS",
            trust_score=0.95,
            trust_color="green",
        )
        self.assertIsNone(event_id)

    async def test_get_trust_events_offline(self):
        events = await database.get_trust_events(limit=10)
        self.assertEqual(events, [])

    async def test_insert_audit_log_offline(self):
        audit_id = await database.insert_audit_log(
            action="TEST_ACTION",
            subject_id="subj-123",
            actor_id="tester",
            details={"key": "val"},
        )
        self.assertIsNone(audit_id)


class TestDatabaseLayerMockedExecution(unittest.IsolatedAsyncioTestCase):
    """Verifies queries execute properly when connection pool is active."""

    async def asyncSetUp(self):
        database._pg_pool = None
        database._redis_client = None

    async def asyncTearDown(self):
        database._pg_pool = None
        database._redis_client = None

    async def test_insert_trust_event_with_mock_pool(self):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {"id": "11111111-2222-3333-4444-555555555555"}

        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        database._pg_pool = mock_pool

        event_id = await database.insert_trust_event(
            session_id="sess-42",
            query_id="query-42",
            query_text="Explain RAG",
            answer_text="Retrieval Augmented Generation",
            verdict="PASS",
            trust_score=0.92,
            trust_color="green",
            agent_id="agent-01",
            circuit_breaker_tripped=False,
            latency_ms=85,
        )

        self.assertEqual(event_id, "11111111-2222-3333-4444-555555555555")
        mock_conn.fetchrow.assert_called_once()

    async def test_get_trust_events_with_mock_pool(self):
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {
                "query_id": "q1",
                "session_id": "s1",
                "agent_id": "a1",
                "query_text": "hi",
                "answer_text": "hello",
                "verdict": "PASS",
                "trust_score": 0.99,
                "trust_color": "green",
                "circuit_breaker_tripped": False,
                "latency_ms": 20,
                "created_at": "2026-09-17T10:00:00Z",
            }
        ]

        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        database._pg_pool = mock_pool

        events = await database.get_trust_events(limit=5, session_id="s1")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["query_id"], "q1")

    async def test_health_check_healthy(self):
        mock_conn = AsyncMock()
        mock_conn.fetchval.return_value = 1
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True

        database._pg_pool = mock_pool
        database._redis_client = mock_redis

        status = await database.health_check()
        self.assertEqual(status["postgresql"], "connected")
        self.assertEqual(status["redis"], "connected")

    async def test_shutdown_closes_connections(self):
        mock_pool = AsyncMock()
        mock_redis = AsyncMock()

        database._pg_pool = mock_pool
        database._redis_client = mock_redis

        await database.shutdown()

        mock_pool.close.assert_called_once()
        mock_redis.aclose.assert_called_once()
        self.assertIsNone(database._pg_pool)
        self.assertIsNone(database._redis_client)


    async def test_hitl_records_lifecycle_in_memory(self):
        # Insert HITL record
        res_id = await database.insert_hitl_record(
            item_id="hitl-test-01",
            query_id="q-test-01",
            session_id="s-test-01",
            query_text="Suspicious query",
            answer_text="Uncertain answer",
            violation_type="GROUNDEDNESS_FAILURE",
            reason="Score 0.42 below threshold",
            status="PENDING",
        )
        self.assertEqual(res_id, "hitl-test-01")

        # Fetch records
        records = await database.get_hitl_records(status="PENDING")
        self.assertTrue(any(r["item_id"] == "hitl-test-01" for r in records))

        # Update record
        updated = await database.update_hitl_record(
            item_id="hitl-test-01",
            status="RESOLVED",
            operator_id="operator-dev",
            corrected_answer="Verified accurate answer",
        )
        self.assertTrue(updated)

        # Check updated status
        resolved_records = await database.get_hitl_records(status="RESOLVED")
        self.assertTrue(any(r["item_id"] == "hitl-test-01" and r["status"] == "RESOLVED" for r in resolved_records))

    async def test_load_test_runs_lifecycle_in_memory(self):
        test_id = "k6-run-test-99"
        created_id = await database.insert_load_test_run(
            test_id=test_id,
            name="Stress Benchmark",
            test_type="stress",
            target="http://localhost:8000/health",
            vus=100,
            duration="30s",
        )
        self.assertEqual(created_id, test_id)

        # Update metrics
        success = await database.update_load_test_run(
            test_id=test_id,
            status="COMPLETED",
            p95_ms=31.5,
            p99_ms=44.2,
            rps=850.0,
            error_rate=0.0,
            threshold_passed=True,
            breaking_point="SLA Compliant (P95 < 45ms)",
        )
        self.assertTrue(success)

        # Fetch single test
        run = await database.get_load_test_run(test_id)
        self.assertIsNotNone(run)
        self.assertEqual(run["status"], "COMPLETED")
        self.assertEqual(run["p95_ms"], 31.5)
        self.assertTrue(run["threshold_passed"])

        # Fetch all tests
        all_runs = await database.get_load_test_runs()
        self.assertTrue(any(r["id"] == test_id for r in all_runs))

    async def test_get_database_stats_structure(self):
        stats = await database.get_database_stats()
        self.assertIn("status", stats)
        self.assertIn("timestamp", stats)
        self.assertIn("postgresql", stats)
        self.assertIn("redis", stats)
        self.assertIn("active_connections", stats["postgresql"])
        self.assertIn("tables", stats["postgresql"])
        self.assertIn("trust_events", stats["postgresql"]["tables"])
        self.assertIn("hitl_records", stats["postgresql"]["tables"])
        self.assertIn("load_test_runs", stats["postgresql"]["tables"])
        self.assertIn("active_sessions", stats["redis"])



class TestDatabaseEndpoints(unittest.TestCase):
    """Integration tests for database-backed REST API endpoints."""

    def setUp(self):
        from fastapi.testclient import TestClient
        import main
        self.client = TestClient(main.app)

    def test_database_stats_endpoint(self):
        resp = self.client.get("/api/database/stats")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("postgresql", data)
        self.assertIn("redis", data)
        self.assertIn("tables", data["postgresql"])
        self.assertIn("trust_events", data["postgresql"]["tables"])
        self.assertIn("hitl_records", data["postgresql"]["tables"])
        self.assertIn("load_test_runs", data["postgresql"]["tables"])

    def test_history_endpoint_global(self):
        resp = self.client.get("/history")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("count", data)
        self.assertIn("queries", data)
        self.assertIn("source", data)

    def test_hitl_records_endpoint(self):
        resp = self.client.get("/api/hitl/records")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("count", data)
        self.assertIn("items", data)


if __name__ == "__main__":
    unittest.main()


