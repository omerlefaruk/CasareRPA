"""
Process Mining Panel UI Component.

Provides AI-powered process discovery, variant analysis, conformance checking,
pattern recognition, ROI estimation, and optimization insights from workflow
execution logs.
"""

from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QComboBox,
    QLabel,
    QHeaderView,
    QAbstractItemView,
    QTabWidget,
    QTextEdit,
    QProgressBar,
    QGroupBox,
    QTreeWidget,
    QTreeWidgetItem,
    QSpinBox,
    QDoubleSpinBox,
    QFileDialog,
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QObject
from PySide6.QtGui import QColor, QBrush, QFont

from loguru import logger

from casare_rpa.presentation.canvas.theme import THEME
from casare_rpa.presentation.canvas.ui.panels.panel_ux_helpers import (
    get_panel_table_stylesheet,
    get_panel_toolbar_stylesheet,
)


class AIEnhanceWorker(QObject):
    """Worker for background AI enhancement of process insights."""

    finished = Signal(list)
    error = Signal(str)

    def __init__(
        self,
        insights: List[Dict[str, Any]],
        model: str,
        provider: str,
        process_model: Dict[str, Any],
    ) -> None:
        """Initialize worker with insights data."""
        super().__init__()
        self.insights = insights
        self.model = model
        self.provider = provider
        self.process_model = process_model
        self._llm_manager = None

    def _get_llm_manager(self):
        """Get or create LLM resource manager."""
        if self._llm_manager is None:
            try:
                from casare_rpa.infrastructure.resources.llm_resource_manager import (
                    LLMResourceManager,
                )

                self._llm_manager = LLMResourceManager()
            except ImportError:
                return None
        return self._llm_manager

    def run(self) -> None:
        """Execute the AI enhancement."""
        try:
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self._enhance_async())
                self.finished.emit(result)
            finally:
                loop.close()
        except Exception as e:
            self.error.emit(str(e))

    async def _enhance_async(self) -> List[Dict[str, Any]]:
        """Async AI enhancement logic."""
        manager = self._get_llm_manager()
        if not manager:
            raise RuntimeError("LLM manager not available")

        from casare_rpa.infrastructure.resources.llm_resource_manager import (
            LLMConfig,
            LLMProvider,
        )

        # Configure with selected model
        provider_map = {
            "OpenAI": LLMProvider.OPENAI,
            "Anthropic": LLMProvider.ANTHROPIC,
            "Local (Ollama)": LLMProvider.OLLAMA,
        }
        llm_provider = provider_map.get(self.provider, LLMProvider.OPENAI)

        manager.configure(
            LLMConfig(
                provider=llm_provider,
                model=self.model,
            )
        )

        # Build prompt with insights summary
        insights_text = "\n".join(
            [
                f"- {i.get('title', '')}: {i.get('description', '')} (Impact: {i.get('impact', 'low')})"
                for i in self.insights
            ]
        )

        prompt = f"""Analyze these process mining insights and provide enhanced recommendations.

Current Insights:
{insights_text}

Process Model Summary:
- Activities: {len(self.process_model.get('activities', []))}
- Edges: {sum(len(t) for t in self.process_model.get('edges', {}).values())}

For each insight, provide:
1. A more specific actionable recommendation
2. Potential root cause analysis
3. Estimated improvement impact

Format your response as a structured list with clear sections."""

        response, _ = await manager.chat(
            message=prompt,
            system_prompt=(
                "You are a process optimization expert. Analyze RPA workflow "
                "execution data and provide actionable insights for improvement. "
                "Be specific and practical."
            ),
            temperature=0.3,
            max_tokens=2000,
        )

        # Parse response and enhance insights
        enhanced = []
        for insight in self.insights:
            enhanced_insight = insight.copy()
            enhanced_insight["ai_enhanced"] = True
            enhanced_insight["ai_analysis"] = response.content
            enhanced.append(enhanced_insight)

        return enhanced


