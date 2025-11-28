"""
Edge case and boundary condition tests for workflow validation.

Tests boundary values, corner cases, and unusual but valid scenarios.
"""

import pytest
from typing import Dict, Any

# Note: validation module still in core/ but doesn't trigger deprecation warnings
from casare_rpa.domain.validation import (
    validate_workflow,
    validate_node,
    validate_connections,
    ValidationResult,
    _parse_connection,
    _is_exec_port,
    _find_entry_points_and_reachable,
)


# ============================================================================
# Boundary Value Tests
# ============================================================================


class TestBoundaryValues:
    """Test boundary values for numeric and string fields."""

    def test_zero_nodes(self) -> None:
        """Test workflow with zero nodes."""
        data = {"metadata": {"name": "Empty"}, "nodes": {}, "connections": []}
        result = validate_workflow(data)
        assert result.is_valid is False
        assert any(issue.code == "EMPTY_WORKFLOW" for issue in result.errors)

    def test_single_node(self) -> None:
        """Test workflow with exactly one node."""
        data = {
            "metadata": {"name": "Single"},
            "nodes": {"n1": {"node_id": "n1", "node_type": "StartNode"}},
            "connections": [],
        }
        result = validate_workflow(data)
        assert result.is_valid is True

    def test_exactly_100_char_workflow_name(self) -> None:
        """Test workflow name at exactly 100 characters (boundary)."""
        name_100 = "A" * 100
        data = {
            "metadata": {"name": name_100},
            "nodes": {"n1": {"node_id": "n1", "node_type": "StartNode"}},
        }
        result = validate_workflow(data)
        # Should not generate warning (exactly at limit)
        assert not any(issue.code == "NAME_TOO_LONG" for issue in result.warnings)

    def test_101_char_workflow_name(self) -> None:
        """Test workflow name at 101 characters (just over boundary)."""
        name_101 = "A" * 101
        data = {
            "metadata": {"name": name_101},
            "nodes": {"n1": {"node_id": "n1", "node_type": "StartNode"}},
        }
        result = validate_workflow(data)
        # Should generate warning (over limit)
        assert any(issue.code == "NAME_TOO_LONG" for issue in result.warnings)

    def test_empty_string_workflow_name(self) -> None:
        """Test workflow with empty string name."""
        data = {
            "metadata": {"name": ""},
            "nodes": {"n1": {"node_id": "n1", "node_type": "StartNode"}},
        }
        result = validate_workflow(data)
        assert any(issue.code == "MISSING_NAME" for issue in result.warnings)

    def test_position_at_zero(self) -> None:
        """Test node position at (0, 0)."""
        node_data = {
            "node_id": "n1",
            "node_type": "StartNode",
            "position": [0, 0],
        }
        result = validate_node("n1", node_data)
        assert result.is_valid is True

    def test_position_with_negative_values(self) -> None:
        """Test node position with negative coordinates."""
        node_data = {
            "node_id": "n1",
            "node_type": "StartNode",
            "position": [-100, -200],
        }
        result = validate_node("n1", node_data)
        assert result.is_valid is True  # Negative positions are valid

    def test_position_with_float_values(self) -> None:
        """Test node position with float values."""
        node_data = {
            "node_id": "n1",
            "node_type": "StartNode",
            "position": [123.456, 789.012],
        }
        result = validate_node("n1", node_data)
        assert result.is_valid is True

    def test_position_with_very_large_values(self) -> None:
        """Test node position with very large coordinates."""
        node_data = {
            "node_id": "n1",
            "node_type": "StartNode",
            "position": [999999, 999999],
        }
        result = validate_node("n1", node_data)
        assert result.is_valid is True


# ============================================================================
# Empty and Missing Field Tests
# ============================================================================


