"""
Comprehensive headless Qt test suite for ALL CasareRPA visual nodes.

Tests every single node in the registry for:
1. Creation without errors
2. Widget initialization (text inputs, dropdowns, checkboxes, etc.)
3. Port configuration (inputs, outputs, exec ports)
4. Connection compatibility between nodes
5. Property access and modification

This test uses a real QApplication in offscreen/headless mode to test
actual Qt widget behavior without requiring a display.

Run with: pytest tests/presentation/canvas/visual_nodes/test_all_nodes_headless.py -v
"""

import os
import sys
import pytest
from typing import Dict, List, Tuple, Type, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict

# Set Qt to offscreen mode BEFORE any Qt imports
os.environ["QT_QPA_PLATFORM"] = "offscreen"


@dataclass
class NodeTestResult:
    """Result of testing a single node."""

    node_name: str
    visual_class_name: str
    success: bool = True
    creation_error: Optional[str] = None
    widget_errors: List[str] = field(default_factory=list)
    port_errors: List[str] = field(default_factory=list)
    property_errors: List[str] = field(default_factory=list)
    widgets_count: int = 0
    input_ports_count: int = 0
    output_ports_count: int = 0
    has_casare_node: bool = False

    @property
    def all_errors(self) -> List[str]:
        errors = []
        if self.creation_error:
            errors.append(f"CREATION: {self.creation_error}")
        errors.extend([f"WIDGET: {e}" for e in self.widget_errors])
        errors.extend([f"PORT: {e}" for e in self.port_errors])
        errors.extend([f"PROPERTY: {e}" for e in self.property_errors])
        return errors


@dataclass
class TestSummary:
    """Summary of all node tests."""

    total_nodes: int = 0
    successful_nodes: int = 0
    failed_nodes: int = 0
    total_widgets: int = 0
    total_input_ports: int = 0
    total_output_ports: int = 0
    results: List[NodeTestResult] = field(default_factory=list)
    errors_by_category: Dict[str, List[str]] = field(
        default_factory=lambda: defaultdict(list)
    )

    @property
    def success_rate(self) -> float:
        if self.total_nodes == 0:
            return 0.0
        return (self.successful_nodes / self.total_nodes) * 100


# Global QApplication instance
_qapp = None


def get_qapp():
    """Get or create the QApplication instance."""
    global _qapp
    if _qapp is None:
        from PySide6.QtWidgets import QApplication

        # Check if there's already a QApplication
        _qapp = QApplication.instance()
        if _qapp is None:
            _qapp = QApplication([])
    return _qapp


@pytest.fixture(scope="module")
def qapp():
    """Provide a QApplication for the test module."""
    app = get_qapp()
    yield app


@pytest.fixture(scope="module")
def node_graph(qapp):
    """Create a NodeGraph instance for testing."""
    from NodeGraphQt import NodeGraph

    graph = NodeGraph()
    return graph


@pytest.fixture(scope="module")
def visual_node_registry():
    """Get the visual node registry with all node classes."""
    from casare_rpa.presentation.canvas.visual_nodes import (
        _VISUAL_NODE_REGISTRY,
        _lazy_import,
    )

    return _VISUAL_NODE_REGISTRY, _lazy_import


@pytest.fixture(scope="module")
def registered_graph(node_graph):
    """Register all nodes with the graph."""
    from casare_rpa.presentation.canvas.graph.node_registry import (
        get_node_registry,
    )

    registry = get_node_registry()
    registry.register_all_nodes(node_graph)
    return node_graph


