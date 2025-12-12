"""
CasareRPA - TOTP Manager for Multi-Factor Authentication.

Provides TOTP (Time-based One-Time Password) functionality for MFA:
- Secret generation
- QR code generation for authenticator apps
- Code verification with valid window

Usage:
    from casare_rpa.infrastructure.auth import TOTPManager

    manager = TOTPManager()

    # Generate secret for new user
    secret = manager.generate_secret()
    uri = manager.get_provisioning_uri(secret, "user@example.com")
    qr_bytes = manager.generate_qr_code(uri)

    # Display QR code to user for authenticator app setup

    # Verify code during login
    if manager.verify_code(secret, "123456"):
        print("MFA verified")
"""

import base64
import hashlib
import hmac
import io
import secrets
import struct
import time
from typing import Optional

from loguru import logger


# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_ISSUER = "CasareRPA"
TOTP_DIGITS = 6
TOTP_INTERVAL = 30  # seconds
TOTP_VALID_WINDOW = 1  # Allow 1 interval before/after
SECRET_BYTES = 20  # 160 bits for TOTP


# =============================================================================
# EXCEPTIONS
# =============================================================================


class TOTPError(Exception):
    """Base exception for TOTP operations."""

    pass


class InvalidSecretError(TOTPError):
    """Raised when secret is invalid."""

    pass


class InvalidCodeError(TOTPError):
    """Raised when verification code is invalid."""

    pass


# =============================================================================
# TOTP MANAGER
# =============================================================================


