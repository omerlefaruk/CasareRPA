"""
Credential Manager Dialog UI Component.

Full-featured dialog for managing encrypted credentials:
- API Keys (LLM providers)
- Username/Password pairs
- Database connections
- Custom credentials
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal, QThread, QObject
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from loguru import logger

from casare_rpa.presentation.canvas.ui.dialogs.dialog_styles import (
    DialogStyles,
    DialogSize,
    apply_dialog_style,
    COLORS,
)


class ApiKeyTestWorker(QObject):
    """Worker for testing API keys in a background thread."""

    finished = Signal(bool, str)  # success, message

    def __init__(self, provider: str, api_key: str) -> None:
        super().__init__()
        self.provider = provider
        self.api_key = api_key

    def run(self) -> None:
        """Test the API key by making a minimal API call."""
        try:
            success, message = self._test_provider(self.provider, self.api_key)
            self.finished.emit(success, message)
        except Exception as e:
            self.finished.emit(False, f"Test failed: {str(e)}")

    def _test_provider(self, provider: str, api_key: str) -> tuple[bool, str]:
        """Test API key for specific provider."""
        import httpx

        # Provider-specific test endpoints and headers
        test_configs = {
            "openai": {
                "url": "https://api.openai.com/v1/models",
                "headers": {"Authorization": f"Bearer {api_key}"},
                "method": "GET",
            },
            "anthropic": {
                "url": "https://api.anthropic.com/v1/messages",
                "headers": {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                "method": "POST",
                "body": {
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "Hi"}],
                },
            },
            "google": {
                "url": f"https://generativelanguage.googleapis.com/v1/models?key={api_key}",
                "headers": {},
                "method": "GET",
            },
            "mistral": {
                "url": "https://api.mistral.ai/v1/models",
                "headers": {"Authorization": f"Bearer {api_key}"},
                "method": "GET",
            },
            "groq": {
                "url": "https://api.groq.com/openai/v1/models",
                "headers": {"Authorization": f"Bearer {api_key}"},
                "method": "GET",
            },
            "deepseek": {
                "url": "https://api.deepseek.com/v1/models",
                "headers": {"Authorization": f"Bearer {api_key}"},
                "method": "GET",
            },
            "cohere": {
                "url": "https://api.cohere.ai/v1/models",
                "headers": {"Authorization": f"Bearer {api_key}"},
                "method": "GET",
            },
            "together": {
                "url": "https://api.together.xyz/v1/models",
                "headers": {"Authorization": f"Bearer {api_key}"},
                "method": "GET",
            },
            "perplexity": {
                "url": "https://api.perplexity.ai/chat/completions",
                "headers": {"Authorization": f"Bearer {api_key}"},
                "method": "POST",
                "body": {
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 1,
                },
            },
            "openrouter": {
                "url": "https://openrouter.ai/api/v1/models",
                "headers": {"Authorization": f"Bearer {api_key}"},
                "method": "GET",
            },
            "azure": {
                # Azure requires endpoint configuration, just validate key format
                "skip_request": True,
            },
        }

        config = test_configs.get(provider)
        if not config:
            return False, f"Unknown provider: {provider}"

        if config.get("skip_request"):
            # For providers needing extra config, just validate key exists
            if api_key and len(api_key) > 10:
                return (
                    True,
                    "API key format looks valid. Full test requires endpoint configuration.",
                )
            return False, "API key appears to be invalid (too short)."

        try:
            with httpx.Client(timeout=15.0) as client:
                if config["method"] == "GET":
                    response = client.get(config["url"], headers=config["headers"])
                else:
                    response = client.post(
                        config["url"],
                        headers=config["headers"],
                        json=config.get("body", {}),
                    )

                if response.status_code == 200:
                    return True, "Connection successful! API key is valid."
                elif response.status_code == 401:
                    return False, "Authentication failed. Invalid API key."
                elif response.status_code == 403:
                    return False, "Access forbidden. Check API key permissions."
                elif response.status_code == 429:
                    return True, "API key valid (rate limited - try again later)."
                else:
                    # Some APIs return 400 for minimal requests but key is still valid
                    error_text = response.text[:200] if response.text else ""
                    if (
                        "invalid" in error_text.lower()
                        or "unauthorized" in error_text.lower()
                    ):
                        return (
                            False,
                            f"API error ({response.status_code}): {error_text}",
                        )
                    return (
                        True,
                        f"API key appears valid (status: {response.status_code}).",
                    )

        except httpx.ConnectError:
            return False, "Connection failed. Check your internet connection."
        except httpx.TimeoutException:
            return False, "Connection timed out. The API server may be slow."
        except Exception as e:
            return False, f"Test error: {str(e)}"


class ApiKeyTestThread(QThread):
    """Thread for running API key tests."""

    finished = Signal(bool, str)

    def __init__(self, provider: str, api_key: str, parent=None):
        super().__init__(parent)
        self.provider = provider
        self.api_key = api_key
        self._worker = ApiKeyTestWorker(provider, api_key)

    def run(self):
        """Run the test in this thread."""
        self._worker.run()

    def start(self):
        """Start the thread and connect signals."""
        self._worker.finished.connect(self.finished.emit)
        super().start()


class TokenRefreshThread(QThread):
    """Thread for refreshing Google OAuth tokens without blocking Qt."""

    finished = Signal(str)  # Emits new token or empty string on failure
    error = Signal(str)  # Emits error message on failure

    def __init__(self, credential_id: str, parent=None):
        super().__init__(parent)
        self._credential_id = credential_id

    def run(self):
        """Run the token refresh in a separate thread."""
        import asyncio

        try:
            from casare_rpa.infrastructure.security.google_oauth import (
                GoogleOAuthManager,
            )

            async def do_refresh():
                manager = GoogleOAuthManager()
                return await manager.get_access_token(self._credential_id)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                token = loop.run_until_complete(do_refresh())
                self.finished.emit(token or "")
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            self.error.emit(str(e))


class CredentialManagerDialog(QDialog):
    """
    Credential management dialog.

    Features:
    - Add/Edit/Delete credentials
    - Organize by category (LLM, Database, Email, Custom)
    - Secure display (masked values)
    - Search and filter
    - Import/Export (future)

    Signals:
        credentials_changed: Emitted when credentials are modified
    """

    credentials_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize credential manager dialog."""
        super().__init__(parent)

        self._store = None
        self._current_credential_id: Optional[str] = None
        self._test_thread: Optional[ApiKeyTestThread] = None
        self._token_refresh_thread: Optional[TokenRefreshThread] = None

        self.setWindowTitle("Credential Manager")
        self.setModal(True)

        # Apply standardized dialog styling
        apply_dialog_style(self, DialogSize.LG)

        self._setup_ui()
        self._load_credentials()

        logger.debug("CredentialManagerDialog opened")

    def closeEvent(self, event) -> None:
        """Clean up resources when dialog closes."""
        # Stop any running test thread
        if self._test_thread is not None:
            if self._test_thread.isRunning():
                logger.debug("Stopping API test thread on dialog close")
                self._test_thread.quit()
                if not self._test_thread.wait(1000):  # Wait up to 1 second
                    logger.warning(
                        "API test thread did not stop gracefully, terminating"
                    )
                    self._test_thread.terminate()
                    self._test_thread.wait(500)
            self._test_thread = None

        # Stop any running token refresh thread
        if self._token_refresh_thread is not None:
            if self._token_refresh_thread.isRunning():
                logger.debug("Stopping token refresh thread on dialog close")
                self._token_refresh_thread.quit()
                if not self._token_refresh_thread.wait(1000):  # Wait up to 1 second
                    logger.warning(
                        "Token refresh thread did not stop gracefully, terminating"
                    )
                    self._token_refresh_thread.terminate()
                    self._token_refresh_thread.wait(500)
            self._token_refresh_thread = None

        super().closeEvent(event)

    def _get_store(self):
        """Lazy-load the credential store."""
        if self._store is None:
            from casare_rpa.infrastructure.security.credential_store import (
                get_credential_store,
            )

            self._store = get_credential_store()
        return self._store

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Create tab widget for categories
        self._tabs = QTabWidget()

        # API Keys tab
        api_tab = self._create_api_keys_tab()
        self._tabs.addTab(api_tab, "API Keys")

        # Username/Password tab
        userpass_tab = self._create_userpass_tab()
        self._tabs.addTab(userpass_tab, "Logins")

        # Google Accounts tab
        google_tab = self._create_google_accounts_tab()
        self._tabs.addTab(google_tab, "Google Accounts")

        # All Credentials tab
        all_tab = self._create_all_credentials_tab()
        self._tabs.addTab(all_tab, "All Credentials")

        layout.addWidget(self._tabs)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.accept)
        layout.addWidget(button_box)

    def _create_api_keys_tab(self) -> QWidget:
        """Create API Keys management tab."""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Left panel - provider list
        left_panel = QVBoxLayout()

        provider_label = QLabel("LLM Providers")
        provider_label.setStyleSheet(DialogStyles.header(font_size=14))
        left_panel.addWidget(provider_label)

        self._api_provider_list = QListWidget()
        self._api_provider_list.setMaximumWidth(200)
        self._api_provider_list.itemClicked.connect(self._on_api_provider_selected)

        # Add providers
        providers = [
            ("OpenAI", "openai"),
            ("Anthropic", "anthropic"),
            ("Azure OpenAI", "azure"),
            ("Google AI", "google"),
            ("Mistral", "mistral"),
            ("Groq", "groq"),
            ("DeepSeek", "deepseek"),
            ("Cohere", "cohere"),
            ("Together AI", "together"),
            ("Perplexity", "perplexity"),
            ("OpenRouter", "openrouter"),
        ]
        for display_name, provider_id in providers:
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, provider_id)
            self._api_provider_list.addItem(item)

        left_panel.addWidget(self._api_provider_list)
        layout.addLayout(left_panel)

        # Right panel - API key form
        right_panel = QVBoxLayout()

        self._api_form_group = QGroupBox("API Key Configuration")
        form_layout = QFormLayout()

        self._api_provider_label = QLabel("Select a provider")
        self._api_provider_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        form_layout.addRow(self._api_provider_label)

        self._api_key_input = QLineEdit()
        self._api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_input.setPlaceholderText("Enter API key...")
        form_layout.addRow("API Key:", self._api_key_input)

        self._api_name_input = QLineEdit()
        self._api_name_input.setPlaceholderText("e.g., Production, Development")
        form_layout.addRow("Name:", self._api_name_input)

        self._api_description = QLineEdit()
        self._api_description.setPlaceholderText("Optional description")
        form_layout.addRow("Description:", self._api_description)

        # Show/Hide button
        show_hide_layout = QHBoxLayout()
        self._api_show_btn = QPushButton("Show")
        self._api_show_btn.setCheckable(True)
        self._api_show_btn.toggled.connect(self._toggle_api_key_visibility)
        show_hide_layout.addWidget(self._api_show_btn)
        show_hide_layout.addStretch()
        form_layout.addRow("", show_hide_layout)

        # Status
        self._api_status_label = QLabel("")
        form_layout.addRow("Status:", self._api_status_label)

        self._api_form_group.setLayout(form_layout)
        right_panel.addWidget(self._api_form_group)

        # Buttons
        btn_layout = QHBoxLayout()
        self._api_save_btn = QPushButton("Save API Key")
        self._api_save_btn.clicked.connect(self._save_api_key)
        btn_layout.addWidget(self._api_save_btn)

        self._api_delete_btn = QPushButton("Delete")
        self._api_delete_btn.clicked.connect(self._delete_api_key)
        btn_layout.addWidget(self._api_delete_btn)

        self._api_test_btn = QPushButton("Test Connection")
        self._api_test_btn.clicked.connect(self._test_api_key)
        btn_layout.addWidget(self._api_test_btn)

        btn_layout.addStretch()
        right_panel.addLayout(btn_layout)
        right_panel.addStretch()

        layout.addLayout(right_panel, 1)

        return widget

    def _create_userpass_tab(self) -> QWidget:
        """Create Username/Password management tab."""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Left panel - credential list
        left_panel = QVBoxLayout()

        list_label = QLabel("Saved Logins")
        list_label.setStyleSheet(DialogStyles.header(font_size=14))
        left_panel.addWidget(list_label)

        self._userpass_list = QListWidget()
        self._userpass_list.setMaximumWidth(250)
        self._userpass_list.itemClicked.connect(self._on_userpass_selected)
        left_panel.addWidget(self._userpass_list)

        # Add new button
        add_btn = QPushButton("+ Add New Login")
        add_btn.clicked.connect(self._add_new_userpass)
        left_panel.addWidget(add_btn)

        layout.addLayout(left_panel)

        # Right panel - form
        right_panel = QVBoxLayout()

        self._userpass_form_group = QGroupBox("Login Credentials")
        form_layout = QFormLayout()

        self._userpass_name_input = QLineEdit()
        self._userpass_name_input.setPlaceholderText("e.g., Database Production")
        form_layout.addRow("Name:", self._userpass_name_input)

        self._userpass_category = QComboBox()
        self._userpass_category.addItems(["database", "email", "application", "custom"])
        form_layout.addRow("Category:", self._userpass_category)

        self._userpass_username = QLineEdit()
        self._userpass_username.setPlaceholderText("Username")
        form_layout.addRow("Username:", self._userpass_username)

        self._userpass_password = QLineEdit()
        self._userpass_password.setEchoMode(QLineEdit.EchoMode.Password)
        self._userpass_password.setPlaceholderText("Password")
        form_layout.addRow("Password:", self._userpass_password)

        # Show/Hide
        show_layout = QHBoxLayout()
        self._userpass_show_btn = QPushButton("Show Password")
        self._userpass_show_btn.setCheckable(True)
        self._userpass_show_btn.toggled.connect(self._toggle_password_visibility)
        show_layout.addWidget(self._userpass_show_btn)
        show_layout.addStretch()
        form_layout.addRow("", show_layout)

        # Extra fields
        self._userpass_host = QLineEdit()
        self._userpass_host.setPlaceholderText("Host/Server (optional)")
        form_layout.addRow("Host:", self._userpass_host)

        self._userpass_port = QLineEdit()
        self._userpass_port.setPlaceholderText("Port (optional)")
        form_layout.addRow("Port:", self._userpass_port)

        self._userpass_description = QLineEdit()
        self._userpass_description.setPlaceholderText("Description (optional)")
        form_layout.addRow("Description:", self._userpass_description)

        self._userpass_form_group.setLayout(form_layout)
        right_panel.addWidget(self._userpass_form_group)

        # Buttons
        btn_layout = QHBoxLayout()
        self._userpass_save_btn = QPushButton("Save")
        self._userpass_save_btn.clicked.connect(self._save_userpass)
        btn_layout.addWidget(self._userpass_save_btn)

        self._userpass_delete_btn = QPushButton("Delete")
        self._userpass_delete_btn.clicked.connect(self._delete_userpass)
        btn_layout.addWidget(self._userpass_delete_btn)

        btn_layout.addStretch()
        right_panel.addLayout(btn_layout)
        right_panel.addStretch()

        layout.addLayout(right_panel, 1)

        return widget

    def _create_google_accounts_tab(self) -> QWidget:
        """Create Google Accounts management tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Connected Google Accounts")
        header_label.setStyleSheet(DialogStyles.header(font_size=16))
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        # Add account button (Google blue)
        self._google_add_btn = QPushButton("+ Add Google Account")
        self._google_add_btn.clicked.connect(self._add_google_account)
        self._google_add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285F4;
                color: white;
                border: none;
                padding: 0 16px;
                border-radius: 4px;
                font-weight: 600;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #5a95f5;
            }
        """)
        header_layout.addWidget(self._google_add_btn)
        layout.addLayout(header_layout)

        # Description
        desc_label = QLabel(
            "Manage your Google accounts for Sheets, Drive, Gmail, Calendar, and Docs integration."
        )
        desc_label.setStyleSheet(DialogStyles.subheader())
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Accounts list
        self._google_accounts_list = QListWidget()
        self._google_accounts_list.setMinimumHeight(200)
        self._google_accounts_list.itemClicked.connect(self._on_google_account_selected)
        layout.addWidget(self._google_accounts_list)

        # Account details panel
        self._google_details_group = QGroupBox("Account Details")
        details_layout = QFormLayout()

        self._google_email_label = QLabel("-")
        details_layout.addRow("Email:", self._google_email_label)

        self._google_scopes_label = QLabel("-")
        self._google_scopes_label.setWordWrap(True)
        details_layout.addRow("Scopes:", self._google_scopes_label)

        self._google_status_label = QLabel("-")
        details_layout.addRow("Status:", self._google_status_label)

        self._google_created_label = QLabel("-")
        details_layout.addRow("Added:", self._google_created_label)

        self._google_details_group.setLayout(details_layout)
        layout.addWidget(self._google_details_group)

        # Action buttons
        btn_layout = QHBoxLayout()

        self._google_refresh_btn = QPushButton("Refresh Token")
        self._google_refresh_btn.clicked.connect(self._refresh_google_token)
        self._google_refresh_btn.setEnabled(False)
        btn_layout.addWidget(self._google_refresh_btn)

        self._google_set_default_btn = QPushButton("Set as Default")
        self._google_set_default_btn.clicked.connect(self._set_google_default)
        self._google_set_default_btn.setEnabled(False)
        btn_layout.addWidget(self._google_set_default_btn)

        self._google_delete_btn = QPushButton("Remove Account")
        self._google_delete_btn.clicked.connect(self._delete_google_account)
        self._google_delete_btn.setEnabled(False)
        self._google_delete_btn.setStyleSheet(DialogStyles.button_danger())
        btn_layout.addWidget(self._google_delete_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()

        # Load accounts
        self._refresh_google_accounts()

        return widget

    def _refresh_google_accounts(self) -> None:
        """Refresh the Google accounts list."""
        self._google_accounts_list.clear()
        store = self._get_store()

        credentials = store.list_google_credentials()
        for cred in credentials:
            # Get additional details
            data = store.get_credential(cred["id"])
            email = data.get("user_email", "Unknown") if data else "Unknown"

            # Create list item
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, cred["id"])

            # Display format: email (name)
            display_text = f"[G] {email}"
            if cred["name"] != email:
                display_text += f" - {cred['name']}"
            item.setText(display_text)

            self._google_accounts_list.addItem(item)

        # Update button states
        has_accounts = self._google_accounts_list.count() > 0
        if not has_accounts:
            self._google_email_label.setText("No accounts connected")
            self._google_scopes_label.setText("-")
            self._google_status_label.setText("-")
            self._google_created_label.setText("-")

    def _on_google_account_selected(self, item: QListWidgetItem) -> None:
        """Handle Google account selection."""
        cred_id = item.data(Qt.ItemDataRole.UserRole)
        self._current_google_id = cred_id

        store = self._get_store()
        info = store.get_credential_info(cred_id)
        data = store.get_credential(cred_id)

        if info and data:
            # Update details
            self._google_email_label.setText(data.get("user_email", "Unknown"))

            # Format scopes nicely
            scopes = data.get("scopes", [])
            if scopes:
                scope_names = []
                for scope in scopes:
                    if "spreadsheets" in scope:
                        scope_names.append("Sheets")
                    elif "drive" in scope:
                        scope_names.append("Drive")
                    elif "gmail" in scope:
                        scope_names.append("Gmail")
                    elif "calendar" in scope:
                        scope_names.append("Calendar")
                    elif "documents" in scope:
                        scope_names.append("Docs")
                self._google_scopes_label.setText(", ".join(set(scope_names)) or "None")
            else:
                self._google_scopes_label.setText("None")

            # Check token status
            token_expiry = data.get("token_expiry")
            if token_expiry:
                from datetime import datetime

                try:
                    expiry = datetime.fromisoformat(token_expiry.replace("Z", "+00:00"))
                    if expiry > datetime.now(expiry.tzinfo):
                        self._google_status_label.setText("Valid")
                        self._google_status_label.setStyleSheet("color: #4CAF50;")
                    else:
                        self._google_status_label.setText("Expired - Click Refresh")
                        self._google_status_label.setStyleSheet("color: #f44336;")
                except Exception:
                    self._google_status_label.setText("Unknown")
                    self._google_status_label.setStyleSheet("color: #ff9800;")
            else:
                self._google_status_label.setText("Unknown")
                self._google_status_label.setStyleSheet("color: #ff9800;")

            self._google_created_label.setText(info.get("created_at", "Unknown")[:10])

            # Enable buttons
            self._google_refresh_btn.setEnabled(True)
            self._google_set_default_btn.setEnabled(True)
            self._google_delete_btn.setEnabled(True)

    def _add_google_account(self) -> None:
        """Open OAuth dialog to add a Google account."""
        try:
            from casare_rpa.presentation.canvas.ui.dialogs.google_oauth_dialog import (
                GoogleOAuthDialog,
            )

            dialog = GoogleOAuthDialog(self)
            dialog.credential_created.connect(self._on_google_credential_created)
            dialog.exec()

        except ImportError as e:
            logger.error(f"Google OAuth dialog not available: {e}")
            QMessageBox.critical(
                self,
                "Error",
                "Google OAuth dialog is not available. Please check your installation.",
            )

    def _on_google_credential_created(self, credential_id: str) -> None:
        """Handle new Google credential creation."""
        self._refresh_google_accounts()
        self._refresh_all_credentials()
        self.credentials_changed.emit()

        QMessageBox.information(
            self,
            "Success",
            "Google account connected successfully!",
        )

    def _refresh_google_token(self) -> None:
        """Refresh the selected Google account's token.

        Uses a background thread to avoid blocking the Qt event loop.
        """
        cred_id = getattr(self, "_current_google_id", None)
        if not cred_id:
            return

        # Don't start another refresh if one is already running
        if (
            self._token_refresh_thread is not None
            and self._token_refresh_thread.isRunning()
        ):
            logger.debug("Token refresh already in progress")
            return

        # Disable button and show refreshing state
        self._google_refresh_btn.setEnabled(False)
        self._google_refresh_btn.setText("Refreshing...")
        self._google_status_label.setText("Refreshing...")
        self._google_status_label.setStyleSheet("color: #2196F3;")

        # Run refresh in background thread
        self._token_refresh_thread = TokenRefreshThread(cred_id, self)
        self._token_refresh_thread.finished.connect(self._on_token_refresh_complete)
        self._token_refresh_thread.error.connect(self._on_token_refresh_error)
        self._token_refresh_thread.start()

    def _on_token_refresh_complete(self, token: str) -> None:
        """Handle token refresh completion."""
        # Re-enable button
        self._google_refresh_btn.setEnabled(True)
        self._google_refresh_btn.setText("Refresh Token")

        if token:
            self._google_status_label.setText("Valid")
            self._google_status_label.setStyleSheet("color: #4CAF50;")
            QMessageBox.information(self, "Success", "Token refreshed successfully!")
        else:
            self._google_status_label.setText("Expired - Needs re-auth")
            self._google_status_label.setStyleSheet("color: #f44336;")
            QMessageBox.warning(
                self,
                "Warning",
                "Could not refresh token. You may need to re-authenticate.",
            )

    def _on_token_refresh_error(self, error_message: str) -> None:
        """Handle token refresh error."""
        # Re-enable button
        self._google_refresh_btn.setEnabled(True)
        self._google_refresh_btn.setText("Refresh Token")

        self._google_status_label.setText("Error")
        self._google_status_label.setStyleSheet("color: #f44336;")
        QMessageBox.critical(self, "Error", f"Failed to refresh token: {error_message}")

    def _set_google_default(self) -> None:
        """Set the selected Google account as default."""
        cred_id = getattr(self, "_current_google_id", None)
        if not cred_id:
            return

        # TODO: Implement default account setting
        # For now, just show a message
        QMessageBox.information(
            self,
            "Info",
            "Default account setting will be implemented in a future update.",
        )

    def _delete_google_account(self) -> None:
        """Delete the selected Google account."""
        cred_id = getattr(self, "_current_google_id", None)
        if not cred_id:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to remove this Google account?\n\n"
            "This will revoke access for all workflows using this account.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            store = self._get_store()
            store.delete_credential(cred_id)
            self._current_google_id = None

            # Reset UI
            self._google_email_label.setText("-")
            self._google_scopes_label.setText("-")
            self._google_status_label.setText("-")
            self._google_created_label.setText("-")
            self._google_refresh_btn.setEnabled(False)
            self._google_set_default_btn.setEnabled(False)
            self._google_delete_btn.setEnabled(False)

            self._refresh_google_accounts()
            self._refresh_all_credentials()
            self.credentials_changed.emit()

    def _create_all_credentials_tab(self) -> QWidget:
        """Create tab showing all credentials."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search credentials...")
        self._search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self._search_input)
        layout.addLayout(search_layout)

        # Credentials list
        self._all_credentials_list = QListWidget()
        self._all_credentials_list.itemDoubleClicked.connect(
            self._on_credential_double_clicked
        )
        layout.addWidget(self._all_credentials_list)

        # Info panel
        self._credential_info = QLabel("Select a credential to view details")
        self._credential_info.setWordWrap(True)
        self._credential_info.setStyleSheet(
            f"background: {COLORS.bg_button}; padding: 10px; border-radius: 4px;"
        )
        layout.addWidget(self._credential_info)

        return widget

    def _load_credentials(self) -> None:
        """Load credentials into the UI."""
        store = self._get_store()

        # Load API keys status
        self._refresh_api_status()

        # Load username/password list
        self._refresh_userpass_list()

        # Load all credentials
        self._refresh_all_credentials()

    def _refresh_api_status(self) -> None:
        """Refresh API key status indicators."""
        # Update status for currently selected provider
        item = self._api_provider_list.currentItem()
        if item:
            self._on_api_provider_selected(item)

    def _refresh_userpass_list(self) -> None:
        """Refresh the username/password list."""
        self._userpass_list.clear()
        store = self._get_store()

        from casare_rpa.infrastructure.security.credential_store import CredentialType

        credentials = store.list_credentials(
            credential_type=CredentialType.USERNAME_PASSWORD
        )
        for cred in credentials:
            item = QListWidgetItem(f"{cred['name']} ({cred['category']})")
            item.setData(Qt.ItemDataRole.UserRole, cred["id"])
            self._userpass_list.addItem(item)

    def _refresh_all_credentials(self) -> None:
        """Refresh the all credentials list."""
        self._all_credentials_list.clear()
        store = self._get_store()

        credentials = store.list_credentials()
        for cred in credentials:
            item = QListWidgetItem(
                f"{cred['name']} [{cred['type']}] - {cred['category']}"
            )
            item.setData(Qt.ItemDataRole.UserRole, cred["id"])
            self._all_credentials_list.addItem(item)

    def _on_api_provider_selected(self, item: QListWidgetItem) -> None:
        """Handle API provider selection."""
        provider = item.data(Qt.ItemDataRole.UserRole)
        display_name = item.text()

        self._api_provider_label.setText(display_name)
        self._current_provider = provider

        # Check if we have a key for this provider
        store = self._get_store()
        credentials = store.list_credentials(category="llm")

        existing_cred = None
        for cred in credentials:
            data = store.get_credential(cred["id"])
            if data and data.get("provider") == provider:
                existing_cred = cred
                break

        if existing_cred:
            self._current_credential_id = existing_cred["id"]
            data = store.get_credential(existing_cred["id"])
            self._api_key_input.setText(data.get("api_key", ""))
            self._api_name_input.setText(existing_cred["name"])
            self._api_description.setText(existing_cred.get("description", ""))
            self._api_status_label.setText("Configured")
            self._api_status_label.setStyleSheet("color: #4CAF50;")
        else:
            self._current_credential_id = None
            self._api_key_input.clear()
            self._api_name_input.setText(f"{display_name} API Key")
            self._api_description.clear()
            self._api_status_label.setText("Not configured")
            self._api_status_label.setStyleSheet("color: #ff9800;")

    def _toggle_api_key_visibility(self, checked: bool) -> None:
        """Toggle API key visibility."""
        if checked:
            self._api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self._api_show_btn.setText("Hide")
        else:
            self._api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self._api_show_btn.setText("Show")

    def _toggle_password_visibility(self, checked: bool) -> None:
        """Toggle password visibility."""
        if checked:
            self._userpass_password.setEchoMode(QLineEdit.EchoMode.Normal)
            self._userpass_show_btn.setText("Hide Password")
        else:
            self._userpass_password.setEchoMode(QLineEdit.EchoMode.Password)
            self._userpass_show_btn.setText("Show Password")

    def _save_api_key(self) -> None:
        """Save API key."""
        api_key = self._api_key_input.text().strip()
        name = self._api_name_input.text().strip()

        if not api_key:
            QMessageBox.warning(self, "Error", "Please enter an API key.")
            return

        if not name:
            QMessageBox.warning(self, "Error", "Please enter a name.")
            return

        store = self._get_store()

        try:
            store.save_credential(
                name=name,
                credential_type=store._credentials.get(
                    self._current_credential_id
                ).credential_type
                if self._current_credential_id
                else __import__(
                    "casare_rpa.infrastructure.security.credential_store",
                    fromlist=["CredentialType"],
                ).CredentialType.API_KEY,
                category="llm",
                data={"api_key": api_key, "provider": self._current_provider},
                description=self._api_description.text().strip(),
                credential_id=self._current_credential_id,
            )

            self._api_status_label.setText("Saved!")
            self._api_status_label.setStyleSheet("color: #4CAF50;")
            self.credentials_changed.emit()

            QMessageBox.information(self, "Success", "API key saved successfully.")
            self._refresh_all_credentials()

        except Exception as e:
            logger.error(f"Failed to save API key: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")

    def _delete_api_key(self) -> None:
        """Delete API key."""
        if not self._current_credential_id:
            QMessageBox.warning(self, "Error", "No API key to delete.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this API key?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            store = self._get_store()
            store.delete_credential(self._current_credential_id)
            self._current_credential_id = None
            self._api_key_input.clear()
            self._api_status_label.setText("Deleted")
            self._api_status_label.setStyleSheet("color: #f44336;")
            self.credentials_changed.emit()
            self._refresh_all_credentials()

    def _test_api_key(self) -> None:
        """Test API key connection."""
        api_key = self._api_key_input.text().strip()
        provider = getattr(self, "_current_provider", None)

        if not api_key:
            QMessageBox.warning(self, "Error", "Please enter an API key to test.")
            return

        if not provider:
            QMessageBox.warning(self, "Error", "Please select a provider first.")
            return

        # Disable button and show testing state
        self._api_test_btn.setEnabled(False)
        self._api_test_btn.setText("Testing...")
        self._api_status_label.setText("Testing connection...")
        self._api_status_label.setStyleSheet("color: #2196F3;")

        # Run test in background thread
        self._test_thread = ApiKeyTestThread(provider, api_key, self)
        self._test_thread.finished.connect(self._on_test_complete)
        self._test_thread.start()

    def _on_test_complete(self, success: bool, message: str) -> None:
        """Handle API key test completion."""
        # Re-enable button
        self._api_test_btn.setEnabled(True)
        self._api_test_btn.setText("Test Connection")

        if success:
            self._api_status_label.setText("Valid")
            self._api_status_label.setStyleSheet("color: #4CAF50;")
            QMessageBox.information(self, "Test Successful", message)
        else:
            self._api_status_label.setText("Invalid")
            self._api_status_label.setStyleSheet("color: #f44336;")
            QMessageBox.warning(self, "Test Failed", message)

    def _on_userpass_selected(self, item: QListWidgetItem) -> None:
        """Handle username/password selection."""
        cred_id = item.data(Qt.ItemDataRole.UserRole)
        self._current_userpass_id = cred_id

        store = self._get_store()
        info = store.get_credential_info(cred_id)
        data = store.get_credential(cred_id)

        if info and data:
            self._userpass_name_input.setText(info["name"])
            self._userpass_category.setCurrentText(info["category"])
            self._userpass_username.setText(data.get("username", ""))
            self._userpass_password.setText(data.get("password", ""))
            self._userpass_host.setText(data.get("host", ""))
            self._userpass_port.setText(data.get("port", ""))
            self._userpass_description.setText(info.get("description", ""))

    def _add_new_userpass(self) -> None:
        """Add new username/password credential."""
        self._current_userpass_id = None
        self._userpass_name_input.clear()
        self._userpass_username.clear()
        self._userpass_password.clear()
        self._userpass_host.clear()
        self._userpass_port.clear()
        self._userpass_description.clear()
        self._userpass_name_input.setFocus()

    def _save_userpass(self) -> None:
        """Save username/password credential."""
        name = self._userpass_name_input.text().strip()
        username = self._userpass_username.text().strip()
        password = self._userpass_password.text()

        if not name:
            QMessageBox.warning(self, "Error", "Please enter a name.")
            return

        if not username:
            QMessageBox.warning(self, "Error", "Please enter a username.")
            return

        store = self._get_store()
        from casare_rpa.infrastructure.security.credential_store import CredentialType

        data = {
            "username": username,
            "password": password,
            "host": self._userpass_host.text().strip(),
            "port": self._userpass_port.text().strip(),
        }

        try:
            store.save_credential(
                name=name,
                credential_type=CredentialType.USERNAME_PASSWORD,
                category=self._userpass_category.currentText(),
                data=data,
                description=self._userpass_description.text().strip(),
                credential_id=getattr(self, "_current_userpass_id", None),
            )

            QMessageBox.information(self, "Success", "Login saved successfully.")
            self.credentials_changed.emit()
            self._refresh_userpass_list()
            self._refresh_all_credentials()

        except Exception as e:
            logger.error(f"Failed to save login: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")

    def _delete_userpass(self) -> None:
        """Delete username/password credential."""
        cred_id = getattr(self, "_current_userpass_id", None)
        if not cred_id:
            QMessageBox.warning(self, "Error", "No login selected.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this login?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            store = self._get_store()
            store.delete_credential(cred_id)
            self._add_new_userpass()
            self.credentials_changed.emit()
            self._refresh_userpass_list()
            self._refresh_all_credentials()

    def _on_search_changed(self, text: str) -> None:
        """Handle search text change."""
        if not text:
            self._refresh_all_credentials()
            return

        store = self._get_store()
        results = store.search_credentials(text)

        self._all_credentials_list.clear()
        for cred in results:
            item = QListWidgetItem(
                f"{cred['name']} [{cred['type']}] - {cred['category']}"
            )
            item.setData(Qt.ItemDataRole.UserRole, cred["id"])
            self._all_credentials_list.addItem(item)

    def _on_credential_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle credential double-click to edit."""
        cred_id = item.data(Qt.ItemDataRole.UserRole)
        store = self._get_store()
        info = store.get_credential_info(cred_id)

        if info:
            self._credential_info.setText(
                f"<b>{info['name']}</b><br>"
                f"Type: {info['type']}<br>"
                f"Category: {info['category']}<br>"
                f"Description: {info.get('description', 'N/A')}<br>"
                f"Created: {info.get('created_at', 'N/A')}<br>"
                f"Last Used: {info.get('last_used', 'Never')}"
            )