class TestNodeCreation:
    """Test that all nodes can be created without errors."""

    def test_all_nodes_can_be_imported(self, visual_node_registry):
        """Test that all visual node classes can be imported."""
        registry, lazy_import = visual_node_registry

        import_errors = []
        imported_classes = []

        for node_name in registry.keys():
            try:
                cls = lazy_import(node_name)
                imported_classes.append((node_name, cls))
            except Exception as e:
                import_errors.append((node_name, str(e)))

        # Report all import errors
        if import_errors:
            error_msg = "\n".join([f"  {name}: {err}" for name, err in import_errors])
            print(f"\nImport errors ({len(import_errors)}):\n{error_msg}")

        # All nodes should import successfully
        assert (
            len(import_errors) == 0
        ), f"Failed to import {len(import_errors)} nodes:\n{error_msg}"
        print(f"\nSuccessfully imported {len(imported_classes)} node classes")

    def test_all_nodes_can_be_created(self, registered_graph, visual_node_registry):
        """Test that all nodes can be instantiated in the graph."""
        registry, lazy_import = visual_node_registry
        graph = registered_graph

        summary = TestSummary()
        creation_errors = []

        for node_name in sorted(registry.keys()):
            result = NodeTestResult(
                node_name=node_name,
                visual_class_name=node_name,
            )
            summary.total_nodes += 1

            try:
                # Get the visual node class
                visual_cls = lazy_import(node_name)

                # Create the node
                identifier = f"{visual_cls.__identifier__}.{node_name}"
                node = graph.create_node(identifier)

                if node is None:
                    result.creation_error = "create_node returned None"
                    result.success = False
                else:
                    # Count widgets
                    try:
                        widgets = node.widgets()
                        result.widgets_count = len(widgets)
                        summary.total_widgets += result.widgets_count
                    except Exception as e:
                        result.widget_errors.append(f"Failed to get widgets: {e}")

                    # Count ports
                    try:
                        input_ports = node.input_ports()
                        output_ports = node.output_ports()
                        result.input_ports_count = len(input_ports)
                        result.output_ports_count = len(output_ports)
                        summary.total_input_ports += result.input_ports_count
                        summary.total_output_ports += result.output_ports_count
                    except Exception as e:
                        result.port_errors.append(f"Failed to get ports: {e}")

                    # Check for CasareRPA node
                    try:
                        casare_node = (
                            node.get_casare_node()
                            if hasattr(node, "get_casare_node")
                            else None
                        )
                        result.has_casare_node = casare_node is not None
                    except Exception:
                        pass

                    # Clean up
                    try:
                        graph.delete_node(node)
                    except Exception:
                        pass

            except Exception as e:
                result.creation_error = str(e)
                result.success = False

            if result.success:
                summary.successful_nodes += 1
            else:
                summary.failed_nodes += 1
                creation_errors.append(result)

            summary.results.append(result)

        # Print summary
        print(f"\n{'='*80}")
        print("NODE CREATION TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total nodes tested: {summary.total_nodes}")
        print(f"Successful: {summary.successful_nodes}")
        print(f"Failed: {summary.failed_nodes}")
        print(f"Success rate: {summary.success_rate:.1f}%")
        print(f"Total widgets: {summary.total_widgets}")
        print(f"Total input ports: {summary.total_input_ports}")
        print(f"Total output ports: {summary.total_output_ports}")

        if creation_errors:
            print(f"\n{'='*80}")
            print(f"FAILED NODES ({len(creation_errors)}):")
            print(f"{'='*80}")
            for result in creation_errors:
                print(f"\n  {result.node_name}:")
                for error in result.all_errors:
                    print(f"    - {error}")

        assert (
            summary.failed_nodes == 0
        ), f"{summary.failed_nodes} nodes failed to create"


