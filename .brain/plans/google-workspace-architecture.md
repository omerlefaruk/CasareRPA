# Google Workspace Integration Architecture

**Created**: 2025-12-08
**Status**: DESIGN
**Author**: Claude (Architect Agent)

---

## Overview

Design for comprehensive Google Workspace integration in CasareRPA, covering:
1. OAuth credential type with auto-refresh
2. OAuth browser flow for desktop app
3. Credential picker widget
4. Cascading dropdown system for Google resources
5. Node architecture enhancements

---

## 1. Google OAuth Credential Type

### 1.1 Credential Store Extension

**File**: `src/casare_rpa/infrastructure/security/credential_store.py`

```
# Add new credential type enum value
class CredentialType(Enum):
    ...
    GOOGLE_OAUTH = "google_oauth"  # NEW

# Add new category to CREDENTIAL_CATEGORIES
CREDENTIAL_CATEGORIES = {
    ...
    "google": {
        "name": "Google Workspace",
        "type": CredentialType.GOOGLE_OAUTH,
        "providers": ["google_workspace", "gmail", "drive", "sheets", "docs", "calendar"],
        "fields": [
            "client_id",
            "client_secret",
            "access_token",
            "refresh_token",
            "token_expiry",
            "scopes",
        ],
        "auto_refresh": True,
    },
}
```

### 1.2 GoogleOAuthCredential Data Contract

**File**: `src/casare_rpa/infrastructure/security/google_oauth.py`

```python
@dataclass
class GoogleOAuthCredentialData:
    """Data stored for Google OAuth credentials."""

    client_id: str
    client_secret: str
    access_token: str
    refresh_token: str
    token_expiry: datetime  # UTC timestamp
    scopes: List[str]

    # Metadata
    user_email: Optional[str] = None  # From token info
    project_id: Optional[str] = None  # Google Cloud project

    def is_expired(self) -> bool:
        """Check if access token is expired (with 5 min buffer)."""
        buffer = timedelta(minutes=5)
        return datetime.now(timezone.utc) >= (self.token_expiry - buffer)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_expiry": self.token_expiry.isoformat(),
            "scopes": self.scopes,
            "user_email": self.user_email,
            "project_id": self.project_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GoogleOAuthCredentialData":
        expiry = data.get("token_expiry")
        if isinstance(expiry, str):
            expiry = datetime.fromisoformat(expiry)
        return cls(
            client_id=data["client_id"],
            client_secret=data["client_secret"],
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            token_expiry=expiry,
            scopes=data.get("scopes", []),
            user_email=data.get("user_email"),
            project_id=data.get("project_id"),
        )
```

### 1.3 GoogleOAuthManager (Auto-Refresh)

**File**: `src/casare_rpa/infrastructure/security/google_oauth.py`

```python
class GoogleOAuthManager:
    """
    Manages Google OAuth credentials with automatic token refresh.

    Thread-safe singleton for credential access across the application.
    """

    TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
    USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v3/userinfo"

    _instance: Optional["GoogleOAuthManager"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self, credential_store: CredentialStore):
        self._store = credential_store
        self._cache: Dict[str, GoogleOAuthCredentialData] = {}
        self._refresh_lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "GoogleOAuthManager":
        with cls._lock:
            if cls._instance is None:
                from casare_rpa.infrastructure.security.credential_store import (
                    get_credential_store,
                )
                cls._instance = cls(get_credential_store())
            return cls._instance

    async def get_access_token(self, credential_id: str) -> str:
        """
        Get valid access token, refreshing if expired.

        Thread-safe with automatic refresh handling.
        """
        async with self._refresh_lock:
            # Get credential data
            cred_data = self._get_credential_data(credential_id)
            if not cred_data:
                raise GoogleAuthError(f"Credential not found: {credential_id}")

            # Check if refresh needed
            if cred_data.is_expired():
                cred_data = await self._refresh_token(credential_id, cred_data)

            return cred_data.access_token

    async def _refresh_token(
        self,
        credential_id: str,
        cred_data: GoogleOAuthCredentialData
    ) -> GoogleOAuthCredentialData:
        """Refresh access token using refresh_token."""
        async with aiohttp.ClientSession() as session:
            data = {
                "grant_type": "refresh_token",
                "refresh_token": cred_data.refresh_token,
                "client_id": cred_data.client_id,
                "client_secret": cred_data.client_secret,
            }

            async with session.post(self.TOKEN_ENDPOINT, data=data) as response:
                if response.status != 200:
                    error = await response.text()
                    raise GoogleAuthError(f"Token refresh failed: {error}")

                result = await response.json()

                # Update credential data
                new_cred = GoogleOAuthCredentialData(
                    client_id=cred_data.client_id,
                    client_secret=cred_data.client_secret,
                    access_token=result["access_token"],
                    refresh_token=result.get("refresh_token", cred_data.refresh_token),
                    token_expiry=datetime.now(timezone.utc) + timedelta(
                        seconds=result.get("expires_in", 3600)
                    ),
                    scopes=cred_data.scopes,
                    user_email=cred_data.user_email,
                    project_id=cred_data.project_id,
                )

                # Persist updated credential
                self._store.save_credential(
                    name=self._get_credential_name(credential_id),
                    credential_type=CredentialType.GOOGLE_OAUTH,
                    category="google",
                    data=new_cred.to_dict(),
                    credential_id=credential_id,
                )

                # Update cache
                self._cache[credential_id] = new_cred

                logger.info(f"Refreshed Google OAuth token for {credential_id}")
                return new_cred

    def _get_credential_data(self, credential_id: str) -> Optional[GoogleOAuthCredentialData]:
        """Get credential data from cache or store."""
        if credential_id in self._cache:
            return self._cache[credential_id]

        raw_data = self._store.get_credential(credential_id)
        if not raw_data:
            return None

        cred_data = GoogleOAuthCredentialData.from_dict(raw_data)
        self._cache[credential_id] = cred_data
        return cred_data
```

