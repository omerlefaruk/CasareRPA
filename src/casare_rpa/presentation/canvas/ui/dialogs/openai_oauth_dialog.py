"""
OpenAI / Generic OAuth Dialog.

Allows adding OAuth 2.0 credentials for OpenAI, Azure OpenAI, or other providers.
"""

from __future__ import annotations

import urllib.parse
import webbrowser
from datetime import UTC, datetime, timedelta

from loguru import logger
from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from casare_rpa.infrastructure.security.oauth_server import LocalOAuthServer
from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS
from casare_rpa.presentation.canvas.theme_system.helpers import (
    set_fixed_height,
    set_margins,
    set_min_size,
    set_spacing,
)


class OAuthExchangeWorker(QObject):
    """Worker to handle code exchange and credential saving in background."""

    finished = Signal(bool, str, str)  # success, message, credential_id

    def __init__(self, config: dict[str, str], code: str, redirect_uri: str):
        super().__init__()
        self.config = config
        self.code = code
        self.redirect_uri = redirect_uri

    def run(self):
        """Execute the token exchange and save credential."""
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success, message, cred_id = loop.run_until_complete(self._process_async())
            self.finished.emit(success, message, cred_id or "")
        except Exception as e:
            logger.error(f"OAuth exchange failed: {e}")
            self.finished.emit(False, str(e), "")
        finally:
            loop.close()

    async def _process_async(self):
        """Async implementation of exchange and save using UnifiedHttpClient."""
        from casare_rpa.infrastructure.http import UnifiedHttpClient, UnifiedHttpClientConfig
        from casare_rpa.infrastructure.security.credential_store import get_credential_store

        client_id = self.config["client_id"]
        client_secret = self.config["client_secret"]
        token_url = self.config["token_url"]

        # Configure client for external OAuth APIs (SSRF protection enabled)
        config = UnifiedHttpClientConfig(
            enable_ssrf_protection=True,
            max_retries=2,
            default_timeout=30.0,
        )

        # 1. Exchange Code for Token
        async with UnifiedHttpClient(config) as http_client:
            data = {
                "grant_type": "authorization_code",
                "code": self.code,
                "redirect_uri": self.redirect_uri,
                "client_id": client_id,
                "client_secret": client_secret,
            }

            # Handle Azure specific resource/scope requirements if needed
            # For now standard OAuth 2.0

            resp = await http_client.post(token_url, data=data)
            if resp.status != TOKENS.sizes.panel_min_width:
                text = await resp.text()
                return False, f"Token exchange failed ({resp.status}): {text}", None

            result = await resp.json()

        # 2. Extract Data
        access_token = result.get("access_token")
        refresh_token = result.get("refresh_token", "")
        expires_in = result.get("expires_in", 3600)

        if not access_token:
            return False, "No access_token in response", None

        # Calculate expiry
        token_expiry = (datetime.now(UTC) + timedelta(seconds=int(expires_in))).isoformat()

        # 3. Save to Store
        store = get_credential_store()

        scopes = result.get("scope", self.config["scopes"]).split(" ")

        cred_id = store.save_openai_oauth(
            name=self.config["name"],
            client_id=client_id,
            client_secret=client_secret,
            authorization_url=self.config["auth_url"],
            token_url=token_url,
            access_token=access_token,
            refresh_token=refresh_token,
            scopes=scopes,
            token_expiry=token_expiry,
            tenant_id=self.config.get("tenant_id"),
            description=f"Created via OAuth flow ({self.config['preset']})",
        )

        return True, "Credential saved successfully!", cred_id


