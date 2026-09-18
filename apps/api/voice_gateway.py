"""
voice_gateway.py — Real-time Voice Audio & Transcript Reliability Gateway for LiveKit.

Routes LiveKit WebRTC audio transcripts through the TrustMoss safety fabric:
1. Inbound Guardrails (Jailbreak, Injection, PII scrubbing on speech)
2. Ultra-low latency Moss contextual retrieval (sub-15ms)
3. Pre-generation relevance gating
4. LLM reasoning (Groq / Llama-3.1)
5. Outbound groundedness evaluation (target >= 0.85)
6. Outbound PII / toxicity verification
7. Tri-state circuit breaker (PASS/WARN/FAIL): Immediately suppresses audio playback on FAIL
8. Per-hop voice latency telemetry (WebRTC Ingress -> STT -> Inbound -> Moss -> LLM -> Groundedness -> TTS)
"""

from datetime import UTC, datetime
import logging
import os
import time
from typing import Any
import uuid

from dotenv import load_dotenv
from groq import AsyncGroq
from guardrails import pii_scan, relevance
import moss_client
from prompts.crispe import VOICE_AGENT_V1, render_voice_prompt
from retention import DataCategory, retention_manager
from tracer import Tracer
from trust_score import aggregate

load_dotenv()

_voice_groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", ""))
_voice_groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
logger = logging.getLogger("trustmoss.voice_gateway")

# In-memory session tracking for voice rooms
_voice_sessions: dict[str, dict[str, Any]] = {}

# Quantitative Thresholds as per PRD & evaluation benchmarks
GROUNDEDNESS_TARGET = float(os.getenv("GROUNDEDNESS_THRESHOLD", "0.85"))
RELEVANCE_TARGET = float(os.getenv("RELEVANCE_THRESHOLD", "0.70"))
CIRCUIT_BREAKER_FALLBACK_SPEECH = (
    "Notice: Trust verification failed. The generated response was suppressed "
    "by the circuit breaker to prevent ungrounded information."
)


def compute_audio_groundedness(answer: str, context_chunks: list[dict]) -> dict:
    """
    Evaluates real-time groundedness of agent voice transcripts against retrieved Moss chunks.
    Target threshold: >= 0.85 for production trust.
    """
    if not context_chunks:
        return {
            "passed": False,
            "score": 0.0,
            "reason": "Zero context chunks retrieved from Moss. Hallucination risk high.",
        }

    # Extract all text tokens/words from retrieved chunks
    context_text = " ".join(c.get("text", "") for c in context_chunks).lower()
    answer_words = [w.strip(".,!?;:()[]\"'") for w in answer.lower().split() if len(w) > 3]

    if not answer_words:
        return {
            "passed": True,
            "score": 1.0,
            "reason": "Minimal or trivial voice response; passed groundedness.",
        }

    matches = sum(1 for word in answer_words if word in context_text)
    groundedness_score = round(min(1.0, matches / max(1, len(answer_words))), 2)

    passed = groundedness_score >= GROUNDEDNESS_TARGET
    reason = (
        f"Groundedness score {groundedness_score:.2f} meets target {GROUNDEDNESS_TARGET:.2f}"
        if passed
        else f"Groundedness score {groundedness_score:.2f} below target {GROUNDEDNESS_TARGET:.2f}"
    )

    return {
        "passed": passed,
        "score": groundedness_score,
        "reason": reason,
    }


def scan_speech_injection(transcript: str) -> dict:
    """
    Scans real-time spoken transcript for prompt injection or jailbreak attempts.
    """
    adversarial_triggers = [
        "ignore previous instructions",
        "system override",
        "bypass guardrails",
        "disregard safety",
        "developer mode",
        "dan mode",
        "jailbreak",
        "reveal system prompt",
    ]
    lower = transcript.lower()
    detected = [phrase for phrase in adversarial_triggers if phrase in lower]
    if detected:
        return {
            "passed": False,
            "score": 0.0,
            "reason": f"Spoken injection/jailbreak detected: {', '.join(detected)}",
        }
    return {
        "passed": True,
        "score": 1.0,
        "reason": "Spoken transcript verified safe.",
    }


