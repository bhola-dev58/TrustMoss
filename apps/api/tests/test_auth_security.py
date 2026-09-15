"""
test_auth_security.py — Unit and integration tests for OWASP API Security and JWT/OAuth2 RBAC.
"""

import os
import sys
import unittest
from datetime import timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

import auth
from apps.api.main import app as gateway_app


class TestJWTRBAC(unittest.TestCase):
    def test_create_and_decode_token(self):
        token = auth.create_access_token(identity="agent-007", role="agent")
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 20)

        payload = auth.decode_access_token(token)
        self.assertEqual(payload["sub"], "agent-007")
        self.assertEqual(payload["role"], "agent")
        self.assertEqual(payload["iss"], "trustmoss-gateway")

    def test_expired_token_rejected(self):
        expired_token = auth.create_access_token(
            identity="agent-old",
            role="agent",
            expires_delta=timedelta(seconds=-10),
        )
        with self.assertRaises(Exception) as ctx:
            auth.decode_access_token(expired_token)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("expired", ctx.exception.detail.lower())

    def test_invalid_signature_rejected(self):
        tampered_token = auth.create_access_token(identity="agent-legit", role="agent") + "badsignature"
        with self.assertRaises(Exception) as ctx:
            auth.decode_access_token(tampered_token)
        self.assertEqual(ctx.exception.status_code, 401)


class TestOWASPSecurityHeadersAndEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(gateway_app)

    def test_owasp_headers_present_on_health(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)

        headers = res.headers
        self.assertEqual(headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(headers.get("x-frame-options"), "DENY")
        self.assertIn("max-age", headers.get("strict-transport-security", ""))
        self.assertIn("default-src 'self'", headers.get("content-security-policy", ""))
        self.assertEqual(headers.get("x-xss-protection"), "1; mode=block")

    def test_auth_token_endpoint(self):
        res = self.client.post(
            "/api/auth/token",
            json={
                "client_id": "security-officer-1",
                "client_secret": "secret123",
                "role": "reviewer",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["role"], "reviewer")
        self.assertEqual(data["client_id"], "security-officer-1")

    def test_auth_me_with_bearer_token(self):
        token = auth.create_access_token(identity="compliance-lead", role="reviewer")
        res = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["identity"], "compliance-lead")
        self.assertEqual(data["role"], "reviewer")


if __name__ == "__main__":
    unittest.main()
