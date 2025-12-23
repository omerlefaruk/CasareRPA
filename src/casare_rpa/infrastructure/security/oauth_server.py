"""
CasareRPA - OAuth Callback Server

Provides OAuth 2.0 callback handling for desktop applications.
Supports two modes:
1. LOCAL mode: Localhost server for development (http://127.0.0.1:{port}/oauth/callback)
2. CLOUD mode: Production server at api.casare.net (https://api.casare.net/oauth/callback)

Features:
- Runs on a random available port in the ephemeral range (LOCAL mode)
- Polls cloud server for auth code (CLOUD mode)
- Handles OAuth callback with authorization code extraction
- CSRF protection via state parameter validation
- User-friendly HTML responses for success/error
- Automatic shutdown after callback received

Usage:
    # LOCAL mode (development)
    server = LocalOAuthServer()
    port = server.start()
    redirect_uri = server.redirect_uri
    auth_code, error = await server.wait_for_callback(timeout=300)
    server.stop()

    # CLOUD mode (production)
    redirect_uri = get_cloud_redirect_uri()
    state = generate_oauth_state()
    # ... user authorizes ...
    auth_code, error = await poll_for_cloud_auth_code(state, timeout=300)
"""

from __future__ import annotations

import asyncio
import secrets
import socket
import threading
from enum import Enum
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from loguru import logger


class OAuthMode(Enum):
    """OAuth redirect mode."""

    LOCAL = "local"  # Development - uses localhost
    CLOUD = "cloud"  # Production - uses api.casare.net


# Cloud OAuth endpoints
CLOUD_REDIRECT_URI = "https://api.casare.net/oauth/callback"
CLOUD_AUTH_CODE_ENDPOINT = "https://api.casare.net/oauth/code"  # Polling endpoint


# HTML templates for callback responses
SUCCESS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Authorization Successful</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
        }
        .container {
            text-align: center;
            padding: 40px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            max-width: 500px;
            margin: 20px;
        }
        .icon {
            width: 80px;
            height: 80px;
            margin: 0 auto 20px;
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
        }
        .icon svg {
            width: 40px;
            height: 40px;
            fill: white;
        }
        h1 {
            font-size: 24px;
            margin-bottom: 16px;
            font-weight: 600;
        }
        p {
            color: rgba(255, 255, 255, 0.7);
            line-height: 1.6;
            margin-bottom: 24px;
        }
        .brand {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin-top: 24px;
            padding-top: 24px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.5);
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">
            <svg viewBox="0 0 24 24">
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
            </svg>
        </div>
        <h1>Authorization Successful!</h1>
        <p>Your Google account has been connected to CasareRPA. You can close this window and return to the application.</p>
        <div class="brand">
            CasareRPA
        </div>
    </div>
    <script>
        // Auto-close after 3 seconds
        setTimeout(function() {
            window.close();
        }, 3000);
    </script>
