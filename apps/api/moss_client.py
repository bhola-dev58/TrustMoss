"""
moss_client.py — Moss retrieval wrapper.

Wraps the official `moss` Python SDK (pip install moss).
On startup the app calls `init()` once which:
  1. Connects to Moss with project credentials
  2. Ensures the knowledge base index exists (creates it from SAMPLE_DOCS if not)
  3. Loads the index into memory so queries are sub-10 ms

`retrieve(query, top_k)` is the only function the pipeline calls.
It returns:
  {
    "chunks": [{"id": str, "text": str, "score": float}, ...],
    "top_score": float,
    "latency_ms": float       <- Moss query latency only, measured here
  }
"""

import asyncio
import logging
import os
import time
from typing import Any

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

try:
    from secret_manager import get_secret as _get_secret
except ImportError:
    _get_secret = lambda k, d="": os.getenv(k, d)  # noqa: E731

MOSS_PROJECT_ID = (
    _get_secret("MOSS_PROJECT_ID")
    or os.getenv("MOSS_PROJECT_ID")
    or os.getenv("MOSS_PROJECTID")
    or "ci-project"
)
MOSS_PROJECT_KEY = (
    _get_secret("MOSS_PROJECT_KEY")
    or os.getenv("MOSS_PROJECT_KEY")
    or os.getenv("MOSS_PROJECTKEY")
    or "ci-project-key"
)
MOSS_INDEX_NAME = (
    _get_secret("MOSS_INDEX_NAME")
    or os.getenv("MOSS_INDEX_NAME")
    or "trustmoss-kb"
)

# ---------------------------------------------------------------------------
# Sample knowledge base — used to seed the Moss index on first run.
# Covers a fictional SaaS product so demo queries work out of the box.
# ---------------------------------------------------------------------------
SAMPLE_DOCS = [
    {
        "id": "kb-001",
        "text": (
            "Our refund policy allows customers to request a full refund within 30 days "
            "of purchase. Digital products are eligible for refunds if the product is "
            "defective or not as described. Refunds are processed within 5–7 business days."
        ),
    },
    {
        "id": "kb-002",
        "text": (
            "To reset your password, go to the login page and click 'Forgot Password'. "
            "You will receive an email with a reset link valid for 24 hours. "
            "If you don't receive the email, check your spam folder or contact support."
        ),
    },
    {
        "id": "kb-003",
        "text": (
            "Our pricing plans are: Starter ($9/month) — up to 3 users, 10 GB storage; "
            "Pro ($29/month) — up to 20 users, 100 GB storage; "
            "Enterprise (custom) — unlimited users, dedicated support, SLA guarantee."
        ),
    },
    {
        "id": "kb-004",
        "text": (
            "TrustMoss supports Single Sign-On (SSO) via SAML 2.0 and OAuth 2.0. "
            "SSO configuration is available on Enterprise plans. "
            "Contact your account manager or submit a support ticket to enable it."
        ),
    },
    {
        "id": "kb-005",
        "text": (
            "Data retention: active account data is kept for the duration of your subscription. "
            "After cancellation, data is retained for 90 days and then permanently deleted. "
            "You can export all your data in CSV or JSON format from Account Settings > Export."
        ),
    },
    {
        "id": "kb-006",
        "text": (
            "API rate limits: free tier allows 100 requests/minute; "
            "Pro allows 1,000 requests/minute; Enterprise allows custom limits. "
            "Rate limit headers are included in every API response: X-RateLimit-Limit, "
            "X-RateLimit-Remaining, X-RateLimit-Reset."
        ),
    },
    {
        "id": "kb-007",
        "text": (
            "We maintain a 99.9% uptime SLA for Pro and Enterprise customers. "
            "Planned maintenance windows are scheduled on the first Sunday of each month "
            "between 02:00–04:00 UTC and announced 72 hours in advance via status page."
        ),
    },
    {
        "id": "kb-008",
        "text": (
            "To cancel your subscription, go to Account Settings > Billing > Cancel Subscription. "
            "Your access continues until the end of the current billing period. "
            "Cancellation takes effect immediately for annual plans with no pro-rated refund."
        ),
    },
]

