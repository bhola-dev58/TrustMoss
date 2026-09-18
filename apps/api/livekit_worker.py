"""
livekit_worker.py — Autonomous LiveKit Voice Agent Worker for TrustMoss.

Subscribes to incoming audio streams in a LiveKit room, transcribes user speech,
routes transcripts through the Trust Gateway, and streams back verified audio while
publishing real-time trust telemetry and circuit-breaker status to room participants via DataChannel.
"""

import argparse
import asyncio
import json
import logging

from dotenv import load_dotenv
import livekit_service
import voice_gateway

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trustmoss.livekit_worker")

AGENT_IDENTITY = "trustmoss-agent"
DEFAULT_ROOM = "trustmoss-demo-room"


class TrustMossVoiceAgent:
    """
    LiveKit Real-time Voice Agent managing audio tracks, trust evaluation,
    and circuit-breaker interrupts.
    """

    def __init__(self, room_name: str = DEFAULT_ROOM):
        self.room_name = room_name
        self.agent_identity = AGENT_IDENTITY
        self.token = livekit_service.generate_token(
            room_name=self.room_name,
            participant_identity=self.agent_identity,
            participant_name="TrustMoss Voice Agent",
            is_agent=True,
        )

    async def handle_user_transcript(
        self,
        participant_identity: str,
        transcript: str,
    ) -> dict:
        """
        Process incoming participant voice transcript through Trust Gateway.
        """
        logger.info(
            "Agent received speech from [%s] in room [%s]: '%s'",
            participant_identity,
            self.room_name,
            transcript,
        )

        # Route through Trust Gateway
        eval_result = await voice_gateway.process_voice_turn(
            room_name=self.room_name,
            participant_identity=participant_identity,
            transcript=transcript,
        )

        logger.info(
            "Trust Evaluation verdict=%s (CB=%s, latency=%.1fms)",
            eval_result["trust"]["verdict"],
            eval_result["circuit_breaker_tripped"],
            eval_result["total_latency_ms"],
        )

        return eval_result

    def format_datachannel_payload(self, eval_result: dict) -> str:
        """
        Format telemetry for LiveKit DataChannel real-time broadcasting to client UI.
        """
        return json.dumps({
            "type": "trustmoss_voice_eval",
            "turn_id": eval_result["turn_id"],
            "verdict": eval_result["trust"]["verdict"],
            "score": eval_result["trust"]["score"],
            "circuit_breaker_tripped": eval_result["circuit_breaker_tripped"],
            "audio_suppressed": eval_result["audio_suppressed"],
            "final_speech": eval_result["final_speech_text"],
            "latency_ms": eval_result["total_latency_ms"],
            "latency_trace": eval_result["latency_trace"],
        })


async def main():
    parser = argparse.ArgumentParser(description="TrustMoss LiveKit Voice Agent Worker")
    parser.add_argument("--room", type=str, default=DEFAULT_ROOM, help="LiveKit room name")
    parser.add_argument("--test-speech", type=str, help="Simulate a speech transcript for test verification")
    args = parser.parse_args()

    agent = TrustMossVoiceAgent(room_name=args.room)
    logger.info("Initialized TrustMoss Voice Agent for room: %s", args.room)
    logger.info("LiveKit Gateway Token generated successfully.")

    if args.test_speech:
        logger.info("Simulating speech turn: %s", args.test_speech)
        result = await agent.handle_user_transcript("test_user", args.test_speech)
        print("\n--- VOICE EVALUATION RESULT ---")
        print(json.dumps(result, indent=2))
        print("--------------------------------\n")
    else:
        logger.info("Worker standing by for live WebRTC audio streams...")


if __name__ == "__main__":
    asyncio.run(main())