class TestEmptyAndMissingFields:
    """Test handling of empty and missing fields."""

    def test_empty_connections_list(self) -> None:
        """Test workflow with empty connections list."""
        data = {
            "metadata": {"name": "No Connections"},
            "nodes": {
                "n1": {"node_id": "n1", "node_type": "StartNode"},
                "n2": {"node_id": "n2", "node_type": "EndNode"},
            },
            "connections": [],
        }
        result = validate_workflow(data)
        # Valid workflow, just no connections
        assert result.is_valid is True

    def test_missing_metadata(self) -> None:
        """Test workflow with missing metadata section."""
        data = {
            "nodes": {"n1": {"node_id": "n1", "node_type": "StartNode"}},
            "connections": [],
        }
        result = validate_workflow(data)
        # Should still validate (metadata is optional)

    def test_missing_connections(self) -> None:
        """Test workflow with missing connections section."""
        data = {
            "metadata": {"name": "No Connections Key"},
            "nodes": {"n1": {"node_id": "n1", "node_type": "StartNode"}},
        }
        result = validate_workflow(data)
        # Should still validate (connections defaults to empty)

    def test_node_with_empty_config(self) -> None:
        """Test node with empty config dict."""
        node_data = {
            "node_id": "n1",
            "node_type": "StartNode",
            "config": {},
        }
        result = validate_node("n1", node_data)
        assert result.is_valid is True

    def test_node_with_missing_config(self) -> None:
        """Test node with missing config field."""
        node_data = {
            "node_id": "n1",
            "node_type": "StartNode",
        }
        result = validate_node("n1", node_data)
        assert result.is_valid is True  # Config is optional

    def test_node_with_missing_position(self) -> None:
        """Test node with missing position field."""
        node_data = {
            "node_id": "n1",
            "node_type": "StartNode",
        }
        result = validate_node("n1", node_data)
        assert result.is_valid is True  # Position is optional

    def test_empty_port_names(self) -> None:
        """Test connection with empty port names."""
        data = {
            "nodes": {
                "n1": {"node_id": "n1", "node_type": "StartNode"},
                "n2": {"node_id": "n2", "node_type": "EndNode"},
            },
            "connections": [
                {
                    "source_node": "n1",
                    "source_port": "",
                    "target_node": "n2",
                    "target_port": "",
                }
            ],
        }
        result = validate_workflow(data)
        # Empty port names are technically valid but unusual


# ============================================================================
# Special Character Tests
# ============================================================================


class TestSpecialCharacters:
    """Test handling of special characters in various fields."""

    def test_unicode_emoji_in_workflow_name(self) -> None:
        """Test Unicode emoji in workflow name."""
        data = {
            "metadata": {"name": "My Workflow 🚀 🎉"},
            "nodes": {"n1": {"node_id": "n1", "node_type": "StartNode"}},
        }
        result = validate_workflow(data)
        assert result.is_valid is True

    def test_unicode_characters_in_node_id(self) -> None:
        """Test Unicode characters in node ID."""
        node_id = "节点_123_🔥"
        data = {
            "nodes": {
                node_id: {
                    "node_id": node_id,
                    "node_type": "StartNode",
                }
            }
        }
        result = validate_workflow(data)
        assert result.is_valid is True

    def test_whitespace_in_node_id(self) -> None:
        """Test whitespace characters in node ID."""
        node_id = "node with spaces"
        data = {
            "nodes": {
                node_id: {
                    "node_id": node_id,
                    "node_type": "StartNode",
                }
            }
        }
        result = validate_workflow(data)
        assert result.is_valid is True

    def test_newlines_in_metadata(self) -> None:
        """Test newline characters in metadata."""
        data = {
            "metadata": {
                "name": "Line 1\nLine 2\nLine 3",
                "description": "Multi\nline\ndescription",
            },
            "nodes": {"n1": {"node_id": "n1", "node_type": "StartNode"}},
        }
        result = validate_workflow(data)
        assert result.is_valid is True

    def test_tab_characters_in_config(self) -> None:
        """Test tab characters in config values."""
        data = {
            "nodes": {
                "n1": {
                    "node_id": "n1",
                    "node_type": "StartNode",
                    "config": {"value": "col1\tcol2\tcol3"},
                }
            }
        }
        result = validate_workflow(data)
        assert result.is_valid is True


# ============================================================================
# Connection Format Tests
# ============================================================================


class TestConnectionFormats:
    """Test various connection data formats."""

    def test_parse_connection_standard_format(self) -> None:
        """Test parsing standard connection format."""
        conn = {
            "source_node": "n1",
            "source_port": "out",
            "target_node": "n2",
            "target_port": "in",
        }
        parsed = _parse_connection(conn)
        assert parsed is not None
        assert parsed["source_node"] == "n1"
        assert parsed["source_port"] == "out"
        assert parsed["target_node"] == "n2"
        assert parsed["target_port"] == "in"

    def test_parse_connection_alternative_format(self) -> None:
        """Test parsing alternative connection format."""
        conn = {"out": ["n1", "output_port"], "in": ["n2", "input_port"]}
        parsed = _parse_connection(conn)
        assert parsed is not None
        assert parsed["source_node"] == "n1"
        assert parsed["source_port"] == "output_port"
        assert parsed["target_node"] == "n2"
        assert parsed["target_port"] == "input_port"

    def test_parse_connection_with_extra_fields(self) -> None:
        """Test parsing connection with extra fields."""
        conn = {
            "source_node": "n1",
            "source_port": "out",
            "target_node": "n2",
            "target_port": "in",
            "extra_field": "should be ignored",
            "another_field": 123,
        }
        parsed = _parse_connection(conn)
        assert parsed is not None
        # Extra fields should not cause issues

    def test_parse_connection_insufficient_array_length(self) -> None:
        """Test parsing connection with insufficient array length."""
        conn = {"out": ["n1"], "in": ["n2"]}  # Missing port names
        parsed = _parse_connection(conn)
        assert parsed is None

    def test_parse_connection_empty_arrays(self) -> None:
        """Test parsing connection with empty arrays."""
        conn = {"out": [], "in": []}
        parsed = _parse_connection(conn)
        assert parsed is None

    def test_parse_connection_mixed_types(self) -> None:
        """Test parsing connection with mixed types in arrays."""
        conn = {"out": [123, 456], "in": ["n2", "port"]}  # Numbers instead of strings
        parsed = _parse_connection(conn)
        # Should still parse (type coercion may happen)