class OpenAIOAuthDialog(QDialog):
    credential_created = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add OAuth Credential (OpenAI/Azure)")
        set_min_size(self, TOKENS.sizes.dialog_md_width, TOKENS.sizes.dialog_height_md)
        self._oauth_server = None
        self._exchange_thread = None

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        set_margins(layout, TOKENS.margin.dialog)
        set_spacing(layout, TOKENS.spacing.md)

        # Name
        form = QFormLayout()
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("e.g. My Azure OpenAI")
        form.addRow("Name:", self._name_input)
        layout.addLayout(form)

        # Provider Preset
        self._preset_combo = QComboBox()
        self._preset_combo.addItems(["Custom", "Azure OpenAI"])
        self._preset_combo.currentTextChanged.connect(self._on_preset_changed)
        layout.addWidget(QLabel("Provider Preset:"))
        layout.addWidget(self._preset_combo)

        # Config
        self._config_group = QGroupBox("Configuration")
        form_config = QFormLayout(self._config_group)

        self._client_id = QLineEdit()
        form_config.addRow("Client ID:", self._client_id)

        self._client_secret = QLineEdit()
        self._client_secret.setEchoMode(QLineEdit.EchoMode.Password)
        form_config.addRow("Client Secret:", self._client_secret)

        self._auth_url = QLineEdit()
        form_config.addRow("Auth URL:", self._auth_url)

        self._token_url = QLineEdit()
        form_config.addRow("Token URL:", self._token_url)

        self._scopes = QLineEdit()
        form_config.addRow("Scopes (space sep):", self._scopes)

        self._tenant_id = QLineEdit()
        self._tenant_id.setPlaceholderText("For Azure (optional)")
        form_config.addRow("Tenant ID:", self._tenant_id)

        layout.addWidget(self._config_group)

        # Status
        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet(f"color: {THEME.text_secondary};")
        layout.addWidget(self._status_label)

        # Buttons
        self._auth_btn = QPushButton("Authorize")
        self._auth_btn.clicked.connect(self._start_auth)
        set_fixed_height(self._auth_btn, TOKENS.sizes.button_lg)
        self._auth_btn.setStyleSheet(
            f"background-color: {THEME.bg_component}; color: {THEME.text_primary}; padding: {TOKENS.spacing.sm}px; font-weight: bold;"
        )
        layout.addWidget(self._auth_btn)

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QDialog {{ background-color: {THEME.bg_canvas}; color: {THEME.text_primary}; }}
            QLineEdit {{ background-color: {THEME.bg_component}; border: 1px solid {THEME.border}; padding: {TOKENS.spacing.xs}px; color: {THEME.text_primary}; }}
            QGroupBox {{ border: 1px solid {THEME.border}; margin-top: {TOKENS.spacing.sm}px; padding-top: {TOKENS.spacing.md}px; font-weight: bold; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: {TOKENS.spacing.md}px; padding: 0 {TOKENS.spacing.xs}px; }}
            QComboBox {{ background-color: {THEME.bg_component}; color: {THEME.text_primary}; border: 1px solid {THEME.border}; padding: {TOKENS.spacing.xs}px; }}
        """)

    def _on_preset_changed(self, text):
        if text == "Azure OpenAI":
            self._auth_url.setText(
                "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
            )
            self._token_url.setText("https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token")
            self._scopes.setText("https://cognitiveservices.azure.com/.default offline_access")
        else:
            self._auth_url.clear()
            self._token_url.clear()
            self._scopes.clear()

    def _start_auth(self):
        name = self._name_input.text().strip()
        client_id = self._client_id.text().strip()
        client_secret = self._client_secret.text().strip()

        if not all([name, client_id, client_secret]):
            QMessageBox.warning(
                self, "Validation Error", "Name, Client ID, and Client Secret are required."
            )
            return

        self._auth_btn.setEnabled(False)
        self._status_label.setText("Starting local server...")

        # 1. Start local server
        try:
            self._oauth_server = LocalOAuthServer()
            self._oauth_server.start()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start local server: {e}")
            self._auth_btn.setEnabled(True)
            return

        # 2. Build URL
        auth_url_template = self._auth_url.text().strip()
        tenant = self._tenant_id.text().strip()

        if "{tenant}" in auth_url_template:
            if not tenant:
                QMessageBox.warning(
                    self, "Validation Error", "Tenant ID is required for this URL format."
                )
                self._auth_btn.setEnabled(True)
                return
            auth_url = auth_url_template.replace("{tenant}", tenant)
        else:
            auth_url = auth_url_template

        params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": self._oauth_server.redirect_uri,
            "scope": self._scopes.text().strip(),
            "state": self._oauth_server.state,
            "access_type": "offline",  # Common for requesting refresh tokens
            "prompt": "consent",
        }

        full_url = f"{auth_url}?{urllib.parse.urlencode(params)}"

        logger.info(f"Opening auth URL: {full_url}")
        webbrowser.open(full_url)
        self._status_label.setText("Waiting for browser authorization...")

        # 3. Wait for code in background
        import threading

        threading.Thread(target=self._wait_for_code_thread, daemon=True).start()

    def _wait_for_code_thread(self):
        """Blocking wait running in a thread."""
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            code, error = loop.run_until_complete(
                self._oauth_server.wait_for_callback(timeout=300.0)
            )
        finally:
            loop.close()
            # Stop server
            if self._oauth_server:
                self._oauth_server.stop()

        # Update UI via meta object or signal is safer, but for now we'll trigger the next step
        # Since we are in a thread, we must not touch UI directly.
        # We will use QMetaObject.invokeMethod pattern or simple signals if self was a QObject
        # self is a QDialog (QObject).
        from PySide6.QtCore import Q_ARG, QMetaObject, Qt

        if code:
            QMetaObject.invokeMethod(
                self, "_on_code_received", Qt.QueuedConnection, Q_ARG(str, code)
            )
        else:
            QMetaObject.invokeMethod(
                self, "_on_auth_failed", Qt.QueuedConnection, Q_ARG(str, error or "Timeout")
            )

    @Slot(str)
    def _on_code_received(self, code):
        self._status_label.setText("Code received. Exchanging for token...")

        # Gather config
        token_url_template = self._token_url.text().strip()
        tenant = self._tenant_id.text().strip()
        token_url = (
            token_url_template.replace("{tenant}", tenant)
            if "{tenant}" in token_url_template
            else token_url_template
        )

        config = {
            "name": self._name_input.text().strip(),
            "client_id": self._client_id.text().strip(),
            "client_secret": self._client_secret.text().strip(),
            "token_url": token_url,
            "auth_url": self._auth_url.text().strip(),  # Store the template or original
            "scopes": self._scopes.text().strip(),
            "tenant_id": tenant,
            "preset": self._preset_combo.currentText(),
        }

        # Start exchange thread (QThread)
        self._exchange_thread = QThread()
        self._worker = OAuthExchangeWorker(config, code, self._oauth_server.redirect_uri)
        self._worker.moveToThread(self._exchange_thread)

        self._exchange_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_exchange_finished)
        self._worker.finished.connect(self._exchange_thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._exchange_thread.finished.connect(self._exchange_thread.deleteLater)

        self._exchange_thread.start()

    @Slot(str)
    def _on_auth_failed(self, error):
        self._status_label.setText(f"Error: {error}")
        QMessageBox.critical(self, "Authorization Failed", str(error))
        self._auth_btn.setEnabled(True)

    @Slot(bool, str, str)
    def _on_exchange_finished(self, success, message, cred_id):
        if success:
            self._status_label.setText("Success!")
            QMessageBox.information(self, "Success", message)
            self.credential_created.emit(cred_id)
            self.accept()
        else:
            self._status_label.setText("Exchange failed.")
            QMessageBox.critical(self, "Token Exchange Failed", message)
            self._auth_btn.setEnabled(True)

    def closeEvent(self, event):
        if self._oauth_server:
            self._oauth_server.stop()
        super().closeEvent(event)
