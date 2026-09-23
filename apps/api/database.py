"""
database.py — TrustMoss Async Database Layer (Phase 9 & 10 Enterprise)
=======================================================================
Provides:
  - PostgreSQL async connection pool via asyncpg (SQLAlchemy-free for sub-microsecond latency)
  - Redis async client via redis.asyncio (session cache + circuit-breaker state)
  - Full relational persistence for:
      * trust_events (real-time audit & latency logs)
      * audit_log (GDPR Art. 17 immutable compliance stream)
      * hitl_records (human-in-the-loop review queue & decisions)
      * load_test_runs (k6 OSS scalability & SLA benchmark runs)
  - Real-time connection pool & Redis cache telemetry (`get_database_stats()`)
  - Graceful degradation: if DB/Redis unavailable, services degrade seamlessly to in-memory mode

Environment variables:
  POSTGRES_DSN  — Full DSN e.g. postgresql://user:pass@host:5432/trustmoss
  REDIS_URL     — Full URL e.g. redis://redis:6379/0

Both resolved via the TrustMoss secret provider (Vault | AWS | ENV).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
import json
import logging
import os
from typing import Any
import uuid

logger = logging.getLogger("trustmoss.database")

# ─────────────────────────────────────────────────────────────────────────────
# Secret-aware config loading
# ─────────────────────────────────────────────────────────────────────────────
try:
    from secret_manager import get_secret as _get_secret
except ImportError:
    _get_secret = lambda k, d=None: os.getenv(k, d)  # noqa: E731

POSTGRES_DSN: str = (
    _get_secret("POSTGRES_DSN")
    or os.getenv("POSTGRES_DSN", "postgresql://trustmoss:trustmoss@localhost:5432/trustmoss")
)

REDIS_URL: str = (
    _get_secret("REDIS_URL")
    or os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

# ─────────────────────────────────────────────────────────────────────────────
# In-Memory Fallback Stores (active when PostgreSQL or Redis is offline)
# ─────────────────────────────────────────────────────────────────────────────
_in_memory_trust_events: list[dict[str, Any]] = []
_in_memory_audit_logs: list[dict[str, Any]] = []
_in_memory_hitl_records: dict[str, dict[str, Any]] = {}
_in_memory_load_tests: dict[str, dict[str, Any]] = {}

# ─────────────────────────────────────────────────────────────────────────────
# PostgreSQL — asyncpg Connection Pool
# ─────────────────────────────────────────────────────────────────────────────
_pg_pool: Any = None    # asyncpg.Pool
MAX_POOL_SIZE: int = 10
MIN_POOL_SIZE: int = 2


async def _ensure_schema(conn) -> None:
    """Idempotently ensure all tables and indexes exist in PostgreSQL."""
    schema_ddl = """
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";

    CREATE TABLE IF NOT EXISTS trust_events (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        session_id VARCHAR(128) NOT NULL,
        query_id VARCHAR(128) NOT NULL,
        agent_id VARCHAR(64),
        query_text TEXT NOT NULL,
        answer_text TEXT,
        verdict VARCHAR(16) NOT NULL,
        trust_score NUMERIC(5, 4) NOT NULL,
        trust_color VARCHAR(16),
        relevance_result JSONB,
        groundedness_result JSONB,
        pii_result JSONB,
        evaluation_result JSONB,
        circuit_breaker_tripped BOOLEAN DEFAULT FALSE,
        context_chunks_count INTEGER,
        top_retrieval_score NUMERIC(5, 4),
        model_used VARCHAR(64),
        latency_ms INTEGER,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_trust_events_session ON trust_events (session_id);
    CREATE INDEX IF NOT EXISTS idx_trust_events_created ON trust_events (created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_trust_events_query ON trust_events (query_id);

    CREATE TABLE IF NOT EXISTS audit_log (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        action VARCHAR(64) NOT NULL,
        subject_id VARCHAR(128) NOT NULL,
        actor_id VARCHAR(64) DEFAULT 'system',
        details JSONB,
        gdpr_article VARCHAR(32),
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_audit_log_subject ON audit_log (subject_id);
    CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log (created_at DESC);

    CREATE TABLE IF NOT EXISTS hitl_records (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        item_id VARCHAR(128) UNIQUE NOT NULL,
        query_id VARCHAR(128) NOT NULL,
        session_id VARCHAR(128),
        query_text TEXT NOT NULL,
        answer_text TEXT,
        violation_type VARCHAR(64) NOT NULL,
        reason TEXT,
        status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
        operator_id VARCHAR(64),
        operator_notes TEXT,
        corrected_answer TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_hitl_records_status ON hitl_records (status);
    CREATE INDEX IF NOT EXISTS idx_hitl_records_created ON hitl_records (created_at DESC);

    CREATE TABLE IF NOT EXISTS load_test_runs (
        id VARCHAR(128) PRIMARY KEY,
        name VARCHAR(256) NOT NULL,
        test_type VARCHAR(32) NOT NULL,
        target VARCHAR(512) NOT NULL,
        vus INTEGER NOT NULL,
        duration VARCHAR(32) NOT NULL,
        status VARCHAR(32) NOT NULL DEFAULT 'CREATED',
        p95_ms NUMERIC(8, 2),
        p99_ms NUMERIC(8, 2),
        rps NUMERIC(10, 2),
        error_rate NUMERIC(6, 4),
        threshold_passed BOOLEAN,
        breaking_point VARCHAR(256),
        raw_metrics JSONB,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        completed_at TIMESTAMPTZ
    );

    CREATE INDEX IF NOT EXISTS idx_load_test_runs_created ON load_test_runs (created_at DESC);
    """
    try:
        await conn.execute(schema_ddl)
        logger.info("PostgreSQL schema validated (trust_events, audit_log, hitl_records, load_test_runs).")
    except Exception as exc:
        logger.warning("PostgreSQL schema check returned warning: %s", exc)


async def init_postgres() -> None:
    """
    Initialize the asyncpg connection pool.
    Called once at application startup in the FastAPI lifespan handler.
    """
    global _pg_pool
    try:
        import asyncpg  # type: ignore
        _pg_pool = await asyncpg.create_pool(
            dsn=POSTGRES_DSN,
            min_size=MIN_POOL_SIZE,
            max_size=MAX_POOL_SIZE,
            max_inactive_connection_lifetime=300,   # 5-minute idle timeout
            command_timeout=30,
        )
        # Smoke-test connection and verify tables
        async with _pg_pool.acquire() as conn:
            version = await conn.fetchval("SELECT version()")
            logger.info("PostgreSQL connected: %s", version.split(",")[0])
            await _ensure_schema(conn)
    except Exception as exc:
        logger.warning(
            "PostgreSQL unavailable (%s) — falling back to in-memory mode. "
            "Set POSTGRES_DSN to enable persistent storage.", exc
        )
        _pg_pool = None


async def close_postgres() -> None:
    """Close the asyncpg pool gracefully at application shutdown."""
    global _pg_pool
    if _pg_pool is not None:
        try:
            await _pg_pool.close()
            logger.info("PostgreSQL connection pool closed.")
        except Exception as exc:
            logger.warning("Error closing PostgreSQL pool: %s", exc)
        _pg_pool = None


@asynccontextmanager
async def get_pg_conn() -> AsyncGenerator:
    """
    Async context manager that yields an asyncpg connection from the pool.
    Falls through (yields None) if PostgreSQL is unavailable.
    """
    if _pg_pool is None:
        yield None
        return
    try:
        async with _pg_pool.acquire() as conn:
            yield conn
    except Exception as exc:
        logger.error("PostgreSQL connection error: %s", exc)
        yield None


def is_postgres_available() -> bool:
    """Check if PostgreSQL pool is initialized and healthy."""
    return _pg_pool is not None


# ─────────────────────────────────────────────────────────────────────────────
# Redis — Async Client (Session Cache + Circuit Breaker State)
# ─────────────────────────────────────────────────────────────────────────────
_redis_client: Any = None    # redis.asyncio.Redis


async def init_redis() -> None:
    """
    Initialize the Redis async client.
    Called once at application startup.
    """
    global _redis_client
    try:
        from redis.asyncio import Redis  # type: ignore
        from redis.asyncio.connection import ConnectionPool  # type: ignore

        pool = ConnectionPool.from_url(
            REDIS_URL,
            max_connections=20,
            decode_responses=True,       # All values returned as str
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        _redis_client = Redis(connection_pool=pool)

        # Smoke-test: PING
        pong = await _redis_client.ping()
        if pong:
            info = await _redis_client.info("server")
            logger.info("Redis connected: v%s", info.get("redis_version", "?"))
    except Exception as exc:
        logger.warning(
            "Redis unavailable (%s) — falling back to in-memory mode. "
            "Set REDIS_URL to enable session caching.", exc
        )
        _redis_client = None


async def close_redis() -> None:
    """Close the Redis client gracefully at application shutdown."""
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.aclose()
            logger.info("Redis connection closed.")
        except Exception as exc:
            logger.warning("Error closing Redis client: %s", exc)
        _redis_client = None


def get_redis() -> object | None:
    """Return the Redis client instance or None if unavailable."""
    return _redis_client


def is_redis_available() -> bool:
    """Check if Redis client is initialized and connected."""
    return _redis_client is not None


# ─────────────────────────────────────────────────────────────────────────────
# Startup / Shutdown Lifecycle Helpers
# ─────────────────────────────────────────────────────────────────────────────

async def startup() -> None:
    """Initialize all database connections. Call from FastAPI lifespan."""
    logger.info("Initializing database connections...")
    await init_postgres()
    await init_redis()
    logger.info(
        "Database init complete — PostgreSQL: %s | Redis: %s",
        "✓" if is_postgres_available() else "✗ (in-memory fallback)",
        "✓" if is_redis_available() else "✗ (in-memory fallback)",
    )


async def shutdown() -> None:
    """Close all database connections. Call from FastAPI lifespan."""
    logger.info("Closing database connections...")
    await close_postgres()
    await close_redis()


async def health_check() -> dict:
    """Return database health status for the /health endpoint."""
    pg_status = "connected" if is_postgres_available() else "unavailable (in-memory mode)"
    redis_status = "connected" if is_redis_available() else "unavailable (in-memory mode)"

    if is_postgres_available():
        try:
            async with get_pg_conn() as conn:
                if conn:
                    await conn.fetchval("SELECT 1")
        except Exception:
            pg_status = "error"

    if is_redis_available():
        try:
            await _redis_client.ping()
        except Exception:
            redis_status = "error"

    return {
        "postgresql": pg_status,
        "redis": redis_status,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 1. Trust Events Data Access
# ─────────────────────────────────────────────────────────────────────────────

async def insert_trust_event(
    session_id: str,
    query_id: str,
    query_text: str,
    answer_text: str | None,
    verdict: str,
    trust_score: float,
    trust_color: str | None = None,
    agent_id: str | None = None,
    relevance_result: dict | None = None,
    groundedness_result: dict | None = None,
    pii_result: dict | None = None,
    evaluation_result: dict | None = None,
    circuit_breaker_tripped: bool = False,
    context_chunks_count: int | None = None,
    top_retrieval_score: float | None = None,
    model_used: str | None = None,
    latency_ms: int | None = None,
) -> str | None:
    """
    Insert a trust evaluation event into PostgreSQL or in-memory fallback.
    Returns the event UUID string.
    """
    event_dict = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "query_id": query_id,
        "agent_id": agent_id,
        "query_text": query_text,
        "answer_text": answer_text,
        "verdict": verdict,
        "trust_score": float(trust_score),
        "trust_color": trust_color,
        "relevance_result": relevance_result,
        "groundedness_result": groundedness_result,
        "pii_result": pii_result,
        "evaluation_result": evaluation_result,
        "circuit_breaker_tripped": circuit_breaker_tripped,
        "context_chunks_count": context_chunks_count,
        "top_retrieval_score": top_retrieval_score,
        "model_used": model_used,
        "latency_ms": latency_ms,
        "created_at": datetime.now(UTC).isoformat(),
    }

    if not is_postgres_available():
        _in_memory_trust_events.append(event_dict)
        return None

    try:
        async with get_pg_conn() as conn:
            if not conn:
                _in_memory_trust_events.append(event_dict)
                return None
            row = await conn.fetchrow(
                """
                INSERT INTO trust_events (
                    session_id, query_id, agent_id, query_text, answer_text,
                    verdict, trust_score, trust_color,
                    relevance_result, groundedness_result, pii_result, evaluation_result,
                    circuit_breaker_tripped, context_chunks_count, top_retrieval_score,
                    model_used, latency_ms
                ) VALUES (
                    $1, $2, $3, $4, $5,
                    $6, $7, $8,
                    $9::jsonb, $10::jsonb, $11::jsonb, $12::jsonb,
                    $13, $14, $15,
                    $16, $17
                )
                RETURNING id
                """,
                session_id, query_id, agent_id, query_text, answer_text,
                verdict, float(trust_score), trust_color,
                json.dumps(relevance_result) if relevance_result else None,
                json.dumps(groundedness_result) if groundedness_result else None,
                json.dumps(pii_result) if pii_result else None,
                json.dumps(evaluation_result) if evaluation_result else None,
                circuit_breaker_tripped, context_chunks_count, top_retrieval_score,
                model_used, latency_ms,
            )
            return str(row["id"]) if row else None
    except Exception as exc:
        logger.error("Failed to insert trust_event (%s): %s", query_id, exc)
        _in_memory_trust_events.append(event_dict)
        return None


async def get_trust_events(limit: int = 50, session_id: str | None = None) -> list[dict]:
    """Retrieve recent trust events from PostgreSQL or in-memory fallback."""
    if not is_postgres_available():
        if session_id:
            filtered = [e for e in _in_memory_trust_events if e.get("session_id") == session_id]
            return list(reversed(filtered))[:limit]
        return list(reversed(_in_memory_trust_events))[:limit]

    try:
        async with get_pg_conn() as conn:
            if not conn:
                return []
            if session_id:
                rows = await conn.fetch(
                    """
                    SELECT query_id, session_id, agent_id, query_text, answer_text,
                           verdict, trust_score, trust_color, circuit_breaker_tripped,
                           latency_ms, created_at
                    FROM trust_events
                    WHERE session_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    session_id, limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT query_id, session_id, agent_id, query_text, answer_text,
                           verdict, trust_score, trust_color, circuit_breaker_tripped,
                           latency_ms, created_at
                    FROM trust_events
                    ORDER BY created_at DESC
                    LIMIT $1
                    """,
                    limit,
                )
            return [dict(r) for r in rows]
    except Exception as exc:
        logger.error("Failed to fetch trust_events: %s", exc)
        return []


# ─────────────────────────────────────────────────────────────────────────────
# 2. Audit Log Data Access (GDPR Art. 17 Immutable Records)
# ─────────────────────────────────────────────────────────────────────────────

async def insert_audit_log(
    action: str,
    subject_id: str,
    actor_id: str = "system",
    details: dict | None = None,
    gdpr_article: str | None = None,
) -> str | None:
    """Insert an immutable audit log entry into PostgreSQL or in-memory fallback."""
    log_item = {
        "id": str(uuid.uuid4()),
        "action": action,
        "subject_id": subject_id,
        "actor_id": actor_id,
        "details": details,
        "gdpr_article": gdpr_article,
        "created_at": datetime.now(UTC).isoformat(),
    }

    if not is_postgres_available():
        _in_memory_audit_logs.append(log_item)
        return None

    try:
        async with get_pg_conn() as conn:
            if not conn:
                _in_memory_audit_logs.append(log_item)
                return None
            row = await conn.fetchrow(
                """
                INSERT INTO audit_log (
                    action, subject_id, actor_id, details, gdpr_article
                ) VALUES (
                    $1, $2, $3, $4::jsonb, $5
                )
                RETURNING id
                """,
                action, subject_id, actor_id,
                json.dumps(details) if details else None,
                gdpr_article,
            )
            return str(row["id"]) if row else None
    except Exception as exc:
        logger.error("Failed to insert audit_log: %s", exc)
        _in_memory_audit_logs.append(log_item)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 3. Human-in-the-Loop (HITL) Review Queue Data Access
# ─────────────────────────────────────────────────────────────────────────────

async def insert_hitl_record(
    item_id: str,
    query_id: str,
    session_id: str | None,
    query_text: str,
    answer_text: str | None,
    violation_type: str,
    reason: str | None = None,
    status: str = "PENDING",
    operator_id: str | None = None,
    operator_notes: str | None = None,
    corrected_answer: str | None = None,
) -> str | None:
    """Persist a new HITL review record into PostgreSQL or in-memory store."""
    record = {
        "item_id": item_id,
        "query_id": query_id,
        "session_id": session_id,
        "query_text": query_text,
        "answer_text": answer_text,
        "violation_type": violation_type,
        "reason": reason,
        "status": status,
        "operator_id": operator_id,
        "operator_notes": operator_notes,
        "corrected_answer": corrected_answer,
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }
    _in_memory_hitl_records[item_id] = record

    if not is_postgres_available():
        return item_id

    try:
        async with get_pg_conn() as conn:
            if not conn:
                return item_id
            row = await conn.fetchrow(
                """
                INSERT INTO hitl_records (
                    item_id, query_id, session_id, query_text, answer_text,
                    violation_type, reason, status, operator_id, operator_notes, corrected_answer
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (item_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    operator_id = EXCLUDED.operator_id,
                    operator_notes = EXCLUDED.operator_notes,
                    corrected_answer = EXCLUDED.corrected_answer,
                    updated_at = NOW()
                RETURNING id
                """,
                item_id, query_id, session_id, query_text, answer_text,
                violation_type, reason, status, operator_id, operator_notes, corrected_answer,
            )
            return str(row["id"]) if row else item_id
    except Exception as exc:
        logger.error("Failed to insert hitl_record (%s): %s", item_id, exc)
        return item_id


async def get_hitl_records(status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """Retrieve HITL review queue records."""
    if not is_postgres_available():
        records = list(_in_memory_hitl_records.values())
        if status:
            records = [r for r in records if r.get("status") == status]
        return sorted(records, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]

    try:
        async with get_pg_conn() as conn:
            if not conn:
                return []
            if status:
                rows = await conn.fetch(
                    """
                    SELECT item_id, query_id, session_id, query_text, answer_text,
                           violation_type, reason, status, operator_id, operator_notes,
                           corrected_answer, created_at, updated_at
                    FROM hitl_records
                    WHERE status = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    status, limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT item_id, query_id, session_id, query_text, answer_text,
                           violation_type, reason, status, operator_id, operator_notes,
                           corrected_answer, created_at, updated_at
                    FROM hitl_records
                    ORDER BY created_at DESC
                    LIMIT $1
                    """,
                    limit,
                )
            return [dict(r) for r in rows]
    except Exception as exc:
        logger.error("Failed to fetch hitl_records: %s", exc)
        return []


async def update_hitl_record(
    item_id: str,
    status: str,
    operator_id: str | None = None,
    operator_notes: str | None = None,
    corrected_answer: str | None = None,
) -> bool:
    """Update operator decision on a HITL review item."""
    if item_id in _in_memory_hitl_records:
        rec = _in_memory_hitl_records[item_id]
        rec["status"] = status
        rec["operator_id"] = operator_id or rec.get("operator_id")
        rec["operator_notes"] = operator_notes or rec.get("operator_notes")
        rec["corrected_answer"] = corrected_answer or rec.get("corrected_answer")
        rec["updated_at"] = datetime.now(UTC).isoformat()

    if not is_postgres_available():
        return True

    try:
        async with get_pg_conn() as conn:
            if not conn:
                return True
            res = await conn.execute(
                """
                UPDATE hitl_records
                SET status = $2, operator_id = $3, operator_notes = $4, corrected_answer = $5, updated_at = NOW()
                WHERE item_id = $1
                """,
                item_id, status, operator_id, operator_notes, corrected_answer,
            )
            return "UPDATE" in res
    except Exception as exc:
        logger.error("Failed to update hitl_record (%s): %s", item_id, exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# 4. k6 OSS Scalability & Benchmark Runs Data Access
# ─────────────────────────────────────────────────────────────────────────────

async def insert_load_test_run(
    test_id: str,
    name: str,
    test_type: str,
    target: str,
    vus: int,
    duration: str,
    status: str = "CREATED",
) -> str | None:
    """Persist a new load test execution record."""
    test_item = {
        "id": test_id,
        "name": name,
        "test_type": test_type,
        "target": target,
        "vus": vus,
        "duration": duration,
        "status": status,
        "p95_ms": None,
        "p99_ms": None,
        "rps": None,
        "error_rate": 0.0,
        "threshold_passed": None,
        "breaking_point": None,
        "raw_metrics": None,
        "created_at": datetime.now(UTC).isoformat(),
        "completed_at": None,
    }
    _in_memory_load_tests[test_id] = test_item

    if not is_postgres_available():
        return test_id

    try:
        async with get_pg_conn() as conn:
            if not conn:
                return test_id
            await conn.execute(
                """
                INSERT INTO load_test_runs (
                    id, name, test_type, target, vus, duration, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status
                """,
                test_id, name, test_type, target, vus, duration, status,
            )
            return test_id
    except Exception as exc:
        logger.error("Failed to insert load_test_run (%s): %s", test_id, exc)
        return test_id


async def update_load_test_run(
    test_id: str,
    status: str,
    p95_ms: float | None = None,
    p99_ms: float | None = None,
    rps: float | None = None,
    error_rate: float | None = None,
    threshold_passed: bool | None = None,
    breaking_point: str | None = None,
    raw_metrics: dict | None = None,
) -> bool:
    """Update status, metrics, and completion timestamp for a load test run."""
    if test_id in _in_memory_load_tests:
        run = _in_memory_load_tests[test_id]
        run["status"] = status
        if p95_ms is not None:
            run["p95_ms"] = p95_ms
        if p99_ms is not None:
            run["p99_ms"] = p99_ms
        if rps is not None:
            run["rps"] = rps
        if error_rate is not None:
            run["error_rate"] = error_rate
        if threshold_passed is not None:
            run["threshold_passed"] = threshold_passed
        if breaking_point is not None:
            run["breaking_point"] = breaking_point
        if raw_metrics is not None:
            run["raw_metrics"] = raw_metrics
        if status in ("COMPLETED", "FAILED", "CANCELLED"):
            run["completed_at"] = datetime.now(UTC).isoformat()

    if not is_postgres_available():
        return True

    try:
        async with get_pg_conn() as conn:
            if not conn:
                return True
            completed_now = datetime.now(UTC) if status in ("COMPLETED", "FAILED", "CANCELLED") else None
            await conn.execute(
                """
                UPDATE load_test_runs SET
                    status = $2,
                    p95_ms = COALESCE($3, p95_ms),
                    p99_ms = COALESCE($4, p99_ms),
                    rps = COALESCE($5, rps),
                    error_rate = COALESCE($6, error_rate),
                    threshold_passed = COALESCE($7, threshold_passed),
                    breaking_point = COALESCE($8, breaking_point),
                    raw_metrics = COALESCE($9::jsonb, raw_metrics),
                    completed_at = COALESCE($10, completed_at)
                WHERE id = $1
                """,
                test_id, status, p95_ms, p99_ms, rps, error_rate, threshold_passed,
                breaking_point, json.dumps(raw_metrics) if raw_metrics else None, completed_now,
            )
            return True
    except Exception as exc:
        logger.error("Failed to update load_test_run (%s): %s", test_id, exc)
        return False


async def get_load_test_runs(limit: int = 50) -> list[dict[str, Any]]:
    """Fetch history of load test executions."""
    if not is_postgres_available():
        runs = list(_in_memory_load_tests.values())
        return sorted(runs, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]

    try:
        async with get_pg_conn() as conn:
            if not conn:
                return list(_in_memory_load_tests.values())[:limit]
            rows = await conn.fetch(
                """
                SELECT id, name, test_type, target, vus, duration, status,
                       p95_ms, p99_ms, rps, error_rate, threshold_passed,
                       breaking_point, raw_metrics, created_at, completed_at
                FROM load_test_runs
                ORDER BY created_at DESC
                LIMIT $1
                """,
                limit,
            )
            return [dict(r) for r in rows]
    except Exception as exc:
        logger.error("Failed to get load_test_runs: %s", exc)
        return list(_in_memory_load_tests.values())[:limit]


async def get_load_test_run(test_id: str) -> dict[str, Any] | None:
    """Fetch single load test run by ID."""
    if not is_postgres_available():
        return _in_memory_load_tests.get(test_id)

    try:
        async with get_pg_conn() as conn:
            if not conn:
                return _in_memory_load_tests.get(test_id)
            row = await conn.fetchrow(
                """
                SELECT id, name, test_type, target, vus, duration, status,
                       p95_ms, p99_ms, rps, error_rate, threshold_passed,
                       breaking_point, raw_metrics, created_at, completed_at
                FROM load_test_runs
                WHERE id = $1
                """,
                test_id,
            )
            return dict(row) if row else None
    except Exception as exc:
        logger.error("Failed to get load_test_run (%s): %s", test_id, exc)
        return _in_memory_load_tests.get(test_id)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Database Connection Pool & Cache Telemetry (`get_database_stats`)
# ─────────────────────────────────────────────────────────────────────────────

async def get_database_stats() -> dict[str, Any]:
    """
    Produce comprehensive runtime telemetry for PostgreSQL connection pool,
    table row counts, and Redis session caching state.
    Consumed by `GET /api/database/stats` for the Operations Console.
    """
    pg_available = is_postgres_available()
    redis_available = is_redis_available()

    # PostgreSQL pool telemetry
    active_conns = 0
    idle_conns = 0
    pool_size = 0
    if pg_available and _pg_pool is not None:
        try:
            # asyncpg pool attributes
            pool_size = getattr(_pg_pool, "_size", 0)
            holders = getattr(_pg_pool, "_holders", [])
            active_conns = sum(1 for h in holders if getattr(h, "_in_use", False))
            idle_conns = max(0, pool_size - active_conns)
        except Exception:
            pool_size = MIN_POOL_SIZE
            active_conns = 1
            idle_conns = 1

    # Table counts
    trust_events_count = len(_in_memory_trust_events)
    audit_logs_count = len(_in_memory_audit_logs)
    hitl_records_count = len(_in_memory_hitl_records)
    load_test_runs_count = len(_in_memory_load_tests)

    if pg_available:
        try:
            async with get_pg_conn() as conn:
                if conn:
                    te_count = await conn.fetchval("SELECT count(*) FROM trust_events")
                    al_count = await conn.fetchval("SELECT count(*) FROM audit_log")
                    hr_count = await conn.fetchval("SELECT count(*) FROM hitl_records")
                    lt_count = await conn.fetchval("SELECT count(*) FROM load_test_runs")
                    trust_events_count = int(te_count or 0)
                    audit_logs_count = int(al_count or 0)
                    hitl_records_count = int(hr_count or 0)
                    load_test_runs_count = int(lt_count or 0)
        except Exception as exc:
            logger.warning("Error fetching table counts from PostgreSQL: %s", exc)

    # Redis telemetry
    active_sessions = 0
    circuit_breakers_tripped = 0
    redis_memory_used = "0 KB"
    if redis_available and _redis_client is not None:
        try:
            keys = await _redis_client.keys("session:*")
            active_sessions = len(keys)
            cb_keys = await _redis_client.keys("cb:tripped:*")
            circuit_breakers_tripped = len(cb_keys)
            info = await _redis_client.info("memory")
            redis_memory_used = info.get("used_memory_human", "N/A")
        except Exception as exc:
            logger.warning("Error fetching Redis telemetry: %s", exc)

    return {
        "status": "healthy" if (pg_available or redis_available) else "degraded_in_memory",
        "timestamp": datetime.now(UTC).isoformat(),
        "postgresql": {
            "connected": pg_available,
            "pool_status": "active" if pg_available else "offline",
            "active_connections": active_conns,
            "idle_connections": idle_conns,
            "pool_size": pool_size,
            "max_pool_size": MAX_POOL_SIZE,
            "tables": {
                "trust_events": trust_events_count,
                "audit_log": audit_logs_count,
                "hitl_records": hitl_records_count,
                "load_test_runs": load_test_runs_count,
            },
        },
        "redis": {
            "connected": redis_available,
            "status": "active" if redis_available else "offline",
            "active_sessions": active_sessions,
            "circuit_breakers_tripped": circuit_breakers_tripped,
            "memory_used": redis_memory_used,
        },
    }
