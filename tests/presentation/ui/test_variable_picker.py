"""
Unit tests for Variable Picker components.

Tests VariableInfo, VariableProvider, VariablePickerPopup, VariableButton,
and VariableAwareLineEdit classes.
"""

import pytest
from unittest.mock import Mock, patch

from casare_rpa.presentation.canvas.ui.widgets.variable_picker import (
    VariableInfo,
    VariableProvider,
    TYPE_COLORS,
    TYPE_BADGES,
)


class TestVariableInfo:
    """Tests for VariableInfo dataclass."""

    def test_create_simple_variable(self):
        """Test creating a basic variable info."""
        var = VariableInfo(name="url", var_type="String", source="workflow")

        assert var.name == "url"
        assert var.var_type == "String"
        assert var.source == "workflow"
        assert var.value is None
        assert var.children == []
        assert var.path is None

    def test_display_name_without_path(self):
        """Test display_name returns name when no path is set."""
        var = VariableInfo(name="counter", var_type="Integer")

        assert var.display_name == "counter"

    def test_display_name_with_path(self):
        """Test display_name returns path when set."""
        var = VariableInfo(name="field", var_type="String", path="data.field")

        assert var.display_name == "data.field"

    def test_insertion_text(self):
        """Test insertion_text wraps in double braces."""
        var = VariableInfo(name="myVar")

        assert var.insertion_text == "{{myVar}}"

    def test_insertion_text_with_path(self):
        """Test insertion_text uses path for nested variables."""
        var = VariableInfo(name="email", path="user.email")

        assert var.insertion_text == "{{user.email}}"

    def test_type_color_for_known_type(self):
        """Test type_color returns correct color for known types."""
        var = VariableInfo(name="x", var_type="String")

        assert var.type_color == TYPE_COLORS["String"]
        assert var.type_color == "#4ec9b0"

    def test_type_color_for_unknown_type(self):
        """Test type_color returns Any color for unknown types."""
        var = VariableInfo(name="x", var_type="UnknownType")

        assert var.type_color == TYPE_COLORS["Any"]

    def test_type_badge_for_known_types(self):
        """Test type_badge returns correct badge for each known type."""
        test_cases = [
            ("String", "T"),
            ("Integer", "#"),
            ("Float", "."),
            ("Boolean", "?"),
            ("List", "[]"),
            ("Dict", "{}"),
            ("DataTable", "tbl"),
        ]

        for var_type, expected_badge in test_cases:
            var = VariableInfo(name="x", var_type=var_type)
            assert var.type_badge == expected_badge, f"Failed for {var_type}"

    def test_type_badge_for_unknown_type(self):
        """Test type_badge returns * for unknown types."""
        var = VariableInfo(name="x", var_type="Custom")

        assert var.type_badge == TYPE_BADGES["Any"]
        assert var.type_badge == "*"

    def test_get_preview_text_no_value(self):
        """Test preview text when no value is set."""
        var = VariableInfo(name="x")

        assert var.get_preview_text() == "(no value)"

    def test_get_preview_text_with_value(self):
        """Test preview text with a value."""
        var = VariableInfo(name="url", value="https://example.com")

        assert var.get_preview_text() == "https://example.com"

    def test_get_preview_text_truncates_long_value(self):
        """Test preview text truncates values longer than 50 chars."""
        long_value = "a" * 100
        var = VariableInfo(name="data", value=long_value)

        preview = var.get_preview_text()
        assert len(preview) == 50
        assert preview.endswith("...")

    def test_nested_children(self):
        """Test variable with nested children."""
        child1 = VariableInfo(name="name", var_type="String", path="user.name")
        child2 = VariableInfo(name="email", var_type="String", path="user.email")

        parent = VariableInfo(
            name="user",
            var_type="Dict",
            children=[child1, child2],
        )

        assert len(parent.children) == 2
        assert parent.children[0].path == "user.name"
        assert parent.children[1].path == "user.email"