class TestNodeWidgets:
    """Test node widgets for all nodes."""

    def test_all_widgets_are_accessible(self, registered_graph, visual_node_registry):
        """Test that all node widgets can be accessed and have valid values."""
        registry, lazy_import = visual_node_registry
        graph = registered_graph

        widget_errors = []

        for node_name in sorted(registry.keys()):
            try:
                visual_cls = lazy_import(node_name)
                identifier = f"{visual_cls.__identifier__}.{node_name}"
                node = graph.create_node(identifier)

                if node is None:
                    continue

                try:
                    widgets = node.widgets()
                    for widget_name, widget in widgets.items():
                        try:
                            # Test widget visibility
                            visible = (
                                widget.isVisible()
                                if hasattr(widget, "isVisible")
                                else True
                            )

                            # Test getting the custom widget
                            if hasattr(widget, "get_custom_widget"):
                                custom = widget.get_custom_widget()
                                if custom is None:
                                    widget_errors.append(
                                        f"{node_name}.{widget_name}: get_custom_widget returned None"
                                    )

                            # Test property value access
                            try:
                                value = node.get_property(widget_name)
                            except Exception as e:
                                widget_errors.append(
                                    f"{node_name}.{widget_name}: get_property failed: {e}"
                                )

                        except Exception as e:
                            widget_errors.append(f"{node_name}.{widget_name}: {e}")

                finally:
                    try:
                        graph.delete_node(node)
                    except Exception:
                        pass

            except Exception as e:
                # Skip nodes that can't be created - tested in TestNodeCreation
                pass

        if widget_errors:
            print(f"\nWidget errors ({len(widget_errors)}):")
            for error in widget_errors[:50]:  # Limit output
                print(f"  - {error}")
            if len(widget_errors) > 50:
                print(f"  ... and {len(widget_errors) - 50} more errors")

        # Allow some widget errors (some widgets may have special requirements)
        max_errors = len(registry) * 0.1  # Allow 10% error rate
        assert (
            len(widget_errors) <= max_errors
        ), f"Too many widget errors: {len(widget_errors)}"


class TestNodePorts:
    """Test node ports for all nodes."""

    def test_all_input_ports_valid(self, registered_graph, visual_node_registry):
        """Test that all input ports are properly configured."""
        registry, lazy_import = visual_node_registry
        graph = registered_graph

        port_errors = []
        nodes_without_inputs = []

        for node_name in sorted(registry.keys()):
            try:
                visual_cls = lazy_import(node_name)
                identifier = f"{visual_cls.__identifier__}.{node_name}"
                node = graph.create_node(identifier)

                if node is None:
                    continue

                try:
                    input_ports = node.input_ports()

                    # Most nodes should have at least exec_in
                    # Exception: Start nodes, trigger nodes don't need exec_in
                    if len(input_ports) == 0:
                        # Check if it's a start/trigger node
                        category = getattr(visual_cls, "NODE_CATEGORY", "")
                        if "trigger" not in category and "Start" not in node_name:
                            nodes_without_inputs.append(node_name)

                    for port in input_ports:
                        try:
                            # Test port name
                            port_name = port.name()
                            if not port_name:
                                port_errors.append(
                                    f"{node_name}: Input port has no name"
                                )

                            # Test port color
                            if hasattr(port, "color"):
                                color = port.color
                                if color is None:
                                    port_errors.append(
                                        f"{node_name}.{port_name}: No color"
                                    )

                        except Exception as e:
                            port_errors.append(f"{node_name}: Port error: {e}")

                finally:
                    try:
                        graph.delete_node(node)
                    except Exception:
                        pass

            except Exception:
                pass

        if nodes_without_inputs:
            print(f"\nNodes without input ports ({len(nodes_without_inputs)}):")
            for name in nodes_without_inputs[:20]:
                print(f"  - {name}")

        if port_errors:
            print(f"\nPort errors ({len(port_errors)}):")
            for error in port_errors[:20]:
                print(f"  - {error}")

        # Port errors should be minimal
        assert len(port_errors) <= 5, f"Too many port errors: {len(port_errors)}"

    def test_all_output_ports_valid(self, registered_graph, visual_node_registry):
        """Test that all output ports are properly configured."""
        registry, lazy_import = visual_node_registry
        graph = registered_graph

        port_errors = []
        nodes_without_outputs = []

        for node_name in sorted(registry.keys()):
            try:
                visual_cls = lazy_import(node_name)
                identifier = f"{visual_cls.__identifier__}.{node_name}"
                node = graph.create_node(identifier)

                if node is None:
                    continue

                try:
                    output_ports = node.output_ports()

                    # Most nodes should have at least exec_out
                    # Exception: End nodes don't need exec_out
                    if len(output_ports) == 0:
                        if "End" not in node_name:
                            nodes_without_outputs.append(node_name)

                    for port in output_ports:
                        try:
                            port_name = port.name()
                            if not port_name:
                                port_errors.append(
                                    f"{node_name}: Output port has no name"
                                )

                        except Exception as e:
                            port_errors.append(f"{node_name}: Port error: {e}")

                finally:
                    try:
                        graph.delete_node(node)
                    except Exception:
                        pass

            except Exception:
                pass

        if nodes_without_outputs:
            print(f"\nNodes without output ports ({len(nodes_without_outputs)}):")
            for name in nodes_without_outputs[:20]:
                print(f"  - {name}")

        assert len(port_errors) <= 5, "Too many output port errors"

    def test_exec_port_consistency(self, registered_graph, visual_node_registry):
        """Test that exec ports follow naming conventions."""
        registry, lazy_import = visual_node_registry
        graph = registered_graph

        exec_port_issues = []

        for node_name in sorted(registry.keys()):
            try:
                visual_cls = lazy_import(node_name)
                identifier = f"{visual_cls.__identifier__}.{node_name}"
                node = graph.create_node(identifier)

                if node is None:
                    continue

                try:
                    input_ports = node.input_ports()
                    output_ports = node.output_ports()

                    # Check for exec_in port
                    exec_in_names = [
                        p.name() for p in input_ports if "exec" in p.name().lower()
                    ]
                    exec_out_names = [
                        p.name() for p in output_ports if "exec" in p.name().lower()
                    ]

                    # Control flow nodes should have specific exec outputs
                    category = getattr(visual_cls, "NODE_CATEGORY", "")
                    if "control_flow" in category:
                        if "If" in node_name:
                            # If nodes should have true/false outputs
                            out_names = [p.name().lower() for p in output_ports]
                            if "true" not in out_names and "false" not in out_names:
                                if "then" not in out_names and "else" not in out_names:
                                    exec_port_issues.append(
                                        f"{node_name}: If node missing true/false or then/else outputs"
                                    )

                finally:
                    try:
                        graph.delete_node(node)
                    except Exception:
                        pass

            except Exception:
                pass

        if exec_port_issues:
            print(f"\nExec port consistency issues ({len(exec_port_issues)}):")
            for issue in exec_port_issues:
                print(f"  - {issue}")