---

## 2. OAuth Browser Flow

### 2.1 Class Diagram

```
+---------------------------+
|   GoogleOAuthFlowDialog   |
+---------------------------+
| - _client_id: str         |
| - _client_secret: str     |
| - _scopes: List[str]      |
| - _server: LocalOAuthServer|
| - _state: str             |
+---------------------------+
| + start_flow()            |
| + _on_auth_complete()     |
| - _build_auth_url()       |
+---------------------------+
            |
            | uses
            v
+---------------------------+
|    LocalOAuthServer       |
+---------------------------+
| - _port: int              |
| - _server: HTTPServer     |
| - _auth_code: Optional    |
| - _error: Optional        |
+---------------------------+
| + start() -> int (port)   |
| + wait_for_callback()     |
| + stop()                  |
+---------------------------+
            |
            | receives
            v
+---------------------------+
|   OAuthCallbackHandler    |
+---------------------------+
| - path: str               |
+---------------------------+
| + do_GET()                |
+---------------------------+
```

### 2.2 LocalOAuthServer

**File**: `src/casare_rpa/infrastructure/security/oauth_server.py`

```python
class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    SUCCESS_HTML = """
    <!DOCTYPE html>
    <html>
    <head><title>Authorization Successful</title></head>
    <body style="font-family: sans-serif; text-align: center; padding: 50px;">
        <h1>Authorization Successful!</h1>
        <p>You can close this window and return to CasareRPA.</p>
        <script>window.close();</script>
    </body>
    </html>
    """

    ERROR_HTML = """
    <!DOCTYPE html>
    <html>
    <head><title>Authorization Failed</title></head>
    <body style="font-family: sans-serif; text-align: center; padding: 50px;">
        <h1>Authorization Failed</h1>
        <p>Error: {error}</p>
        <p>Please close this window and try again.</p>
    </body>
    </html>
    """

    def do_GET(self):
        """Handle OAuth callback GET request."""
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        # Check state parameter
        state = params.get("state", [None])[0]
        if state != self.server.expected_state:
            self._send_error("Invalid state parameter")
            return

        # Check for error
        error = params.get("error", [None])[0]
        if error:
            self.server.error = error
            self._send_error(error)
            return

        # Get authorization code
        code = params.get("code", [None])[0]
        if not code:
            self._send_error("No authorization code received")
            return

        self.server.auth_code = code
        self._send_success()

    def _send_success(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(self.SUCCESS_HTML.encode())

    def _send_error(self, error: str):
        self.send_response(400)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(self.ERROR_HTML.format(error=error).encode())

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class LocalOAuthServer:
    """
    Local HTTP server for OAuth callback.

    Starts on a random available port and waits for the OAuth callback.
    """

    REDIRECT_PATH = "/oauth/callback"
    PORT_RANGE = (49152, 65535)  # Dynamic/private port range

    def __init__(self, state: str):
        self._state = state
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._port: int = 0

    def start(self) -> int:
        """
        Start the local server on a random available port.

        Returns:
            The port number the server is listening on.
        """
        # Find available port
        for port in range(self.PORT_RANGE[0], self.PORT_RANGE[1]):
            try:
                self._server = HTTPServer(("127.0.0.1", port), OAuthCallbackHandler)
                self._server.expected_state = self._state
                self._server.auth_code = None
                self._server.error = None
                self._port = port
                break
            except OSError:
                continue

        if not self._server:
            raise RuntimeError("Could not find available port for OAuth callback")

        # Start server in background thread
        self._thread = threading.Thread(target=self._server.serve_forever)
        self._thread.daemon = True
        self._thread.start()

        logger.debug(f"OAuth callback server started on port {self._port}")
        return self._port

    @property
    def redirect_uri(self) -> str:
        """Get the redirect URI for this server."""
        return f"http://127.0.0.1:{self._port}{self.REDIRECT_PATH}"

    def wait_for_callback(self, timeout: float = 300.0) -> Tuple[Optional[str], Optional[str]]:
        """
        Wait for OAuth callback.

        Args:
            timeout: Maximum time to wait in seconds (default 5 minutes)

        Returns:
            Tuple of (auth_code, error)
        """
        start = time.time()
        while time.time() - start < timeout:
            if self._server.auth_code or self._server.error:
                return self._server.auth_code, self._server.error
            time.sleep(0.1)

        return None, "Timeout waiting for authorization"

    def stop(self):
        """Stop the server."""
        if self._server:
            self._server.shutdown()
            self._server = None
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
```

### 2.3 GoogleOAuthFlowDialog

**File**: `src/casare_rpa/presentation/canvas/dialogs/google_oauth_dialog.py`

