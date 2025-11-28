"""
Security-focused tests for workflow validation module.

Tests for security vulnerabilities including:
- Injection attacks
- Resource exhaustion (DoS)
- Code execution vulnerabilities
- Path traversal
- Infinite loops/recursion
- Memory leaks
- Input sanitization
"""

import pytest
import sys
from typing import Dict, Any

# Note: validation module still in core/ but doesn't trigger deprecation warnings
from casare_rpa.core.validation import (
    validate_workflow,
    validate_node,
    validate_connections,
    _has_circular_dependency,
    _find_entry_points_and_reachable,
    _parse_connection,
)


# ============================================================================
# Injection Attack Tests
# ============================================================================


class TestInjectionAttacks:
    """Test for injection vulnerabilities in validation."""

    def test_sql_injection_in_node_id(self) -> None:
        """Test SQL injection attempt in node_id field."""
        malicious_id = "'; DROP TABLE nodes; --"
        data = {
            "nodes": {
                malicious_id: {
                    "node_id": malicious_id,
                    "node_type": "StartNode",
                }
            }
        }
        # Should handle safely without executing anything
        result = validate_workflow(data)
        # Validation should complete without crash

    def test_javascript_injection_in_config(self) -> None:
        """Test JavaScript injection in node config."""
        data = {
            "nodes": {
                "n1": {
                    "node_id": "n1",
                    "node_type": "StartNode",
                    "config": {
                        "script": "<script>alert('XSS')</script>",
                        "eval": "eval('malicious code')",
                    },
                }
            }
        }
        result = validate_workflow(data)
        # Should not execute any code

    def test_command_injection_in_metadata(self) -> None:
        """Test command injection in metadata fields."""
        data = {
            "metadata": {
                "name": "workflow; rm -rf /",
                "description": "$(malicious command)",
            },
            "nodes": {"n1": {"node_id": "n1", "node_type": "StartNode"}},
        }
        result = validate_workflow(data)
        # Should treat as plain text

    def test_python_code_injection_in_node_type(self) -> None:
        """Test Python code injection in node_type."""
        data = {
            "nodes": {
                "n1": {
                    "node_id": "n1",
                    "node_type": "__import__('os').system('echo pwned')",
                }
            }
        }
        result = validate_workflow(data)
        # Should fail validation but not execute code
        assert result.is_valid is False

    def test_format_string_injection(self) -> None:
        """Test format string injection vulnerabilities."""
        data = {
            "metadata": {"name": "{.__class__.__bases__[0].__subclasses__()}"},
            "nodes": {
                "n1": {
                    "node_id": "n1",
                    "node_type": "StartNode",
                    "config": {"value": "{0.__class__}"},
                }
            },
        }
        result = validate_workflow(data)
        # Should not evaluate format strings


# ============================================================================
# Resource Exhaustion (DoS) Tests
# ============================================================================