class ProcessMiningPanel(QDockWidget):
    """
    Dockable panel for Process Mining capabilities.

    Features:
    - Process Discovery: Build process models from execution logs
    - Variant Analysis: See different execution paths
    - Conformance Checking: Compare actual vs expected
    - Optimization Insights: AI-generated recommendations

    Signals:
        workflow_selected: Emitted when workflow is selected (str: workflow_id)
        insight_clicked: Emitted when insight is clicked (dict: insight_data)
    """

    workflow_selected = Signal(str)
    insight_clicked = Signal(dict)

    def __init__(
        self, parent: Optional[QWidget] = None, embedded: bool = False
    ) -> None:
        """Initialize the process mining panel.

        Args:
            parent: Optional parent widget
            embedded: If True, behave as QWidget (for embedding in tab panels)
        """
        self._embedded = embedded
        if embedded:
            QWidget.__init__(self, parent)
        else:
            super().__init__("Process Mining", parent)
            self.setObjectName("ProcessMiningDock")

        self._miner = None
        self._current_workflow: Optional[str] = None
        self._current_model = None
        self._current_insights: List[Dict[str, Any]] = []
        self._llm_manager = None

        # Pattern recognition and ROI
        self._pattern_recognizer = None
        self._frequent_miner = None
        self._roi_estimator = None
        self._current_patterns: List[Any] = []
        self._current_roi_estimates: List[Any] = []

        # Thread management for AI enhancement
        self._ai_thread: Optional[QThread] = None
        self._ai_worker: Optional[AIEnhanceWorker] = None

        if not embedded:
            self._setup_dock()
        self._setup_ui()
        self._apply_styles()
        self._setup_refresh_timer()

        logger.debug("ProcessMiningPanel initialized")

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
        self.setMinimumWidth(350)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        if self._embedded:
            main_layout = QVBoxLayout(self)
        else:
            container = QWidget()
            main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Header with workflow selector
        header = self._create_header()
        main_layout.addLayout(header)

        # AI Settings (credential and model selector)
        self._ai_settings = self._create_ai_settings()
        main_layout.addWidget(self._ai_settings)

        # Summary stats
        self._stats_group = self._create_stats_group()
        main_layout.addWidget(self._stats_group)

        # Tab widget for different views
        self._tabs = QTabWidget()

        # Discovery tab
        discovery_tab = self._create_discovery_tab()
        self._tabs.addTab(discovery_tab, "Discovery")

        # Variants tab
        variants_tab = self._create_variants_tab()
        self._tabs.addTab(variants_tab, "Variants")

        # Patterns tab (ML pattern recognition)
        patterns_tab = self._create_patterns_tab()
        self._tabs.addTab(patterns_tab, "Patterns")

        # Insights tab
        insights_tab = self._create_insights_tab()
        self._tabs.addTab(insights_tab, "Insights")

        # Conformance tab
        conformance_tab = self._create_conformance_tab()
        self._tabs.addTab(conformance_tab, "Conformance")

        # ROI / Automation Candidates tab
        candidates_tab = self._create_candidates_tab()
        self._tabs.addTab(candidates_tab, "ROI")

        main_layout.addWidget(self._tabs)
        if not self._embedded:
            self.setWidget(container)

    def _create_header(self) -> QHBoxLayout:
        """Create header with workflow selector."""
        layout = QHBoxLayout()
        layout.setSpacing(8)

        # Workflow selector
        workflow_label = QLabel("Workflow:")
        self._workflow_combo = QComboBox()
        self._workflow_combo.setMinimumWidth(150)
        self._workflow_combo.addItem("Select workflow...", None)
        self._workflow_combo.currentIndexChanged.connect(self._on_workflow_changed)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedWidth(70)
        refresh_btn.clicked.connect(self._refresh_data)

        # Discover button
        self._discover_btn = QPushButton("Discover")
        self._discover_btn.setFixedWidth(70)
        self._discover_btn.clicked.connect(self._run_discovery)
        self._discover_btn.setEnabled(False)

        layout.addWidget(workflow_label)
        layout.addWidget(self._workflow_combo, 1)
        layout.addWidget(refresh_btn)
        layout.addWidget(self._discover_btn)

        return layout

    def _create_ai_settings(self) -> QGroupBox:
        """Create AI settings group with credential and model selectors."""
        group = QGroupBox("AI Model")
        layout = QHBoxLayout(group)
        layout.setSpacing(12)

        # Provider selector
        provider_label = QLabel("Provider:")
        self._provider_combo = QComboBox()
        self._provider_combo.setMinimumWidth(100)
        self._provider_combo.addItems(
            [
                "OpenAI",
                "Anthropic",
                "Google",
                "Mistral",
                "Groq",
                "DeepSeek",
                "OpenRouter",
                "Local (Ollama)",
            ]
        )
        self._provider_combo.setToolTip("Select AI provider for generating insights")
        self._provider_combo.currentTextChanged.connect(self._on_provider_changed)

        # Model selector
        model_label = QLabel("Model:")
        self._model_combo = QComboBox()
        self._model_combo.setMinimumWidth(150)
        self._model_combo.setToolTip("Select AI model")
        self._update_model_list()

        # API Key indicator
        self._api_key_label = QLabel("API Key:")
        self._api_key_status = QLabel("Auto-detect")
        self._api_key_status.setStyleSheet(f"color: {THEME.status_success};")
        self._api_key_status.setToolTip(
            "Uses environment variables (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)\n"
            "or stored credentials from Credential Manager"
        )

        # Manage credentials button
        self._manage_creds_btn = QPushButton("...")
        self._manage_creds_btn.setFixedWidth(30)
        self._manage_creds_btn.setToolTip("Manage API credentials")
        self._manage_creds_btn.clicked.connect(self._on_manage_credentials)

        layout.addWidget(provider_label)
        layout.addWidget(self._provider_combo)
        layout.addWidget(model_label)
        layout.addWidget(self._model_combo, 1)
        layout.addWidget(self._api_key_label)
        layout.addWidget(self._api_key_status)
        layout.addWidget(self._manage_creds_btn)

        return group

    def _on_provider_changed(self, provider: str) -> None:
        """Handle provider change - update model list."""
        self._update_model_list()
        self._check_api_key_status()

    def _update_model_list(self) -> None:
        """Update model combo based on selected provider."""
        provider = self._provider_combo.currentText()

        # Model lists by provider
        models = {
            "OpenAI": [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-3.5-turbo",
                "o1-preview",
                "o1-mini",
            ],
            "Anthropic": [
                "claude-3-5-sonnet-latest",
                "claude-3-5-haiku-latest",
                "claude-3-opus-latest",
            ],
            "Google": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash-exp"],
            "Mistral": [
                "mistral-large-latest",
                "mistral-medium-latest",
                "mistral-small-latest",
            ],
            "Groq": [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "mixtral-8x7b-32768",
            ],
            "DeepSeek": ["deepseek-chat", "deepseek-coder"],
            "OpenRouter": [
                "openrouter/openai/gpt-4o",
                "openrouter/anthropic/claude-3.5-sonnet",
                "openrouter/google/gemini-2.0-flash-exp:free",
                "openrouter/meta-llama/llama-3.3-70b-instruct",
            ],
            "Local (Ollama)": ["ollama/llama3.2", "ollama/mistral", "ollama/codellama"],
        }

        current_model = self._model_combo.currentText()
        self._model_combo.clear()
        self._model_combo.addItems(models.get(provider, []))

        # Try to restore selection
        idx = self._model_combo.findText(current_model)
        if idx >= 0:
            self._model_combo.setCurrentIndex(idx)

    def _check_api_key_status(self) -> None:
        """Check if API key is available for selected provider."""
        import os

        provider = self._provider_combo.currentText()

        # Map provider to env var
        env_vars = {
            "OpenAI": "OPENAI_API_KEY",
            "Anthropic": "ANTHROPIC_API_KEY",
            "Google": "GOOGLE_API_KEY",
            "Mistral": "MISTRAL_API_KEY",
            "Groq": "GROQ_API_KEY",
            "DeepSeek": "DEEPSEEK_API_KEY",
            "OpenRouter": "OPENROUTER_API_KEY",
            "Local (Ollama)": None,  # No API key needed
        }

        env_var = env_vars.get(provider)

        if env_var is None:
            # Local provider - no key needed
            self._api_key_status.setText("Not required")
            self._api_key_status.setStyleSheet(f"color: {THEME.status_success};")
            return

        # Check environment
        if os.environ.get(env_var):
            self._api_key_status.setText("Found (env)")
            self._api_key_status.setStyleSheet(f"color: {THEME.status_success};")
            return

        # Check credential store
        try:
            from casare_rpa.infrastructure.security.credential_store import (
                get_credential_store,
            )

            store = get_credential_store()
            creds = store.list_credentials(category="llm")
            provider_lower = provider.lower()
            for cred in creds:
                if provider_lower in cred.get("name", "").lower():
                    self._api_key_status.setText(f"Found ({cred['name']})")
                    self._api_key_status.setStyleSheet(
                        f"color: {THEME.status_success};"
                    )
                    return
        except Exception:
            pass

        # Not found
        self._api_key_status.setText("Not found")
        self._api_key_status.setStyleSheet(f"color: {THEME.status_error};")

    def _on_manage_credentials(self) -> None:
        """Open credential management dialog."""
        try:
            # Try to open the credential manager if available
            from casare_rpa.presentation.canvas.ui.dialogs.credential_dialog import (
                CredentialDialog,
            )

            dialog = CredentialDialog(self, category="llm")
            dialog.exec()
            self._check_api_key_status()
        except ImportError:
            # Show info message
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.information(
                self,
                "API Keys",
                "To use AI features, set environment variables:\n\n"
                "- OPENAI_API_KEY\n"
                "- ANTHROPIC_API_KEY\n"
                "- GOOGLE_API_KEY\n"
                "- etc.\n\n"
                "Or add credentials in Settings > Credential Manager.",
            )

    def get_ai_settings(self) -> dict:
        """Get current AI model settings.

        Returns:
            Dict with provider and model keys.
        """
        return {
            "provider": self._provider_combo.currentText(),
            "model": self._model_combo.currentText(),
        }

    def _create_stats_group(self) -> QGroupBox:
        """Create statistics summary group."""
        group = QGroupBox("Summary")
        layout = QHBoxLayout(group)
        layout.setSpacing(20)

        # Traces count
        traces_layout = QVBoxLayout()
        self._traces_label = QLabel("0")
        self._traces_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self._traces_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        traces_desc = QLabel("Traces")
        traces_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        traces_layout.addWidget(self._traces_label)
        traces_layout.addWidget(traces_desc)

        # Variants count
        variants_layout = QVBoxLayout()
        self._variants_label = QLabel("0")
        self._variants_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self._variants_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        variants_desc = QLabel("Variants")
        variants_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        variants_layout.addWidget(self._variants_label)
        variants_layout.addWidget(variants_desc)

        # Success rate
        success_layout = QVBoxLayout()
        self._success_label = QLabel("0%")
        self._success_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self._success_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        success_desc = QLabel("Success")
        success_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        success_layout.addWidget(self._success_label)
        success_layout.addWidget(success_desc)

        # Avg duration
        duration_layout = QVBoxLayout()
        self._duration_label = QLabel("0s")
        self._duration_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self._duration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        duration_desc = QLabel("Avg Time")
        duration_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        duration_layout.addWidget(self._duration_label)
        duration_layout.addWidget(duration_desc)

        layout.addLayout(traces_layout)
        layout.addLayout(variants_layout)
        layout.addLayout(success_layout)
        layout.addLayout(duration_layout)

        return group

    def _create_discovery_tab(self) -> QWidget:
        """Create process discovery tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        # Process model visualization (Mermaid text for now)
        model_label = QLabel("Discovered Process Model:")
        layout.addWidget(model_label)

        self._model_text = QTextEdit()
        self._model_text.setReadOnly(True)
        self._model_text.setMinimumHeight(200)
        self._model_text.setPlaceholderText(
            "Select a workflow and click 'Discover' to see the process model...\n\n"
            "The model shows:\n"
            "- Nodes: Activities in the workflow\n"
            "- Edges: Transitions between activities (with frequency)\n"
            "- Entry/Exit points\n"
            "- Loops and parallel paths"
        )
        layout.addWidget(self._model_text)

        # Model statistics
        stats_group = QGroupBox("Model Statistics")
        stats_layout = QHBoxLayout(stats_group)

        self._nodes_stat = QLabel("Nodes: -")
        self._edges_stat = QLabel("Edges: -")
        self._loops_stat = QLabel("Loops: -")
        self._parallel_stat = QLabel("Parallel: -")

        stats_layout.addWidget(self._nodes_stat)
        stats_layout.addWidget(self._edges_stat)
        stats_layout.addWidget(self._loops_stat)
        stats_layout.addWidget(self._parallel_stat)

        layout.addWidget(stats_group)

        return widget

    def _create_variants_tab(self) -> QWidget:
        """Create variant analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        info_label = QLabel(
            "Variants are distinct execution paths through the workflow.\n"
            "Each variant represents a unique sequence of nodes executed."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {THEME.text_muted}; font-size: 11px;")
        layout.addWidget(info_label)

        # Variants table
        self._variants_table = QTableWidget()
        self._variants_table.setColumnCount(5)
        self._variants_table.setHorizontalHeaderLabels(
            ["Variant", "Count", "%", "Avg Time", "Success"]
        )
        self._variants_table.setAlternatingRowColors(True)
        self._variants_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._variants_table.itemSelectionChanged.connect(self._on_variant_selected)

        header = self._variants_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._variants_table)

        # Variant detail
        detail_group = QGroupBox("Variant Path")
        detail_layout = QVBoxLayout(detail_group)
        self._variant_path = QTextEdit()
        self._variant_path.setReadOnly(True)
        self._variant_path.setMaximumHeight(80)
        self._variant_path.setPlaceholderText("Select a variant to see its path...")
        detail_layout.addWidget(self._variant_path)
        layout.addWidget(detail_group)

        return widget

    def _create_insights_tab(self) -> QWidget:
        """Create optimization insights tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        # Header with AI enhance button
        header_layout = QHBoxLayout()
        info_label = QLabel(
            "AI-generated recommendations for improving workflow performance."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {THEME.text_muted}; font-size: 11px;")
        header_layout.addWidget(info_label, 1)

        # Enhance with AI button
        self._enhance_btn = QPushButton("✨ Enhance with AI")
        self._enhance_btn.setToolTip(
            "Use the selected AI model to generate enhanced recommendations"
        )
        self._enhance_btn.clicked.connect(self._enhance_insights_with_ai)
        self._enhance_btn.setEnabled(False)
        header_layout.addWidget(self._enhance_btn)
        layout.addLayout(header_layout)

        # Progress bar for AI enhancement (hidden by default)
        self._enhance_progress = QProgressBar()
        self._enhance_progress.setTextVisible(True)
        self._enhance_progress.setFormat("Generating AI insights...")
        self._enhance_progress.setRange(0, 0)  # Indeterminate
        self._enhance_progress.hide()
        layout.addWidget(self._enhance_progress)

        # Insights tree
        self._insights_tree = QTreeWidget()
        self._insights_tree.setHeaderLabels(["Insight", "Impact"])
        self._insights_tree.setAlternatingRowColors(True)
        self._insights_tree.itemClicked.connect(self._on_insight_clicked)

        header = self._insights_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._insights_tree)

        # Insight detail
        detail_group = QGroupBox("Details")
        detail_layout = QVBoxLayout(detail_group)
        self._insight_detail = QTextEdit()
        self._insight_detail.setReadOnly(True)
        self._insight_detail.setMaximumHeight(120)
        self._insight_detail.setPlaceholderText("Click an insight for details...")
        detail_layout.addWidget(self._insight_detail)
        layout.addWidget(detail_group)

        return widget

    def _create_conformance_tab(self) -> QWidget:
        """Create conformance checking tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        info_label = QLabel(
            "Compare actual executions against the discovered process model.\n"
            "High conformance = executions match expected patterns."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {THEME.text_muted}; font-size: 11px;")
        layout.addWidget(info_label)

        # Conformance summary
        summary_group = QGroupBox("Conformance Summary")
        summary_layout = QHBoxLayout(summary_group)

        # Conformance rate
        rate_layout = QVBoxLayout()
        self._conformance_rate = QLabel("-")
        self._conformance_rate.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self._conformance_rate.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rate_desc = QLabel("Conformance Rate")
        rate_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rate_layout.addWidget(self._conformance_rate)
        rate_layout.addWidget(rate_desc)

        # Fitness score
        fitness_layout = QVBoxLayout()
        self._fitness_score = QLabel("-")
        self._fitness_score.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self._fitness_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fitness_desc = QLabel("Avg Fitness")
        fitness_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fitness_layout.addWidget(self._fitness_score)
        fitness_layout.addWidget(fitness_desc)

        summary_layout.addLayout(rate_layout)
        summary_layout.addLayout(fitness_layout)
        layout.addWidget(summary_group)

        # Deviations table
        deviations_label = QLabel("Deviations Found:")
        layout.addWidget(deviations_label)

        self._deviations_table = QTableWidget()
        self._deviations_table.setColumnCount(3)
        self._deviations_table.setHorizontalHeaderLabels(["Type", "Count", "Severity"])
        self._deviations_table.setAlternatingRowColors(True)

        header = self._deviations_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._deviations_table)

        return widget

    def _create_patterns_tab(self) -> QWidget:
        """Create ML pattern recognition tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        # Header with info and controls
        info_label = QLabel(
            "ML-based pattern recognition identifies repetitive task patterns\n"
            "using DBSCAN clustering. Higher automation potential = better candidate."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {THEME.text_muted}; font-size: 11px;")
        layout.addWidget(info_label)

        # Controls row
        controls_layout = QHBoxLayout()

        # Min samples control
        min_samples_label = QLabel("Min Samples:")
        self._min_samples_spin = QSpinBox()
        self._min_samples_spin.setRange(2, 20)
        self._min_samples_spin.setValue(3)
        self._min_samples_spin.setToolTip("Minimum traces for a cluster")

        # Epsilon control
        eps_label = QLabel("Epsilon:")
        self._eps_spin = QDoubleSpinBox()
        self._eps_spin.setRange(0.1, 2.0)
        self._eps_spin.setValue(0.5)
        self._eps_spin.setSingleStep(0.1)
        self._eps_spin.setToolTip("Maximum distance for DBSCAN clustering")

        # Analyze button
        self._analyze_patterns_btn = QPushButton("Find Patterns")
        self._analyze_patterns_btn.setFixedWidth(100)
        self._analyze_patterns_btn.clicked.connect(self._run_pattern_analysis)
        self._analyze_patterns_btn.setEnabled(False)

        controls_layout.addWidget(min_samples_label)
        controls_layout.addWidget(self._min_samples_spin)
        controls_layout.addWidget(eps_label)
        controls_layout.addWidget(self._eps_spin)
        controls_layout.addStretch()
        controls_layout.addWidget(self._analyze_patterns_btn)
        layout.addLayout(controls_layout)

        # Progress bar (hidden by default)
        self._pattern_progress = QProgressBar()
        self._pattern_progress.setTextVisible(True)
        self._pattern_progress.setFormat("Analyzing patterns...")
        self._pattern_progress.setRange(0, 0)
        self._pattern_progress.hide()
        layout.addWidget(self._pattern_progress)

        # Patterns table
        self._patterns_table = QTableWidget()
        self._patterns_table.setColumnCount(6)
        self._patterns_table.setHorizontalHeaderLabels(
            ["Pattern", "Frequency", "Avg Time", "Success", "Potential", "Variance"]
        )
        self._patterns_table.setAlternatingRowColors(True)
        self._patterns_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._patterns_table.itemSelectionChanged.connect(self._on_pattern_selected)

        header = self._patterns_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 6):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._patterns_table)

        # Pattern detail
        detail_group = QGroupBox("Pattern Details")
        detail_layout = QVBoxLayout(detail_group)

        self._pattern_detail = QTextEdit()
        self._pattern_detail.setReadOnly(True)
        self._pattern_detail.setMaximumHeight(100)
        self._pattern_detail.setPlaceholderText(
            "Select a pattern to see activity sequence..."
        )
        detail_layout.addWidget(self._pattern_detail)

        # Create subflow button
        btn_layout = QHBoxLayout()
        self._create_subflow_btn = QPushButton("Create Subflow from Pattern")
        self._create_subflow_btn.setEnabled(False)
        self._create_subflow_btn.clicked.connect(self._create_subflow_from_pattern)
        btn_layout.addStretch()
        btn_layout.addWidget(self._create_subflow_btn)
        detail_layout.addLayout(btn_layout)

        layout.addWidget(detail_group)

        return widget

    def _create_candidates_tab(self) -> QWidget:
        """Create ROI / Automation Candidates tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        # Header info
        info_label = QLabel(
            "ROI estimation scores automation candidates by potential savings.\n"
            "Higher score = better return on investment for automation."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {THEME.text_muted}; font-size: 11px;")
        layout.addWidget(info_label)

        # Configuration row
        config_layout = QHBoxLayout()

        # Hourly cost
        cost_label = QLabel("Hourly Cost ($):")
        self._hourly_cost_spin = QDoubleSpinBox()
        self._hourly_cost_spin.setRange(10.0, 500.0)
        self._hourly_cost_spin.setValue(50.0)
        self._hourly_cost_spin.setSingleStep(5.0)
        self._hourly_cost_spin.setToolTip("Hourly labor cost for ROI calculation")

        # Calculate ROI button
        self._calc_roi_btn = QPushButton("Calculate ROI")
        self._calc_roi_btn.setFixedWidth(100)
        self._calc_roi_btn.clicked.connect(self._calculate_roi)
        self._calc_roi_btn.setEnabled(False)

        # Export button
        self._export_roi_btn = QPushButton("Export CSV")
        self._export_roi_btn.setFixedWidth(80)
        self._export_roi_btn.clicked.connect(self._export_roi_csv)
        self._export_roi_btn.setEnabled(False)

        config_layout.addWidget(cost_label)
        config_layout.addWidget(self._hourly_cost_spin)
        config_layout.addStretch()
        config_layout.addWidget(self._calc_roi_btn)
        config_layout.addWidget(self._export_roi_btn)
        layout.addLayout(config_layout)

        # Summary stats
        summary_group = QGroupBox("ROI Summary")
        summary_layout = QHBoxLayout(summary_group)

        # Total savings
        savings_layout = QVBoxLayout()
        self._total_savings_label = QLabel("$0")
        self._total_savings_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self._total_savings_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        savings_desc = QLabel("Annual Savings")
        savings_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        savings_layout.addWidget(self._total_savings_label)
        savings_layout.addWidget(savings_desc)

        # Hours saved
        hours_layout = QVBoxLayout()
        self._total_hours_label = QLabel("0h")
        self._total_hours_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self._total_hours_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hours_desc = QLabel("Hours/Year")
        hours_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hours_layout.addWidget(self._total_hours_label)
        hours_layout.addWidget(hours_desc)

        # Avg payback
        payback_layout = QVBoxLayout()
        self._avg_payback_label = QLabel("-")
        self._avg_payback_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self._avg_payback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        payback_desc = QLabel("Avg Payback")
        payback_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        payback_layout.addWidget(self._avg_payback_label)
        payback_layout.addWidget(payback_desc)

        summary_layout.addLayout(savings_layout)
        summary_layout.addLayout(hours_layout)
        summary_layout.addLayout(payback_layout)
        layout.addWidget(summary_group)

        # Candidates table
        self._candidates_table = QTableWidget()
        self._candidates_table.setColumnCount(7)
        self._candidates_table.setHorizontalHeaderLabels(
            [
                "Pattern",
                "ROI Score",
                "Hours/Yr",
                "Savings/Yr",
                "Dev Hours",
                "Payback",
                "Rec.",
            ]
        )
        self._candidates_table.setAlternatingRowColors(True)
        self._candidates_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._candidates_table.itemSelectionChanged.connect(self._on_candidate_selected)

        header = self._candidates_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 7):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._candidates_table)

        # Candidate detail
        detail_group = QGroupBox("ROI Details")
        detail_layout = QVBoxLayout(detail_group)
        self._candidate_detail = QTextEdit()
        self._candidate_detail.setReadOnly(True)
        self._candidate_detail.setMaximumHeight(100)
        self._candidate_detail.setPlaceholderText(
            "Select a candidate to see detailed ROI breakdown..."
        )
        detail_layout.addWidget(self._candidate_detail)
        layout.addWidget(detail_group)

        return widget

    def _apply_styles(self) -> None:
        """Apply VSCode Dark+ theme styling using THEME system."""
        self.setStyleSheet(f"""
            QDockWidget {{
                background-color: {THEME.bg_panel};
                color: {THEME.text_primary};
            }}
            QDockWidget::title {{
                background-color: {THEME.dock_title_bg};
                color: {THEME.dock_title_text};
                padding: 6px 12px;
                font-weight: 600;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-bottom: 1px solid {THEME.border_dark};
            }}
            QGroupBox {{
                background-color: {THEME.bg_header};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: 500;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: {THEME.text_secondary};
            }}
            {get_panel_table_stylesheet()}
            QTextEdit {{
                background-color: {THEME.bg_darkest};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border_dark};
                font-family: 'Cascadia Code', 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }}
            QLabel {{
                color: {THEME.text_primary};
                background: transparent;
            }}
            QPushButton {{
                background-color: {THEME.bg_light};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                padding: 4px 12px;
                border-radius: 3px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {THEME.bg_hover};
                border-color: {THEME.border_light};
            }}
            QPushButton:pressed {{
                background-color: {THEME.bg_lighter};
            }}
            QPushButton:disabled {{
                background-color: {THEME.bg_medium};
                color: {THEME.text_disabled};
                border-color: {THEME.border_dark};
            }}
            {get_panel_toolbar_stylesheet()}
            QProgressBar {{
                background-color: {THEME.bg_light};
                border: 1px solid {THEME.border_dark};
                border-radius: 3px;
                height: 18px;
                text-align: center;
                color: {THEME.text_primary};
                font-size: 10px;
            }}
            QProgressBar::chunk {{
                background-color: {THEME.accent_primary};
                border-radius: 2px;
            }}
            QTabWidget {{
                background-color: {THEME.bg_panel};
                border: none;
            }}
            QTabWidget::pane {{
                background-color: {THEME.bg_panel};
                border: none;
                border-top: 1px solid {THEME.border_dark};
            }}
            QTabBar {{
                background-color: {THEME.bg_header};
            }}
            QTabBar::tab {{
                background-color: {THEME.bg_header};
                color: {THEME.text_muted};
                padding: 8px 16px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 11px;
                font-weight: 500;
            }}
            QTabBar::tab:hover {{
                color: {THEME.text_primary};
                background-color: {THEME.bg_hover};
            }}
            QTabBar::tab:selected {{
                color: {THEME.text_primary};
                background-color: {THEME.bg_panel};
                border-bottom: 2px solid {THEME.accent_primary};
            }}
        """)

    def _setup_refresh_timer(self) -> None:
        """Setup auto-refresh timer."""
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._auto_refresh)
        # Refresh every 30 seconds when visible
        self._refresh_timer.setInterval(30000)

    def showEvent(self, event) -> None:
        """Handle show event."""
        super().showEvent(event)
        self._refresh_timer.start()
        self._load_workflows()

    def hideEvent(self, event) -> None:
        """Handle hide event."""
        super().hideEvent(event)
        self._refresh_timer.stop()

    def _get_miner(self):
        """Get or create process miner instance."""
        if self._miner is None:
            try:
                from casare_rpa.infrastructure.analytics.process_mining import (
                    get_process_miner,
                )

                self._miner = get_process_miner()
            except ImportError:
                logger.warning("Process mining module not available")
                return None
        return self._miner

    def _load_workflows(self) -> None:
        """Load available workflows into combo box."""
        miner = self._get_miner()
        if not miner:
            return

        current_text = self._workflow_combo.currentText()
        self._workflow_combo.blockSignals(True)
        self._workflow_combo.clear()
        self._workflow_combo.addItem("Select workflow...", None)

        workflows = miner.event_log.get_all_workflows()
        for wf_id in workflows:
            trace_count = miner.event_log.get_trace_count(wf_id)
            self._workflow_combo.addItem(f"{wf_id} ({trace_count} traces)", wf_id)

        # Restore selection
        idx = self._workflow_combo.findText(current_text)
        if idx >= 0:
            self._workflow_combo.setCurrentIndex(idx)

        self._workflow_combo.blockSignals(False)

    def _on_workflow_changed(self, index: int) -> None:
        """Handle workflow selection change."""
        workflow_id = self._workflow_combo.currentData()
        self._current_workflow = workflow_id
        self._discover_btn.setEnabled(workflow_id is not None)
        self._analyze_patterns_btn.setEnabled(workflow_id is not None)

        # Clear patterns when workflow changes
        self._current_patterns = []
        self._current_roi_estimates = []
        self._patterns_table.setRowCount(0)
        self._candidates_table.setRowCount(0)
        self._calc_roi_btn.setEnabled(False)
        self._export_roi_btn.setEnabled(False)

        if workflow_id:
            self.workflow_selected.emit(workflow_id)
            self._refresh_data()

    def _refresh_data(self) -> None:
        """Refresh all data for current workflow."""
        if not self._current_workflow:
            return

        miner = self._get_miner()
        if not miner:
            return

        # Get summary
        summary = miner.get_process_summary(self._current_workflow)

        # Update stats
        self._traces_label.setText(str(summary.get("trace_count", 0)))
        self._variants_label.setText(str(summary.get("variant_count", 0)))

        success_rate = summary.get("success_rate", 0) * 100
        self._success_label.setText(f"{success_rate:.0f}%")
        if success_rate >= 90:
            self._success_label.setStyleSheet(f"color: {THEME.status_success};")
        elif success_rate >= 70:
            self._success_label.setStyleSheet(f"color: {THEME.status_warning};")
        else:
            self._success_label.setStyleSheet(f"color: {THEME.status_error};")

        avg_duration = summary.get("avg_duration_ms", 0) / 1000
        self._duration_label.setText(f"{avg_duration:.1f}s")

        # Update model if available
        if summary.get("has_model"):
            self._current_model = summary.get("model")
            self._update_model_display(self._current_model)
            self._update_insights(summary.get("insights", []))

        # Update variants
        self._update_variants()

    def _run_discovery(self) -> None:
        """Run process discovery."""
        if not self._current_workflow:
            return

        miner = self._get_miner()
        if not miner:
            return

        model = miner.discover_process(self._current_workflow, min_traces=3)
        if model:
            self._current_model = model.to_dict()
            self._update_model_display(self._current_model)

            # Update insights
            insights = miner.get_insights(self._current_workflow)
            self._current_insights = [i.to_dict() for i in insights]
            self._update_insights(self._current_insights)

            # Enable AI enhance button if insights exist
            self._enhance_btn.setEnabled(len(self._current_insights) > 0)

            # Run conformance check
            self._run_conformance_check()

            self._refresh_data()
        else:
            self._enhance_btn.setEnabled(False)
            self._model_text.setText(
                "Insufficient data for process discovery.\n"
                "Need at least 3 execution traces."
            )

    def _update_model_display(self, model: Dict[str, Any]) -> None:
        """Update process model display."""
        if not model:
            return

        # Generate Mermaid diagram
        mermaid_lines = ["graph LR"]
        nodes = model.get("nodes", [])
        edges = model.get("edges", {})
        entry_nodes = set(model.get("entry_nodes", []))
        exit_nodes = set(model.get("exit_nodes", []))

        # Add nodes with styling
        for node in nodes:
            node_type = model.get("node_types", {}).get(node, "node")
            if node in entry_nodes:
                mermaid_lines.append(f"    {node}(({node_type}))")
            elif node in exit_nodes:
                mermaid_lines.append(f"    {node}[/{node_type}/]")
            else:
                mermaid_lines.append(f"    {node}[{node_type}]")

        # Add edges with frequencies
        for source, targets in edges.items():
            for target, edge_data in targets.items():
                freq = edge_data.get("frequency", 1)
                mermaid_lines.append(f"    {source} -->|{freq}| {target}")

        self._model_text.setText("\n".join(mermaid_lines))

        # Update statistics
        self._nodes_stat.setText(f"Nodes: {len(nodes)}")
        edge_count = sum(len(targets) for targets in edges.values())
        self._edges_stat.setText(f"Edges: {edge_count}")
        self._loops_stat.setText(f"Loops: {len(model.get('loop_nodes', []))}")
        self._parallel_stat.setText(f"Parallel: {len(model.get('parallel_pairs', []))}")

    def _update_variants(self) -> None:
        """Update variants table."""
        if not self._current_workflow:
            return

        miner = self._get_miner()
        if not miner:
            return

        variants = miner.get_variants(self._current_workflow)
        self._variants_table.setRowCount(0)

        for variant in variants.get("variants", []):
            row = self._variants_table.rowCount()
            self._variants_table.insertRow(row)

            # Variant ID (shortened)
            id_item = QTableWidgetItem(variant["variant_id"])
            id_item.setData(Qt.ItemDataRole.UserRole, variant)
            self._variants_table.setItem(row, 0, id_item)

            # Count
            count_item = QTableWidgetItem(str(variant["count"]))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._variants_table.setItem(row, 1, count_item)

            # Percentage
            pct_item = QTableWidgetItem(f"{variant['percentage']:.1f}%")
            pct_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._variants_table.setItem(row, 2, pct_item)

            # Avg duration
            duration = variant["avg_duration_ms"] / 1000
            duration_item = QTableWidgetItem(f"{duration:.1f}s")
            duration_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._variants_table.setItem(row, 3, duration_item)

            # Success rate
            success = variant["success_rate"] * 100
            success_item = QTableWidgetItem(f"{success:.0f}%")
            success_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if success >= 90:
                success_item.setForeground(QBrush(QColor(THEME.status_success)))
            elif success >= 70:
                success_item.setForeground(QBrush(QColor(THEME.status_warning)))
            else:
                success_item.setForeground(QBrush(QColor(THEME.status_error)))
            self._variants_table.setItem(row, 4, success_item)

    def _on_variant_selected(self) -> None:
        """Handle variant selection."""
        items = self._variants_table.selectedItems()
        if not items:
            return

        row = items[0].row()
        id_item = self._variants_table.item(row, 0)
        variant = id_item.data(Qt.ItemDataRole.UserRole)

        if variant:
            path = variant.get("sample_path", [])
            self._variant_path.setText(" -> ".join(path))

    def _update_insights(self, insights: List[Dict[str, Any]]) -> None:
        """Update insights tree."""
        self._insights_tree.clear()

        # Group by category
        categories = {}
        for insight in insights:
            category = insight.get("category", "other")
            if category not in categories:
                categories[category] = []
            categories[category].append(insight)

        # Category icons
        category_icons = {
            "bottleneck": "⚠️",
            "parallelization": "⚡",
            "simplification": "✂️",
            "error_pattern": "❌",
            "variant_analysis": "📊",
        }

        # Add to tree
        for category, cat_insights in categories.items():
            icon = category_icons.get(category, "📌")
            parent = QTreeWidgetItem(
                [f"{icon} {category.replace('_', ' ').title()}", ""]
            )
            parent.setExpanded(True)
            self._insights_tree.addTopLevelItem(parent)

            for insight in cat_insights:
                impact = insight.get("impact", "low")
                child = QTreeWidgetItem([insight.get("title", ""), impact.upper()])
                child.setData(0, Qt.ItemDataRole.UserRole, insight)

                # Color by impact
                if impact == "high":
                    child.setForeground(1, QBrush(QColor(THEME.status_error)))
                elif impact == "medium":
                    child.setForeground(1, QBrush(QColor(THEME.status_warning)))
                else:
                    child.setForeground(1, QBrush(QColor(THEME.status_success)))

                parent.addChild(child)

    def _on_insight_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle insight click."""
        insight = item.data(0, Qt.ItemDataRole.UserRole)
        if insight:
            # Show detail
            detail = f"**{insight.get('title', '')}**\n\n"
            detail += f"{insight.get('description', '')}\n\n"
            detail += f"**Recommendation:**\n{insight.get('recommendation', '')}\n\n"

            metrics = insight.get("metrics", {})
            if metrics:
                detail += "**Metrics:**\n"
                for key, value in metrics.items():
                    detail += f"  - {key}: {value}\n"

            self._insight_detail.setText(detail)
            self.insight_clicked.emit(insight)

    def _run_conformance_check(self) -> None:
        """Run conformance check."""
        if not self._current_workflow or not self._current_model:
            return

        miner = self._get_miner()
        if not miner:
            return

        traces = miner.event_log.get_traces_for_workflow(self._current_workflow)
        if not traces:
            return

        # Get model object
        model = miner._models.get(self._current_workflow)
        if not model:
            return

        # Run batch conformance check
        result = miner.conformance.batch_check(traces, model)

        # Update UI
        rate = result.get("conformance_rate", 0) * 100
        self._conformance_rate.setText(f"{rate:.0f}%")
        if rate >= 90:
            self._conformance_rate.setStyleSheet(f"color: {THEME.status_success};")
        elif rate >= 70:
            self._conformance_rate.setStyleSheet(f"color: {THEME.status_warning};")
        else:
            self._conformance_rate.setStyleSheet(f"color: {THEME.status_error};")

        fitness = result.get("average_fitness", 0) * 100
        self._fitness_score.setText(f"{fitness:.0f}%")
        if fitness >= 90:
            self._fitness_score.setStyleSheet(f"color: {THEME.status_success};")
        elif fitness >= 70:
            self._fitness_score.setStyleSheet(f"color: {THEME.status_warning};")
        else:
            self._fitness_score.setStyleSheet(f"color: {THEME.status_error};")

        # Update deviations table
        self._deviations_table.setRowCount(0)
        deviations = result.get("deviation_summary", {})
        for dev_type, count in deviations.items():
            row = self._deviations_table.rowCount()
            self._deviations_table.insertRow(row)

            type_item = QTableWidgetItem(dev_type.replace("_", " ").title())
            self._deviations_table.setItem(row, 0, type_item)

            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._deviations_table.setItem(row, 1, count_item)

            # Severity based on type
            severity = (
                "High" if "unexpected" in dev_type or "wrong" in dev_type else "Medium"
            )
            severity_item = QTableWidgetItem(severity)
            severity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if severity == "High":
                severity_item.setForeground(QBrush(QColor(THEME.status_error)))
            else:
                severity_item.setForeground(QBrush(QColor(THEME.status_warning)))
            self._deviations_table.setItem(row, 2, severity_item)

    def _auto_refresh(self) -> None:
        """Auto-refresh data."""
        if self.isVisible() and self._current_workflow:
            self._load_workflows()
            self._refresh_data()

    def add_demo_data(self) -> None:
        """Add demo data for testing."""
        miner = self._get_miner()
        if not miner:
            return

        from casare_rpa.infrastructure.analytics.process_mining import (
            ActivityStatus,
        )

        # Simulate workflow executions
        for i in range(20):
            case_id = f"demo_case_{i}"

            miner.record_activity(
                case_id=case_id,
                workflow_id="demo_workflow",
                workflow_name="Demo Workflow",
                node_id="start",
                node_type="start",
                duration_ms=50,
                status=ActivityStatus.COMPLETED,
            )

            miner.record_activity(
                case_id=case_id,
                workflow_id="demo_workflow",
                workflow_name="Demo Workflow",
                node_id="open_browser",
                node_type="browser",
                duration_ms=2000 + (i * 100),
                status=ActivityStatus.COMPLETED,
            )

            # Variant: some go through login
            if i % 3 == 0:
                miner.record_activity(
                    case_id=case_id,
                    workflow_id="demo_workflow",
                    workflow_name="Demo Workflow",
                    node_id="login",
                    node_type="type",
                    duration_ms=1500,
                    status=ActivityStatus.COMPLETED,
                )

            miner.record_activity(
                case_id=case_id,
                workflow_id="demo_workflow",
                workflow_name="Demo Workflow",
                node_id="extract_data",
                node_type="extract",
                duration_ms=500,
                status=ActivityStatus.FAILED
                if i % 7 == 0
                else ActivityStatus.COMPLETED,
            )

            miner.record_activity(
                case_id=case_id,
                workflow_id="demo_workflow",
                workflow_name="Demo Workflow",
                node_id="end",
                node_type="end",
                duration_ms=50,
                status=ActivityStatus.COMPLETED,
            )

            miner.complete_trace(case_id)

        self._load_workflows()
        logger.info("Added demo data for process mining")

    def cleanup(self) -> None:
        """Clean up resources."""
        self._refresh_timer.stop()

        # Clean up AI thread if running
        if self._ai_thread is not None:
            if self._ai_thread.isRunning():
                self._ai_thread.quit()
                self._ai_thread.wait(3000)  # Wait up to 3 seconds
            self._ai_thread.deleteLater()
            self._ai_thread = None

        if self._ai_worker is not None:
            self._ai_worker.deleteLater()
            self._ai_worker = None

        logger.debug("ProcessMiningPanel cleaned up")

    def _get_llm_manager(self):
        """Get or create LLM resource manager."""
        if self._llm_manager is None:
            try:
                from casare_rpa.infrastructure.resources.llm_resource_manager import (
                    LLMResourceManager,
                    LLMConfig,
                    LLMProvider,
                )

                self._llm_manager = LLMResourceManager()
            except ImportError:
                logger.warning("LLMResourceManager not available")
                return None
        return self._llm_manager

    def _enhance_insights_with_ai(self) -> None:
        """Enhance insights using the selected AI model."""
        if not self._current_insights:
            return

        # Guard against concurrent AI operations
        if self._ai_thread is not None and self._ai_thread.isRunning():
            logger.warning("AI enhancement already in progress")
            return

        ai_settings = self.get_ai_settings()
        model = ai_settings.get("model", "gpt-4o-mini")
        provider = ai_settings.get("provider", "OpenAI")

        # Show progress
        self._enhance_progress.show()
        self._enhance_btn.setEnabled(False)

        # Clean up previous thread/worker if they exist
        if self._ai_thread is not None:
            self._ai_thread.deleteLater()
        if self._ai_worker is not None:
            self._ai_worker.deleteLater()

        # Create worker and thread using module-level class
        self._ai_thread = QThread()
        self._ai_worker = AIEnhanceWorker(
            insights=self._current_insights,
            model=model,
            provider=provider,
            process_model=self._current_model or {},
        )
        self._ai_worker.moveToThread(self._ai_thread)

        # Connect signals
        self._ai_thread.started.connect(self._ai_worker.run)
        self._ai_worker.finished.connect(self._on_ai_enhance_finished)
        self._ai_worker.error.connect(self._on_ai_enhance_error)

        # Proper cleanup: quit thread after worker signals
        self._ai_worker.finished.connect(self._ai_thread.quit)
        self._ai_worker.error.connect(self._ai_thread.quit)

        # Schedule deletion after thread finishes
        self._ai_thread.finished.connect(self._ai_worker.deleteLater)
        self._ai_thread.finished.connect(self._ai_thread.deleteLater)

        # Start
        self._ai_thread.start()

    def _on_ai_enhance_finished(self, enhanced_insights: List[Dict[str, Any]]) -> None:
        """Handle AI enhancement completion."""
        self._enhance_progress.hide()
        self._enhance_btn.setEnabled(True)

        # Update insights with AI analysis
        self._current_insights = enhanced_insights
        self._update_insights(enhanced_insights)

        # Show AI analysis in detail panel
        if enhanced_insights and enhanced_insights[0].get("ai_analysis"):
            ai_text = enhanced_insights[0].get("ai_analysis", "")
            self._insight_detail.setText(f"**AI Analysis:**\n\n{ai_text}")

        logger.info("AI enhancement completed")

    def _on_ai_enhance_error(self, error_msg: str) -> None:
        """Handle AI enhancement error."""
        self._enhance_progress.hide()
        self._enhance_btn.setEnabled(True)

        from PySide6.QtWidgets import QMessageBox

        QMessageBox.warning(
            self,
            "AI Enhancement Error",
            f"Failed to enhance insights with AI:\n\n{error_msg}\n\n"
            "Make sure your API key is configured correctly.",
        )
        logger.error(f"AI enhancement failed: {error_msg}")

    # =========================================================================
    # Pattern Recognition Methods
    # =========================================================================

    def _get_pattern_recognizer(self):
        """Get or create pattern recognizer instance."""
        if self._pattern_recognizer is None:
            try:
                from casare_rpa.infrastructure.analytics.pattern_recognizer import (
                    PatternRecognizer,
                )

                self._pattern_recognizer = PatternRecognizer()
            except ImportError:
                logger.warning("PatternRecognizer not available")
                return None
        return self._pattern_recognizer

    def _get_roi_estimator(self):
        """Get or create ROI estimator instance."""
        if self._roi_estimator is None:
            try:
                from casare_rpa.infrastructure.analytics.roi_estimator import (
                    ROIEstimator,
                    ROIConfig,
                )

                config = ROIConfig(hourly_labor_cost=self._hourly_cost_spin.value())
                self._roi_estimator = ROIEstimator(config)
            except ImportError:
                logger.warning("ROIEstimator not available")
                return None
        return self._roi_estimator

    def _run_pattern_analysis(self) -> None:
        """Run pattern recognition on current workflow traces."""
        if not self._current_workflow:
            return

        miner = self._get_miner()
        if not miner:
            return

        recognizer = self._get_pattern_recognizer()
        if not recognizer:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self,
                "Pattern Recognition",
                "Pattern recognizer not available. Install scikit-learn for ML features.",
            )
            return

        # Get traces
        traces = miner.event_log.get_traces_for_workflow(self._current_workflow)
        if not traces:
            return

        # Show progress
        self._pattern_progress.show()
        self._analyze_patterns_btn.setEnabled(False)

        try:
            # Extract patterns
            patterns = recognizer.extract_patterns(
                traces=traces,
                min_samples=self._min_samples_spin.value(),
                eps=self._eps_spin.value(),
            )

            self._current_patterns = patterns
            self._update_patterns_table(patterns)

            # Enable ROI calculation if patterns found
            self._calc_roi_btn.setEnabled(len(patterns) > 0)

            logger.info(f"Found {len(patterns)} patterns in workflow")

        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self,
                "Pattern Analysis Error",
                f"Failed to analyze patterns:\n\n{str(e)}",
            )
        finally:
            self._pattern_progress.hide()
            self._analyze_patterns_btn.setEnabled(True)

    def _update_patterns_table(self, patterns: List[Any]) -> None:
        """Update patterns table with discovered patterns."""
        self._patterns_table.setRowCount(0)

        for pattern in patterns:
            row = self._patterns_table.rowCount()
            self._patterns_table.insertRow(row)

            # Pattern ID
            id_item = QTableWidgetItem(pattern.pattern_id)
            id_item.setData(Qt.ItemDataRole.UserRole, pattern)
            self._patterns_table.setItem(row, 0, id_item)

            # Frequency
            freq_item = QTableWidgetItem(str(pattern.frequency))
            freq_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._patterns_table.setItem(row, 1, freq_item)

            # Avg duration
            duration_s = pattern.avg_duration / 1000
            duration_item = QTableWidgetItem(f"{duration_s:.1f}s")
            duration_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._patterns_table.setItem(row, 2, duration_item)

            # Success rate
            success_pct = pattern.success_rate * 100
            success_item = QTableWidgetItem(f"{success_pct:.0f}%")
            success_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if success_pct >= 90:
                success_item.setForeground(QBrush(QColor(THEME.status_success)))
            elif success_pct >= 70:
                success_item.setForeground(QBrush(QColor(THEME.status_warning)))
            else:
                success_item.setForeground(QBrush(QColor(THEME.status_error)))
            self._patterns_table.setItem(row, 3, success_item)

            # Automation potential
            potential_pct = pattern.automation_potential * 100
            potential_item = QTableWidgetItem(f"{potential_pct:.0f}%")
            potential_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if potential_pct >= 70:
                potential_item.setForeground(QBrush(QColor(THEME.status_success)))
            elif potential_pct >= 40:
                potential_item.setForeground(QBrush(QColor(THEME.status_warning)))
            else:
                potential_item.setForeground(QBrush(QColor(THEME.status_error)))
            self._patterns_table.setItem(row, 4, potential_item)

            # Variance
            variance_item = QTableWidgetItem(f"{pattern.variance_score:.2f}")
            variance_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._patterns_table.setItem(row, 5, variance_item)

    def _on_pattern_selected(self) -> None:
        """Handle pattern selection in table."""
        items = self._patterns_table.selectedItems()
        if not items:
            self._create_subflow_btn.setEnabled(False)
            return

        row = items[0].row()
        id_item = self._patterns_table.item(row, 0)
        pattern = id_item.data(Qt.ItemDataRole.UserRole)

        if pattern:
            self._create_subflow_btn.setEnabled(True)

            # Show pattern details
            detail_text = f"**Pattern: {pattern.pattern_id}**\n\n"
            detail_text += "**Activity Sequence:**\n"
            detail_text += " -> ".join(pattern.activity_sequence)
            detail_text += f"\n\n**Node Types:** {', '.join(pattern.node_types)}"

            if pattern.time_pattern:
                detail_text += f"\n**Time Pattern:** {pattern.time_pattern}"

            detail_text += f"\n**Representative Traces:** {', '.join(pattern.representative_traces[:3])}"

            self._pattern_detail.setText(detail_text)

    def _create_subflow_from_pattern(self) -> None:
        """Create a subflow from the selected pattern."""
        items = self._patterns_table.selectedItems()
        if not items:
            return

        row = items[0].row()
        id_item = self._patterns_table.item(row, 0)
        pattern = id_item.data(Qt.ItemDataRole.UserRole)

        if not pattern:
            return

        # Emit signal or create subflow
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.information(
            self,
            "Create Subflow",
            f"Would create subflow from pattern {pattern.pattern_id}\n\n"
            f"Activities: {', '.join(pattern.activity_sequence)}\n\n"
            "This feature will be connected to the workflow editor.",
        )

        logger.info(f"Create subflow requested for pattern {pattern.pattern_id}")

    # =========================================================================
    # ROI Estimation Methods
    # =========================================================================

    def _calculate_roi(self) -> None:
        """Calculate ROI for discovered patterns."""
        if not self._current_patterns:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.information(
                self,
                "Calculate ROI",
                "No patterns available. Run pattern analysis first.",
            )
            return

        # Update ROI estimator with current hourly cost
        try:
            from casare_rpa.infrastructure.analytics.roi_estimator import (
                ROIEstimator,
                ROIConfig,
            )

            config = ROIConfig(hourly_labor_cost=self._hourly_cost_spin.value())
            self._roi_estimator = ROIEstimator(config)

        except ImportError:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self,
                "ROI Calculation",
                "ROI estimator not available.",
            )
            return

        try:
            # Calculate ROI for all patterns
            estimates = self._roi_estimator.estimate_batch(self._current_patterns)
            self._current_roi_estimates = estimates

            self._update_candidates_table(estimates)
            self._update_roi_summary(estimates)

            self._export_roi_btn.setEnabled(len(estimates) > 0)

            logger.info(f"Calculated ROI for {len(estimates)} patterns")

        except Exception as e:
            logger.error(f"ROI calculation failed: {e}")
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self,
                "ROI Calculation Error",
                f"Failed to calculate ROI:\n\n{str(e)}",
            )

    def _update_candidates_table(self, estimates: List[Any]) -> None:
        """Update candidates table with ROI estimates."""
        self._candidates_table.setRowCount(0)

        for estimate in estimates:
            row = self._candidates_table.rowCount()
            self._candidates_table.insertRow(row)

            # Pattern ID
            id_item = QTableWidgetItem(estimate.pattern_id)
            id_item.setData(Qt.ItemDataRole.UserRole, estimate)
            self._candidates_table.setItem(row, 0, id_item)

            # ROI Score
            score_item = QTableWidgetItem(f"{estimate.roi_score:.0f}")
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if estimate.roi_score >= 70:
                score_item.setForeground(QBrush(QColor(THEME.status_success)))
            elif estimate.roi_score >= 40:
                score_item.setForeground(QBrush(QColor(THEME.status_warning)))
            else:
                score_item.setForeground(QBrush(QColor(THEME.status_error)))
            self._candidates_table.setItem(row, 1, score_item)

            # Hours/Year
            hours_item = QTableWidgetItem(f"{estimate.annual_hours_saved:.0f}h")
            hours_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._candidates_table.setItem(row, 2, hours_item)

            # Savings/Year
            savings_item = QTableWidgetItem(f"${estimate.annual_cost_savings:,.0f}")
            savings_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._candidates_table.setItem(row, 3, savings_item)

            # Dev Hours
            dev_item = QTableWidgetItem(f"{estimate.estimated_dev_hours:.0f}h")
            dev_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._candidates_table.setItem(row, 4, dev_item)

            # Payback
            if estimate.payback_months < 999:
                payback_text = f"{estimate.payback_months:.1f}mo"
            else:
                payback_text = ">3yr"
            payback_item = QTableWidgetItem(payback_text)
            payback_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if estimate.payback_months <= 6:
                payback_item.setForeground(QBrush(QColor(THEME.status_success)))
            elif estimate.payback_months <= 18:
                payback_item.setForeground(QBrush(QColor(THEME.status_warning)))
            else:
                payback_item.setForeground(QBrush(QColor(THEME.status_error)))
            self._candidates_table.setItem(row, 5, payback_item)

            # Recommendation
            rec_text = estimate.recommendation.value.replace("_", " ").title()
            rec_item = QTableWidgetItem(rec_text[:12])  # Truncate for display
            rec_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            rec_item.setToolTip(rec_text)
            self._candidates_table.setItem(row, 6, rec_item)

    def _update_roi_summary(self, estimates: List[Any]) -> None:
        """Update ROI summary statistics."""
        if not estimates:
            self._total_savings_label.setText("$0")
            self._total_hours_label.setText("0h")
            self._avg_payback_label.setText("-")
            return

        # Calculate totals (for recommended patterns only)
        recommended = [
            e
            for e in estimates
            if e.recommendation.value in ("highly_recommended", "recommended")
        ]

        if recommended:
            total_savings = sum(e.annual_cost_savings for e in recommended)
            total_hours = sum(e.annual_hours_saved for e in recommended)
            avg_payback = sum(min(e.payback_months, 36) for e in recommended) / len(
                recommended
            )
        else:
            total_savings = sum(e.annual_cost_savings for e in estimates)
            total_hours = sum(e.annual_hours_saved for e in estimates)
            avg_payback = sum(min(e.payback_months, 36) for e in estimates) / len(
                estimates
            )

        self._total_savings_label.setText(f"${total_savings:,.0f}")
        if total_savings > 10000:
            self._total_savings_label.setStyleSheet(f"color: {THEME.status_success};")
        else:
            self._total_savings_label.setStyleSheet("")

        self._total_hours_label.setText(f"{total_hours:.0f}h")

        self._avg_payback_label.setText(f"{avg_payback:.1f}mo")
        if avg_payback <= 6:
            self._avg_payback_label.setStyleSheet(f"color: {THEME.status_success};")
        elif avg_payback <= 18:
            self._avg_payback_label.setStyleSheet(f"color: {THEME.status_warning};")
        else:
            self._avg_payback_label.setStyleSheet(f"color: {THEME.status_error};")

    def _on_candidate_selected(self) -> None:
        """Handle candidate selection in table."""
        items = self._candidates_table.selectedItems()
        if not items:
            return

        row = items[0].row()
        id_item = self._candidates_table.item(row, 0)
        estimate = id_item.data(Qt.ItemDataRole.UserRole)

        if estimate:
            # Show ROI details
            factors = estimate.factors

            detail_text = f"**{estimate.pattern_id} - {estimate.recommendation.value.replace('_', ' ').title()}**\n\n"
            detail_text += f"**ROI Score:** {estimate.roi_score:.0f}/100 (Confidence: {estimate.confidence*100:.0f}%)\n"
            detail_text += f"**Complexity:** {estimate.complexity.value}\n\n"
            detail_text += "**Calculations:**\n"
            detail_text += (
                f"  - Annual Executions: {factors.get('annual_executions', 0):,}\n"
            )
            detail_text += f"  - Time per Execution: {factors.get('time_per_exec_hours', 0)*60:.1f} min\n"
            detail_text += (
                f"  - Development Cost: ${factors.get('dev_cost_usd', 0):,.0f}\n"
            )
            detail_text += f"  - Annual Maintenance: ${factors.get('annual_maintenance_usd', 0):,.0f}\n"

            self._candidate_detail.setText(detail_text)

    def _export_roi_csv(self) -> None:
        """Export ROI estimates to CSV file."""
        if not self._current_roi_estimates:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export ROI Analysis",
            "roi_analysis.csv",
            "CSV Files (*.csv);;All Files (*)",
        )

        if not file_path:
            return

        try:
            import csv

            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Header
                writer.writerow(
                    [
                        "Pattern ID",
                        "ROI Score",
                        "Annual Hours Saved",
                        "Annual Cost Savings",
                        "Development Hours",
                        "Payback Months",
                        "Recommendation",
                        "Complexity",
                        "Confidence",
                    ]
                )

                # Data
                for e in self._current_roi_estimates:
                    writer.writerow(
                        [
                            e.pattern_id,
                            f"{e.roi_score:.1f}",
                            f"{e.annual_hours_saved:.1f}",
                            f"{e.annual_cost_savings:.2f}",
                            f"{e.estimated_dev_hours:.1f}",
                            f"{e.payback_months:.1f}",
                            e.recommendation.value,
                            e.complexity.value,
                            f"{e.confidence:.2f}",
                        ]
                    )

            logger.info(f"ROI analysis exported to {file_path}")

            from PySide6.QtWidgets import QMessageBox

            QMessageBox.information(
                self,
                "Export Complete",
                f"ROI analysis exported to:\n{file_path}",
            )

        except Exception as e:
            logger.error(f"Failed to export ROI: {e}")
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self,
                "Export Error",
                f"Failed to export ROI analysis:\n\n{str(e)}",
            )

    def _on_workflow_changed_pattern_update(self, index: int) -> None:
        """Update pattern buttons when workflow changes."""
        workflow_id = self._workflow_combo.currentData()
        has_workflow = workflow_id is not None

        self._analyze_patterns_btn.setEnabled(has_workflow)
        self._calc_roi_btn.setEnabled(has_workflow and len(self._current_patterns) > 0)
