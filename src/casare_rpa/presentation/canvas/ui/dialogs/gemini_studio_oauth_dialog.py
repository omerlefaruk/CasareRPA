"""
Gemini AI Studio OAuth Dialog for CasareRPA.

Provides a simplified OAuth flow specifically for Gemini AI Studio:
- Uses built-in Gemini CLI OAuth client (no client ID/secret needed)
- Uses generative-language scope (works with Gemini subscription, no GCP billing)
- PKCE flow with local server on port 8085
- Auto-detects and saves user email

Based on opencode-gemini-auth: https://github.com/jenslys/opencode-gemini-auth
"""

from __future__ import annotations

import os
import secrets
import webbrowser
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from socket import socket
from typing import Any

from loguru import logger
from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Import styled dialog helpers
from casare_rpa.presentation.canvas.ui.dialogs.dialog_styles import (
    show_styled_information,
    show_styled_warning,
)

# =============================================================================
# Gemini AI Studio OAuth Configuration
# =============================================================================


# Gemini CLI OAuth 2.0 Client (from opencode-gemini-auth)
# These are public OAuth client credentials - safe to expose
# Source: https://github.com/jenslys/opencode-gemini-auth
def _get_gemini_client_id() -> str:
    """Get Gemini OAuth client ID from environment or use default."""
    return os.getenv(
        "GEMINI_OAUTH_CLIENT_ID",
        "681255809395-oo8ft2oprdrnp9e3aqf6av3hmdib135j.apps.googleusercontent.com",
    )


def _get_gemini_client_secret() -> str:
    """Get Gemini OAuth client secret from environment or use default."""
    return os.getenv(
        "GEMINI_OAUTH_CLIENT_SECRET",
        "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",
    )


GEMINI_REDIRECT_URI = "http://localhost:8085/oauth2callback"

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

GEMINI_SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
]


# =============================================================================
# Local OAuth Server for Callback
# =============================================================================


@dataclass
class OAuthCallbackResult:
    """Result from OAuth callback server."""

    code: str | None = None
    state: str | None = None
    error: str | None = None


