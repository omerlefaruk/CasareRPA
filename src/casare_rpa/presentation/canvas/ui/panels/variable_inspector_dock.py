"""
Variable Inspector Dock - Runtime variable value viewer.

Shows real-time variable values during workflow execution.
"""

from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PySide6.QtCore import Qt
from loguru import logger


class VariableInspectorDock(QDockWidget):
    """
    Dock widget for inspecting runtime variable values.

    Shows variable values during workflow execution, separate from
    the design-time Variables panel.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the variable inspector dock."""
        super().__init__("Variable Inspector", parent)
        self.setObjectName("VariableInspectorDock")

        self._setup_ui()
        logger.debug("VariableInspectorDock initialized")

    def _setup_ui(self) -> None:
        """Setup the UI components."""
        container = QWidget()
        layout = QVBoxLayout(container)

        # Create table
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Name", "Type", "Value"])

        # Configure table
        header = self._table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self._table)
        self.setWidget(container)

    def update_variables(self, variables: Dict[str, Any]) -> None:
        """
        Update displayed variables.

        Args:
            variables: Dictionary of variable name -> value
        """
        self._table.setRowCount(len(variables))

        for row, (name, value) in enumerate(variables.items()):
            # Name
            self._table.setItem(row, 0, QTableWidgetItem(name))

            # Type
            type_name = type(value).__name__
            self._table.setItem(row, 1, QTableWidgetItem(type_name))

            # Value
            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:100] + "..."
            self._table.setItem(row, 2, QTableWidgetItem(value_str))

    def clear(self) -> None:
        """Clear all displayed variables."""
        self._table.setRowCount(0)
