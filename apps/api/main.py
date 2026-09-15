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
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from groq import AsyncGroq
from pydantic import BaseModel

import auth
import livekit_service
import moss_client
import voice_gateway
from guardrails import groundedness, pii_scan, relevance
from security_middleware import SecurityHeadersMiddleware
from tracer import Tracer
from trust_score import aggregate

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Microservice Topology URLs (empty = local colocated execution)
GUARDRAILS_SERVICE_URL = os.getenv("GUARDRAILS_SERVICE_URL", "").rstrip("/")
MOSS_SERVICE_URL = os.getenv("MOSS_SERVICE_URL", "").rstrip("/")
EVALUATION_SERVICE_URL = os.getenv("EVALUATION_SERVICE_URL", "").rstrip("/")

# In-memory session history (list of QueryResponse dicts)
_session_history: List[dict] = []

# ---------------------------------------------------------------------------
# Groq client (module-level singleton)
# ---------------------------------------------------------------------------
groq_client = AsyncGroq(api_key=GROQ_API_KEY)


# ---------------------------------------------------------------------------
# Microservice Dispatch Helpers (HTTP with local fallback)
# ---------------------------------------------------------------------------
import httpx


async def dispatch_retrieval(query: str, top_k: int = 3) -> dict:
    if MOSS_SERVICE_URL:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(f"{MOSS_SERVICE_URL}/retrieve", json={"query": query, "top_k": top_k})
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.warning("Moss microservice error (%s), falling back to local client.", e)
    return await moss_client.retrieve(query, top_k=top_k)


async def dispatch_evaluation(query: str, answer: str, context_chunks: list, top_score: float, pii_res: dict) -> dict:
    if EVALUATION_SERVICE_URL:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"{EVALUATION_SERVICE_URL}/evaluate",
                    json={
                        "query": query,
                        "answer": answer,
                        "context_chunks": context_chunks,
                        "top_score": top_score,
                        "pii_passed": pii_res.get("passed", True),
                        "pii_reason": pii_res.get("reason", ""),
                    },
                )
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.warning("Evaluation microservice error (%s), falling back to local evaluator.", e)

    rel_res = relevance.check(top_score)
    ground_res = groundedness.check(answer, context_chunks)
    trust_res = aggregate(rel_res, ground_res, pii_res)
    return {
        "verdict": trust_res["verdict"],
        "color": trust_res["color"],
        "score": trust_res["score"],
        "reason": trust_res["reason"],
        "groundedness": ground_res,
        "relevance": rel_res,
        "circuit_breaker_tripped": trust_res["verdict"] == "FAIL",
    }


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

# OWASP API Security Middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS configuration
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://web:3000",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if os.getenv("ENV") == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],
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


class LiveKitTokenRequest(BaseModel):
    room_name: str
    participant_identity: str
    participant_name: Optional[str] = None
    is_agent: bool = False
    ttl_seconds: int = 3600


class VoiceTurnRequest(BaseModel):
    room_name: str
    participant_identity: str
    transcript: str
    top_k: int = 3
    webrtc_latency_ms: float = 12.0
    stt_latency_ms: float = 45.0


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
        retrieval = await dispatch_retrieval(request.query, top_k=request.top_k)

    context_chunks = retrieval.get("chunks", [])
    top_score = retrieval.get("top_score", 0.0)

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
    # Stage 4: Outbound PII scan
    # ------------------------------------------------------------------
    with tracer.stage("pii_scan"):
        pii_result = pii_scan.check(answer)

    final_answer = pii_result.get("redacted_answer", answer)

    # ------------------------------------------------------------------
    # Stage 5: Evaluation & Trust Aggregation (Microservice / Local)
    # ------------------------------------------------------------------
    with tracer.stage("evaluation_and_trust"):
        eval_result = await dispatch_evaluation(
            query=request.query,
            answer=final_answer,
            context_chunks=context_chunks,
            top_score=top_score,
            pii_res=pii_result,
        )

    trust = {
        "verdict": eval_result["verdict"],
        "color": eval_result["color"],
        "score": eval_result["score"],
        "reason": eval_result["reason"],
    }
    groundedness_result = eval_result.get("groundedness", {})

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
# LiveKit & Real-Time Voice Gateway Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/livekit/config")
async def livekit_config_endpoint():
    """Returns public LiveKit gateway connection metadata."""
    return livekit_service.get_livekit_config()


