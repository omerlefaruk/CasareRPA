"""
Google OAuth Flow Dialog for CasareRPA.

Provides a dialog for authenticating with Google OAuth 2.0:
- Credential name input
- Load from credentials.json file
- Client ID and Client Secret inputs (with show/hide toggle)
- Scope selection checkboxes
- Authorization flow via browser
- Token exchange and credential storage

Epic 7.x - Migrated to THEME_V2/TOKENS_V2 (kept QDialog due to dynamic button states).
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

# Import scopes from google_client
from casare_rpa.infrastructure.resources.google_client import GoogleScope
from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2

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


from casare_rpa.presentation.canvas.ui.dialogs_v2 import BaseDialogV2, DialogSizeV2


class GoogleOAuthDialog(BaseDialogV2):
    """
    Google OAuth 2.0 authorization dialog.

    Features:
    - Credential name and client ID/secret inputs
    - Load credentials from JSON file
    - Scope selection with checkboxes
    - OAuth authorization flow via browser
    - Token exchange and storage

    Migrated to BaseDialogV2 (Epic 7.x).

    Signals:
        credential_created: Emitted when a credential is successfully created (credential_id)
    """

    credential_created = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            title="Add Google Account",
            parent=parent,
            size=DialogSizeV2.LG,  # Slightly larger for scopes list
            resizable=True,
        )

        self._oauth_server = None
        self._oauth_thread: OAuthThread | None = None
        self._waiting_for_callback = False
        self._current_redirect_uri: str | None = None
        self._current_state: str | None = None
        self._pkce_verifier: str | None = None

        # Create content widget
        content = QWidget()
        self._setup_ui(content)
        self.set_body_widget(content)

        # Set footer actions
        self.set_primary_button("Authorize & Add Account", self._start_authorization)
        self.set_secondary_button("Cancel", self.reject)

        self._apply_styles()
        self._connect_signals()

        logger.debug("GoogleOAuthDialog opened")

    def _setup_ui(self, content: QWidget) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(content)
        layout.setSpacing(TOKENS_V2.spacing.lg)
        layout.setContentsMargins(TOKENS_V2.margin.dialog)

        # Description (Header label removed as it is in title bar)
        description = QLabel(
            "Enter your Google Cloud OAuth credentials to connect your Google account. "
            "You can load credentials from a JSON file downloaded from Google Cloud Console."
        )
        description.setWordWrap(True)
        description.setStyleSheet(
            f"color: {THEME_V2.text_secondary}; margin-bottom: {TOKENS_V2.spacing.sm}px;"
        )
        layout.addWidget(description)

        # Credential Name
        name_group = QGroupBox("Credential Name")
        self._style_group_box(name_group)
        name_layout = QFormLayout(name_group)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("e.g., My Google Account")
        self._style_line_edit(self._name_input)
        name_layout.addRow("Name:", self._name_input)

        layout.addWidget(name_group)

        # Client Credentials
        creds_group = QGroupBox("OAuth Credentials")
        self._style_group_box(creds_group)
        creds_layout = QVBoxLayout(creds_group)

        # Load from file button
        file_layout = QHBoxLayout()
        self._load_file_btn = QPushButton("Load from credentials.json")
        self._style_button_secondary(self._load_file_btn)
        self._load_file_btn.setToolTip(
            "Load client ID and secret from a credentials.json file "
            "downloaded from Google Cloud Console"
        )
        file_layout.addWidget(self._load_file_btn)

        # Use Default Gemini App button
        self._use_default_creds_btn = QPushButton("Use Default Gemini App")
        self._style_button_secondary(self._use_default_creds_btn)
        self._use_default_creds_btn.setToolTip(
            "Use the built-in Gemini CLI credentials (easiest for testing)"
        )
        file_layout.addWidget(self._use_default_creds_btn)

        file_layout.addStretch()
        creds_layout.addLayout(file_layout)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {THEME_V2.border};")
        creds_layout.addWidget(separator)

        # Client ID
        form_layout = QFormLayout()

        self._client_id_input = QLineEdit()
        self._client_id_input.setPlaceholderText("Enter Client ID...")
        self._style_line_edit(self._client_id_input)
        form_layout.addRow("Client ID:", self._client_id_input)

        # Client Secret with show/hide
        secret_layout = QHBoxLayout()
        self._client_secret_input = QLineEdit()
        self._client_secret_input.setPlaceholderText("Enter Client Secret...")
        self._client_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._style_line_edit(self._client_secret_input)
        secret_layout.addWidget(self._client_secret_input)

        self._show_secret_btn = QPushButton("Show")
        self._show_secret_btn.setCheckable(True)
        self._show_secret_btn.setMinimumWidth(60)
        self._style_button_secondary(self._show_secret_btn)
        secret_layout.addWidget(self._show_secret_btn)

        form_layout.addRow("Client Secret:", secret_layout)
        creds_layout.addLayout(form_layout)

        layout.addWidget(creds_group)

        # OAuth Mode Selection
        mode_group = QGroupBox("Redirect Mode")
        self._style_group_box(mode_group)
        mode_layout = QVBoxLayout(mode_group)

        mode_description = QLabel("Choose where Google should redirect after authorization:")
        mode_description.setStyleSheet(
            f"color: {THEME_V2.text_secondary}; margin-bottom: {TOKENS_V2.spacing.sm}px;"
        )
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
            f"color: {THEME_V2.text_secondary}; font-family: monospace; font-size: {TOKENS_V2.typography.sm}px;"
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
            f"color: {THEME_V2.text_secondary}; font-family: monospace; font-size: {TOKENS_V2.typography.sm}px;"
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
        mode_note.setStyleSheet(
            f"color: {THEME_V2.text_disabled}; font-size: {TOKENS_V2.typography.sm}px; margin-top: {TOKENS_V2.spacing.sm}px;"
        )
        mode_layout.addWidget(mode_note)

        layout.addWidget(mode_group)

        # Scope Selection
        scope_group = QGroupBox("Permissions (Scopes)")
        self._style_group_box(scope_group)
        scope_layout = QVBoxLayout(scope_group)

        scope_description = QLabel("Select the permissions your workflow needs:")
        scope_description.setStyleSheet(
            f"color: {THEME_V2.text_secondary}; margin-bottom: {TOKENS_V2.spacing.sm}px;"
        )
        scope_layout.addWidget(scope_description)

        # Scrollable scope area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(TOKENS_V2.sizes.dialog_height_sm)
        scroll_area.setStyleSheet(
            f"QScrollArea {{ border: 1px solid {THEME_V2.border}; background: {THEME_V2.bg_component}; }}"
        )

        scope_container = QWidget()
        scope_grid = QGridLayout(scope_container)
        scope_grid.setSpacing(TOKENS_V2.spacing.sm)

        self._scope_checkboxes: dict[str, QCheckBox] = {}
        row = 0
        col = 0

        for scope_key, scope_info in GOOGLE_SCOPES.items():
            checkbox = QCheckBox(scope_info["label"])
            checkbox.setStyleSheet(f"color: {THEME_V2.text_primary};")
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
        self._style_group_box(status_group)
        status_layout = QVBoxLayout(status_group)

        self._status_label = QLabel("Ready to authorize")
        self._status_label.setStyleSheet(f"color: {THEME_V2.text_secondary};")
        status_layout.addWidget(self._status_label)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)  # Indeterminate
        self._progress_bar.setVisible(False)
        self._progress_bar.setFixedHeight(TOKENS_V2.sizes.progress_height)
        self._style_progress_bar(self._progress_bar)
        status_layout.addWidget(self._progress_bar)

        layout.addWidget(status_group)

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self._load_file_btn.clicked.connect(self._on_load_file)
        self._use_default_creds_btn.clicked.connect(self._on_use_default_creds)
        self._show_secret_btn.toggled.connect(self._toggle_secret_visibility)

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
            self._status_label.setStyleSheet(f"color: {THEME_V2.error};")
        elif success:
            self._status_label.setStyleSheet(f"color: {THEME_V2.success};")
        else:
            self._status_label.setStyleSheet(f"color: {THEME_V2.text_secondary};")

    def _apply_styles(self) -> None:
        """Apply v2 theme styles."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {THEME_V2.bg_surface};
                color: {THEME_V2.text_primary};
            }}
            QLabel {{
                color: {THEME_V2.text_primary};
            }}
            QRadioButton {{
                color: {THEME_V2.text_primary};
                spacing: {TOKENS_V2.spacing.sm}px;
            }}
            QRadioButton::indicator {{
                width: {TOKENS_V2.sizes.checkbox_size}px;
                height: {TOKENS_V2.sizes.checkbox_size}px;
                border: 2px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.sizes.checkbox_size // 2}px;
                background: {THEME_V2.bg_component};
            }}
            QRadioButton::indicator:checked {{
                background: {THEME_V2.accent_base};
                border-color: {THEME_V2.accent_base};
            }}
            QRadioButton::indicator:hover {{
                border-color: {THEME_V2.border_focus};
            }}
        """)

    def _style_group_box(self, group: QGroupBox) -> None:
        """Apply v2 styling to group box."""
        group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                margin-top: {TOKENS_V2.spacing.md}px;
                padding-top: {TOKENS_V2.spacing.md}px;
                font-weight: bold;
                color: {THEME_V2.text_primary};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {TOKENS_V2.spacing.md}px;
                padding: 0 {TOKENS_V2.spacing.xs}px;
            }}
        """)

    def _style_line_edit(self, edit: QLineEdit) -> None:
        """Apply v2 styling to line edit."""
        edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME_V2.bg_component};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                padding: {TOKENS_V2.spacing.sm}px;
                color: {THEME_V2.text_primary};
            }}
            QLineEdit:focus {{
                border-color: {THEME_V2.border_focus};
            }}
        """)

    def _style_button_secondary(self, button: QPushButton) -> None:
        """Apply v2 secondary button styling."""
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME_V2.bg_component};
                color: {THEME_V2.text_primary};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                padding: {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.md}px;
            }}
            QPushButton:hover {{
                background-color: {THEME_V2.bg_hover};
                border-color: {THEME_V2.accent_base};
            }}
            QPushButton:pressed {{
                background-color: {THEME_V2.bg_selected};
            }}
            QPushButton:disabled {{
                background-color: {THEME_V2.bg_component};
                color: {THEME_V2.text_disabled};
                border-color: {THEME_V2.border};
            }}
        """)

    def _style_button_google(self, button: QPushButton) -> None:
        """Apply Google brand button styling."""
        # Using a blue similar to Google's brand
        google_blue = "#4285F4"
        google_blue_hover = "#3367D6"
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {google_blue};
                color: white;
                font-weight: bold;
                font-size: {TOKENS_V2.typography.body}px;
                border: none;
                border-radius: {TOKENS_V2.radius.sm}px;
                padding: {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.lg}px;
            }}
            QPushButton:hover {{
                background-color: {google_blue_hover};
            }}
            QPushButton:pressed {{
                background-color: {google_blue};
            }}
            QPushButton:disabled {{
                background-color: {THEME_V2.border};
                color: {THEME_V2.text_disabled};
            }}
        """)

    def _style_progress_bar(self, bar: QProgressBar) -> None:
        """Apply v2 styling to progress bar."""
        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {THEME_V2.bg_component};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
            }}
            QProgressBar::chunk {{
                background-color: {THEME_V2.accent_base};
                border-radius: {TOKENS_V2.radius.sm}px;
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