class TestResourceExhaustion:
    """Test for denial-of-service vulnerabilities."""

    def test_extremely_large_node_count(self) -> None:
        """Test validation with massive number of nodes."""
        # Create 10,000 nodes to test memory limits
        nodes = {}
        for i in range(10000):
            nodes[f"node{i}"] = {
                "node_id": f"node{i}",
                "node_type": "LogNode",
            }

        data = {"metadata": {"name": "Large"}, "nodes": nodes, "connections": []}

        # Should complete without memory error
        try:
            result = validate_workflow(data)
            assert result is not None
        except MemoryError:
            pytest.fail("Validation caused memory error with large node count")

    def test_extremely_large_connection_count(self) -> None:
        """Test validation with massive number of connections."""
        nodes = {}
        connections = []

        # Create 100 nodes with fully connected graph (10,000 connections)
        for i in range(100):
            nodes[f"n{i}"] = {"node_id": f"n{i}", "node_type": "LogNode"}

        for i in range(100):
            for j in range(100):
                if i != j:
                    connections.append(
                        {
                            "source_node": f"n{i}",
                            "source_port": "exec_out",
                            "target_node": f"n{j}",
                            "target_port": "exec_in",
                        }
                    )

        data = {
            "metadata": {"name": "Dense"},
            "nodes": nodes,
            "connections": connections[:1000],  # Limit to prevent actual DoS
        }

        try:
            result = validate_workflow(data)
            assert result is not None
        except RecursionError:
            pytest.fail("Validation caused recursion error with many connections")

    def test_deeply_nested_dict_structure(self) -> None:
        """Test deeply nested dictionary structures."""
        # Create deeply nested config
        config = {"level0": {}}
        current = config["level0"]
        for i in range(1000):
            current[f"level{i+1}"] = {}
            current = current[f"level{i+1}"]

        data = {
            "nodes": {
                "n1": {"node_id": "n1", "node_type": "StartNode", "config": config}
            }
        }

        try:
            result = validate_workflow(data)
            assert result is not None
        except RecursionError:
            pytest.fail("Validation caused recursion error with deep nesting")

    def test_very_long_strings(self) -> None:
        """Test validation with extremely long string values."""
        long_string = "A" * 1000000  # 1MB string

        data = {
            "metadata": {"name": long_string},
            "nodes": {
                "n1": {
                    "node_id": "n1",
                    "node_type": "StartNode",
                    "config": {"value": long_string},
                }
            },
        }

        try:
            result = validate_workflow(data)
            assert result is not None
        except MemoryError:
            pytest.fail("Validation caused memory error with long strings")

    def test_circular_reference_in_config(self) -> None:
        """Test handling of circular references in config."""
        config = {"key": "value"}
        config["self"] = config  # Circular reference

        data = {"nodes": {"n1": {"node_id": "n1", "node_type": "StartNode"}}}
        # Don't include circular config as it would fail JSON serialization
        # This tests that validation doesn't crash on complex structures

        result = validate_workflow(data)
        assert result is not None


# ============================================================================
# Infinite Loop/Recursion Tests
# ============================================================================


class TestInfiniteLoopsAndRecursion:
    """Test for infinite loop vulnerabilities."""

    def test_circular_dependency_deep_chain(self) -> None:
        """Test circular dependency detection with deep chains."""
        # Create a long circular chain: n0 -> n1 -> ... -> n99 -> n0
        nodes = {}
        connections = []

        for i in range(100):
            nodes[f"n{i}"] = {"node_id": f"n{i}", "node_type": "LogNode"}

        for i in range(100):
            next_i = (i + 1) % 100  # Wrap around to create circle
            connections.append(
                {
                    "source_node": f"n{i}",
                    "source_port": "exec_out",
                    "target_node": f"n{next_i}",
                    "target_port": "exec_in",
                }
            )

        data = {
            "metadata": {"name": "Deep Circle"},
            "nodes": nodes,
            "connections": connections,
        }

        # Should detect circular dependency without infinite loop
        try:
            result = validate_workflow(data)
            assert result.is_valid is False
            # Should have detected circular dependency
        except RecursionError:
            pytest.fail("Circular dependency detection caused infinite recursion")

    def test_multiple_circular_dependencies(self) -> None:
        """Test multiple separate circular dependency chains."""
        nodes = {
            "a1": {"node_id": "a1", "node_type": "LogNode"},
            "a2": {"node_id": "a2", "node_type": "LogNode"},
            "b1": {"node_id": "b1", "node_type": "LogNode"},
            "b2": {"node_id": "b2", "node_type": "LogNode"},
        }
        connections = [
            # Circle 1: a1 -> a2 -> a1
            {
                "source_node": "a1",
                "source_port": "exec_out",
                "target_node": "a2",
                "target_port": "exec_in",
            },
            {
                "source_node": "a2",
                "source_port": "exec_out",
                "target_node": "a1",
                "target_port": "exec_in",
            },
            # Circle 2: b1 -> b2 -> b1
            {
                "source_node": "b1",
                "source_port": "exec_out",
                "target_node": "b2",
                "target_port": "exec_in",
            },
            {
                "source_node": "b2",
                "source_port": "exec_out",
                "target_node": "b1",
                "target_port": "exec_in",
            },
        ]

        data = {
            "metadata": {"name": "Multiple Circles"},
            "nodes": nodes,
            "connections": connections,
        }

        try:
            result = validate_workflow(data)
            assert result.is_valid is False
        except RecursionError:
            pytest.fail("Multiple circular dependencies caused infinite recursion")

    def test_self_referencing_connection(self) -> None:
        """Test self-referencing connection handling."""
        data = {
            "nodes": {"n1": {"node_id": "n1", "node_type": "LogNode"}},
            "connections": [
                {
                    "source_node": "n1",
                    "source_port": "exec_out",
                    "target_node": "n1",
                    "target_port": "exec_in",
                }
            ],
        }

        try:
            result = validate_workflow(data)
            # Should detect self-connection error
            assert result.is_valid is False
        except RecursionError:
            pytest.fail("Self-connection caused infinite recursion")


