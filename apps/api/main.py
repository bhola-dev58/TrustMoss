"""
main.py — TrustMoss FastAPI backend.

Endpoints:
  POST /query    — full pipeline: Moss retrieval → guardrails → LLM → trust score
  GET  /history  — returns session query history (in-memory for MVP)
  GET  /health   — liveness check

Pipeline order:
  1. Moss retrieval          (moss_client)
  2. Relevance check         (guardrails.relevance)
  3. LLM generation          (Groq)
  4. Groundedness check      (guardrails.groundedness  — stub in baseline)
  5. PII scan                (guardrails.pii_scan      — stub in baseline)
  6. Trust score aggregation (trust_score)
"""

import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from groq import AsyncGroq
from pydantic import BaseModel

import moss_client
from guardrails import groundedness, pii_scan, relevance
from tracer import Tracer
from trust_score import aggregate

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# In-memory session history (list of QueryResponse dicts)
_session_history: List[dict] = []

# ---------------------------------------------------------------------------
# Groq client (module-level singleton)
# ---------------------------------------------------------------------------
groq_client = AsyncGroq(api_key=GROQ_API_KEY)


# ---------------------------------------------------------------------------
# Lifespan: initialize Moss on startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting TrustMoss backend…")
    await moss_client.init()
    logger.info("Moss client ready. Server accepting requests.")
    yield
    logger.info("Shutting down TrustMoss backend.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="TrustMoss API",
    description="Real-time trust layer for AI agent responses.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Tighten before production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    query: str
    top_k: int = 3


class QueryResponse(BaseModel):
    query_id: str
    query: str
    answer: str
    context_chunks: list
    trust: dict
    guardrails: dict
    latency_trace: list
    total_latency_ms: float
    timestamp: str


# ---------------------------------------------------------------------------
# Helper: call Groq LLM
# ---------------------------------------------------------------------------
async def call_llm(query: str, context_chunks: list) -> str:
    context_text = "\n\n".join(
        f"[Source {i + 1}] {chunk['text']}"
        for i, chunk in enumerate(context_chunks)
    )

    system_prompt = (
        "You are a helpful knowledge base assistant. "
        "Answer the user's question using ONLY the provided context. "
        "If the context doesn't contain enough information, say so clearly. "
        "Be concise and accurate."
    )

    user_message = (
        f"Context:\n{context_text}\n\n"
        f"Question: {query}\n\n"
        "Answer:"
    )

    response = await groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        max_tokens=512,
        temperature=0.3,
    )

    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# POST /query — main pipeline
# ---------------------------------------------------------------------------
@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    tracer = Tracer()
    query_id = str(uuid.uuid4())[:8]

    # ------------------------------------------------------------------
    # Stage 1: Moss retrieval
    # ------------------------------------------------------------------
    with tracer.stage("moss_retrieval"):
        retrieval = await moss_client.retrieve(request.query, top_k=request.top_k)

    context_chunks = retrieval["chunks"]
    top_score = retrieval["top_score"]

    # ------------------------------------------------------------------
    # Stage 2: Relevance check (pre-LLM guardrail)
    # ------------------------------------------------------------------
    with tracer.stage("relevance_check"):
        relevance_result = relevance.check(top_score)

    # ------------------------------------------------------------------
    # Stage 3: LLM generation (Groq)
    # ------------------------------------------------------------------
    with tracer.stage("llm_generation"):
        answer = await call_llm(request.query, context_chunks)

    # ------------------------------------------------------------------
    # Stage 4: Groundedness check (stub in baseline)
    # ------------------------------------------------------------------
    with tracer.stage("groundedness_check"):
        groundedness_result = groundedness.check(answer, context_chunks)

    # ------------------------------------------------------------------
    # Stage 5: PII scan (stub in baseline)
    # ------------------------------------------------------------------
    with tracer.stage("pii_scan"):
        pii_result = pii_scan.check(answer)

    # Use the (possibly redacted) answer going forward
    final_answer = pii_result["redacted_answer"]

    # ------------------------------------------------------------------
    # Stage 6: Trust score aggregation
    # ------------------------------------------------------------------
    trust = aggregate(relevance_result, groundedness_result, pii_result)

    # ------------------------------------------------------------------
    # Build response
    # ------------------------------------------------------------------
    latency_trace = tracer.get_trace()
    total_ms = tracer.total_ms()

    response = {
        "query_id": query_id,
        "query": request.query,
        "answer": final_answer,
        "context_chunks": context_chunks,
        "trust": trust,
        "guardrails": {
            "relevance": relevance_result,
            "groundedness": groundedness_result,
            "pii": {k: v for k, v in pii_result.items() if k != "redacted_answer"},
        },
        "latency_trace": latency_trace,
        "total_latency_ms": total_ms,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    # Store in session history (keep last 50)
    _session_history.append(response)
    if len(_session_history) > 50:
        _session_history.pop(0)

    logger.info(
        "query_id=%s verdict=%s total_ms=%.1f",
        query_id,
        trust["verdict"],
        total_ms,
    )

    return response


# ---------------------------------------------------------------------------
# GET /history — session log
# ---------------------------------------------------------------------------
@app.get("/history")
async def history_endpoint():
    return {
        "count": len(_session_history),
        "queries": list(reversed(_session_history)),  # newest first
    }


# ---------------------------------------------------------------------------
# GET /health — liveness
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