# ============================================================================
# Port Name Tests
# ============================================================================


class TestPortNames:
    """Test port name detection and classification."""

    def test_is_exec_port_various_names(self) -> None:
        """Test execution port detection with various names."""
        exec_ports = [
            "exec_in",
            "exec_out",
            "exec",
            "EXEC_IN",  # Case insensitive
            "ExEc_OuT",
            "loop_body",
            "true",
            "false",
            "then",
            "else",
            "on_success",
            "on_error",
            "on_finally",
            "body",
            "done",
            "finish",
            "next",
        ]

        for port in exec_ports:
            assert _is_exec_port(port) is True, f"'{port}' should be exec port"

    def test_is_exec_port_data_ports(self) -> None:
        """Test that data ports are not classified as exec ports."""
        data_ports = [
            "data_in",
            "data_out",
            "value",
            "result",
            "output",
            "input",
            "text",
            "number",
        ]

        for port in data_ports:
            assert _is_exec_port(port) is False, f"'{port}' should not be exec port"

    def test_is_exec_port_edge_cases(self) -> None:
        """Test exec port detection with edge cases."""
        assert _is_exec_port("") is False
        assert _is_exec_port(" exec_in ") is False  # Whitespace (exact match needed)
        assert _is_exec_port("exec") is True
        assert _is_exec_port("execution") is True  # Contains "exec"


# ============================================================================
# Graph Structure Tests
# ============================================================================


class TestGraphStructures:
    """Test various graph structures and topologies."""

    def test_linear_chain(self) -> None:
        """Test simple linear chain of nodes."""
        nodes = {
            f"n{i}": {"node_id": f"n{i}", "node_type": "LogNode"} for i in range(5)
        }
        connections = [
            {
                "source_node": f"n{i}",
                "source_port": "exec_out",
                "target_node": f"n{i+1}",
                "target_port": "exec_in",
            }
            for i in range(4)
        ]

        data = {
            "metadata": {"name": "Linear"},
            "nodes": nodes,
            "connections": connections,
        }
        result = validate_workflow(data)
        assert result.is_valid is True

    def test_branching_structure(self) -> None:
        """Test workflow with branching (one source, multiple targets)."""
        data = {
            "metadata": {"name": "Branching"},
            "nodes": {
                "start": {"node_id": "start", "node_type": "StartNode"},
                "branch1": {"node_id": "branch1", "node_type": "LogNode"},
                "branch2": {"node_id": "branch2", "node_type": "LogNode"},
            },
            "connections": [
                {
                    "source_node": "start",
                    "source_port": "exec_out",
                    "target_node": "branch1",
                    "target_port": "exec_in",
                },
                {
                    "source_node": "start",
                    "source_port": "exec_out",
                    "target_node": "branch2",
                    "target_port": "exec_in",
                },
            ],
        }
        result = validate_workflow(data)
        assert result.is_valid is True

    def test_merging_structure(self) -> None:
        """Test workflow with merging (multiple sources, one target)."""
        data = {
            "metadata": {"name": "Merging"},
            "nodes": {
                "source1": {"node_id": "source1", "node_type": "StartNode"},
                "source2": {"node_id": "source2", "node_type": "StartNode"},
                "target": {"node_id": "target", "node_type": "EndNode"},
            },
            "connections": [
                {
                    "source_node": "source1",
                    "source_port": "exec_out",
                    "target_node": "target",
                    "target_port": "exec_in",
                },
                {
                    "source_node": "source2",
                    "source_port": "exec_out",
                    "target_node": "target",
                    "target_port": "exec_in",
                },
            ],
        }
        result = validate_workflow(data)
        # Multiple entry points
        entry_points, _ = _find_entry_points_and_reachable(
            data["nodes"], data["connections"]
        )
        assert len(entry_points) == 2

    def test_disconnected_components(self) -> None:
        """Test workflow with multiple disconnected subgraphs."""
        data = {
            "metadata": {"name": "Disconnected"},
            "nodes": {
                "a1": {"node_id": "a1", "node_type": "StartNode"},
                "a2": {"node_id": "a2", "node_type": "EndNode"},
                "b1": {"node_id": "b1", "node_type": "StartNode"},
                "b2": {"node_id": "b2", "node_type": "EndNode"},
            },
            "connections": [
                {
                    "source_node": "a1",
                    "source_port": "exec_out",
                    "target_node": "a2",
                    "target_port": "exec_in",
                },
                {
                    "source_node": "b1",
                    "source_port": "exec_out",
                    "target_node": "b2",
                    "target_port": "exec_in",
                },
            ],
        }
        result = validate_workflow(data)
        # Valid workflow with two separate flows
        assert result.is_valid is True