```python
class GoogleOAuthFlowDialog(QDialog):
    """
    Dialog for Google OAuth authorization flow.

    Handles:
    1. Client ID/Secret input (or load from file)
    2. Scope selection
    3. OAuth browser flow
    4. Token exchange
    5. Credential storage

    Signals:
        credential_created: Emitted when credential is successfully created
    """

    AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"

    # Predefined scope sets
    SCOPE_PRESETS = {
        "Gmail (Full)": SCOPES["gmail"],
        "Gmail (Read Only)": SCOPES["gmail_readonly"],
        "Sheets (Full)": SCOPES["sheets"],
        "Sheets (Read Only)": SCOPES["sheets_readonly"],
        "Drive (Full)": SCOPES["drive"],
        "Drive (File Access)": SCOPES["drive_file"],
        "Docs (Full)": SCOPES["docs"],
        "Calendar": SCOPES.get("calendar", []),
    }

    credential_created = Signal(str)  # credential_id

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._oauth_server: Optional[LocalOAuthServer] = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Add Google Credential")
        self.setMinimumSize(500, 600)

        layout = QVBoxLayout(self)

        # Step 1: Credential Name
        name_group = QGroupBox("Credential Name")
        name_layout = QFormLayout(name_group)
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("e.g., My Google Account")
        name_layout.addRow("Name:", self._name_input)
        layout.addWidget(name_group)

        # Step 2: OAuth Client Credentials
        client_group = QGroupBox("OAuth Client Credentials")
        client_layout = QVBoxLayout(client_group)

        # Load from file button
        load_btn = QPushButton("Load from credentials.json...")
        load_btn.clicked.connect(self._load_credentials_file)
        client_layout.addWidget(load_btn)

        # Or manual entry
        form = QFormLayout()
        self._client_id_input = QLineEdit()
        self._client_id_input.setPlaceholderText("Your OAuth Client ID")
        form.addRow("Client ID:", self._client_id_input)

        self._client_secret_input = QLineEdit()
        self._client_secret_input.setPlaceholderText("Your OAuth Client Secret")
        self._client_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Client Secret:", self._client_secret_input)

        client_layout.addLayout(form)
        layout.addWidget(client_group)

        # Step 3: Scope Selection
        scope_group = QGroupBox("API Access (Scopes)")
        scope_layout = QVBoxLayout(scope_group)

        self._scope_checkboxes: Dict[str, QCheckBox] = {}
        for name, scopes in self.SCOPE_PRESETS.items():
            cb = QCheckBox(name)
            cb.setToolTip(", ".join(scopes))
            self._scope_checkboxes[name] = cb
            scope_layout.addWidget(cb)

        # Default to Sheets + Drive (common use case)
        self._scope_checkboxes["Sheets (Full)"].setChecked(True)
        self._scope_checkboxes["Drive (File Access)"].setChecked(True)

        layout.addWidget(scope_group)

        # Status label
        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        # Progress bar (hidden by default)
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # Indeterminate
        self._progress.hide()
        layout.addWidget(self._progress)

        # Buttons
        button_layout = QHBoxLayout()

        self._authorize_btn = QPushButton("Authorize with Google")
        self._authorize_btn.clicked.connect(self._start_oauth_flow)
        button_layout.addWidget(self._authorize_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _load_credentials_file(self):
        """Load OAuth credentials from JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select OAuth Credentials File",
            "",
            "JSON Files (*.json)",
        )

        if not file_path:
            return

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            # Handle Google Cloud Console format
            if "installed" in data:
                data = data["installed"]
            elif "web" in data:
                data = data["web"]

            self._client_id_input.setText(data.get("client_id", ""))
            self._client_secret_input.setText(data.get("client_secret", ""))
            self._status_label.setText("Credentials loaded from file")

        except Exception as e:
            QMessageBox.warning(
                self,
                "Error Loading File",
                f"Could not load credentials: {e}",
            )

    def _get_selected_scopes(self) -> List[str]:
        """Get list of selected OAuth scopes."""
        scopes = set()
        for name, cb in self._scope_checkboxes.items():
            if cb.isChecked():
                scopes.update(self.SCOPE_PRESETS[name])
        return list(scopes)

    def _start_oauth_flow(self):
        """Start the OAuth authorization flow."""
        # Validate inputs
        if not self._name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a credential name")
            return

        if not self._client_id_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter Client ID")
            return

        if not self._client_secret_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter Client Secret")
            return

        scopes = self._get_selected_scopes()
        if not scopes:
            QMessageBox.warning(self, "Validation Error", "Please select at least one scope")
            return

        # Run OAuth flow in background
        self._authorize_btn.setEnabled(False)
        self._progress.show()
        self._status_label.setText("Opening browser for authorization...")

        # Start in thread to not block UI
        thread = threading.Thread(target=self._run_oauth_flow, args=(scopes,))
        thread.start()

    def _run_oauth_flow(self, scopes: List[str]):
        """Execute OAuth flow (runs in background thread)."""
        try:
            # Generate state for CSRF protection
            state = secrets.token_urlsafe(32)

            # Start local server
            self._oauth_server = LocalOAuthServer(state)
            port = self._oauth_server.start()
            redirect_uri = self._oauth_server.redirect_uri

            # Build authorization URL
            params = {
                "client_id": self._client_id_input.text().strip(),
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": " ".join(scopes),
                "state": state,
                "access_type": "offline",  # Get refresh token
                "prompt": "consent",  # Always show consent screen
            }
            auth_url = f"{self.AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}"

            # Open browser
            webbrowser.open(auth_url)

            # Wait for callback
            QMetaObject.invokeMethod(
                self._status_label,
                "setText",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, "Waiting for authorization in browser...")
            )

            auth_code, error = self._oauth_server.wait_for_callback(timeout=300)

            if error:
                self._on_oauth_error(error)
                return

            if not auth_code:
                self._on_oauth_error("No authorization code received")
                return

            # Exchange code for tokens
            QMetaObject.invokeMethod(
                self._status_label,
                "setText",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, "Exchanging authorization code...")
            )

            self._exchange_code_for_token(auth_code, redirect_uri, scopes)

        except Exception as e:
            self._on_oauth_error(str(e))
        finally:
            if self._oauth_server:
                self._oauth_server.stop()

    def _exchange_code_for_token(
        self,
        auth_code: str,
        redirect_uri: str,
        scopes: List[str]
    ):
        """Exchange authorization code for access/refresh tokens."""
        data = {
            "code": auth_code,
            "client_id": self._client_id_input.text().strip(),
            "client_secret": self._client_secret_input.text().strip(),
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        response = requests.post(self.TOKEN_ENDPOINT, data=data)

        if response.status_code != 200:
            self._on_oauth_error(f"Token exchange failed: {response.text}")
            return

        result = response.json()

        # Create credential data
        cred_data = GoogleOAuthCredentialData(
            client_id=self._client_id_input.text().strip(),
            client_secret=self._client_secret_input.text().strip(),
            access_token=result["access_token"],
            refresh_token=result.get("refresh_token", ""),
            token_expiry=datetime.now(timezone.utc) + timedelta(
                seconds=result.get("expires_in", 3600)
            ),
            scopes=scopes,
        )

        # Store credential
        store = get_credential_store()
        cred_id = store.save_credential(
            name=self._name_input.text().strip(),
            credential_type=CredentialType.GOOGLE_OAUTH,
            category="google",
            data=cred_data.to_dict(),
            description=f"Google OAuth - Scopes: {', '.join(scopes)}",
        )

        # Success callback (on main thread)
        QMetaObject.invokeMethod(
            self,
            "_on_oauth_success",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, cred_id),
        )

    @Slot(str)
    def _on_oauth_success(self, credential_id: str):
        """Handle successful OAuth flow."""
        self._progress.hide()
        self._authorize_btn.setEnabled(True)
        self._status_label.setText("Authorization successful!")

        self.credential_created.emit(credential_id)

        QMessageBox.information(
            self,
            "Success",
            "Google credential created successfully!",
        )
        self.accept()

    def _on_oauth_error(self, error: str):
        """Handle OAuth error (thread-safe)."""
        QMetaObject.invokeMethod(
            self,
            "_show_oauth_error",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, error),
        )

    @Slot(str)
    def _show_oauth_error(self, error: str):
        """Display OAuth error in UI."""
        self._progress.hide()
        self._authorize_btn.setEnabled(True)
        self._status_label.setText(f"Error: {error}")

        QMessageBox.warning(
            self,
            "Authorization Failed",
            f"OAuth authorization failed:\n\n{error}",
        )
```

