"""
session_store.py — TrustMoss Redis Session Cache & Circuit Breaker State
=========================================================================
Provides:
  1. Session History Cache — stores per-session query/response history in Redis
     with automatic TTL expiry (matching GDPR retention policy).
  2. Circuit Breaker State — tracks consecutive failure counts per agent/session,
     enabling the circuit breaker pattern to trip and recover automatically.
  3. Graceful in-memory fallback when Redis is unavailable.

Redis Key Schema:
  session:{session_id}:history    → LIST of JSON-encoded QueryResponse dicts (TTL: 2h)
  session:{session_id}:trust      → HASH of latest trust score per session (TTL: 2h)
  circuit_breaker:{agent_id}      → HASH with {count, tripped, last_fail_at} (TTL: 5min window)
  hitl_queue:pending              → SORTED SET keyed by priority score (no TTL)
"""

from __future__ import annotations

from datetime import UTC, datetime
import json
import logging
import os
from typing import Any

logger = logging.getLogger("trustmoss.session_store")

# ─────────────────────────────────────────────────────────────────────────────
# In-memory fallback store (used when Redis is unavailable)
# ─────────────────────────────────────────────────────────────────────────────
_memory_sessions: dict[str, list[dict]] = {}
_memory_circuit: dict[str, dict] = {}
_memory_hitl: list[dict[str, Any]] = []

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "7200"))           # 2 hours
SESSION_MAX_HISTORY = int(os.getenv("SESSION_MAX_HISTORY", "50"))             # max 50 turns
CIRCUIT_BREAKER_WINDOW = int(os.getenv("CIRCUIT_BREAKER_WINDOW_SEC", "300")) # 5-minute window
CIRCUIT_BREAKER_THRESHOLD = int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "3")) # 3 failures → trip


# ─────────────────────────────────────────────────────────────────────────────
# Session History
# ─────────────────────────────────────────────────────────────────────────────

async def push_session_event(session_id: str, event: dict[str, Any]) -> None:
    """
    Append a query/response event to the session's history.
    Trims to SESSION_MAX_HISTORY to prevent unbounded growth.
    """
    from database import get_redis  # late import avoids circular deps
    redis = get_redis()

    key = f"session:{session_id}:history"
    payload = json.dumps(event, default=str)

    if redis is not None:
        try:
            pipe = redis.pipeline()
            await pipe.rpush(key, payload)
            await pipe.ltrim(key, -SESSION_MAX_HISTORY, -1)   # keep last N entries
            await pipe.expire(key, SESSION_TTL_SECONDS)
            await pipe.execute()
            return
        except Exception as exc:
            logger.warning("Redis push_session_event failed (%s) — using in-memory fallback.", exc)

    # In-memory fallback
    hist = _memory_sessions.setdefault(session_id, [])
    hist.append(event)
    if len(hist) > SESSION_MAX_HISTORY:
        _memory_sessions[session_id] = hist[-SESSION_MAX_HISTORY:]


async def get_session_history(session_id: str) -> list[dict[str, Any]]:
    """
    Retrieve the full session history as a list of event dicts.
    Returns an empty list if session not found.
    """
    from database import get_redis
    redis = get_redis()

    key = f"session:{session_id}:history"

    if redis is not None:
        try:
            raw_items = await redis.lrange(key, 0, -1)
            return [json.loads(item) for item in raw_items]
        except Exception as exc:
            logger.warning("Redis get_session_history failed (%s) — using in-memory fallback.", exc)

    return list(_memory_sessions.get(session_id, []))


async def set_session_trust(session_id: str, verdict: str, score: float) -> None:
    """Cache the latest trust verdict for a session (used by the dashboard)."""
    from database import get_redis
    redis = get_redis()

    key = f"session:{session_id}:trust"
    data = {"verdict": verdict, "score": str(score), "updated_at": datetime.now(UTC).isoformat()}

    if redis is not None:
        try:
            await redis.hset(key, mapping=data)
            await redis.expire(key, SESSION_TTL_SECONDS)
            return
        except Exception as exc:
            logger.warning("Redis set_session_trust failed (%s) — in-memory fallback.", exc)