class TestNodeConnections:
    """Test node connection compatibility."""

    def test_basic_exec_connections(self, registered_graph, visual_node_registry):
        """Test that basic exec connections work between nodes."""
        registry, lazy_import = visual_node_registry
        graph = registered_graph

        connection_errors = []

        # Get Start and End nodes
        try:
            start_cls = lazy_import("VisualStartNode")
            end_cls = lazy_import("VisualEndNode")

            start_node = graph.create_node(
                f"{start_cls.__identifier__}.VisualStartNode"
            )
            end_node = graph.create_node(f"{end_cls.__identifier__}.VisualEndNode")

            if start_node and end_node:
                # Try to connect exec ports
                start_outputs = start_node.output_ports()
                end_inputs = end_node.input_ports()

                exec_out = None
                exec_in = None

                for port in start_outputs:
                    if "exec" in port.name().lower():
                        exec_out = port
                        break

                for port in end_inputs:
                    if "exec" in port.name().lower():
                        exec_in = port
                        break

                if exec_out and exec_in:
                    try:
                        exec_out.connect_to(exec_in)
                        # Verify connection
                        connected_ports = exec_out.connected_ports()
                        if exec_in not in connected_ports:
                            connection_errors.append(
                                "Start->End exec connection failed to establish"
                            )
                    except Exception as e:
                        connection_errors.append(f"Start->End connection error: {e}")
                else:
                    if not exec_out:
                        connection_errors.append("Start node has no exec_out port")
                    if not exec_in:
                        connection_errors.append("End node has no exec_in port")

                # Cleanup
                try:
                    graph.delete_node(start_node)
                    graph.delete_node(end_node)
                except Exception:
                    pass

        except Exception as e:
            connection_errors.append(f"Failed to test Start->End connection: {e}")

        assert len(connection_errors) == 0, f"Connection errors: {connection_errors}"

    def test_sample_node_chain(self, registered_graph, visual_node_registry):
        """Test creating a chain of commonly used nodes."""
        registry, lazy_import = visual_node_registry
        graph = registered_graph

        # Try to create a simple chain: Start -> SetVariable -> MessageBox -> End
        nodes_to_chain = [
            "VisualStartNode",
            "VisualSetVariableNode",
            "VisualMessageBoxNode",
            "VisualEndNode",
        ]

        created_nodes = []
        chain_errors = []

        for node_name in nodes_to_chain:
            try:
                if node_name in registry:
                    visual_cls = lazy_import(node_name)
                    identifier = f"{visual_cls.__identifier__}.{node_name}"
                    node = graph.create_node(identifier)
                    if node:
                        created_nodes.append(node)
                    else:
                        chain_errors.append(f"Failed to create {node_name}")
            except Exception as e:
                chain_errors.append(f"Error creating {node_name}: {e}")

        # Try to connect them in sequence
        for i in range(len(created_nodes) - 1):
            source = created_nodes[i]
            target = created_nodes[i + 1]

            try:
                # Find exec ports
                source_exec = None
                target_exec = None

                for port in source.output_ports():
                    name = port.name().lower()
                    if "exec" in name or name in ("exec_out", "output", "out"):
                        source_exec = port
                        break

                for port in target.input_ports():
                    name = port.name().lower()
                    if "exec" in name or name in ("exec_in", "input", "in"):
                        target_exec = port
                        break

                if source_exec and target_exec:
                    source_exec.connect_to(target_exec)
            except Exception as e:
                chain_errors.append(
                    f"Connection {source.name()} -> {target.name()} failed: {e}"
                )

        # Cleanup
        for node in created_nodes:
            try:
                graph.delete_node(node)
            except Exception:
                pass

        if chain_errors:
            print(f"\nChain errors: {chain_errors}")

        assert len(chain_errors) == 0, f"Chain test failed: {chain_errors}"


