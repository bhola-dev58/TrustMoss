"""
livekit_service.py — LiveKit Voice & Video Gateway Service for TrustMoss.

Handles WebRTC access token generation for voice participants and autonomous voice agents,
validates connection state, and manages room permissions.
"""

import logging
import os
from datetime import timedelta
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("trustmoss.livekit")

# ── Secret Resolution via unified provider (Vault | AWS | ENV) ────────────────
try:
    from secrets import get_secret as _get_secret
except ImportError:
    _get_secret = lambda key, default=None: os.getenv(key, default)  # noqa: E731

LIVEKIT_URL        = _get_secret("LIVEKIT_URL")        or os.getenv("LIVEKIT_URL", "wss://trustmoss-demo.livekit.cloud")
LIVEKIT_API_KEY    = _get_secret("LIVEKIT_API_KEY")    or os.getenv("LIVEKIT_API_KEY", "devkey")
LIVEKIT_API_SECRET = _get_secret("LIVEKIT_API_SECRET") or os.getenv("LIVEKIT_API_SECRET", "secret0123456789abcdef0123456789abcdef")


def get_livekit_config() -> dict:
    """Return public configuration for client connections."""
    return {
        "url": LIVEKIT_URL,
        "configured": bool(LIVEKIT_API_KEY and LIVEKIT_API_SECRET),
        "protocol": "webrtc",
    }


def generate_token(
    room_name: str,
    participant_identity: str,
    participant_name: Optional[str] = None,
    is_agent: bool = False,
    ttl_seconds: int = 3600,
) -> str:
    """
    Generate an authenticated WebRTC JWT token for a LiveKit room participant or AI agent.
    """
    try:
        from livekit.api import AccessToken, VideoGrants
    except ImportError:
        logger.error("livekit-api package is not installed.")
        raise RuntimeError("LiveKit API SDK is required for voice gateway tokens.")

    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise ValueError("LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be configured.")

    token = AccessToken(
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_API_SECRET,
    )
    token.identity = participant_identity
    token.name = participant_name or participant_identity
    token.ttl = timedelta(seconds=ttl_seconds)

    # Set WebRTC video/audio grants
    grants = VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
    )

    if is_agent:
        token.metadata = '{"role": "trustmoss_voice_agent", "trust_mode": "strict"}'
    else:
        token.metadata = '{"role": "client_participant"}'

    token.video_grants = grants
    jwt_token = token.to_jwt()
    logger.info(
        "Generated LiveKit token for room=%s participant=%s is_agent=%s",
        room_name,
        participant_identity,
        is_agent,
    )
    return jwt_token
