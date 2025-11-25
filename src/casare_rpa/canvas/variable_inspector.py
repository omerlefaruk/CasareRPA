"""
Variable Inspector panel for debugging.

Displays all variables in the execution context in real-time
during workflow execution.
"""

from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QHBoxLayout,
    QLabel,
)

from loguru import logger


class VariableInspectorPanel(QDockWidget):
    """
    Dock widget for inspecting workflow variables.
    
    Displays all variables in the ExecutionContext as a table
    with name and value columns. Updates in real-time during
    workflow execution.
    
    Signals:
        refresh_requested: Emitted when user requests manual refresh
    """
    
    refresh_requested = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the variable inspector panel.
        
        Args:
            parent: Optional parent widget
        """
        super().__init__("Variable Inspector", parent)
        
        self.setObjectName("VariableInspectorPanel")
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        
        # Create main widget
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header with refresh button
        header_layout = QHBoxLayout()
        
        self.label_count = QLabel("Variables: 0")
        header_layout.addWidget(self.label_count)
        
        header_layout.addStretch()
        
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setToolTip("Refresh variable list")
        self.btn_refresh.clicked.connect(self._on_refresh)
        header_layout.addWidget(self.btn_refresh)
        
        layout.addLayout(header_layout)
        
        # Table for variables
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Name", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        # Set column widths
        self.table.setColumnWidth(0, 150)

        layout.addWidget(self.table)

        # Empty state guidance
        self.empty_state_label = QLabel(
            "No variables yet.\n\n"
            "Variables will appear here when:\n"
            "- A workflow is running\n"
            "- SetVariable nodes create variables\n"
            "- Loop nodes create iterator variables\n\n"
            "Use SetVariableNode to create variables\n"
            "in your workflow."
        )
        self.empty_state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_state_label.setWordWrap(True)
        self.empty_state_label.setProperty("empty-state", True)
        self.empty_state_label.setStyleSheet("""
            QLabel {
                color: #7a7f85;
                font-size: 12px;
                padding: 20px;
            }
        """)
        layout.addWidget(self.empty_state_label)
        
        # Auto-refresh toggle
        refresh_layout = QHBoxLayout()
        
        self.btn_auto_refresh = QPushButton("Enable Auto-Refresh")
        self.btn_auto_refresh.setCheckable(True)
        self.btn_auto_refresh.setToolTip("Automatically refresh variables during execution")
        self.btn_auto_refresh.toggled.connect(self._on_auto_refresh_toggled)
        refresh_layout.addWidget(self.btn_auto_refresh)
        
        layout.addLayout(refresh_layout)
        
        self.setWidget(main_widget)
        
        # Auto-refresh timer
        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.timeout.connect(self._on_refresh)
        self._auto_refresh_interval = 500  # ms

        # Show empty state initially
        self.table.setVisible(False)
        self.empty_state_label.setVisible(True)

        logger.debug("Variable inspector panel initialized")
    
    def update_variables(self, variables: Dict[str, Any]) -> None:
        """
        Update the displayed variables.

        Args:
            variables: Dictionary of variable names to values
        """
        # Store current selection
        current_row = self.table.currentRow()
        current_var = None
        if current_row >= 0 and current_row < self.table.rowCount():
            current_var = self.table.item(current_row, 0).text()

        # Clear table
        self.table.setRowCount(0)

        # Update count
        self.label_count.setText(f"Variables: {len(variables)}")

        # Toggle empty state visibility
        has_variables = len(variables) > 0
        self.table.setVisible(has_variables)
        self.empty_state_label.setVisible(not has_variables)
        
        # Populate table
        for name, value in sorted(variables.items()):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Name column
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, name_item)
            
            # Value column
            value_str = self._format_value(value)
            value_item = QTableWidgetItem(value_str)
            value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, value_item)
            
            # Restore selection
            if name == current_var:
                self.table.setCurrentCell(row, 0)
        
        logger.debug(f"Updated variable inspector with {len(variables)} variables")
    
    def _format_value(self, value: Any) -> str:
        """
        Format a value for display.
        
        Args:
            value: The value to format
            
        Returns:
            Formatted string representation
        """
        if value is None:
            return "None"
        elif isinstance(value, str):
            # Limit string length
            max_len = 100
            if len(value) > max_len:
                return f'"{value[:max_len]}..."'
            return f'"{value}"'
        elif isinstance(value, (list, tuple)):
            # Show list/tuple summary
            if len(value) > 5:
                return f"{type(value).__name__}[{len(value)} items]"
            return str(value)
        elif isinstance(value, dict):
            # Show dict summary
            if len(value) > 5:
                return f"dict[{len(value)} items]"
            return str(value)
        else:
            return str(value)
    
    def _on_refresh(self) -> None:
        """Handle refresh button click."""
        logger.debug("Variable refresh requested")
        self.refresh_requested.emit()
    
    def _on_auto_refresh_toggled(self, checked: bool) -> None:
        """Handle auto-refresh toggle."""
        if checked:
            self.btn_auto_refresh.setText("Disable Auto-Refresh")
            self._auto_refresh_timer.start(self._auto_refresh_interval)
            logger.debug(f"Auto-refresh enabled ({self._auto_refresh_interval}ms)")
        else:
            self.btn_auto_refresh.setText("Enable Auto-Refresh")
            self._auto_refresh_timer.stop()
            logger.debug("Auto-refresh disabled")
    
    def clear(self) -> None:
        """Clear all variables from display."""
        self.table.setRowCount(0)
        self.label_count.setText("Variables: 0")
        # Show empty state
        self.table.setVisible(False)
        self.empty_state_label.setVisible(True)
        logger.debug("Variable inspector cleared")
    
    def set_auto_refresh_interval(self, interval_ms: int) -> None:
        """
        Set the auto-refresh interval.
        
        Args:
            interval_ms: Refresh interval in milliseconds
        """
        self._auto_refresh_interval = interval_ms
        if self._auto_refresh_timer.isActive():
            self._auto_refresh_timer.start(interval_ms)
        logger.debug(f"Auto-refresh interval set to {interval_ms}ms")
