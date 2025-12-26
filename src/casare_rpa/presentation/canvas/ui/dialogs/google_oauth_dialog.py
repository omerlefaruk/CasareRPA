"""
Google OAuth Flow Dialog for CasareRPA.

Provides a dialog for authenticating with Google OAuth 2.0:
- Credential name input
- Load from credentials.json file
- Client ID and Client Secret inputs (with show/hide toggle)
- Scope selection checkboxes
- Authorization flow via browser
- Token exchange and credential storage
"""

from __future__ import annotations

import asyncio
import json
import webbrowser
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from loguru import logger
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME
from casare_rpa.presentation.canvas.theme_system.helpers import (
    set_fixed_width,
    set_margins,
    set_min_size,
    set_spacing,
)
from casare_rpa.presentation.canvas.theme_system.tokens import TOKENS

# Import scopes from google_client
from casare_rpa.infrastructure.resources.google_client import GoogleScope

# Scope definitions with human-readable names
GOOGLE_SCOPES = {
    "gmail_full": {
        "label": "Gmail (Full Access)",
        "scope": GoogleScope.GMAIL_MODIFY.value,
        "description": "Read, send, and manage emails",
    },
    "gmail_readonly": {
        "label": "Gmail (Read Only)",
        "scope": GoogleScope.GMAIL_READONLY.value,
        "description": "Read emails only",
    },
    "sheets_full": {
        "label": "Sheets (Full Access)",
        "scope": GoogleScope.SHEETS_FULL.value,
        "description": "Read and write spreadsheets",
    },
    "sheets_readonly": {
        "label": "Sheets (Read Only)",
        "scope": GoogleScope.SHEETS_READONLY.value,
        "description": "Read spreadsheets only",
    },
    "drive_full": {
        "label": "Drive (Full Access)",
        "scope": GoogleScope.DRIVE_FULL.value,
        "description": "Full access to Google Drive",
    },
    "drive_file": {
        "label": "Drive (File Access)",
        "scope": GoogleScope.DRIVE_FILE.value,
        "description": "Access files created by this app",
    },
    "docs_full": {
        "label": "Google Docs",
        "scope": GoogleScope.DOCS_FULL.value,
        "description": "Read and write documents",
    },
    "calendar": {
        "label": "Calendar (Full Access)",
        "scope": GoogleScope.CALENDAR_FULL.value,
        "description": "Read and manage calendar events",
    },
    "calendar_readonly": {
        "label": "Calendar (Read Only)",
        "scope": GoogleScope.CALENDAR_READONLY.value,
        "description": "View calendar events only",
    },
    "gemini_ai": {
        "label": "Gemini AI / Vertex AI",
        "scope": GoogleScope.CLOUD_PLATFORM.value,
        "description": "Access Gemini via Vertex AI (requires API enabled in GCP project). For simpler setup, use an API key instead.",
    },
}


class OAuthWorker(QObject):
    """Background worker for OAuth token exchange."""

    finished = Signal(bool, str, object)  # success, message, token_data
    progress = Signal(str)  # status message

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        auth_code: str,
        redirect_uri: str,
        scopes: list[str],
        code_verifier: str | None = None,
    ) -> None:
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_code = auth_code
        self.redirect_uri = redirect_uri
        self.scopes = scopes
        self.code_verifier = code_verifier

    def run(self) -> None:
        """Exchange authorization code for tokens."""
        import asyncio

        try:
            self.progress.emit("Exchanging authorization code for tokens...")

            # Run async token exchange in sync context
            result, user_email = asyncio.run(self._exchange_token_async())

            if "error" in result:
                error_desc = result.get("error_description", result["error"])
                self.finished.emit(False, f"Token exchange failed: {error_desc}", None)
                return

            # Calculate token expiry
            expires_in = result.get("expires_in", 3600)
            token_expiry = datetime.now(UTC) + timedelta(seconds=expires_in)

            token_data = {
                "access_token": result["access_token"],
                "refresh_token": result.get("refresh_token", ""),
                "token_expiry": token_expiry.isoformat(),
                "scopes": self.scopes,
            }

            if user_email:
                token_data["user_email"] = user_email

            self.finished.emit(True, "Authorization successful!", token_data)

        except Exception as e:
            logger.error(f"OAuth token exchange error: {e}")
            self.finished.emit(False, f"Error: {str(e)}", None)

    async def _exchange_token_async(self) -> tuple[dict[str, Any], str | None]:
        """Async token exchange using UnifiedHttpClient."""
        from casare_rpa.infrastructure.http import (
            UnifiedHttpClient,
            UnifiedHttpClientConfig,
        )

        config = UnifiedHttpClientConfig(
            default_timeout=30.0,
            max_retries=2,
        )

        async with UnifiedHttpClient(config) as client:
            # Exchange authorization code for tokens
            data = {
                "grant_type": "authorization_code",
                "code": self.auth_code,
                "redirect_uri": self.redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }

            if self.code_verifier:
                data["code_verifier"] = self.code_verifier

            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data=data,
            )
            result = await response.json()

            if "error" in result:
                return result, None

            # Try to get user info
            user_email: str | None = None
            try:
                headers = {"Authorization": f"Bearer {result['access_token']}"}
                user_response = await client.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers=headers,
                )
                if user_response.status == 200:
                    user_info = await user_response.json()
                    user_email = user_info.get("email", "")
            except Exception as e:
                logger.debug(f"Could not fetch user info: {e}")

            return result, user_email