---

## 3. Credential Picker Widget

### 3.1 Class Diagram

```
+--------------------------------+
|   GoogleCredentialPicker       |
+--------------------------------+
| - _combo: QComboBox            |
| - _add_btn: QPushButton        |
| - _refresh_btn: QPushButton    |
| - _filter_category: str        |
| - _credential_store: CredStore |
+--------------------------------+
| + load_credentials()           |
| + get_selected_credential_id() |
| + _on_add_credential()         |
| + _on_refresh_clicked()        |
+--------------------------------+
| Signal: credential_changed     |
+--------------------------------+
```

### 3.2 GoogleCredentialPicker Widget

**File**: `src/casare_rpa/presentation/canvas/ui/widgets/google_credential_picker.py`

```python
class GoogleCredentialPicker(QWidget):
    """
    Reusable widget for selecting Google credentials in node properties.

    Features:
    - Dropdown showing only Google credentials
    - Auto-selects first credential if only one exists
    - "Add Credential" option opens OAuth flow
    - Refresh button to reload credentials
    - Shows credential email/name for identification

    Signals:
        credential_changed(str): Emitted when selection changes (credential_id)
    """

    credential_changed = Signal(str)

    ADD_NEW_ITEM = "__add_new__"

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        filter_category: str = "google",
        required_scopes: Optional[List[str]] = None,
    ):
        super().__init__(parent)
        self._filter_category = filter_category
        self._required_scopes = required_scopes or []
        self._setup_ui()
        self.load_credentials()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Credential dropdown
        self._combo = QComboBox()
        self._combo.setMinimumWidth(200)
        self._combo.currentIndexChanged.connect(self._on_selection_changed)
        layout.addWidget(self._combo, 1)

        # Refresh button
        self._refresh_btn = QPushButton()
        self._refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        self._refresh_btn.setToolTip("Refresh credentials")
        self._refresh_btn.setFixedSize(28, 28)
        self._refresh_btn.clicked.connect(self.load_credentials)
        layout.addWidget(self._refresh_btn)

        # Add button
        self._add_btn = QPushButton()
        self._add_btn.setIcon(QIcon.fromTheme("list-add"))
        self._add_btn.setToolTip("Add new Google credential")
        self._add_btn.setFixedSize(28, 28)
        self._add_btn.clicked.connect(self._on_add_credential)
        layout.addWidget(self._add_btn)

        # Apply dark theme styling
        self.setStyleSheet("""
            QComboBox {
                background-color: #3C3C3C;
                color: #D4D4D4;
                border: 1px solid #505050;
                border-radius: 3px;
                padding: 4px 8px;
            }
            QComboBox:hover {
                border-color: #007ACC;
            }
            QComboBox::drop-down {
                border: none;
            }
            QPushButton {
                background-color: #3C3C3C;
                border: 1px solid #505050;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #4C4C4C;
                border-color: #007ACC;
            }
        """)

    def load_credentials(self):
        """Load Google credentials into dropdown."""
        store = get_credential_store()
        current_id = self.get_selected_credential_id()

        self._combo.blockSignals(True)
        self._combo.clear()

        # Add empty option
        self._combo.addItem("-- Select Credential --", "")

        # Add existing credentials
        credentials = store.list_credentials(category=self._filter_category)

        for cred in credentials:
            # Filter by required scopes if specified
            if self._required_scopes:
                cred_data = store.get_credential(cred["id"])
                if cred_data:
                    cred_scopes = set(cred_data.get("scopes", []))
                    required = set(self._required_scopes)
                    if not required.issubset(cred_scopes):
                        continue

            # Display format: "Name (email@domain.com)"
            display = cred["name"]
            cred_data = store.get_credential(cred["id"])
            if cred_data and cred_data.get("user_email"):
                display = f"{cred['name']} ({cred_data['user_email']})"

            self._combo.addItem(display, cred["id"])

        # Add "Add New Credential" option
        self._combo.insertSeparator(self._combo.count())
        self._combo.addItem("+ Add New Credential...", self.ADD_NEW_ITEM)

        # Restore selection or auto-select if only one
        self._combo.blockSignals(False)

        if current_id:
            idx = self._combo.findData(current_id)
            if idx >= 0:
                self._combo.setCurrentIndex(idx)
        elif self._combo.count() == 4:  # Empty + 1 credential + separator + add new
            self._combo.setCurrentIndex(1)  # Auto-select the single credential

    def get_selected_credential_id(self) -> str:
        """Get the currently selected credential ID."""
        return self._combo.currentData() or ""

    def set_credential_id(self, credential_id: str):
        """Set the selected credential by ID."""
        idx = self._combo.findData(credential_id)
        if idx >= 0:
            self._combo.setCurrentIndex(idx)

    def _on_selection_changed(self, index: int):
        """Handle dropdown selection change."""
        data = self._combo.itemData(index)

        if data == self.ADD_NEW_ITEM:
            self._on_add_credential()
            # Reset to previous selection
            self._combo.setCurrentIndex(0)
            return

        if data:
            self.credential_changed.emit(data)

    def _on_add_credential(self):
        """Open Google OAuth flow dialog."""
        from casare_rpa.presentation.canvas.dialogs.google_oauth_dialog import (
            GoogleOAuthFlowDialog,
        )

        dialog = GoogleOAuthFlowDialog(self.window())
        dialog.credential_created.connect(self._on_credential_created)
        dialog.exec()

    def _on_credential_created(self, credential_id: str):
        """Handle new credential creation."""
        self.load_credentials()
        self.set_credential_id(credential_id)
        self.credential_changed.emit(credential_id)
```

