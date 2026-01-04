"""
Variables Tab - QWidget wrapper for VariablesPanel.

Provides tab-compatible interface for bottom panel integration.
"""

from typing import Any

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget

# Epic 6.1: Migrated to v2 design system
from casare_rpa.presentation.canvas.theme import THEME_V2
from casare_rpa.presentation.canvas.ui.panels.panel_ux_helpers import VariablesTableWidget


class VariablesTab(QWidget):
    """
    Tab wrapper for UiPath-style variables table.

    Signals:
        variables_changed: Emitted when variables dict changes
    """

    variables_changed = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the variables tab."""
        super().__init__(parent)

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create table widget
        self._table = VariablesTableWidget(self)
        self._table.variable_created.connect(self._on_variable_created)
        self._table.variable_deleted.connect(self._on_variable_deleted)
        layout.addWidget(self._table)

        # Apply consistent background styling
        self._apply_styles()

    def _apply_styles(self) -> None:
        """Apply VSCode Dark+ theme styling."""
        self.setStyleSheet(f"""
            VariablesTab, QWidget {{
                background-color: {THEME_V2.bg_surface};
            }}
        """)

    @Slot(str, str, str, object)
    def _on_variable_created(self, name: str, var_type: str, scope: str, default: Any) -> None:
        """Handle variable creation from table."""
        # Add variable to internal storage
        self._table.add_variable(name, var_type, scope, default)
        # Emit change signal
        self.variables_changed.emit(self._table.get_variables())

    @Slot(str)
    def _on_variable_deleted(self, name: str) -> None:
        """Handle variable deletion from table."""
        self._table.remove_variable(name)
        # Emit change signal
        self.variables_changed.emit(self._table.get_variables())

    def get_variables(self) -> dict[str, dict[str, Any]]:
        """Get current variables."""
        return self._table.get_variables()

    def set_variables(self, variables: dict[str, dict[str, Any]]) -> None:
        """Set variables."""
        self._table.set_variables(variables)

    def clear(self) -> None:
        """Clear all variables."""
        self._table.set_variables({})

    def update_runtime_values(self, values: dict[str, Any]) -> None:
        """
        Update variable values during runtime.

        Args:
            values: Dict of {variable_name: current_value}
        """
        # TODO: Implement runtime value updates
        pass

    def set_runtime_mode(self, enabled: bool) -> None:
        """
        Switch between design mode and runtime mode.

        Args:
            enabled: True for runtime mode, False for design mode
        """
        # TODO: Implement runtime mode switching
        pass