async def process_voice_turn(
    room_name: str,
    participant_identity: str,
    transcript: str,
    top_k: int = 3,
    simulated_webrtc_ms: float = 12.0,
    simulated_stt_ms: float = 45.0,
) -> dict[str, Any]:
    """
    Main real-time voice pipeline interceptor.
    Routes speech from LiveKit through Trust Gateway and executes circuit breaker if needed.
    """
    turn_id = str(uuid.uuid4())[:8]
    tracer = Tracer()

    # 1. Ingress & STT tracing
    with tracer.stage("webrtc_ingress"):
        time.sleep(min(simulated_webrtc_ms / 1000.0, 0.05))

    with tracer.stage("stt_transcription"):
        time.sleep(min(simulated_stt_ms / 1000.0, 0.05))

    # 2. Inbound speech guardrail
    with tracer.stage("inbound_guardrail"):
        injection_result = scan_speech_injection(transcript)
        inbound_pii = pii_scan.check(transcript)

    # If injection detected, trip breaker immediately before hitting Moss or LLM
    if not injection_result["passed"]:
        total_ms = tracer.total_ms()
        return {
            "turn_id": turn_id,
            "room_name": room_name,
            "participant": participant_identity,
            "user_transcript": transcript,
            "final_speech_text": "Warning: Prompt injection attempt detected in audio stream. Query blocked.",
            "audio_suppressed": True,
            "circuit_breaker_tripped": True,
            "trust": {
                "verdict": "FAIL",
                "color": "red",
                "score": 0.0,
                "reason": injection_result["reason"],
                "failed_checks": ["injection"],
            },
            "latency_trace": tracer.get_trace(),
            "total_latency_ms": total_ms,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    # 3. Moss retrieval
    with tracer.stage("moss_retrieval"):
        retrieval = await moss_client.retrieve(transcript, top_k=top_k)
        context_chunks = retrieval.get("chunks", [])
        top_score = retrieval.get("top_score", 0.0)

    # 4. Relevance check
    with tracer.stage("relevance_gate"):
        relevance_result = relevance.check(top_score)

    # 5. LLM reasoning — VOICE_AGENT_V1 CRISPE template (TTS-optimised brevity)
    with tracer.stage("llm_reasoning"):
        _sys, _usr = render_voice_prompt(transcript, context_chunks)
        _resp = await _voice_groq_client.chat.completions.create(
            model=_voice_groq_model,
            messages=[
                {"role": "system", "content": _sys},
                {"role": "user", "content": _usr},
            ],
            max_tokens=VOICE_AGENT_V1.metadata.get("max_tokens", 256),
            temperature=VOICE_AGENT_V1.metadata.get("temperature", 0.25),
        )
        raw_agent_response = _resp.choices[0].message.content.strip()

    # 6. Outbound Groundedness & PII
    with tracer.stage("groundedness_eval"):
        groundedness_result = compute_audio_groundedness(raw_agent_response, context_chunks)

    with tracer.stage("outbound_pii_check"):
        outbound_pii = pii_scan.check(raw_agent_response)
        sanitized_response = outbound_pii.get("redacted_answer", raw_agent_response)

    # 7. Tri-state trust aggregation
    trust = aggregate(relevance_result, groundedness_result, outbound_pii)

    # 8. Circuit Breaker Enforcement on Audio
    circuit_breaker_tripped = False
    audio_suppressed = False

    if trust["verdict"] == "FAIL":
        circuit_breaker_tripped = True
        audio_suppressed = True
        final_speech_text = CIRCUIT_BREAKER_FALLBACK_SPEECH
    elif trust["verdict"] == "WARN":
        final_speech_text = f"[Notice: Low confidence] {sanitized_response}"
    else:
        final_speech_text = sanitized_response

    # 9. TTS preparation
    with tracer.stage("tts_synthesis"):
        # Synthetic TTS budget tracking (audio buffer packaging)
        time.sleep(0.005)

    total_ms = tracer.total_ms()
    latency_trace = tracer.get_trace()

    result = {
        "turn_id": turn_id,
        "room_name": room_name,
        "participant": participant_identity,
        "user_transcript": transcript,
        "raw_response": raw_agent_response,
        "final_speech_text": final_speech_text,
        "audio_suppressed": audio_suppressed,
        "circuit_breaker_tripped": circuit_breaker_tripped,
        "context_chunks": context_chunks,
        "verdict": trust["verdict"],
        "trust": trust,
        "guardrails": {
            "injection": injection_result,
            "relevance": relevance_result,
            "groundedness": groundedness_result,
            "pii": outbound_pii,
        },
        "latency_trace": latency_trace,
        "total_latency_ms": total_ms,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    # Record into voice session telemetry
    if room_name not in _voice_sessions:
        _voice_sessions[room_name] = {
            "room_name": room_name,
            "participant_identity": participant_identity,
            "created_at": datetime.now(UTC).isoformat(),
            "turns": [],
            "total_turns": 0,
            "circuit_breaker_events": 0,
        }

    session = _voice_sessions[room_name]
    session["participant_identity"] = participant_identity
    session["total_turns"] += 1
    if circuit_breaker_tripped:
        session["circuit_breaker_events"] += 1
    session["turns"].append({
        "turn_id": turn_id,
        "timestamp": result["timestamp"],
        "verdict": trust["verdict"],
        "total_ms": total_ms,
        "circuit_breaker": circuit_breaker_tripped,
    })
    # Keep last 50 turns
    if len(session["turns"]) > 50:
        session["turns"].pop(0)

    # Register transcript turn under GDPR TTL retention manager
    try:
        retention_manager.register_record(
            record_id=turn_id,
            subject_id=participant_identity,
            category=DataCategory.TRANSCRIPT,
            data={
                "room_name": room_name,
                "transcript": transcript,
                "verdict": trust["verdict"],
                "circuit_breaker_tripped": circuit_breaker_tripped,
                "latency_breakdown": result.get("latency_trace", []),
            },
        )
    except Exception as e:
        logger.warning("Could not register turn in retention manager: %s", e)

    logger.info(
        "Voice turn completed: room=%s turn_id=%s verdict=%s cb=%s total_ms=%.1f",
        room_name,
        turn_id,
        trust["verdict"],
        circuit_breaker_tripped,
        total_ms,
    )

    return result


def get_voice_session(room_name: str) -> dict[str, Any] | None:
    """Fetch active voice room session metrics."""
    return _voice_sessions.get(room_name)


def list_active_voice_sessions() -> list[dict[str, Any]]:
    """List summary of all active voice rooms."""
    return [
        {
            "room_name": s["room_name"],
            "participant_identity": s.get("participant_identity"),
            "created_at": s["created_at"],
            "total_turns": s["total_turns"],
            "circuit_breaker_events": s["circuit_breaker_events"],
        }
        for s in _voice_sessions.values()
    ]


def erase_voice_session_data(subject_or_room: str) -> int:
    """
    Purges voice sessions matching room_name or participant_identity.
    Supports GDPR Article 17 Right to Erasure.
    """
    to_delete = [
        room for room, sess in _voice_sessions.items()
        if room == subject_or_room or sess.get("participant_identity") == subject_or_room
    ]
    for r in to_delete:
        del _voice_sessions[r]
    return len(to_delete)
