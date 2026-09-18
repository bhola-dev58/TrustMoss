"""
test_secret_manager.py — Unit tests for the TrustMoss Secret Abstraction Layer (secret_manager.py).

Tests cover:
  - ENV provider (default — no external dependencies)
  - Vault provider (mocked hvac client)
  - AWS provider (mocked boto3 client)
  - get_required_secret() fail-fast behavior
  - Cache invalidation
  - Provider auto-detection logic
  - Graceful fallback when hvac/boto3 not installed
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))


class TestSecretProviderENV(unittest.TestCase):
    """Tests for the default ENV provider — no external dependencies."""

    def setUp(self):
        # Force ENV provider by clearing Vault/AWS env vars
        for key in ["VAULT_ADDR", "VAULT_TOKEN", "AWS_SECRET_NAME", "SECRET_PROVIDER"]:
            os.environ.pop(key, None)

    def _reimport_secrets(self):
        """Force re-import of secrets module to pick up new env vars."""
        if "secret_manager" in sys.modules:
            del sys.modules["secret_manager"]
        import secret_manager as s  # noqa: PLC0415
        return s

    def test_get_secret_returns_env_value(self):
        os.environ["GROQ_API_KEY"] = "env-test-groq-key"
        s = self._reimport_secrets()
        result = s.get_secret("GROQ_API_KEY")
        self.assertEqual(result, "env-test-groq-key")
        del os.environ["GROQ_API_KEY"]

    def test_get_secret_returns_default_if_missing(self):
        os.environ.pop("MISSING_KEY_XYZ", None)
        s = self._reimport_secrets()
        result = s.get_secret("MISSING_KEY_XYZ", "my-default")
        self.assertEqual(result, "my-default")

    def test_get_secret_returns_none_if_missing_no_default(self):
        os.environ.pop("MISSING_KEY_ABC", None)
        s = self._reimport_secrets()
        result = s.get_secret("MISSING_KEY_ABC")
        self.assertIsNone(result)

    def test_get_required_secret_raises_if_missing(self):
        os.environ.pop("REQUIRED_MISSING_KEY", None)
        s = self._reimport_secrets()
        with self.assertRaises(RuntimeError) as ctx:
            s.get_required_secret("REQUIRED_MISSING_KEY")
        self.assertIn("REQUIRED_MISSING_KEY", str(ctx.exception))
        self.assertIn("TrustMoss", str(ctx.exception))

    def test_get_required_secret_returns_value_if_present(self):
        os.environ["ENCRYPTION_KEY"] = "0" * 64
        s = self._reimport_secrets()
        result = s.get_required_secret("ENCRYPTION_KEY")
        self.assertEqual(result, "0" * 64)
        del os.environ["ENCRYPTION_KEY"]

    def test_active_provider_returns_env(self):
        s = self._reimport_secrets()
        from secret_manager import SecretProvider  # noqa: PLC0415
        self.assertEqual(s.active_provider(), SecretProvider.ENV)

    def test_explicit_secret_provider_env_var(self):
        os.environ["SECRET_PROVIDER"] = "env"
        s = self._reimport_secrets()
        from secret_manager import SecretProvider  # noqa: PLC0415
        self.assertEqual(s.active_provider(), SecretProvider.ENV)
        del os.environ["SECRET_PROVIDER"]


class TestSecretProviderAutoDetection(unittest.TestCase):
    """Tests for auto-detection of provider based on environment."""

    def _reimport_secrets(self):
        if "secret_manager" in sys.modules:
            del sys.modules["secret_manager"]
        import secret_manager as s  # noqa: PLC0415
        return s

    def setUp(self):
        for key in ["VAULT_ADDR", "VAULT_TOKEN", "AWS_SECRET_NAME", "SECRET_PROVIDER"]:
            os.environ.pop(key, None)

    def tearDown(self):
        for key in ["VAULT_ADDR", "VAULT_TOKEN", "AWS_SECRET_NAME", "SECRET_PROVIDER"]:
            os.environ.pop(key, None)

    def test_vault_provider_auto_detected_when_addr_and_token_set(self):
        os.environ["VAULT_ADDR"] = "http://localhost:8200"
        os.environ["VAULT_TOKEN"] = "test-vault-token"
        s = self._reimport_secrets()
        from secret_manager import SecretProvider  # noqa: PLC0415
        self.assertEqual(s.active_provider(), SecretProvider.VAULT)

    def test_aws_provider_auto_detected_when_secret_name_set(self):
        os.environ["AWS_SECRET_NAME"] = "trustmoss/production"
        s = self._reimport_secrets()
        from secret_manager import SecretProvider  # noqa: PLC0415
        self.assertEqual(s.active_provider(), SecretProvider.AWS)

    def test_env_provider_when_nothing_set(self):
        s = self._reimport_secrets()
        from secret_manager import SecretProvider  # noqa: PLC0415
        self.assertEqual(s.active_provider(), SecretProvider.ENV)

    def test_explicit_secret_provider_overrides_auto(self):
        # Even with Vault env vars set, explicit SECRET_PROVIDER=env should win
        os.environ["VAULT_ADDR"] = "http://localhost:8200"
        os.environ["VAULT_TOKEN"] = "test-vault-token"
        os.environ["SECRET_PROVIDER"] = "env"
        s = self._reimport_secrets()
        from secret_manager import SecretProvider  # noqa: PLC0415
        self.assertEqual(s.active_provider(), SecretProvider.ENV)


class TestSecretProviderVault(unittest.TestCase):
    """Tests for HashiCorp Vault provider using mocked hvac."""

    def setUp(self):
        for key in ["VAULT_ADDR", "VAULT_TOKEN", "AWS_SECRET_NAME", "SECRET_PROVIDER"]:
            os.environ.pop(key, None)
        os.environ["VAULT_ADDR"] = "http://localhost:8200"
        os.environ["VAULT_TOKEN"] = "test-dev-root-token"
        os.environ["SECRET_PROVIDER"] = "vault"

    def tearDown(self):
        for key in ["VAULT_ADDR", "VAULT_TOKEN", "SECRET_PROVIDER"]:
            os.environ.pop(key, None)
        if "secret_manager" in sys.modules:
            del sys.modules["secret_manager"]

    def _make_mock_hvac(self, secrets_data: dict) -> MagicMock:
        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": secrets_data}
        }
        mock_hvac.Client.return_value = mock_client
        return mock_hvac

    def test_vault_fetch_returns_correct_secret(self):
        mock_hvac = self._make_mock_hvac({"GROQ_API_KEY": "vault-groq-key-prod"})
        if "secret_manager" in sys.modules:
            del sys.modules["secret_manager"]
        with patch.dict("sys.modules", {"hvac": mock_hvac}):
            import secret_manager as s  # noqa: PLC0415
            # Clear the vault cache
            s.invalidate_cache()
            result = s.get_secret("GROQ_API_KEY")
            self.assertEqual(result, "vault-groq-key-prod")

    def test_vault_fallback_to_env_on_auth_failure(self):
        os.environ["GROQ_API_KEY"] = "env-fallback-key"
        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = False
        mock_hvac.Client.return_value = mock_client
        if "secret_manager" in sys.modules:
            del sys.modules["secret_manager"]
        with patch.dict("sys.modules", {"hvac": mock_hvac}):
            import secret_manager as s  # noqa: PLC0415
            s.invalidate_cache()
            result = s.get_secret("GROQ_API_KEY")
            self.assertEqual(result, "env-fallback-key")
        del os.environ["GROQ_API_KEY"]

    def test_vault_fallback_when_hvac_not_installed(self):
        os.environ["ENCRYPTION_KEY"] = "env-enc-key-fallback"
        if "secret_manager" in sys.modules:
            del sys.modules["secret_manager"]
        with patch.dict("sys.modules", {"hvac": None}):
            import secret_manager as s  # noqa: PLC0415
            s.invalidate_cache()
            result = s.get_secret("ENCRYPTION_KEY")
            self.assertEqual(result, "env-enc-key-fallback")
        del os.environ["ENCRYPTION_KEY"]


class TestSecretProviderAWS(unittest.TestCase):
    """Tests for AWS Secrets Manager provider using mocked boto3."""

    def setUp(self):
        for key in ["VAULT_ADDR", "VAULT_TOKEN", "AWS_SECRET_NAME", "SECRET_PROVIDER"]:
            os.environ.pop(key, None)
        os.environ["AWS_SECRET_NAME"] = "trustmoss/production"
        os.environ["SECRET_PROVIDER"] = "aws"
        if "secret_manager" in sys.modules:
            del sys.modules["secret_manager"]

    def tearDown(self):
        for key in ["AWS_SECRET_NAME", "SECRET_PROVIDER"]:
            os.environ.pop(key, None)
        if "secret_manager" in sys.modules:
            del sys.modules["secret_manager"]

    def test_aws_fetch_returns_correct_secret(self):
        mock_boto3 = MagicMock()
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            "SecretString": '{"GROQ_API_KEY": "aws-groq-key-prod", "ENCRYPTION_KEY": "aws-enc-key"}'
        }
        mock_boto3.client.return_value = mock_client

        mock_botocore = MagicMock()
        mock_botocore.exceptions.ClientError = Exception

        with patch.dict("sys.modules", {"boto3": mock_boto3, "botocore": mock_botocore,
                                         "botocore.exceptions": mock_botocore.exceptions}):
            import secret_manager as s  # noqa: PLC0415
            s.invalidate_cache()
            result = s.get_secret("GROQ_API_KEY")
            self.assertEqual(result, "aws-groq-key-prod")

    def test_aws_fallback_when_boto3_not_installed(self):
        os.environ["GROQ_API_KEY"] = "env-groq-fallback"
        with patch.dict("sys.modules", {"boto3": None}):
            import secret_manager as s  # noqa: PLC0415
            s.invalidate_cache()
            result = s.get_secret("GROQ_API_KEY")
            self.assertEqual(result, "env-groq-fallback")
        del os.environ["GROQ_API_KEY"]


class TestInvalidateCache(unittest.TestCase):
    """Test cache invalidation mechanism."""

    def test_invalidate_cache_clears_vault_and_aws_caches(self):
        if "secret_manager" in sys.modules:
            del sys.modules["secret_manager"]
        import secret_manager as s  # noqa: PLC0415
        s._vault_cache["GROQ_API_KEY"] = "cached-value"
        s._aws_cache["ENCRYPTION_KEY"] = "cached-enc"
        s.invalidate_cache()
        self.assertEqual(s._vault_cache, {})
        self.assertEqual(s._aws_cache, {})


if __name__ == "__main__":
    unittest.main()