async def clear_session(session_id: str) -> None:
    """
    Clear all session data (GDPR Article 17 — Right to Erasure).
    """
    from database import get_redis
    redis = get_redis()

    keys = [
        f"session:{session_id}:history",
        f"session:{session_id}:trust",
    ]

    if redis is not None:
        try:
            await redis.delete(*keys)
        except Exception as exc:
            logger.warning("Redis clear_session failed (%s).", exc)

    _memory_sessions.pop(session_id, None)


# ─────────────────────────────────────────────────────────────────────────────
# Circuit Breaker State Machine
# ─────────────────────────────────────────────────────────────────────────────

async def record_trust_failure(agent_id: str) -> dict[str, Any]:
    """
    Record a trust failure for an agent. Increments failure count.
    Returns the current circuit breaker state after recording.

    Circuit trips when failure count reaches CIRCUIT_BREAKER_THRESHOLD.
    State resets automatically after CIRCUIT_BREAKER_WINDOW seconds.
    """
    from database import get_redis
    redis = get_redis()

    key = f"circuit_breaker:{agent_id}"

    if redis is not None:
        try:
            pipe = redis.pipeline()
            await pipe.hincrby(key, "count", 1)
            await pipe.hset(key, "last_fail_at", datetime.now(UTC).isoformat())
            await pipe.expire(key, CIRCUIT_BREAKER_WINDOW)
            results = await pipe.execute()
            count = results[0]

            tripped = count >= CIRCUIT_BREAKER_THRESHOLD
            if tripped:
                await redis.hset(key, "tripped", "1")
                logger.warning(
                    "Circuit breaker TRIPPED for agent_id=%s after %d failures in %ds window.",
                    agent_id, count, CIRCUIT_BREAKER_WINDOW
                )
            return {"agent_id": agent_id, "count": count, "tripped": tripped, "provider": "redis"}

        except Exception as exc:
            logger.warning("Redis circuit_breaker record failed (%s) — in-memory fallback.", exc)

    # In-memory fallback
    state = _memory_circuit.setdefault(agent_id, {"count": 0, "tripped": False})
    state["count"] += 1
    state["last_fail_at"] = datetime.now(UTC).isoformat()
    state["tripped"] = state["count"] >= CIRCUIT_BREAKER_THRESHOLD
    if state["tripped"]:
        logger.warning("Circuit breaker TRIPPED (in-memory) for agent_id=%s.", agent_id)
    return {"agent_id": agent_id, "count": state["count"], "tripped": state["tripped"], "provider": "memory"}


async def is_circuit_open(agent_id: str) -> bool:
    """
    Check if the circuit breaker is open (tripped) for an agent.
    Returns True if the circuit is open (agent requests should be blocked/degraded).
    """
    from database import get_redis
    redis = get_redis()

    key = f"circuit_breaker:{agent_id}"

    if redis is not None:
        try:
            tripped = await redis.hget(key, "tripped")
            return tripped == "1"
        except Exception as exc:
            logger.warning("Redis is_circuit_open failed (%s) — in-memory fallback.", exc)

    return _memory_circuit.get(agent_id, {}).get("tripped", False)


async def reset_circuit(agent_id: str) -> None:
    """
    Manually reset the circuit breaker for an agent (called by HITL reviewer approval).
    """
    from database import get_redis
    redis = get_redis()

    key = f"circuit_breaker:{agent_id}"

    if redis is not None:
        try:
            await redis.delete(key)
            logger.info("Circuit breaker RESET for agent_id=%s.", agent_id)
            return
        except Exception as exc:
            logger.warning("Redis reset_circuit failed (%s) — in-memory fallback.", exc)

    _memory_circuit.pop(agent_id, None)
    logger.info("Circuit breaker RESET (in-memory) for agent_id=%s.", agent_id)


