"""
Tests for Database Connectivity nodes.

This module tests all database nodes including connection, queries,
transactions, and table operations. Uses SQLite for testing since
it's built-in and doesn't require external servers.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.core.types import NodeStatus
from casare_rpa.nodes.database_nodes import (
    DatabaseConnection,
    DatabaseConnectNode,
    ExecuteQueryNode,
    ExecuteNonQueryNode,
    BeginTransactionNode,
    CommitTransactionNode,
    RollbackTransactionNode,
    CloseDatabaseNode,
    TableExistsNode,
    GetTableColumnsNode,
    ExecuteBatchNode,
)


@pytest.fixture
def context():
    """Create a mock execution context."""
    ctx = MagicMock(spec=ExecutionContext)
    ctx.variables = {}
    ctx.get_variable = MagicMock(side_effect=lambda k, d=None: ctx.variables.get(k, d))
    ctx.set_variable = MagicMock(side_effect=lambda k, v: ctx.variables.update({k: v}))
    return ctx


@pytest.fixture
def temp_db():
    """Create a temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    try:
        os.unlink(db_path)
    except (OSError, FileNotFoundError):
        pass


@pytest.fixture
async def sqlite_connection(temp_db, context):
    """Create a SQLite connection for testing."""
    node = DatabaseConnectNode("connect_id")
    node.set_input_value("db_type", "sqlite")
    node.set_input_value("database", temp_db)

    result = await node.execute(context)
    assert result["success"] is True

    connection = node.get_output_value("connection")
    yield connection

    # Cleanup
    await connection.close()


# =============================================================================
# DatabaseConnection Tests
# =============================================================================

class TestDatabaseConnection:
    """Tests for DatabaseConnection class."""

    def test_init(self):
        """Test connection initialization."""
        conn = DatabaseConnection("sqlite", MagicMock(), ":memory:")
        assert conn.db_type == "sqlite"
        assert conn.connection_string == ":memory:"
        assert conn.in_transaction is False
        assert conn.last_results == []

    @pytest.mark.asyncio
    async def test_close(self):
        """Test connection close."""
        mock_conn = MagicMock()
        mock_conn.close = MagicMock()

        conn = DatabaseConnection("sqlite", mock_conn, ":memory:")
        await conn.close()

        mock_conn.close.assert_called_once()
        assert conn.connection is None


# =============================================================================
# DatabaseConnectNode Tests
# =============================================================================

class TestDatabaseConnectNode:
    """Tests for DatabaseConnectNode."""

    def test_init_default_config(self):
        """Test node initialization with default config."""
        node = DatabaseConnectNode("test_id")
        assert node.node_type == "DatabaseConnectNode"
        assert node.config.get("db_type") == "sqlite"
        assert node.config.get("host") == "localhost"
        assert node.config.get("port") == 5432

    def test_init_custom_config(self):
        """Test node initialization with custom config."""
        node = DatabaseConnectNode(
            "test_id",
            config={
                "db_type": "postgresql",
                "host": "db.example.com",
                "port": 5433,
            }
        )
        assert node.config.get("db_type") == "postgresql"
        assert node.config.get("host") == "db.example.com"
        assert node.config.get("port") == 5433

    def test_ports_defined(self):
        """Test that all required ports are defined."""
        node = DatabaseConnectNode("test_id")

        # Check input ports
        assert "exec_in" in node.input_ports
        assert "db_type" in node.input_ports
        assert "host" in node.input_ports
        assert "database" in node.input_ports

        # Check output ports
        assert "exec_out" in node.output_ports
        assert "connection" in node.output_ports
        assert "success" in node.output_ports
        assert "error" in node.output_ports

    @pytest.mark.asyncio
    async def test_connect_sqlite_memory(self, context):
        """Test connecting to in-memory SQLite database."""
        node = DatabaseConnectNode("test_id")
        node.set_input_value("db_type", "sqlite")
        node.set_input_value("database", ":memory:")

        result = await node.execute(context)

        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        assert node.get_output_value("success") is True

        connection = node.get_output_value("connection")
        assert connection is not None
        assert connection.db_type == "sqlite"

        # Cleanup
        await connection.close()

    @pytest.mark.asyncio
    async def test_connect_sqlite_file(self, context, temp_db):
        """Test connecting to SQLite file database."""
        node = DatabaseConnectNode("test_id")
        node.set_input_value("db_type", "sqlite")
        node.set_input_value("database", temp_db)

        result = await node.execute(context)

        assert result["success"] is True
        connection = node.get_output_value("connection")
        assert connection is not None

        # Cleanup
        await connection.close()

    @pytest.mark.asyncio
    async def test_connect_unsupported_db(self, context):
        """Test error with unsupported database type."""
        node = DatabaseConnectNode("test_id")
        node.set_input_value("db_type", "oracle")
        node.set_input_value("database", "test")

        result = await node.execute(context)

        assert result["success"] is False
        assert "Unsupported database type" in result["error"]

    @pytest.mark.asyncio
    async def test_connect_postgresql_without_driver(self, context):
        """Test PostgreSQL connection without asyncpg installed."""
        node = DatabaseConnectNode("test_id")
        node.set_input_value("db_type", "postgresql")
        node.set_input_value("host", "localhost")
        node.set_input_value("database", "test")

        # This should fail because asyncpg is likely not installed
        result = await node.execute(context)

        # Either succeeds (if asyncpg is installed) or fails with import error
        if not result["success"]:
            assert "asyncpg" in result["error"].lower() or "connection" in result["error"].lower()


