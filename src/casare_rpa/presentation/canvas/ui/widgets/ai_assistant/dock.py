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
- Multi-turn conversation support with intent classification
- Undo/redo for workflow changes
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from loguru import logger
from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS
from casare_rpa.presentation.canvas.theme_system.helpers import (
    margin_none,
    set_fixed_size,
    set_margins,
    set_min_size,
    set_spacing,
)
from casare_rpa.presentation.canvas.ui.widgets.ai_assistant.chat_area import ChatArea
from casare_rpa.presentation.canvas.ui.widgets.ai_assistant.preview_card import (
    PreviewCard,
)
from casare_rpa.presentation.canvas.ui.widgets.ai_settings_widget import (
    AISettingsWidget,
)

if TYPE_CHECKING:
    from casare_rpa.infrastructure.ai.agent import WorkflowGenerationResult
    from casare_rpa.infrastructure.ai.conversation_manager import ConversationManager
    from casare_rpa.infrastructure.ai.intent_classifier import IntentClassifier


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
        credential_id: str | None = None,
        provider: str | None = None,
        existing_workflow: dict[str, Any] | None = None,
        canvas_state: dict[str, Any] | None = None,
        is_edit: bool = False,
    ) -> None:
        super().__init__()
        self._prompt = prompt
        self._model_id = model_id
        self._credential_id = credential_id
        self._provider = provider
        self._existing_workflow = existing_workflow
        self._canvas_state = canvas_state
        self._is_edit = is_edit

    def _get_api_key_from_credential(self) -> str | None:
        """Retrieve API key from credential store."""
        if not self._credential_id:
            return None

        try:
            from casare_rpa.infrastructure.security.credential_store import (
                get_credential_store,
            )

            store = get_credential_store()
            # If explicit credential ID is provided
            if self._credential_id != "auto":
                cred_data = store.get_credential(self._credential_id)
                if cred_data:
                    return (
                        cred_data.get("api_key")
                        or cred_data.get("key")
                        or cred_data.get("token")
                        or cred_data.get("secret")
                    )

            # If "auto" or provider-based lookup needed
            if self._provider:
                # Map provider string to store key
                provider_key = self._provider.lower()
                if "openai" in provider_key:
                    provider_key = "openai"
                elif "anthropic" in provider_key:
                    provider_key = "anthropic"
                elif "openrouter" in provider_key:
                    provider_key = "openrouter"

                return store.get_api_key_by_provider(provider_key) or store.get_key(provider_key)

        except Exception as e:
            logger.warning(f"Could not retrieve credential: {e}")

        return None

    def run(self) -> None:
        """Execute workflow generation with real credentials."""
        try:
            from casare_rpa.infrastructure.ai.agent import SmartWorkflowAgent
            from casare_rpa.infrastructure.resources.llm_resource_manager import (
                LLMConfig,
                LLMProvider,
                LLMResourceManager,
            )

            # Configure LLM client with the credential
            llm_client = LLMResourceManager()

            # Determine provider enum
            provider = LLMProvider.OPENAI  # Default

            if self._provider:
                p_lower = self._provider.lower()
                if "openrouter" in p_lower:
                    provider = LLMProvider.OPENROUTER
                elif "anthropic" in p_lower:
                    provider = LLMProvider.ANTHROPIC
                elif "google" in p_lower or "gemini" in p_lower:
                    provider = LLMProvider.CUSTOM  # Google OAuth will be resolved via credential_id
                elif "ollama" in p_lower:
                    provider = LLMProvider.OLLAMA
                elif "openai" in p_lower:
                    provider = LLMProvider.OPENAI
            else:
                # Fallback to model name detection
                model_lower = self._model_id.lower()
                if model_lower.startswith("gemini") or "gemini" in model_lower:
                    provider = LLMProvider.CUSTOM
                elif model_lower.startswith("gpt") or model_lower.startswith("o1"):
                    provider = LLMProvider.OPENAI
                elif model_lower.startswith("claude"):
                    provider = LLMProvider.ANTHROPIC

            # Check for model mismatch situations (e.g. Gemini without OAuth credential -> OpenRouter)
            if (
                not self._credential_id
                and (self._model_id.startswith("google/") or "gemini" in self._model_id)
                and not self._model_id.startswith("openrouter/")
            ):
                self._model_id = f"openrouter/{self._model_id}"
                provider = LLMProvider.OPENROUTER

            # Pass credential_id to config for dynamic resolution
            config = LLMConfig(
                provider=provider, model=self._model_id, credential_id=self._credential_id
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
            from casare_rpa.infrastructure.ai.agent import (
                WorkflowGenerationResult,
            )

            error_result = WorkflowGenerationResult(
                success=False,
                error=str(e),
                attempts=0,
            )
            self.finished.emit(error_result)


class AutoResizingTextEdit(QTextEdit):
    """
    Text edit that auto-resizes vertically based on content.
    Enter sends, Shift+Enter adds new line.
    """

    returnPressed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(False)
        self.setPlaceholderText("Message AI Assistant...")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.document().documentLayout().documentSizeChanged.connect(self._adjust_height)
        self._min_height = TOKENS.sizes.input_md + TOKENS.sizes.spacing.xs
        self._max_height = TOKENS.sizes.input_lg + TOKENS.sizes.dialog_height_md
        self.setFixedHeight(self._min_height)

    def _adjust_height(self):
        doc_height = self.document().size().height()
        new_height = min(max(doc_height + 10, self._min_height), self._max_height)
        self.setFixedHeight(int(new_height))

    def keyPressEvent(self, event):
        # Enter sends, Shift+Enter adds new line
        if event.key() == Qt.Key.Key_Return:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                # Shift+Enter - insert new line
                super().keyPressEvent(event)
            else:
                # Plain Enter - send message
                self.returnPressed.emit()
                event.accept()
        else:
            super().keyPressEvent(event)


class InputBar(QFrame):
    """
    iMessage-style input bar with clean rounded design and send arrow.
    """

    sendClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        colors = THEME

        # Container style with ElevenLabs design tokens
        self.setStyleSheet(f"""
            InputBar {{
                background-color: {colors.background};
                border-top: none;
            }}
            QFrame#InputContainer {{
                background-color: {colors.bg_elevated};
                border: 1px solid {colors.border};
                border-radius: {TOKENS.radius.xl}px;  /* 20px - ElevenLabs radius-xl */
            }}
            QFrame#InputContainer:focus-within {{
                border: 1px solid {colors.accent};
            }}
            QPushButton#SendButton {{
                background-color: {THEME.primary};
                color: white;
                border: none;
                border-radius: {TOKENS.radius.xl}px;  /* 20px - pill shape */
                font-family: {TOKENS.typography.family};
                font-weight: 900;
                font-size: {TOKENS.typography.xxl}px;
            }}
            QPushButton#SendButton:hover {{
                background-color: {THEME.primary_hover};
            }}
            QPushButton#SendButton:pressed {{
                background-color: {THEME.primary_pressed};
            }}
            QPushButton#SendButton:disabled {{
                background-color: {colors.surface};
                color: {colors.text_disabled};
            }}
        """)

        layout = QVBoxLayout(self)
        set_margins(
            layout, (TOKENS.spacing.xl, TOKENS.spacing.sm, TOKENS.spacing.xl, TOKENS.spacing.sm)
        )

        # Rounded Container
        self._container = QFrame()
        self._container.setObjectName("InputContainer")
        container_layout = QHBoxLayout(self._container)
        set_margins(
            container_layout,
            (TOKENS.spacing.xl, TOKENS.spacing.sm, TOKENS.spacing.sm, TOKENS.spacing.sm),
        )
        set_spacing(container_layout, TOKENS.spacing.sm)

        # Text Edit
        self._text_edit = AutoResizingTextEdit()
        self._text_edit.setFrameStyle(QFrame.Shape.NoFrame)
        self._text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                color: {colors.text_primary};
                font-family: {TOKENS.typography.family};
                font-size: {TOKENS.typography.body_lg}px;  /* 14px */
            }}
        """)
        container_layout.addWidget(self._text_edit)

        # Send Button with arrow icon - centered vertically
        self._send_btn = QPushButton("➤")
        self._send_btn.setObjectName("SendButton")
        set_fixed_size(
            self._send_btn,
            TOKENS.sizes.input_lg + TOKENS.sizes.button_md,
            TOKENS.sizes.input_lg + TOKENS.sizes.button_md,
        )
        self._send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._send_btn.clicked.connect(self.sendClicked.emit)
        self._text_edit.returnPressed.connect(self.sendClicked.emit)

        container_layout.addWidget(self._send_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self._container)

    def text(self) -> str:
        return self._text_edit.toPlainText()

    def clear(self):
        self._text_edit.clear()

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self._text_edit.setEnabled(enabled)
        self._send_btn.setEnabled(enabled)

    def setPlaceholderText(self, text: str):
        self._text_edit.setPlaceholderText(text)


class WorkflowGenerationThread(QThread):
    """Thread wrapper for workflow generation worker."""

    finished = Signal(object)  # WorkflowGenerationResult

    def __init__(
        self,
        prompt: str,
        model_id: str,
        credential_id: str | None = None,
        provider: str | None = None,
        existing_workflow: dict[str, Any] | None = None,
        canvas_state: dict[str, Any] | None = None,
        is_edit: bool = False,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._worker = WorkflowGenerationWorker(
            prompt=prompt,
            model_id=model_id,
            credential_id=credential_id,
            provider=provider,
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

    def __init__(
        self,
        parent: QWidget | None = None,
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
        self._current_credential_id: str | None = None
        self._current_model_id: str | None = None
        self._current_provider: str | None = None
        self._current_workflow: dict[str, Any] | None = None
        self._is_generating = False
        self._generation_thread: WorkflowGenerationThread | None = None
        self._last_prompt: str | None = None
        self._auto_append = True  # Auto-append workflows to canvas

        # Multi-turn conversation support
        self._conversation_manager: ConversationManager | None = None
        self._intent_classifier: IntentClassifier | None = None
        self._init_conversation_support()

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

        logger.debug("AIAssistantDock initialized with conversation support")

    def _init_conversation_support(self) -> None:
        """Initialize conversation manager and intent classifier."""
        try:
            from casare_rpa.infrastructure.ai.conversation_manager import (
                ConversationManager,
            )
            from casare_rpa.infrastructure.ai.intent_classifier import (
                IntentClassifier,
            )

            self._conversation_manager = ConversationManager(
                max_messages=20,
                max_workflow_history=10,
            )
            self._intent_classifier = IntentClassifier(
                confidence_threshold=0.7,
            )
            logger.debug("Conversation support initialized")
        except ImportError as e:
            logger.warning(f"Could not initialize conversation support: {e}")
            self._conversation_manager = None
            self._intent_classifier = None
        except Exception as e:
            logger.error(f"Error initializing conversation support: {e}")
            self._conversation_manager = None
            self._intent_classifier = None

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

    def _get_canvas_state(self) -> dict[str, Any] | None:
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
                simplified_nodes[node_id] = {
                    "type": node_data.get("node_type", ""),
                    "name": node_data.get("name", ""),
                    "properties": node_data.get("config", {}),
                    "position": node_data.get("position", [0, 0]),
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

        Uses intent classifier if available, falls back to keyword matching.

        Args:
            prompt: User's prompt text

        Returns:
            True if this looks like an edit request
        """
        # Try using intent classifier
        if self._intent_classifier is not None:
            from casare_rpa.infrastructure.ai.conversation_manager import UserIntent

            has_workflow = self._current_workflow is not None
            classification = self._intent_classifier.classify(prompt, has_workflow)

            edit_intents = {
                UserIntent.MODIFY_WORKFLOW,
                UserIntent.ADD_NODE,
                UserIntent.REMOVE_NODE,
                UserIntent.REFINE,
            }

            if classification.intent in edit_intents:
                return True

        # Fallback to keyword matching
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

    def _classify_intent(self, prompt: str):
        """
        Classify user intent from prompt.

        Args:
            prompt: User's prompt text

        Returns:
            IntentClassification or None if classifier not available
        """
        if self._intent_classifier is None:
            return None

        has_workflow = self._current_workflow is not None
        return self._intent_classifier.classify(prompt, has_workflow)

    def _setup_dock(self) -> None:
        """Configure dock widget properties."""
        self.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea
            | Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.BottomDockWidgetArea
            | Qt.DockWidgetArea.TopDockWidgetArea
        )
        # Dock-only: NO DockWidgetFloatable (v2 requirement)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
            # NO DockWidgetFloatable - dock-only enforcement (v2 requirement)
        )
        set_min_size(
            self,
            TOKENS.sizes.panel_default_width,
            TOKENS.sizes.dialog_sm_width + TOKENS.sizes.dialog_md_width,
        )
        # Set reasonable initial floating size
        self.topLevelChanged.connect(self._on_top_level_changed)

    @Slot(bool)
    def _on_top_level_changed(self, top_level: bool) -> None:
        """Handle dock floating state change."""
        if top_level:
            self.resize(
                TOKENS.sizes.dialog_md_width,
                TOKENS.sizes.dialog_height_lg + TOKENS.sizes.dialog_height_sm,
            )

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        THEME

        # Main container
        if self._embedded:
            container = self
            main_layout = QVBoxLayout(container)
        else:
            container = QWidget()
            main_layout = QVBoxLayout(container)

        margin_none(main_layout)
        set_spacing(main_layout, TOKENS.spacing.xs)

        # Header section
        header = self._create_header()
        main_layout.addWidget(header)

        # Chat area (expandable)
        self._chat_area = ChatArea()
        self._chat_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self._chat_area, stretch=1)

        # Preview card (hidden initially)
        self._preview_card = PreviewCard()
        self._preview_card.setVisible(False)
        main_layout.addWidget(self._preview_card)

        # Input Bar (Replaces old input section + status bar)
        self._input_bar = InputBar()
        main_layout.addWidget(self._input_bar)

        if not self._embedded:
            self.setWidget(container)

    def _create_header(self) -> QFrame:
        """Create the header with title and collapsible settings."""
        from PySide6.QtWidgets import QCheckBox, QVBoxLayout

        THEME
        THEME

        header = QFrame()
        header.setObjectName("AIAssistantHeader")
        header_layout = QVBoxLayout(header)
        set_margins(
            header_layout,
            (TOKENS.spacing.md, TOKENS.spacing.sm, TOKENS.spacing.md, TOKENS.spacing.sm),
        )
        set_spacing(header_layout, TOKENS.spacing.xs)

        # Title row with settings toggle
        title_row = QHBoxLayout()
        title_label = QLabel("AI Assistant")
        title_label.setObjectName("AIAssistantTitle")
        font = title_label.font()
        font.setWeight(QFont.Weight.Bold)
        font.setFamily(TOKENS.typography.ui)
        font.setPointSize(TOKENS.typography.body)
        title_label.setFont(font)
        title_row.addWidget(title_label)
        title_row.addStretch()

        # Settings toggle button (gear icon)
        self._settings_toggle_btn = QPushButton("⚙")
        self._settings_toggle_btn.setObjectName("SettingsToggleBtn")
        self._settings_toggle_btn.setToolTip("AI Settings")
        set_fixed_size(self._settings_toggle_btn, TOKENS.sizes.button_md, TOKENS.sizes.button_md)
        self._settings_toggle_btn.setCheckable(True)
        self._settings_toggle_btn.setChecked(False)
        title_row.addWidget(self._settings_toggle_btn)

        # Debug toggle checkbox
        self._debug_checkbox = QCheckBox("Debug")
        self._debug_checkbox.setObjectName("DebugCheckbox")
        self._debug_checkbox.setToolTip("Show raw LLM output for debugging")
        self._debug_checkbox.setChecked(False)
        title_row.addWidget(self._debug_checkbox)

        # Clear chat button
        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setObjectName("ClearChatButton")
        self._clear_btn.setToolTip("Clear conversation history")
        set_min_size(
            self._clear_btn,
            TOKENS.sizes.button_md + TOKENS.sizes.button_md,
            TOKENS.sizes.button_md,
        )
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        title_row.addWidget(self._clear_btn)

        header_layout.addLayout(title_row)

        # Collapsible settings panel
        self._settings_panel = QFrame()
        self._settings_panel.setObjectName("SettingsPanel")
        settings_panel_layout = QVBoxLayout(self._settings_panel)
        set_margins(settings_panel_layout, (0, TOKENS.spacing.sm, 0, 0))
        set_spacing(settings_panel_layout, TOKENS.spacing.sm)

        # Unified AI Settings Widget (compact mode)
        self._ai_settings_widget = AISettingsWidget(
            parent=self._settings_panel,
            show_credential=True,
            show_provider=True,
            show_model=True,
            compact=True,
            title="",
        )
        settings_panel_layout.addWidget(self._ai_settings_widget)

        # Initially hide settings panel
        self._settings_panel.setVisible(False)
        header_layout.addWidget(self._settings_panel)

        # Connect toggle
        self._settings_toggle_btn.toggled.connect(self._on_settings_toggled)

        return header

    @Slot(bool)
    def _on_settings_toggled(self, checked: bool) -> None:
        """Handle settings panel toggle."""
        self._settings_panel.setVisible(checked)

    def _apply_styles(self) -> None:
        """Apply theme styling with ElevenLabs design tokens."""
        colors = THEME
        radius = RADIUS

        self.setStyleSheet(f"""
            /* Dock Widget */
            QDockWidget {{
                background-color: {colors.background};
                color: {colors.text_primary};
            }}
            QDockWidget::title {{
                background-color: {colors.dock_title_bg};
                color: {colors.dock_title_text};
                padding: {TOKENS.spacing.sm}px {TOKENS.spacing.md}px;
                font-weight: 600;
                font-size: {TOKENS.typography.caption}px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-bottom: 1px solid {colors.border_dark};
            }}

            /* Header Section - Cleaner like ChatGPT */
            #AIAssistantHeader {{
                background-color: {colors.background};
                border-bottom: 1px solid {colors.border};
            }}
            #AIAssistantTitle {{
                color: {colors.text_primary};
                font-family: {TOKENS.typography.ui};
            }}
            #SettingsToggleBtn {{
                background-color: transparent;
                color: {colors.text_secondary};
                border: 1px solid {colors.border};
                border-radius: {TOKENS.radius.xl // 2}px;
                font-size: {TOKENS.typography.body}px;
                font-family: {TOKENS.typography.ui};
            }}
            #SettingsToggleBtn:hover {{
                background-color: {colors.surface_hover};
                color: {colors.text_primary};
            }}
            #SettingsToggleBtn:checked {{
                background-color: {colors.bg_surface};
                color: {colors.accent};
                border-color: {colors.accent};
            }}
            #SettingsPanel {{
                background-color: {colors.bg_elevated};
                border-radius: {radius.md}px;
            }}
            #ClearChatButton {{
                background-color: transparent;
                color: {colors.text_primary};
                border: 1px solid {colors.border};
                border-radius: {TOKENS.radius.sm}px;
                font-size: {TOKENS.typography.body}px;
                font-weight: 500;
                font-family: {TOKENS.typography.ui};
            }}
            #ClearChatButton:hover {{
                background-color: {colors.surface};
                color: {colors.text_primary};
                border-color: {colors.border_light};
            }}
            #RefreshCredButton {{
                background-color: {colors.surface};
                color: {colors.text_secondary};
                border: 1px solid {colors.border};
                border-radius: {TOKENS.radius.sm}px;
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
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.sm}px {TOKENS.spacing.md}px;
                min-height: {TOKENS.sizes.input_sm}px;
                font-family: {TOKENS.typography.ui};
            }}
            #CredentialCombo:hover {{
                border-color: {colors.border_light};
            }}
            #CredentialCombo:focus {{
                border-color: {colors.border_focus};
            }}
            #CredentialCombo::drop-down {{
                border: none;
                width: {TOKENS.sizes.combo_dropdown_width}px;
            }}
            #CredentialCombo::down-arrow {{
                border-left: {TOKENS.spacing.xs}px solid transparent;
                border-right: {TOKENS.spacing.xs}px solid transparent;
                border-top: 5px solid {colors.text_secondary};
                margin-right: {TOKENS.spacing.sm}px;
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
                font-size: {TOKENS.typography.body}px;
                font-family: {TOKENS.typography.ui};
            }}
            #ModelCombo {{
                background-color: {colors.background};
                color: {colors.text_primary};
                border: 1px solid {colors.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.sm}px {TOKENS.spacing.md}px;
                min-height: {TOKENS.sizes.input_sm}px;
                font-family: {TOKENS.typography.ui};
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
                width: {TOKENS.sizes.combo_dropdown_width}px;
            }}
            #ModelCombo::down-arrow {{
                border-left: {TOKENS.spacing.xs}px solid transparent;
                border-right: {TOKENS.spacing.xs}px solid transparent;
                border-top: 5px solid {colors.text_secondary};
                margin-right: {TOKENS.spacing.sm}px;
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
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.sm}px {TOKENS.spacing.md}px;
                selection-background-color: {colors.accent};
                font-family: {TOKENS.typography.ui};
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
                border-radius: {TOKENS.radius.sm}px;
                font-weight: 600;
                font-family: {TOKENS.typography.ui};
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
                font-size: {TOKENS.typography.body}px;
                font-family: {TOKENS.typography.ui};
            }}
            #ValidationBadge {{
                background-color: {colors.success};
                color: #FFFFFF;
                font-size: {TOKENS.typography.caption}px;
                font-weight: bold;
                padding: {TOKENS.spacing.xs}px {TOKENS.spacing.sm}px;
                border-radius: {TOKENS.radius.sm}px;
            }}
        """)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        # Input Bar
        self._input_bar.sendClicked.connect(self._on_send_clicked)

        # Clear chat
        self._clear_btn.clicked.connect(self._clear_chat)

        # AI Settings Widget signals
        self._ai_settings_widget.credential_changed.connect(self._on_credential_changed)
        self._ai_settings_widget.provider_changed.connect(self._on_provider_changed)
        self._ai_settings_widget.model_changed.connect(self._on_model_changed)
        self._ai_settings_widget.settings_changed.connect(self._save_ai_settings)

        # Debug checkbox
        self._debug_checkbox.toggled.connect(self._on_debug_toggled)

        # Preview card signals
        self._preview_card.append_clicked.connect(self._on_append_clicked)
        self._preview_card.regenerate_clicked.connect(self._on_regenerate_clicked)

        # Load saved settings (must be after widget setup)
        self._load_ai_settings()

        # Initialize input bar state based on current credential selection
        # (signal was emitted before we connected, so we need to sync manually)
        initial_cred = self._ai_settings_widget.get_credential_id()
        if initial_cred:
            self._on_credential_changed(initial_cred)

    def _load_ai_settings(self) -> None:
        """Load AI assistant settings from persistent storage."""
        try:
            from casare_rpa.utils.settings_manager import get_settings_manager

            manager = get_settings_manager()

            # Load saved settings
            saved_provider = manager.get("ai.provider")
            saved_model = manager.get("ai.model")
            saved_credential = manager.get("ai.credential_id")
            saved_debug = manager.get("ai.debug_mode", False)

            if saved_provider or saved_model or saved_credential:
                settings = {}
                if saved_provider:
                    settings["provider"] = saved_provider
                if saved_model:
                    settings["model"] = saved_model
                if saved_credential:
                    settings["credential_id"] = saved_credential

                self._ai_settings_widget.set_settings(settings)
                logger.debug(f"Loaded AI settings: provider={saved_provider}, model={saved_model}")

            # Restore debug mode setting
            self._debug_checkbox.setChecked(saved_debug)

        except Exception as e:
            logger.warning(f"Could not load AI settings: {e}")

    def _save_ai_settings(self, settings: dict) -> None:
        """Save AI assistant settings to persistent storage."""
        try:
            from casare_rpa.utils.settings_manager import get_settings_manager

            manager = get_settings_manager()

            if "provider" in settings:
                manager.set("ai.provider", settings["provider"])
            if "model" in settings:
                manager.set("ai.model", settings["model"])
            if "credential_id" in settings and settings["credential_id"]:
                manager.set("ai.credential_id", settings["credential_id"])

            logger.debug(f"Saved AI settings: {settings}")

        except Exception as e:
            logger.warning(f"Could not save AI settings: {e}")

    def _on_debug_toggled(self, checked: bool) -> None:
        """Handle debug checkbox toggle."""
        try:
            from casare_rpa.utils.settings_manager import get_settings_manager

            manager = get_settings_manager()
            manager.set("ai.debug_mode", checked)
            logger.debug(f"Debug mode {'enabled' if checked else 'disabled'}")

        except Exception as e:
            logger.warning(f"Could not save debug setting: {e}")

    def _on_credential_changed(self, cred_id: str) -> None:
        """Handle credential selection change."""
        self._current_credential_id = cred_id
        self.credential_changed.emit(cred_id or "")

        # Enable UI if valid credential selected
        if cred_id:
            self._set_status("Connected", "ready")
            self._input_bar.setEnabled(True)
        else:
            self._set_status("Select an AI provider to start", "idle")
            self._input_bar.setEnabled(False)

    def _on_provider_changed(self, provider: str) -> None:
        """Handle provider selection change."""
        self._current_provider = provider
        logger.debug(f"Selected provider: {provider}")

    def _on_model_changed(self, model_id: str) -> None:
        """Handle model selection change."""
        self._current_model_id = model_id
        if model_id:
            logger.debug(f"Selected model: {model_id}")

    def _on_send_clicked(self) -> None:
        """Handle send button click."""
        prompt = self._input_bar.text().strip()
        if not prompt:
            return

        if not self._current_credential_id:
            self._set_status("Please select an AI provider first", "warning")
            return

        if self._is_generating:
            return

        # Add user message to UI
        self._chat_area.add_user_message(prompt)
        self._input_bar.clear()

        # Add to conversation manager
        if self._conversation_manager is not None:
            self._conversation_manager.add_user_message(prompt)

        # Classify intent
        classification = self._classify_intent(prompt)

        # Handle special intents locally
        if classification is not None:
            from casare_rpa.infrastructure.ai.conversation_manager import UserIntent

            if classification.intent == UserIntent.UNDO:
                self._handle_undo()
                return

            if classification.intent == UserIntent.REDO:
                self._handle_redo()
                return

            if classification.intent == UserIntent.CLEAR and classification.confidence > 0.8:
                self._clear_chat()
                self._chat_area.add_ai_message("Conversation cleared. How can I help you?")
                return

            if classification.intent == UserIntent.HELP:
                self._show_help()
                return

        # Start generation
        self._start_generation(prompt, classification)

    def _start_generation(self, prompt: str, classification=None) -> None:
        """
        Start workflow generation using SmartWorkflowAgent.

        Spawns a background thread to run async LLM calls without blocking UI.

        Args:
            prompt: User prompt text
            classification: Optional intent classification result
        """
        self._is_generating = True
        self._last_prompt = prompt
        self._set_status("Generating workflow...", "loading")
        self._input_bar.setEnabled(False)

        # Show thinking indicator
        self._chat_area.show_thinking()

        # Emit signal
        self.generation_started.emit()

        # Get credential ID from selection
        credential_id = self._current_credential_id

        # Get model ID
        model_id = self._current_model_id

        # If no model selected, pick a default based on provider or fallback
        if not model_id:
            if self._current_provider == "Google":
                model_id = "models/gemini-3-flash-preview"
            elif self._current_provider == "OpenAI":
                model_id = "gpt-4o"
            elif self._current_provider == "Anthropic":
                model_id = "claude-3-5-sonnet-latest"
            else:
                model_id = "openrouter/deepseek/deepseek-v3.2"

        if not credential_id:
            self._chat_area.hide_thinking()
            self._chat_area.add_ai_message(
                "Please select an AI provider credential before generating workflows."
            )
            self._finish_generation(False)
            return

        # Get canvas state for context
        canvas_state = self._get_canvas_state()

        # Determine if this is an edit request using classification or fallback
        if classification is not None:
            from casare_rpa.infrastructure.ai.conversation_manager import UserIntent

            edit_intents = {
                UserIntent.MODIFY_WORKFLOW,
                UserIntent.ADD_NODE,
                UserIntent.REMOVE_NODE,
                UserIntent.REFINE,
            }
            is_edit = classification.intent in edit_intents and canvas_state is not None
            intent_str = classification.intent.value
        else:
            is_edit = self._is_edit_request(prompt) and canvas_state is not None
            intent_str = "edit" if is_edit else "generate"

        if is_edit:
            logger.info(f"Detected {intent_str} request - will modify existing nodes")
            self._set_status("Analyzing canvas and modifying...", "loading")

        # Create and start generation thread
        self._generation_thread = WorkflowGenerationThread(
            prompt=prompt,
            model_id=model_id,
            credential_id=credential_id,
            provider=self._current_provider,
            existing_workflow=None,
            canvas_state=canvas_state,
            is_edit=is_edit,
            parent=self,
        )
        self._generation_thread.finished.connect(self._on_generation_complete)
        self._generation_thread.start()

        logger.info(
            f"Started workflow generation: intent={intent_str}, prompt='{prompt[:50]}...', "
            f"model={model_id}, credential={credential_id[:8] if credential_id else 'None'}..., "
            f"canvas_nodes={canvas_state.get('node_count', 0) if canvas_state else 0}"
        )

    def _handle_undo(self) -> None:
        """Handle undo request."""
        if self._conversation_manager is None:
            self._chat_area.add_ai_message("Undo is not available.")
            return

        workflow = self._conversation_manager.undo_workflow()
        if workflow:
            self._current_workflow = workflow
            self.append_requested.emit(workflow)
            self._chat_area.add_ai_message("Undone. Previous workflow version restored.")
            if self._conversation_manager is not None:
                self._conversation_manager.add_assistant_message(
                    "Undone. Previous workflow version restored."
                )
        else:
            self._chat_area.add_ai_message("Nothing to undo.")
            if self._conversation_manager is not None:
                self._conversation_manager.add_assistant_message("Nothing to undo.")

    def _handle_redo(self) -> None:
        """Handle redo request."""
        if self._conversation_manager is None:
            self._chat_area.add_ai_message("Redo is not available.")
            return

        workflow = self._conversation_manager.redo_workflow()
        if workflow:
            self._current_workflow = workflow
            self.append_requested.emit(workflow)
            self._chat_area.add_ai_message("Redone. Workflow restored.")
            if self._conversation_manager is not None:
                self._conversation_manager.add_assistant_message("Redone. Workflow restored.")
        else:
            self._chat_area.add_ai_message("Nothing to redo.")
            if self._conversation_manager is not None:
                self._conversation_manager.add_assistant_message("Nothing to redo.")

    def _show_help(self) -> None:
        """Show help message with available commands."""
        help_text = """I can help you create and modify RPA workflows. Here's what I can do:

**Create Workflows:**
- "Create a workflow to login to example.com"
- "Build an automation to scrape data from a website"
- "Make a workflow to fill out a form"

**Modify Workflows:**
- "Add a click after the login"
- "Change the URL to https://..."
- "Remove the wait node"

**Refine Workflows:**
- "Add error handling"
- "Optimize the waits"
- "Make it more robust"

**Commands:**
- "undo" - Undo the last change
- "redo" - Redo an undone change
- "clear" - Start a new conversation

What would you like to create?"""
        self._chat_area.add_ai_message(help_text)
        if self._conversation_manager is not None:
            self._conversation_manager.add_assistant_message(help_text)

    def _on_generation_complete(self, result: WorkflowGenerationResult) -> None:
        """
        Handle workflow generation result from background thread.

        Args:
            result: WorkflowGenerationResult from SmartWorkflowAgent
        """
        self._chat_area.hide_thinking()

        try:
            if result.success and result.workflow:
                # Check for pure chat response
                if result.workflow.get("type") == "chat":
                    message = result.workflow.get("message", "")
                    self._chat_area.add_ai_message(message)
                    if self._conversation_manager:
                        self._conversation_manager.add_assistant_message(message)
                    self._finish_generation(True, skip_workflow_ready=True)
                    return

                # Count nodes and connections for message
                nodes = result.workflow.get("nodes", {})
                connections = result.workflow.get("connections", [])
                node_count = len(nodes) if isinstance(nodes, dict | list) else 0
                conn_count = len(connections) if isinstance(connections, list) else 0

                # Build response message
                response = (
                    f"I've created a workflow based on your request.\n\n"
                    f"**Nodes:** {node_count}\n"
                    f"**Connections:** {conn_count}\n"
                    f"**Attempts:** {result.attempts}\n"
                    f"**Time:** {result.generation_time_ms:.0f}ms"
                )
                self._chat_area.add_ai_message(response)

                # Show raw LLM output if debug mode is enabled
                if self._debug_checkbox.isChecked() and result.raw_response:
                    self._chat_area.add_system_message("📋 Raw LLM Output:")
                    # Truncate if too long
                    raw_output = result.raw_response
                    if len(raw_output) > 3000:
                        raw_output = raw_output[:3000] + "\n\n... (truncated)"
                    self._chat_area.add_code_block(raw_output)

                # Track assistant response in conversation manager
                if self._conversation_manager is not None:
                    self._conversation_manager.add_assistant_message(
                        response,
                        metadata={"workflow_generated": True, "node_count": node_count},
                    )

                # Store workflow and log info
                try:
                    self._current_workflow = result.workflow

                    # Update conversation manager with new workflow
                    if self._conversation_manager is not None:
                        description = (
                            f"Generated: {self._last_prompt[:50]}..."
                            if self._last_prompt
                            else "Generated workflow"
                        )
                        self._conversation_manager.set_workflow(result.workflow, description)

                    # Log detailed workflow info for debugging
                    nodes = result.workflow.get("nodes", {})
                    if isinstance(nodes, dict):
                        node_types = [
                            n.get("node_type", n.get("type", "?")) for n in nodes.values()
                        ]
                    else:
                        node_types = [n.get("node_type", n.get("type", "?")) for n in nodes]
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
                    f" after {result.attempts} attempt(s)" if result.attempts > 0 else ""
                )

                response = (
                    f"I couldn't generate the workflow{attempts_info}.\n\n"
                    f"**Error:** {error_msg}\n\n"
                    f"Please try rephrasing your request or check the AI provider settings."
                )
                self._chat_area.add_ai_message(response)

                # Show raw LLM output if debug mode is enabled (helpful for debugging failures)
                if self._debug_checkbox.isChecked() and result.raw_response:
                    self._chat_area.add_system_message("📋 Raw LLM Output (for debugging):")
                    raw_output = result.raw_response
                    if len(raw_output) > 3000:
                        raw_output = raw_output[:3000] + "\n\n... (truncated)"
                    self._chat_area.add_code_block(raw_output)

                # Track failure in conversation manager
                if self._conversation_manager is not None:
                    self._conversation_manager.add_assistant_message(
                        response,
                        metadata={"workflow_generated": False, "error": error_msg},
                    )

                self._finish_generation(False)
        except Exception as e:
            logger.error(f"Error handling generation result: {e}", exc_info=True)
            self._chat_area.add_ai_message(f"An error occurred: {e}")
            self._finish_generation(False)
        finally:
            # Cleanup thread reference - ALWAYS runs
            self._generation_thread = None

    def _finish_generation(self, success: bool, skip_workflow_ready: bool = False) -> None:
        """Finish generation and update UI state.

        Args:
            success: Whether generation succeeded
            skip_workflow_ready: If True, don't emit workflow_ready signal
                (used when auto-append already emitted append_requested)
        """
        self._is_generating = False
        self._input_bar.setEnabled(True)

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
        """Clear conversation history and reset conversation state."""
        self._chat_area.clear_messages()
        self._preview_card.setVisible(False)
        self._current_workflow = None
        self._set_status("Ready", "ready")
        self._show_validation_badge(False)

        # Clear conversation manager state
        if self._conversation_manager is not None:
            self._conversation_manager.clear_all()
            logger.debug("Conversation manager cleared")

    def _set_status(self, message: str, state: str = "idle") -> None:
        """Update status (placeholder text on input bar)."""
        if hasattr(self, "_input_bar"):
            if state in ("idle", "ready", "success") and message in (
                "Ready",
                "Connected",
            ):
                self._input_bar.setPlaceholderText("Message AI Assistant...")
            else:
                self._input_bar.setPlaceholderText(message)
        logger.debug(f"Status update: {message} ({state})")

    def _show_validation_badge(self, show: bool) -> None:
        """Show/hide validation badge (No-op in new UI)."""
        pass

    # ==================== Public API ====================

    def set_workflow_result(
        self, workflow: dict[str, Any] | None, success: bool, message: str = ""
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
            self._chat_area.add_ai_message(message or "Workflow generated successfully.")
            self._current_workflow = workflow
            self._preview_card.set_workflow(workflow)
            self._preview_card.setVisible(True)
            self._finish_generation(True)
        else:
            self._chat_area.add_ai_message(message or "Failed to generate workflow.")
            self._finish_generation(False)

    def get_selected_credential_id(self) -> str | None:
        """Get the currently selected credential ID."""
        return self._current_credential_id

    def get_selected_model_id(self) -> str | None:
        """Get the currently selected model ID."""
        return self._current_model_id

    def get_selected_provider(self) -> str | None:
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
