"""
Unit and Integration Tests for AES-256-GCM Data-at-Rest Encryption (Task 4.2)
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from apps.api import crypto
from apps.api.main import app as gateway_app
from services.evaluation_service import app as eval_app, _hitl_queue, _encrypted_store


class TestCryptoAES256GCM(unittest.TestCase):
    def setUp(self):
        self.key = crypto.get_encryption_key()

    def test_key_is_256_bits(self):
        self.assertEqual(len(self.key), 32)  # 32 bytes = 256 bits

    def test_encrypt_decrypt_roundtrip(self):
        plaintext = "Patient John Doe medical diagnosis: hypertension Stage 2"
        token = crypto.encrypt(plaintext, key=self.key)
        self.assertTrue(crypto.is_encrypted(token))
        self.assertTrue(token.startswith(crypto.CIPHER_PREFIX))

        decrypted = crypto.decrypt(token, key=self.key)
        self.assertEqual(decrypted, plaintext)

    def test_nonce_uniqueness(self):
        # Two encryptions of the exact same plaintext MUST yield different ciphertexts
        # due to random 96-bit nonce generation per NIST SP 800-38D
        text = "Secret proprietary knowledge chunk"
        token1 = crypto.encrypt(text, key=self.key)
        token2 = crypto.encrypt(text, key=self.key)
        self.assertNotEqual(token1, token2)

        # Both decrypt back to original
        self.assertEqual(crypto.decrypt(token1, key=self.key), text)
        self.assertEqual(crypto.decrypt(token2, key=self.key), text)

    def test_tamper_proofing_integrity_failure(self):
        # Modifying even a single character in the ciphertext or authentication tag
        # MUST fail GCM tag verification and raise DecryptionError
        text = "Confidential prompt instruction"
        token = crypto.encrypt(text, key=self.key)

        # Tamper with the base64 payload
        prefix = crypto.CIPHER_PREFIX
        raw_b64 = token[len(prefix):]
        tampered_b64 = ("A" if raw_b64[10] != "A" else "B") + raw_b64[1:]
        tampered_token = f"{prefix}{tampered_b64}"

        with self.assertRaises(crypto.DecryptionError):
            crypto.decrypt(tampered_token, key=self.key)

    def test_additional_authenticated_data_aad(self):
        # AAD binds the ciphertext to an external context (e.g. record_id or tenant)
        text = "User prompt containing SSN 000-12-3456"
        aad_valid = "record-user-991"
        aad_invalid = "record-user-992"

        token = crypto.encrypt(text, aad=aad_valid, key=self.key)

        # Decrypt with matching AAD succeeds
        decrypted = crypto.decrypt(token, aad=aad_valid, key=self.key)
        self.assertEqual(decrypted, text)

        # Decrypt with mismatched AAD fails authentication
        with self.assertRaises(crypto.DecryptionError):
            crypto.decrypt(token, aad=aad_invalid, key=self.key)

    def test_field_level_dictionary_encryption(self):
        record = {
            "query_id": "q101",
            "public_metadata": "v1.4",
            "query": "What is the secret API key?",
            "answer": "The secret key is sk-prod-9988.",
            "status": "flagged",
        }
        sensitive_fields = ["query", "answer"]

        encrypted_record = crypto.encrypt_fields(record, sensitive_fields, aad="q101", key=self.key)

        # Public metadata stays untouched
        self.assertEqual(encrypted_record["query_id"], "q101")
        self.assertEqual(encrypted_record["public_metadata"], "v1.4")
        self.assertEqual(encrypted_record["status"], "flagged")

        # Sensitive fields are encrypted with prefix
        self.assertTrue(crypto.is_encrypted(encrypted_record["query"]))
        self.assertTrue(crypto.is_encrypted(encrypted_record["answer"]))
        self.assertNotIn("secret key", encrypted_record["answer"])

        # Decrypt fields restores original values
        decrypted_record = crypto.decrypt_fields(encrypted_record, sensitive_fields, aad="q101", key=self.key)
        self.assertEqual(decrypted_record["query"], record["query"])
        self.assertEqual(decrypted_record["answer"], record["answer"])


class TestEncryptedStorePersistence(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.store_file = Path(self.temp_dir) / "test_hitl.enc.json"
        self.store = crypto.EncryptedStore(
            filepath=self.store_file,
            sensitive_fields=["query", "answer", "context_chunks"],
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_data_at_rest_is_encrypted_on_disk(self):
        sample_items = [
            {
                "query_id": "hitl-01",
                "query": "Is customer PIN 9876 valid?",
                "answer": "Yes, PIN 9876 is verified.",
                "context_chunks": [{"text": "Customer PIN verification policy"}],
                "status": "pending_review",
            }
        ]

        self.store.save_records(sample_items)
        self.assertTrue(self.store_file.exists())

        # Inspect raw disk file — verify plaintext NEVER appears on disk
        with open(self.store_file, "r", encoding="utf-8") as f:
            raw_content = f.read()

        self.assertNotIn("9876", raw_content)
        self.assertNotIn("Customer PIN verification policy", raw_content)
        self.assertIn("$aes256gcm$", raw_content)
        self.assertIn("AES-256-GCM", raw_content)

        # Load back via store and verify full decryption
        loaded_items = self.store.load_records()
        self.assertEqual(len(loaded_items), 1)
        self.assertEqual(loaded_items[0]["query"], "Is customer PIN 9876 valid?")
        self.assertEqual(loaded_items[0]["answer"], "Yes, PIN 9876 is verified.")

        # Verify load_raw_encrypted API returns encrypted envelope
        raw_env = self.store.load_raw_encrypted()
        self.assertEqual(raw_env["algorithm"], "AES-256-GCM")
        self.assertEqual(raw_env["key_bits"], 256)
        self.assertEqual(raw_env["record_count"], 1)


class TestEvaluationServiceEncryptionIntegration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(eval_app)
        self.temp_dir = tempfile.mkdtemp()
        self.store_file = Path(self.temp_dir) / "eval_hitl.enc.json"
        # Temporarily redirect store to isolated temp file
        _encrypted_store.filepath = self.store_file
        _hitl_queue.clear()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_evaluate_fail_persists_encrypted_record_at_rest(self):
        req = {
            "query": "Confidential query about company acquisitions",
            "answer": "Acquisition of competitor for $500M planned next month.",
            "context_chunks": [],
            "top_score": 0.20,
            "pii_passed": True,
        }

        res = self.client.post("/evaluate", json=req)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["verdict"], "FAIL")
        self.assertTrue(data["requires_hitl"])

        # Check raw encrypted endpoint — proves ciphertext on disk
        raw_res = self.client.get("/hitl/queue/raw")
        self.assertEqual(raw_res.status_code, 200)
        raw_data = raw_res.json()
        self.assertEqual(raw_data["algorithm"], "AES-256-GCM")
        self.assertGreater(raw_data["record_count"], 0)
        raw_rec = raw_data["records"][0]
        self.assertTrue(raw_rec["query"].startswith("$aes256gcm$"))
        self.assertTrue(raw_rec["answer"].startswith("$aes256gcm$"))

        # Check authenticated reviewer queue endpoint — decrypted for review
        queue_res = self.client.get("/hitl/queue")
        self.assertEqual(queue_res.status_code, 200)
        queue_data = queue_res.json()
        self.assertGreater(queue_data["total_flagged"], 0)
        item = queue_data["items"][0]
        self.assertEqual(item["query"], req["query"])
        self.assertEqual(item["answer"], req["answer"])

    def test_health_reports_encryption_posture(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("encryption", data)
        self.assertEqual(data["encryption"]["data_at_rest"], "AES-256-GCM")
        self.assertEqual(data["encryption"]["key_size_bits"], 256)


class TestGatewayEncryptionEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(gateway_app)

    def test_gateway_health_reports_aes256gcm(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        sec = data["security"]
        self.assertEqual(sec["data_at_rest_encryption"], "AES-256-GCM")
        self.assertEqual(sec["key_size_bits"], 256)

    def test_gateway_security_encryption_status(self):
        res = self.client.get("/api/security/encryption")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["algorithm"], "AES-256-GCM")
        self.assertEqual(data["key_size_bits"], 256)
        self.assertEqual(data["nonce_length_bytes"], 12)
        self.assertEqual(data["auth_tag_length_bytes"], 16)
        self.assertTrue(data["tamper_proof"])