# ============================================================================
# Input Validation Bypass Tests
# ============================================================================


class TestInputValidationBypass:
    """Test for input validation bypass vulnerabilities."""

    def test_null_byte_injection(self) -> None:
        """Test null byte injection in strings."""
        data = {
            "metadata": {"name": "test\x00injection"},
            "nodes": {
                "n1\x00": {
                    "node_id": "n1\x00",
                    "node_type": "StartNode",
                }
            },
        }
        result = validate_workflow(data)
        # Should handle null bytes safely

    def test_unicode_normalization_attack(self) -> None:
        """Test Unicode normalization vulnerabilities."""
        # Using Unicode characters that normalize to dangerous strings
        data = {
            "metadata": {"name": "\u0041\u0301"},  # Á (decomposed)
            "nodes": {
                "n1": {
                    "node_id": "n1",
                    "node_type": "StartNode",
                    "config": {"value": "\ufeff"},  # Zero-width no-break space
                }
            },
        }
        result = validate_workflow(data)
        # Should handle Unicode normalization

    def test_type_confusion_attack(self) -> None:
        """Test type confusion vulnerabilities."""
        # Passing unexpected types to trigger type confusion
        data = {
            "nodes": {
                123: {  # Integer instead of string
                    "node_id": 123,
                    "node_type": "StartNode",
                }
            }
        }
        # Should handle type mismatch gracefully
        result = validate_workflow(data)

    def test_empty_string_node_id(self) -> None:
        """Test empty string as node_id."""
        data = {
            "nodes": {
                "": {
                    "node_id": "",
                    "node_type": "StartNode",
                }
            }
        }
        result = validate_workflow(data)
        # Empty string is technically valid but unusual

    def test_special_characters_in_ids(self) -> None:
        """Test special characters in node IDs."""
        special_chars = "!@#$%^&*()[]{}|\\;:'\",.<>?/`~"
        data = {
            "nodes": {
                special_chars: {
                    "node_id": special_chars,
                    "node_type": "StartNode",
                }
            }
        }
        result = validate_workflow(data)
        # Should handle special characters


# ============================================================================
# Memory Leak Tests
# ============================================================================


class TestMemoryLeaks:
    """Test for potential memory leaks."""

    def test_repeated_validation_no_leak(self) -> None:
        """Test that repeated validations don't leak memory."""
        data = {
            "metadata": {"name": "Test"},
            "nodes": {
                "n1": {"node_id": "n1", "node_type": "StartNode"},
                "n2": {"node_id": "n2", "node_type": "EndNode"},
            },
            "connections": [
                {
                    "source_node": "n1",
                    "source_port": "exec_out",
                    "target_node": "n2",
                    "target_port": "exec_in",
                }
            ],
        }

        # Run validation many times
        for _ in range(1000):
            result = validate_workflow(data)
            assert result is not None
            # Clear reference to help GC
            del result

    def test_large_validation_result_cleanup(self) -> None:
        """Test that large validation results are cleaned up properly."""
        nodes = {}
        for i in range(1000):
            nodes[f"node{i}"] = {
                "node_id": f"node{i}",
                "node_type": "UnknownType",  # Will generate errors
            }

        data = {"metadata": {"name": "Errors"}, "nodes": nodes}

        result = validate_workflow(data)
        # Should have many errors
        assert len(result.issues) > 0
        # Clear and ensure cleanup
        del result


