"""
AI Settings Widget - Reusable credential and model selector for AI features.

Provides a standardized way to select:
- API Key / Credential (from credential store)
- AI Provider (OpenAI, Anthropic, Google, etc.)
- Model (filtered by provider)
"""

import json
import urllib.request
from typing import Any

from loguru import logger
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME
from casare_rpa.presentation.canvas.theme_system.helpers import (
    set_fixed_width,
    set_min_width,
    set_spacing,
)
from casare_rpa.presentation.canvas.theme_system.tokens import TOKENS

# Available models organized by provider
LLM_MODELS: dict[str, list[str]] = {
    "OpenAI": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
        "o1-preview",
        "o1-mini",
    ],
    "Anthropic": [
        "claude-3-5-sonnet-latest",
        "claude-3-5-haiku-latest",
        "claude-3-opus-latest",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ],
    "Google": [
        "models/gemini-flash-lite-latest",
        "models/gemini-flash-latest",
        "models/gemini-3-flash-preview",
        "models/gemini-3-pro-preview",
    ],
    "GLM (Z.ai)": [
        "glm-4.7",
        "glm-4.6",
        "glm-4.5",
    ],
    "Mistral": [
        "mistral-large-latest",
        "mistral-medium-latest",
        "mistral-small-latest",
        "codestral-latest",
    ],
    "Groq": [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
    ],
    "DeepSeek": [
        "deepseek-chat",
        "deepseek-coder",
    ],
    "OpenRouter": [
        "openrouter/google/gemini-flash-lite-latest",
        "openrouter/google/gemini-flash-latest",
        "openrouter/google/gemini-3-flash-preview",
        "openrouter/google/gemini-3-pro-preview",
        "openrouter/deepseek/deepseek-v3.2",
        "openrouter/deepseek/deepseek-chat",
        "openrouter/openai/gpt-4o",
        "openrouter/anthropic/claude-3.5-sonnet",
        "openrouter/meta-llama/llama-3.3-70b-instruct",
        "openrouter/mistralai/mistral-large-latest",
    ],
    "Local (Ollama)": [
        "ollama/llama3.2",
        "ollama/mistral",
        "ollama/codellama",
        "ollama/phi3",
    ],
}

# Provider to credential category mapping
PROVIDER_TO_CATEGORY = {
    "OpenAI": "openai",
    "Anthropic": "anthropic",
    "Google": "google",
    "GLM (Z.ai)": "glm",
    "Mistral": "mistral",
    "Groq": "groq",
    "DeepSeek": "deepseek",
    "OpenRouter": "openrouter",
    "Local (Ollama)": "ollama",
}


def get_all_models() -> list[str]:
    """Get flat list of all available models."""
    all_models = []
    for models in LLM_MODELS.values():
        all_models.extend(models)
    return all_models


def get_llm_credentials() -> list[dict[str, Any]]:
    """Get available LLM credentials from credential store.

    Returns:
        List of credential dicts with id, name, provider fields.
    """
    credentials = []

    try:
        from casare_rpa.infrastructure.security.credential_store import (
            get_credential_store,
        )

        store = get_credential_store()

        # 1. Get standard LLM API keys
        for cred in store.list_credentials(category="llm"):
            credentials.append(
                {
                    "id": cred["id"],
                    "name": cred["name"],
                    "provider": cred.get("tags", ["unknown"])[0] if cred.get("tags") else "unknown",
                    "type": "api_key",
                }
            )

        # 2. Get Google OAuth credentials
        # (These can be used for Gemini models)
        for cred in store.list_credentials(category="google"):
            # Only include if it has scopes/tags, or include all and let user decide
            # Typically user would select "My Google Account"
            display_name = cred["name"]
            # Try to get email if available in description or we'd need to peek (expensive)
            # For now just use name
            credentials.append(
                {
                    "id": cred["id"],
                    "name": display_name,
                    "provider": "google",
                    "type": "oauth",
                }
            )

        # 3. Get OpenAI/Azure OAuth credentials
        for cred in store.list_credentials(category="openai_oauth"):
            display_name = cred["name"]
            credentials.append(
                {
                    "id": cred["id"],
                    "name": display_name,
                    "provider": "openai",
                    "type": "oauth",
                }
            )

    except ImportError:
        logger.debug("Credential store not available")
    except Exception as e:
        logger.warning(f"Error loading credentials: {e}")

    return credentials


