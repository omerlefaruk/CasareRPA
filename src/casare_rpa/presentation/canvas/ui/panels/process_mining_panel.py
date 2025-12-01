"""
Process Mining Panel UI Component.

Provides AI-powered process discovery, variant analysis, conformance checking,
and optimization insights from workflow execution logs.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

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
    QSplitter,
    QProgressBar,
    QGroupBox,
    QTreeWidget,
    QTreeWidgetItem,
    QFrame,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QBrush, QFont

from loguru import logger


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

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the process mining panel."""
        super().__init__("Process Mining", parent)
        self.setObjectName("ProcessMiningDock")

        self._miner = None
        self._current_workflow: Optional[str] = None
        self._current_model = None
        self._current_insights: List[Dict[str, Any]] = []
        self._llm_manager = None

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

        # Insights tab
        insights_tab = self._create_insights_tab()
        self._tabs.addTab(insights_tab, "Insights")

        # Conformance tab
        conformance_tab = self._create_conformance_tab()
        self._tabs.addTab(conformance_tab, "Conformance")

        main_layout.addWidget(self._tabs)
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
        self._api_key_status.setStyleSheet("color: #89d185;")  # Green = OK
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
            "Local (Ollama)": None,  # No API key needed
        }

        env_var = env_vars.get(provider)

        if env_var is None:
            # Local provider - no key needed
            self._api_key_status.setText("Not required")
            self._api_key_status.setStyleSheet("color: #89d185;")
            return

        # Check environment
        if os.environ.get(env_var):
            self._api_key_status.setText("Found (env)")
            self._api_key_status.setStyleSheet("color: #89d185;")
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
                    self._api_key_status.setStyleSheet("color: #89d185;")
                    return
        except Exception:
            pass

        # Not found
        self._api_key_status.setText("Not found")
        self._api_key_status.setStyleSheet("color: #f44747;")

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
        info_label.setStyleSheet("color: #888; font-size: 9pt;")
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
        info_label.setStyleSheet("color: #888; font-size: 9pt;")
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
        info_label.setStyleSheet("color: #888; font-size: 9pt;")
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

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QDockWidget {
                background: #252525;
                color: #e0e0e0;
            }
            QDockWidget::title {
                background: #2d2d2d;
                padding: 6px;
            }
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
            }
            QTableWidget {
                background-color: #2d2d2d;
                alternate-background-color: #323232;
                border: 1px solid #4a4a4a;
                gridline-color: #3d3d3d;
                color: #e0e0e0;
            }
            QTableWidget::item:selected {
                background-color: #5a8a9a;
            }
            QHeaderView::section {
                background-color: #3d3d3d;
                color: #e0e0e0;
                border: none;
                border-right: 1px solid #4a4a4a;
                border-bottom: 1px solid #4a4a4a;
                padding: 4px;
            }
            QTreeWidget {
                background-color: #2d2d2d;
                alternate-background-color: #323232;
                border: 1px solid #4a4a4a;
                color: #e0e0e0;
            }
            QTreeWidget::item:selected {
                background-color: #5a8a9a;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3d3d3d;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
            }
            QLabel {
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #3d3d3d;
                color: #e0e0e0;
                border: 1px solid #4a4a4a;
                padding: 4px 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #5a5a5a;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #666666;
            }
            QComboBox {
                background-color: #3d3d3d;
                color: #e0e0e0;
                border: 1px solid #4a4a4a;
                padding: 4px;
                border-radius: 3px;
            }
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
            self._success_label.setStyleSheet("color: #89d185;")
        elif success_rate >= 70:
            self._success_label.setStyleSheet("color: #cca700;")
        else:
            self._success_label.setStyleSheet("color: #f44747;")

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
                success_item.setForeground(QBrush(QColor("#89d185")))
            elif success >= 70:
                success_item.setForeground(QBrush(QColor("#cca700")))
            else:
                success_item.setForeground(QBrush(QColor("#f44747")))
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
                    child.setForeground(1, QBrush(QColor("#f44747")))
                elif impact == "medium":
                    child.setForeground(1, QBrush(QColor("#cca700")))
                else:
                    child.setForeground(1, QBrush(QColor("#89d185")))

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
            self._conformance_rate.setStyleSheet("color: #89d185;")
        elif rate >= 70:
            self._conformance_rate.setStyleSheet("color: #cca700;")
        else:
            self._conformance_rate.setStyleSheet("color: #f44747;")

        fitness = result.get("average_fitness", 0) * 100
        self._fitness_score.setText(f"{fitness:.0f}%")
        if fitness >= 90:
            self._fitness_score.setStyleSheet("color: #89d185;")
        elif fitness >= 70:
            self._fitness_score.setStyleSheet("color: #cca700;")
        else:
            self._fitness_score.setStyleSheet("color: #f44747;")

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
                severity_item.setForeground(QBrush(QColor("#f44747")))
            else:
                severity_item.setForeground(QBrush(QColor("#cca700")))
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

        ai_settings = self.get_ai_settings()
        model = ai_settings.get("model", "gpt-4o-mini")

        # Show progress
        self._enhance_progress.show()
        self._enhance_btn.setEnabled(False)

        # Run in background thread to avoid blocking UI
        from PySide6.QtCore import QThread, QObject, Signal as QtSignal

        class AIEnhanceWorker(QObject):
            finished = QtSignal(list)
            error = QtSignal(str)

            def __init__(self, panel, insights, model):
                super().__init__()
                self.panel = panel
                self.insights = insights
                self.model = model

            def run(self):
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

            async def _enhance_async(self):
                manager = self.panel._get_llm_manager()
                if not manager:
                    raise RuntimeError("LLM manager not available")

                from casare_rpa.infrastructure.resources.llm_resource_manager import (
                    LLMConfig,
                    LLMProvider,
                )

                # Configure with selected model
                provider = self.panel._provider_combo.currentText()
                provider_map = {
                    "OpenAI": LLMProvider.OPENAI,
                    "Anthropic": LLMProvider.ANTHROPIC,
                    "Local (Ollama)": LLMProvider.OLLAMA,
                }
                llm_provider = provider_map.get(provider, LLMProvider.OPENAI)

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
- Activities: {len(self.panel._current_model.get('activities', []))}
- Edges: {sum(len(t) for t in self.panel._current_model.get('edges', {}).values())}

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

        # Create worker and thread
        self._ai_thread = QThread()
        self._ai_worker = AIEnhanceWorker(self, self._current_insights, model)
        self._ai_worker.moveToThread(self._ai_thread)

        # Connect signals
        self._ai_thread.started.connect(self._ai_worker.run)
        self._ai_worker.finished.connect(self._on_ai_enhance_finished)
        self._ai_worker.error.connect(self._on_ai_enhance_error)
        self._ai_worker.finished.connect(self._ai_thread.quit)
        self._ai_worker.error.connect(self._ai_thread.quit)

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