class TestVariableProvider:
    """Tests for VariableProvider class."""

    def test_singleton_instance(self):
        """Test get_instance returns same instance."""
        instance1 = VariableProvider.get_instance()
        instance2 = VariableProvider.get_instance()

        assert instance1 is instance2

    def test_add_and_get_variable(self):
        """Test adding and retrieving a custom variable."""
        provider = VariableProvider()
        var = VariableInfo(name="testVar", var_type="String", value="hello")

        provider.add_variable(var)
        all_vars = provider.get_all_variables()

        # Should contain our custom var plus system vars
        names = [v.name for v in all_vars]
        assert "testVar" in names

    def test_remove_variable(self):
        """Test removing a custom variable."""
        provider = VariableProvider()
        var = VariableInfo(name="toRemove")

        provider.add_variable(var)
        provider.remove_variable("toRemove")
        all_vars = provider.get_all_variables()

        names = [v.name for v in all_vars]
        assert "toRemove" not in names

    def test_clear_variables(self):
        """Test clearing all custom variables."""
        provider = VariableProvider()
        provider.add_variable(VariableInfo(name="var1"))
        provider.add_variable(VariableInfo(name="var2"))

        provider.clear_variables()

        # Should only have system variables now
        all_vars = provider.get_all_variables()
        names = [v.name for v in all_vars]
        assert "var1" not in names
        assert "var2" not in names

    def test_system_variables_included(self):
        """Test that system variables are always included."""
        provider = VariableProvider()
        all_vars = provider.get_all_variables()

        names = [v.name for v in all_vars]
        assert "$currentDate" in names
        assert "$currentTime" in names
        assert "$currentDateTime" in names
        assert "$timestamp" in names

    def test_system_variables_have_correct_types(self):
        """Test that system variables have correct types."""
        provider = VariableProvider()
        all_vars = provider.get_all_variables()

        var_map = {v.name: v for v in all_vars}

        assert var_map["$currentDate"].var_type == "String"
        assert var_map["$currentTime"].var_type == "String"
        assert var_map["$currentDateTime"].var_type == "String"
        assert var_map["$timestamp"].var_type == "Integer"

    def test_system_variables_have_source(self):
        """Test that system variables have source set to 'system'."""
        provider = VariableProvider()
        all_vars = provider.get_all_variables()

        system_vars = [v for v in all_vars if v.name.startswith("$")]
        for var in system_vars:
            assert var.source == "system"

    def test_infer_type_string(self):
        """Test type inference for string values."""
        provider = VariableProvider()
        assert provider._infer_type("hello") == "String"

    def test_infer_type_integer(self):
        """Test type inference for integer values."""
        provider = VariableProvider()
        assert provider._infer_type(42) == "Integer"

    def test_infer_type_float(self):
        """Test type inference for float values."""
        provider = VariableProvider()
        assert provider._infer_type(3.14) == "Float"

    def test_infer_type_boolean(self):
        """Test type inference for boolean values."""
        provider = VariableProvider()
        assert provider._infer_type(True) == "Boolean"
        assert provider._infer_type(False) == "Boolean"

    def test_infer_type_list(self):
        """Test type inference for list values."""
        provider = VariableProvider()
        assert provider._infer_type([1, 2, 3]) == "List"

    def test_infer_type_dict(self):
        """Test type inference for dict values."""
        provider = VariableProvider()
        assert provider._infer_type({"key": "value"}) == "Dict"

    def test_infer_type_any(self):
        """Test type inference for unknown types."""
        provider = VariableProvider()
        assert provider._infer_type(object()) == "Any"


class TestTypeConstants:
    """Tests for TYPE_COLORS and TYPE_BADGES constants."""

    def test_all_types_have_colors(self):
        """Test that all expected types have colors defined."""
        expected_types = [
            "String",
            "Integer",
            "Float",
            "Boolean",
            "List",
            "Dict",
            "DataTable",
            "Any",
        ]

        for type_name in expected_types:
            assert type_name in TYPE_COLORS, f"Missing color for {type_name}"
            assert TYPE_COLORS[type_name].startswith(
                "#"
            ), f"Invalid color format for {type_name}"

    def test_all_types_have_badges(self):
        """Test that all expected types have badges defined."""
        expected_types = [
            "String",
            "Integer",
            "Float",
            "Boolean",
            "List",
            "Dict",
            "DataTable",
            "Any",
        ]

        for type_name in expected_types:
            assert type_name in TYPE_BADGES, f"Missing badge for {type_name}"

    def test_colors_are_valid_hex(self):
        """Test that all colors are valid hex color codes."""
        import re

        hex_pattern = re.compile(r"^#[0-9a-fA-F]{6}$")

        for type_name, color in TYPE_COLORS.items():
            assert hex_pattern.match(
                color
            ), f"Invalid hex color for {type_name}: {color}"
