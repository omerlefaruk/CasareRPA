"""
Node decorator consistency tests.

Policy:
- Every executable node must use both @node and @properties.
- The decorators must attach runtime metadata (__node_meta__) and a config schema
  (__node_schema__) used by the Canvas UI and workflow execution.
- The @node decorator strictly enforces configured execution ports.

Run: pytest tests/domain/test_node_decorators.py -v
"""

from __future__ import annotations

import logging
from typing import Any, Dict

import pytest

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef
from casare_rpa.domain.value_objects.types import DataType, NodeResult, PortType
from casare_rpa.nodes import get_all_node_classes


def test_all_registered_nodes_have_node_and_properties_decorators() -> None:
    offenders: list[str] = []

    for name, cls in get_all_node_classes().items():
        if not hasattr(cls, "__node_meta__"):
            offenders.append(f"{name} missing __node_meta__ (add @node)")
        if not hasattr(cls, "__node_schema__"):
            offenders.append(f"{name} missing __node_schema__ (add @properties)")

    assert not offenders, "Decorator policy violations:\n- " + "\n- ".join(offenders)


class TestNodeDecoratorEnforcement:
    def test_node_decorator_enforces_exec_ports(self, caplog) -> None:
        """Test that @node removes unconfigured execution ports and logs a warning."""

        # Define a node that manually adds an exec port NOT in the decorator config
        @properties()
        @node(category="test", exec_inputs=["exec_in"], exec_outputs=["exec_out"])
        class RogueNode(BaseNode):
            def _define_ports(self) -> None:
                # Add standard ports
                self.add_input_port("data", DataType.STRING)
                # Rogue execution port!
                self.add_input_port("on_error", DataType.EXEC)

            async def execute(self, context: Any) -> NodeResult:
                return {"success": True}

        # Instantiate node
        with caplog.at_level(logging.WARNING):
            n = RogueNode("test_1")

        # Verify rogue port was removed
        assert "on_error" not in n.input_ports
        assert "data" in n.input_ports
        assert "exec_in" in n.input_ports

        # Verify warning was logged
        assert "Removing unconfigured execution input port 'on_error'" in caplog.text

    def test_node_decorator_preserves_configured_exec_ports(self) -> None:
        """Test that @node keeps execution ports that ARE in the config."""

        @properties()
        @node(
            category="test",
            exec_inputs=["start", "trigger"],
            exec_outputs=["done", "failed"],
        )
        class CustomFlowNode(BaseNode):
            def _define_ports(self) -> None:
                # These should be preserved because they are in @node
                # Note: add_exec_input is the preferred way, but even if added via add_input_port
                # with DataType.EXEC, they should be kept if configured.
                self.add_input_port("trigger", DataType.EXEC)

            async def execute(self, context: Any) -> NodeResult:
                return {"success": True}

        n = CustomFlowNode("test_2")

        assert "start" in n.input_ports  # Added automatically by decorator
        assert "trigger" in n.input_ports  # Preserved
        assert "done" in n.output_ports
        assert "failed" in n.output_ports
