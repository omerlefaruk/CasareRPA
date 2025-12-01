"""Tests for webhook authentication utilities."""

import hmac
import hashlib
import time
import pytest

from casare_rpa.triggers.webhook_auth import (
    WebhookAuthenticator,
    verify_webhook_auth,
)


class TestNoAuth:
    """Tests for no authentication mode."""

    def test_no_auth_always_passes(self):
        """Test that no auth mode always succeeds."""
        config = {"auth_type": "none"}
        headers = {}
        body = b'{"test": "data"}'

        is_valid, error = verify_webhook_auth(config, headers, body)

        assert is_valid is True
        assert error is None

    def test_missing_auth_type_defaults_to_none(self):
        """Test that missing auth_type defaults to none."""
        config = {}
        headers = {}
        body = b"{}"

        is_valid, error = verify_webhook_auth(config, headers, body)

        assert is_valid is True


class TestApiKeyAuth:
    """Tests for API key authentication."""

    def test_valid_api_key_in_x_api_key_header(self):
        """Test valid API key in X-API-Key header."""
        config = {"auth_type": "api_key", "secret": "my-secret-key"}
        headers = {"X-API-Key": "my-secret-key"}
        body = b"{}"

        is_valid, error = verify_webhook_auth(config, headers, body)

        assert is_valid is True
        assert error is None

    def test_valid_api_key_in_x_webhook_secret_header(self):
        """Test valid API key in X-Webhook-Secret header."""
        config = {"auth_type": "api_key", "secret": "my-secret-key"}
        headers = {"X-Webhook-Secret": "my-secret-key"}
        body = b"{}"

        is_valid, error = verify_webhook_auth(config, headers, body)

        assert is_valid is True

    def test_invalid_api_key(self):
        """Test invalid API key returns error."""
        config = {"auth_type": "api_key", "secret": "correct-key"}
        headers = {"X-API-Key": "wrong-key"}
        body = b"{}"

        is_valid, error = verify_webhook_auth(config, headers, body)

        assert is_valid is False
        assert "Invalid API key" in error

    def test_missing_api_key_header(self):
        """Test missing API key header returns error."""
        config = {"auth_type": "api_key", "secret": "my-secret-key"}
        headers = {}
        body = b"{}"

        is_valid, error = verify_webhook_auth(config, headers, body)

        assert is_valid is False
        assert "not provided" in error


class TestBearerAuth:
    """Tests for Bearer token authentication."""

    def test_valid_bearer_token(self):
        """Test valid Bearer token."""
        config = {"auth_type": "bearer", "secret": "my-token-123"}
        headers = {"Authorization": "Bearer my-token-123"}
        body = b"{}"

        is_valid, error = verify_webhook_auth(config, headers, body)

        assert is_valid is True
        assert error is None

    def test_invalid_bearer_token(self):
        """Test invalid Bearer token."""
        config = {"auth_type": "bearer", "secret": "correct-token"}
        headers = {"Authorization": "Bearer wrong-token"}
        body = b"{}"

        is_valid, error = verify_webhook_auth(config, headers, body)

        assert is_valid is False
        assert "Invalid bearer token" in error

    def test_missing_authorization_header(self):
        """Test missing Authorization header."""
        config = {"auth_type": "bearer", "secret": "my-token"}
        headers = {}
        body = b"{}"

        is_valid, error = verify_webhook_auth(config, headers, body)

        assert is_valid is False
        assert "not provided" in error

    def test_non_bearer_auth_header(self):
        """Test non-Bearer Authorization header."""
        config = {"auth_type": "bearer", "secret": "my-token"}
        headers = {"Authorization": "Basic dXNlcjpwYXNz"}
        body = b"{}"

        is_valid, error = verify_webhook_auth(config, headers, body)

        assert is_valid is False


class TestHmacSha256Auth:
    """Tests for HMAC-SHA256 authentication."""

    def test_valid_hmac_sha256_github_format(self):
        """Test valid HMAC-SHA256 signature in GitHub format."""
        secret = "webhook-secret-key"
        body = b'{"event": "push", "ref": "refs/heads/main"}'
        signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

        config = {
            "auth_type": "hmac_sha256",
            "secret": secret,
            "hmac_provider": "github",
        }
        headers = {"X-Hub-Signature-256": f"sha256={signature}"}

        is_valid, error = verify_webhook_auth(config, headers, body)

        assert is_valid is True
        assert error is None

    def test_valid_hmac_sha256_generic_format(self):
        """Test valid HMAC-SHA256 signature in generic format."""
        secret = "my-secret"
        body = b'{"data": "test"}'
        signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

        config = {
            "auth_type": "hmac_sha256",
            "secret": secret,
        }
        headers = {"X-Webhook-Signature": f"sha256={signature}"}

        is_valid, error = verify_webhook_auth(config, headers, body)

        assert is_valid is True

    def test_invalid_hmac_sha256_signature(self):
        """Test invalid HMAC-SHA256 signature."""
        config = {
            "auth_type": "hmac_sha256",
            "secret": "correct-secret",
        }
        headers = {"X-Webhook-Signature": "sha256=invalid-signature"}
        body = b'{"test": "data"}'

        is_valid, error = verify_webhook_auth(config, headers, body)

        assert is_valid is False
        assert "verification failed" in error.lower()

    def test_hmac_sha256_tampered_body(self):
        """Test that tampered body is detected."""
        secret = "webhook-secret"
        original_body = b'{"amount": 100}'
        signature = hmac.new(secret.encode(), original_body, hashlib.sha256).hexdigest()

        config = {
            "auth_type": "hmac_sha256",
            "secret": secret,
        }
        headers = {"X-Webhook-Signature": f"sha256={signature}"}
        tampered_body = b'{"amount": 10000}'  # Tampered!

        is_valid, error = verify_webhook_auth(config, headers, tampered_body)

        assert is_valid is False

    def test_missing_signature_header(self):
        """Test missing signature header."""
        config = {
            "auth_type": "hmac_sha256",
            "secret": "my-secret",
        }
        headers = {}
        body = b'{"test": "data"}'

        is_valid, error = verify_webhook_auth(config, headers, body)

        assert is_valid is False
        assert "header not found" in error.lower() or "not found" in error.lower()


