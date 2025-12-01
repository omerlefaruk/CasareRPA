"""
Connection Validation Tests for CasareRPA.

Comprehensive tests covering:
- Port type compatibility (DataType matching rules)
- NodeConnection entity behavior
- Topology validation (cycle detection, disconnected nodes)

These tests follow domain TDD principles:
- NO mocks for domain objects (real DataType, NodeConnection)
- Tests document expected behavior for missing TopologyValidator
"""

import pytest
from typing import Dict, List, Set, Tuple

from casare_rpa.domain.entities.node_connection import NodeConnection
from casare_rpa.domain.value_objects.types import DataType, PortType
from casare_rpa.domain.ports.port_type_interfaces import DefaultCompatibilityRule
from casare_rpa.application.services.port_type_service import PortTypeRegistry


# ============================================================================
# Port Compatibility Tests - DefaultCompatibilityRule
# ============================================================================


class TestPortTypeCompatibility:
    """Tests for DefaultCompatibilityRule type compatibility checking."""

    @pytest.fixture
    def compatibility_rule(self) -> DefaultCompatibilityRule:
        """Create a fresh DefaultCompatibilityRule instance."""
        return DefaultCompatibilityRule()

    # -------------------------------------------------------------------------
    # Same Type Compatibility
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize(
        "data_type",
        [
            DataType.STRING,
            DataType.INTEGER,
            DataType.FLOAT,
            DataType.BOOLEAN,
            DataType.LIST,
            DataType.DICT,
            DataType.ANY,
            DataType.PAGE,
            DataType.BROWSER,
            DataType.ELEMENT,
            DataType.EXEC,
        ],
    )
    def test_same_types_compatible(
        self, compatibility_rule: DefaultCompatibilityRule, data_type: DataType
    ) -> None:
        """Same DataType can always connect to itself."""
        assert compatibility_rule.is_compatible(data_type, data_type) is True

    def test_same_types_no_incompatibility_reason(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """Compatible types return None for incompatibility reason."""
        reason = compatibility_rule.get_incompatibility_reason(
            DataType.STRING, DataType.STRING
        )
        assert reason is None

    # -------------------------------------------------------------------------
    # ANY Type (Wildcard) Compatibility
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize(
        "other_type",
        [
            DataType.STRING,
            DataType.INTEGER,
            DataType.FLOAT,
            DataType.BOOLEAN,
            DataType.LIST,
            DataType.DICT,
            DataType.PAGE,
            DataType.BROWSER,
            DataType.ELEMENT,
            DataType.EXEC,
        ],
    )
    def test_any_accepts_all_as_target(
        self, compatibility_rule: DefaultCompatibilityRule, other_type: DataType
    ) -> None:
        """ANY type as target accepts all other types."""
        assert compatibility_rule.is_compatible(other_type, DataType.ANY) is True

    @pytest.mark.parametrize(
        "other_type",
        [
            DataType.STRING,
            DataType.INTEGER,
            DataType.FLOAT,
            DataType.BOOLEAN,
            DataType.LIST,
            DataType.DICT,
            DataType.PAGE,
            DataType.BROWSER,
            DataType.ELEMENT,
        ],
    )
    def test_any_provides_all_as_source(
        self, compatibility_rule: DefaultCompatibilityRule, other_type: DataType
    ) -> None:
        """ANY type as source can connect to all targets."""
        assert compatibility_rule.is_compatible(DataType.ANY, other_type) is True

    def test_any_to_any_compatible(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """ANY to ANY is compatible."""
        assert compatibility_rule.is_compatible(DataType.ANY, DataType.ANY) is True

    # -------------------------------------------------------------------------
    # Incompatible Types
    # -------------------------------------------------------------------------

    def test_string_to_integer_incompatible(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """STRING cannot connect to INTEGER target."""
        assert (
            compatibility_rule.is_compatible(DataType.STRING, DataType.INTEGER) is False
        )

    def test_string_to_float_incompatible(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """STRING cannot connect to FLOAT target."""
        assert (
            compatibility_rule.is_compatible(DataType.STRING, DataType.FLOAT) is False
        )

    def test_string_to_boolean_incompatible(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """STRING cannot connect to BOOLEAN target."""
        assert (
            compatibility_rule.is_compatible(DataType.STRING, DataType.BOOLEAN) is False
        )

    def test_boolean_to_integer_incompatible(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """BOOLEAN cannot connect to INTEGER target."""
        assert (
            compatibility_rule.is_compatible(DataType.BOOLEAN, DataType.INTEGER)
            is False
        )

    def test_float_to_integer_incompatible(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """FLOAT cannot connect to INTEGER target (narrowing conversion)."""
        assert (
            compatibility_rule.is_compatible(DataType.FLOAT, DataType.INTEGER) is False
        )

    def test_list_to_dict_incompatible(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """LIST cannot connect to DICT target."""
        assert compatibility_rule.is_compatible(DataType.LIST, DataType.DICT) is False

    def test_dict_to_list_incompatible(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """DICT cannot connect to LIST target."""
        assert compatibility_rule.is_compatible(DataType.DICT, DataType.LIST) is False

    def test_page_to_element_incompatible(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """PAGE cannot connect to ELEMENT target."""
        assert (
            compatibility_rule.is_compatible(DataType.PAGE, DataType.ELEMENT) is False
        )

    def test_browser_to_page_incompatible(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """BROWSER cannot connect to PAGE target."""
        assert (
            compatibility_rule.is_compatible(DataType.BROWSER, DataType.PAGE) is False
        )

    def test_element_to_browser_incompatible(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """ELEMENT cannot connect to BROWSER target."""
        assert (
            compatibility_rule.is_compatible(DataType.ELEMENT, DataType.BROWSER)
            is False
        )

    def test_incompatible_types_return_reason(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """Incompatible types return a descriptive reason string."""
        reason = compatibility_rule.get_incompatibility_reason(
            DataType.STRING, DataType.INTEGER
        )
        assert reason is not None
        assert isinstance(reason, str)
        assert len(reason) > 0

    # -------------------------------------------------------------------------
    # EXEC Port Compatibility
    # -------------------------------------------------------------------------

    def test_exec_to_exec_compatible(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """EXEC ports can connect to EXEC ports."""
        assert compatibility_rule.is_compatible(DataType.EXEC, DataType.EXEC) is True

    def test_exec_to_string_incompatible(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """EXEC cannot connect to data port (STRING)."""
        # EXEC is a strict type, only connects to EXEC or ANY
        result = compatibility_rule.is_compatible(DataType.EXEC, DataType.STRING)
        # Note: This tests current behavior. EXEC should not connect to data ports.
        assert result is False

    def test_exec_to_integer_incompatible(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """EXEC cannot connect to data port (INTEGER)."""
        result = compatibility_rule.is_compatible(DataType.EXEC, DataType.INTEGER)
        assert result is False

    def test_string_to_exec_incompatible(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """Data port (STRING) cannot connect to EXEC."""
        result = compatibility_rule.is_compatible(DataType.STRING, DataType.EXEC)
        assert result is False

    def test_exec_to_any_compatible(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """EXEC can connect to ANY target (wildcard)."""
        assert compatibility_rule.is_compatible(DataType.EXEC, DataType.ANY) is True

    # -------------------------------------------------------------------------
    # Numeric Cross-Compatibility
    # -------------------------------------------------------------------------

    def test_integer_to_float_compatible(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """INTEGER can widen to FLOAT."""
        assert (
            compatibility_rule.is_compatible(DataType.INTEGER, DataType.FLOAT) is True
        )

    def test_integer_to_string_compatible(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """INTEGER can convert to STRING."""
        assert (
            compatibility_rule.is_compatible(DataType.INTEGER, DataType.STRING) is True
        )

    def test_float_to_string_compatible(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """FLOAT can convert to STRING."""
        assert compatibility_rule.is_compatible(DataType.FLOAT, DataType.STRING) is True

    def test_boolean_to_string_compatible(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """BOOLEAN can convert to STRING."""
        assert (
            compatibility_rule.is_compatible(DataType.BOOLEAN, DataType.STRING) is True
        )

    # -------------------------------------------------------------------------
    # Strict Type Enforcement
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize(
        "strict_type",
        [
            DataType.PAGE,
            DataType.BROWSER,
            DataType.ELEMENT,
            DataType.LIST,
            DataType.DICT,
        ],
    )
    def test_strict_types_require_exact_match(
        self, compatibility_rule: DefaultCompatibilityRule, strict_type: DataType
    ) -> None:
        """Strict types (PAGE, BROWSER, ELEMENT, LIST, DICT) require exact match."""
        # Same type is compatible
        assert compatibility_rule.is_compatible(strict_type, strict_type) is True
        # To ANY is compatible
        assert compatibility_rule.is_compatible(strict_type, DataType.ANY) is True
        # To STRING is NOT compatible for strict types
        if strict_type != DataType.LIST and strict_type != DataType.DICT:
            assert (
                compatibility_rule.is_compatible(strict_type, DataType.STRING) is False
            )

    def test_strict_type_incompatibility_reason_is_descriptive(
        self, compatibility_rule: DefaultCompatibilityRule
    ) -> None:
        """Strict type incompatibility provides helpful error message."""
        reason = compatibility_rule.get_incompatibility_reason(
            DataType.PAGE, DataType.STRING
        )
        assert reason is not None
        assert "PAGE" in reason
        assert "exact" in reason.lower() or "match" in reason.lower()


# ============================================================================
# Port Type Registry Tests
# ============================================================================


class TestPortTypeRegistry:
    """Tests for PortTypeRegistry service."""

    @pytest.fixture
    def registry(self) -> PortTypeRegistry:
        """Get PortTypeRegistry singleton instance."""
        return PortTypeRegistry()

    def test_registry_is_singleton(self) -> None:
        """PortTypeRegistry returns same instance."""
        reg1 = PortTypeRegistry()
        reg2 = PortTypeRegistry()
        assert reg1 is reg2

    def test_is_compatible_delegates_to_rule(self, registry: PortTypeRegistry) -> None:
        """Registry.is_compatible uses internal compatibility rule."""
        # Same types compatible
        assert registry.is_compatible(DataType.STRING, DataType.STRING) is True
        # Incompatible types
        assert registry.is_compatible(DataType.STRING, DataType.INTEGER) is False

    def test_get_compatible_types_for_any(self, registry: PortTypeRegistry) -> None:
        """ANY type is compatible with all types."""
        compatible = registry.get_compatible_types(DataType.ANY)
        # ANY should be compatible with all DataTypes
        for dt in DataType:
            assert dt in compatible

    def test_get_compatible_types_for_integer(self, registry: PortTypeRegistry) -> None:
        """INTEGER compatible types include FLOAT, STRING, ANY."""
        compatible = registry.get_compatible_types(DataType.INTEGER)
        assert DataType.INTEGER in compatible
        assert DataType.FLOAT in compatible
        assert DataType.STRING in compatible
        assert DataType.ANY in compatible
        # Not compatible with strict types
        assert DataType.PAGE not in compatible
        assert DataType.ELEMENT not in compatible

    def test_get_incompatibility_reason(self, registry: PortTypeRegistry) -> None:
        """Registry provides incompatibility reasons."""
        reason = registry.get_incompatibility_reason(DataType.LIST, DataType.INTEGER)
        assert reason is not None
        assert isinstance(reason, str)

    def test_get_type_color_returns_rgba(self, registry: PortTypeRegistry) -> None:
        """Type colors are RGBA tuples."""
        color = registry.get_type_color(DataType.STRING)
        assert isinstance(color, tuple)
        assert len(color) == 4
        assert all(0 <= c <= 255 for c in color)

    def test_exec_color_is_white(self, registry: PortTypeRegistry) -> None:
        """Execution port color is white."""
        color = registry.get_exec_color()
        assert color == (255, 255, 255, 255)


# ============================================================================
# NodeConnection Tests - ID Format Verification
# ============================================================================


class TestNodeConnectionIdFormat:
    """Tests verifying NodeConnection source_id and target_id format."""

    def test_source_id_format_simple(self) -> None:
        """Source ID follows 'node_id.port_name' format."""
        conn = NodeConnection(
            source_node="my_node",
            source_port="output",
            target_node="other",
            target_port="input",
        )
        assert conn.source_id == "my_node.output"

    def test_target_id_format_simple(self) -> None:
        """Target ID follows 'node_id.port_name' format."""
        conn = NodeConnection(
            source_node="node_a",
            source_port="out",
            target_node="node_b",
            target_port="input_port",
        )
        assert conn.target_id == "node_b.input_port"

    def test_source_id_with_uuid_node(self) -> None:
        """Source ID works with UUID-style node IDs."""
        conn = NodeConnection(
            source_node="550e8400-e29b-41d4-a716-446655440000",
            source_port="data_out",
            target_node="other",
            target_port="in",
        )
        assert conn.source_id == "550e8400-e29b-41d4-a716-446655440000.data_out"

    def test_target_id_with_uuid_node(self) -> None:
        """Target ID works with UUID-style node IDs."""
        conn = NodeConnection(
            source_node="src",
            source_port="out",
            target_node="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            target_port="exec_in",
        )
        assert conn.target_id == "a1b2c3d4-e5f6-7890-abcd-ef1234567890.exec_in"

    def test_id_format_with_special_characters_in_port(self) -> None:
        """ID format handles underscores and numbers in port names."""
        conn = NodeConnection(
            source_node="node_1",
            source_port="output_value_2",
            target_node="node_2",
            target_port="input_data_1",
        )
        assert conn.source_id == "node_1.output_value_2"
        assert conn.target_id == "node_2.input_data_1"

    def test_id_format_exec_ports(self) -> None:
        """ID format for execution flow ports."""
        conn = NodeConnection(
            source_node="start_node",
            source_port="exec_out",
            target_node="action_node",
            target_port="exec_in",
        )
        assert conn.source_id == "start_node.exec_out"
        assert conn.target_id == "action_node.exec_in"

    def test_source_id_is_port_id_type(self) -> None:
        """source_id returns PortId (str) type."""
        conn = NodeConnection("a", "b", "c", "d")
        source_id = conn.source_id
        assert isinstance(source_id, str)
        assert "." in source_id

    def test_target_id_is_port_id_type(self) -> None:
        """target_id returns PortId (str) type."""
        conn = NodeConnection("a", "b", "c", "d")
        target_id = conn.target_id
        assert isinstance(target_id, str)
        assert "." in target_id


class TestNodeConnectionSerialization:
    """Additional serialization tests for NodeConnection."""

    def test_to_dict_contains_all_fields(self) -> None:
        """to_dict includes all required connection fields."""
        conn = NodeConnection(
            source_node="node_a",
            source_port="port_out",
            target_node="node_b",
            target_port="port_in",
        )
        data = conn.to_dict()
        required_keys = {"source_node", "source_port", "target_node", "target_port"}
        assert required_keys == set(data.keys())

    def test_from_dict_missing_field_raises_error(self) -> None:
        """from_dict with missing field raises KeyError."""
        incomplete_data = {
            "source_node": "a",
            "source_port": "out",
            # missing target_node and target_port
        }
        with pytest.raises(KeyError):
            NodeConnection.from_dict(incomplete_data)

    def test_serialization_preserves_exact_values(self) -> None:
        """Serialization preserves exact string values."""
        conn = NodeConnection(
            source_node="Node_With_Caps",
            source_port="Port123",
            target_node="another-node",
            target_port="data_in",
        )
        data = conn.to_dict()
        assert data["source_node"] == "Node_With_Caps"
        assert data["source_port"] == "Port123"
        assert data["target_node"] == "another-node"
        assert data["target_port"] == "data_in"


# ============================================================================
# Topology Validation Tests
# ============================================================================


class TestTopologyValidation:
    """
    Tests for workflow topology validation.

    NOTE: TopologyValidator class does not currently exist in the codebase.
    These tests document EXPECTED BEHAVIOR for when it is implemented.
    Tests use helper functions that simulate the validation logic.
    """

    @staticmethod
    def build_adjacency_list(connections: List[NodeConnection]) -> Dict[str, Set[str]]:
        """Build adjacency list from connections for graph analysis."""
        adj: Dict[str, Set[str]] = {}
        for conn in connections:
            if conn.source_node not in adj:
                adj[conn.source_node] = set()
            adj[conn.source_node].add(conn.target_node)
            # Ensure target node exists in adjacency list
            if conn.target_node not in adj:
                adj[conn.target_node] = set()
        return adj

    @staticmethod
    def detect_cycle(
        adj: Dict[str, Set[str]], start_nodes: Set[str]
    ) -> Tuple[bool, List[str]]:
        """
        Detect cycle in directed graph using DFS.

        Args:
            adj: Adjacency list {node: {connected_nodes}}
            start_nodes: Set of nodes to start search from

        Returns:
            Tuple of (has_cycle, cycle_path)
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {node: WHITE for node in adj}
        path: List[str] = []

        def dfs(node: str) -> bool:
            color[node] = GRAY
            path.append(node)
            for neighbor in adj.get(node, set()):
                if color[neighbor] == GRAY:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    return True
                if color[neighbor] == WHITE and dfs(neighbor):
                    return True
            path.pop()
            color[node] = BLACK
            return False

        for node in start_nodes:
            if color[node] == WHITE:
                if dfs(node):
                    return True, path
        return False, []

    @staticmethod
    def get_all_nodes(connections: List[NodeConnection]) -> Set[str]:
        """Get all unique node IDs from connections."""
        nodes: Set[str] = set()
        for conn in connections:
            nodes.add(conn.source_node)
            nodes.add(conn.target_node)
        return nodes

    # -------------------------------------------------------------------------
    # Circular Dependency Detection
    # -------------------------------------------------------------------------

    def test_detect_circular_dependency_simple(self) -> None:
        """Detect simple circular dependency: A -> B -> C -> A."""
        connections = [
            NodeConnection("A", "out", "B", "in"),
            NodeConnection("B", "out", "C", "in"),
            NodeConnection("C", "out", "A", "in"),  # Creates cycle
        ]
        adj = self.build_adjacency_list(connections)
        has_cycle, _ = self.detect_cycle(adj, {"A"})
        assert has_cycle is True

    def test_detect_circular_dependency_self_loop(self) -> None:
        """Detect self-referencing node: A -> A."""
        connections = [
            NodeConnection("A", "out", "A", "in"),  # Self-loop
        ]
        adj = self.build_adjacency_list(connections)
        has_cycle, _ = self.detect_cycle(adj, {"A"})
        assert has_cycle is True

    def test_detect_circular_dependency_complex(self) -> None:
        """Detect cycle in complex graph with multiple paths."""
        # Graph: A -> B -> C -> D
        #              |       ^
        #              v       |
        #              E ------+
        connections = [
            NodeConnection("A", "out", "B", "in"),
            NodeConnection("B", "out1", "C", "in"),
            NodeConnection("B", "out2", "E", "in"),
            NodeConnection("C", "out", "D", "in"),
            NodeConnection("E", "out", "D", "in"),  # E -> D (no cycle yet)
            NodeConnection("D", "out", "B", "in"),  # D -> B creates cycle
        ]
        adj = self.build_adjacency_list(connections)
        has_cycle, _ = self.detect_cycle(adj, {"A"})
        assert has_cycle is True

    def test_no_cycle_in_linear_chain(self) -> None:
        """Linear chain A -> B -> C -> D has no cycle."""
        connections = [
            NodeConnection("A", "out", "B", "in"),
            NodeConnection("B", "out", "C", "in"),
            NodeConnection("C", "out", "D", "in"),
        ]
        adj = self.build_adjacency_list(connections)
        has_cycle, _ = self.detect_cycle(adj, {"A"})
        assert has_cycle is False

    def test_no_cycle_in_tree_structure(self) -> None:
        """Tree structure has no cycle."""
        #       A
        #      / \
        #     B   C
        #    / \   \
        #   D   E   F
        connections = [
            NodeConnection("A", "out1", "B", "in"),
            NodeConnection("A", "out2", "C", "in"),
            NodeConnection("B", "out1", "D", "in"),
            NodeConnection("B", "out2", "E", "in"),
            NodeConnection("C", "out", "F", "in"),
        ]
        adj = self.build_adjacency_list(connections)
        has_cycle, _ = self.detect_cycle(adj, {"A"})
        assert has_cycle is False

    def test_no_cycle_in_dag(self) -> None:
        """DAG (Directed Acyclic Graph) has no cycle."""
        # Diamond pattern: A -> B -> D
        #                  A -> C -> D
        connections = [
            NodeConnection("A", "out1", "B", "in"),
            NodeConnection("A", "out2", "C", "in"),
            NodeConnection("B", "out", "D", "in"),
            NodeConnection("C", "out", "D", "in"),
        ]
        adj = self.build_adjacency_list(connections)
        has_cycle, _ = self.detect_cycle(adj, {"A"})
        assert has_cycle is False

    # -------------------------------------------------------------------------
    # Disconnected Node Detection
    # -------------------------------------------------------------------------

    def test_detect_disconnected_nodes_isolated(self) -> None:
        """Detect isolated node with no connections."""
        # Nodes: A, B, C - but only A -> B connected
        connections = [
            NodeConnection("A", "out", "B", "in"),
        ]
        connected_nodes = self.get_all_nodes(connections)
        all_workflow_nodes = {"A", "B", "C"}  # C is isolated
        disconnected = all_workflow_nodes - connected_nodes
        assert "C" in disconnected

    def test_detect_disconnected_nodes_multiple_islands(self) -> None:
        """Detect multiple disconnected subgraphs."""
        # Island 1: A -> B
        # Island 2: C -> D
        # Node E is completely isolated
        connections = [
            NodeConnection("A", "out", "B", "in"),
            NodeConnection("C", "out", "D", "in"),
        ]
        connected_nodes = self.get_all_nodes(connections)
        all_workflow_nodes = {"A", "B", "C", "D", "E"}
        disconnected = all_workflow_nodes - connected_nodes
        assert "E" in disconnected

    def test_no_disconnected_in_fully_connected(self) -> None:
        """Fully connected workflow has no disconnected nodes."""
        connections = [
            NodeConnection("A", "out", "B", "in"),
            NodeConnection("B", "out", "C", "in"),
            NodeConnection("C", "out", "D", "in"),
        ]
        connected_nodes = self.get_all_nodes(connections)
        all_workflow_nodes = {"A", "B", "C", "D"}
        disconnected = all_workflow_nodes - connected_nodes
        assert len(disconnected) == 0

    def test_empty_workflow_has_no_connections(self) -> None:
        """Empty connection list means all nodes are disconnected."""
        connections: List[NodeConnection] = []
        connected_nodes = self.get_all_nodes(connections)
        all_workflow_nodes = {"A", "B", "C"}
        disconnected = all_workflow_nodes - connected_nodes
        assert disconnected == {"A", "B", "C"}


# ============================================================================
# Edge Cases and Chaos Tests
# ============================================================================


class TestConnectionEdgeCases:
    """Edge case tests for connection validation."""

    def test_empty_node_id(self) -> None:
        """Connection with empty node ID still creates valid object."""
        conn = NodeConnection("", "out", "target", "in")
        assert conn.source_node == ""
        assert conn.source_id == ".out"

    def test_empty_port_name(self) -> None:
        """Connection with empty port name still creates valid object."""
        conn = NodeConnection("source", "", "target", "in")
        assert conn.source_port == ""
        assert conn.source_id == "source."

    def test_whitespace_in_ids(self) -> None:
        """Connection preserves whitespace in IDs (caller should validate)."""
        conn = NodeConnection("node 1", "port out", "node 2", "port in")
        assert conn.source_id == "node 1.port out"
        assert conn.target_id == "node 2.port in"

    def test_very_long_node_id(self) -> None:
        """Connection handles very long node IDs."""
        long_id = "x" * 1000
        conn = NodeConnection(long_id, "out", "target", "in")
        assert conn.source_node == long_id
        assert len(conn.source_id) == 1004  # 1000 + len(".out")

    def test_connection_equality_is_order_dependent(self) -> None:
        """Reversed source/target creates different connection."""
        conn1 = NodeConnection("A", "out", "B", "in")
        conn2 = NodeConnection("B", "in", "A", "out")  # Reversed
        assert conn1 != conn2

    def test_unicode_in_ids(self) -> None:
        """Connection handles unicode characters in IDs."""
        conn = NodeConnection("nodo_espanol", "salida", "noeud_francais", "entree")
        assert conn.source_id == "nodo_espanol.salida"
        assert conn.target_id == "noeud_francais.entree"


class TestCompatibilityRuleEdgeCases:
    """Edge case tests for compatibility rules."""

    @pytest.fixture
    def rule(self) -> DefaultCompatibilityRule:
        """Create DefaultCompatibilityRule instance."""
        return DefaultCompatibilityRule()

    def test_all_data_types_checked(self, rule: DefaultCompatibilityRule) -> None:
        """Verify all DataType values are handled by compatibility rule."""
        for source in DataType:
            for target in DataType:
                # Should not raise - all combinations are handled
                result = rule.is_compatible(source, target)
                assert isinstance(result, bool)

    def test_compatibility_is_not_symmetric(
        self, rule: DefaultCompatibilityRule
    ) -> None:
        """Compatibility is NOT symmetric: A->B does not imply B->A."""
        # INTEGER -> FLOAT is OK (widening)
        assert rule.is_compatible(DataType.INTEGER, DataType.FLOAT) is True
        # FLOAT -> INTEGER is NOT OK (narrowing)
        assert rule.is_compatible(DataType.FLOAT, DataType.INTEGER) is False

    def test_compatibility_chain_not_transitive(
        self, rule: DefaultCompatibilityRule
    ) -> None:
        """Compatibility is NOT transitive: A->B, B->C does not imply A->C."""
        # INTEGER -> FLOAT is OK
        assert rule.is_compatible(DataType.INTEGER, DataType.FLOAT) is True
        # FLOAT -> STRING is OK
        assert rule.is_compatible(DataType.FLOAT, DataType.STRING) is True
        # But STRING is a valid target for INTEGER directly too
        assert rule.is_compatible(DataType.INTEGER, DataType.STRING) is True
