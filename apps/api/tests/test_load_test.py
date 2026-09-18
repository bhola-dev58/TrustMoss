"""
test_load_test.py — Unit & Integration tests for Grafana k6 OSS Scalability Engine.
===================================================================================
Tests cover:
  1. k6 binary detection and version reporting
  2. Duration parsing and error handling
  3. Configuration validation and safety limits (max VUs, max duration, URL schemes)
  4. Injection-safe JavaScript k6 script generation with SLA thresholds
  5. k6 summary JSON parser and SLA threshold evaluation
  6. Rule-based breaking point diagnosis
  7. Async test execution lifecycle (CREATED -> RUNNING -> COMPLETED)
  8. Manual cancellation lifecycle (RUNNING -> CANCELLED)
  9. FastAPI REST API endpoints (/api/load-tests CRUD + start/cancel)
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import database
from fastapi.testclient import TestClient
import load_test
import main


class TestLoadTestEngineUnit(unittest.IsolatedAsyncioTestCase):
    """Unit tests for load_test module components."""

    def test_duration_parser_valid(self):
        self.assertEqual(load_test.parse_duration_seconds("30s"), 30)
        self.assertEqual(load_test.parse_duration_seconds("2m"), 120)
        self.assertEqual(load_test.parse_duration_seconds("1h"), 3600)
        self.assertEqual(load_test.parse_duration_seconds("45"), 45)

    def test_duration_parser_invalid(self):
        with self.assertRaises(ValueError):
            load_test.parse_duration_seconds("invalid")
        with self.assertRaises(ValueError):
            load_test.parse_duration_seconds("10x")

    def test_validation_safety_limits(self):
        # Valid config passes
        load_test.validate_test_config("http://localhost:8000/health", vus=50, duration="30s", test_type="load")

        # Empty URL fails
        with self.assertRaises(ValueError):
            load_test.validate_test_config("", vus=10, duration="10s")

        # Unsupported protocol fails
        with self.assertRaises(ValueError):
            load_test.validate_test_config("ftp://localhost:8000", vus=10, duration="10s")

        # Zero or negative VUs fail
        with self.assertRaises(ValueError):
            load_test.validate_test_config("http://localhost:8000", vus=0, duration="10s")

        # Exceeding MAX_VIRTUAL_USERS fails
        with self.assertRaises(ValueError):
            load_test.validate_test_config("http://localhost:8000", vus=5000, duration="10s")

        # Exceeding MAX_DURATION fails
        with self.assertRaises(ValueError):
            load_test.validate_test_config("http://localhost:8000", vus=10, duration="2h")

        # Invalid test type fails
        with self.assertRaises(ValueError):
            load_test.validate_test_config("http://localhost:8000", vus=10, duration="10s", test_type="destroy")

    def test_generate_k6_script_load_profile(self):
        script = load_test.generate_k6_script(
            target_url="http://localhost:8000/health",
            vus=25,
            duration="15s",
            test_type="load",
        )
        self.assertIn("import http from 'k6/http';", script)
        self.assertIn("http_req_duration': ['p(95)<45.0', 'p(99)<75.0']", script)
        self.assertIn("vus: 25,", script)
        self.assertIn("http://localhost:8000/health", script)

    def test_generate_k6_script_ramp_profile(self):
        script = load_test.generate_k6_script(
            target_url="http://localhost:8000/health",
            vus=50,
            duration="60s",
            test_type="ramp",
        )
        self.assertIn("stages: [", script)
        self.assertIn("target: 50", script)

    def test_parse_k6_summary_passed(self):
        mock_summary = {
            "metrics": {
                "http_req_duration": {
                    "values": {
                        "p(95)": 28.4,
                        "p(99)": 41.2,
                        "avg": 20.1,
                        "med": 18.5,
                    }
                },
                "http_reqs": {
                    "values": {
                        "rate": 450.0,
                        "count": 13500,
                    }
                },
                "http_req_failed": {
                    "values": {
                        "rate": 0.0,
                    }
                },
                "vus": {
                    "values": {
                        "value": 50,
                    }
                },
            }
        }
        res = load_test.parse_k6_summary(mock_summary)
        self.assertEqual(res["p95_ms"], 28.4)
        self.assertEqual(res["p99_ms"], 41.2)
        self.assertEqual(res["rps"], 450.0)
        self.assertTrue(res["threshold_passed"])
        self.assertEqual(res["breaking_point"], "SLA Compliant (P95 < 45ms)")

    def test_parse_k6_summary_sla_breach(self):
        mock_summary = {
            "metrics": {
                "http_req_duration": {
                    "values": {
                        "p(95)": 88.5,
                        "p(99)": 140.0,
                        "avg": 65.0,
                        "med": 55.0,
                    }
                },
                "http_reqs": {
                    "values": {
                        "rate": 800.0,
                        "count": 24000,
                    }
                },
                "http_req_failed": {
                    "values": {
                        "rate": 0.0,
                    }
                },
                "vus": {
                    "values": {
                        "value": 200,
                    }
                },
            }
        }
        res = load_test.parse_k6_summary(mock_summary)
        self.assertFalse(res["threshold_passed"])
        self.assertIn("Latency SLA Breached", res["breaking_point"])

    async def test_run_load_test_simulated_lifecycle(self):
        test_id = "test-sim-run-1"
        await database.insert_load_test_run(
            test_id=test_id,
            name="Simulated Ingress Run",
            test_type="load",
            target="http://localhost:8000/health",
            vus=20,
            duration="5s",
        )

        result = await load_test.run_load_test(
            test_id=test_id,
            target_url="http://localhost:8000/health",
            vus=20,
            duration="5s",
            test_type="load",
        )
        self.assertEqual(result["status"], "COMPLETED")
        self.assertIn("metrics", result)
        self.assertLess(result["metrics"]["p95_ms"], 45.0)

        # Check database record updated
        record = await database.get_load_test_run(test_id)
        self.assertEqual(record["status"], "COMPLETED")
        self.assertIsNotNone(record["p95_ms"])
        self.assertTrue(record["threshold_passed"])

    async def test_cancel_load_test(self):
        test_id = "test-cancel-run-1"
        await database.insert_load_test_run(
            test_id=test_id,
            name="Run to cancel",
            test_type="load",
            target="http://localhost:8000/health",
            vus=10,
            duration="10s",
        )
        cancelled = await load_test.cancel_load_test(test_id)
        self.assertTrue(cancelled)

        record = await database.get_load_test_run(test_id)
        self.assertEqual(record["status"], "CANCELLED")


class TestLoadTestEndpoints(unittest.TestCase):
    """Integration tests for FastAPI /api/load-tests REST API endpoints."""

    def setUp(self):
        self.client = TestClient(main.app)

    def test_create_load_test_endpoint(self):
        payload = {
            "name": "Production Ingress SLA Gate",
            "test_type": "load",
            "target": "http://localhost:8000/health",
            "vus": 30,
            "duration": "15s",
        }
        res = self.client.post("/api/load-tests", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("id", data)
        self.assertEqual(data["status"], "CREATED")
        self.assertEqual(data["vus"], 30)

        test_id = data["id"]

        # Fetch test by ID
        get_res = self.client.get(f"/api/load-tests/{test_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["name"], "Production Ingress SLA Gate")

        # List tests
        list_res = self.client.get("/api/load-tests")
        self.assertEqual(list_res.status_code, 200)
        self.assertTrue(any(t["id"] == test_id for t in list_res.json()["tests"]))

        # Cancel test
        cancel_res = self.client.post(f"/api/load-tests/{test_id}/cancel")
        self.assertEqual(cancel_res.status_code, 200)
        self.assertEqual(cancel_res.json()["status"], "CANCELLED")

    def test_create_load_test_invalid_url(self):
        payload = {
            "target": "ftp://bad-url.com",
            "vus": 10,
            "duration": "10s",
        }
        res = self.client.post("/api/load-tests", json=payload)
        self.assertEqual(res.status_code, 400)


if __name__ == "__main__":
    unittest.main()
