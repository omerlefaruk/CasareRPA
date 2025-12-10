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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

from PySide6.QtCore import Qt, Signal, QThread, QObject
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QCheckBox,
    QFileDialog,
    QMessageBox,
    QWidget,
    QProgressBar,
    QScrollArea,
    QGridLayout,
    QFrame,
    QRadioButton,
    QButtonGroup,
)

from loguru import logger

# Import scopes from google_client
from casare_rpa.infrastructure.resources.google_client import SCOPES, GoogleScope


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
        scopes: List[str],
    ) -> None:
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_code = auth_code
        self.redirect_uri = redirect_uri
        self.scopes = scopes

    def run(self) -> None:
        """Exchange authorization code for tokens."""
        try:
            self.progress.emit("Exchanging authorization code for tokens...")

            import httpx

            data = {
                "grant_type": "authorization_code",
                "code": self.auth_code,
                "redirect_uri": self.redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    "https://oauth2.googleapis.com/token",
                    data=data,
                )
                result = response.json()

            if "error" in result:
                error_desc = result.get("error_description", result["error"])
                self.finished.emit(False, f"Token exchange failed: {error_desc}", None)
                return

            # Calculate token expiry
            expires_in = result.get("expires_in", 3600)
            token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

            token_data = {
                "access_token": result["access_token"],
                "refresh_token": result.get("refresh_token", ""),
                "token_expiry": token_expiry.isoformat(),
                "scopes": self.scopes,
            }

            # Try to get user info
            self.progress.emit("Fetching user information...")
            try:
                headers = {"Authorization": f"Bearer {result['access_token']}"}
                user_response = client.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers=headers,
                )
                if user_response.status_code == 200:
                    user_info = user_response.json()
                    token_data["user_email"] = user_info.get("email", "")
            except Exception as e:
                logger.debug(f"Could not fetch user info: {e}")

            self.finished.emit(True, "Authorization successful!", token_data)

        except Exception as e:
            logger.error(f"OAuth token exchange error: {e}")
            self.finished.emit(False, f"Error: {str(e)}", None)


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
        scopes: List[str],
        parent=None,
    ):
        super().__init__(parent)
        self._worker = OAuthWorker(
            client_id, client_secret, auth_code, redirect_uri, scopes
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

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._oauth_server = None
        self._oauth_thread: Optional[OAuthThread] = None
        self._waiting_for_callback = False
        self._current_redirect_uri: Optional[str] = None
        self._current_state: Optional[str] = None

        self.setWindowTitle("Add Google Account")
        self.setMinimumWidth(550)
        self.setMinimumHeight(600)
        self.setModal(True)

        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

        logger.debug("GoogleOAuthDialog opened")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_label = QLabel("Connect Google Account")
        header_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #e0e0e0;"
        )
        layout.addWidget(header_label)

        description = QLabel(
            "Enter your Google Cloud OAuth credentials to connect your Google account. "
            "You can load credentials from a JSON file downloaded from Google Cloud Console."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #888888; margin-bottom: 10px;")
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
        file_layout.addStretch()
        creds_layout.addLayout(file_layout)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #3c3c3c;")
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
        self._show_secret_btn.setFixedWidth(60)
        secret_layout.addWidget(self._show_secret_btn)

        form_layout.addRow("Client Secret:", secret_layout)
        creds_layout.addLayout(form_layout)

        layout.addWidget(creds_group)

        # OAuth Mode Selection
        mode_group = QGroupBox("Redirect Mode")
        mode_layout = QVBoxLayout(mode_group)

        mode_description = QLabel(
            "Choose where Google should redirect after authorization:"
        )
        mode_description.setStyleSheet("color: #888888; margin-bottom: 8px;")
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
            "color: #888888; font-family: monospace; font-size: 11px;"
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
            "color: #888888; font-family: monospace; font-size: 11px;"
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
        mode_note.setStyleSheet("color: #666666; font-size: 11px; margin-top: 8px;")
        mode_layout.addWidget(mode_note)

        layout.addWidget(mode_group)

        # Scope Selection
        scope_group = QGroupBox("Permissions (Scopes)")
        scope_layout = QVBoxLayout(scope_group)

        scope_description = QLabel("Select the permissions your workflow needs:")
        scope_description.setStyleSheet("color: #888888; margin-bottom: 8px;")
        scope_layout.addWidget(scope_description)

        # Scrollable scope area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(200)
        scroll_area.setStyleSheet(
            "QScrollArea { border: 1px solid #3c3c3c; background: #252526; }"
        )

        scope_container = QWidget()
        scope_grid = QGridLayout(scope_container)
        scope_grid.setSpacing(8)

        self._scope_checkboxes: Dict[str, QCheckBox] = {}
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
        self._status_label.setStyleSheet("color: #888888;")
        status_layout.addWidget(self._status_label)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)  # Indeterminate
        self._progress_bar.setVisible(False)
        self._progress_bar.setMaximumHeight(6)
        status_layout.addWidget(self._progress_bar)

        layout.addWidget(status_group)

        # Buttons
        button_layout = QHBoxLayout()

        self._authorize_btn = QPushButton("Authorize with Google")
        self._authorize_btn.setDefault(True)
        self._authorize_btn.setMinimumHeight(40)
        self._authorize_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285f4;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5a95f5;
            }
            QPushButton:disabled {
                background-color: #2d5a9e;
            }
        """)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setMinimumHeight(40)

        button_layout.addWidget(self._cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(self._authorize_btn)

        layout.addLayout(button_layout)

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self._load_file_btn.clicked.connect(self._on_load_file)
        self._show_secret_btn.toggled.connect(self._toggle_secret_visibility)
        self._authorize_btn.clicked.connect(self._start_authorization)
        self._cancel_btn.clicked.connect(self.reject)

    def _toggle_secret_visibility(self, checked: bool) -> None:
        """Toggle client secret visibility."""
        if checked:
            self._client_secret_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self._show_secret_btn.setText("Hide")
        else:
            self._client_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
            self._show_secret_btn.setText("Show")

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
            with open(file_path, "r") as f:
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

    def _get_selected_scopes(self) -> List[str]:
        """Get list of selected OAuth scopes."""
        scopes = []
        for scope_key, checkbox in self._scope_checkboxes.items():
            if checkbox.isChecked():
                scopes.append(GOOGLE_SCOPES[scope_key]["scope"])
        return scopes

    def _validate_inputs(self) -> bool:
        """Validate all inputs before authorization."""
        if not self._name_input.text().strip():
            QMessageBox.warning(
                self, "Validation Error", "Please enter a credential name."
            )
            self._name_input.setFocus()
            return False

        if not self._client_id_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a Client ID.")
            self._client_id_input.setFocus()
            return False

        if not self._client_secret_input.text().strip():
            QMessageBox.warning(
                self, "Validation Error", "Please enter a Client Secret."
            )
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
            )

            # Start local OAuth server
            self._oauth_server = LocalOAuthServer()
            port = self._oauth_server.start()
            redirect_uri = self._oauth_server.redirect_uri
            state = self._oauth_server.state

            # Store for token exchange
            self._current_redirect_uri = redirect_uri

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
                get_cloud_redirect_uri,
                generate_oauth_state,
            )

            redirect_uri = get_cloud_redirect_uri()
            state = generate_oauth_state()

            # Store for token exchange and polling
            self._current_redirect_uri = redirect_uri
            self._current_state = state

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
            parent=self,
        )
        self._oauth_thread.finished.connect(self._on_token_exchange_complete)
        self._oauth_thread.progress.connect(self._update_status)
        self._oauth_thread.start()

    def _on_token_exchange_complete(
        self, success: bool, message: str, token_data: Optional[Dict[str, Any]]
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

    def _update_status(
        self, message: str, success: bool = False, error: bool = False
    ) -> None:
        """Update status label with appropriate styling."""
        self._status_label.setText(message)

        if error:
            self._status_label.setStyleSheet("color: #f44336;")
        elif success:
            self._status_label.setStyleSheet("color: #4caf50;")
        else:
            self._status_label.setStyleSheet("color: #2196f3;")

    def _apply_styles(self) -> None:
        """Apply dark theme styles."""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #e0e0e0;
            }
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #5c5c5c;
                border-radius: 4px;
                padding: 8px;
                color: #d4d4d4;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #094771;
            }
            QPushButton:disabled {
                background-color: #3c3c3c;
                color: #888888;
            }
            QCheckBox {
                color: #d4d4d4;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #5c5c5c;
                border-radius: 3px;
                background: #3c3c3c;
            }
            QCheckBox::indicator:checked {
                background: #0e639c;
                border-color: #0e639c;
            }
            QCheckBox::indicator:hover {
                border-color: #007acc;
            }
            QRadioButton {
                color: #d4d4d4;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #5c5c5c;
                border-radius: 9px;
                background: #3c3c3c;
            }
            QRadioButton::indicator:checked {
                background: #0e639c;
                border-color: #0e639c;
            }
            QRadioButton::indicator:hover {
                border-color: #007acc;
            }
            QScrollArea {
                background: #252526;
            }
            QProgressBar {
                background-color: #3c3c3c;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #0e639c;
                border-radius: 3px;
            }
            QLabel {
                color: #d4d4d4;
            }
        """)

    def closeEvent(self, event) -> None:
        """Handle dialog close."""
        # Stop OAuth server if running
        if self._oauth_server:
            self._oauth_server.stop()
            self._oauth_server = None

        super().closeEvent(event)


__all__ = ["GoogleOAuthDialog", "GOOGLE_SCOPES"]
