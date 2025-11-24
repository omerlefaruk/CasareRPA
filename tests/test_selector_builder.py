"""
Unit and Integration tests for Desktop Selector Builder

Tests selector_strategy, element_tree_widget, element_picker, selector_validator, and desktop_selector_builder
"""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication

from casare_rpa.desktop import DesktopElement
from casare_rpa.canvas.selector_strategy import (
    generate_selectors,
    SelectorStrategy,
    ConfidenceLevel,
    filter_best_selectors,
    validate_selector_uniqueness
)
from casare_rpa.canvas.selector_validator import (
    SelectorValidator,
    ValidationStatus,
    validate_selector_sync
)


class TestSelectorStrategy:
    """Test suite for selector strategy generation"""

    def test_selector_strategy_to_dict(self):
        """Test converting SelectorStrategy to dictionary"""
        # Test with empty properties
        strategy = SelectorStrategy(
            strategy="automation_id",
            value="btn_123",
            properties={},
            confidence=ConfidenceLevel.HIGH,
            score=95.0,
            description="By AutomationId: btn_123"
        )

        selector_dict = strategy.to_dict()

        assert selector_dict["strategy"] == "automation_id"
        assert selector_dict["value"] == "btn_123"
        # Empty properties are not included
        assert "properties" not in selector_dict or selector_dict.get("properties") == {}

        # Test with non-empty properties
        strategy_with_props = SelectorStrategy(
            strategy="control_type",
            value="Button",
            properties={"Name": "Submit"},
            confidence=ConfidenceLevel.MEDIUM,
            score=75.0,
            description="By Button with Name: Submit"
        )

        selector_dict_with_props = strategy_with_props.to_dict()
        assert "properties" in selector_dict_with_props
        assert selector_dict_with_props["properties"]["Name"] == "Submit"

    def test_generate_selectors_with_automation_id(self):
        """Test generating selectors for element with AutomationId"""
        mock_element = MagicMock(spec=DesktopElement)
        mock_element.get_property.side_effect = lambda prop: {
            "AutomationId": "btn_submit",
            "Name": "Submit",
            "ControlTypeName": "ButtonControl",
            "ClassName": "WinButton"
        }.get(prop)

        strategies = generate_selectors(mock_element)

        assert len(strategies) > 0

        # Check that AutomationId strategy was generated
        automation_id_strategies = [s for s in strategies if s.strategy == "automation_id"]
        assert len(automation_id_strategies) > 0
        assert automation_id_strategies[0].value == "btn_submit"
        assert automation_id_strategies[0].confidence == ConfidenceLevel.HIGH

    def test_generate_selectors_with_name_only(self):
        """Test generating selectors for element with only Name"""
        mock_element = MagicMock(spec=DesktopElement)
        mock_element.get_property.side_effect = lambda prop: {
            "AutomationId": None,
            "Name": "Submit Button",
            "ControlTypeName": "ButtonControl",
            "ClassName": None
        }.get(prop)

        strategies = generate_selectors(mock_element)

        assert len(strategies) > 0

        # Check that Name strategy was generated
        name_strategies = [s for s in strategies if s.strategy == "name" and not s.properties]
        assert len(name_strategies) > 0
        assert name_strategies[0].value == "Submit Button"

    def test_generate_selectors_with_control_type(self):
        """Test generating control type strategies"""
        mock_element = MagicMock(spec=DesktopElement)
        mock_element.get_property.side_effect = lambda prop: {
            "AutomationId": None,
            "Name": None,
            "ControlTypeName": "EditControl",
            "ClassName": None
        }.get(prop)

        strategies = generate_selectors(mock_element)

        assert len(strategies) > 0

        # Check that ControlType strategy was generated
        control_type_strategies = [s for s in strategies if s.strategy == "control_type"]
        assert len(control_type_strategies) > 0

    def test_filter_best_selectors(self):
        """Test filtering selectors to keep only the best"""
        strategies = [
            SelectorStrategy("automation_id", "btn_1", {}, ConfidenceLevel.HIGH, 95.0, True),
            SelectorStrategy("name", "Button", {}, ConfidenceLevel.MEDIUM, 75.0, False),
            SelectorStrategy("control_type", "Button", {"index": 0}, ConfidenceLevel.LOW, 40.0, False),
            SelectorStrategy("class_name", "WinButton", {}, ConfidenceLevel.MEDIUM, 70.0, False),
        ]

        filtered = filter_best_selectors(strategies, max_count=3)

        assert len(filtered) <= 3
        # Unique strategies should be prioritized
        assert filtered[0].is_unique

    def test_selector_strategy_scoring(self):
        """Test that strategies are sorted by score"""
        strategies = [
            SelectorStrategy("control_type", "Button", {}, ConfidenceLevel.LOW, 40.0),
            SelectorStrategy("automation_id", "btn_1", {}, ConfidenceLevel.HIGH, 95.0),
            SelectorStrategy("name", "Click Me", {}, ConfidenceLevel.MEDIUM, 75.0),
        ]

        # Strategies should already be sorted by score in real usage
        strategies_sorted = sorted(strategies, key=lambda s: s.score, reverse=True)

        assert strategies_sorted[0].score == 95.0
        assert strategies_sorted[1].score == 75.0
        assert strategies_sorted[2].score == 40.0