async def get_circuit_state(agent_id: str) -> dict[str, Any]:
    """Return the full circuit breaker state for an agent (for observability)."""
    from database import get_redis
    redis = get_redis()

    key = f"circuit_breaker:{agent_id}"

    if redis is not None:
        try:
            state = await redis.hgetall(key)
            if state:
                return {
                    "agent_id": agent_id,
                    "count": int(state.get("count", 0)),
                    "tripped": state.get("tripped") == "1",
                    "last_fail_at": state.get("last_fail_at"),
                    "threshold": CIRCUIT_BREAKER_THRESHOLD,
                    "window_seconds": CIRCUIT_BREAKER_WINDOW,
                    "provider": "redis",
                }
        except Exception as exc:
            logger.warning("Redis get_circuit_state failed (%s) — in-memory fallback.", exc)

    mem = _memory_circuit.get(agent_id, {})
    return {
        "agent_id": agent_id,
        "count": mem.get("count", 0),
        "tripped": mem.get("tripped", False),
        "last_fail_at": mem.get("last_fail_at"),
        "threshold": CIRCUIT_BREAKER_THRESHOLD,
        "window_seconds": CIRCUIT_BREAKER_WINDOW,
        "provider": "memory",
    }


# ─────────────────────────────────────────────────────────────────────────────
# HITL Queue
# ─────────────────────────────────────────────────────────────────────────────

async def enqueue_hitl(query_id: str, priority_score: float, metadata: dict[str, Any]) -> None:
    """
    Add a query_id to the HITL pending review queue (Redis sorted set).
    priority_score: higher = reviewed first. Derived from hitl_priority:
      URGENT=100, HIGH=75, MEDIUM=50, LOW=25
    """
    from database import get_redis
    redis = get_redis()

    if redis is not None:
        try:
            pipe = redis.pipeline()
            await pipe.zadd("hitl_queue:pending", {query_id: priority_score})
            await pipe.hset(f"hitl_meta:{query_id}", mapping={
                k: json.dumps(v, default=str) if isinstance(v, (dict, list)) else str(v)
                for k, v in metadata.items()
            })
            await pipe.execute()
            logger.info("HITL enqueued query_id=%s priority=%.0f", query_id, priority_score)
            return
        except Exception as exc:
            logger.warning("Redis enqueue_hitl failed (%s) — using in-memory fallback.", exc)

    # In-memory fallback
    _memory_hitl.append({
        "query_id": query_id,
        "priority_score": priority_score,
        **metadata,
    })
    # Keep sorted by priority_score descending
    _memory_hitl.sort(key=lambda x: x.get("priority_score", 0.0), reverse=True)
    logger.info("HITL enqueued (in-memory) query_id=%s priority=%.0f", query_id, priority_score)


async def dequeue_hitl(count: int = 10) -> list[dict[str, Any]]:
    """
    Dequeue up to `count` highest-priority HITL items for the reviewer dashboard.
    Returns list of dicts with query_id and metadata.
    """
    from database import get_redis
    redis = get_redis()

    if redis is not None:
        try:
            items = await redis.zrevrangebyscore(
                "hitl_queue:pending", "+inf", "-inf",
                start=0, num=count, withscores=True
            )
            results = []
            for query_id, score in items:
                raw_meta = await redis.hgetall(f"hitl_meta:{query_id}")
                results.append({
                    "query_id": query_id,
                    "priority_score": score,
                    **{k: json.loads(v) if v.startswith(("{", "[")) else v
                       for k, v in raw_meta.items()},
                })
            return results
        except Exception as exc:
            logger.warning("Redis dequeue_hitl failed (%s) — using in-memory fallback.", exc)

    # In-memory fallback: return top `count` items
    return list(_memory_hitl[:count])