### 3.3 PropertyType Extension

**File**: `src/casare_rpa/domain/schemas/property_types.py` (modification)

```python
class PropertyType(str, Enum):
    ...
    # Integration types (NEW)
    GOOGLE_CREDENTIAL = "google_credential"  # Google credential picker
    GOOGLE_SPREADSHEET = "google_spreadsheet"  # Spreadsheet picker (cascading)
    GOOGLE_SHEET = "google_sheet"  # Sheet picker (depends on spreadsheet)
    GOOGLE_DRIVE_FILE = "google_drive_file"  # Drive file picker
    GOOGLE_DRIVE_FOLDER = "google_drive_folder"  # Drive folder picker
```

---

## 4. Cascading Dropdown System

### 4.1 Data Flow Diagram

```
User selects credential
        |
        v
+-------------------+
| CredentialPicker  | ---> credential_changed(cred_id)
+-------------------+
        |
        v
+-------------------+
| SpreadsheetPicker | ---> spreadsheet_changed(spreadsheet_id)
+-------------------+
        |
        | Loads spreadsheets via Google Drive API
        | query: mimeType='application/vnd.google-apps.spreadsheet'
        |
        v
+-------------------+
|   SheetPicker     | ---> sheet_changed(sheet_name)
+-------------------+
        |
        | Loads sheets via Google Sheets API
        | endpoint: GET spreadsheets/{id}?fields=sheets.properties
        |
        v
+-------------------+
|   RangePicker     | (optional)
+-------------------+
```

### 4.2 CascadingDropdownBase

**File**: `src/casare_rpa/presentation/canvas/ui/widgets/cascading_dropdown.py`

```python
class LoadingState(Enum):
    """State of async data loading."""
    IDLE = "idle"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"


class CascadingDropdownBase(QWidget):
    """
    Base class for cascading dropdown widgets with async loading.

    Features:
    - Loading indicator
    - Caching with TTL invalidation
    - Error handling with retry
    - Parent dependency management
    """

    # Signals
    selection_changed = Signal(str)  # item_id
    loading_started = Signal()
    loading_finished = Signal()
    error_occurred = Signal(str)  # error message

    # Cache settings
    CACHE_TTL = timedelta(minutes=5)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        placeholder: str = "-- Select --",
    ):
        super().__init__(parent)
        self._state = LoadingState.IDLE
        self._cache: Dict[str, Tuple[List, datetime]] = {}  # key -> (items, timestamp)
        self._parent_value: Optional[str] = None
        self._placeholder = placeholder
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Main dropdown
        self._combo = QComboBox()
        self._combo.setMinimumWidth(200)
        self._combo.addItem(self._placeholder, "")
        self._combo.currentIndexChanged.connect(self._on_selection_changed)
        layout.addWidget(self._combo, 1)

        # Loading spinner (hidden by default)
        self._spinner = QLabel()
        self._spinner.setFixedSize(20, 20)
        self._spinner.hide()
        layout.addWidget(self._spinner)

        # Refresh button
        self._refresh_btn = QPushButton()
        self._refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        self._refresh_btn.setToolTip("Refresh")
        self._refresh_btn.setFixedSize(28, 28)
        self._refresh_btn.clicked.connect(self._on_refresh)
        layout.addWidget(self._refresh_btn)

    def set_parent_value(self, value: str):
        """
        Set the parent dropdown's selected value.

        Called when parent selection changes. Triggers reload if value changed.
        """
        if value != self._parent_value:
            self._parent_value = value
            self._load_items()

    def _load_items(self):
        """Load items from API or cache."""
        if not self._parent_value:
            self._clear_items()
            return

        # Check cache
        cache_key = self._get_cache_key()
        if cache_key in self._cache:
            items, timestamp = self._cache[cache_key]
            if datetime.now() - timestamp < self.CACHE_TTL:
                self._populate_items(items)
                return

        # Load from API
        self._set_loading_state(True)

        # Run async load in thread
        thread = threading.Thread(target=self._async_load_items, args=(cache_key,))
        thread.start()

    def _async_load_items(self, cache_key: str):
        """Async item loading (runs in background thread)."""
        try:
            # Create event loop for async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            items = loop.run_until_complete(self._fetch_items())

            # Cache results
            self._cache[cache_key] = (items, datetime.now())

            # Update UI on main thread
            QMetaObject.invokeMethod(
                self,
                "_on_items_loaded",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(list, items),
            )

        except Exception as e:
            QMetaObject.invokeMethod(
                self,
                "_on_load_error",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, str(e)),
            )
        finally:
            loop.close()

    @abstractmethod
    async def _fetch_items(self) -> List[Tuple[str, str]]:
        """
        Fetch items from API.

        Returns:
            List of (display_text, item_id) tuples
        """
        ...

    def _get_cache_key(self) -> str:
        """Generate cache key from parent value."""
        return f"{self.__class__.__name__}:{self._parent_value}"

    @Slot(list)
    def _on_items_loaded(self, items: List[Tuple[str, str]]):
        """Handle items loaded (main thread)."""
        self._set_loading_state(False)
        self._populate_items(items)
        self.loading_finished.emit()

    @Slot(str)
    def _on_load_error(self, error: str):
        """Handle load error (main thread)."""
        self._set_loading_state(False)
        self._state = LoadingState.ERROR
        self._combo.clear()
        self._combo.addItem(f"Error: {error[:30]}...", "")
        self.error_occurred.emit(error)

    def _populate_items(self, items: List[Tuple[str, str]]):
        """Populate dropdown with items."""
        current_id = self.get_selected_id()

        self._combo.blockSignals(True)
        self._combo.clear()
        self._combo.addItem(self._placeholder, "")

        for display, item_id in items:
            self._combo.addItem(display, item_id)

        self._combo.blockSignals(False)
        self._state = LoadingState.LOADED

        # Restore selection if still valid
        if current_id:
            idx = self._combo.findData(current_id)
            if idx >= 0:
                self._combo.setCurrentIndex(idx)

    def _clear_items(self):
        """Clear all items from dropdown."""
        self._combo.clear()
        self._combo.addItem(self._placeholder, "")
        self._state = LoadingState.IDLE

    def _set_loading_state(self, loading: bool):
        """Set loading UI state."""
        if loading:
            self._state = LoadingState.LOADING
            self._spinner.show()
            self._combo.setEnabled(False)
            self.loading_started.emit()
        else:
            self._spinner.hide()
            self._combo.setEnabled(True)

    def _on_selection_changed(self, index: int):
        """Handle selection change."""
        item_id = self._combo.itemData(index)
        if item_id:
            self.selection_changed.emit(item_id)

    def _on_refresh(self):
        """Force refresh from API."""
        cache_key = self._get_cache_key()
        if cache_key in self._cache:
            del self._cache[cache_key]
        self._load_items()

    def get_selected_id(self) -> str:
        """Get currently selected item ID."""
        return self._combo.currentData() or ""

    def set_selected_id(self, item_id: str):
        """Set selection by item ID."""
        idx = self._combo.findData(item_id)
        if idx >= 0:
            self._combo.setCurrentIndex(idx)

    def invalidate_cache(self):
        """Clear cache to force reload on next access."""
        self._cache.clear()
```

