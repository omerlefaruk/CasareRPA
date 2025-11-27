"""
Variable Inspector Dock for CasareRPA.

A dockable panel that displays real-time variable values during workflow execution.
Can be docked side-by-side with the bottom panel.
"""

from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
    QHBoxLayout,
    QPushButton,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QBrush
from loguru import logger


class VariableInspectorDock(QDockWidget):
    """
    Dockable panel showing real-time variable values during execution.

    Features:
    - Live variable value updates during runtime
    - Auto-refresh with configurable interval
    - Color-coded value changes
    - Can be docked side-by-side with bottom panel

    Signals:
        refresh_requested: Emitted when manual refresh is requested
    """

    refresh_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the Variable Inspector dock.

        Args:
            parent: Optional parent widget
        """
        super().__init__("Variable Inspector", parent)
        self.setObjectName("VariableInspectorDock")

        self._runtime_values: Dict[str, Any] = {}
        self._previous_values: Dict[str, Any] = {}
        self._is_running = False

        # Auto-refresh timer
        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.timeout.connect(self._on_auto_refresh)
        self._auto_refresh_interval = 500  # ms

        self._setup_dock()
        self._setup_ui()
        self._apply_styles()

        logger.debug("VariableInspectorDock initialized")

    def _setup_dock(self) -> None:
        """Configure dock widget properties."""
        # Allow docking at bottom and right
        self.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
        )

        # Set features
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )

        # Set minimum size
        self.setMinimumWidth(250)
        self.setMinimumHeight(150)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Header with status and controls
        header_layout = QHBoxLayout()

        self._status_label = QLabel("Idle")
        self._status_label.setStyleSheet("color: #888888; font-weight: bold;")
        header_layout.addWidget(self._status_label)

        header_layout.addStretch()

        # Auto-refresh toggle
        self._btn_auto_refresh = QPushButton("Auto")
        self._btn_auto_refresh.setCheckable(True)
        self._btn_auto_refresh.setChecked(True)
        self._btn_auto_refresh.setToolTip("Toggle auto-refresh")
        self._btn_auto_refresh.clicked.connect(self._on_toggle_auto_refresh)
        header_layout.addWidget(self._btn_auto_refresh)

        # Manual refresh button
        self._btn_refresh = QPushButton("Refresh")
        self._btn_refresh.setToolTip("Manually refresh variable values")
        self._btn_refresh.clicked.connect(self._on_manual_refresh)
        header_layout.addWidget(self._btn_refresh)

        # Clear button
        self._btn_clear = QPushButton("Clear")
        self._btn_clear.setToolTip("Clear all values")
        self._btn_clear.clicked.connect(self.clear)
        header_layout.addWidget(self._btn_clear)

        layout.addLayout(header_layout)

        # Variable table
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Variable", "Type", "Value"])

        # Set column resize modes
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        # Set column widths
        self._table.setColumnWidth(0, 120)
        self._table.setColumnWidth(1, 70)

        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)

        layout.addWidget(self._table)

        # Variable count label
        self._count_label = QLabel("Variables: 0")
        layout.addWidget(self._count_label)

        self.setWidget(container)

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        from ..theme import THEME

        self.setStyleSheet(f"""
            QDockWidget {{
                background-color: {THEME.bg_panel};
                color: {THEME.text_secondary};
            }}
            QDockWidget::title {{
                background-color: {THEME.dock_title_bg};
                padding: 6px;
                text-align: left;
            }}
            QTableWidget {{
                background-color: {THEME.bg_panel};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border_dark};
                gridline-color: {THEME.border_dark};
            }}
            QTableWidget::item {{
                padding: 4px;
            }}
            QTableWidget::item:selected {{
                background-color: {THEME.bg_selected};
            }}
            QTableWidget::item:alternate {{
                background-color: {THEME.bg_dark};
            }}
            QHeaderView::section {{
                background-color: {THEME.bg_header};
                color: {THEME.text_secondary};
                padding: 6px;
                border: none;
                border-right: 1px solid {THEME.border_dark};
            }}
            QPushButton {{
                background-color: {THEME.bg_light};
                color: {THEME.text_secondary};
                border: 1px solid {THEME.border};
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {THEME.bg_hover};
            }}
            QPushButton:pressed {{
                background-color: {THEME.bg_medium};
            }}
            QPushButton:checked {{
                background-color: {THEME.accent_primary};
                border-color: {THEME.accent_secondary};
            }}
            QLabel {{
                color: {THEME.text_secondary};
            }}
        """)

    def _on_toggle_auto_refresh(self, checked: bool) -> None:
        """Handle auto-refresh toggle."""
        if checked and self._is_running:
            self._auto_refresh_timer.start(self._auto_refresh_interval)
        else:
            self._auto_refresh_timer.stop()

    def _on_auto_refresh(self) -> None:
        """Handle auto-refresh timer tick."""
        self.refresh_requested.emit()

    def _on_manual_refresh(self) -> None:
        """Handle manual refresh button click."""
        self.refresh_requested.emit()

    def _format_value(self, value: Any) -> str:
        """Format a value for display."""
        if value is None:
            return "None"
        elif isinstance(value, str):
            # Truncate long strings
            if len(value) > 100:
                return f'"{value[:100]}..."'
            return f'"{value}"'
        elif isinstance(value, bool):
            return str(value)
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, (list, tuple)):
            if len(value) > 5:
                return f"[{len(value)} items]"
            return str(value)
        elif isinstance(value, dict):
            if len(value) > 5:
                return f"{{{len(value)} keys}}"
            return str(value)
        else:
            return str(value)

    def _get_type_name(self, value: Any) -> str:
        """Get a friendly type name for a value."""
        if value is None:
            return "None"
        elif isinstance(value, str):
            return "String"
        elif isinstance(value, bool):
            return "Boolean"
        elif isinstance(value, int):
            return "Integer"
        elif isinstance(value, float):
            return "Float"
        elif isinstance(value, list):
            return "List"
        elif isinstance(value, dict):
            return "Dict"
        else:
            return type(value).__name__

    # ==================== Public API ====================

    def update_values(self, values: Dict[str, Any]) -> None:
        """
        Update displayed variable values.

        Args:
            values: Dictionary of {variable_name: current_value}
        """
        self._previous_values = self._runtime_values.copy()
        self._runtime_values = values.copy()

        # Clear and rebuild table
        self._table.setRowCount(0)

        for name, value in sorted(values.items()):
            row = self._table.rowCount()
            self._table.insertRow(row)

            # Variable name
            name_item = QTableWidgetItem(name)
            name_item.setForeground(QBrush(QColor("#9CDCFE")))  # Light blue
            self._table.setItem(row, 0, name_item)

            # Type
            type_name = self._get_type_name(value)
            type_item = QTableWidgetItem(type_name)
            type_item.setForeground(QBrush(QColor("#4EC9B0")))  # Teal
            self._table.setItem(row, 1, type_item)

            # Value
            formatted_value = self._format_value(value)
            value_item = QTableWidgetItem(formatted_value)

            # Highlight changed values
            if name in self._previous_values and self._previous_values[name] != value:
                value_item.setBackground(QColor(50, 100, 50))  # Dark green
                value_item.setForeground(QBrush(QColor("#4CAF50")))  # Green
            else:
                value_item.setForeground(
                    QBrush(QColor("#CE9178"))
                )  # Orange/string color

            self._table.setItem(row, 2, value_item)

        self._count_label.setText(f"Variables: {len(values)}")

    def set_running(self, running: bool) -> None:
        """
        Set the running state.

        Args:
            running: True if workflow is executing
        """
        self._is_running = running

        if running:
            self._status_label.setText("Running")
            self._status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            if self._btn_auto_refresh.isChecked():
                self._auto_refresh_timer.start(self._auto_refresh_interval)
        else:
            self._status_label.setText("Idle")
            self._status_label.setStyleSheet("color: #888888; font-weight: bold;")
            self._auto_refresh_timer.stop()

    def clear(self) -> None:
        """Clear all displayed values."""
        self._runtime_values.clear()
        self._previous_values.clear()
        self._table.setRowCount(0)
        self._count_label.setText("Variables: 0")
        logger.debug("Variable inspector cleared")

    def get_values(self) -> Dict[str, Any]:
        """Get current runtime values."""
        return self._runtime_values.copy()