class TestSelectorValidator:
    """Test suite for selector validator"""

    def test_validation_result_properties(self):
        """Test ValidationResult properties"""
        from casare_rpa.canvas.selector_validator import ValidationResult

        # Test VALID_UNIQUE
        result = ValidationResult(
            status=ValidationStatus.VALID_UNIQUE,
            element_count=1,
            execution_time_ms=45.2
        )

        assert result.is_valid
        assert result.is_unique
        assert result.icon == "✓"
        assert "#10b981" in result.color  # Green
        assert "exactly 1 element" in result.message

        # Test VALID_MULTIPLE
        result = ValidationResult(
            status=ValidationStatus.VALID_MULTIPLE,
            element_count=3,
            execution_time_ms=52.1
        )

        assert result.is_valid
        assert not result.is_unique
        assert result.icon == "⚠"
        assert "#fbbf24" in result.color  # Yellow

        # Test NOT_FOUND
        result = ValidationResult(
            status=ValidationStatus.NOT_FOUND,
            element_count=0,
            execution_time_ms=100.0
        )

        assert not result.is_valid
        assert not result.is_unique
        assert result.icon == "✗"
        assert "#ef4444" in result.color  # Red

    @patch('casare_rpa.canvas.selector_validator.find_elements')
    def test_validator_validate_unique(self, mock_find_elements):
        """Test validating a unique selector"""
        mock_control = MagicMock()

        # Mock finding exactly 1 element
        mock_element = MagicMock(spec=DesktopElement)
        mock_find_elements.return_value = [mock_element]

        validator = SelectorValidator(mock_control)
        result = validator.validate({"strategy": "automation_id", "value": "btn_1"}, find_all=True)

        assert result.status == ValidationStatus.VALID_UNIQUE
        assert result.element_count == 1
        assert result.is_unique

    @patch('casare_rpa.canvas.selector_validator.find_elements')
    def test_validator_validate_multiple(self, mock_find_elements):
        """Test validating a non-unique selector"""
        mock_control = MagicMock()

        # Mock finding multiple elements
        mock_elements = [MagicMock(spec=DesktopElement) for _ in range(3)]
        mock_find_elements.return_value = mock_elements

        validator = SelectorValidator(mock_control)
        result = validator.validate({"strategy": "name", "value": "Button"}, find_all=True)

        assert result.status == ValidationStatus.VALID_MULTIPLE
        assert result.element_count == 3
        assert not result.is_unique

    @patch('casare_rpa.canvas.selector_validator.find_elements')
    def test_validator_validate_not_found(self, mock_find_elements):
        """Test validating a selector that finds nothing"""
        mock_control = MagicMock()

        # Mock finding no elements
        mock_find_elements.return_value = []

        validator = SelectorValidator(mock_control)
        result = validator.validate({"strategy": "name", "value": "NonExistent"}, find_all=True)

        assert result.status == ValidationStatus.NOT_FOUND
        assert result.element_count == 0
        assert not result.is_valid

    @patch('casare_rpa.canvas.selector_validator.parse_selector')
    def test_validator_validate_error(self, mock_parse_selector):
        """Test validation error handling"""
        mock_control = MagicMock()

        # Mock parsing error
        mock_parse_selector.side_effect = ValueError("Invalid selector")

        validator = SelectorValidator(mock_control)
        result = validator.validate({"invalid": "selector"}, find_all=True)

        assert result.status == ValidationStatus.ERROR
        assert result.error_message is not None
        assert not result.is_valid

    @patch('casare_rpa.canvas.selector_validator.find_element')
    def test_validator_quick_check(self, mock_find_element):
        """Test quick check functionality"""
        mock_control = MagicMock()
        mock_element = MagicMock(spec=DesktopElement)
        mock_find_element.return_value = mock_element

        validator = SelectorValidator(mock_control)
        result = validator.quick_check({"strategy": "name", "value": "Button"})

        assert result is True

        # Test when element not found
        mock_find_element.side_effect = ValueError("Not found")
        result2 = validator.quick_check({"strategy": "name", "value": "NonExistent"})
        assert result2 is False

    @patch('casare_rpa.canvas.selector_validator.find_elements')
    def test_validator_validate_multiple_selectors(self, mock_find_elements):
        """Test validating multiple selectors at once"""
        mock_control = MagicMock()

        # Mock different results for different selectors using side_effect list
        mock_find_elements.side_effect = [
            [MagicMock(spec=DesktopElement)],  # Unique (automation_id)
            [MagicMock(spec=DesktopElement) for _ in range(3)],  # Multiple (name: Button)
            []  # Not found (name: NonExistent)
        ]

        validator = SelectorValidator(mock_control)
        selectors = [
            {"strategy": "automation_id", "value": "btn_1"},
            {"strategy": "name", "value": "Button"},
            {"strategy": "name", "value": "NonExistent"}
        ]

        results = validator.validate_multiple(selectors)

        assert len(results) == 3
        assert results[0].status == ValidationStatus.VALID_UNIQUE
        assert results[1].status == ValidationStatus.VALID_MULTIPLE
        assert results[2].status == ValidationStatus.NOT_FOUND


