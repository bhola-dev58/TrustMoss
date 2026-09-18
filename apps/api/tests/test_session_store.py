"""
test_session_store.py — Unit tests for Redis Session Cache & Circuit Breaker (Phase 9).

Tests cover:
  - In-memory fallback for session event history
  - History trimming (SESSION_MAX_HISTORY limit)
  - Circuit breaker failure recording & threshold trip
  - Circuit breaker reset
  - Circuit breaker state inspection
  - HITL priority queue enqueue and dequeue
  - Mocked Redis operations for pipeline push & history retrieval
"""

import json
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure apps/api and root are on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import database
import session_store


class TestSessionStoreInMemory(unittest.IsolatedAsyncioTestCase):
    """Tests session store fallback behavior when Redis is offline."""

    async def asyncSetUp(self):
        database._redis_client = None
        session_store._memory_sessions.clear()
        session_store._memory_circuit.clear()
        session_store._memory_hitl.clear()

    async def test_session_event_push_and_get(self):
        session_id = "sess-inmem-01"
        event1 = {"query": "test 1", "answer": "ans 1", "trust": {"verdict": "PASS"}}
        event2 = {"query": "test 2", "answer": "ans 2", "trust": {"verdict": "WARN"}}

        await session_store.push_session_event(session_id, event1)
        await session_store.push_session_event(session_id, event2)

        history = await session_store.get_session_history(session_id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["query"], "test 1")
        self.assertEqual(history[1]["query"], "test 2")

    async def test_session_history_trimming(self):
        session_id = "sess-trim"
        # Push 60 events with MAX_HISTORY=50
        for i in range(60):
            await session_store.push_session_event(session_id, {"idx": i})

        history = await session_store.get_session_history(session_id)
        self.assertEqual(len(history), 50)
        self.assertEqual(history[0]["idx"], 10)  # first 10 dropped
        self.assertEqual(history[-1]["idx"], 59)

    async def test_clear_session(self):
        session_id = "sess-clear"
        await session_store.push_session_event(session_id, {"q": "hello"})
        await session_store.clear_session(session_id)
        history = await session_store.get_session_history(session_id)
        self.assertEqual(history, [])

    async def test_circuit_breaker_trips_at_threshold(self):
        agent_id = "agent-flaky"
        self.assertFalse(await session_store.is_circuit_open(agent_id))

        # Record failures up to threshold (default: 3)
        res1 = await session_store.record_trust_failure(agent_id)
        self.assertEqual(res1["count"], 1)
        self.assertFalse(res1["tripped"])
        self.assertFalse(await session_store.is_circuit_open(agent_id))

        res2 = await session_store.record_trust_failure(agent_id)
        self.assertEqual(res2["count"], 2)
        self.assertFalse(res2["tripped"])
        self.assertFalse(await session_store.is_circuit_open(agent_id))

        res3 = await session_store.record_trust_failure(agent_id)
        self.assertEqual(res3["count"], 3)
        self.assertTrue(res3["tripped"])
        self.assertTrue(await session_store.is_circuit_open(agent_id))

    async def test_circuit_breaker_manual_reset(self):
        agent_id = "agent-reset"
        # Trip the breaker
        for _ in range(3):
            await session_store.record_trust_failure(agent_id)
        self.assertTrue(await session_store.is_circuit_open(agent_id))

        # Reset
        await session_store.reset_circuit(agent_id)
        self.assertFalse(await session_store.is_circuit_open(agent_id))
        state = await session_store.get_circuit_state(agent_id)
        self.assertEqual(state["count"], 0)
        self.assertFalse(state["tripped"])

    async def test_hitl_queue_priority_order(self):
        # Enqueue 3 queries with different priorities
        await session_store.enqueue_hitl("q_low", priority_score=0.2, metadata={"urgency": "low"})
        await session_store.enqueue_hitl("q_urgent", priority_score=0.9, metadata={"urgency": "urgent"})
        await session_store.enqueue_hitl("q_med", priority_score=0.5, metadata={"urgency": "med"})

        items = await session_store.dequeue_hitl(count=3)
        self.assertEqual(len(items), 3)
        # Highest priority score first
        self.assertEqual(items[0]["query_id"], "q_urgent")
        self.assertEqual(items[1]["query_id"], "q_med")
        self.assertEqual(items[2]["query_id"], "q_low")


class TestSessionStoreMockedRedis(unittest.IsolatedAsyncioTestCase):
    """Tests session store interaction with an active Redis client."""

    async def test_push_session_event_with_redis(self):
        mock_pipe = AsyncMock()
        mock_redis = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe

        with patch("database.get_redis", return_value=mock_redis):
            await session_store.push_session_event("sess-r1", {"query": "mock test"})
            mock_pipe.rpush.assert_called_once()
            mock_pipe.ltrim.assert_called_once()
            mock_pipe.expire.assert_called_once()
            mock_pipe.execute.assert_called_once()

    async def test_get_session_history_with_redis(self):
        raw_events = [
            json.dumps({"query": "q1", "answer": "a1"}),
            json.dumps({"query": "q2", "answer": "a2"}),
        ]
        mock_redis = AsyncMock()
        mock_redis.lrange.return_value = raw_events

        with patch("database.get_redis", return_value=mock_redis):
            history = await session_store.get_session_history("sess-r2")
            self.assertEqual(len(history), 2)
            self.assertEqual(history[0]["query"], "q1")
            self.assertEqual(history[1]["query"], "q2")


if __name__ == "__main__":
    unittest.main()