class TestHmacSha1Auth:
    """Tests for HMAC-SHA1 authentication (GitHub legacy format)."""

    def test_valid_hmac_sha1(self):
        """Test valid HMAC-SHA1 signature."""
        secret = "webhook-secret"
        body = b'{"action": "opened"}'
        signature = hmac.new(secret.encode(), body, hashlib.sha1).hexdigest()

        config = {
            "auth_type": "hmac_sha1",
            "secret": secret,
        }
        headers = {"X-Hub-Signature": f"sha1={signature}"}

        is_valid, error = verify_webhook_auth(config, headers, body)

        assert is_valid is True


class TestSignatureGeneration:
    """Tests for signature generation utility."""

    def test_generate_github_format(self):
        """Test generating signature in GitHub format."""
        secret = "test-secret"
        body = b'{"test": "data"}'

        signature = WebhookAuthenticator.generate_signature(
            secret, body, algorithm="hmac_sha256", format="github"
        )

        assert signature.startswith("sha256=")
        # Verify the generated signature
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        assert signature == f"sha256={expected}"

    def test_generate_stripe_format(self):
        """Test generating signature in Stripe format."""
        secret = "test-secret"
        body = b'{"test": "data"}'

        signature = WebhookAuthenticator.generate_signature(
            secret, body, algorithm="hmac_sha256", format="stripe"
        )

        assert signature.startswith("t=")
        assert ",v1=" in signature

    def test_generate_plain_format(self):
        """Test generating plain signature."""
        secret = "test-secret"
        body = b'{"test": "data"}'

        signature = WebhookAuthenticator.generate_signature(
            secret, body, algorithm="hmac_sha256", format="plain"
        )

        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        assert signature == expected


class TestMissingSecret:
    """Tests for missing secret scenarios."""

    def test_missing_secret_returns_error(self):
        """Test that missing secret returns error for auth types requiring it."""
        config = {"auth_type": "api_key"}  # No secret
        headers = {"X-API-Key": "some-key"}
        body = b"{}"

        is_valid, error = verify_webhook_auth(config, headers, body)

        assert is_valid is False
        assert "not configured" in error.lower()


class TestCaseInsensitiveHeaders:
    """Tests for case-insensitive header handling."""

    def test_lowercase_headers_work(self):
        """Test that lowercase headers are handled correctly."""
        config = {"auth_type": "api_key", "secret": "my-key"}
        headers = {"x-api-key": "my-key"}  # lowercase
        body = b"{}"

        is_valid, error = verify_webhook_auth(config, headers, body)

        assert is_valid is True

    def test_mixed_case_headers_work(self):
        """Test that mixed case headers are handled correctly."""
        config = {"auth_type": "bearer", "secret": "my-token"}
        headers = {"AUTHORIZATION": "Bearer my-token"}  # uppercase
        body = b"{}"

        is_valid, error = verify_webhook_auth(config, headers, body)

        assert is_valid is True


class TestCustomHmacHeader:
    """Tests for custom HMAC header configuration."""

    def test_custom_hmac_header_name(self):
        """Test using custom header name for HMAC signature."""
        secret = "custom-secret"
        body = b'{"event": "test"}'
        signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

        config = {
            "auth_type": "hmac_sha256",
            "secret": secret,
            "hmac_header": "X-Custom-Signature",
        }
        headers = {"X-Custom-Signature": f"sha256={signature}"}

        is_valid, error = verify_webhook_auth(config, headers, body)

        assert is_valid is True


class TestEmptyBody:
    """Tests for empty body handling."""

    def test_hmac_with_empty_body(self):
        """Test HMAC verification with empty body."""
        secret = "my-secret"
        body = b""
        signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

        config = {
            "auth_type": "hmac_sha256",
            "secret": secret,
        }
        headers = {"X-Webhook-Signature": f"sha256={signature}"}

        is_valid, error = verify_webhook_auth(config, headers, body)

        assert is_valid is True


class TestUnknownAuthType:
    """Tests for unknown auth type handling."""

    def test_unknown_auth_type_returns_error(self):
        """Test that unknown auth type returns error."""
        config = {"auth_type": "oauth2", "secret": "key"}  # Not supported
        headers = {}
        body = b"{}"

        is_valid, error = verify_webhook_auth(config, headers, body)

        assert is_valid is False
        assert "Unknown auth_type" in error
