"""
database.py — TrustMoss Async Database Layer (Phase 9)
=======================================================
Provides:
  - PostgreSQL async connection pool via asyncpg (SQLAlchemy-free for performance)
  - Redis async client via redis.asyncio (session cache + circuit-breaker state)
  - Graceful degradation: if DB/Redis unavailable, services degrade to in-memory mode

Environment variables:
  POSTGRES_DSN  — Full DSN e.g. postgresql://user:pass@host:5432/trustmoss
  REDIS_URL     — Full URL e.g. redis://redis:6379/0

Both resolved via the TrustMoss secret provider (Vault | AWS | ENV).
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

logger = logging.getLogger("trustmoss.database")

# ─────────────────────────────────────────────────────────────────────────────
# Secret-aware config loading
# ─────────────────────────────────────────────────────────────────────────────
try:
    from secrets import get_secret as _get_secret
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
# PostgreSQL — asyncpg Connection Pool
# ─────────────────────────────────────────────────────────────────────────────
_pg_pool: Optional[object] = None    # asyncpg.Pool


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
            min_size=2,
            max_size=10,
            max_inactive_connection_lifetime=300,   # 5-minute idle timeout
            command_timeout=30,
        )
        # Smoke-test the connection
        async with _pg_pool.acquire() as conn:
            version = await conn.fetchval("SELECT version()")
            logger.info("PostgreSQL connected: %s", version.split(",")[0])
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

    Usage:
        async with get_pg_conn() as conn:
            if conn:
                await conn.execute("INSERT INTO ...")
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
_redis_client: Optional[object] = None    # redis.asyncio.Redis


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


def get_redis() -> Optional[object]:
    """
    Return the Redis client instance.
    Returns None if Redis is unavailable (caller must handle gracefully).
    """
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
    """
    Return database health status for the /health endpoint.
    """
    pg_status = "connected" if is_postgres_available() else "unavailable (in-memory mode)"
    redis_status = "connected" if is_redis_available() else "unavailable (in-memory mode)"

    # Quick live probe if available
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
# Core Data Access Helpers (PostgreSQL with in-memory fallback)
# ─────────────────────────────────────────────────────────────────────────────
import json


async def insert_trust_event(
    session_id: str,
    query_id: str,
    query_text: str,
    answer_text: Optional[str],
    verdict: str,
    trust_score: float,
    trust_color: Optional[str] = None,
    agent_id: Optional[str] = None,
    relevance_result: Optional[dict] = None,
    groundedness_result: Optional[dict] = None,
    pii_result: Optional[dict] = None,
    evaluation_result: Optional[dict] = None,
    circuit_breaker_tripped: bool = False,
    context_chunks_count: Optional[int] = None,
    top_retrieval_score: Optional[float] = None,
    model_used: Optional[str] = None,
    latency_ms: Optional[int] = None,
) -> Optional[str]:
    """
    Insert a trust evaluation event into PostgreSQL.
    Returns the event UUID string or None if Postgres is unavailable.
    """
    if not is_postgres_available():
        return None

    try:
        async with get_pg_conn() as conn:
            if not conn:
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
        return None


async def get_trust_events(limit: int = 50, session_id: Optional[str] = None) -> list[dict]:
    """Retrieve recent trust events from PostgreSQL."""
    if not is_postgres_available():
        return []

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


async def insert_audit_log(
    action: str,
    subject_id: str,
    actor_id: str = "system",
    details: Optional[dict] = None,
    gdpr_article: Optional[str] = None,
) -> Optional[str]:
    """
    Insert an immutable audit log entry into PostgreSQL.
    """
    if not is_postgres_available():
        return None

    try:
        async with get_pg_conn() as conn:
            if not conn:
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
        return None