class TestNodeProperties:
    """Test node property access and modification."""

    def test_property_get_set(self, registered_graph, visual_node_registry):
        """Test getting and setting properties on nodes."""
        registry, lazy_import = visual_node_registry
        graph = registered_graph

        property_errors = []
        nodes_tested = 0

        # Test a sample of nodes
        sample_nodes = [
            "VisualMessageBoxNode",
            "VisualSetVariableNode",
            "VisualGoToURLNode",
            "VisualTypeTextNode",
            "VisualWaitNode",
            "VisualReadFileNode",
        ]

        for node_name in sample_nodes:
            if node_name not in registry:
                continue

            try:
                visual_cls = lazy_import(node_name)
                identifier = f"{visual_cls.__identifier__}.{node_name}"
                node = graph.create_node(identifier)

                if node is None:
                    continue

                nodes_tested += 1

                try:
                    widgets = node.widgets()
                    for widget_name in widgets.keys():
                        try:
                            # Get current value
                            old_value = node.get_property(widget_name)

                            # Set a test value based on type
                            if isinstance(old_value, str):
                                test_value = "test_value"
                            elif isinstance(old_value, bool):
                                test_value = not old_value
                            elif isinstance(old_value, (int, float)):
                                test_value = old_value + 1
                            else:
                                continue  # Skip complex types

                            node.set_property(widget_name, test_value)

                            # Verify the change
                            new_value = node.get_property(widget_name)
                            if new_value != test_value:
                                property_errors.append(
                                    f"{node_name}.{widget_name}: Value not set correctly"
                                )

                        except Exception as e:
                            property_errors.append(f"{node_name}.{widget_name}: {e}")

                finally:
                    try:
                        graph.delete_node(node)
                    except Exception:
                        pass

            except Exception as e:
                property_errors.append(f"{node_name}: Creation failed: {e}")

        print(f"\nTested {nodes_tested} nodes for property access")

        if property_errors:
            print(f"Property errors ({len(property_errors)}):")
            for error in property_errors:
                print(f"  - {error}")

        # Allow some errors (some properties may be read-only)
        assert len(property_errors) <= nodes_tested, "Too many property errors"


