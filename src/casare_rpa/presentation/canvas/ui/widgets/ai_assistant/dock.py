"""
AI Assistant Dock Widget.

Main dockable container for the AI-powered workflow assistant.
Provides credential selection, chat interface, and workflow preview.

Features:
- Credential selector for AI providers (GOOGLE_AI, OPENAI)
- Chat area with conversation history
- Input field with send button
- Status bar showing validation progress
- Preview card for generated workflows
- Integration with SmartWorkflowAgent for validated workflow generation
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from PySide6.QtCore import Qt, Signal, QTimer, QThread, QObject
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtWidgets import (
    QComboBox,
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from loguru import logger

from casare_rpa.presentation.canvas.ui.theme import Theme, ANIMATIONS
from casare_rpa.presentation.canvas.ui.widgets.ai_assistant.chat_area import ChatArea
from casare_rpa.presentation.canvas.ui.widgets.ai_assistant.preview_card import (
    PreviewCard,
)

if TYPE_CHECKING:
    from casare_rpa.infrastructure.ai.smart_agent import WorkflowGenerationResult


# =============================================================================
# Background Worker for AI Generation
# =============================================================================


class WorkflowGenerationWorker(QObject):
    """
    Worker for running SmartWorkflowAgent in background thread.

    Executes async LLM calls without blocking the Qt event loop.
    Uses credentials from the credential store for API authentication.
    """

    finished = Signal(object)  # WorkflowGenerationResult

    def __init__(
        self,
        prompt: str,
        model_id: str,
        credential_id: Optional[str] = None,
        existing_workflow: Optional[Dict[str, Any]] = None,
        canvas_state: Optional[Dict[str, Any]] = None,
        is_edit: bool = False,
    ) -> None:
        super().__init__()
        self._prompt = prompt
        self._model_id = model_id
        self._credential_id = credential_id
        self._existing_workflow = existing_workflow
        self._canvas_state = canvas_state
        self._is_edit = is_edit

    def _get_api_key_from_credential(self) -> Optional[str]:
        """Retrieve API key from credential store."""
        if not self._credential_id:
            return None

        try:
            from casare_rpa.infrastructure.security.credential_store import (
                get_credential_store,
            )

            store = get_credential_store()
            cred_data = store.get_credential(self._credential_id)

            if cred_data:
                # Try common key field names
                return (
                    cred_data.get("api_key")
                    or cred_data.get("key")
                    or cred_data.get("token")
                    or cred_data.get("secret")
                )
        except Exception as e:
            logger.warning(f"Could not retrieve credential: {e}")

        return None

    def run(self) -> None:
        """Execute workflow generation with real credentials."""
        try:
            from casare_rpa.infrastructure.ai.smart_agent import SmartWorkflowAgent
            from casare_rpa.infrastructure.resources.llm_resource_manager import (
                LLMResourceManager,
                LLMConfig,
                LLMProvider,
            )

            # Get API key from credential store
            api_key = self._get_api_key_from_credential()

            if not api_key:
                logger.warning(
                    f"No API key found for credential {self._credential_id}, "
                    "falling back to environment/auto-detection"
                )

            # Configure LLM client with the credential
            llm_client = LLMResourceManager()

            # Detect provider from model ID
            model_lower = self._model_id.lower()
            if model_lower.startswith("gemini") or "gemini" in model_lower:
                provider = LLMProvider.CUSTOM  # Gemini uses custom base
            elif model_lower.startswith("gpt") or model_lower.startswith("o1"):
                provider = LLMProvider.OPENAI
            elif model_lower.startswith("claude"):
                provider = LLMProvider.ANTHROPIC
            else:
                provider = LLMProvider.OPENAI  # Default

            config = LLMConfig(
                provider=provider,
                model=self._model_id,
                api_key=api_key,
            )
            llm_client.configure(config)

            logger.info(
                f"Starting workflow generation with model={self._model_id}, "
                f"credential={self._credential_id[:8] if self._credential_id else 'None'}..."
            )

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                agent = SmartWorkflowAgent(llm_client=llm_client, max_retries=3)
                result = loop.run_until_complete(
                    agent.generate_workflow(
                        user_prompt=self._prompt,
                        existing_workflow=self._existing_workflow,
                        canvas_state=self._canvas_state,
                        is_edit=self._is_edit,
                        model=self._model_id,
                    )
                )
                self.finished.emit(result)
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Workflow generation error: {e}", exc_info=True)
            # Create error result
            from casare_rpa.infrastructure.ai.smart_agent import (
                WorkflowGenerationResult,
            )

            error_result = WorkflowGenerationResult(
                success=False,
                error=str(e),
                attempts=0,
            )
            self.finished.emit(error_result)


class WorkflowGenerationThread(QThread):
    """Thread wrapper for workflow generation worker."""

    finished = Signal(object)  # WorkflowGenerationResult

    def __init__(
        self,
        prompt: str,
        model_id: str,
        credential_id: Optional[str] = None,
        existing_workflow: Optional[Dict[str, Any]] = None,
        canvas_state: Optional[Dict[str, Any]] = None,
        is_edit: bool = False,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._worker = WorkflowGenerationWorker(
            prompt=prompt,
            model_id=model_id,
            credential_id=credential_id,
            existing_workflow=existing_workflow,
            canvas_state=canvas_state,
            is_edit=is_edit,
        )

    def run(self) -> None:
        self._worker.finished.connect(self.finished.emit)
        self._worker.run()


class AIAssistantDock(QDockWidget):
    """
    Dockable AI Assistant panel for natural language workflow generation.

    Provides:
    - Credential selector for AI providers
    - Conversational interface for workflow requests
    - Real-time validation feedback
    - Workflow preview with append/regenerate actions

    Signals:
        workflow_ready(dict): Emitted when valid workflow is generated
        append_requested(dict): Emitted when user clicks append
        generation_started(): Emitted when AI generation begins
        generation_finished(bool): Emitted when generation completes (success/fail)
        credential_changed(str): Emitted when selected credential changes
    """

    # Signals
    workflow_ready = Signal(dict)
    append_requested = Signal(dict)
    generation_started = Signal()
    generation_finished = Signal(bool)
    credential_changed = Signal(str)

    # Supported AI provider tags (lowercase as stored in credential store)
    # Maps credential tag -> display label
    SUPPORTED_PROVIDER_TAGS = {
        "google": "Google AI",
        "openai": "OpenAI",
    }

    # Available AI models by provider (model_id, display_name)
    # Model IDs use LiteLLM format: gemini/<model-name>
    GOOGLE_AI_MODELS = [
        ("gemini/gemini-3-pro-preview", "Gemini 3 Pro (Preview)"),
        ("gemini/gemini-flash-latest", "Gemini Flash (Latest)"),
        ("gemini/gemini-flash-lite-latest", "Gemini Flash Lite"),
    ]

    OPENAI_MODELS = [
        ("gpt-4o", "GPT-4o (Best)"),
        ("gpt-4o-mini", "GPT-4o Mini (Fast)"),
        ("gpt-4-turbo", "GPT-4 Turbo"),
    ]

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        embedded: bool = False,
    ) -> None:
        """
        Initialize the AI Assistant dock.

        Args:
            parent: Optional parent widget
            embedded: If True, behave as QWidget for embedding in tab panels
        """
        self._embedded = embedded
        self._credential_store = None
        self._current_credential_id: Optional[str] = None
        self._current_model_id: Optional[str] = None
        self._current_provider: Optional[str] = None
        self._current_workflow: Optional[Dict[str, Any]] = None
        self._is_generating = False
        self._generation_thread: Optional[WorkflowGenerationThread] = None
        self._last_prompt: Optional[str] = None
        self._auto_append = True  # Auto-append workflows to canvas

        if embedded:
            QWidget.__init__(self, parent)
        else:
            super().__init__("AI Assistant", parent)
            self.setObjectName("AIAssistantDock")

        if not embedded:
            self._setup_dock()
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()
        self._load_credentials()

        logger.debug("AIAssistantDock initialized")

    def _get_credential_store(self):
        """Lazy-load the credential store."""
        if self._credential_store is None:
            try:
                from casare_rpa.infrastructure.security.credential_store import (
                    get_credential_store,
                )

                self._credential_store = get_credential_store()
            except Exception as e:
                logger.error(f"Failed to load credential store: {e}")
        return self._credential_store

    def _get_main_window(self):
        """Get reference to main window."""
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, "_get_workflow_data"):
                return parent
            parent = parent.parent() if hasattr(parent, "parent") else None
        return None

    def _get_canvas_state(self) -> Optional[Dict[str, Any]]:
        """
        Get current canvas state for context.

        Returns simplified representation of nodes on canvas for AI context.
        """
        main_window = self._get_main_window()
        if not main_window:
            return None

        try:
            workflow_data = main_window._get_workflow_data()
            if not workflow_data:
                return None

            # Simplify for AI context
            nodes = workflow_data.get("nodes", {})
            simplified_nodes = {}
            for node_id, node_data in nodes.items():
                # Extract just the relevant info for AI
                custom = node_data.get("custom", {})
                simplified_nodes[custom.get("node_id", node_id)] = {
                    "type": node_data.get("type_", "")
                    .split(".")[-1]
                    .replace("Visual", ""),
                    "name": node_data.get("name", ""),
                    "properties": {
                        k: v
                        for k, v in custom.items()
                        if k
                        not in (
                            "node_id",
                            "status",
                            "_is_running",
                            "_is_completed",
                            "_disabled",
                        )
                    },
                    "position": node_data.get("pos", [0, 0]),
                }

            return {
                "nodes": simplified_nodes,
                "node_count": len(simplified_nodes),
            }
        except Exception as e:
            logger.debug(f"Failed to get canvas state: {e}")
            return None

    def _is_edit_request(self, prompt: str) -> bool:
        """
        Detect if user is requesting edits to existing nodes.

        Args:
            prompt: User's prompt text

        Returns:
            True if this looks like an edit request
        """
        prompt_lower = prompt.lower()

        # Edit keywords
        edit_keywords = [
            "change",
            "modify",
            "update",
            "edit",
            "replace",
            "instead of",
            "rather than",
            "switch to",
            "swap",
            "set to",
            "make it",
            "turn into",
        ]

        # Check for edit keywords
        for keyword in edit_keywords:
            if keyword in prompt_lower:
                return True

        return False

    def _setup_dock(self) -> None:
        """Configure dock widget properties."""
        self.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea
        )
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.setMinimumWidth(320)
        self.setMinimumHeight(400)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        colors = Theme.get_colors()

        # Main container
        if self._embedded:
            container = self
            main_layout = QVBoxLayout(container)
        else:
            container = QWidget()
            main_layout = QVBoxLayout(container)

        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header section
        header = self._create_header()
        main_layout.addWidget(header)

        # Chat area (expandable)
        self._chat_area = ChatArea()
        self._chat_area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        main_layout.addWidget(self._chat_area, stretch=1)

        # Preview card (hidden initially)
        self._preview_card = PreviewCard()
        self._preview_card.setVisible(False)
        main_layout.addWidget(self._preview_card)

        # Input section
        input_section = self._create_input_section()
        main_layout.addWidget(input_section)

        # Status bar
        self._status_bar = self._create_status_bar()
        main_layout.addWidget(self._status_bar)

        if not self._embedded:
            self.setWidget(container)

    def _create_header(self) -> QFrame:
        """Create the header with credential selector."""
        colors = Theme.get_colors()
        spacing = Theme.get_spacing()

        header = QFrame()
        header.setObjectName("AIAssistantHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(spacing.sm, spacing.sm, spacing.sm, spacing.sm)
        header_layout.setSpacing(spacing.xs)

        # Title row
        title_row = QHBoxLayout()
        title_label = QLabel("AI Workflow Assistant")
        title_label.setObjectName("AIAssistantTitle")
        font = title_label.font()
        font.setWeight(QFont.Weight.Bold)
        font.setPointSize(Theme.get_font_sizes().lg)
        title_label.setFont(font)
        title_row.addWidget(title_label)
        title_row.addStretch()

        # Clear chat button
        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setObjectName("ClearChatButton")
        self._clear_btn.setToolTip("Clear conversation history")
        self._clear_btn.setFixedSize(60, 24)
        title_row.addWidget(self._clear_btn)

        header_layout.addLayout(title_row)

        # Credential selector row
        cred_row = QHBoxLayout()
        cred_label = QLabel("AI Provider:")
        cred_label.setObjectName("CredentialLabel")
        cred_row.addWidget(cred_label)

        self._credential_combo = QComboBox()
        self._credential_combo.setObjectName("CredentialCombo")
        self._credential_combo.setToolTip("Select AI credential (Google AI or OpenAI)")
        self._credential_combo.setMinimumWidth(180)
        self._credential_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        cred_row.addWidget(self._credential_combo, stretch=1)

        # Refresh credentials button
        self._refresh_cred_btn = QPushButton("R")
        self._refresh_cred_btn.setObjectName("RefreshCredButton")
        self._refresh_cred_btn.setToolTip("Refresh credentials")
        self._refresh_cred_btn.setFixedSize(28, 28)
        cred_row.addWidget(self._refresh_cred_btn)

        header_layout.addLayout(cred_row)

        # Model selector row
        model_row = QHBoxLayout()
        model_label = QLabel("Model:")
        model_label.setObjectName("ModelLabel")
        model_row.addWidget(model_label)

        self._model_combo = QComboBox()
        self._model_combo.setObjectName("ModelCombo")
        self._model_combo.setToolTip("Select AI model for generation")
        self._model_combo.setMinimumWidth(180)
        self._model_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._model_combo.setEnabled(False)  # Disabled until credential selected
        model_row.addWidget(self._model_combo, stretch=1)

        header_layout.addLayout(model_row)

        return header

    def _create_input_section(self) -> QFrame:
        """Create the input field and send button."""
        colors = Theme.get_colors()
        spacing = Theme.get_spacing()

        input_frame = QFrame()
        input_frame.setObjectName("InputSection")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(spacing.sm, spacing.sm, spacing.sm, spacing.sm)
        input_layout.setSpacing(spacing.xs)

        # Input field
        self._input_field = QLineEdit()
        self._input_field.setObjectName("ChatInput")
        self._input_field.setPlaceholderText(
            "Describe the workflow you want to create..."
        )
        self._input_field.setMinimumHeight(36)
        input_layout.addWidget(self._input_field, stretch=1)

        # Send button
        self._send_btn = QPushButton("Send")
        self._send_btn.setObjectName("SendButton")
        self._send_btn.setMinimumHeight(36)
        self._send_btn.setMinimumWidth(70)
        input_layout.addWidget(self._send_btn)

        return input_frame

    def _create_status_bar(self) -> QFrame:
        """Create the status bar showing validation progress."""
        colors = Theme.get_colors()
        spacing = Theme.get_spacing()

        status_frame = QFrame()
        status_frame.setObjectName("StatusBar")
        status_frame.setFixedHeight(28)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(spacing.sm, 0, spacing.sm, 0)

        # Status icon (animated dot or checkmark)
        self._status_icon = QLabel()
        self._status_icon.setObjectName("StatusIcon")
        self._status_icon.setFixedSize(16, 16)
        self._status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self._status_icon)

        # Status text
        self._status_label = QLabel("Ready")
        self._status_label.setObjectName("StatusLabel")
        status_layout.addWidget(self._status_label, stretch=1)

        # Validation badge (hidden initially)
        self._validation_badge = QLabel()
        self._validation_badge.setObjectName("ValidationBadge")
        self._validation_badge.setVisible(False)
        status_layout.addWidget(self._validation_badge)

        return status_frame

    def _apply_styles(self) -> None:
        """Apply theme styling."""
        colors = Theme.get_colors()
        radius = Theme.get_border_radius()

        self.setStyleSheet(f"""
            /* Dock Widget */
            QDockWidget {{
                background-color: {colors.background_alt};
                color: {colors.text_primary};
            }}
            QDockWidget::title {{
                background-color: {colors.dock_title_bg};
                color: {colors.dock_title_text};
                padding: 8px 12px;
                font-weight: 600;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-bottom: 1px solid {colors.border_dark};
            }}

            /* Header Section */
            #AIAssistantHeader {{
                background-color: {colors.surface};
                border-bottom: 1px solid {colors.border};
            }}
            #AIAssistantTitle {{
                color: {colors.text_primary};
            }}
            #CredentialLabel {{
                color: {colors.text_secondary};
                font-size: 11px;
            }}
            #ClearChatButton {{
                background-color: transparent;
                color: {colors.text_secondary};
                border: 1px solid {colors.border};
                border-radius: {radius.sm}px;
                font-size: 11px;
            }}
            #ClearChatButton:hover {{
                background-color: {colors.surface_hover};
                color: {colors.text_primary};
            }}
            #RefreshCredButton {{
                background-color: {colors.surface};
                color: {colors.text_secondary};
                border: 1px solid {colors.border};
                border-radius: {radius.sm}px;
                font-weight: bold;
            }}
            #RefreshCredButton:hover {{
                background-color: {colors.surface_hover};
                color: {colors.text_primary};
            }}

            /* Credential Combo */
            #CredentialCombo {{
                background-color: {colors.background};
                color: {colors.text_primary};
                border: 1px solid {colors.border};
                border-radius: {radius.sm}px;
                padding: 6px 10px;
                min-height: 24px;
            }}
            #CredentialCombo:hover {{
                border-color: {colors.border_light};
            }}
            #CredentialCombo:focus {{
                border-color: {colors.border_focus};
            }}
            #CredentialCombo::drop-down {{
                border: none;
                width: 20px;
            }}
            #CredentialCombo::down-arrow {{
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {colors.text_secondary};
                margin-right: 6px;
            }}
            #CredentialCombo QAbstractItemView {{
                background-color: {colors.surface};
                border: 1px solid {colors.border};
                selection-background-color: {colors.accent};
                outline: none;
            }}

            /* Model Combo */
            #ModelLabel {{
                color: {colors.text_secondary};
                font-size: 11px;
            }}
            #ModelCombo {{
                background-color: {colors.background};
                color: {colors.text_primary};
                border: 1px solid {colors.border};
                border-radius: {radius.sm}px;
                padding: 6px 10px;
                min-height: 24px;
            }}
            #ModelCombo:hover {{
                border-color: {colors.border_light};
            }}
            #ModelCombo:focus {{
                border-color: {colors.border_focus};
            }}
            #ModelCombo:disabled {{
                background-color: {colors.surface};
                color: {colors.text_disabled};
            }}
            #ModelCombo::drop-down {{
                border: none;
                width: 20px;
            }}
            #ModelCombo::down-arrow {{
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {colors.text_secondary};
                margin-right: 6px;
            }}
            #ModelCombo QAbstractItemView {{
                background-color: {colors.surface};
                border: 1px solid {colors.border};
                selection-background-color: {colors.accent};
                outline: none;
            }}

            /* Input Section */
            #InputSection {{
                background-color: {colors.surface};
                border-top: 1px solid {colors.border};
            }}
            #ChatInput {{
                background-color: {colors.background};
                color: {colors.text_primary};
                border: 1px solid {colors.border};
                border-radius: {radius.sm}px;
                padding: 8px 12px;
                selection-background-color: {colors.accent};
            }}
            #ChatInput:focus {{
                border-color: {colors.border_focus};
            }}
            #ChatInput:disabled {{
                background-color: {colors.surface};
                color: {colors.text_disabled};
            }}
            #SendButton {{
                background-color: {colors.accent};
                color: #FFFFFF;
                border: none;
                border-radius: {radius.sm}px;
                font-weight: 600;
            }}
            #SendButton:hover {{
                background-color: {colors.accent_hover};
            }}
            #SendButton:pressed {{
                background-color: {colors.primary_pressed};
            }}
            #SendButton:disabled {{
                background-color: {colors.secondary};
                color: {colors.text_disabled};
            }}

            /* Status Bar */
            #StatusBar {{
                background-color: {colors.background};
                border-top: 1px solid {colors.border_dark};
            }}
            #StatusIcon {{
                color: {colors.text_muted};
            }}
            #StatusLabel {{
                color: {colors.text_muted};
                font-size: 11px;
            }}
            #ValidationBadge {{
                background-color: {colors.success};
                color: #FFFFFF;
                font-size: 10px;
                font-weight: bold;
                padding: 2px 6px;
                border-radius: {radius.sm}px;
            }}
        """)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        # Send button
        self._send_btn.clicked.connect(self._on_send_clicked)

        # Input field Enter key
        self._input_field.returnPressed.connect(self._on_send_clicked)

        # Clear chat
        self._clear_btn.clicked.connect(self._clear_chat)

        # Credential selector
        self._credential_combo.currentIndexChanged.connect(self._on_credential_changed)

        # Model selector
        self._model_combo.currentIndexChanged.connect(self._on_model_changed)

        # Refresh credentials
        self._refresh_cred_btn.clicked.connect(self._load_credentials)

        # Preview card signals
        self._preview_card.append_clicked.connect(self._on_append_clicked)
        self._preview_card.regenerate_clicked.connect(self._on_regenerate_clicked)

    def _load_credentials(self) -> None:
        """Load AI provider credentials into combo box."""
        self._credential_combo.clear()
        self._credential_combo.addItem("Select AI Provider...", None)

        store = self._get_credential_store()
        if not store:
            logger.warning("Credential store not available")
            return

        try:
            # Get LLM credentials (category="llm")
            credentials = store.list_credentials(category="llm")
            ai_creds: List[Dict[str, Any]] = []

            for cred in credentials:
                cred_id = cred.get("id", "")
                matched_provider = None

                # Method 1: Check tags for supported providers
                tags = cred.get("tags", [])
                for tag in tags:
                    tag_lower = tag.lower()
                    if tag_lower in self.SUPPORTED_PROVIDER_TAGS:
                        matched_provider = tag_lower
                        break

                # Method 2: If no tag match, try to get provider from encrypted data
                if not matched_provider and cred_id:
                    try:
                        cred_data = store.get_credential(cred_id)
                        if cred_data:
                            provider = cred_data.get("provider", "").lower()
                            if provider in self.SUPPORTED_PROVIDER_TAGS:
                                matched_provider = provider
                    except Exception as e:
                        logger.debug(
                            f"Could not get provider from credential data: {e}"
                        )

                if matched_provider:
                    cred["_provider_tag"] = matched_provider
                    ai_creds.append(cred)

            # Sort by name
            ai_creds.sort(key=lambda c: c.get("name", "").lower())

            for cred in ai_creds:
                cred_id = cred.get("id", "")
                name = cred.get("name", "Unknown")
                provider_tag = cred.get("_provider_tag", "")

                # Get display label from mapping
                provider_label = self.SUPPORTED_PROVIDER_TAGS.get(provider_tag, "AI")
                display_text = f"{name} ({provider_label})"

                self._credential_combo.addItem(display_text, cred_id)

            logger.debug(f"Loaded {len(ai_creds)} AI credentials")

        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")

    def _on_credential_changed(self, index: int) -> None:
        """Handle credential selection change."""
        cred_id = self._credential_combo.currentData()
        self._current_credential_id = cred_id
        self.credential_changed.emit(cred_id or "")

        # Determine provider from credential
        provider = None
        if cred_id:
            # Get provider tag from the credential info stored earlier
            for i in range(self._credential_combo.count()):
                if self._credential_combo.itemData(i) == cred_id:
                    text = self._credential_combo.itemText(i)
                    if "Google" in text:
                        provider = "google"
                    elif "OpenAI" in text:
                        provider = "openai"
                    break

        self._current_provider = provider
        self._load_models_for_provider(provider)

        # Update status
        if cred_id:
            self._set_status("Ready", "ready")
            self._input_field.setEnabled(True)
            self._send_btn.setEnabled(True)
            self._model_combo.setEnabled(True)
        else:
            self._set_status("Select an AI provider to start", "idle")
            self._input_field.setEnabled(False)
            self._send_btn.setEnabled(False)
            self._model_combo.setEnabled(False)

    def _load_models_for_provider(self, provider: Optional[str]) -> None:
        """Load available models for the selected provider."""
        self._model_combo.clear()

        if not provider:
            self._model_combo.addItem("Select model...", None)
            self._current_model_id = None
            return

        if provider == "google":
            models = self.GOOGLE_AI_MODELS
        elif provider == "openai":
            models = self.OPENAI_MODELS
        else:
            models = []

        for model_id, display_name in models:
            self._model_combo.addItem(display_name, model_id)

        # Select first model by default
        if models:
            self._current_model_id = models[0][0]

        logger.debug(f"Loaded {len(models)} models for provider: {provider}")

    def _on_model_changed(self, index: int) -> None:
        """Handle model selection change."""
        model_id = self._model_combo.currentData()
        self._current_model_id = model_id

        if model_id:
            logger.debug(f"Selected model: {model_id}")

    def _on_send_clicked(self) -> None:
        """Handle send button click."""
        prompt = self._input_field.text().strip()
        if not prompt:
            return

        if not self._current_credential_id:
            self._set_status("Please select an AI provider first", "warning")
            return

        if self._is_generating:
            return

        # Add user message
        self._chat_area.add_user_message(prompt)
        self._input_field.clear()

        # Start generation
        self._start_generation(prompt)

    def _start_generation(self, prompt: str) -> None:
        """
        Start workflow generation using SmartWorkflowAgent.

        Spawns a background thread to run async LLM calls without blocking UI.
        """
        self._is_generating = True
        self._last_prompt = prompt
        self._set_status("Generating workflow...", "loading")
        self._send_btn.setEnabled(False)
        self._input_field.setEnabled(False)

        # Show thinking indicator
        self._chat_area.show_thinking()

        # Emit signal
        self.generation_started.emit()

        # Get model ID (default to gpt-4o-mini if not selected)
        model_id = self._current_model_id or "gpt-4o-mini"

        # Get credential ID from selection
        credential_id = self._current_credential_id

        if not credential_id:
            self._chat_area.hide_thinking()
            self._chat_area.add_ai_message(
                "Please select an AI provider credential before generating workflows."
            )
            self._finish_generation(False)
            return

        # Get canvas state for context
        canvas_state = self._get_canvas_state()

        # Detect if this is an edit request
        is_edit = self._is_edit_request(prompt) and canvas_state is not None

        if is_edit:
            logger.info("Detected edit request - will modify existing nodes")
            self._set_status("Analyzing canvas and modifying...", "loading")

        # Create and start generation thread
        self._generation_thread = WorkflowGenerationThread(
            prompt=prompt,
            model_id=model_id,
            credential_id=credential_id,
            existing_workflow=None,
            canvas_state=canvas_state,
            is_edit=is_edit,
            parent=self,
        )
        self._generation_thread.finished.connect(self._on_generation_complete)
        self._generation_thread.start()

        mode = "edit" if is_edit else "generate"
        logger.info(
            f"Started workflow {mode}: {prompt[:50]}... "
            f"(model: {model_id}, credential: {credential_id[:8]}..., "
            f"canvas_nodes: {canvas_state.get('node_count', 0) if canvas_state else 0})"
        )

    def _on_generation_complete(self, result: "WorkflowGenerationResult") -> None:
        """
        Handle workflow generation result from background thread.

        Args:
            result: WorkflowGenerationResult from SmartWorkflowAgent
        """
        self._chat_area.hide_thinking()

        try:
            if result.success and result.workflow:
                # Count nodes and connections for message
                nodes = result.workflow.get("nodes", {})
                connections = result.workflow.get("connections", [])
                node_count = len(nodes) if isinstance(nodes, (dict, list)) else 0
                conn_count = len(connections) if isinstance(connections, list) else 0

                # Build response message
                response = (
                    f"I've created a workflow based on your request.\n\n"
                    f"**Nodes:** {node_count}\n"
                    f"**Connections:** {conn_count}\n"
                    f"**Attempts:** {result.attempts}"
                )
                self._chat_area.add_ai_message(response)

                # Store workflow and log info
                try:
                    self._current_workflow = result.workflow

                    # Log detailed workflow info for debugging
                    nodes = result.workflow.get("nodes", {})
                    if isinstance(nodes, dict):
                        node_types = [
                            n.get("node_type", n.get("type", "?"))
                            for n in nodes.values()
                        ]
                    else:
                        node_types = [
                            n.get("node_type", n.get("type", "?")) for n in nodes
                        ]
                    logger.info(f"AI generated node types: {node_types}")

                    # Auto-append to canvas (skip preview card)
                    already_appended = False
                    if self._auto_append and node_count > 0:
                        logger.info("Auto-appending workflow to canvas...")
                        self.append_requested.emit(result.workflow)
                        # Don't show preview card - workflow is already on canvas
                        self._preview_card.setVisible(False)
                        already_appended = True
                    else:
                        # Show preview card for manual append
                        self._preview_card.set_workflow(result.workflow)
                        self._preview_card.setVisible(True)
                        self._preview_card.updateGeometry()
                        self._preview_card.adjustSize()
                        logger.debug("Preview card shown")
                except Exception as e:
                    logger.error(f"Failed to process workflow: {e}", exc_info=True)
                    self._chat_area.add_system_message(
                        f"Error: {e}. Workflow may not have been added."
                    )
                    already_appended = False

                # Update status (skip workflow_ready if already appended)
                self._finish_generation(True, skip_workflow_ready=already_appended)
            else:
                # Generation failed
                error_msg = result.error or "Unknown error occurred"
                attempts_info = (
                    f" after {result.attempts} attempt(s)"
                    if result.attempts > 0
                    else ""
                )

                response = (
                    f"I couldn't generate the workflow{attempts_info}.\n\n"
                    f"**Error:** {error_msg}\n\n"
                    f"Please try rephrasing your request or check the AI provider settings."
                )
                self._chat_area.add_ai_message(response)
                self._finish_generation(False)
        except Exception as e:
            logger.error(f"Error handling generation result: {e}", exc_info=True)
            self._chat_area.add_ai_message(f"An error occurred: {e}")
            self._finish_generation(False)
        finally:
            # Cleanup thread reference - ALWAYS runs
            self._generation_thread = None

    def _finish_generation(
        self, success: bool, skip_workflow_ready: bool = False
    ) -> None:
        """Finish generation and update UI state.

        Args:
            success: Whether generation succeeded
            skip_workflow_ready: If True, don't emit workflow_ready signal
                (used when auto-append already emitted append_requested)
        """
        self._is_generating = False
        self._send_btn.setEnabled(True)
        self._input_field.setEnabled(True)
        self._input_field.setFocus()

        if success:
            self._set_status("Workflow generated", "success")
            self._show_validation_badge(True)
            self.generation_finished.emit(True)
            # Only emit workflow_ready if not already auto-appended
            if self._current_workflow and not skip_workflow_ready:
                self.workflow_ready.emit(self._current_workflow)
        else:
            self._set_status("Generation failed", "error")
            self.generation_finished.emit(False)

    def _on_append_clicked(self) -> None:
        """Handle append to canvas button click."""
        if self._current_workflow:
            self.append_requested.emit(self._current_workflow)
            self._preview_card.setVisible(False)
            self._chat_area.add_system_message("Workflow appended to canvas.")
            self._current_workflow = None
            self._set_status("Ready", "ready")
            self._show_validation_badge(False)

    def _on_regenerate_clicked(self) -> None:
        """Handle regenerate button click."""
        # Get the last user message
        last_prompt = self._chat_area.get_last_user_message()
        if last_prompt:
            self._preview_card.setVisible(False)
            self._start_generation(last_prompt)

    def _clear_chat(self) -> None:
        """Clear conversation history."""
        self._chat_area.clear_messages()
        self._preview_card.setVisible(False)
        self._current_workflow = None
        self._set_status("Ready", "ready")
        self._show_validation_badge(False)

    def _set_status(self, message: str, state: str = "idle") -> None:
        """Update status bar."""
        colors = Theme.get_colors()

        self._status_label.setText(message)

        # Update status icon based on state
        icons = {
            "idle": "",
            "ready": "",
            "loading": "",
            "success": "",
            "warning": "",
            "error": "",
        }

        state_colors = {
            "idle": colors.text_muted,
            "ready": colors.success,
            "loading": colors.warning,
            "success": colors.success,
            "warning": colors.warning,
            "error": colors.error,
        }

        icon_color = state_colors.get(state, colors.text_muted)
        self._status_icon.setStyleSheet(f"color: {icon_color};")

    def _show_validation_badge(self, show: bool) -> None:
        """Show/hide validation badge."""
        self._validation_badge.setVisible(show)
        if show:
            self._validation_badge.setText("Verified")

    # ==================== Public API ====================

    def set_workflow_result(
        self, workflow: Optional[Dict[str, Any]], success: bool, message: str = ""
    ) -> None:
        """
        Set the generated workflow result from external AI service.

        Args:
            workflow: Generated workflow dict or None on failure
            success: Whether generation was successful
            message: Response message to display
        """
        self._chat_area.hide_thinking()

        if success and workflow:
            self._chat_area.add_ai_message(
                message or "Workflow generated successfully."
            )
            self._current_workflow = workflow
            self._preview_card.set_workflow(workflow)
            self._preview_card.setVisible(True)
            self._finish_generation(True)
        else:
            self._chat_area.add_ai_message(message or "Failed to generate workflow.")
            self._finish_generation(False)

    def get_selected_credential_id(self) -> Optional[str]:
        """Get the currently selected credential ID."""
        return self._current_credential_id

    def get_selected_model_id(self) -> Optional[str]:
        """Get the currently selected model ID."""
        return self._current_model_id

    def get_selected_provider(self) -> Optional[str]:
        """Get the currently selected provider (google, openai)."""
        return self._current_provider

    def refresh_credentials(self) -> None:
        """Refresh the credentials list."""
        self._load_credentials()

    def is_generating(self) -> bool:
        """Check if currently generating."""
        return self._is_generating

    def cleanup(self) -> None:
        """Clean up resources."""
        # Stop any running generation thread
        if self._generation_thread and self._generation_thread.isRunning():
            logger.debug("Waiting for generation thread to finish...")
            self._generation_thread.quit()
            self._generation_thread.wait(3000)  # Wait up to 3 seconds
            if self._generation_thread.isRunning():
                logger.warning("Generation thread did not stop gracefully")
                self._generation_thread.terminate()
            self._generation_thread = None

        logger.debug("AIAssistantDock cleaned up")