class _CallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callback."""

    def do_GET(self) -> None:
        """Handle GET request for OAuth callback."""
        if self.path.startswith("/oauth2callback"):
            # Parse query parameters
            from urllib.parse import parse_qs, urlparse

            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            code = params.get("code", [None])[0]
            state = params.get("state", [None])[0]
            error = params.get("error", [None])[0]

            # Store result for server to retrieve
            if hasattr(self.server, "_callback_result"):
                self.server._callback_result = OAuthCallbackResult(
                    code=code, state=state, error=error
                )

            # Send response
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()

            if error:
                self.wfile.write(
                    b"<html><body><h1>Authorization Failed</h1>"
                    b"<p>You can close this window and return to CasareRPA.</p></body></html>"
                )
            else:
                self.wfile.write(
                    b"<html><body><h1>Authorization Successful!</h1>"
                    b"<p>You can close this window and return to CasareRPA.</p></body></html>"
                )

            # Signal server to stop
            if hasattr(self.server, "_stop_event"):
                self.server._stop_event.set()

    def log_message(self, format: str, *args) -> None:
        """Suppress default logging."""
        pass


class _LocalOAuthServer:
    """Simple local HTTP server for OAuth callback."""

    def __init__(self, port: int = 8085):
        self.port = port
        self.server: HTTPServer | None = None
        self._callback_result: OAuthCallbackResult | None = None
        self._stop_event: Any = None

    def start(self) -> bool:
        """Start the local server. Returns True if successful."""
        try:
            # Find available port
            self.server = HTTPServer(("localhost", self.port), _CallbackHandler)
            self.server._callback_result = OAuthCallbackResult()
            self.server._stop_event = (
                threading.Event() if (threading := __import__("threading")) else None
            )
            self.server.timeout = 1

            # Start in background thread
            import threading

            thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            thread.start()

            logger.debug(f"OAuth server started on port {self.port}")
            return True

        except OSError as e:
            if e.errno == 48 or "address already in use" in str(e).lower():
                logger.warning(f"Port {self.port} already in use")
            return False

    def stop(self) -> None:
        """Stop the server."""
        if self.server:
            self.server.shutdown()
            self.server = None

    def wait_for_callback(self, timeout: float = 300.0) -> OAuthCallbackResult:
        """Wait for OAuth callback. Returns the result."""
        import time

        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.server and hasattr(self.server, "_callback_result"):
                result = self.server._callback_result
                if result.code or result.error:
                    return result
            time.sleep(0.5)

        return OAuthCallbackResult(error="Timeout waiting for authorization")


# =============================================================================
# PKCE Helpers
# =============================================================================


def _generate_code_verifier() -> str:
    """Generate a secure random code verifier for PKCE."""
    return secrets.token_urlsafe(32)


def _generate_code_challenge(verifier: str) -> str:
    """Generate the code challenge from the verifier using SHA256."""
    import base64
    import hashlib

    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def _encode_state(payload: dict) -> str:
    """Encode a dict into a URL-safe base64 string for OAuth state."""
    import base64
    import json

    json_str = json.dumps(payload)
    return base64.urlsafe_b64encode(json_str.encode()).rstrip(b"=").decode()


# =============================================================================
# Callback Waiter Thread
# =============================================================================


class _CallbackWaiterThread(QThread):
    """Background thread to wait for OAuth callback without blocking UI."""

    callback_received = Signal(str, str)  # code, state
    error_occurred = Signal(str)

    def __init__(self, oauth_server: _LocalOAuthServer, timeout: float = 300.0):
        super().__init__()
        self._oauth_server = oauth_server
        self._timeout = timeout

    def run(self) -> None:
        """Wait for OAuth callback in background thread."""
        try:
            result = self._oauth_server.wait_for_callback(timeout=self._timeout)
            if result.error:
                self.error_occurred.emit(result.error)
            elif result.code:
                self.callback_received.emit(result.code, result.state or "")
        except Exception as e:
            self.error_occurred.emit(str(e))


# =============================================================================
# Token Exchange Worker
# =============================================================================


class GeminiTokenExchangeWorker(QThread):
    """
    Background worker for exchanging authorization code for tokens.
    """

    finished = Signal(bool, str, object)  # success, message, token_data
    progress = Signal(str)

    def __init__(self, code: str, state: str, verifier: str):
        super().__init__()
        self.code = code
        self.state = state
        self.verifier = verifier

    def run(self) -> None:
        """Exchange authorization code for tokens."""
        try:
            self.progress.emit("Exchanging authorization code for tokens...")

            # Run async token exchange
            result = asyncio.run(self._exchange_token_async())

            if not result["success"]:
                self.finished.emit(False, result.get("error", "Token exchange failed"), None)
                return

            self.finished.emit(True, "Authorization successful!", result["token_data"])

        except Exception as e:
            logger.error(f"Gemini token exchange error: {e}")
            self.finished.emit(False, f"Error: {str(e)}", None)

    async def _exchange_token_async(self) -> dict[str, Any]:
        """Async token exchange using aiohttp."""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            # Exchange code for tokens
            data = {
                "client_id": _get_gemini_client_id(),
                "client_secret": _get_gemini_client_secret(),
                "code": self.code,
                "grant_type": "authorization_code",
                "redirect_uri": GEMINI_REDIRECT_URI,
                "code_verifier": self.verifier,
            }

            async with session.post(GOOGLE_TOKEN_URL, data=data) as response:
                # Check HTTP status first
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Token exchange HTTP {response.status}: {error_text}")
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}

                result = await response.json()

                if "error" in result:
                    error_desc = result.get("error_description", result["error"])
                    return {"success": False, "error": error_desc}

                access_token = result.get("access_token")
                refresh_token = result.get("refresh_token")

                if not refresh_token:
                    return {"success": False, "error": "Missing refresh token in response"}

                # Get user email
                user_email = None
                if access_token:
                    async with session.get(
                        GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
                    ) as userinfo_response:
                        if userinfo_response.status == 200:
                            userinfo = await userinfo_response.json()
                            user_email = userinfo.get("email")

                # Calculate token expiry
                expires_in = result.get("expires_in", 3600)
                token_expiry = datetime.now(UTC) + timedelta(seconds=expires_in)

                token_data = {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_expiry": token_expiry.isoformat(),
                    "scopes": GEMINI_SCOPES,
                    "user_email": user_email,
                }

                return {"success": True, "token_data": token_data}


# =============================================================================
# Main Dialog
# =============================================================================


class GeminiStudioOAuthDialog(QDialog):
    """
    Gemini AI Studio OAuth authorization dialog.

    Simplified OAuth flow specifically for Gemini AI Studio:
    - Uses built-in Gemini CLI OAuth client
    - Uses generative-language scope (no GCP billing needed)
    - Auto-detects user email

    Signals:
        credential_created: Emitted when credential is created (credential_id)
    """

    credential_created = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._oauth_server: _LocalOAuthServer | None = None
        self._worker: GeminiTokenExchangeWorker | None = None
        self._callback_waiter: _CallbackWaiterThread | None = None

        self.setWindowTitle("Connect Gemini AI Studio")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setModal(True)

        self._setup_ui()

        logger.debug("GeminiStudioOAuthDialog opened")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        from casare_rpa.presentation.canvas.theme import THEME

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Header
        header = QLabel("Connect Gemini AI Studio")
        header.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {THEME.text_primary};")
        layout.addWidget(header)

        # Description
        description = QLabel(
            "Authenticate with your Google account to use Gemini models.\n"
            "This uses your Gemini subscription (no separate API billing needed)."
        )
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {THEME.text_secondary};")
        layout.addWidget(description)

        # Info box
        info = QLabel(
            "<b>What this does:</b><br>"
            "• Uses Gemini AI Studio API (generativelanguage.googleapis.com)<br>"
            "• Works with your Gemini subscription or free tier<br>"
            "• No Google Cloud project or billing required<br>"
            "• Credentials are stored securely on your computer"
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            f"color: {THEME.text_secondary}; background: {THEME.bg_medium}; "
            f"padding: 12px; border-radius: 4px;"
        )
        layout.addWidget(info)

        layout.addStretch()

        # Status
        self._status_label = QLabel("Ready to authorize")
        self._status_label.setStyleSheet(f"color: {THEME.text_secondary};")
        layout.addWidget(self._status_label)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setVisible(False)
        self._progress_bar.setMaximumHeight(4)
        layout.addWidget(self._progress_bar)

        # Authorize button
        self._authorize_btn = QPushButton("Authorize with Google")
        self._authorize_btn.setMinimumHeight(44)
        self._authorize_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME.accent_primary};
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {THEME.accent_hover};
            }}
            QPushButton:disabled {{
                background-color: {THEME.bg_light};
                color: {THEME.text_muted};
            }}
        """)

        # Cancel button
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setMinimumHeight(44)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self._cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(self._authorize_btn)
        layout.addLayout(button_layout)

        # Connect signals
        self._authorize_btn.clicked.connect(self._start_authorization)
        self._cancel_btn.clicked.connect(self.reject)

        # Apply styles
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {THEME.bg_darkest};
                color: {THEME.text_primary};
            }}
            QLabel {{
                color: {THEME.text_primary};
            }}
            QPushButton {{
                background-color: {THEME.bg_light};
                color: {THEME.text_primary};
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {THEME.bg_medium};
            }}
            QProgressBar {{
                background-color: {THEME.bg_light};
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {THEME.accent_primary};
                border-radius: 2px;
            }}
        """)

    @Slot()
    def _start_authorization(self) -> None:
        """Start the OAuth authorization flow."""
        self._authorize_btn.setEnabled(False)
        self._progress_bar.setVisible(True)
        self._update_status("Starting authorization...")

        # Start local OAuth server
        self._oauth_server = _LocalOAuthServer()
        if not self._oauth_server.start():
            self._on_auth_error("Failed to start local server. Port 8085 may be in use.")
            return

        # Generate PKCE pair
        code_verifier = _generate_code_verifier()
        code_challenge = _generate_code_challenge(code_verifier)

        # Build state with verifier
        state = _encode_state({"verifier": code_verifier})

        # Build authorization URL
        from urllib.parse import urlencode

        params = {
            "client_id": _get_gemini_client_id(),
            "response_type": "code",
            "redirect_uri": GEMINI_REDIRECT_URI,
            "scope": " ".join(GEMINI_SCOPES),
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }

        auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

        # Open browser
        self._update_status("Opening browser for authorization...")
        webbrowser.open(auth_url)

        # Wait for callback in background thread
        self._update_status("Waiting for authorization... (check your browser)")
        self._callback_waiter = _CallbackWaiterThread(self._oauth_server, timeout=300.0)
        self._callback_waiter.callback_received.connect(self._on_code_received)
        self._callback_waiter.error_occurred.connect(self._on_callback_error)
        self._callback_waiter.finished.connect(self._on_callback_wait_finished)
        self._callback_waiter.start()

    @Slot(str)
    def _on_callback_error(self, error: str) -> None:
        """Handle callback waiter error."""
        self._on_auth_error(error)

    @Slot()
    def _on_callback_wait_finished(self) -> None:
        """Clean up after callback waiter finishes."""
        if self._oauth_server:
            self._oauth_server.stop()
            self._oauth_server = None
        self._callback_waiter = None

    @Slot(str, str)
    def _on_code_received(self, code: str, state: str) -> None:
        """Handle received authorization code."""
        self._update_status("Authorization code received, exchanging for tokens...")

        # Decode state to get verifier
        try:
            import base64
            import json

            padded = state + "=" * (4 - len(state) % 4)
            state_json = base64.urlsafe_b64decode(padded.encode()).decode()
            state_data = json.loads(state_json)
            verifier = state_data.get("verifier", "")
        except Exception:
            verifier = ""

        # Exchange code for tokens in background thread
        self._worker = GeminiTokenExchangeWorker(code, state, verifier)
        self._worker.finished.connect(self._on_token_exchange_complete)
        self._worker.progress.connect(self._update_status)
        self._worker.start()

    @Slot(bool, str, object)
    def _on_token_exchange_complete(
        self, success: bool, message: str, token_data: dict[str, Any] | None
    ) -> None:
        """Handle token exchange completion."""
        self._progress_bar.setVisible(False)

        if not success or not token_data:
            self._on_auth_error(message)
            return

        self._update_status("Saving credential...")

        # Save credential to store
        try:
            from casare_rpa.infrastructure.security.credential_store import (
                CredentialType,
                get_credential_store,
            )

            store = get_credential_store()

            # Create a descriptive name
            user_email = token_data.get("user_email", "")
            credential_name = (
                f"Gemini AI Studio ({user_email})" if user_email else "Gemini AI Studio"
            )

            credential_id = store.save_credential(
                name=credential_name,
                credential_type=CredentialType.GOOGLE_OAUTH_KIND,
                category="google",
                data={
                    "client_id": _get_gemini_client_id(),
                    "client_secret": _get_gemini_client_secret(),
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data["refresh_token"],
                    "token_expiry": token_data["token_expiry"],
                    "scopes": token_data["scopes"],
                    "user_email": user_email,
                },
                description="Gemini AI Studio OAuth (generative-language scope)",
                tags=["gemini", "ai_studio", "oauth"],
            )

            logger.info(f"Gemini AI Studio credential saved: {credential_id}")

            # Show success message
            show_styled_information(
                self,
                "Success!",
                f"Gemini AI Studio connected successfully!\n\n"
                f"Signed in as: {user_email or 'N/A'}\n"
                f"Credential saved as: {credential_name}",
            )

            self.credential_created.emit(credential_id)
            self.accept()

        except Exception as e:
            logger.error(f"Failed to save credential: {e}")
            self._on_auth_error(f"Failed to save credential: {e}")

    @Slot(str)
    def _on_auth_error(self, error: str) -> None:
        """Handle authorization error."""
        self._update_status(f"Error: {error}")
        self._authorize_btn.setEnabled(True)
        self._progress_bar.setVisible(False)

        show_styled_warning(
            self,
            "Authorization Failed",
            f"Failed to authorize with Gemini AI Studio:\n\n{error}",
        )

    @Slot(str)
    def _update_status(self, message: str) -> None:
        """Update status label."""
        self._status_label.setText(message)

    @Slot()
    def closeEvent(self, event) -> None:
        """Handle dialog close."""
        if self._oauth_server:
            self._oauth_server.stop()
            self._oauth_server = None

        super().closeEvent(event)


__all__ = ["GeminiStudioOAuthDialog"]