# =============================================================================
# ExecuteQueryNode Tests
# =============================================================================

class TestExecuteQueryNode:
    """Tests for ExecuteQueryNode."""

    def test_init(self):
        """Test node initialization."""
        node = ExecuteQueryNode("test_id")
        assert node.node_type == "ExecuteQueryNode"

    def test_ports_defined(self):
        """Test that required ports are defined."""
        node = ExecuteQueryNode("test_id")

        assert "connection" in node.input_ports
        assert "query" in node.input_ports
        assert "parameters" in node.input_ports
        assert "results" in node.output_ports
        assert "row_count" in node.output_ports
        assert "columns" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_missing_connection(self, context):
        """Test error when connection is missing."""
        node = ExecuteQueryNode("test_id")
        node.set_input_value("query", "SELECT 1")

        result = await node.execute(context)

        assert result["success"] is False
        assert "connection is required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_missing_query(self, context, sqlite_connection):
        """Test error when query is missing."""
        node = ExecuteQueryNode("test_id")
        node.set_input_value("connection", sqlite_connection)

        result = await node.execute(context)

        assert result["success"] is False
        assert "Query is required" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_simple_query(self, context, sqlite_connection):
        """Test executing a simple SELECT query."""
        node = ExecuteQueryNode("test_id")
        node.set_input_value("connection", sqlite_connection)
        node.set_input_value("query", "SELECT 1 as num, 'hello' as text")

        result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("success") is True

        results = node.get_output_value("results")
        assert len(results) == 1
        assert results[0]["num"] == 1
        assert results[0]["text"] == "hello"

        columns = node.get_output_value("columns")
        assert "num" in columns
        assert "text" in columns

    @pytest.mark.asyncio
    async def test_execute_query_with_parameters(self, context, sqlite_connection):
        """Test executing a query with parameters."""
        # First create a table and insert data
        create_node = ExecuteNonQueryNode("create_id")
        create_node.set_input_value("connection", sqlite_connection)
        create_node.set_input_value("query", "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        await create_node.execute(context)

        insert_node = ExecuteNonQueryNode("insert_id")
        insert_node.set_input_value("connection", sqlite_connection)
        insert_node.set_input_value("query", "INSERT INTO users (name) VALUES (?)")
        insert_node.set_input_value("parameters", ["Alice"])
        await insert_node.execute(context)

        # Now query with parameters
        query_node = ExecuteQueryNode("query_id")
        query_node.set_input_value("connection", sqlite_connection)
        query_node.set_input_value("query", "SELECT * FROM users WHERE name = ?")
        query_node.set_input_value("parameters", ["Alice"])

        result = await query_node.execute(context)

        assert result["success"] is True
        results = query_node.get_output_value("results")
        assert len(results) == 1
        assert results[0]["name"] == "Alice"


# =============================================================================
# ExecuteNonQueryNode Tests
# =============================================================================

class TestExecuteNonQueryNode:
    """Tests for ExecuteNonQueryNode."""

    def test_init(self):
        """Test node initialization."""
        node = ExecuteNonQueryNode("test_id")
        assert node.node_type == "ExecuteNonQueryNode"

    def test_ports_defined(self):
        """Test that required ports are defined."""
        node = ExecuteNonQueryNode("test_id")

        assert "connection" in node.input_ports
        assert "query" in node.input_ports
        assert "rows_affected" in node.output_ports
        assert "last_insert_id" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_create_table(self, context, sqlite_connection):
        """Test creating a table."""
        node = ExecuteNonQueryNode("test_id")
        node.set_input_value("connection", sqlite_connection)
        node.set_input_value("query", "CREATE TABLE test_table (id INTEGER PRIMARY KEY, value TEXT)")

        result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_execute_insert(self, context, sqlite_connection):
        """Test inserting data."""
        # Create table first
        create_node = ExecuteNonQueryNode("create_id")
        create_node.set_input_value("connection", sqlite_connection)
        create_node.set_input_value("query", "CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")
        await create_node.execute(context)

        # Insert data
        insert_node = ExecuteNonQueryNode("insert_id")
        insert_node.set_input_value("connection", sqlite_connection)
        insert_node.set_input_value("query", "INSERT INTO items (name) VALUES (?)")
        insert_node.set_input_value("parameters", ["Test Item"])

        result = await insert_node.execute(context)

        assert result["success"] is True
        assert insert_node.get_output_value("rows_affected") == 1
        assert insert_node.get_output_value("last_insert_id") == 1

    @pytest.mark.asyncio
    async def test_execute_update(self, context, sqlite_connection):
        """Test updating data."""
        # Setup
        create_node = ExecuteNonQueryNode("create_id")
        create_node.set_input_value("connection", sqlite_connection)
        create_node.set_input_value("query", "CREATE TABLE data (id INTEGER PRIMARY KEY, status TEXT)")
        await create_node.execute(context)

        insert_node = ExecuteNonQueryNode("insert_id")
        insert_node.set_input_value("connection", sqlite_connection)
        insert_node.set_input_value("query", "INSERT INTO data (status) VALUES ('pending')")
        await insert_node.execute(context)

        # Update
        update_node = ExecuteNonQueryNode("update_id")
        update_node.set_input_value("connection", sqlite_connection)
        update_node.set_input_value("query", "UPDATE data SET status = 'done' WHERE id = 1")

        result = await update_node.execute(context)

        assert result["success"] is True
        assert update_node.get_output_value("rows_affected") == 1

    @pytest.mark.asyncio
    async def test_execute_delete(self, context, sqlite_connection):
        """Test deleting data."""
        # Setup
        create_node = ExecuteNonQueryNode("create_id")
        create_node.set_input_value("connection", sqlite_connection)
        create_node.set_input_value("query", "CREATE TABLE temp (id INTEGER)")
        await create_node.execute(context)

        insert_node = ExecuteNonQueryNode("insert_id")
        insert_node.set_input_value("connection", sqlite_connection)
        insert_node.set_input_value("query", "INSERT INTO temp VALUES (1), (2), (3)")
        await insert_node.execute(context)

        # Delete
        delete_node = ExecuteNonQueryNode("delete_id")
        delete_node.set_input_value("connection", sqlite_connection)
        delete_node.set_input_value("query", "DELETE FROM temp WHERE id > 1")

        result = await delete_node.execute(context)

        assert result["success"] is True
        assert delete_node.get_output_value("rows_affected") == 2


# =============================================================================
# Transaction Tests
# =============================================================================

class TestTransactionNodes:
    """Tests for transaction nodes."""

    @pytest.mark.asyncio
    async def test_begin_transaction(self, context, sqlite_connection):
        """Test beginning a transaction."""
        node = BeginTransactionNode("test_id")
        node.set_input_value("connection", sqlite_connection)

        result = await node.execute(context)

        assert result["success"] is True
        connection = node.get_output_value("connection")
        assert connection.in_transaction is True

    @pytest.mark.asyncio
    async def test_commit_transaction(self, context, sqlite_connection):
        """Test committing a transaction."""
        # Begin transaction
        begin_node = BeginTransactionNode("begin_id")
        begin_node.set_input_value("connection", sqlite_connection)
        await begin_node.execute(context)

        # Do some work
        create_node = ExecuteNonQueryNode("create_id")
        create_node.set_input_value("connection", sqlite_connection)
        create_node.set_input_value("query", "CREATE TABLE tx_test (id INTEGER)")
        await create_node.execute(context)

        # Commit
        commit_node = CommitTransactionNode("commit_id")
        commit_node.set_input_value("connection", sqlite_connection)

        result = await commit_node.execute(context)

        assert result["success"] is True
        connection = commit_node.get_output_value("connection")
        assert connection.in_transaction is False

    @pytest.mark.asyncio
    async def test_rollback_transaction(self, context, sqlite_connection):
        """Test rolling back a transaction."""
        # Begin transaction
        begin_node = BeginTransactionNode("begin_id")
        begin_node.set_input_value("connection", sqlite_connection)
        await begin_node.execute(context)

        # Rollback
        rollback_node = RollbackTransactionNode("rollback_id")
        rollback_node.set_input_value("connection", sqlite_connection)

        result = await rollback_node.execute(context)

        assert result["success"] is True
        connection = rollback_node.get_output_value("connection")
        assert connection.in_transaction is False

    @pytest.mark.asyncio
    async def test_transaction_missing_connection(self, context):
        """Test error when connection is missing."""
        node = BeginTransactionNode("test_id")

        result = await node.execute(context)

        assert result["success"] is False
        assert "connection is required" in result["error"].lower()


# =============================================================================
# CloseDatabaseNode Tests
# =============================================================================

class TestCloseDatabaseNode:
    """Tests for CloseDatabaseNode."""

    def test_init(self):
        """Test node initialization."""
        node = CloseDatabaseNode("test_id")
        assert node.node_type == "CloseDatabaseNode"

    @pytest.mark.asyncio
    async def test_close_connection(self, context, temp_db):
        """Test closing a database connection."""
        # Create connection
        connect_node = DatabaseConnectNode("connect_id")
        connect_node.set_input_value("db_type", "sqlite")
        connect_node.set_input_value("database", temp_db)
        await connect_node.execute(context)

        connection = connect_node.get_output_value("connection")

        # Close connection
        close_node = CloseDatabaseNode("close_id")
        close_node.set_input_value("connection", connection)

        result = await close_node.execute(context)

        assert result["success"] is True
        assert close_node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_close_missing_connection(self, context):
        """Test error when connection is missing."""
        node = CloseDatabaseNode("test_id")

        result = await node.execute(context)

        assert result["success"] is False
        assert "connection is required" in result["error"].lower()


# =============================================================================
# TableExistsNode Tests
# =============================================================================

class TestTableExistsNode:
    """Tests for TableExistsNode."""

    def test_init(self):
        """Test node initialization."""
        node = TableExistsNode("test_id")
        assert node.node_type == "TableExistsNode"

    def test_ports_defined(self):
        """Test that required ports are defined."""
        node = TableExistsNode("test_id")

        assert "connection" in node.input_ports
        assert "table_name" in node.input_ports
        assert "exists" in node.output_ports

    @pytest.mark.asyncio
    async def test_table_exists_true(self, context, sqlite_connection):
        """Test checking existing table."""
        # Create table
        create_node = ExecuteNonQueryNode("create_id")
        create_node.set_input_value("connection", sqlite_connection)
        create_node.set_input_value("query", "CREATE TABLE existing_table (id INTEGER)")
        await create_node.execute(context)

        # Check if exists
        check_node = TableExistsNode("check_id")
        check_node.set_input_value("connection", sqlite_connection)
        check_node.set_input_value("table_name", "existing_table")

        result = await check_node.execute(context)

        assert result["success"] is True
        assert check_node.get_output_value("exists") is True

    @pytest.mark.asyncio
    async def test_table_exists_false(self, context, sqlite_connection):
        """Test checking non-existing table."""
        check_node = TableExistsNode("check_id")
        check_node.set_input_value("connection", sqlite_connection)
        check_node.set_input_value("table_name", "nonexistent_table")

        result = await check_node.execute(context)

        assert result["success"] is True
        assert check_node.get_output_value("exists") is False

    @pytest.mark.asyncio
    async def test_table_exists_missing_name(self, context, sqlite_connection):
        """Test error when table name is missing."""
        node = TableExistsNode("test_id")
        node.set_input_value("connection", sqlite_connection)

        result = await node.execute(context)

        assert result["success"] is False
        assert "Table name is required" in result["error"]


# =============================================================================
# GetTableColumnsNode Tests
# =============================================================================

class TestGetTableColumnsNode:
    """Tests for GetTableColumnsNode."""

    def test_init(self):
        """Test node initialization."""
        node = GetTableColumnsNode("test_id")
        assert node.node_type == "GetTableColumnsNode"

    def test_ports_defined(self):
        """Test that required ports are defined."""
        node = GetTableColumnsNode("test_id")

        assert "connection" in node.input_ports
        assert "table_name" in node.input_ports
        assert "columns" in node.output_ports
        assert "column_names" in node.output_ports

    @pytest.mark.asyncio
    async def test_get_columns(self, context, sqlite_connection):
        """Test getting table columns."""
        # Create table with columns
        create_node = ExecuteNonQueryNode("create_id")
        create_node.set_input_value("connection", sqlite_connection)
        create_node.set_input_value("query", """
            CREATE TABLE column_test (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                value REAL,
                active INTEGER DEFAULT 1
            )
        """)
        await create_node.execute(context)

        # Get columns
        columns_node = GetTableColumnsNode("columns_id")
        columns_node.set_input_value("connection", sqlite_connection)
        columns_node.set_input_value("table_name", "column_test")

        result = await columns_node.execute(context)

        assert result["success"] is True

        columns = columns_node.get_output_value("columns")
        assert len(columns) == 4

        column_names = columns_node.get_output_value("column_names")
        assert "id" in column_names
        assert "name" in column_names
        assert "value" in column_names
        assert "active" in column_names

    @pytest.mark.asyncio
    async def test_get_columns_missing_table(self, context, sqlite_connection):
        """Test error when table doesn't exist."""
        node = GetTableColumnsNode("test_id")
        node.set_input_value("connection", sqlite_connection)
        node.set_input_value("table_name", "nonexistent_table")

        result = await node.execute(context)

        # SQLite returns empty list for non-existent table
        assert result["success"] is True
        assert len(node.get_output_value("columns")) == 0


# =============================================================================
# ExecuteBatchNode Tests
# =============================================================================

class TestExecuteBatchNode:
    """Tests for ExecuteBatchNode."""

    def test_init(self):
        """Test node initialization."""
        node = ExecuteBatchNode("test_id")
        assert node.node_type == "ExecuteBatchNode"
        assert node.config.get("stop_on_error") is True

    def test_ports_defined(self):
        """Test that required ports are defined."""
        node = ExecuteBatchNode("test_id")

        assert "connection" in node.input_ports
        assert "statements" in node.input_ports
        assert "results" in node.output_ports
        assert "total_rows_affected" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_batch(self, context, sqlite_connection):
        """Test executing a batch of statements."""
        node = ExecuteBatchNode("test_id")
        node.set_input_value("connection", sqlite_connection)
        node.set_input_value("statements", [
            "CREATE TABLE batch_test (id INTEGER, value TEXT)",
            "INSERT INTO batch_test VALUES (1, 'one')",
            "INSERT INTO batch_test VALUES (2, 'two')",
            "INSERT INTO batch_test VALUES (3, 'three')",
        ])

        result = await node.execute(context)

        assert result["success"] is True
        results = node.get_output_value("results")
        assert len(results) == 4
        assert all(r["success"] for r in results)

    @pytest.mark.asyncio
    async def test_execute_batch_with_error(self, context, sqlite_connection):
        """Test batch with error statement."""
        node = ExecuteBatchNode("test_id", config={"stop_on_error": True})
        node.set_input_value("connection", sqlite_connection)
        node.set_input_value("statements", [
            "CREATE TABLE error_test (id INTEGER)",
            "INVALID SQL STATEMENT",  # This should fail
            "INSERT INTO error_test VALUES (1)",  # This won't run
        ])

        result = await node.execute(context)

        # Should stop on error
        results = node.get_output_value("results")
        assert results[0]["success"] is True
        assert results[1]["success"] is False

    @pytest.mark.asyncio
    async def test_execute_batch_missing_statements(self, context, sqlite_connection):
        """Test error when statements list is missing."""
        node = ExecuteBatchNode("test_id")
        node.set_input_value("connection", sqlite_connection)

        result = await node.execute(context)

        assert result["success"] is False
        assert "Statements list is required" in result["error"]


# =============================================================================
# Integration Tests
# =============================================================================

class TestDatabaseIntegration:
    """Integration tests for database operations."""

    @pytest.mark.asyncio
    async def test_crud_workflow(self, context, sqlite_connection):
        """Test complete CRUD workflow."""
        # Create table
        create_node = ExecuteNonQueryNode("create_id")
        create_node.set_input_value("connection", sqlite_connection)
        create_node.set_input_value("query", """
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL
            )
        """)
        result = await create_node.execute(context)
        assert result["success"] is True

        # Insert (Create)
        insert_node = ExecuteNonQueryNode("insert_id")
        insert_node.set_input_value("connection", sqlite_connection)
        insert_node.set_input_value("query", "INSERT INTO products (name, price) VALUES (?, ?)")
        insert_node.set_input_value("parameters", ["Widget", 19.99])
        result = await insert_node.execute(context)
        assert result["success"] is True
        product_id = insert_node.get_output_value("last_insert_id")

        # Read
        query_node = ExecuteQueryNode("query_id")
        query_node.set_input_value("connection", sqlite_connection)
        query_node.set_input_value("query", "SELECT * FROM products WHERE id = ?")
        query_node.set_input_value("parameters", [product_id])
        result = await query_node.execute(context)
        assert result["success"] is True
        assert query_node.get_output_value("row_count") == 1
        assert query_node.get_output_value("results")[0]["name"] == "Widget"

        # Update
        update_node = ExecuteNonQueryNode("update_id")
        update_node.set_input_value("connection", sqlite_connection)
        update_node.set_input_value("query", "UPDATE products SET price = ? WHERE id = ?")
        update_node.set_input_value("parameters", [24.99, product_id])
        result = await update_node.execute(context)
        assert result["success"] is True
        assert update_node.get_output_value("rows_affected") == 1

        # Delete
        delete_node = ExecuteNonQueryNode("delete_id")
        delete_node.set_input_value("connection", sqlite_connection)
        delete_node.set_input_value("query", "DELETE FROM products WHERE id = ?")
        delete_node.set_input_value("parameters", [product_id])
        result = await delete_node.execute(context)
        assert result["success"] is True
        assert delete_node.get_output_value("rows_affected") == 1

    @pytest.mark.asyncio
    async def test_multiple_tables(self, context, sqlite_connection):
        """Test working with multiple tables."""
        # Create tables
        batch_node = ExecuteBatchNode("batch_id")
        batch_node.set_input_value("connection", sqlite_connection)
        batch_node.set_input_value("statements", [
            "CREATE TABLE categories (id INTEGER PRIMARY KEY, name TEXT)",
            "CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT, category_id INTEGER)",
            "INSERT INTO categories VALUES (1, 'Electronics'), (2, 'Books')",
            "INSERT INTO items VALUES (1, 'Phone', 1), (2, 'Novel', 2)",
        ])
        result = await batch_node.execute(context)
        assert result["success"] is True

        # Query with join
        query_node = ExecuteQueryNode("query_id")
        query_node.set_input_value("connection", sqlite_connection)
        query_node.set_input_value("query", """
            SELECT i.name as item_name, c.name as category_name
            FROM items i
            JOIN categories c ON i.category_id = c.id
        """)
        result = await query_node.execute(context)
        assert result["success"] is True
        assert query_node.get_output_value("row_count") == 2


# =============================================================================
# Node Export Tests
# =============================================================================

class TestDatabaseNodesExports:
    """Tests for database nodes module exports."""

    def test_all_nodes_importable(self):
        """Test that all database nodes can be imported."""
        from casare_rpa.nodes import (
            DatabaseConnectNode,
            ExecuteQueryNode,
            ExecuteNonQueryNode,
            BeginTransactionNode,
            CommitTransactionNode,
            RollbackTransactionNode,
            CloseDatabaseNode,
            TableExistsNode,
            GetTableColumnsNode,
            ExecuteBatchNode,
        )

        # All imports should succeed
        assert DatabaseConnectNode is not None
        assert ExecuteQueryNode is not None
        assert ExecuteNonQueryNode is not None
        assert BeginTransactionNode is not None
        assert CommitTransactionNode is not None
        assert RollbackTransactionNode is not None
        assert CloseDatabaseNode is not None
        assert TableExistsNode is not None
        assert GetTableColumnsNode is not None
        assert ExecuteBatchNode is not None

    def test_nodes_in_registry(self):
        """Test that all database nodes are registered."""
        from casare_rpa.nodes import __all__

        db_nodes = [
            "DatabaseConnectNode",
            "ExecuteQueryNode",
            "ExecuteNonQueryNode",
            "BeginTransactionNode",
            "CommitTransactionNode",
            "RollbackTransactionNode",
            "CloseDatabaseNode",
            "TableExistsNode",
            "GetTableColumnsNode",
            "ExecuteBatchNode",
        ]

        for node_name in db_nodes:
            assert node_name in __all__, f"{node_name} should be in __all__"