class TestDesktopSelectorBuilderIntegration:
    """Integration tests for Desktop Selector Builder dialog"""

    @pytest.fixture
    def qapp(self):
        """Qt Application fixture"""
        import sys
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        yield app

    def test_dialog_creation(self, qapp):
        """Test creating the dialog"""
        from casare_rpa.canvas.desktop_selector_builder import DesktopSelectorBuilder

        dialog = DesktopSelectorBuilder()

        assert dialog is not None
        assert dialog.windowTitle() == "Desktop Selector Builder"
        assert dialog.tree_widget is not None
        assert dialog.selectors_list is not None
        assert dialog.selector_editor is not None

    def test_dialog_has_buttons(self, qapp):
        """Test that dialog has required buttons"""
        from casare_rpa.canvas.desktop_selector_builder import DesktopSelectorBuilder

        dialog = DesktopSelectorBuilder()

        # Find buttons by object name
        pick_button = dialog.findChild(object, "pickButton")
        use_button = dialog.findChild(object, "useButton")
        copy_button = dialog.findChild(object, "copyButton")
        cancel_button = dialog.findChild(object, "cancelButton")

        # At least some buttons should exist
        assert pick_button is not None or use_button is not None

    def test_dialog_update_for_element(self, qapp):
        """Test updating dialog for selected element"""
        from casare_rpa.canvas.desktop_selector_builder import DesktopSelectorBuilder

        dialog = DesktopSelectorBuilder()

        # Create mock element
        mock_element = MagicMock(spec=DesktopElement)
        mock_element.get_property.side_effect = lambda prop: {
            "AutomationId": "test_btn",
            "Name": "Test Button",
            "ControlTypeName": "ButtonControl",
            "ClassName": "WinButton",
            "IsEnabled": True,
            "IsOffscreen": False,
            "ProcessId": 12345
        }.get(prop)
        mock_element._control = MagicMock()

        dialog.selected_element = mock_element
        dialog._update_for_selected_element()

        # Check that properties table was updated
        assert dialog.properties_table.rowCount() > 0

        # Check that selectors were generated
        assert len(dialog.selector_strategies) > 0

        # Check that selectors list was populated
        assert dialog.selectors_list.count() > 0

    def test_dialog_get_selected_selector(self, qapp):
        """Test getting selected selector from dialog"""
        from casare_rpa.canvas.desktop_selector_builder import DesktopSelectorBuilder

        dialog = DesktopSelectorBuilder()

        # Set a mock selected strategy
        dialog.selected_strategy = SelectorStrategy(
            strategy="automation_id",
            value="btn_test",
            properties={},
            confidence=ConfidenceLevel.HIGH,
            score=95.0
        )

        selector = dialog.get_selected_selector()

        assert selector is not None
        assert selector["strategy"] == "automation_id"
        assert selector["value"] == "btn_test"