@app.post("/api/livekit/token")
async def livekit_token_endpoint(request: LiveKitTokenRequest):
    """
    Generate an authenticated WebRTC access token for a LiveKit room participant or AI agent.
    """
    try:
        token = livekit_service.generate_token(
            room_name=request.room_name,
            participant_identity=request.participant_identity,
            participant_name=request.participant_name,
            is_agent=request.is_agent,
            ttl_seconds=request.ttl_seconds,
        )
        return {
            "token": token,
            "room_name": request.room_name,
            "participant": request.participant_identity,
            "is_agent": request.is_agent,
            "url": livekit_service.LIVEKIT_URL,
        }
    except Exception as e:
        logger.error("Failed to generate LiveKit token: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice/process-transcript")
async def process_voice_transcript_endpoint(request: VoiceTurnRequest):
    """
    Real-time LiveKit audio transcript reliability gateway.
    Routes user speech through Trust Gateway and executes tri-state circuit breaker.
    """
    try:
        result = await voice_gateway.process_voice_turn(
            room_name=request.room_name,
            participant_identity=request.participant_identity,
            transcript=request.transcript,
            top_k=request.top_k,
            simulated_webrtc_ms=request.webrtc_latency_ms,
            simulated_stt_ms=request.stt_latency_ms,
        )
        return result
    except Exception as e:
        logger.error("Error processing voice turn: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/voice/session/{room_name}")
async def voice_session_endpoint(room_name: str):
    """Retrieve telemetry and latency metrics for an active voice room."""
    session = voice_gateway.get_voice_session(room_name)
    if not session:
        raise HTTPException(status_code=404, detail="Voice session not found.")
    return session


@app.get("/api/voice/sessions")
async def list_voice_sessions_endpoint():
    """List all active LiveKit voice rooms and their circuit breaker statistics."""
    return {"sessions": voice_gateway.list_active_voice_sessions()}


# ---------------------------------------------------------------------------
# Auth Endpoints (JWT / OAuth2 & RBAC)
# ---------------------------------------------------------------------------
@app.post("/api/auth/token", response_model=auth.TokenResponse)
async def generate_token_endpoint(req: auth.TokenRequest):
    """Issues authenticated JWT token for agent, reviewer, or admin roles."""
    if req.role not in ["agent", "reviewer", "admin"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid role. Must be 'agent', 'reviewer', or 'admin'.",
        )

    token = auth.create_access_token(identity=req.client_id, role=req.role)
    return auth.TokenResponse(
        access_token=token,
        role=req.role,
        client_id=req.client_id,
        expires_in_minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


@app.get("/api/auth/me")
async def get_current_user_endpoint(user: dict = Depends(auth.get_current_user)):
    """Returns currently authenticated identity and assigned role."""
    return {
        "identity": user.get("sub"),
        "role": user.get("role"),
        "auth_mode": user.get("mode", "jwt_verified"),
    }


# ---------------------------------------------------------------------------
# GET /health — liveness
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {
        "service": "trustmoss-gateway",
        "status": "healthy",
        "version": "0.2.0",
        "security": {
            "auth_strict": auth.AUTH_STRICT,
            "owasp_headers_enabled": True,
            "jwt_algorithm": auth.JWT_ALGORITHM,
        },
        "microservices": {
            "guardrails_service": GUARDRAILS_SERVICE_URL or "internal/colocated",
            "moss_service": MOSS_SERVICE_URL or "internal/colocated",
            "evaluation_service": EVALUATION_SERVICE_URL or "internal/colocated",
            "livekit_voice_gateway": livekit_service.get_livekit_config()["configured"],
        },
    }