# ---------------------------------------------------------------------------
# Moss client — lazy-initialized singleton
# ---------------------------------------------------------------------------
_moss_client: Any = None
_index_loaded: bool = False
_init_lock = asyncio.Lock()


async def init():
    """
    Initialize the Moss client and ensure the index is ready.
    Called once at FastAPI startup via lifespan.
    """
    global _moss_client, _index_loaded

    async with _init_lock:
        if _index_loaded:
            return  # Already initialized by another coroutine

        try:
            from moss import DocumentInfo, MossClient  # type: ignore

            logger.info("Connecting to Moss (project_id=%s)…", MOSS_PROJECT_ID)
            client = MossClient(MOSS_PROJECT_ID, MOSS_PROJECT_KEY)

            # Check if the index already exists; create it if not
            try:
                existing = await client.get_index(MOSS_INDEX_NAME)
                logger.info("Moss index '%s' already exists.", MOSS_INDEX_NAME)
            except Exception:
                logger.info(
                    "Moss index '%s' not found — creating from sample KB…",
                    MOSS_INDEX_NAME,
                )
                docs = [DocumentInfo(id=d["id"], text=d["text"]) for d in SAMPLE_DOCS]
                await client.create_index(MOSS_INDEX_NAME, docs)
                logger.info(
                    "Created Moss index '%s' with %d documents.", MOSS_INDEX_NAME, len(docs)
                )

            # Load index into memory for fast queries
            await client.load_index(MOSS_INDEX_NAME)
            logger.info("Moss index '%s' loaded into memory.", MOSS_INDEX_NAME)

            _moss_client = client
            _index_loaded = True

        except ImportError:
            logger.warning(
                "moss package not installed — falling back to MOCK mode. "
                "Run: pip install moss"
            )
            _moss_client = None
            _index_loaded = True  # Mark as done so we don't retry
        except Exception as exc:
            logger.error("Failed to initialize Moss: %s — falling back to MOCK.", exc)
            _moss_client = None
            _index_loaded = True


async def retrieve(query: str, top_k: int = 3) -> dict:
    """
    Query Moss and return context chunks with scores.
    Falls back to deterministic mock if Moss is unavailable.
    """
    if _moss_client is not None:
        return await _retrieve_real(query, top_k)
    else:
        return _retrieve_mock(query, top_k)


async def _retrieve_real(query: str, top_k: int) -> dict:
    from moss import QueryOptions  # type: ignore

    t0 = time.perf_counter()
    results = await _moss_client.query(
        MOSS_INDEX_NAME, query, QueryOptions(top_k=top_k)
    )
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    chunks = [
        {"id": doc.id, "text": doc.text, "score": round(doc.score, 4)}
        for doc in results.docs
    ]
    top_score = chunks[0]["score"] if chunks else 0.0

    return {"chunks": chunks, "top_score": top_score, "latency_ms": latency_ms}


def _retrieve_mock(query: str, top_k: int) -> dict:
    """
    Deterministic mock: scores docs by simple keyword overlap so the pipeline
    behaves realistically (off-topic queries get low scores → WARN/FAIL trust).
    """
    import re

    query_words = set(re.findall(r"\w+", query.lower()))

    scored: list[dict] = []
    for doc in SAMPLE_DOCS:
        doc_words = set(re.findall(r"\w+", doc["text"].lower()))
        overlap = len(query_words & doc_words)
        total = len(query_words | doc_words)
        score = round(overlap / total if total else 0.0, 4)
        scored.append({"id": doc["id"], "text": doc["text"], "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    chunks = scored[:top_k]
    top_score = chunks[0]["score"] if chunks else 0.0

    # Simulate realistic Moss latency (2–12 ms)
    import random
    latency_ms = round(random.uniform(2.0, 12.0), 2)

    return {"chunks": chunks, "top_score": top_score, "latency_ms": latency_ms}
