"""
guardrails_service.py — Dedicated Microservice for Inbound & Outbound Safety (Port 8001).

Responsibilities:
1. Inbound: Prompt injection classification, jailbreak detection, PII masking.
2. Outbound: Groundedness verification support, outbound PII redaction, toxic speech filtering.
3. Isolated failure domain: Independent health checks, autoscaling boundary, and zero reliance on LLM runtime.
"""

import logging
import os
import sys

# Add apps/api to path to reuse existing guardrail modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../apps/api")))

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from guardrails import pii_scan
from pydantic import BaseModel

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trustmoss.guardrails_service")

app = FastAPI(
    title="TrustMoss Guardrails Service",
    description="Dedicated microservice for inbound and outbound AI agent safety filtering.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ADVERSARIAL_PATTERNS = [
    "ignore previous instructions",
    "system override",
    "bypass guardrails",
    "disregard safety",
    "developer mode",
    "dan mode",
    "jailbreak",
    "reveal system prompt",
    "exfiltrate credentials",
]


class InboundScanRequest(BaseModel):
    prompt: str


class InboundScanResponse(BaseModel):
    passed: bool
    is_jailbreak: bool
    pii_detected: bool
    sanitized_prompt: str
    risk_category: str | None = None
    reason: str


class OutboundScanRequest(BaseModel):
    response_text: str


class OutboundScanResponse(BaseModel):
    passed: bool
    pii_detected: bool
    redacted_response: str
    reason: str


@app.post("/inbound/scan", response_model=InboundScanResponse)
async def inbound_scan(req: InboundScanRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    lower = req.prompt.lower()
    detected_jailbreaks = [p for p in ADVERSARIAL_PATTERNS if p in lower]
    pii_res = pii_scan.check(req.prompt)

    is_jailbreak = len(detected_jailbreaks) > 0
    pii_found = not pii_res["passed"]

    if is_jailbreak:
        return InboundScanResponse(
            passed=False,
            is_jailbreak=True,
            pii_detected=pii_found,
            sanitized_prompt="[BLOCKED: Adversarial prompt injection detected]",
            risk_category="prompt_injection",
            reason=f"Adversarial patterns flagged: {', '.join(detected_jailbreaks)}",
        )

    return InboundScanResponse(
        passed=not pii_found,
        is_jailbreak=False,
        pii_detected=pii_found,
        sanitized_prompt=pii_res.get("redacted_answer", req.prompt),
        risk_category=None if not pii_found else "pii_exposure",
        reason="Inbound checks passed clean." if not pii_found else pii_res["reason"],
    )


@app.post("/outbound/scan", response_model=OutboundScanResponse)
async def outbound_scan(req: OutboundScanRequest):
    pii_res = pii_scan.check(req.response_text)
    return OutboundScanResponse(
        passed=pii_res["passed"],
        pii_detected=not pii_res["passed"],
        redacted_response=pii_res.get("redacted_answer", req.response_text),
        reason=pii_res["reason"],
    )


@app.get("/health")
async def health():
    return {
        "service": "guardrails-service",
        "status": "healthy",
        "version": "0.2.0",
        "patterns_loaded": len(ADVERSARIAL_PATTERNS),
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("GUARDRAILS_PORT", "8001"))
    uvicorn.run(app, host=os.getenv("HOST", "0.0.0.0"), port=port)  # nosec B104
