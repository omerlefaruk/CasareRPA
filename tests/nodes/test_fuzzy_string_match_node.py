"""
Tests for FuzzyStringMatchNode.

Ensures custom execution output ports are preserved by @node(exec_outputs=...).
"""

from casare_rpa.nodes.string_nodes import FuzzyStringMatchNode


def test_fuzzy_string_match_node_exec_outputs_preserved() -> None:
    node = FuzzyStringMatchNode("test_node")

    assert "exec_in" in node.input_ports
    assert "match_found" in node.output_ports
    assert "no_match" in node.output_ports
    assert "exec_out" not in node.output_ports