class OAuthThread(QThread):
    """Thread for running OAuth worker."""

    finished = Signal(bool, str, object)
    progress = Signal(str)

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        auth_code: str,
        redirect_uri: str,
        scopes: list[str],
        code_verifier: str | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._worker = OAuthWorker(
            client_id, client_secret, auth_code, redirect_uri, scopes, code_verifier
        )

    def run(self):
        self._worker.finished.connect(self.finished.emit)
        self._worker.progress.connect(self.progress.emit)
        self._worker.run()


class GoogleOAuthDialog(QDialog):
    """
    Google OAuth 2.0 authorization dialog.

    Features:
    - Credential name and client ID/secret inputs
    - Load credentials from JSON file
    - Scope selection with checkboxes
    - OAuth authorization flow via browser
    - Token exchange and storage

    Signals:
        credential_created: Emitted when a credential is successfully created (credential_id)
    """

    credential_created = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._oauth_server = None
        self._oauth_thread: OAuthThread | None = None
        self._waiting_for_callback = False
        self._current_redirect_uri: str | None = None
        self._current_state: str | None = None
        self._pkce_verifier: str | None = None

        self.setWindowTitle("Add Google Account")
        set_min_size(self, TOKENS.sizes.dialog_width_md + TOKENS.sizes.dialog_width_sm, TOKENS.sizes.dialog_height_xl)
        self.setModal(True)

        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

        logger.debug("GoogleOAuthDialog opened")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        set_spacing(layout, TOKENS.spacing.lg)
        set_margins(layout, TOKENS.margins.dialog)

        # Header
        header_label = QLabel("Connect Google Account")
        header_label.setStyleSheet(f"font-size: {TOKENS.fonts.xl}px; font-weight: bold; color: {THEME.text_primary};")
        layout.addWidget(header_label)

        description = QLabel(
            "Enter your Google Cloud OAuth credentials to connect your Google account. "
            "You can load credentials from a JSON file downloaded from Google Cloud Console."
        )
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {THEME.text_secondary}; margin-bottom: {TOKENS.spacing.sm}px;")
        layout.addWidget(description)

        # Credential Name
        name_group = QGroupBox("Credential Name")
        name_layout = QFormLayout(name_group)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("e.g., My Google Account")
        name_layout.addRow("Name:", self._name_input)

        layout.addWidget(name_group)

        # Client Credentials
        creds_group = QGroupBox("OAuth Credentials")
        creds_layout = QVBoxLayout(creds_group)

        # Load from file button
        file_layout = QHBoxLayout()
        self._load_file_btn = QPushButton("Load from credentials.json")
        self._load_file_btn.setToolTip(
            "Load client ID and secret from a credentials.json file "
            "downloaded from Google Cloud Console"
        )
        file_layout.addWidget(self._load_file_btn)

        # Use Default Gemini App button
        self._use_default_creds_btn = QPushButton("Use Default Gemini App")
        self._use_default_creds_btn.setToolTip(
            "Use the built-in Gemini CLI credentials (easiest for testing)"
        )
        file_layout.addWidget(self._use_default_creds_btn)

        file_layout.addStretch()
        creds_layout.addLayout(file_layout)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {THEME.border};")
        creds_layout.addWidget(separator)

        # Client ID
        form_layout = QFormLayout()

        self._client_id_input = QLineEdit()
        self._client_id_input.setPlaceholderText("Enter Client ID...")
        form_layout.addRow("Client ID:", self._client_id_input)

        # Client Secret with show/hide
        secret_layout = QHBoxLayout()
        self._client_secret_input = QLineEdit()
        self._client_secret_input.setPlaceholderText("Enter Client Secret...")
        self._client_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        secret_layout.addWidget(self._client_secret_input)

        self._show_secret_btn = QPushButton("Show")
        self._show_secret_btn.setCheckable(True)
        set_fixed_width(self._show_secret_btn, TOKENS.sizes.button_width_sm)
        secret_layout.addWidget(self._show_secret_btn)

        form_layout.addRow("Client Secret:", secret_layout)
        creds_layout.addLayout(form_layout)

        layout.addWidget(creds_group)

        # OAuth Mode Selection
        mode_group = QGroupBox("Redirect Mode")
        mode_layout = QVBoxLayout(mode_group)

        mode_description = QLabel("Choose where Google should redirect after authorization:")
        mode_description.setStyleSheet(f"color: {THEME.text_secondary}; margin-bottom: {TOKENS.spacing.sm}px;")
        mode_layout.addWidget(mode_description)

        self._mode_button_group = QButtonGroup(self)

        # Local mode (development)
        local_layout = QHBoxLayout()
        self._local_radio = QRadioButton("Local (Development)")
        self._local_radio.setChecked(True)
        self._local_radio.setToolTip("Uses localhost - works without server setup")
        local_layout.addWidget(self._local_radio)

        self._local_uri_label = QLabel("http://127.0.0.1:{port}/oauth/callback")
        self._local_uri_label.setStyleSheet(
            f"color: {THEME.text_secondary}; font-family: monospace; font-size: {TOKENS.fonts.xs}px;"
        )
        local_layout.addWidget(self._local_uri_label)
        local_layout.addStretch()
        mode_layout.addLayout(local_layout)

        # Cloud mode (production)
        cloud_layout = QHBoxLayout()
        self._cloud_radio = QRadioButton("Cloud (Production)")
        self._cloud_radio.setToolTip("Uses api.casare.net - requires server-side setup")
        cloud_layout.addWidget(self._cloud_radio)

        self._cloud_uri_label = QLabel("https://api.casare.net/oauth/callback")
        self._cloud_uri_label.setStyleSheet(
            f"color: {THEME.text_secondary}; font-family: monospace; font-size: {TOKENS.fonts.xs}px;"
        )
        cloud_layout.addWidget(self._cloud_uri_label)
        cloud_layout.addStretch()
        mode_layout.addLayout(cloud_layout)

        self._mode_button_group.addButton(self._local_radio, 0)
        self._mode_button_group.addButton(self._cloud_radio, 1)

        # Mode note
        mode_note = QLabel(
            "Note: Add the redirect URI to your Google Cloud Console OAuth settings."
        )
        mode_note.setWordWrap(True)
        mode_note.setStyleSheet(f"color: {THEME.text_muted}; font-size: {TOKENS.fonts.xs}px; margin-top: {TOKENS.spacing.sm}px;")
        mode_layout.addWidget(mode_note)

        layout.addWidget(mode_group)

        # Scope Selection
        scope_group = QGroupBox("Permissions (Scopes)")
        scope_layout = QVBoxLayout(scope_group)

        scope_description = QLabel("Select the permissions your workflow needs:")
        scope_description.setStyleSheet(f"color: {THEME.text_secondary}; margin-bottom: {TOKENS.spacing.sm}px;")
        scope_layout.addWidget(scope_description)

        # Scrollable scope area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(TOKENS.sizes.dialog_height_sm)
        scroll_area.setStyleSheet(f"QScrollArea {{ border: 1px solid {THEME.border}; background: {THEME.bg_dark}; }}")

        scope_container = QWidget()
        scope_grid = QGridLayout(scope_container)
        set_spacing(scope_grid, TOKENS.spacing.sm)

        self._scope_checkboxes: dict[str, QCheckBox] = {}
        row = 0
        col = 0

        for scope_key, scope_info in GOOGLE_SCOPES.items():
            checkbox = QCheckBox(scope_info["label"])
            checkbox.setToolTip(scope_info["description"])
            self._scope_checkboxes[scope_key] = checkbox
            scope_grid.addWidget(checkbox, row, col)

            col += 1
            if col >= 2:
                col = 0
                row += 1

        scroll_area.setWidget(scope_container)
        scope_layout.addWidget(scroll_area)

        layout.addWidget(scope_group)

        # Status section
        status_group = QGroupBox("Authorization Status")
        status_layout = QVBoxLayout(status_group)

        self._status_label = QLabel("Ready to authorize")
        self._status_label.setStyleSheet(f"color: {THEME.text_secondary};")
        status_layout.addWidget(self._status_label)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)  # Indeterminate
        self._progress_bar.setVisible(False)
        self._progress_bar.setMaximumHeight(TOKENS.sizes.progress_height)
        status_layout.addWidget(self._progress_bar)

        layout.addWidget(status_group)

        # Buttons
        button_layout = QHBoxLayout()

        self._authorize_btn = QPushButton("Authorize with Google")
        self._authorize_btn.setDefault(True)
        self._authorize_btn.setMinimumHeight(TOKENS.sizes.button_height_lg)
        self._authorize_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #4285f4;
                color: white;
                font-weight: bold;
                font-size: {TOKENS.fonts.md}px;
            }}
            QPushButton:hover {{
                background-color: #5a95f5;
            }}
            QPushButton:disabled {{
                background-color: #2d5a9e;
            }}
        """)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setMinimumHeight(TOKENS.sizes.button_height_lg)

        button_layout.addWidget(self._cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(self._authorize_btn)

        layout.addLayout(button_layout)

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self._load_file_btn.clicked.connect(self._on_load_file)
        self._use_default_creds_btn.clicked.connect(self._on_use_default_creds)
        self._show_secret_btn.toggled.connect(self._toggle_secret_visibility)
        self._authorize_btn.clicked.connect(self._start_authorization)
        self._cancel_btn.clicked.connect(self.reject)

    def _toggle_secret_visibility(self, checked: bool) -> None:
        """Toggle client secret visibility."""
        if checked:
            self._client_secret_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self._show_secret_btn.setText("Hide")
        else:
            self._show_secret_btn.setText("Show")

    def _on_use_default_creds(self) -> None:
        """Fill in default Gemini CLI credentials."""
        # Use known Google Gemini CLI credentials (publicly available in their repo)
        # Client ID: 681255809395-oo8ft2oprdrnp9e3aqf6av3hmdib135j.apps.googleusercontent.com
        # Client Secret: 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
        self._client_id_input.setText(
            "681255809395-oo8ft2oprdrnp9e3aqf6av3hmdib135j.apps.googleusercontent.com"
        )
        self._client_secret_input.setText("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")

        if not self._name_input.text():
            self._name_input.setText("Gemini Default App")

        # Select Gemini AI scope by default
        if "gemini_ai" in self._scope_checkboxes:
            self._scope_checkboxes["gemini_ai"].setChecked(True)

        self._update_status("Loaded default Gemini App credentials", success=True)

    def _on_load_file(self) -> None:
        """Load credentials from JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load OAuth Credentials",
            "",
            "JSON Files (*.json);;All Files (*)",
        )

        if not file_path:
            return

        try:
            with open(file_path) as f:
                data = json.load(f)

            # Handle both formats: direct and nested under "installed" or "web"
            creds = data
            if "installed" in data:
                creds = data["installed"]
            elif "web" in data:
                creds = data["web"]

            client_id = creds.get("client_id", "")
            client_secret = creds.get("client_secret", "")

            if not client_id or not client_secret:
                QMessageBox.warning(
                    self,
                    "Invalid File",
                    "The selected file does not contain valid OAuth credentials.\n"
                    "Please download a credentials.json file from Google Cloud Console.",
                )
                return

            self._client_id_input.setText(client_id)
            self._client_secret_input.setText(client_secret)

            # Auto-populate name from file
            if not self._name_input.text():
                file_name = Path(file_path).stem
                self._name_input.setText(f"Google - {file_name}")

            self._update_status("Credentials loaded from file", success=True)

        except json.JSONDecodeError:
            QMessageBox.warning(
                self,
                "Invalid JSON",
                "The selected file is not valid JSON.",
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to load credentials: {e}",
            )

    def _get_selected_scopes(self) -> list[str]:
        """Get list of selected OAuth scopes."""
        scopes = []
        for scope_key, checkbox in self._scope_checkboxes.items():
            if checkbox.isChecked():
                scopes.append(GOOGLE_SCOPES[scope_key]["scope"])
        return scopes

    def _validate_inputs(self) -> bool:
        """Validate all inputs before authorization."""
        if not self._name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a credential name.")
            self._name_input.setFocus()
            return False

        if not self._client_id_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a Client ID.")
            self._client_id_input.setFocus()
            return False

        if not self._client_secret_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a Client Secret.")
            self._client_secret_input.setFocus()
            return False

        if not self._get_selected_scopes():
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please select at least one permission scope.",
            )
            return False

        return True

    def _is_cloud_mode(self) -> bool:
        """Check if cloud mode is selected."""
        return self._cloud_radio.isChecked()

    def _start_authorization(self) -> None:
        """Start the OAuth authorization flow."""
        if not self._validate_inputs():
            return

        self._authorize_btn.setEnabled(False)
        self._progress_bar.setVisible(True)
        self._update_status("Starting authorization...")

        if self._is_cloud_mode():
            self._start_cloud_authorization()
        else:
            self._start_local_authorization()

    def _start_local_authorization(self) -> None:
        """Start OAuth authorization using local server."""
        try:
            from casare_rpa.infrastructure.security.oauth_server import (
                LocalOAuthServer,
                build_google_auth_url,
                generate_pkce_pair,
            )

            # Start local OAuth server
            self._oauth_server = LocalOAuthServer()
            self._oauth_server.start()
            redirect_uri = self._oauth_server.redirect_uri
            state = self._oauth_server.state

            # Store for token exchange
            self._current_redirect_uri = redirect_uri

            # Generate PKCE pair
            self._pkce_verifier, code_challenge = generate_pkce_pair()

            client_id = self._client_id_input.text().strip()
            scopes = self._get_selected_scopes()

            # Build authorization URL
            auth_url = build_google_auth_url(
                client_id=client_id,
                redirect_uri=redirect_uri,
                scopes=scopes,
                state=state,
                access_type="offline",
                prompt="consent",
                code_challenge=code_challenge,
                code_challenge_method="S256",
            )

            self._update_status("Opening browser for authorization...")

            # Open browser
            webbrowser.open(auth_url)

            self._update_status("Waiting for authorization... (check your browser)")
            self._waiting_for_callback = True

            # Wait for callback in background
            asyncio.get_event_loop().create_task(self._wait_for_local_callback())

        except Exception as e:
            logger.error(f"Failed to start local authorization: {e}")
            self._update_status(f"Error: {e}", error=True)
            self._authorize_btn.setEnabled(True)
            self._progress_bar.setVisible(False)

            if self._oauth_server:
                self._oauth_server.stop()
                self._oauth_server = None

    def _start_cloud_authorization(self) -> None:
        """Start OAuth authorization using cloud server (api.casare.net)."""
        try:
            from casare_rpa.infrastructure.security.oauth_server import (
                build_google_auth_url,
                generate_oauth_state,
                generate_pkce_pair,
                get_cloud_redirect_uri,
            )

            redirect_uri = get_cloud_redirect_uri()
            state = generate_oauth_state()

            # Store for token exchange and polling
            self._current_redirect_uri = redirect_uri
            self._current_state = state

            # Generate PKCE pair
            self._pkce_verifier, code_challenge = generate_pkce_pair()

            client_id = self._client_id_input.text().strip()
            scopes = self._get_selected_scopes()

            # Build authorization URL
            auth_url = build_google_auth_url(
                client_id=client_id,
                redirect_uri=redirect_uri,
                scopes=scopes,
                state=state,
                access_type="offline",
                prompt="consent",
                code_challenge=code_challenge,
                code_challenge_method="S256",
            )

            self._update_status("Opening browser for authorization...")

            # Open browser
            webbrowser.open(auth_url)

            self._update_status("Waiting for authorization via api.casare.net...")
            self._waiting_for_callback = True

            # Poll for callback in background
            asyncio.get_event_loop().create_task(self._wait_for_cloud_callback())

        except Exception as e:
            logger.error(f"Failed to start cloud authorization: {e}")
            self._update_status(f"Error: {e}", error=True)
            self._authorize_btn.setEnabled(True)
            self._progress_bar.setVisible(False)

    async def _wait_for_local_callback(self) -> None:
        """Wait for OAuth callback from local server asynchronously."""
        try:
            auth_code, error = await self._oauth_server.wait_for_callback(timeout=300.0)

            if error:
                self._on_auth_error(error)
                return

            if auth_code:
                self._on_auth_code_received(auth_code)

        except Exception as e:
            self._on_auth_error(str(e))
        finally:
            self._waiting_for_callback = False
            if self._oauth_server:
                self._oauth_server.stop()
                self._oauth_server = None

    async def _wait_for_cloud_callback(self) -> None:
        """Wait for OAuth callback from cloud server by polling."""
        try:
            from casare_rpa.infrastructure.security.oauth_server import (
                poll_for_cloud_auth_code,
            )

            auth_code, error = await poll_for_cloud_auth_code(
                state=self._current_state,
                timeout=300.0,
                poll_interval=2.0,
            )

            if error:
                self._on_auth_error(error)
                return

            if auth_code:
                self._on_auth_code_received(auth_code)

        except Exception as e:
            self._on_auth_error(str(e))
        finally:
            self._waiting_for_callback = False

    def _on_auth_code_received(self, auth_code: str) -> None:
        """Handle received authorization code."""
        self._update_status("Authorization code received, exchanging for tokens...")

        client_id = self._client_id_input.text().strip()
        client_secret = self._client_secret_input.text().strip()
        scopes = self._get_selected_scopes()

        # Use stored redirect URI (works for both local and cloud modes)
        redirect_uri = getattr(self, "_current_redirect_uri", None)
        if not redirect_uri and self._oauth_server:
            redirect_uri = self._oauth_server.redirect_uri

        # Exchange code for tokens in background thread
        self._oauth_thread = OAuthThread(
            client_id=client_id,
            client_secret=client_secret,
            auth_code=auth_code,
            redirect_uri=redirect_uri,
            scopes=scopes,
            code_verifier=self._pkce_verifier,
            parent=self,
        )
        self._oauth_thread.finished.connect(self._on_token_exchange_complete)
        self._oauth_thread.progress.connect(self._update_status)
        self._oauth_thread.start()

    def _on_token_exchange_complete(
        self, success: bool, message: str, token_data: dict[str, Any] | None
    ) -> None:
        """Handle token exchange completion."""
        self._progress_bar.setVisible(False)

        if not success:
            self._on_auth_error(message)
            return

        self._update_status(message, success=True)

        # Save credential to store
        try:
            from casare_rpa.infrastructure.security.credential_store import (
                get_credential_store,
            )

            store = get_credential_store()

            client_id = self._client_id_input.text().strip()
            client_secret = self._client_secret_input.text().strip()

            credential_id = store.save_google_oauth(
                name=self._name_input.text().strip(),
                client_id=client_id,
                client_secret=client_secret,
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                scopes=token_data["scopes"],
                token_expiry=token_data.get("token_expiry"),
                user_email=token_data.get("user_email"),
                description="Created via OAuth flow",
            )

            logger.info(f"Google OAuth credential saved: {credential_id}")

            # Show success message
            user_email = token_data.get("user_email", "")
            email_info = f" ({user_email})" if user_email else ""

            QMessageBox.information(
                self,
                "Success",
                f"Google account connected successfully{email_info}!\n\n"
                f"Credential saved as: {self._name_input.text().strip()}",
            )

            self.credential_created.emit(credential_id)
            self.accept()

        except Exception as e:
            logger.error(f"Failed to save credential: {e}")
            self._on_auth_error(f"Failed to save credential: {e}")

    def _on_auth_error(self, error: str) -> None:
        """Handle authorization error."""
        self._update_status(f"Error: {error}", error=True)
        self._authorize_btn.setEnabled(True)
        self._progress_bar.setVisible(False)

        QMessageBox.warning(
            self,
            "Authorization Failed",
            f"Failed to authorize with Google:\n\n{error}",
        )

    def _update_status(self, message: str, success: bool = False, error: bool = False) -> None:
        """Update status label with appropriate styling."""
        self._status_label.setText(message)

        if error:
            self._status_label.setStyleSheet(f"color: {THEME.status_error};")
        elif success:
            self._status_label.setStyleSheet(f"color: {THEME.status_success};")
        else:
            self._status_label.setStyleSheet(f"color: {THEME.accent_primary};")

    def _apply_styles(self) -> None:
        """Apply dark theme styles."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {THEME.bg_darkest};
                color: {THEME.text_primary};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radii.md}px;
                margin-top: {TOKENS.spacing.sm}px;
                padding-top: {TOKENS.spacing.lg}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {TOKENS.spacing.md}px;
                padding: 0 {TOKENS.spacing.xs}px;
                color: {THEME.text_primary};
            }}
            QLineEdit {{
                background-color: {THEME.bg_medium};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radii.md}px;
                padding: {TOKENS.spacing.sm}px;
                color: {THEME.text_primary};
            }}
            QLineEdit:focus {{
                border: 1px solid {THEME.border_focus};
            }}
            QPushButton {{
                background-color: {THEME.bg_medium};
                color: {THEME.text_primary};
                border: none;
                padding: {TOKENS.spacing.sm}px {TOKENS.spacing.md}px;
                border-radius: {TOKENS.radii.md}px;
            }}
            QPushButton:hover {{
                background-color: {THEME.bg_hover};
            }}
            QPushButton:pressed {{
                background-color: {THEME.bg_dark};
            }}
            QPushButton:disabled {{
                background-color: {THEME.bg_medium};
                color: {THEME.text_disabled};
            }}
            QCheckBox {{
                color: {THEME.text_primary};
                spacing: {TOKENS.spacing.sm}px;
            }}
            QCheckBox::indicator {{
                width: {TOKENS.sizes.checkbox_size}px;
                height: {TOKENS.sizes.checkbox_size}px;
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radii.sm}px;
                background: {THEME.bg_medium};
            }}
            QCheckBox::indicator:checked {{
                background: {THEME.accent_primary};
                border-color: {THEME.accent_primary};
            }}
            QCheckBox::indicator:hover {{
                border-color: {THEME.border_focus};
            }}
            QRadioButton {{
                color: {THEME.text_primary};
                spacing: {TOKENS.spacing.sm}px;
            }}
            QRadioButton::indicator {{
                width: {TOKENS.sizes.checkbox_size}px;
                height: {TOKENS.sizes.checkbox_size}px;
                border: 2px solid {THEME.border};
                border-radius: {TOKENS.sizes.checkbox_size // 2}px;
                background: {THEME.bg_medium};
            }}
            QRadioButton::indicator:checked {{
                background: {THEME.accent_primary};
                border-color: {THEME.accent_primary};
            }}
            QRadioButton::indicator:hover {{
                border-color: {THEME.border_focus};
            }}
            QScrollArea {{
                background: {THEME.bg_dark};
            }}
            QProgressBar {{
                background-color: {THEME.bg_medium};
                border: none;
                border-radius: {TOKENS.radii.sm}px;
            }}
            QProgressBar::chunk {{
                background-color: {THEME.accent_primary};
                border-radius: {TOKENS.radii.sm}px;
            }}
            QLabel {{
                color: {THEME.text_primary};
            }}
        """)

    def closeEvent(self, event) -> None:
        """Handle dialog close."""
        # Stop OAuth server if running
        if self._oauth_server:
            self._oauth_server.stop()
            self._oauth_server = None

        super().closeEvent(event)


__all__ = ["GoogleOAuthDialog", "GOOGLE_SCOPES"]