</body>
</html>"""

ERROR_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Authorization Failed</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
        }
        .container {
            text-align: center;
            padding: 40px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            max-width: 500px;
            margin: 20px;
        }
        .icon {
            width: 80px;
            height: 80px;
            margin: 0 auto 20px;
            background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 15px rgba(244, 67, 54, 0.3);
        }
        .icon svg {
            width: 40px;
            height: 40px;
            fill: white;
        }
        h1 {
            font-size: 24px;
            margin-bottom: 16px;
            font-weight: 600;
        }
        p {
            color: rgba(255, 255, 255, 0.7);
            line-height: 1.6;
            margin-bottom: 16px;
        }
        .error-code {
            background: rgba(244, 67, 54, 0.1);
            border: 1px solid rgba(244, 67, 54, 0.3);
            border-radius: 8px;
            padding: 12px 16px;
            font-family: monospace;
            font-size: 14px;
            color: #f44336;
            margin-bottom: 24px;
            word-break: break-all;
        }
        .brand {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin-top: 24px;
            padding-top: 24px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.5);
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">
            <svg viewBox="0 0 24 24">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
        </div>
        <h1>Authorization Failed</h1>
        <p>We couldn't complete the authorization. Please close this window and try again in CasareRPA.</p>
        <div class="error-code">{error_message}</div>
        <div class="brand">
            CasareRPA
        </div>
    </div>
</body>
</html>"""


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for OAuth 2.0 callbacks.

    Handles GET requests to /oauth/callback with authorization code
    and state parameter validation for CSRF protection.
    """

    def log_message(self, format: str, *args) -> None:
        """Suppress default HTTP server logging."""
        # Use loguru instead
        logger.debug(f"OAuth callback server: {format % args}")

    def do_GET(self) -> None:
        """Handle GET requests for OAuth callback."""
        parsed = urlparse(self.path)

        # Only handle the callback path
        if parsed.path != self.server.redirect_path:
            self._send_404()
            return

        # Parse query parameters
        query_params = parse_qs(parsed.query)

        # Check for error response from OAuth provider
        if "error" in query_params:
            error = query_params["error"][0]
            error_description = query_params.get("error_description", ["Unknown error"])[0]
            logger.warning(f"OAuth error: {error} - {error_description}")
            self._send_error_response(f"{error}: {error_description}")
            self.server.set_result(None, f"{error}: {error_description}")
            return

        # Validate state parameter for CSRF protection
        received_state = query_params.get("state", [None])[0]
        expected_state = self.server.expected_state

        if expected_state and received_state != expected_state:
            logger.warning(f"State mismatch: expected={expected_state}, received={received_state}")
            self._send_error_response("Invalid state parameter (CSRF protection)")
            self.server.set_result(None, "Invalid state parameter")
            return

        # Extract authorization code
        auth_code = query_params.get("code", [None])[0]

        if not auth_code:
            logger.warning("No authorization code in callback")
            self._send_error_response("No authorization code received")
            self.server.set_result(None, "No authorization code")
            return

        # Success - store the code
        logger.info("OAuth authorization code received successfully")
        self._send_success_response()
        self.server.set_result(auth_code, None)

    def _send_success_response(self) -> None:
        """Send success HTML response."""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(SUCCESS_HTML.encode("utf-8"))

    def _send_error_response(self, error_message: str) -> None:
        """Send error HTML response."""
        self.send_response(400)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        html = ERROR_HTML.replace("{error_message}", error_message)
        self.wfile.write(html.encode("utf-8"))

    def _send_404(self) -> None:
        """Send 404 response."""
        self.send_response(404)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Not Found")


class OAuthHTTPServer(HTTPServer):
    """
    Custom HTTPServer with result storage for OAuth callback.

    Extends HTTPServer to store the authorization code and error
    from the callback, allowing the main thread to retrieve results.
    """

    def __init__(
        self,
        server_address: tuple[str, int],
        handler_class: type,
        redirect_path: str,
        expected_state: str | None,
    ) -> None:
        super().__init__(server_address, handler_class)
        self.redirect_path = redirect_path
        self.expected_state = expected_state
        self._result_auth_code: str | None = None
        self._result_error: str | None = None
        self._result_event = threading.Event()

    def set_result(self, auth_code: str | None, error: str | None) -> None:
        """Store the callback result."""
        self._result_auth_code = auth_code
        self._result_error = error
        self._result_event.set()

    def get_result(self) -> tuple[str | None, str | None]:
        """Get the stored result."""
        return self._result_auth_code, self._result_error

    def wait_for_result(self, timeout: float) -> bool:
        """Wait for result with timeout. Returns True if result received."""
        return self._result_event.wait(timeout)


class LocalOAuthServer:
    """
    Local HTTP server for OAuth 2.0 authorization callback handling.

    Starts a temporary HTTP server on localhost to receive the OAuth
    authorization code redirect. Provides CSRF protection via the
    state parameter.

    Attributes:
        REDIRECT_PATH: The callback path ("/oauth/callback")
        PORT_RANGE_START: Start of ephemeral port range (49152)
        PORT_RANGE_END: End of ephemeral port range (65535)
    """

    REDIRECT_PATH = "/oauth/callback"
    PORT_RANGE_START = 49152
    PORT_RANGE_END = 65535

    def __init__(self) -> None:
        """Initialize the OAuth server."""
        self._server: OAuthHTTPServer | None = None
        self._server_thread: threading.Thread | None = None
        self._port: int | None = None
        self._state: str | None = None

    def _find_available_port(self) -> int:
        """
        Find an available port in the ephemeral range.

        Returns:
            Available port number.

        Raises:
            RuntimeError: If no port is available.
        """
        # Try to find an available port
        for _ in range(100):  # Try up to 100 times
            # Use system to find a free port
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", 0))
                port = s.getsockname()[1]

                # Verify it's in our preferred range or accept any ephemeral
                if self.PORT_RANGE_START <= port <= self.PORT_RANGE_END:
                    return port

        # Fallback: let the OS choose any port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    def generate_state(self) -> str:
        """
        Generate a cryptographically secure state parameter for CSRF protection.

        Returns:
            Random state string (32 hex characters).
        """
        self._state = secrets.token_hex(16)
        return self._state

    @property
    def state(self) -> str | None:
        """Get the current state parameter."""
        return self._state

    def start(self, state: str | None = None) -> int:
        """
        Start the OAuth callback server.

        Args:
            state: Optional state parameter for CSRF protection.
                   If not provided, one will be generated.

        Returns:
            Port number the server is listening on.

        Raises:
            RuntimeError: If server is already running or cannot start.
        """
        if self._server is not None:
            raise RuntimeError("OAuth server is already running")

        # Generate or use provided state
        if state is not None:
            self._state = state
        elif self._state is None:
            self.generate_state()

        # Find available port
        self._port = self._find_available_port()

        try:
            self._server = OAuthHTTPServer(
                ("127.0.0.1", self._port),
                OAuthCallbackHandler,
                self.REDIRECT_PATH,
                self._state,
            )

            # Start server in background thread
            self._server_thread = threading.Thread(
                target=self._server.serve_forever,
                daemon=True,
                name="OAuthCallbackServer",
            )
            self._server_thread.start()

            logger.info(f"OAuth callback server started on port {self._port}")
            return self._port

        except Exception as e:
            self._server = None
            self._server_thread = None
            logger.error(f"Failed to start OAuth server: {e}")
            raise RuntimeError(f"Failed to start OAuth server: {e}") from e

    @property
    def redirect_uri(self) -> str:
        """
        Get the redirect URI for OAuth authorization requests.

        Returns:
            Full redirect URI (e.g., "http://127.0.0.1:12345/oauth/callback")

        Raises:
            RuntimeError: If server is not running.
        """
        if self._port is None:
            raise RuntimeError("OAuth server is not running")
        return f"http://127.0.0.1:{self._port}{self.REDIRECT_PATH}"

    @property
    def port(self) -> int | None:
        """Get the port number the server is listening on."""
        return self._port

    @property
    def is_running(self) -> bool:
        """Check if the server is running."""
        return self._server is not None and self._server_thread is not None

    async def wait_for_callback(self, timeout: float = 300.0) -> tuple[str | None, str | None]:
        """
        Wait for the OAuth callback to be received.

        Blocks until the callback is received or timeout expires.
        Uses asyncio to avoid blocking the event loop.

        Args:
            timeout: Maximum seconds to wait (default: 300 = 5 minutes).

        Returns:
            Tuple of (authorization_code, error_message).
            - On success: (code, None)
            - On error: (None, error_message)
            - On timeout: (None, "Timeout waiting for OAuth callback")
        """
        if self._server is None:
            return None, "OAuth server is not running"

        # Use asyncio to wait without blocking
        loop = asyncio.get_event_loop()

        try:
            received = await loop.run_in_executor(None, self._server.wait_for_result, timeout)

            if not received:
                return None, "Timeout waiting for OAuth callback"

            return self._server.get_result()

        except Exception as e:
            logger.error(f"Error waiting for OAuth callback: {e}")
            return None, f"Error waiting for callback: {e}"

    def stop(self) -> None:
        """
        Stop the OAuth callback server.

        Safe to call multiple times or if server is not running.
        """
        if self._server is not None:
            try:
                self._server.shutdown()
                logger.info("OAuth callback server stopped")
            except Exception as e:
                logger.warning(f"Error stopping OAuth server: {e}")
            finally:
                self._server = None

        if self._server_thread is not None:
            try:
                self._server_thread.join(timeout=1.0)
            except Exception:
                pass
            finally:
                self._server_thread = None

        self._port = None

    def __enter__(self) -> LocalOAuthServer:
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()

    async def __aenter__(self) -> LocalOAuthServer:
        """Async context manager entry."""
        self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        self.stop()


# Convenience function for creating authorization URL
def build_google_auth_url(
    client_id: str,
    redirect_uri: str,
    scopes: list[str],
    state: str,
    access_type: str = "offline",
    prompt: str = "consent",
    login_hint: str | None = None,
) -> str:
    """
    Build a Google OAuth 2.0 authorization URL.

    Args:
        client_id: OAuth 2.0 client ID.
        redirect_uri: Callback URI for the authorization response.
        scopes: List of OAuth scopes to request.
        state: State parameter for CSRF protection.
        access_type: "offline" for refresh token, "online" for access only.
        prompt: "consent" to always show consent screen, "none" for silent.
        login_hint: Optional email to pre-fill in login form.

    Returns:
        Complete authorization URL to redirect the user to.
    """
    from urllib.parse import urlencode

    base_url = "https://accounts.google.com/o/oauth2/v2/auth"

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "state": state,
        "access_type": access_type,
        "prompt": prompt,
    }

    if login_hint:
        params["login_hint"] = login_hint

    return f"{base_url}?{urlencode(params)}"


def get_cloud_redirect_uri() -> str:
    """
    Get the cloud redirect URI for production OAuth.

    Returns:
        The api.casare.net OAuth callback URL.
    """
    return CLOUD_REDIRECT_URI


def generate_oauth_state() -> str:
    """
    Generate a cryptographically secure state parameter.

    Returns:
        Random state string (32 hex characters).
    """
    return secrets.token_hex(16)


async def poll_for_cloud_auth_code(
    state: str,
    timeout: float = 300.0,
    poll_interval: float = 2.0,
) -> tuple[str | None, str | None]:
    """
    Poll the cloud server for the OAuth authorization code.

    The cloud server (api.casare.net) receives the OAuth callback and stores
    the authorization code. This function polls the server to retrieve it.

    Args:
        state: The state parameter used in the OAuth request.
        timeout: Maximum seconds to wait (default: 300 = 5 minutes).
        poll_interval: Seconds between poll attempts (default: 2).

    Returns:
        Tuple of (authorization_code, error_message).
        - On success: (code, None)
        - On error: (None, error_message)
        - On timeout: (None, "Timeout waiting for OAuth callback")
    """
    import aiohttp

    start_time = asyncio.get_event_loop().time()
    endpoint = f"{CLOUD_AUTH_CODE_ENDPOINT}?state={state}"

    logger.debug(f"Starting cloud OAuth polling for state: {state[:8]}...")

    async with aiohttp.ClientSession() as session:
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                logger.warning("Timeout waiting for cloud OAuth callback")
                return None, "Timeout waiting for OAuth callback"

            try:
                async with session.get(
                    endpoint, timeout=aiohttp.ClientTimeout(total=10.0)
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data.get("status") == "pending":
                            # Auth code not yet received, continue polling
                            await asyncio.sleep(poll_interval)
                            continue

                        if data.get("status") == "complete":
                            auth_code = data.get("code")
                            if auth_code:
                                logger.info("Cloud OAuth authorization code received")
                                return auth_code, None
                            else:
                                return None, "No authorization code in response"

                        if data.get("status") == "error":
                            error = data.get("error", "Unknown error")
                            logger.warning(f"Cloud OAuth error: {error}")
                            return None, error

                    elif response.status == 404:
                        # State not found yet, continue polling
                        await asyncio.sleep(poll_interval)
                        continue

                    else:
                        error_text = await response.text()
                        logger.warning(f"Cloud OAuth poll failed: {response.status} - {error_text}")
                        await asyncio.sleep(poll_interval)
                        continue

            except aiohttp.ClientError as e:
                logger.debug(f"Cloud OAuth poll network error: {e}")
                await asyncio.sleep(poll_interval)
                continue

            except Exception as e:
                logger.error(f"Cloud OAuth poll error: {e}")
                await asyncio.sleep(poll_interval)
                continue


__all__ = [
    # Enums
    "OAuthMode",
    # Constants
    "CLOUD_REDIRECT_URI",
    "CLOUD_AUTH_CODE_ENDPOINT",
    # HTML templates
    "SUCCESS_HTML",
    "ERROR_HTML",
    # Handler
    "OAuthCallbackHandler",
    # Server
    "LocalOAuthServer",
    # Utilities
    "build_google_auth_url",
    "get_cloud_redirect_uri",
    "generate_oauth_state",
    "poll_for_cloud_auth_code",
]