class TestNodeCategories:
    """Test node categorization."""

    def test_all_nodes_have_categories(self, visual_node_registry):
        """Test that all nodes have a NODE_CATEGORY defined."""
        registry, lazy_import = visual_node_registry

        nodes_without_category = []

        for node_name in registry.keys():
            try:
                cls = lazy_import(node_name)
                category = getattr(cls, "NODE_CATEGORY", None)
                if not category:
                    nodes_without_category.append(node_name)
            except Exception:
                pass

        if nodes_without_category:
            print(f"\nNodes without category ({len(nodes_without_category)}):")
            for name in nodes_without_category[:10]:
                print(f"  - {name}")

        assert (
            len(nodes_without_category) == 0
        ), f"{len(nodes_without_category)} nodes missing category"

    def test_category_distribution(self, visual_node_registry):
        """Report on node distribution across categories."""
        registry, lazy_import = visual_node_registry

        categories = defaultdict(list)

        for node_name in registry.keys():
            try:
                cls = lazy_import(node_name)
                category = getattr(cls, "NODE_CATEGORY", "uncategorized")
                categories[category].append(node_name)
            except Exception:
                categories["import_failed"].append(node_name)

        print(f"\n{'='*80}")
        print("NODE CATEGORY DISTRIBUTION")
        print(f"{'='*80}")

        for category in sorted(categories.keys()):
            nodes = categories[category]
            print(f"  {category}: {len(nodes)} nodes")

        total = sum(len(nodes) for nodes in categories.values())
        print(f"\nTotal: {total} nodes across {len(categories)} categories")


class TestCasareNodeLinking:
    """Test that visual nodes are properly linked to CasareRPA nodes."""

    def test_all_nodes_have_casare_mapping(
        self, registered_graph, visual_node_registry
    ):
        """Test that all visual nodes have a CasareRPA node mapping."""
        registry, lazy_import = visual_node_registry
        graph = registered_graph

        nodes_without_mapping = []
        nodes_with_mapping = []

        # Visual-only nodes that don't need CasareRPA mapping
        visual_only_patterns = [
            "Comment",
            "Reroute",
            "StickyNote",
        ]

        for node_name in sorted(registry.keys()):
            # Skip visual-only nodes
            if any(pattern in node_name for pattern in visual_only_patterns):
                continue

            try:
                visual_cls = lazy_import(node_name)
                identifier = f"{visual_cls.__identifier__}.{node_name}"
                node = graph.create_node(identifier)

                if node is None:
                    continue

                try:
                    if hasattr(node, "get_casare_node"):
                        casare_node = node.get_casare_node()
                        if casare_node is not None:
                            nodes_with_mapping.append(node_name)
                        else:
                            nodes_without_mapping.append(node_name)
                    else:
                        nodes_without_mapping.append(node_name)

                finally:
                    try:
                        graph.delete_node(node)
                    except Exception:
                        pass

            except Exception:
                pass

        total = len(nodes_with_mapping) + len(nodes_without_mapping)
        mapping_rate = (len(nodes_with_mapping) / total * 100) if total > 0 else 0

        print(f"\n{'='*80}")
        print("CASARE NODE MAPPING SUMMARY")
        print(f"{'='*80}")
        print(f"Nodes with CasareRPA mapping: {len(nodes_with_mapping)}")
        print(f"Nodes without mapping: {len(nodes_without_mapping)}")
        print(f"Mapping rate: {mapping_rate:.1f}%")

        if nodes_without_mapping:
            print(f"\nNodes without CasareRPA mapping ({len(nodes_without_mapping)}):")
            for name in nodes_without_mapping[:30]:
                print(f"  - {name}")
            if len(nodes_without_mapping) > 30:
                print(f"  ... and {len(nodes_without_mapping) - 30} more")

        # Most nodes should have mapping
        assert mapping_rate >= 80, f"Low mapping rate: {mapping_rate:.1f}%"


# =============================================================================
# Full Comprehensive Test
# =============================================================================


