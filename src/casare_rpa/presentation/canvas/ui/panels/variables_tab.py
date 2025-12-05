"""
Variables Tab - QWidget wrapper for VariablesPanel.

Provides tab-compatible interface for bottom panel integration.
"""

from typing import Optional, Dict, Any

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal

from casare_rpa.presentation.canvas.ui.panels.variables_panel import VariablesPanel
from casare_rpa.presentation.canvas.theme import THEME


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

        # Apply consistent background styling
        self._apply_styles()

    def _apply_styles(self) -> None:
        """Apply VSCode Dark+ theme styling."""
        self.setStyleSheet(f"""
            VariablesTab, QWidget, QStackedWidget, QFrame {{
                background-color: {THEME.bg_panel};
            }}
        """)

    def get_variables(self) -> Dict[str, Dict[str, Any]]:
        """Get current variables."""
        return self._panel.get_variables()

    def set_variables(self, variables: Dict[str, Dict[str, Any]]) -> None:
        """Set variables."""
        # Clear existing and add new ones
        self._panel.clear_variables()
        for name, var_data in variables.items():
            self._panel.add_variable(
                name=name,
                var_type=var_data.get("type", "String"),
                default_value=var_data.get("default", ""),
                scope=var_data.get("scope", "Workflow"),
            )

    def clear(self) -> None:
        """Clear all variables."""
        self._panel.clear_variables()

    def update_runtime_values(self, values: Dict[str, Any]) -> None:
        """
        Update variable values during runtime.

        Args:
            values: Dict of {variable_name: current_value}
        """
        for name, value in values.items():
            self._panel.update_variable_value(name, value)

    def set_runtime_mode(self, enabled: bool) -> None:
        """
        Switch between design mode and runtime mode.

        Args:
            enabled: True for runtime mode, False for design mode
        """
        self._panel.set_runtime_mode(enabled)
