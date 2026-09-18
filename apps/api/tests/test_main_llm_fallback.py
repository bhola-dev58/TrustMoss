import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import main


class TestMainLLMFallback(unittest.IsolatedAsyncioTestCase):
    @patch("main.groq_client")
    async def test_call_llm_falls_back_to_context_on_groq_failure(self, mock_groq_client):
        mock_groq_client.chat.completions.create = AsyncMock(side_effect=RuntimeError("invalid api key"))
        context_chunks = [
            {"id": "c1", "text": "Password reset requires an email verification link.", "score": 0.92},
        ]

        answer = await main.call_llm("How do I reset my password?", context_chunks)

        self.assertEqual(answer, "Password reset requires an email verification link.")

    @patch("main.groq_client")
    async def test_call_llm_returns_safe_message_when_no_context(self, mock_groq_client):
        mock_groq_client.chat.completions.create = AsyncMock(side_effect=RuntimeError("invalid api key"))

        answer = await main.call_llm("How do I reset my password?", [])

        self.assertIn("Please try again shortly.", answer)


if __name__ == "__main__":
    unittest.main()