def detect_provider_from_model(model: str) -> str:
    """Detect provider from model name.

    Args:
        model: Model identifier

    Returns:
        Provider name
    """
    model_lower = model.lower()

    if model_lower.startswith("openrouter/"):
        return "OpenRouter"
    elif model_lower.startswith("glm"):
        return "GLM (Z.ai)"
    elif "gemini" in model_lower:
        # Default Gemini to Google unless specifically OpenRouter
        if model_lower.startswith("openrouter/"):
            return "OpenRouter"
        return "Google"
    elif "gpt" in model_lower or "o1" in model_lower:
        return "OpenAI"
    elif "claude" in model_lower:
        return "Anthropic"
    elif "mistral" in model_lower or "codestral" in model_lower:
        return "Mistral"
    elif "llama" in model_lower or "mixtral" in model_lower:
        return "Groq"
    elif "deepseek" in model_lower:
        return "DeepSeek"
    elif "ollama" in model_lower:
        return "Local (Ollama)"

    return "OpenAI"  # Default


class AISettingsWidget(QWidget):
    """
    Reusable widget for AI credential and model selection.

    Signals:
        settings_changed: Emitted when any setting changes (dict with provider, model, credential)
        credential_changed: Emitted when credential changes (str: credential_id)
        provider_changed: Emitted when provider changes (str: provider_name)
        model_changed: Emitted when model changes (str: model_id)
    """

    settings_changed = Signal(dict)
    credential_changed = Signal(str)
    provider_changed = Signal(str)
    model_changed = Signal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        title: str = "AI Settings",
        show_credential: bool = True,
        show_provider: bool = True,
        show_model: bool = True,
        compact: bool = False,
    ) -> None:
        """
        Initialize AI settings widget.

        Args:
            parent: Parent widget
            title: Group box title (empty for no group box)
            show_credential: Whether to show credential selector
            show_provider: Whether to show provider selector
            show_model: Whether to show model selector
            compact: Use compact layout (horizontal)
        """
        super().__init__(parent)

        self._show_credential = show_credential
        self._show_provider = show_provider
        self._show_model = show_model
        self._compact = compact
        self._title = title
        self._updating = False  # Prevent recursive updates

        self._setup_ui()
        self._load_credentials()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        if self._title:
            group = QGroupBox(self._title)
            outer_layout = QVBoxLayout(self)
            outer_layout.setContentsMargins(*TOKENS.margins.none)
            outer_layout.addWidget(group)
            container = group
        else:
            container = self

        if self._compact:
            layout = QHBoxLayout(container)
        else:
            layout = QVBoxLayout(container)

        set_spacing(layout, TOKENS.spacing.md)

        # Credential selector
        if self._show_credential:
            cred_layout = QHBoxLayout() if not self._compact else layout
            cred_label = QLabel("API Key:")
            set_fixed_width(cred_label, 70)
            self._credential_combo = QComboBox()
            self._credential_combo.setMinimumWidth(TOKENS.sizes.input_min_width)
            self._credential_combo.setToolTip(
                "Select stored API credentials or use environment variables"
            )

            if not self._compact:
                cred_layout.addWidget(cred_label)
                cred_layout.addWidget(self._credential_combo, 1)
                layout.addLayout(cred_layout)
            else:
                layout.addWidget(cred_label)
                layout.addWidget(self._credential_combo)

        # Provider selector
        if self._show_provider:
            provider_layout = QHBoxLayout() if not self._compact else layout
            provider_label = QLabel("Provider:")
            set_fixed_width(provider_label, 70)
            self._provider_combo = QComboBox()
            set_min_width(_provider_combo, 120)
            self._provider_combo.addItems(list(LLM_MODELS.keys()))
            self._provider_combo.setToolTip("Select AI provider")

            # Set GLM (Z.ai) as default provider
            idx = self._provider_combo.findText("GLM (Z.ai)")
            if idx >= 0:
                self._provider_combo.setCurrentIndex(idx)

            if not self._compact:
                provider_layout.addWidget(provider_label)
                provider_layout.addWidget(self._provider_combo, 1)
                layout.addLayout(provider_layout)
            else:
                layout.addWidget(provider_label)
                layout.addWidget(self._provider_combo)

        # Model selector
        if self._show_model:
            model_layout = QHBoxLayout() if not self._compact else layout
            model_label = QLabel("Model:")
            set_fixed_width(model_label, 70)
            self._model_combo = QComboBox()
            set_min_width(_model_combo, 180)
            self._model_combo.setToolTip("Select AI model")
            self._update_models()  # Populate initial models

            # Fetch models button (for OpenRouter)
            self._fetch_btn = QPushButton("Refresh")
            self._fetch_btn.setToolTip("Refresh available models from OpenRouter")
            self._fetch_btn.clicked.connect(self._on_fetch_models_clicked)
            self._fetch_btn.setVisible(False)  # Hidden by default

            # Style the button to be small and unobtrusive
            set_fixed_width(self._fetch_btn, 60)

            if not self._compact:
                model_layout.addWidget(model_label)
                model_layout.addWidget(self._model_combo, 1)
                model_layout.addWidget(self._fetch_btn)
                layout.addLayout(model_layout)
            else:
                layout.addWidget(model_label)
                layout.addWidget(self._model_combo)
                layout.addWidget(self._fetch_btn)

        if self._compact:
            layout.addStretch()

    def _load_credentials(self) -> None:
        """Load credentials into combo box."""
        if not self._show_credential:
            return

        self._credential_combo.clear()
        self._credential_combo.addItem("Auto-detect (Environment)", "auto")
        self._credential_combo.addItem("──────────────", None)  # Separator

        credentials = get_llm_credentials()
        if credentials:
            for cred in credentials:
                type_label = "OAuth" if cred.get("type") == "oauth" else "Key"
                display = f"{cred['name']} ({cred['provider']} {type_label})"
                self._credential_combo.addItem(display, cred["id"])
        else:
            self._credential_combo.addItem("No credentials stored", None)

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        if self._show_credential:
            self._credential_combo.currentIndexChanged.connect(self._on_credential_changed)
            # Emit initial credential selection so consumers can enable their UI
            cred_id = self._credential_combo.currentData()
            if cred_id:
                self.credential_changed.emit(cred_id)

        if self._show_provider:
            self._provider_combo.currentTextChanged.connect(self._on_provider_changed)

        if self._show_model:
            self._model_combo.currentTextChanged.connect(self._on_model_changed)

    def _update_models(self) -> None:
        """Update model combo based on selected provider."""
        if not self._show_model:
            return

        if self._updating:
            return

        self._updating = True

        current_model = self._model_combo.currentText()
        self._model_combo.clear()

        if self._show_provider:
            provider = self._provider_combo.currentText()
            models = LLM_MODELS.get(provider, [])
        else:
            models = get_all_models()

        self._model_combo.addItems(models)

        # Try to restore previous selection
        idx = self._model_combo.findText(current_model)
        if idx >= 0:
            self._model_combo.setCurrentIndex(idx)
        elif models:
            self._model_combo.setCurrentIndex(0)

        self._updating = False

        # Force emit signal since _updating suppressed the combo signal
        self.model_changed.emit(self._model_combo.currentText())

    def _on_credential_changed(self, index: int) -> None:
        """Handle credential selection change."""
        if self._updating:
            return

        cred_id = self._credential_combo.currentData()

        # Check if it's a Google credential and auto-switch provider
        if cred_id and cred_id != "auto" and self._show_provider:
            try:
                from casare_rpa.infrastructure.security.credential_store import (
                    get_credential_store,
                )

                store = get_credential_store()
                info = store.get_credential_info(cred_id)
                if info and info.get("type") == "google_oauth":
                    idx = self._provider_combo.findText("Google")
                    if idx >= 0:
                        self._provider_combo.setCurrentIndex(idx)
            except Exception as e:
                logger.debug(f"Auto-switch provider failed: {e}")

        # Emit for both "auto" and stored credentials (skip separator with None)
        if cred_id:
            self.credential_changed.emit(cred_id)

        self._emit_settings_changed()

    def _on_provider_changed(self, provider: str) -> None:
        """Handle provider selection change."""
        if self._updating:
            return

        # Show fetch button only for OpenRouter and Google
        if hasattr(self, "_fetch_btn"):
            can_fetch = provider in ["OpenRouter", "Google"]
            self._fetch_btn.setVisible(can_fetch)

            # Auto-fetch models when OpenRouter is selected
            if provider == "OpenRouter":
                self._auto_fetch_openrouter_models()

        self._update_models()
        self.provider_changed.emit(provider)
        self._emit_settings_changed()

    def _auto_fetch_openrouter_models(self) -> None:
        """Automatically fetch OpenRouter models in background."""
        from PySide6.QtCore import QTimer

        # Use QTimer to defer fetch slightly (allows UI to update first)
        QTimer.singleShot(100, self._fetch_openrouter_silent)

    def _on_model_changed(self, model: str) -> None:
        """Handle model selection change."""
        if self._updating:
            return

        # Auto-update provider based on model
        if self._show_provider and model:
            detected_provider = detect_provider_from_model(model)
            current_provider = self._provider_combo.currentText()

            if detected_provider != current_provider:
                # Check if model is in provider list OR is a fetched OpenRouter model
                is_known_model = model in LLM_MODELS.get(detected_provider, [])
                is_fetched_openrouter = detected_provider == "OpenRouter" and model.startswith(
                    "openrouter/"
                )

                if is_known_model or is_fetched_openrouter:
                    self._updating = True
                    idx = self._provider_combo.findText(detected_provider)
                    if idx >= 0:
                        self._provider_combo.setCurrentIndex(idx)
                        # Also show fetch button if we switched to OpenRouter or Google
                        if hasattr(self, "_fetch_btn"):
                            can_fetch = detected_provider in ["OpenRouter", "Google"]
                            self._fetch_btn.setVisible(can_fetch)
                    self._updating = False

        self.model_changed.emit(model)
        self._emit_settings_changed()

    def _fetch_openrouter_silent(self) -> None:
        """Silently fetch OpenRouter models (no popups)."""
        api_key = self._get_openrouter_api_key()
        if not api_key:
            logger.debug("No OpenRouter API key available for auto-fetch")
            return

        # Remember current selection to restore after fetch
        current_model = self._model_combo.currentText() if self._show_model else ""

        if hasattr(self, "_fetch_btn"):
            self._fetch_btn.setEnabled(False)
            self._fetch_btn.setText("...")

        try:
            models = self._fetch_openrouter_models(api_key)
            if models:
                LLM_MODELS["OpenRouter"] = models
                self._update_models()

                # Restore previous model selection if it exists in fetched list
                if current_model and self._show_model:
                    idx = self._model_combo.findText(current_model)
                    if idx >= 0:
                        self._model_combo.setCurrentIndex(idx)

                logger.info(f"Auto-fetched {len(models)} OpenRouter models")
        except Exception as e:
            logger.warning(f"Auto-fetch OpenRouter models failed: {e}")
        finally:
            if hasattr(self, "_fetch_btn"):
                self._fetch_btn.setEnabled(True)
                self._fetch_btn.setText("Refresh")

    def _get_openrouter_api_key(self) -> str | None:
        """Get OpenRouter API key from credentials."""
        try:
            from casare_rpa.infrastructure.security.credential_store import (
                get_credential_store,
            )

            store = get_credential_store()

            cred_id = self._credential_combo.currentData() if self._show_credential else None

            if cred_id and cred_id != "auto":
                return store.get_api_key(cred_id)
            else:
                return store.get_api_key_by_provider("openrouter")
        except Exception as e:
            logger.debug(f"Could not get OpenRouter API key: {e}")
            return None

    def _get_api_key_for_fetch(self, provider: str) -> str | None:
        """Get API key or token for fetching models."""
        try:
            from casare_rpa.infrastructure.security.credential_store import (
                get_credential_store,
            )

            store = get_credential_store()
            cred_id = self._credential_combo.currentData() if self._show_credential else None

            # If user selected a specific credential, try to use it
            if cred_id and cred_id != "auto":
                info = store.get_credential_info(cred_id)
                if info:
                    if info.get("type") == "google_oauth":
                        # Need to get access token async. Return special marker.
                        return f"CRED_ID:{cred_id}"
                    return store.get_api_key(cred_id)

            # Fallback to provider default
            if provider == "OpenRouter":
                return store.get_api_key_by_provider("openrouter")
            elif provider == "Google":
                # Try to find a default Google OAuth credential
                creds = store.list_google_credentials()
                if creds:
                    return f"CRED_ID:{creds[0]['id']}"

            return None
        except Exception as e:
            logger.debug(f"Could not get API key for {provider}: {e}")
            return None

    def _on_fetch_models_clicked(self) -> None:
        """Fetch models from API (manual button click)."""
        provider = self._provider_combo.currentText()
        api_key_or_ref = self._get_api_key_for_fetch(provider)

        if not api_key_or_ref:
            QMessageBox.warning(
                self,
                "Missing Credentials",
                f"Please select a valid credential for {provider}.",
            )
            return

        self._fetch_btn.setEnabled(False)
        self._fetch_btn.setText("...")

        try:
            models = []
            if provider == "OpenRouter":
                models = self._fetch_openrouter_models(api_key_or_ref)
                LLM_MODELS["OpenRouter"] = models
            elif provider == "Google":
                # Handle Google fetch (async)
                self._fetch_google_models_async(api_key_or_ref)
                return  # Async method handles UI update

            if models:
                self._update_models()
                QMessageBox.information(
                    self, "Success", f"Fetched {len(models)} models from {provider}."
                )
            else:
                QMessageBox.warning(self, "Error", "No models found or API error.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch models: {str(e)}")
        finally:
            self._fetch_btn.setEnabled(True)
            self._fetch_btn.setText("Refresh")

    def _fetch_google_models_async(self, cred_ref: str) -> None:
        """Fetch Google models asynchronously using UnifiedHttpClient."""
        import asyncio

        from casare_rpa.infrastructure.http import UnifiedHttpClient, UnifiedHttpClientConfig
        from casare_rpa.infrastructure.security.google_oauth import get_google_oauth_manager

        # Parse credential ID
        if not cred_ref.startswith("CRED_ID:"):
            QMessageBox.warning(self, "Error", "Invalid credential reference for Google.")
            self._fetch_btn.setEnabled(True)
            self._fetch_btn.setText("Refresh")
            return

        cred_id = cred_ref.replace("CRED_ID:", "")

        async def do_fetch():
            try:
                manager = await get_google_oauth_manager()
                token = await manager.get_access_token(cred_id)
                if not token:
                    raise Exception("Could not get access token")

                # Call API
                url = "https://generativelanguage.googleapis.com/v1beta/models"
                headers = {"Authorization": f"Bearer {token}"}

                # Configure client for external Google APIs (SSRF protection enabled)
                config = UnifiedHttpClientConfig(
                    enable_ssrf_protection=True,
                    max_retries=2,
                    default_timeout=30.0,
                )

                async with UnifiedHttpClient(config) as http_client:
                    resp = await http_client.get(url, headers=headers)
                    if resp.status != TOKENS.sizes.panel_width_min:
                        text = await resp.text()
                        raise Exception(f"API Error {resp.status}: {text}")
                    data = await resp.json()

                # Extract and filter models, sort by newer versions first
                models = [
                    m["name"]
                    for m in data.get("models", [])
                    if "gemini" in m.get("name", "").lower()
                ]
                models.sort(reverse=True)
                return models

            except Exception as e:
                raise e

        # Use a background thread for the async operation (simple QThread wrapper)
        from PySide6.QtCore import QObject, QThread, Signal

        class GoogleFetchWorker(QObject):
            finished = Signal(list)
            error = Signal(str)

            def run(self):
                try:
                    # Create new loop for this thread if needed
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    models = loop.run_until_complete(do_fetch())
                    loop.close()
                    self.finished.emit(models)
                except Exception as e:
                    self.error.emit(str(e))

        # Store worker references to prevent garbage collection
        self._current_worker_thread = QThread()
        self._current_worker = GoogleFetchWorker()
        self._current_worker.moveToThread(self._current_worker_thread)
        self._current_worker_thread.started.connect(self._current_worker.run)

        def on_success(models):
            if models:
                LLM_MODELS["Google"] = models
                self._update_models()
                QMessageBox.information(self, "Success", f"Fetched {len(models)} Google models.")
            else:
                QMessageBox.warning(self, "Error", "No Google Gemini models found.")

            self._current_worker_thread.quit()
            self._fetch_btn.setEnabled(True)
            self._fetch_btn.setText("Refresh")

        def on_error(msg):
            self._current_worker_thread.quit()
            self._fetch_btn.setEnabled(True)
            self._fetch_btn.setText("Refresh")
            QMessageBox.critical(self, "Fetch Failed", f"Could not fetch Google models: {msg}")

        self._current_worker.finished.connect(on_success)
        self._current_worker.error.connect(on_error)
        self._current_worker_thread.start()

    def _fetch_openrouter_models(self, api_key: str) -> list[str]:
        """Call OpenRouter API to get models."""
        url = "https://openrouter.ai/api/v1/models"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://casarerpa.com",
            "X-Title": "CasareRPA",
        }

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status != TOKENS.sizes.panel_width_min:
                    raise Exception(f"HTTP Error {response.status}")

                data = json.loads(response.read().decode())

                models = []
                for item in data.get("data", []):
                    mid = item.get("id")
                    if mid:
                        models.append(
                            f"openrouter/{mid}" if not mid.startswith("openrouter/") else mid
                        )

                models.sort()
                return models
        except Exception as e:
            logger.error(f"OpenRouter API call failed: {e}")
            raise e

    def _emit_settings_changed(self) -> None:
        """Emit settings_changed with current values."""
        settings = self.get_settings()
        self.settings_changed.emit(settings)

    def get_settings(self) -> dict[str, Any]:
        """Get current AI settings.

        Returns:
            Dict with credential_id, provider, model keys.
        """
        settings = {}

        if self._show_credential:
            settings["credential_id"] = self._credential_combo.currentData()
            settings["credential_name"] = self._credential_combo.currentText()

        if self._show_provider:
            settings["provider"] = self._provider_combo.currentText()

        if self._show_model:
            settings["model"] = self._model_combo.currentText()

        return settings

    def set_settings(self, settings: dict[str, Any]) -> None:
        """Set AI settings.

        Args:
            settings: Dict with credential_id, provider, model keys.
        """
        self._updating = True

        provider = settings.get("provider", "")
        model_to_set = settings.get("model", "")

        if self._show_provider and provider:
            idx = self._provider_combo.findText(provider)
            if idx >= 0:
                self._provider_combo.setCurrentIndex(idx)

            # Show/hide fetch button based on provider
            if hasattr(self, "_fetch_btn"):
                can_fetch = provider in ["OpenRouter", "Google"]
                self._fetch_btn.setVisible(can_fetch)

            # Update models for the new provider
            self._update_models()

        # Only set model if it exists in the current provider's list
        if self._show_model and model_to_set:
            idx = self._model_combo.findText(model_to_set)
            if idx >= 0:
                self._model_combo.setCurrentIndex(idx)
            # else: model not in current provider's list, use default (first item)

        if self._show_credential and "credential_id" in settings:
            for i in range(self._credential_combo.count()):
                if self._credential_combo.itemData(i) == settings["credential_id"]:
                    self._credential_combo.setCurrentIndex(i)
                    break

        self._updating = False

        # Auto-fetch OpenRouter models after settings are loaded
        if provider == "OpenRouter":
            self._auto_fetch_openrouter_models()

    def get_model(self) -> str:
        """Get currently selected model."""
        if self._show_model:
            return self._model_combo.currentText()
        return ""

    def set_model(self, model: str) -> None:
        """Set the selected model."""
        if self._show_model:
            idx = self._model_combo.findText(model)
            if idx >= 0:
                self._model_combo.setCurrentIndex(idx)
            else:
                # Model not in list, add it
                self._model_combo.addItem(model)
                self._model_combo.setCurrentText(model)

    def get_provider(self) -> str:
        """Get currently selected provider."""
        if self._show_provider:
            return self._provider_combo.currentText()
        return ""

    def set_provider(self, provider: str) -> None:
        """Set the selected provider."""
        if self._show_provider:
            idx = self._provider_combo.findText(provider)
            if idx >= 0:
                self._provider_combo.setCurrentIndex(idx)

    def get_credential_id(self) -> str | None:
        """Get currently selected credential ID.

        Returns 'auto' for environment variable detection, or the stored credential ID.
        """
        if self._show_credential:
            return self._credential_combo.currentData()
        return None

    def refresh_credentials(self) -> None:
        """Refresh the credentials list."""
        self._load_credentials()

    def apply_dark_style(self) -> None:
        """Apply dark theme styling using THEME constants."""
        self.setStyleSheet(f"""
            QGroupBox {{
                background: {THEME.bg_dark};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radii.sm}px;
                margin-top: {TOKENS.spacing.md}px;
                padding-top: {TOKENS.spacing.md}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {TOKENS.spacing.md}px;
                padding: 0 {TOKENS.spacing.xs}px;
                color: {THEME.text_primary};
            }}
            QLabel {{
                color: {THEME.text_primary};
            }}
            QComboBox {{
                background-color: {THEME.bg_light};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                padding: {TOKENS.spacing.xs}px {TOKENS.spacing.md}px;
                border-radius: {TOKENS.radii.sm}px;
                min-height: {TOKENS.sizes.input_height_sm}px;
            }}
            QComboBox:hover {{
                border-color: {THEME.border_focus};
            }}
            QComboBox::drop-down {{
                border: none;
                width: {TOKENS.sizes.combo_dropdown_width}px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {THEME.bg_dark};
                color: {THEME.text_primary};
                selection-background-color: {THEME.border_focus};
                border: 1px solid {THEME.border};
            }}
        """)
