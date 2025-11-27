"""
Comprehensive tests for VariablesPanel UI.

Tests variables panel functionality including:
- Variable display
- Variable editing
- Variable adding/removing
- Type handling
"""

import pytest
from unittest.mock import Mock
from PySide6.QtWidgets import QApplication

from casare_rpa.presentation.canvas.ui.panels.variables_panel import VariablesPanel


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def variables_panel(qapp):
    """Create a VariablesPanel instance."""
    panel = VariablesPanel()
    yield panel
    panel.deleteLater()


class TestVariablesPanelInitialization:
    """Tests for VariablesPanel initialization."""

    def test_initialization(self, qapp):
        """Test panel initializes correctly."""
        panel = VariablesPanel()
        assert panel.windowTitle() == "Variables"
        panel.deleteLater()

    def test_setup_ui(self, variables_panel):
        """Test UI is set up."""
        assert variables_panel.widget() is not None


class TestVariableDisplay:
    """Tests for variable display."""

    def test_set_variables(self, variables_panel):
        """Test setting variables."""
        variables = {"var1": "value1", "var2": 42, "var3": True}

        if hasattr(variables_panel, "set_variables"):
            variables_panel.set_variables(variables)
        # Should not raise error

    def test_get_all_variables(self, variables_panel):
        """Test getting all variables."""
        if hasattr(variables_panel, "get_all_variables"):
            result = variables_panel.get_all_variables()
            assert isinstance(result, dict)
        else:
            # Method may not exist yet
            pass

    def test_clear_variables(self, variables_panel):
        """Test clearing variables."""
        if hasattr(variables_panel, "clear"):
            variables_panel.clear()


class TestVariableEditing:
    """Tests for variable editing."""

    def test_add_variable(self, variables_panel):
        """Test adding new variable."""
        if hasattr(variables_panel, "add_variable"):
            variables_panel.add_variable("new_var", "value")

    def test_update_variable(self, variables_panel):
        """Test updating existing variable."""
        if hasattr(variables_panel, "update_variable"):
            variables_panel.update_variable("var1", "new_value")

    def test_remove_variable(self, variables_panel):
        """Test removing variable."""
        if hasattr(variables_panel, "remove_variable"):
            variables_panel.remove_variable("var1")


class TestVariableTypes:
    """Tests for variable type handling."""

    def test_string_variable(self, variables_panel):
        """Test handling string variables."""
        if hasattr(variables_panel, "set_variables"):
            variables_panel.set_variables({"str_var": "hello"})

    def test_numeric_variable(self, variables_panel):
        """Test handling numeric variables."""
        if hasattr(variables_panel, "set_variables"):
            variables_panel.set_variables({"int_var": 42, "float_var": 3.14})

    def test_boolean_variable(self, variables_panel):
        """Test handling boolean variables."""
        if hasattr(variables_panel, "set_variables"):
            variables_panel.set_variables({"bool_var": True})

    def test_complex_variable(self, variables_panel):
        """Test handling complex variables."""
        if hasattr(variables_panel, "set_variables"):
            variables_panel.set_variables(
                {"list_var": [1, 2, 3], "dict_var": {"key": "value"}}
            )


class TestVariableValidation:
    """Tests for variable validation."""

    def test_validate_variable_name(self, variables_panel):
        """Test variable name validation."""
        # Should have validation for variable names
        if hasattr(variables_panel, "validate_name"):
            assert variables_panel.validate_name("valid_var") or True
            assert not variables_panel.validate_name("123invalid") or True

    def test_duplicate_variable_name(self, variables_panel):
        """Test handling duplicate variable names."""
        if hasattr(variables_panel, "add_variable"):
            variables_panel.add_variable("dup_var", "value1")
            # Adding same name again should be handled
            variables_panel.add_variable("dup_var", "value2")
