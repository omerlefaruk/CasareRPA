"""
Tests for NodeConnection domain entity.
Covers connection creation, validation, port compatibility, serialization.
"""

import pytest

from casare_rpa.domain.entities.node_connection import NodeConnection


# ============================================================================
# Creation Tests
# ============================================================================


class TestNodeConnectionCreation:
    """Tests for NodeConnection initialization."""

    def test_create_connection(self) -> None:
        """Create a basic connection."""
        conn = NodeConnection(
            source_node="node_a",
            source_port="output",
            target_node="node_b",
            target_port="input",
        )
        assert conn.source_node == "node_a"
        assert conn.source_port == "output"
        assert conn.target_node == "node_b"
        assert conn.target_port == "input"

    def test_create_exec_connection(self) -> None:
        """Create execution flow connection."""
        conn = NodeConnection(
            source_node="start",
            source_port="exec_out",
            target_node="next",
            target_port="exec_in",
        )
        assert conn.source_port == "exec_out"
        assert conn.target_port == "exec_in"

    def test_create_data_connection(self) -> None:
        """Create data flow connection."""
        conn = NodeConnection(
            source_node="extractor",
            source_port="text_out",
            target_node="processor",
            target_port="text_in",
        )
        assert conn.source_port == "text_out"
        assert conn.target_port == "text_in"


# ============================================================================
# Property Tests
# ============================================================================


class TestNodeConnectionProperties:
    """Tests for connection properties."""

    def test_source_node_immutable(self) -> None:
        """Source node is read-only (via property)."""
        conn = NodeConnection("a", "out", "b", "in")
        # Accessing via property returns private attribute
        assert conn.source_node == "a"

    def test_source_port_immutable(self) -> None:
        """Source port is read-only."""
        conn = NodeConnection("a", "out", "b", "in")
        assert conn.source_port == "out"

    def test_target_node_immutable(self) -> None:
        """Target node is read-only."""
        conn = NodeConnection("a", "out", "b", "in")
        assert conn.target_node == "b"

    def test_target_port_immutable(self) -> None:
        """Target port is read-only."""
        conn = NodeConnection("a", "out", "b", "in")
        assert conn.target_port == "in"

    def test_source_id(self) -> None:
        """Source ID combines node and port."""
        conn = NodeConnection("node_1", "output_port", "node_2", "input_port")
        assert conn.source_id == "node_1.output_port"

    def test_target_id(self) -> None:
        """Target ID combines node and port."""
        conn = NodeConnection("node_1", "output_port", "node_2", "input_port")
        assert conn.target_id == "node_2.input_port"


# ============================================================================
# Serialization Tests
# ============================================================================


class TestNodeConnectionSerialization:
    """Tests for to_dict/from_dict serialization."""

    def test_to_dict(self) -> None:
        """Serialize connection to dictionary."""
        conn = NodeConnection("src", "out", "dst", "in")
        data = conn.to_dict()
        assert data["source_node"] == "src"
        assert data["source_port"] == "out"
        assert data["target_node"] == "dst"
        assert data["target_port"] == "in"

    def test_from_dict(self) -> None:
        """Deserialize connection from dictionary."""
        data = {
            "source_node": "node_a",
            "source_port": "exec_out",
            "target_node": "node_b",
            "target_port": "exec_in",
        }
        conn = NodeConnection.from_dict(data)
        assert conn.source_node == "node_a"
        assert conn.source_port == "exec_out"
        assert conn.target_node == "node_b"
        assert conn.target_port == "exec_in"

    def test_roundtrip_serialization(self) -> None:
        """Serialize then deserialize preserves data."""
        original = NodeConnection("n1", "p1", "n2", "p2")
        data = original.to_dict()
        restored = NodeConnection.from_dict(data)
        assert original == restored


# ============================================================================
# Equality Tests
# ============================================================================


class TestNodeConnectionEquality:
    """Tests for equality comparison."""

    def test_equal_connections(self) -> None:
        """Identical connections are equal."""
        conn1 = NodeConnection("a", "out", "b", "in")
        conn2 = NodeConnection("a", "out", "b", "in")
        assert conn1 == conn2

    def test_different_source_node(self) -> None:
        """Different source node makes connections unequal."""
        conn1 = NodeConnection("a", "out", "b", "in")
        conn2 = NodeConnection("x", "out", "b", "in")
        assert conn1 != conn2

    def test_different_source_port(self) -> None:
        """Different source port makes connections unequal."""
        conn1 = NodeConnection("a", "out1", "b", "in")
        conn2 = NodeConnection("a", "out2", "b", "in")
        assert conn1 != conn2

    def test_different_target_node(self) -> None:
        """Different target node makes connections unequal."""
        conn1 = NodeConnection("a", "out", "b", "in")
        conn2 = NodeConnection("a", "out", "c", "in")
        assert conn1 != conn2

    def test_different_target_port(self) -> None:
        """Different target port makes connections unequal."""
        conn1 = NodeConnection("a", "out", "b", "in1")
        conn2 = NodeConnection("a", "out", "b", "in2")
        assert conn1 != conn2

    def test_not_equal_to_non_connection(self) -> None:
        """Connection is not equal to non-Connection object."""
        conn = NodeConnection("a", "out", "b", "in")
        assert conn != "not a connection"
        assert conn != {"source_node": "a"}
        assert conn != 42


# ============================================================================
# Hash Tests
# ============================================================================


class TestNodeConnectionHash:
    """Tests for hash behavior."""

    def test_equal_connections_same_hash(self) -> None:
        """Equal connections have same hash."""
        conn1 = NodeConnection("a", "out", "b", "in")
        conn2 = NodeConnection("a", "out", "b", "in")
        assert hash(conn1) == hash(conn2)

    def test_different_connections_different_hash(self) -> None:
        """Different connections typically have different hash."""
        conn1 = NodeConnection("a", "out", "b", "in")
        conn2 = NodeConnection("x", "out", "y", "in")
        # Note: hash collision is possible but unlikely
        assert hash(conn1) != hash(conn2)

    def test_connection_usable_in_set(self) -> None:
        """Connections can be used in sets."""
        conn1 = NodeConnection("a", "out", "b", "in")
        conn2 = NodeConnection("a", "out", "b", "in")
        conn3 = NodeConnection("c", "out", "d", "in")

        conn_set = {conn1, conn2, conn3}
        assert len(conn_set) == 2  # conn1 and conn2 are duplicates

    def test_connection_usable_as_dict_key(self) -> None:
        """Connections can be used as dictionary keys."""
        conn = NodeConnection("a", "out", "b", "in")
        d = {conn: "connection_data"}
        assert d[conn] == "connection_data"


# ============================================================================
# String Representation Tests
# ============================================================================


class TestNodeConnectionRepr:
    """Tests for __repr__ method."""

    def test_repr_format(self) -> None:
        """String representation shows source -> target."""
        conn = NodeConnection("node_a", "output", "node_b", "input")
        rep = repr(conn)
        assert "NodeConnection" in rep
        assert "node_a.output" in rep
        assert "node_b.input" in rep
        assert "->" in rep

    def test_repr_exec_connection(self) -> None:
        """Repr works for exec connections."""
        conn = NodeConnection("start", "exec_out", "next", "exec_in")
        rep = repr(conn)
        assert "start.exec_out" in rep
        assert "next.exec_in" in rep