### 4.3 GoogleSpreadsheetPicker

**File**: `src/casare_rpa/presentation/canvas/ui/widgets/google_pickers.py`

```python
class GoogleSpreadsheetPicker(CascadingDropdownBase):
    """
    Dropdown for selecting Google Spreadsheets.

    Loads spreadsheets from Google Drive API filtered by MIME type.
    Parent: GoogleCredentialPicker (provides credential_id)
    """

    SPREADSHEET_MIME = "application/vnd.google-apps.spreadsheet"

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent, placeholder="-- Select Spreadsheet --")
        self._oauth_manager = GoogleOAuthManager.get_instance()

    async def _fetch_items(self) -> List[Tuple[str, str]]:
        """Fetch spreadsheets from Google Drive."""
        if not self._parent_value:
            return []

        credential_id = self._parent_value
        access_token = await self._oauth_manager.get_access_token(credential_id)

        # Query Google Drive for spreadsheets
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {access_token}"}
            params = {
                "q": f"mimeType='{self.SPREADSHEET_MIME}' and trashed=false",
                "fields": "files(id,name,modifiedTime)",
                "orderBy": "modifiedTime desc",
                "pageSize": 100,
            }

            async with session.get(
                "https://www.googleapis.com/drive/v3/files",
                headers=headers,
                params=params,
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise GoogleAPIError(f"Failed to list spreadsheets: {error}")

                data = await response.json()

                items = []
                for file in data.get("files", []):
                    display = file["name"]
                    items.append((display, file["id"]))

                return items


class GoogleSheetPicker(CascadingDropdownBase):
    """
    Dropdown for selecting a worksheet within a Google Spreadsheet.

    Loads sheets from Google Sheets API.
    Parent: GoogleSpreadsheetPicker (provides spreadsheet_id)
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent, placeholder="-- Select Sheet --")
        self._credential_id: Optional[str] = None
        self._oauth_manager = GoogleOAuthManager.get_instance()

    def set_credential_id(self, credential_id: str):
        """Set credential ID for API access."""
        self._credential_id = credential_id

    async def _fetch_items(self) -> List[Tuple[str, str]]:
        """Fetch sheets from spreadsheet."""
        if not self._parent_value or not self._credential_id:
            return []

        spreadsheet_id = self._parent_value
        access_token = await self._oauth_manager.get_access_token(self._credential_id)

        # Query Google Sheets API
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {access_token}"}
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"
            params = {"fields": "sheets.properties"}

            async with session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    error = await response.text()
                    raise GoogleAPIError(f"Failed to get spreadsheet: {error}")

                data = await response.json()

                items = []
                for sheet in data.get("sheets", []):
                    props = sheet.get("properties", {})
                    name = props.get("title", "Sheet")
                    sheet_id = str(props.get("sheetId", 0))
                    items.append((name, name))  # Use name as ID for A1 notation

                return items


class GoogleDriveFilePicker(CascadingDropdownBase):
    """
    Dropdown for selecting files from Google Drive.

    Supports filtering by MIME type and folder.
    Parent: GoogleCredentialPicker (provides credential_id)
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        mime_filter: Optional[str] = None,
        folder_id: Optional[str] = None,
    ):
        super().__init__(parent, placeholder="-- Select File --")
        self._mime_filter = mime_filter
        self._folder_id = folder_id
        self._oauth_manager = GoogleOAuthManager.get_instance()

    async def _fetch_items(self) -> List[Tuple[str, str]]:
        """Fetch files from Google Drive."""
        if not self._parent_value:
            return []

        credential_id = self._parent_value
        access_token = await self._oauth_manager.get_access_token(credential_id)

        # Build query
        query_parts = ["trashed=false"]
        if self._mime_filter:
            query_parts.append(f"mimeType='{self._mime_filter}'")
        if self._folder_id:
            query_parts.append(f"'{self._folder_id}' in parents")

        query = " and ".join(query_parts)

        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {access_token}"}
            params = {
                "q": query,
                "fields": "files(id,name,mimeType,modifiedTime)",
                "orderBy": "modifiedTime desc",
                "pageSize": 100,
            }

            async with session.get(
                "https://www.googleapis.com/drive/v3/files",
                headers=headers,
                params=params,
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise GoogleAPIError(f"Failed to list files: {error}")

                data = await response.json()

                items = []
                for file in data.get("files", []):
                    display = file["name"]
                    items.append((display, file["id"]))

                return items
```