class TOTPManager:
    """
    Manager for TOTP-based multi-factor authentication.

    Implements RFC 6238 TOTP without external dependencies.
    Compatible with Google Authenticator, Authy, etc.
    """

    def __init__(
        self,
        issuer: str = DEFAULT_ISSUER,
        digits: int = TOTP_DIGITS,
        interval: int = TOTP_INTERVAL,
        valid_window: int = TOTP_VALID_WINDOW,
    ) -> None:
        """
        Initialize TOTP manager.

        Args:
            issuer: Issuer name shown in authenticator apps
            digits: Number of digits in TOTP code (default 6)
            interval: Time interval in seconds (default 30)
            valid_window: Number of intervals before/after to accept
        """
        self._issuer = issuer
        self._digits = digits
        self._interval = interval
        self._valid_window = valid_window

    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret.

        Returns:
            Base32-encoded secret string (32 chars)
        """
        random_bytes = secrets.token_bytes(SECRET_BYTES)
        secret = base64.b32encode(random_bytes).decode("utf-8")
        logger.debug("Generated new TOTP secret")
        return secret

    def get_provisioning_uri(
        self,
        secret: str,
        user_email: str,
        issuer: Optional[str] = None,
    ) -> str:
        """
        Generate otpauth:// URI for authenticator app setup.

        Args:
            secret: Base32-encoded secret
            user_email: User's email address
            issuer: Override default issuer name

        Returns:
            otpauth:// URI string
        """
        if not secret:
            raise InvalidSecretError("Secret cannot be empty")
        if not user_email:
            raise TOTPError("User email cannot be empty")

        issuer_name = issuer or self._issuer

        # URL encode the issuer and email
        import urllib.parse

        encoded_issuer = urllib.parse.quote(issuer_name, safe="")
        encoded_email = urllib.parse.quote(user_email, safe="")

        # Format: otpauth://totp/Issuer:user@email?secret=XXX&issuer=XXX
        uri = (
            f"otpauth://totp/{encoded_issuer}:{encoded_email}"
            f"?secret={secret}"
            f"&issuer={encoded_issuer}"
            f"&algorithm=SHA1"
            f"&digits={self._digits}"
            f"&period={self._interval}"
        )
        return uri

    def generate_qr_code(self, uri: str, size: int = 200) -> bytes:
        """
        Generate QR code image for the provisioning URI.

        Args:
            uri: otpauth:// URI string
            size: QR code image size in pixels

        Returns:
            PNG image bytes

        Note:
            Requires qrcode package. Returns placeholder if unavailable.
        """
        try:
            import qrcode
            from qrcode.image.pure import PyPNGImage

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=2,
            )
            qr.add_data(uri)
            qr.make(fit=True)

            img = qr.make_image(image_factory=PyPNGImage)
            buffer = io.BytesIO()
            img.save(buffer)
            return buffer.getvalue()

        except ImportError:
            logger.warning("qrcode package not installed, QR generation unavailable")
            return self._generate_placeholder_png(size)
        except Exception as e:
            logger.error(f"Failed to generate QR code: {e}")
            raise TOTPError(f"QR code generation failed: {e}") from e

    def verify_code(
        self,
        secret: str,
        code: str,
        valid_window: Optional[int] = None,
    ) -> bool:
        """
        Verify a TOTP code.

        Args:
            secret: Base32-encoded secret
            code: 6-digit code from authenticator
            valid_window: Override default valid window

        Returns:
            True if code is valid
        """
        if not secret:
            raise InvalidSecretError("Secret cannot be empty")
        if not code:
            return False

        # Clean and validate code
        code = code.strip().replace(" ", "")
        if not code.isdigit() or len(code) != self._digits:
            logger.debug(f"Invalid code format: length={len(code)}")
            return False

        window = valid_window if valid_window is not None else self._valid_window
        current_time = int(time.time())

        # Check codes in valid window
        for offset in range(-window, window + 1):
            counter = (current_time // self._interval) + offset
            expected_code = self._generate_code(secret, counter)

            if hmac.compare_digest(code, expected_code):
                logger.debug(f"TOTP code verified (offset={offset})")
                return True

        logger.debug("TOTP code verification failed")
        return False

    def get_current_code(self, secret: str) -> str:
        """
        Get the current valid TOTP code.

        Args:
            secret: Base32-encoded secret

        Returns:
            Current 6-digit code

        Note:
            Useful for testing. Do not expose to users.
        """
        if not secret:
            raise InvalidSecretError("Secret cannot be empty")

        counter = int(time.time()) // self._interval
        return self._generate_code(secret, counter)

    def get_time_remaining(self) -> int:
        """
        Get seconds until current code expires.

        Returns:
            Seconds remaining in current interval
        """
        return self._interval - (int(time.time()) % self._interval)

    def _generate_code(self, secret: str, counter: int) -> str:
        """
        Generate TOTP code for a specific counter value.

        Args:
            secret: Base32-encoded secret
            counter: Time counter value

        Returns:
            6-digit code string
        """
        try:
            # Decode secret
            key = base64.b32decode(secret.upper() + "=" * (-len(secret) % 8))
        except Exception as e:
            raise InvalidSecretError(f"Invalid secret format: {e}") from e

        # HOTP algorithm (RFC 4226)
        counter_bytes = struct.pack(">Q", counter)
        hmac_hash = hmac.new(key, counter_bytes, hashlib.sha1).digest()

        # Dynamic truncation
        offset = hmac_hash[-1] & 0x0F
        truncated = struct.unpack(">I", hmac_hash[offset : offset + 4])[0]
        truncated &= 0x7FFFFFFF

        # Generate code with leading zeros
        code = truncated % (10**self._digits)
        return str(code).zfill(self._digits)

    def _generate_placeholder_png(self, size: int) -> bytes:
        """
        Generate a minimal placeholder PNG when qrcode is unavailable.

        Args:
            size: Requested image size (ignored, returns 1x1 pixel)

        Returns:
            Minimal valid PNG bytes
        """
        # Minimal 1x1 transparent PNG
        return bytes(
            [
                0x89,
                0x50,
                0x4E,
                0x47,
                0x0D,
                0x0A,
                0x1A,
                0x0A,  # PNG signature
                0x00,
                0x00,
                0x00,
                0x0D,  # IHDR length
                0x49,
                0x48,
                0x44,
                0x52,  # IHDR
                0x00,
                0x00,
                0x00,
                0x01,  # Width: 1
                0x00,
                0x00,
                0x00,
                0x01,  # Height: 1
                0x08,
                0x04,  # Bit depth: 8, Color type: 4 (grayscale+alpha)
                0x00,
                0x00,
                0x00,  # Compression, Filter, Interlace
                0x89,
                0x4E,
                0xB3,
                0x14,  # CRC
                0x00,
                0x00,
                0x00,
                0x0B,  # IDAT length
                0x49,
                0x44,
                0x41,
                0x54,  # IDAT
                0x78,
                0x01,
                0x63,
                0x60,
                0x60,
                0x00,
                0x00,
                0x00,
                0x03,
                0x00,
                0x01,
                0x26,
                0x7E,
                0x1B,
                0x93,
                # CRC (recalculated)
                0x00,
                0x00,
                0x00,
                0x00,  # IEND length
                0x49,
                0x45,
                0x4E,
                0x44,  # IEND
                0xAE,
                0x42,
                0x60,
                0x82,  # CRC
            ]
        )


__all__ = [
    "TOTPManager",
    "TOTPError",
    "InvalidSecretError",
    "InvalidCodeError",
]