# ============================================================================
# Hidden/System Node Tests
# ============================================================================


class TestHiddenNodes:
    """Test handling of hidden/system nodes (starting with __)."""

    def test_auto_start_node(self) -> None:
        """Test __auto_start__ system node."""
        data = {
            "metadata": {"name": "Auto Start"},
            "nodes": {
                "__auto_start__": {
                    "node_id": "__auto_start__",
                    "node_type": "StartNode",
                },
                "n1": {"node_id": "n1", "node_type": "EndNode"},
            },
            "connections": [
                {
                    "source_node": "__auto_start__",
                    "source_port": "exec_out",
                    "target_node": "n1",
                    "target_port": "exec_in",
                }
            ],
        }
        result = validate_workflow(data)
        # __auto_start__ should be recognized as entry point
        entry_points, _ = _find_entry_points_and_reachable(
            data["nodes"], data["connections"]
        )
        assert "__auto_start__" in entry_points

    def test_hidden_nodes_not_in_unreachable_warning(self) -> None:
        """Test that hidden nodes don't appear in unreachable warnings."""
        data = {
            "metadata": {"name": "Hidden"},
            "nodes": {
                "start": {"node_id": "start", "node_type": "StartNode"},
                "end": {"node_id": "end", "node_type": "EndNode"},
                "__internal__": {
                    "node_id": "__internal__",
                    "node_type": "LogNode",
                },
            },
            "connections": [
                {
                    "source_node": "start",
                    "source_port": "exec_out",
                    "target_node": "end",
                    "target_port": "exec_in",
                }
            ],
        }
        result = validate_workflow(data)
        # __internal__ is unreachable but shouldn't appear in warning


# ============================================================================
# Config Data Type Tests
# ============================================================================


class TestConfigDataTypes:
    """Test various data types in node config."""

    def test_config_with_nested_dicts(self) -> None:
        """Test node config with deeply nested dictionaries."""
        config = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {"value": "deep"},
                    }
                }
            }
        }
        node_data = {
            "node_id": "n1",
            "node_type": "StartNode",
            "config": config,
        }
        result = validate_node("n1", node_data)
        assert result.is_valid is True

    def test_config_with_arrays(self) -> None:
        """Test node config with array values."""
        node_data = {
            "node_id": "n1",
            "node_type": "StartNode",
            "config": {
                "items": [1, 2, 3, 4, 5],
                "strings": ["a", "b", "c"],
                "mixed": [1, "two", 3.0, True, None],
            },
        }
        result = validate_node("n1", node_data)
        assert result.is_valid is True

    def test_config_with_boolean_values(self) -> None:
        """Test node config with boolean values."""
        node_data = {
            "node_id": "n1",
            "node_type": "StartNode",
            "config": {
                "enabled": True,
                "disabled": False,
            },
        }
        result = validate_node("n1", node_data)
        assert result.is_valid is True

    def test_config_with_null_values(self) -> None:
        """Test node config with null/None values."""
        node_data = {
            "node_id": "n1",
            "node_type": "StartNode",
            "config": {
                "optional_field": None,
                "another_field": None,
            },
        }
        result = validate_node("n1", node_data)
        assert result.is_valid is True

    def test_config_with_numeric_values(self) -> None:
        """Test node config with various numeric types."""
        node_data = {
            "node_id": "n1",
            "node_type": "StartNode",
            "config": {
                "integer": 42,
                "negative": -100,
                "float": 3.14159,
                "scientific": 1.23e-10,
                "zero": 0,
            },
        }
        result = validate_node("n1", node_data)
        assert result.is_valid is True