---

## 5. Node Architecture

### 5.1 Updated Class Hierarchy

```
BaseNode (domain/entities/base_node.py)
    |
    +-- GoogleBaseNode (nodes/google/google_base.py)
            |
            +-- GmailBaseNode
            |       +-- GmailSendNode
            |       +-- GmailReadNode
            |       +-- GmailSearchNode
            |
            +-- SheetsBaseNode
            |       +-- SheetsReadRangeNode
            |       +-- SheetsWriteRangeNode
            |       +-- SheetsAppendRowNode
            |       +-- SheetsClearRangeNode
            |
            +-- DocsBaseNode
            |       +-- DocsReadNode
            |       +-- DocsInsertTextNode
            |       +-- DocsReplaceTextNode
            |
            +-- DriveBaseNode
            |       +-- DriveUploadNode
            |       +-- DriveDownloadNode
            |       +-- DriveListFilesNode
            |       +-- DriveCreateFolderNode
            |       +-- DriveCopyFileNode
            |       +-- DriveMoveFileNode
            |       +-- DriveDeleteNode
            |
            +-- CalendarBaseNode
                    +-- CalendarListEventsNode
                    +-- CalendarCreateEventNode
                    +-- CalendarUpdateEventNode
```

### 5.2 GoogleBaseNode Enhancements

**File**: `src/casare_rpa/nodes/google/google_base.py` (modifications)

```python
# Add new PropertyDef for credential picker
GOOGLE_CREDENTIAL_PICKER = PropertyDef(
    name="google_credential",
    type=PropertyType.GOOGLE_CREDENTIAL,  # New property type
    default="",
    label="Google Account",
    tooltip="Select Google account credential",
    tab="connection",
    required=True,
)

# Updated credential resolution in GoogleBaseNode
class GoogleBaseNode(CredentialAwareMixin, BaseNode):

    async def _get_credentials(self, context: ExecutionContext) -> GoogleCredentials:
        """Get credentials with auto-refresh support."""
        # 1. Try credential picker selection (NEW)
        credential_id = self.get_parameter("google_credential")
        if credential_id:
            oauth_manager = GoogleOAuthManager.get_instance()
            access_token = await oauth_manager.get_access_token(credential_id)

            cred_data = get_credential_store().get_credential(credential_id)
            return GoogleCredentials(
                access_token=access_token,
                refresh_token=cred_data.get("refresh_token"),
                client_id=cred_data.get("client_id"),
                client_secret=cred_data.get("client_secret"),
                scopes=cred_data.get("scopes", []),
            )

        # 2. Fall back to existing resolution methods
        # ... existing code ...
```

### 5.3 Sheets Node with Cascading Dropdowns

**File**: `src/casare_rpa/nodes/google/sheets_nodes.py`

```python
# PropertyDefs for Sheets nodes
SHEETS_SPREADSHEET = PropertyDef(
    name="spreadsheet_id",
    type=PropertyType.GOOGLE_SPREADSHEET,
    default="",
    label="Spreadsheet",
    tooltip="Select Google Spreadsheet",
    tab="main",
    required=True,
    depends_on="google_credential",  # Cascading dependency
)

SHEETS_SHEET_NAME = PropertyDef(
    name="sheet_name",
    type=PropertyType.GOOGLE_SHEET,
    default="Sheet1",
    label="Sheet",
    tooltip="Select worksheet within spreadsheet",
    tab="main",
    required=False,
    depends_on="spreadsheet_id",  # Cascading dependency
)

SHEETS_RANGE = PropertyDef(
    name="range",
    type=PropertyType.STRING,
    default="A1",
    label="Range",
    tooltip="Cell range in A1 notation (e.g., A1:D10)",
    tab="main",
    required=False,
)


@executable_node
@node_schema(
    GOOGLE_CREDENTIAL_PICKER,
    SHEETS_SPREADSHEET,
    SHEETS_SHEET_NAME,
    SHEETS_RANGE,
    *GOOGLE_COMMON_PROPERTIES[4:],  # Timeout, retries (skip credential props)
)
class SheetsReadRangeNode(SheetsBaseNode):
    """Read data from a Google Sheets range."""

    NODE_NAME = "Read Range"
    CATEGORY = "google/sheets"

    def _define_ports(self) -> None:
        self._define_common_input_ports()
        self._define_spreadsheet_id_port()
        self._define_sheet_name_port()

        self.add_input_port("range", PortType.INPUT, DataType.STRING, label="Range")

        self._define_common_output_ports()
        self.add_output_port("data", PortType.OUTPUT, DataType.LIST, label="Data")
        self.add_output_port("row_count", PortType.OUTPUT, DataType.INTEGER, label="Row Count")

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleAPIClient,
        service: Any,
    ) -> ExecutionResult:
        spreadsheet_id = self._get_spreadsheet_id(context)
        sheet_name = self._get_sheet_name(context)
        range_str = self.get_parameter("range") or "A1"

        # Build full range with sheet name
        full_range = self.build_a1_range(sheet_name, start_cell=range_str)

        # Execute API request
        request = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=full_range,
        )
        result = await client.execute_request(request)

        values = result.get("values", [])

        self._set_success_outputs(
            data=values,
            row_count=len(values),
        )

        return {
            "success": True,
            "data": {
                "values": values,
                "row_count": len(values),
                "range": result.get("range"),
            },
            "next_nodes": self._get_connected_exec_nodes("exec_out"),
        }
```

