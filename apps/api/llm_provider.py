"""
llm_provider.py — Production Multi-Provider LLM Inference Engine with Automatic Fallback.

Supports:
  1. Primary: HiDevs Gemini Gateway (gemini-3.5-flash, gemini-3.6-flash, gemini-3.5-flash-lite)
     Endpoint: https://llm.hidevs.xyz/v1/chat/completions (OpenAI-compatible)
  2. Secondary / Fallback: Groq Cloud API (llama-3.1-8b-instant)
  3. Grounded Fallback: Deterministic context synthesis when remote APIs are unavailable.
"""

import logging
import os
from typing import Any, Tuple
import httpx
from groq import AsyncGroq

logger = logging.getLogger(__name__)

# Environment Configuration
LLM_GATEWAY_URL = (
    os.getenv("LLM_GATEWAY_URL")
    or "https://llm.hidevs.xyz/v1"
).rstrip("/")

LLM_API_KEY = (
    os.getenv("LLM_API_KEY")
    or os.getenv("GEMINI_API_KEY")
    or ""
)

LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.5-flash")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

_groq_client: AsyncGroq | None = None


def get_groq_client() -> AsyncGroq:
    global _groq_client
    if _groq_client is None:
        _groq_client = AsyncGroq(api_key=GROQ_API_KEY or "ci-dummy-key")
    return _groq_client


async def call_gemini_gateway(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
    max_tokens: int = 512,
    temperature: float = 0.2,
    timeout_sec: float = 12.0,
) -> str | None:
    """
    Calls the HiDevs Gemini gateway (OpenAI-compatible /v1/chat/completions endpoint).
    Returns content string on success, or None on failure to enable seamless fallback.
    """
    if os.getenv("ENV") == "test" or os.getenv("TESTING") == "1":
        return None

    api_key = os.getenv("LLM_API_KEY") or LLM_API_KEY
    if not api_key:
        return None

    target_model = model or os.getenv("LLM_MODEL", LLM_MODEL)
    endpoint = f"{LLM_GATEWAY_URL}/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": target_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout_sec) as client:
            res = await client.post(endpoint, headers=headers, json=payload)
            if res.status_code == 200:
                data = res.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "").strip()
                    if content:
                        logger.info("HiDevs Gemini generation succeeded with model: %s", target_model)
                        return content
            logger.warning("HiDevs Gemini returned status %s: %s", res.status_code, res.text[:200])
    except Exception as exc:
        logger.warning("HiDevs Gemini call failed (%s). Falling back to Groq.", exc)

    return None


async def generate_chat_completion(
    system_prompt: str,
    user_message: str,
    context_chunks: list | None = None,
    max_tokens: int = 512,
    temperature: float = 0.2,
    custom_groq_client: Any = None,
) -> Tuple[str, str]:
    """
    Multi-provider inference orchestrator:
      1. Tries HiDevs Gemini (100K token grant)
      2. Tries Groq Cloud API (llama-3.1-8b-instant)
      3. Falls back to verified context chunks
    Returns: (generated_text, model_name_used)
    """
    # 1. Primary: HiDevs Gemini
    gemini_resp = await call_gemini_gateway(
        system_prompt=system_prompt,
        user_message=user_message,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    if gemini_resp:
        return gemini_resp, f"{LLM_MODEL} (HiDevs Gateway)"

    # 2. Secondary: Groq LLM
    groq = custom_groq_client or get_groq_client()
    try:
        response = await groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        content = response.choices[0].message.content.strip()
        if content:
            return content, GROQ_MODEL
        raise ValueError("Groq returned empty response.")
    except Exception as exc:
        logger.warning("Groq call failed (%s). Activating deterministic context fallback.", exc)

    # 3. Grounded Fallback: Synthesize from context chunks
    chunks = context_chunks or []
    for chunk in chunks:
        text = (chunk.get("text") or "").strip()
        if text:
            return text, "context-deterministic-fallback"

    return "I'm unable to complete this request right now. Please try again shortly.", "safe-quarantine-fallback"
