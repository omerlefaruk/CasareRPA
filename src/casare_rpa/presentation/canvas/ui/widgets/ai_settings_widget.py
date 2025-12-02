"""
AI Settings Widget - Reusable credential and model selector for AI features.

Provides a standardized way to select:
- API Key / Credential (from credential store)
- AI Provider (OpenAI, Anthropic, Google, etc.)
- Model (filtered by provider)
"""

from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QGroupBox,
)
from PySide6.QtCore import Signal

from loguru import logger


# Available models organized by provider
LLM_MODELS: Dict[str, List[str]] = {
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
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-2.0-flash-exp",
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
    "Mistral": "mistral",
    "Groq": "groq",
    "DeepSeek": "deepseek",
    "Local (Ollama)": "ollama",
}


def get_all_models() -> List[str]:
    """Get flat list of all available models."""
    all_models = []
    for models in LLM_MODELS.values():
        all_models.extend(models)
    return all_models


def get_llm_credentials() -> List[Dict[str, Any]]:
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
        for cred in store.list_credentials(category="llm"):
            credentials.append(
                {
                    "id": cred["id"],
                    "name": cred["name"],
                    "provider": cred.get("tags", ["unknown"])[0]
                    if cred.get("tags")
                    else "unknown",
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

    if "gpt" in model_lower or "o1" in model_lower:
        return "OpenAI"
    elif "claude" in model_lower:
        return "Anthropic"
    elif "gemini" in model_lower:
        return "Google"
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
        parent: Optional[QWidget] = None,
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
            outer_layout.setContentsMargins(0, 0, 0, 0)
            outer_layout.addWidget(group)
            container = group
        else:
            container = self

        if self._compact:
            layout = QHBoxLayout(container)
        else:
            layout = QVBoxLayout(container)

        layout.setSpacing(8)

        # Credential selector
        if self._show_credential:
            cred_layout = QHBoxLayout() if not self._compact else layout
            cred_label = QLabel("API Key:")
            cred_label.setFixedWidth(70)
            self._credential_combo = QComboBox()
            self._credential_combo.setMinimumWidth(150)
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
            provider_label.setFixedWidth(70)
            self._provider_combo = QComboBox()
            self._provider_combo.setMinimumWidth(120)
            self._provider_combo.addItems(list(LLM_MODELS.keys()))
            self._provider_combo.setToolTip("Select AI provider")

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
            model_label.setFixedWidth(70)
            self._model_combo = QComboBox()
            self._model_combo.setMinimumWidth(180)
            self._model_combo.setToolTip("Select AI model")
            self._update_models()  # Populate initial models

            if not self._compact:
                model_layout.addWidget(model_label)
                model_layout.addWidget(self._model_combo, 1)
                layout.addLayout(model_layout)
            else:
                layout.addWidget(model_label)
                layout.addWidget(self._model_combo)

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
                display = f"{cred['name']} ({cred['provider']})"
                self._credential_combo.addItem(display, cred["id"])
        else:
            self._credential_combo.addItem("No credentials stored", None)

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        if self._show_credential:
            self._credential_combo.currentIndexChanged.connect(
                self._on_credential_changed
            )

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

    def _on_credential_changed(self, index: int) -> None:
        """Handle credential selection change."""
        if self._updating:
            return

        cred_id = self._credential_combo.currentData()
        if cred_id and cred_id != "auto":
            self.credential_changed.emit(cred_id)

        self._emit_settings_changed()

    def _on_provider_changed(self, provider: str) -> None:
        """Handle provider selection change."""
        if self._updating:
            return

        self._update_models()
        self.provider_changed.emit(provider)
        self._emit_settings_changed()

    def _on_model_changed(self, model: str) -> None:
        """Handle model selection change."""
        if self._updating:
            return

        # Auto-update provider based on model
        if self._show_provider and model:
            detected_provider = detect_provider_from_model(model)
            current_provider = self._provider_combo.currentText()

            if detected_provider != current_provider:
                # Check if model is in detected provider's list
                if model in LLM_MODELS.get(detected_provider, []):
                    self._updating = True
                    idx = self._provider_combo.findText(detected_provider)
                    if idx >= 0:
                        self._provider_combo.setCurrentIndex(idx)
                    self._updating = False

        self.model_changed.emit(model)
        self._emit_settings_changed()

    def _emit_settings_changed(self) -> None:
        """Emit settings_changed with current values."""
        settings = self.get_settings()
        self.settings_changed.emit(settings)

    def get_settings(self) -> Dict[str, Any]:
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

    def set_settings(self, settings: Dict[str, Any]) -> None:
        """Set AI settings.

        Args:
            settings: Dict with credential_id, provider, model keys.
        """
        self._updating = True

        if self._show_provider and "provider" in settings:
            idx = self._provider_combo.findText(settings["provider"])
            if idx >= 0:
                self._provider_combo.setCurrentIndex(idx)
            self._update_models()

        if self._show_model and "model" in settings:
            idx = self._model_combo.findText(settings["model"])
            if idx >= 0:
                self._model_combo.setCurrentIndex(idx)

        if self._show_credential and "credential_id" in settings:
            for i in range(self._credential_combo.count()):
                if self._credential_combo.itemData(i) == settings["credential_id"]:
                    self._credential_combo.setCurrentIndex(i)
                    break

        self._updating = False

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

    def get_credential_id(self) -> Optional[str]:
        """Get currently selected credential ID."""
        if self._show_credential:
            cred_id = self._credential_combo.currentData()
            return cred_id if cred_id != "auto" else None
        return None

    def refresh_credentials(self) -> None:
        """Refresh the credentials list."""
        self._load_credentials()

    def apply_dark_style(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QGroupBox {
                background: #2d2d2d;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QComboBox {
                background-color: #3d3d3d;
                color: #e0e0e0;
                border: 1px solid #4a4a4a;
                padding: 4px 8px;
                border-radius: 3px;
                min-height: 20px;
            }
            QComboBox:hover {
                border-color: #5a8a9a;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #e0e0e0;
                selection-background-color: #5a8a9a;
                border: 1px solid #4a4a4a;
            }
        """)
