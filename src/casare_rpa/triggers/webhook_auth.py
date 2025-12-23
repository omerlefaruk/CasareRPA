"""
CasareRPA - Webhook Authentication Utilities

Provides secure authentication methods for webhook triggers including
HMAC signature verification (compatible with GitHub, Stripe, etc.)
"""

import hashlib
import hmac
import time
from typing import Any

from loguru import logger


class WebhookAuthenticator:
    """
    Authenticator for webhook requests.

    Supports multiple authentication methods:
    - api_key: Simple API key in header
    - bearer: Bearer token authentication
    - hmac_sha256: HMAC-SHA256 signature verification
    - hmac_sha1: HMAC-SHA1 signature verification (GitHub compatible)

    HMAC signature verification prevents replay attacks and ensures
    payload integrity by signing the request body with a shared secret.
    """

    # Supported signature algorithms
    HMAC_ALGORITHMS = {
        "hmac_sha256": hashlib.sha256,
        "hmac_sha1": hashlib.sha1,
        "hmac_sha384": hashlib.sha384,
        "hmac_sha512": hashlib.sha512,
    }

    # Default header names for different providers
    SIGNATURE_HEADERS = {
        "github": "X-Hub-Signature-256",
        "github_legacy": "X-Hub-Signature",
        "stripe": "Stripe-Signature",
        "generic": "X-Webhook-Signature",
    }

    @classmethod
    def verify_request(
        cls,
        config: dict[str, Any],
        headers: dict[str, str],
        body: bytes,
    ) -> tuple[bool, str | None]:
        """
        Verify webhook request authentication.

        Args:
            config: Trigger configuration with auth settings
            headers: Request headers (case-insensitive dict recommended)
            body: Raw request body bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        auth_type = config.get("auth_type", "none")
        secret = config.get("secret", "")

        if auth_type == "none":
            return True, None

        if not secret:
            return False, "Secret not configured"

        # Normalize headers to case-insensitive
        normalized_headers = {k.lower(): v for k, v in headers.items()}

        if auth_type == "api_key":
            return cls._verify_api_key(secret, normalized_headers)

        elif auth_type == "bearer":
            return cls._verify_bearer(secret, normalized_headers)

        elif auth_type.startswith("hmac_"):
            return cls._verify_hmac(auth_type, secret, normalized_headers, body, config)

        else:
            return False, f"Unknown auth_type: {auth_type}"

    @classmethod
    def _verify_api_key(cls, secret: str, headers: dict[str, str]) -> tuple[bool, str | None]:
        """Verify API key authentication."""
        # Check common API key header locations
        api_key = (
            headers.get("x-api-key") or headers.get("x-webhook-secret") or headers.get("api-key")
        )

        if not api_key:
            return False, "API key not provided"

        if not hmac.compare_digest(api_key, secret):
            return False, "Invalid API key"

        return True, None

    @classmethod
    def _verify_bearer(cls, secret: str, headers: dict[str, str]) -> tuple[bool, str | None]:
        """Verify Bearer token authentication."""
        auth_header = headers.get("authorization", "")

        if not auth_header.lower().startswith("bearer "):
            return False, "Bearer token not provided"

        token = auth_header[7:].strip()

        if not hmac.compare_digest(token, secret):
            return False, "Invalid bearer token"

        return True, None

    @classmethod
    def _verify_hmac(
        cls,
        auth_type: str,
        secret: str,
        headers: dict[str, str],
        body: bytes,
        config: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """
        Verify HMAC signature.

        Supports multiple providers and formats:
        - GitHub: sha256=<signature> or sha1=<signature>
        - Stripe: t=<timestamp>,v1=<signature>
        - Generic: <algorithm>=<signature> or just <signature>
        """
        # Get hash algorithm
        algorithm = cls.HMAC_ALGORITHMS.get(auth_type)
        if not algorithm:
            return False, f"Unsupported HMAC algorithm: {auth_type}"

        # Get signature header name
        provider = config.get("hmac_provider", "generic")
        header_name = config.get(
            "hmac_header", cls.SIGNATURE_HEADERS.get(provider, "x-webhook-signature")
        )
        signature_header = headers.get(header_name.lower(), "")

        if not signature_header:
            # Try common header names
            for name in [
                "x-webhook-signature",
                "x-hub-signature-256",
                "x-hub-signature",
                "x-signature",
            ]:
                signature_header = headers.get(name, "")
                if signature_header:
                    break

        if not signature_header:
            return False, "Signature header not found"

        # Parse signature based on format
        expected_signature = cls._parse_signature(signature_header, auth_type, config)
        if not expected_signature:
            return False, "Could not parse signature"

        # Calculate expected signature
        key = secret.encode("utf-8")
        calculated = hmac.new(key, body, algorithm).hexdigest()

        # Verify signature
        if not hmac.compare_digest(calculated.lower(), expected_signature.lower()):
            logger.warning(
                f"HMAC verification failed. "
                f"Expected: {expected_signature[:20]}..., "
                f"Got: {calculated[:20]}..."
            )
            return False, "Signature verification failed"

        # Optional timestamp verification (anti-replay)
        tolerance = config.get("hmac_timestamp_tolerance", 300)  # 5 minutes default
        if tolerance > 0 and provider == "stripe":
            timestamp_str = cls._extract_stripe_timestamp(signature_header)
            if timestamp_str:
                try:
                    timestamp = int(timestamp_str)
                    age = abs(time.time() - timestamp)
                    if age > tolerance:
                        return False, f"Request too old ({int(age)}s)"
                except ValueError:
                    pass

        return True, None

    @classmethod
    def _parse_signature(
        cls, signature_header: str, auth_type: str, config: dict[str, Any]
    ) -> str | None:
        """
        Parse signature from various header formats.

        Formats:
        - sha256=abc123 (GitHub)
        - t=1234,v1=abc123 (Stripe)
        - abc123 (plain hex)
        """
        signature_header = signature_header.strip()

        # GitHub format: sha256=<signature>
        if "=" in signature_header and "," not in signature_header:
            parts = signature_header.split("=", 1)
            if len(parts) == 2:
                return parts[1]

        # Stripe format: t=<timestamp>,v1=<signature>
        if "," in signature_header:
            for part in signature_header.split(","):
                if part.strip().startswith("v1="):
                    return part.strip()[3:]

        # Plain signature
        return signature_header

    @classmethod
    def _extract_stripe_timestamp(cls, signature_header: str) -> str | None:
        """Extract timestamp from Stripe signature header."""
        for part in signature_header.split(","):
            if part.strip().startswith("t="):
                return part.strip()[2:]
        return None

    @classmethod
    def generate_signature(
        cls,
        secret: str,
        body: bytes,
        algorithm: str = "hmac_sha256",
        format: str = "github",
    ) -> str:
        """
        Generate signature for testing/debugging.

        Args:
            secret: Shared secret
            body: Request body
            algorithm: HMAC algorithm to use
            format: Output format (github, stripe, plain)

        Returns:
            Signature string in requested format
        """
        hash_func = cls.HMAC_ALGORITHMS.get(algorithm, hashlib.sha256)
        signature = hmac.new(secret.encode("utf-8"), body, hash_func).hexdigest()

        if format == "github":
            algo_name = algorithm.replace("hmac_", "")
            return f"{algo_name}={signature}"
        elif format == "stripe":
            timestamp = int(time.time())
            return f"t={timestamp},v1={signature}"
        else:
            return signature


def verify_webhook_auth(
    config: dict[str, Any],
    headers: dict[str, str],
    body: bytes,
) -> tuple[bool, str | None]:
    """
    Convenience function for webhook authentication.

    Args:
        config: Trigger configuration
        headers: Request headers
        body: Raw request body

    Returns:
        Tuple of (is_valid, error_message)
    """
    return WebhookAuthenticator.verify_request(config, headers, body)
