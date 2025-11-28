"""
Variables Tab - QWidget wrapper for VariablesPanel.

Provides tab-compatible interface for bottom panel integration.
"""

from typing import Optional, Dict, Any

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal

from .variables_panel import VariablesPanel


class VariablesTab(QWidget):
    """
    Tab wrapper for VariablesPanel.

    Signals:
        variables_changed: Emitted when variables dict changes
    """

    variables_changed = Signal(dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the variables tab."""
        super().__init__(parent)

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create embedded panel (as widget, not dock)
        self._panel = VariablesPanel(self)
        # Extract the content widget from the dock
        content = self._panel.widget()
        if content:
            layout.addWidget(content)

        # Connect signals
        self._panel.variables_changed.connect(self.variables_changed.emit)

    def get_variables(self) -> Dict[str, Dict[str, Any]]:
        """Get current variables."""
        return self._panel._variables

    def set_variables(self, variables: Dict[str, Dict[str, Any]]) -> None:
        """Set variables."""
        self._panel._variables = variables
        self._panel._populate_table()

    def clear(self) -> None:
        """Clear all variables."""
        self._panel._variables.clear()
        self._panel._populate_table()