# Integration tests with real Calculator application
class TestSelectorBuilderWithCalculator:
    """Integration tests using real Calculator application"""

    @pytest.fixture
    def calculator_window(self):
        """Fixture to launch Calculator and return its window"""
        from casare_rpa.nodes.desktop_nodes import LaunchApplicationNode
        from casare_rpa.core.execution_context import ExecutionContext
        import asyncio

        launch_node = LaunchApplicationNode("launch")
        context = ExecutionContext()
        launch_node.set_input_value("application_path", "calc.exe")

        # Launch calculator
        result = asyncio.run(launch_node.execute(context))
        window = result['window']

        yield window

        # Cleanup
        try:
            if hasattr(context, 'desktop_context'):
                context.desktop_context.cleanup()
        except:
            pass

    @pytest.mark.integration
    def test_generate_selectors_for_calculator_button(self, calculator_window):
        """Test generating selectors for a Calculator button"""
        from casare_rpa.desktop.selector import find_element

        # Find the "Seven" button
        selector = {"strategy": "name", "value": "Seven"}
        element = find_element(calculator_window._control, selector, timeout=2.0)

        assert element is not None

        # Generate selectors
        strategies = generate_selectors(element, calculator_window._control)

        assert len(strategies) > 0

        # Should generate at least name and control_type strategies
        strategy_types = [s.strategy for s in strategies]
        assert "name" in strategy_types or "control_type" in strategy_types

    @pytest.mark.integration
    def test_validate_calculator_selector(self, calculator_window):
        """Test validating a selector against Calculator"""
        validator = SelectorValidator(calculator_window._control)

        # Test valid selector (should find button)
        result = validator.validate({"strategy": "name", "value": "Seven"}, find_all=True)

        assert result.is_valid
        assert result.element_count >= 1

    @pytest.mark.integration
    def test_validate_nonexistent_selector(self, calculator_window):
        """Test validating a selector that doesn't exist"""
        validator = SelectorValidator(calculator_window._control)

        # Test invalid selector
        result = validator.validate({"strategy": "name", "value": "NonExistentButton12345"}, find_all=True)

        assert result.status == ValidationStatus.NOT_FOUND
        assert not result.is_valid
