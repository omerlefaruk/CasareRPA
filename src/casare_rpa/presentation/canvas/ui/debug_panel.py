"""
Enhanced Debug Panel UI Component.

Provides comprehensive debugging capabilities:
- Execution logs with filtering
- Variable inspector with real-time updates
- Call stack visualization
- Watch expressions
- Breakpoint management (regular, conditional, hit-count)
- Expression evaluation / Debug REPL console
- Execution state snapshot/restore

Uses LazySubscription for EventBus optimization - subscriptions are only active
when the panel is visible, reducing overhead when panel is hidden.

Epic 7.5: Migrated to THEME_V2/TOKENS_V2 design system.
- Uses THEME_V2/TOKENS_V2 for all styling
- Uses icon_v2 singleton for Lucide SVG icons
- Zero hardcoded colors
- Zero animations/shadows
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from loguru import logger
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction, QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS
from casare_rpa.presentation.canvas.theme_system.helpers import (
    margin_compact,
    margin_none,
    set_button_size,
    set_fixed_size,
    set_margins,
    set_min_size,
    set_spacing,
)
from casare_rpa.presentation.canvas.ui.panels.panel_ux_helpers import (
    get_panel_table_stylesheet,
    get_panel_toolbar_stylesheet,
)

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.debugger.debug_controller import (
        CallStackFrame,
        DebugController,
        ExecutionSnapshot,
        WatchExpression,
    )

try:
    from casare_rpa.presentation.canvas.events import (
        Event,
        EventType,
        LazySubscriptionGroup,
    )

    HAS_EVENT_BUS = True
except ImportError:
    HAS_EVENT_BUS = False


class DebugPanel(QDockWidget):
    """
    Enhanced dockable debug panel for interactive workflow debugging.

    Features:
    - Execution logs with filtering and navigation
    - Variable inspector with tree view
    - Call stack visualization
    - Watch expressions
    - Breakpoint management with conditions
    - Debug REPL console for expression evaluation
    - Execution snapshots

    Signals:
        navigate_to_node: Emitted when user requests to navigate to node (str: node_id)
        breakpoint_toggled: Emitted when breakpoint is toggled (str: node_id, bool: enabled)
        breakpoint_condition_changed: Emitted when condition is set (str: node_id, str: condition)
        watch_added: Emitted when watch expression is added (str: expression)
        watch_removed: Emitted when watch expression is removed (str: expression)
        step_over_requested: Emitted when step over is requested
        step_into_requested: Emitted when step into is requested
        step_out_requested: Emitted when step out is requested
        continue_requested: Emitted when continue is requested
        snapshot_requested: Emitted when snapshot is requested
        snapshot_restore_requested: Emitted when snapshot restore is requested (str: id)
        expression_evaluated: Emitted when expression is evaluated (str: expr, result)
        clear_requested: Emitted when user requests to clear logs
    """

    navigate_to_node = Signal(str)
    breakpoint_toggled = Signal(str, bool)
    breakpoint_condition_changed = Signal(str, str)
    watch_added = Signal(str)
    watch_removed = Signal(str)
    step_over_requested = Signal()
    step_into_requested = Signal()
    step_out_requested = Signal()
    continue_requested = Signal()
    snapshot_requested = Signal()
    snapshot_restore_requested = Signal(str)
    expression_evaluated = Signal(str, object)
    clear_requested = Signal()

    COL_TIME = 0
    COL_LEVEL = 1
    COL_NODE = 2
    COL_MESSAGE = 3

    def __init__(
        self,
        parent: QWidget | None = None,
        debug_controller: Optional["DebugController"] = None,
        embedded: bool = False,
    ) -> None:
        """
        Initialize the enhanced debug panel.

        Args:
            parent: Optional parent widget
            debug_controller: Optional debug controller for integration
            embedded: If True, behave as QWidget (for embedding in tab panels)
        """
        self._embedded = embedded
        if embedded:
            # Initialize as QWidget for embedding in tabs
            QWidget.__init__(self, parent)
        else:
            super().__init__("Debug", parent)
            self.setObjectName("DebugDock")

        self._debug_controller = debug_controller
        self._auto_scroll = True
        self._current_filter = "All"
        self._max_log_entries = 1000
        self._repl_history: list[str] = []
        self._repl_history_index = -1

        if not embedded:
            self._setup_dock()
        self._setup_ui()
        self._apply_styles()
        self._setup_connections()

        if HAS_EVENT_BUS:
            self._setup_lazy_subscriptions()

        logger.debug("Enhanced DebugPanel initialized")

    def set_debug_controller(self, controller: "DebugController") -> None:
        """
        Set the debug controller for integration.

        Args:
            controller: Debug controller instance
        """
        self._debug_controller = controller
        self._connect_debug_controller()

    def _connect_debug_controller(self) -> None:
        """Connect to debug controller signals."""
        if not self._debug_controller:
            return

        self._debug_controller.variables_updated.connect(self._on_variables_updated)
        self._debug_controller.call_stack_updated.connect(self._on_call_stack_updated)
        self._debug_controller.watch_updated.connect(self._on_watch_updated)
        self._debug_controller.breakpoint_added.connect(self._on_breakpoint_added)
        self._debug_controller.breakpoint_removed.connect(self._on_breakpoint_removed)
        self._debug_controller.breakpoint_hit.connect(self._on_breakpoint_hit_signal)
        self._debug_controller.step_completed.connect(self._on_step_completed)
        self._debug_controller.snapshot_created.connect(self._on_snapshot_created)
        self._debug_controller.execution_paused.connect(self._on_execution_paused)
        self._debug_controller.execution_resumed.connect(self._on_execution_resumed)

    def _setup_dock(self) -> None:
        """Configure dock widget properties."""
        self.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
            # NO DockWidgetFloatable - dock-only enforcement (v2 requirement)
        )
        set_min_size(self, TOKENS_V2.sizes.panel_default_width, TOKENS_V2.sizes.dialog_sm_width)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        if self._embedded:
            main_layout = QVBoxLayout(self)
        else:
            container = QWidget()
            main_layout = QVBoxLayout(container)
        margin_none(main_layout)
        set_spacing(main_layout, TOKENS_V2.spacing.xs)

        step_toolbar = self._create_step_toolbar()
        main_layout.addWidget(step_toolbar)

        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.TabPosition.South)

        logs_tab = self._create_logs_tab()
        self._tabs.addTab(logs_tab, "Logs")

        variables_tab = self._create_variables_tab()
        self._tabs.addTab(variables_tab, "Variables")

        call_stack_tab = self._create_call_stack_tab()
        self._tabs.addTab(call_stack_tab, "Call Stack")

        watch_tab = self._create_watch_tab()
        self._tabs.addTab(watch_tab, "Watch")

        breakpoints_tab = self._create_breakpoints_tab()
        self._tabs.addTab(breakpoints_tab, "Breakpoints")

        repl_tab = self._create_repl_tab()
        self._tabs.addTab(repl_tab, "REPL")

        snapshots_tab = self._create_snapshots_tab()
        self._tabs.addTab(snapshots_tab, "Snapshots")

        main_layout.addWidget(self._tabs)
        if not self._embedded:
            self.setWidget(container)

    def _create_step_toolbar(self) -> QFrame:
        """
        Create the step control toolbar.

        Returns:
            Toolbar frame widget
        """
        toolbar = QFrame()
        toolbar.setFrameShape(QFrame.Shape.StyledPanel)
        toolbar.setMaximumHeight(TOKENS_V2.sizes.button_lg + TOKENS_V2.spacing.xs)
        layout = QHBoxLayout(toolbar)
        set_margins(layout, TOKENS_V2.margin.toolbar)
        set_spacing(layout, TOKENS_V2.spacing.sm)

        self._btn_step_over = QPushButton("Step Over")
        self._btn_step_over.setToolTip("Execute current node and pause at next (F10)")
        set_button_size(self._btn_step_over, "md")
        self._btn_step_over.setMinimumWidth(TOKENS_V2.sizes.button_min_width)
        self._btn_step_over.clicked.connect(self.step_over_requested.emit)

        self._btn_step_into = QPushButton("Step Into")
        self._btn_step_into.setToolTip("Step into nested structures (F11)")
        set_button_size(self._btn_step_into, "md")
        self._btn_step_into.setMinimumWidth(TOKENS_V2.sizes.button_min_width)
        self._btn_step_into.clicked.connect(self.step_into_requested.emit)

        self._btn_step_out = QPushButton("Step Out")
        self._btn_step_out.setToolTip("Continue until exiting current scope (Shift+F11)")
        set_button_size(self._btn_step_out, "md")
        self._btn_step_out.setMinimumWidth(TOKENS_V2.sizes.button_min_width)
        self._btn_step_out.clicked.connect(self.step_out_requested.emit)

        self._btn_continue = QPushButton("Continue")
        self._btn_continue.setToolTip("Continue to next breakpoint (F5)")
        set_button_size(self._btn_continue, "md")
        self._btn_continue.setMinimumWidth(TOKENS_V2.sizes.button_min_width)
        self._btn_continue.clicked.connect(self.continue_requested.emit)

        self._lbl_status = QLabel("Idle")
        self._lbl_status.setStyleSheet(f"color: {THEME_V2.text_muted}; font-style: italic;")

        layout.addWidget(self._btn_step_over)
        layout.addWidget(self._btn_step_into)
        layout.addWidget(self._btn_step_out)
        layout.addWidget(self._btn_continue)
        layout.addStretch()
        layout.addWidget(self._lbl_status)

        self._set_stepping_enabled(False)

        return toolbar

    def _create_logs_tab(self) -> QWidget:
        """Create the logs tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        margin_compact(layout)
        set_spacing(layout, TOKENS_V2.spacing.sm)

        toolbar = QHBoxLayout()
        set_spacing(toolbar, TOKENS_V2.spacing.md)

        filter_label = QLabel("Filter:")
        self._filter_combo = QComboBox()
        set_fixed_size(
            self._filter_combo, TOKENS_V2.sizes.button_min_width, TOKENS_V2.sizes.input_md
        )
        self._filter_combo.addItems(["All", "Info", "Warning", "Error", "Success"])
        self._filter_combo.currentTextChanged.connect(self._on_filter_changed)

        self._auto_scroll_btn = QPushButton("Auto-scroll: ON")
        self._auto_scroll_btn.setCheckable(True)
        self._auto_scroll_btn.setChecked(True)
        self._auto_scroll_btn.setMinimumWidth(TOKENS_V2.sizes.dialog_sm_width // 10)
        self._auto_scroll_btn.clicked.connect(self._on_auto_scroll_toggled)

        clear_btn = QPushButton("Clear")
        clear_btn.setMinimumWidth(TOKENS_V2.sizes.button_lg + TOKENS_V2.sizes.button_md)
        clear_btn.clicked.connect(self.clear_logs)

        toolbar.addWidget(filter_label)
        toolbar.addWidget(self._filter_combo)
        toolbar.addStretch()
        toolbar.addWidget(self._auto_scroll_btn)
        toolbar.addWidget(clear_btn)

        layout.addLayout(toolbar)

        self._log_table = QTableWidget()
        self._log_table.setColumnCount(4)
        self._log_table.setHorizontalHeaderLabels(["Time", "Level", "Node", "Message"])
        self._log_table.setAlternatingRowColors(True)
        self._log_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._log_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._log_table.itemDoubleClicked.connect(self._on_log_double_click)
        self._log_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        header = self._log_table.horizontalHeader()
        header.setSectionResizeMode(self.COL_TIME, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_LEVEL, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_NODE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_MESSAGE, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self._log_table)

        return widget

    def _create_variables_tab(self) -> QWidget:
        """Create the variables inspector tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        margin_compact(layout)

        toolbar = QHBoxLayout()
        self._var_search = QLineEdit()
        self._var_search.setPlaceholderText("Search variables...")
        self._var_search.textChanged.connect(self._filter_variables)

        btn_refresh = QPushButton("Refresh")
        btn_refresh.setMinimumWidth(TOKENS_V2.sizes.input_md + TOKENS_V2.sizes.button_md)
        btn_refresh.clicked.connect(self._refresh_variables)

        btn_expand_all = QPushButton("Expand All")
        btn_expand_all.setMinimumWidth(TOKENS_V2.sizes.dialog_sm_width // 5)
        btn_expand_all.clicked.connect(self._expand_all_variables)

        btn_collapse_all = QPushButton("Collapse All")
        btn_collapse_all.setMinimumWidth(TOKENS_V2.sizes.dialog_sm_width // 5)
        btn_collapse_all.clicked.connect(self._collapse_all_variables)

        toolbar.addWidget(self._var_search)
        toolbar.addWidget(btn_refresh)
        toolbar.addWidget(btn_expand_all)
        toolbar.addWidget(btn_collapse_all)

        layout.addLayout(toolbar)

        self._var_tree = QTreeWidget()
        self._var_tree.setHeaderLabels(["Name", "Value", "Type"])
        self._var_tree.setAlternatingRowColors(True)
        self._var_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._var_tree.customContextMenuRequested.connect(self._show_variable_context_menu)

        header = self._var_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.resizeSection(0, TOKENS_V2.sizes.panel_default_width // 2)

        layout.addWidget(self._var_tree)

        return widget

    def _create_call_stack_tab(self) -> QWidget:
        """Create the call stack tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        margin_compact(layout)

        self._call_stack_table = QTableWidget()
        self._call_stack_table.setColumnCount(4)
        self._call_stack_table.setHorizontalHeaderLabels(["#", "Node", "Type", "Entry Time"])
        self._call_stack_table.setAlternatingRowColors(True)
        self._call_stack_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._call_stack_table.itemDoubleClicked.connect(self._on_call_stack_double_click)
        self._call_stack_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        header = self._call_stack_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._call_stack_table)

        return widget

    def _create_watch_tab(self) -> QWidget:
        """Create the watch expressions tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        margin_compact(layout)

        toolbar = QHBoxLayout()
        self._watch_input = QLineEdit()
        self._watch_input.setPlaceholderText("Enter expression to watch...")
        self._watch_input.returnPressed.connect(self._add_watch_from_input)

        btn_add = QPushButton("Add")
        btn_add.setMinimumWidth(TOKENS_V2.sizes.button_lg + TOKENS_V2.sizes.button_md)
        btn_add.clicked.connect(self._add_watch_from_input)

        btn_remove = QPushButton("Remove")
        btn_remove.setMinimumWidth(TOKENS_V2.sizes.input_md + TOKENS_V2.sizes.button_md)
        btn_remove.clicked.connect(self._remove_selected_watch)

        toolbar.addWidget(self._watch_input)
        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_remove)

        layout.addLayout(toolbar)

        self._watch_table = QTableWidget()
        self._watch_table.setColumnCount(3)
        self._watch_table.setHorizontalHeaderLabels(["Expression", "Value", "Error"])
        self._watch_table.setAlternatingRowColors(True)
        self._watch_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._watch_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        header = self._watch_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self._watch_table)

        return widget

    def _create_breakpoints_tab(self) -> QWidget:
        """Create the breakpoints management tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        margin_compact(layout)

        toolbar = QHBoxLayout()

        btn_clear_all = QPushButton("Clear All")
        btn_clear_all.setMinimumWidth(TOKENS_V2.sizes.button_min_width)
        btn_clear_all.clicked.connect(self._on_clear_breakpoints)

        btn_disable_all = QPushButton("Disable All")
        btn_disable_all.setMinimumWidth(TOKENS_V2.sizes.button_min_width)
        btn_disable_all.clicked.connect(self._disable_all_breakpoints)

        btn_enable_all = QPushButton("Enable All")
        btn_enable_all.setMinimumWidth(TOKENS_V2.sizes.button_min_width)
        btn_enable_all.clicked.connect(self._enable_all_breakpoints)

        toolbar.addStretch()
        toolbar.addWidget(btn_enable_all)
        toolbar.addWidget(btn_disable_all)
        toolbar.addWidget(btn_clear_all)

        layout.addLayout(toolbar)

        self._bp_table = QTableWidget()
        self._bp_table.setColumnCount(5)
        self._bp_table.setHorizontalHeaderLabels(
            ["Enabled", "Node", "Type", "Condition", "Hit Count"]
        )
        self._bp_table.setAlternatingRowColors(True)
        self._bp_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._bp_table.itemDoubleClicked.connect(self._on_bp_double_click)
        self._bp_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._bp_table.customContextMenuRequested.connect(self._show_breakpoint_context_menu)

        header = self._bp_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._bp_table)

        return widget

    def _create_repl_tab(self) -> QWidget:
        """Create the debug REPL console tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        margin_compact(layout)

        self._repl_output = QPlainTextEdit()
        self._repl_output.setReadOnly(True)
        self._repl_output.setFont(QFont(TOKENS_V2.typography.family, TOKENS_V2.typography.body))
        self._repl_output.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {THEME_V2.bg_canvas};
                color: {THEME_V2.text_primary};
                border: 1px solid {THEME_V2.border};
            }}
        """)
        self._repl_output.setPlainText(
            "Debug REPL Console\n"
            "==================\n"
            "Enter Python expressions to evaluate in the current debug context.\n"
            "Variables are accessible by name. Use Up/Down for history.\n\n"
        )

        input_layout = QHBoxLayout()
        self._repl_prompt = QLabel(">>>")
        self._repl_prompt.setFont(QFont(TOKENS_V2.typography.family, TOKENS_V2.typography.body))
        self._repl_prompt.setStyleSheet(f"color: {THEME_V2.primary};")

        self._repl_input = QLineEdit()
        self._repl_input.setFont(QFont(TOKENS_V2.typography.family, TOKENS_V2.typography.body))
        self._repl_input.setPlaceholderText("Enter expression...")
        self._repl_input.returnPressed.connect(self._evaluate_repl_expression)
        self._repl_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME_V2.bg_canvas};
                color: {THEME_V2.text_primary};
                border: 1px solid {THEME_V2.border};
                padding: {TOKENS_V2.spacing.xs}px;
            }}
        """)

        btn_clear_repl = QPushButton("Clear")
        btn_clear_repl.setMinimumWidth(TOKENS_V2.sizes.button_lg + TOKENS_V2.sizes.button_md)
        btn_clear_repl.clicked.connect(self._clear_repl)

        input_layout.addWidget(self._repl_prompt)
        input_layout.addWidget(self._repl_input)
        input_layout.addWidget(btn_clear_repl)

        layout.addWidget(self._repl_output)
        layout.addLayout(input_layout)

        return widget

    def _create_snapshots_tab(self) -> QWidget:
        """Create the execution snapshots tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        margin_compact(layout)

        toolbar = QHBoxLayout()

        btn_create = QPushButton("Create Snapshot")
        btn_create.setMinimumWidth(
            TOKENS_V2.sizes.dialog_sm_width + TOKENS_V2.sizes.button_min_width
        )
        btn_create.clicked.connect(self._create_snapshot)

        btn_restore = QPushButton("Restore")
        btn_restore.setMinimumWidth(TOKENS_V2.sizes.input_md + TOKENS_V2.sizes.button_md)
        btn_restore.clicked.connect(self._restore_selected_snapshot)

        btn_delete = QPushButton("Delete")
        btn_delete.setMinimumWidth(TOKENS_V2.sizes.button_lg + TOKENS_V2.sizes.button_md)
        btn_delete.clicked.connect(self._delete_selected_snapshot)

        toolbar.addWidget(btn_create)
        toolbar.addStretch()
        toolbar.addWidget(btn_restore)
        toolbar.addWidget(btn_delete)

        layout.addLayout(toolbar)

        self._snapshot_table = QTableWidget()
        self._snapshot_table.setColumnCount(4)
        self._snapshot_table.setHorizontalHeaderLabels(["ID", "Node", "Time", "Description"])
        self._snapshot_table.setAlternatingRowColors(True)
        self._snapshot_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._snapshot_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        header = self._snapshot_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self._snapshot_table)

        return widget

    def _setup_connections(self) -> None:
        """Set up internal signal connections."""
        pass

    def _apply_styles(self) -> None:
        """Apply v2 dark theme styling using THEME_V2/TOKENS_V2 system."""
        # Use standardized v2 styles
        base_button_styles = get_button_styles_v2()
        base_tab_styles = get_tab_widget_styles_v2()

        # Custom dock widget and frame styles
        custom_styles = f"""
            /* ==================== DOCK WIDGET ==================== */
            QDockWidget {{
                background-color: {THEME_V2.bg_surface};
                color: {THEME_V2.text_primary};
            }}
            QDockWidget::title {{
                background-color: {THEME_V2.bg_elevated};
                color: {THEME_V2.text_secondary};
                padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.md}px;
                font-weight: {TOKENS_V2.typography.weight_semibold};
                font-size: {TOKENS_V2.typography.caption}px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-bottom: 1px solid {THEME_V2.border};
            }}
            /* ==================== FRAME ==================== */
            QFrame {{
                background-color: {THEME_V2.bg_surface};
                border: 1px solid {THEME_V2.border};
            }}
            /* ==================== BUTTONS (custom overrides) ==================== */
            QPushButton {{
                background-color: {THEME_V2.bg_component};
                color: {THEME_V2.text_primary};
                border: 1px solid {THEME_V2.border};
                padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.md}px;
                border-radius: {TOKENS_V2.radius.sm}px;
                font-size: {TOKENS_V2.typography.body_sm}px;
            }}
            QPushButton:hover {{
                background-color: {THEME_V2.bg_hover};
                border-color: {THEME_V2.border_light};
            }}
            QPushButton:pressed {{
                background-color: {THEME_V2.bg_selected};
            }}
            QPushButton:disabled {{
                background-color: {THEME_V2.bg_component};
                color: {THEME_V2.text_disabled};
                border-color: {THEME_V2.border};
            }}
            {get_panel_table_stylesheet()}
            {get_panel_toolbar_stylesheet()}
        """
        self.setStyleSheet(base_tab_styles + base_button_styles + custom_styles)

    def _set_stepping_enabled(self, enabled: bool) -> None:
        """Enable or disable step controls."""
        self._btn_step_over.setEnabled(enabled)
        self._btn_step_into.setEnabled(enabled)
        self._btn_step_out.setEnabled(enabled)
        self._btn_continue.setEnabled(enabled)

    def add_log(
        self,
        level: str,
        message: str,
        node_id: str | None = None,
        node_name: str | None = None,
    ) -> None:
        """
        Add a log entry.

        Args:
            level: Log level (Info, Warning, Error, Success)
            message: Log message
            node_id: Optional node ID
            node_name: Optional node name
        """
        if self._current_filter != "All" and self._current_filter != level:
            return

        if self._log_table.rowCount() >= self._max_log_entries:
            self._log_table.removeRow(0)

        row = self._log_table.rowCount()
        self._log_table.insertRow(row)

        time_item = QTableWidgetItem(datetime.now().strftime("%H:%M:%S.%f")[:-3])
        self._log_table.setItem(row, self.COL_TIME, time_item)

        level_item = QTableWidgetItem(level)
        color_map = {
            "Error": THEME_V2.error,
            "Warning": THEME_V2.warning,
            "Success": THEME_V2.success,
            "Info": THEME_V2.info,
        }
        level_item.setForeground(QBrush(QColor(color_map.get(level, THEME_V2.text_muted))))
        self._log_table.setItem(row, self.COL_LEVEL, level_item)

        node_text = node_name if node_name else (node_id[:12] if node_id else "-")
        node_item = QTableWidgetItem(node_text)
        if node_id:
            node_item.setData(Qt.ItemDataRole.UserRole, node_id)
        self._log_table.setItem(row, self.COL_NODE, node_item)

        message_item = QTableWidgetItem(message)
        self._log_table.setItem(row, self.COL_MESSAGE, message_item)

        if self._auto_scroll:
            self._log_table.scrollToBottom()

    def update_variables(self, variables: dict[str, Any]) -> None:
        """
        Update the variable inspector with new values.

        Args:
            variables: Dictionary of variable name -> value
        """
        self._var_tree.clear()

        for name, value in sorted(variables.items()):
            self._add_variable_item(name, value, self._var_tree.invisibleRootItem())

        self._var_tree.expandToDepth(1)

    def _add_variable_item(
        self,
        name: str,
        value: Any,
        parent: QTreeWidgetItem,
    ) -> None:
        """Add a variable item to the tree."""
        item = QTreeWidgetItem(parent)
        item.setText(0, str(name))

        type_name = type(value).__name__

        if isinstance(value, dict):
            item.setText(1, f"dict ({len(value)} items)")
            item.setText(2, "dict")
            for k, v in value.items():
                self._add_variable_item(str(k), v, item)

        elif isinstance(value, list | tuple):
            type_str = "list" if isinstance(value, list) else "tuple"
            item.setText(1, f"{type_str} ({len(value)} items)")
            item.setText(2, type_str)
            for i, v in enumerate(value[:100]):
                self._add_variable_item(f"[{i}]", v, item)
            if len(value) > 100:
                more_item = QTreeWidgetItem(item)
                more_item.setText(0, f"... ({len(value) - 100} more)")

        else:
            value_str = repr(value)
            if len(value_str) > 200:
                value_str = value_str[:200] + "..."
            item.setText(1, value_str)
            item.setText(2, type_name)

    def update_call_stack(self, frames: list["CallStackFrame"]) -> None:
        """
        Update the call stack display.

        Args:
            frames: List of call stack frames
        """
        self._call_stack_table.setRowCount(0)

        for i, frame in enumerate(reversed(frames)):
            row = self._call_stack_table.rowCount()
            self._call_stack_table.insertRow(row)

            depth_item = QTableWidgetItem(str(len(frames) - i - 1))
            self._call_stack_table.setItem(row, 0, depth_item)

            name_item = QTableWidgetItem(frame.node_name)
            name_item.setData(Qt.ItemDataRole.UserRole, frame.node_id)
            self._call_stack_table.setItem(row, 1, name_item)

            type_item = QTableWidgetItem(frame.node_type)
            self._call_stack_table.setItem(row, 2, type_item)

            time_item = QTableWidgetItem(frame.entry_time.strftime("%H:%M:%S"))
            self._call_stack_table.setItem(row, 3, time_item)

    def update_watches(self, watches: list["WatchExpression"]) -> None:
        """
        Update the watch expressions display.

        Args:
            watches: List of watch expressions
        """
        self._watch_table.setRowCount(0)

        for watch in watches:
            row = self._watch_table.rowCount()
            self._watch_table.insertRow(row)

            expr_item = QTableWidgetItem(watch.expression)
            self._watch_table.setItem(row, 0, expr_item)

            if watch.last_error:
                value_item = QTableWidgetItem("-")
                error_item = QTableWidgetItem(watch.last_error)
                error_item.setForeground(QBrush(QColor(THEME_V2.error)))
            else:
                value_str = repr(watch.last_value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                value_item = QTableWidgetItem(value_str)
                error_item = QTableWidgetItem("")

            self._watch_table.setItem(row, 1, value_item)
            self._watch_table.setItem(row, 2, error_item)

    def add_breakpoint_to_list(
        self,
        node_id: str,
        node_name: str,
        bp_type: str = "Regular",
        condition: str = "",
        hit_count: int = 0,
        enabled: bool = True,
    ) -> None:
        """
        Add a breakpoint to the list display.

        Args:
            node_id: Node ID
            node_name: Node display name
            bp_type: Breakpoint type
            condition: Condition expression
            hit_count: Current hit count
            enabled: Whether enabled
        """
        row = self._bp_table.rowCount()
        self._bp_table.insertRow(row)

        enabled_item = QTableWidgetItem()
        enabled_item.setCheckState(Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked)
        enabled_item.setData(Qt.ItemDataRole.UserRole, node_id)
        self._bp_table.setItem(row, 0, enabled_item)

        name_item = QTableWidgetItem(node_name)
        self._bp_table.setItem(row, 1, name_item)

        type_item = QTableWidgetItem(bp_type)
        self._bp_table.setItem(row, 2, type_item)

        cond_item = QTableWidgetItem(condition)
        self._bp_table.setItem(row, 3, cond_item)

        hit_item = QTableWidgetItem(str(hit_count))
        self._bp_table.setItem(row, 4, hit_item)

    def remove_breakpoint_from_list(self, node_id: str) -> None:
        """Remove a breakpoint from the list display."""
        for row in range(self._bp_table.rowCount()):
            item = self._bp_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == node_id:
                self._bp_table.removeRow(row)
                break

    def clear_logs(self) -> None:
        """Clear all log entries."""
        self._log_table.setRowCount(0)
        logger.debug("Logs cleared")

    def clear_breakpoints(self) -> None:
        """Clear all breakpoints from display."""
        self._bp_table.setRowCount(0)
        logger.debug("Breakpoints display cleared")

    def _on_filter_changed(self, filter_text: str) -> None:
        """Handle log filter change."""
        self._current_filter = filter_text

    def _on_auto_scroll_toggled(self) -> None:
        """Handle auto-scroll toggle."""
        self._auto_scroll = self._auto_scroll_btn.isChecked()
        self._auto_scroll_btn.setText(f"Auto-scroll: {'ON' if self._auto_scroll else 'OFF'}")

    def _on_log_double_click(self, item: QTableWidgetItem) -> None:
        """Handle log entry double-click to navigate to node."""
        row = item.row()
        node_item = self._log_table.item(row, self.COL_NODE)
        if node_item:
            node_id = node_item.data(Qt.ItemDataRole.UserRole)
            if node_id:
                self.navigate_to_node.emit(node_id)

    def _on_bp_double_click(self, item: QTableWidgetItem) -> None:
        """Handle breakpoint double-click to navigate to node."""
        row = item.row()
        enabled_item = self._bp_table.item(row, 0)
        if enabled_item:
            node_id = enabled_item.data(Qt.ItemDataRole.UserRole)
            if node_id:
                self.navigate_to_node.emit(node_id)

    def _on_call_stack_double_click(self, item: QTableWidgetItem) -> None:
        """Handle call stack double-click to navigate to node."""
        row = item.row()
        name_item = self._call_stack_table.item(row, 1)
        if name_item:
            node_id = name_item.data(Qt.ItemDataRole.UserRole)
            if node_id:
                self.navigate_to_node.emit(node_id)

    def _on_clear_breakpoints(self) -> None:
        """Handle clear all breakpoints."""
        self.clear_breakpoints()
        self.clear_requested.emit()

    def _disable_all_breakpoints(self) -> None:
        """Disable all breakpoints."""
        for row in range(self._bp_table.rowCount()):
            item = self._bp_table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)
                node_id = item.data(Qt.ItemDataRole.UserRole)
                if node_id:
                    self.breakpoint_toggled.emit(node_id, False)

    def _enable_all_breakpoints(self) -> None:
        """Enable all breakpoints."""
        for row in range(self._bp_table.rowCount()):
            item = self._bp_table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)
                node_id = item.data(Qt.ItemDataRole.UserRole)
                if node_id:
                    self.breakpoint_toggled.emit(node_id, True)

    def _filter_variables(self, text: str) -> None:
        """Filter variables by search text."""
        search_text = text.lower()

        def set_item_visibility(item: QTreeWidgetItem) -> bool:
            name = item.text(0).lower()
            value = item.text(1).lower()

            matches = search_text in name or search_text in value

            for i in range(item.childCount()):
                child = item.child(i)
                if set_item_visibility(child):
                    matches = True

            item.setHidden(not matches and bool(search_text))
            return matches

        for i in range(self._var_tree.topLevelItemCount()):
            set_item_visibility(self._var_tree.topLevelItem(i))

    def _refresh_variables(self) -> None:
        """Request variable refresh from debug controller."""
        if self._debug_controller:
            if hasattr(self._debug_controller, "_current_context"):
                ctx = self._debug_controller._current_context
                if ctx and hasattr(ctx, "variables"):
                    self.update_variables(dict(ctx.variables))

    @Slot()
    def _expand_all_variables(self) -> None:
        """Expand all items in the variable tree."""
        self._var_tree.expandAll()

    @Slot()
    def _collapse_all_variables(self) -> None:
        """Collapse all items in the variable tree."""
        self._var_tree.collapseAll()

    def _show_variable_context_menu(self, pos) -> None:
        """Show context menu for variable tree."""
        item = self._var_tree.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)

        copy_name_action = QAction("Copy Name", self)
        copy_name_action.setData({"type": "copy_name", "text": item.text(0)})
        copy_name_action.triggered.connect(self._on_variable_context_action_triggered)
        menu.addAction(copy_name_action)

        copy_value_action = QAction("Copy Value", self)
        copy_value_action.setData({"type": "copy_value", "text": item.text(1)})
        copy_value_action.triggered.connect(self._on_variable_context_action_triggered)
        menu.addAction(copy_value_action)

        menu.addSeparator()

        add_watch_action = QAction("Add to Watch", self)
        add_watch_action.setData({"type": "add_watch", "text": item.text(0)})
        add_watch_action.triggered.connect(self._on_variable_context_action_triggered)
        menu.addAction(add_watch_action)

        menu.exec_(self._var_tree.viewport().mapToGlobal(pos))

    def _copy_to_clipboard(self, text: str) -> None:
        """Copy text to clipboard."""
        from PySide6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    @Slot()
    def _on_variable_context_action_triggered(self) -> None:
        """Handle variable context menu action."""
        action = self.sender()
        if action:
            data = action.data()
            if data and isinstance(data, dict):
                action_type = data.get("type")
                text = data.get("text", "")
                if action_type in ("copy_name", "copy_value"):
                    self._copy_to_clipboard(text)
                elif action_type == "add_watch":
                    self._add_watch_expression(text)

    def _show_breakpoint_context_menu(self, pos) -> None:
        """Show context menu for breakpoint table."""
        row = self._bp_table.rowAt(pos.y())
        if row < 0:
            return

        enabled_item = self._bp_table.item(row, 0)
        if not enabled_item:
            return

        node_id = enabled_item.data(Qt.ItemDataRole.UserRole)
        if not node_id:
            return

        menu = QMenu(self)

        edit_condition_action = QAction("Edit Condition...", self)
        edit_condition_action.setData({"node_id": node_id, "row": row})
        edit_condition_action.triggered.connect(self._on_edit_condition_action_triggered)
        menu.addAction(edit_condition_action)

        menu.addSeparator()

        remove_action = QAction("Remove Breakpoint", self)
        remove_action.setData(node_id)
        remove_action.triggered.connect(self._on_remove_breakpoint_action_triggered)
        menu.addAction(remove_action)

        menu.exec_(self._bp_table.viewport().mapToGlobal(pos))

    def _edit_breakpoint_condition(self, node_id: str, row: int) -> None:
        """Edit breakpoint condition."""
        current_condition = self._bp_table.item(row, 3).text()

        condition, ok = QInputDialog.getText(
            self,
            "Edit Breakpoint Condition",
            "Enter condition (Python expression):",
            text=current_condition,
        )

        if ok:
            self._bp_table.item(row, 3).setText(condition)
            self.breakpoint_condition_changed.emit(node_id, condition)

    def _remove_breakpoint(self, node_id: str) -> None:
        """Remove a breakpoint."""
        self.remove_breakpoint_from_list(node_id)
        self.breakpoint_toggled.emit(node_id, False)

    @Slot()
    def _on_edit_condition_action_triggered(self) -> None:
        """Handle edit condition action from context menu."""
        action = self.sender()
        if action:
            data = action.data()
            if data and isinstance(data, dict):
                node_id = data.get("node_id")
                row = data.get("row")
                if node_id is not None and row is not None:
                    self._edit_breakpoint_condition(node_id, row)

    @Slot()
    def _on_remove_breakpoint_action_triggered(self) -> None:
        """Handle remove breakpoint action from context menu."""
        action = self.sender()
        if action:
            node_id = action.data()
            if node_id:
                self._remove_breakpoint(node_id)

    def _add_watch_from_input(self) -> None:
        """Add watch expression from input field."""
        expression = self._watch_input.text().strip()
        if expression:
            self._add_watch_expression(expression)
            self._watch_input.clear()

    def _add_watch_expression(self, expression: str) -> None:
        """Add a watch expression."""
        self.watch_added.emit(expression)

        row = self._watch_table.rowCount()
        self._watch_table.insertRow(row)

        expr_item = QTableWidgetItem(expression)
        self._watch_table.setItem(row, 0, expr_item)
        self._watch_table.setItem(row, 1, QTableWidgetItem("(not evaluated)"))
        self._watch_table.setItem(row, 2, QTableWidgetItem(""))

    def _remove_selected_watch(self) -> None:
        """Remove selected watch expression."""
        row = self._watch_table.currentRow()
        if row >= 0:
            expr_item = self._watch_table.item(row, 0)
            if expr_item:
                self.watch_removed.emit(expr_item.text())
            self._watch_table.removeRow(row)

    def _evaluate_repl_expression(self) -> None:
        """Evaluate expression entered in REPL."""
        expression = self._repl_input.text().strip()
        if not expression:
            return

        self._repl_history.append(expression)
        self._repl_history_index = len(self._repl_history)

        self._repl_output.appendPlainText(f">>> {expression}")

        if self._debug_controller:
            result, error = self._debug_controller.evaluate_expression(expression)
            if error:
                self._repl_output.appendPlainText(f"Error: {error}")
            elif result is not None:
                self._repl_output.appendPlainText(repr(result))
            self.expression_evaluated.emit(expression, result)
        else:
            self._repl_output.appendPlainText("(No debug context available)")

        self._repl_input.clear()

    def _clear_repl(self) -> None:
        """Clear REPL output."""
        self._repl_output.clear()
        self._repl_output.setPlainText(
            "Debug REPL Console\n"
            "==================\n"
            "Enter Python expressions to evaluate in the current debug context.\n\n"
        )

    def _create_snapshot(self) -> None:
        """Create execution snapshot."""
        description, ok = QInputDialog.getText(
            self,
            "Create Snapshot",
            "Enter description (optional):",
        )

        if ok:
            self.snapshot_requested.emit()
            if self._debug_controller:
                snapshot = self._debug_controller.create_snapshot(description)
                self._add_snapshot_to_list(snapshot)

    def _add_snapshot_to_list(self, snapshot: "ExecutionSnapshot") -> None:
        """Add snapshot to the list display."""
        row = self._snapshot_table.rowCount()
        self._snapshot_table.insertRow(row)

        id_item = QTableWidgetItem(snapshot.snapshot_id)
        id_item.setData(Qt.ItemDataRole.UserRole, snapshot.snapshot_id)
        self._snapshot_table.setItem(row, 0, id_item)

        node_item = QTableWidgetItem(snapshot.node_id[:12] if snapshot.node_id else "-")
        self._snapshot_table.setItem(row, 1, node_item)

        time_item = QTableWidgetItem(snapshot.timestamp.strftime("%H:%M:%S"))
        self._snapshot_table.setItem(row, 2, time_item)

        desc_item = QTableWidgetItem(snapshot.description or "-")
        self._snapshot_table.setItem(row, 3, desc_item)

    def _restore_selected_snapshot(self) -> None:
        """Restore selected snapshot."""
        row = self._snapshot_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Restore", "Please select a snapshot to restore.")
            return

        id_item = self._snapshot_table.item(row, 0)
        if id_item:
            snapshot_id = id_item.data(Qt.ItemDataRole.UserRole)
            self.snapshot_restore_requested.emit(snapshot_id)

            if self._debug_controller:
                if self._debug_controller.restore_snapshot(snapshot_id):
                    self.add_log("Info", f"Snapshot {snapshot_id} restored")
                else:
                    self.add_log("Error", f"Failed to restore snapshot {snapshot_id}")

    def _delete_selected_snapshot(self) -> None:
        """Delete selected snapshot."""
        row = self._snapshot_table.currentRow()
        if row < 0:
            return

        id_item = self._snapshot_table.item(row, 0)
        if id_item:
            snapshot_id = id_item.data(Qt.ItemDataRole.UserRole)
            if self._debug_controller:
                self._debug_controller.delete_snapshot(snapshot_id)
            self._snapshot_table.removeRow(row)

    @Slot(dict)
    def _on_variables_updated(self, variables: dict) -> None:
        """Handle variables update from debug controller."""
        self.update_variables(variables)

    @Slot(list)
    def _on_call_stack_updated(self, frames: list) -> None:
        """Handle call stack update from debug controller."""
        self.update_call_stack(frames)

    @Slot(list)
    def _on_watch_updated(self, watches: list) -> None:
        """Handle watch update from debug controller."""
        self.update_watches(watches)

    @Slot(str)
    def _on_breakpoint_added(self, node_id: str) -> None:
        """Handle breakpoint added from debug controller."""
        if self._debug_controller:
            bp = self._debug_controller.get_breakpoint(node_id)
            if bp:
                self.add_breakpoint_to_list(
                    node_id=bp.node_id,
                    node_name=bp.node_id[:12],
                    bp_type=bp.breakpoint_type.name,
                    condition=bp.condition or "",
                    hit_count=bp.hit_count,
                    enabled=bp.enabled,
                )

    @Slot(str)
    def _on_breakpoint_removed(self, node_id: str) -> None:
        """Handle breakpoint removed from debug controller."""
        self.remove_breakpoint_from_list(node_id)

    @Slot(str)
    def _on_breakpoint_hit_signal(self, node_id: str) -> None:
        """Handle breakpoint hit signal."""
        self.add_log("Warning", "Breakpoint hit", node_id)
        self._tabs.setCurrentIndex(0)
        self._lbl_status.setText(f"Paused at breakpoint: {node_id[:12]}")
        self._lbl_status.setStyleSheet(f"color: {THEME_V2.warning}; font-weight: bold;")
        self._set_stepping_enabled(True)

    @Slot(str)
    def _on_step_completed(self, node_id: str) -> None:
        """Handle step completed signal."""
        self._lbl_status.setText(f"Paused after step: {node_id[:12]}")
        self._lbl_status.setStyleSheet(f"color: {THEME_V2.info}; font-weight: bold;")

    @Slot(str)
    def _on_snapshot_created(self, snapshot_id: str) -> None:
        """Handle snapshot created signal."""
        self.add_log("Info", f"Snapshot created: {snapshot_id}")

    @Slot()
    def _on_execution_paused(self) -> None:
        """Handle execution paused signal."""
        self._set_stepping_enabled(True)
        self._lbl_status.setText("Paused")
        self._lbl_status.setStyleSheet(f"color: {THEME_V2.warning}; font-weight: bold;")

    @Slot()
    def _on_execution_resumed(self) -> None:
        """Handle execution resumed signal."""
        self._lbl_status.setText("Running...")
        self._lbl_status.setStyleSheet(f"color: {THEME_V2.success};")

    def _setup_lazy_subscriptions(self) -> None:
        """Set up lazy EventBus subscriptions."""
        if not HAS_EVENT_BUS:
            return

        self._lazy_subscriptions = LazySubscriptionGroup(
            self,
            [
                (EventType.NODE_EXECUTION_STARTED, self._on_node_execution_started),
                (EventType.NODE_EXECUTION_COMPLETED, self._on_node_execution_completed),
                (EventType.NODE_EXECUTION_FAILED, self._on_node_execution_failed),
                (EventType.BREAKPOINT_HIT, self._on_breakpoint_hit_event),
            ],
        )

    def _on_node_execution_started(self, event: "Event") -> None:
        """Handle node execution started event."""
        data = event.data if hasattr(event, "data") else event
        node_id = data.get("node_id", "") if isinstance(data, dict) else ""
        node_name = data.get("node_name", "") if isinstance(data, dict) else ""
        self.add_log("Info", f"Executing: {node_name}", node_id, node_name)

    def _on_node_execution_completed(self, event: "Event") -> None:
        """Handle node execution completed event."""
        data = event.data if hasattr(event, "data") else event
        node_id = data.get("node_id", "") if isinstance(data, dict) else ""
        node_name = data.get("node_name", "") if isinstance(data, dict) else ""
        duration = data.get("duration_ms", 0) if isinstance(data, dict) else 0
        self.add_log("Success", f"Completed: {node_name} ({duration}ms)", node_id, node_name)

    def _on_node_execution_failed(self, event: "Event") -> None:
        """Handle node execution failed event."""
        data = event.data if hasattr(event, "data") else event
        node_id = data.get("node_id", "") if isinstance(data, dict) else ""
        node_name = data.get("node_name", "") if isinstance(data, dict) else ""
        error = data.get("error", "Unknown") if isinstance(data, dict) else "Unknown"
        self.add_log("Error", f"Failed: {node_name} - {error}", node_id, node_name)

    def _on_breakpoint_hit_event(self, event: "Event") -> None:
        """Handle breakpoint hit event from EventBus."""
        data = event.data if hasattr(event, "data") else event
        node_id = data.get("node_id", "") if isinstance(data, dict) else ""
        node_name = data.get("node_name", "") if isinstance(data, dict) else ""
        self.add_log("Warning", f"Breakpoint: {node_name}", node_id, node_name)
        self._tabs.setCurrentIndex(0)