---

## 6. File Structure

```
src/casare_rpa/
├── domain/
│   └── schemas/
│       └── property_types.py        # Add GOOGLE_CREDENTIAL, GOOGLE_SPREADSHEET, etc.
│
├── infrastructure/
│   └── security/
│       ├── credential_store.py      # Add GOOGLE_OAUTH type, google category
│       ├── google_oauth.py          # NEW: GoogleOAuthCredentialData, GoogleOAuthManager
│       └── oauth_server.py          # NEW: LocalOAuthServer, OAuthCallbackHandler
│
├── nodes/
│   └── google/
│       ├── google_base.py           # Update with GOOGLE_CREDENTIAL_PICKER
│       ├── sheets_nodes.py          # NEW: All Sheets operation nodes
│       ├── drive_nodes.py           # NEW: All Drive operation nodes
│       ├── docs_nodes.py            # NEW: All Docs operation nodes
│       ├── gmail_nodes.py           # NEW: All Gmail operation nodes
│       └── calendar_nodes.py        # NEW: All Calendar operation nodes
│
└── presentation/
    └── canvas/
        ├── dialogs/
        │   └── google_oauth_dialog.py  # NEW: OAuth flow dialog
        │
        └── ui/
            └── widgets/
                ├── cascading_dropdown.py    # NEW: CascadingDropdownBase
                ├── google_credential_picker.py  # NEW: Credential picker
                └── google_pickers.py        # NEW: Spreadsheet, Sheet, File pickers
```

---

## 7. Implementation Order

### Phase 1: Credential Infrastructure (Priority: HIGH)
1. `infrastructure/security/google_oauth.py` - GoogleOAuthCredentialData, GoogleOAuthManager
2. `infrastructure/security/credential_store.py` - Add GOOGLE_OAUTH type
3. `infrastructure/security/oauth_server.py` - Local OAuth callback server

### Phase 2: OAuth Dialog (Priority: HIGH)
4. `presentation/canvas/dialogs/google_oauth_dialog.py` - OAuth flow UI

### Phase 3: Widgets (Priority: MEDIUM)
5. `domain/schemas/property_types.py` - Add new property types
6. `presentation/canvas/ui/widgets/cascading_dropdown.py` - Base class
7. `presentation/canvas/ui/widgets/google_credential_picker.py` - Credential picker
8. `presentation/canvas/ui/widgets/google_pickers.py` - Spreadsheet, Sheet, File pickers

### Phase 4: Widget Integration (Priority: MEDIUM)
9. `presentation/canvas/visual_nodes/base_visual_node.py` - Auto-create widgets for new types
10. `presentation/canvas/graph/node_widgets.py` - Widget factory for new types

### Phase 5: Node Updates (Priority: LOW)
11. `nodes/google/google_base.py` - Add GOOGLE_CREDENTIAL_PICKER
12. `nodes/google/sheets_nodes.py` - Sheets nodes with cascading props

---

## 8. Data Contracts (JSON Schemas)

### 8.1 GoogleOAuthCredentialData

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GoogleOAuthCredentialData",
  "type": "object",
  "required": ["client_id", "client_secret", "access_token", "refresh_token", "token_expiry", "scopes"],
  "properties": {
    "client_id": {
      "type": "string",
      "description": "OAuth 2.0 Client ID from Google Cloud Console"
    },
    "client_secret": {
      "type": "string",
      "description": "OAuth 2.0 Client Secret"
    },
    "access_token": {
      "type": "string",
      "description": "Current OAuth 2.0 access token"
    },
    "refresh_token": {
      "type": "string",
      "description": "OAuth 2.0 refresh token for obtaining new access tokens"
    },
    "token_expiry": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp when access_token expires"
    },
    "scopes": {
      "type": "array",
      "items": {"type": "string"},
      "description": "List of OAuth 2.0 scopes granted"
    },
    "user_email": {
      "type": "string",
      "format": "email",
      "description": "Email address of authorized Google account"
    },
    "project_id": {
      "type": "string",
      "description": "Google Cloud Project ID (optional)"
    }
  }
}
```

### 8.2 PropertyDef depends_on Extension

```json
{
  "name": "spreadsheet_id",
  "type": "google_spreadsheet",
  "depends_on": "google_credential",
  "description": "Cascading dropdown that loads spreadsheets when credential is selected"
}
```

---

## 9. Unresolved Questions

1. **Token storage security**: Should we encrypt OAuth tokens at rest with a per-user key, or is the existing Fernet encryption sufficient?

2. **Scope management**: When user adds credential with limited scopes, should we:
   - Block nodes that require additional scopes?
   - Prompt for re-authorization with expanded scopes?
   - Show warning but allow execution (will fail at runtime)?

3. **Multi-account support**: Should the credential picker support selecting from multiple Google accounts simultaneously (e.g., copy from Account A to Account B)?

4. **Offline access**: Should we implement token refresh during workflow execution, or require valid tokens before execution starts?

5. **Rate limiting**: Should cascading dropdowns implement client-side rate limiting to avoid Google API quota exhaustion during rapid selection changes?

---

*End of architecture document*