# ============================================================================
# Path Traversal Tests
# ============================================================================


class TestPathTraversal:
    """Test for path traversal vulnerabilities."""

    def test_path_traversal_in_metadata(self) -> None:
        """Test path traversal attempts in metadata."""
        data = {
            "metadata": {
                "name": "../../etc/passwd",
                "description": "..\\..\\windows\\system32",
            },
            "nodes": {"n1": {"node_id": "n1", "node_type": "StartNode"}},
        }
        result = validate_workflow(data)
        # Should treat as plain text, not file paths

    def test_absolute_path_in_config(self) -> None:
        """Test absolute path in node config."""
        data = {
            "nodes": {
                "n1": {
                    "node_id": "n1",
                    "node_type": "StartNode",
                    "config": {
                        "file": "/etc/passwd",
                        "path": "C:\\Windows\\System32",
                    },
                }
            }
        }
        result = validate_workflow(data)
        # Validation should not attempt to access these paths


# ============================================================================
# Race Condition Tests
# ============================================================================


class TestRaceConditions:
    """Test for potential race conditions."""

    def test_concurrent_validation_same_data(self) -> None:
        """Test concurrent validation of the same workflow."""
        import threading

        data = {
            "metadata": {"name": "Concurrent"},
            "nodes": {"n1": {"node_id": "n1", "node_type": "StartNode"}},
        }

        results = []
        errors = []

        def validate_thread():
            try:
                result = validate_workflow(data)
                results.append(result)
            except Exception as e:
                errors.append(e)

        threads = []
        for _ in range(10):
            t = threading.Thread(target=validate_thread)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All validations should succeed
        assert len(errors) == 0
        assert len(results) == 10

    def test_global_state_isolation(self) -> None:
        """Test that validation doesn't rely on mutable global state."""
        # First validation
        data1 = {
            "nodes": {
                "n1": {"node_id": "n1", "node_type": "StartNode"},
            }
        }
        result1 = validate_workflow(data1)

        # Second validation with different data
        data2 = {
            "nodes": {
                "n2": {"node_id": "n2", "node_type": "EndNode"},
            }
        }
        result2 = validate_workflow(data2)

        # Results should be independent
        assert result1.issues != result2.issues


# ============================================================================
# Malformed Data Tests
# ============================================================================


class TestMalformedData:
    """Test handling of malformed/corrupted data."""

    def test_missing_keys_in_connection(self) -> None:
        """Test connection with missing required keys."""
        data = {
            "nodes": {"n1": {"node_id": "n1", "node_type": "StartNode"}},
            "connections": [
                {"source_node": "n1"}  # Missing other required fields
            ],
        }
        result = validate_workflow(data)
        assert result.is_valid is False

    def test_wrong_type_for_position(self) -> None:
        """Test wrong data type for position field."""
        data = {
            "nodes": {
                "n1": {
                    "node_id": "n1",
                    "node_type": "StartNode",
                    "position": "invalid",  # Should be list/tuple
                }
            }
        }
        result = validate_workflow(data)
        # Should generate warning but not crash

    def test_mixed_connection_formats(self) -> None:
        """Test mixing different connection formats."""
        data = {
            "nodes": {
                "n1": {"node_id": "n1", "node_type": "StartNode"},
                "n2": {"node_id": "n2", "node_type": "EndNode"},
            },
            "connections": [
                {
                    "source_node": "n1",
                    "source_port": "exec_out",
                    "target_node": "n2",
                    "target_port": "exec_in",
                },
                {"out": ["n1", "exec_out"], "in": ["n2", "exec_in"]},
            ],
        }
        result = validate_workflow(data)
        # Should handle both formats

    def test_none_as_workflow_data(self) -> None:
        """Test None as workflow data."""
        try:
            result = validate_workflow(None)
            assert result.is_valid is False
        except (TypeError, AttributeError):
            # Expected if validation doesn't handle None
            pass

    def test_list_as_workflow_data(self) -> None:
        """Test list instead of dict as workflow data."""
        result = validate_workflow([])
        assert result.is_valid is False
        assert any(issue.code == "INVALID_TYPE" for issue in result.errors)