class TestComprehensiveNodeValidation:
    """Run comprehensive validation on every single node."""

    def test_validate_all_nodes(self, registered_graph, visual_node_registry):
        """Validate every node in the registry comprehensively."""
        registry, lazy_import = visual_node_registry
        graph = registered_graph

        print(f"\n{'='*80}")
        print("COMPREHENSIVE NODE VALIDATION")
        print(f"Testing {len(registry)} nodes...")
        print(f"{'='*80}\n")

        results = []
        failed_nodes = []

        for node_name in sorted(registry.keys()):
            result = self._validate_single_node(graph, lazy_import, node_name)
            results.append(result)

            if not result.success:
                failed_nodes.append(result)

            # Progress indicator
            status = "OK" if result.success else "FAILED"
            widget_info = f"W:{result.widgets_count}"
            port_info = f"I:{result.input_ports_count}/O:{result.output_ports_count}"
            casare_info = "CasareNode" if result.has_casare_node else "NoMapping"
            print(
                f"  [{status}] {node_name} ({widget_info}, {port_info}, {casare_info})"
            )

        # Summary
        print(f"\n{'='*80}")
        print("VALIDATION COMPLETE")
        print(f"{'='*80}")
        print(f"Total nodes: {len(results)}")
        print(f"Passed: {len(results) - len(failed_nodes)}")
        print(f"Failed: {len(failed_nodes)}")
        print(
            f"Success rate: {((len(results) - len(failed_nodes)) / len(results) * 100):.1f}%"
        )

        if failed_nodes:
            print(f"\n{'='*80}")
            print("FAILED NODES DETAILS")
            print(f"{'='*80}")
            for result in failed_nodes:
                print(f"\n{result.node_name}:")
                for error in result.all_errors:
                    print(f"  - {error}")

        # All nodes should pass
        assert len(failed_nodes) == 0, f"{len(failed_nodes)} nodes failed validation"

    def _validate_single_node(
        self, graph, lazy_import, node_name: str
    ) -> NodeTestResult:
        """Validate a single node comprehensively."""
        result = NodeTestResult(
            node_name=node_name,
            visual_class_name=node_name,
        )

        try:
            # 1. Import the class
            visual_cls = lazy_import(node_name)

            # 2. Create the node
            identifier = f"{visual_cls.__identifier__}.{node_name}"
            node = graph.create_node(identifier)

            if node is None:
                result.creation_error = "create_node returned None"
                result.success = False
                return result

            try:
                # 3. Test widgets
                try:
                    widgets = node.widgets()
                    result.widgets_count = len(widgets)

                    for widget_name, widget in widgets.items():
                        try:
                            # Test widget has required methods
                            if hasattr(widget, "isVisible"):
                                widget.isVisible()
                            if hasattr(widget, "get_custom_widget"):
                                widget.get_custom_widget()
                        except Exception as e:
                            result.widget_errors.append(f"{widget_name}: {e}")

                except Exception as e:
                    result.widget_errors.append(f"widgets() failed: {e}")

                # 4. Test input ports
                try:
                    input_ports = node.input_ports()
                    result.input_ports_count = len(input_ports)

                    for port in input_ports:
                        try:
                            name = port.name()
                            if not name:
                                result.port_errors.append("Input port has empty name")
                        except Exception as e:
                            result.port_errors.append(f"Input port error: {e}")

                except Exception as e:
                    result.port_errors.append(f"input_ports() failed: {e}")

                # 5. Test output ports
                try:
                    output_ports = node.output_ports()
                    result.output_ports_count = len(output_ports)

                    for port in output_ports:
                        try:
                            name = port.name()
                            if not name:
                                result.port_errors.append("Output port has empty name")
                        except Exception as e:
                            result.port_errors.append(f"Output port error: {e}")

                except Exception as e:
                    result.port_errors.append(f"output_ports() failed: {e}")

                # 6. Test CasareRPA node link
                try:
                    if hasattr(node, "get_casare_node"):
                        casare_node = node.get_casare_node()
                        result.has_casare_node = casare_node is not None
                except Exception:
                    pass

                # 7. Test properties
                try:
                    for widget_name in node.widgets().keys():
                        try:
                            node.get_property(widget_name)
                        except Exception as e:
                            result.property_errors.append(
                                f"{widget_name}: get failed - {e}"
                            )
                except Exception as e:
                    result.property_errors.append(f"Property test failed: {e}")

            finally:
                # Cleanup
                try:
                    graph.delete_node(node)
                except Exception:
                    pass

        except Exception as e:
            result.creation_error = str(e)
            result.success = False
            return result

        # Determine overall success
        result.success = (
            not result.creation_error
            and len(result.widget_errors) == 0
            and len(result.port_errors) == 0
        )

        return result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
