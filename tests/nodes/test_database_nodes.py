"""
Comprehensive tests for database nodes.

Tests 10 database nodes:
- DatabaseConnectNode, CloseDatabaseNode, ExecuteQueryNode
- ExecuteNonQueryNode, BeginTransactionNode, CommitTransactionNode
- RollbackTransactionNode, TableExistsNode, GetTableColumnsNode, ExecuteBatchNode

Mocks asyncpg, aiomysql, and uses real sqlite3 for integration.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.nodes.database_nodes import (
    DatabaseConnection,
    DatabaseConnectNode,
    CloseDatabaseNode,
    ExecuteQueryNode,
    ExecuteNonQueryNode,
    BeginTransactionNode,
    CommitTransactionNode,
    RollbackTransactionNode,
    TableExistsNode,
    GetTableColumnsNode,
    ExecuteBatchNode,
)


def create_mock_context():
    """Create mock execution context."""
    context = Mock(spec=ExecutionContext)
    context.variables = {}
    context.resolve_value = lambda x: x
    return context


def create_sqlite_connection_with_table(table_sql: str, inserts: list = None):
    """Create a SQLite DatabaseConnection with specified table."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(table_sql)
    if inserts:
        for insert in inserts:
            conn.execute(insert)
    conn.commit()
    return DatabaseConnection("sqlite", conn, ":memory:")


class TestDatabaseConnectNode:
    """Tests for DatabaseConnectNode."""

    @pytest.fixture
    def execution_context(self):
        """Create mock execution context."""
        return create_mock_context()

    @pytest.mark.asyncio
    async def test_connect_sqlite_memory(self, execution_context):
        """Test SQLite in-memory connection."""
        node = DatabaseConnectNode(node_id="test_connect")
        node.set_input_value("db_type", "sqlite")
        node.set_input_value("database", ":memory:")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["db_type"] == "sqlite"
        conn = node.get_output_value("connection")
        assert conn is not None
        assert isinstance(conn, DatabaseConnection)
        assert conn.db_type == "sqlite"

    @pytest.mark.asyncio
    async def test_connect_sqlite_file(self, execution_context):
        """Test SQLite file connection."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name

        try:
            node = DatabaseConnectNode(node_id="test_connect_file")
            node.set_input_value("db_type", "sqlite")
            node.set_input_value("database", temp_path)

            result = await node.execute(execution_context)

            assert result["success"] is True
            conn = node.get_output_value("connection")
            assert conn.connection_string == temp_path

            # Close connection before cleanup
            conn.connection.close()
        finally:
            Path(temp_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_connect_sqlite_empty_database_uses_memory(self, execution_context):
        """Test empty database defaults to :memory:."""
        node = DatabaseConnectNode(node_id="test_connect_empty")
        node.set_input_value("db_type", "sqlite")
        node.set_input_value("database", "")

        result = await node.execute(execution_context)

        assert result["success"] is True
        conn = node.get_output_value("connection")
        assert conn.connection_string == ":memory:"

    @pytest.mark.asyncio
    async def test_connect_unsupported_db_type(self, execution_context):
        """Test error on unsupported database type."""
        node = DatabaseConnectNode(node_id="test_unsupported")
        node.set_input_value("db_type", "oracle")
        node.set_input_value("database", "test")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "Unsupported database type" in result["error"]

    @pytest.mark.asyncio
    @patch("casare_rpa.nodes.database_nodes.ASYNCPG_AVAILABLE", False)
    async def test_connect_postgresql_unavailable(self, execution_context):
        """Test PostgreSQL error when asyncpg not installed."""
        node = DatabaseConnectNode(node_id="test_pg_unavailable")
        node.set_input_value("db_type", "postgresql")
        node.set_input_value("host", "localhost")
        node.set_input_value("database", "test")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "asyncpg" in result["error"]

    @pytest.mark.asyncio
    @patch("casare_rpa.nodes.database_nodes.AIOMYSQL_AVAILABLE", False)
    async def test_connect_mysql_unavailable(self, execution_context):
        """Test MySQL error when aiomysql not installed."""
        node = DatabaseConnectNode(node_id="test_mysql_unavailable")
        node.set_input_value("db_type", "mysql")
        node.set_input_value("host", "localhost")
        node.set_input_value("database", "test")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "aiomysql" in result["error"]

    def test_execution_result_pattern(self):
        """Test node follows ExecutionResult pattern."""
        node = DatabaseConnectNode(node_id="test_pattern")
        assert node.node_type == "DatabaseConnectNode"
        assert "exec_in" in [p.name for p in node.input_ports.values()]
        assert "exec_out" in [p.name for p in node.output_ports.values()]
        assert "connection" in [p.name for p in node.output_ports.values()]
        assert "success" in [p.name for p in node.output_ports.values()]


class TestCloseDatabaseNode:
    """Tests for CloseDatabaseNode."""

    @pytest.fixture
    def execution_context(self):
        """Create mock execution context."""
        return create_mock_context()

    @pytest.mark.asyncio
    async def test_close_connection(self, execution_context):
        """Test closing database connection."""
        # First create connection
        connect_node = DatabaseConnectNode(node_id="test_connect")
        connect_node.set_input_value("db_type", "sqlite")
        connect_node.set_input_value("database", ":memory:")
        await connect_node.execute(execution_context)
        conn = connect_node.get_output_value("connection")

        # Now close
        close_node = CloseDatabaseNode(node_id="test_close")
        close_node.set_input_value("connection", conn)

        result = await close_node.execute(execution_context)

        assert result["success"] is True
        assert close_node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_close_no_connection_error(self, execution_context):
        """Test error when no connection provided."""
        node = CloseDatabaseNode(node_id="test_close_none")
        node.set_input_value("connection", None)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()


class TestExecuteQueryNode:
    """Tests for ExecuteQueryNode (SELECT queries)."""

    @pytest.fixture
    def execution_context(self):
        """Create mock execution context."""
        return create_mock_context()

    @pytest.fixture
    def sqlite_connection(self):
        """Create SQLite connection with test data."""
        conn = create_sqlite_connection_with_table(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)",
            [
                "INSERT INTO users (name, age) VALUES ('Alice', 30)",
                "INSERT INTO users (name, age) VALUES ('Bob', 25)",
            ],
        )
        yield conn
        try:
            conn.connection.close()
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_execute_select_query(self, execution_context, sqlite_connection):
        """Test SELECT query execution."""
        node = ExecuteQueryNode(node_id="test_select")
        node.set_input_value("connection", sqlite_connection)
        node.set_input_value("query", "SELECT * FROM users")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["row_count"] == 2
        results = node.get_output_value("results")
        assert len(results) == 2
        assert results[0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_execute_query_with_parameters(
        self, execution_context, sqlite_connection
    ):
        """Test parameterized query."""
        node = ExecuteQueryNode(node_id="test_param")
        node.set_input_value("connection", sqlite_connection)
        node.set_input_value("query", "SELECT * FROM users WHERE age > ?")
        node.set_input_value("parameters", [26])

        result = await node.execute(execution_context)

        assert result["success"] is True
        results = node.get_output_value("results")
        assert len(results) == 1
        assert results[0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_execute_query_returns_columns(
        self, execution_context, sqlite_connection
    ):
        """Test query returns column names."""
        node = ExecuteQueryNode(node_id="test_columns")
        node.set_input_value("connection", sqlite_connection)
        node.set_input_value("query", "SELECT name, age FROM users")

        result = await node.execute(execution_context)

        assert result["success"] is True
        columns = node.get_output_value("columns")
        assert "name" in columns
        assert "age" in columns

    @pytest.mark.asyncio
    async def test_execute_query_no_connection_error(self, execution_context):
        """Test error when no connection."""
        node = ExecuteQueryNode(node_id="test_no_conn")
        node.set_input_value("connection", None)
        node.set_input_value("query", "SELECT 1")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_query_no_query_error(
        self, execution_context, sqlite_connection
    ):
        """Test error when no query."""
        node = ExecuteQueryNode(node_id="test_no_query")
        node.set_input_value("connection", sqlite_connection)
        node.set_input_value("query", "")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()


class TestExecuteNonQueryNode:
    """Tests for ExecuteNonQueryNode (INSERT/UPDATE/DELETE)."""

    @pytest.fixture
    def execution_context(self):
        """Create mock execution context."""
        return create_mock_context()

    @pytest.fixture
    def sqlite_connection(self):
        """Create SQLite connection with test table."""
        conn = create_sqlite_connection_with_table(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)"
        )
        yield conn
        try:
            conn.connection.close()
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_execute_insert(self, execution_context, sqlite_connection):
        """Test INSERT statement."""
        node = ExecuteNonQueryNode(node_id="test_insert")
        node.set_input_value("connection", sqlite_connection)
        node.set_input_value(
            "query", "INSERT INTO users (name, age) VALUES ('Charlie', 35)"
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        rows_affected = node.get_output_value("rows_affected")
        assert rows_affected == 1
        last_id = node.get_output_value("last_insert_id")
        assert last_id == 1

    @pytest.mark.asyncio
    async def test_execute_update(self, execution_context, sqlite_connection):
        """Test UPDATE statement."""
        # Insert first
        sqlite_connection.connection.execute(
            "INSERT INTO users (name, age) VALUES ('Alice', 30)"
        )
        sqlite_connection.connection.commit()

        node = ExecuteNonQueryNode(node_id="test_update")
        node.set_input_value("connection", sqlite_connection)
        node.set_input_value("query", "UPDATE users SET age = 31 WHERE name = 'Alice'")

        result = await node.execute(execution_context)

        assert result["success"] is True
        rows_affected = node.get_output_value("rows_affected")
        assert rows_affected == 1

    @pytest.mark.asyncio
    async def test_execute_delete(self, execution_context, sqlite_connection):
        """Test DELETE statement."""
        # Insert first
        sqlite_connection.connection.execute(
            "INSERT INTO users (name, age) VALUES ('Alice', 30)"
        )
        sqlite_connection.connection.execute(
            "INSERT INTO users (name, age) VALUES ('Bob', 25)"
        )
        sqlite_connection.connection.commit()

        node = ExecuteNonQueryNode(node_id="test_delete")
        node.set_input_value("connection", sqlite_connection)
        node.set_input_value("query", "DELETE FROM users WHERE age < 28")

        result = await node.execute(execution_context)

        assert result["success"] is True
        rows_affected = node.get_output_value("rows_affected")
        assert rows_affected == 1


class TestTransactionNodes:
    """Tests for transaction management nodes."""

    @pytest.fixture
    def execution_context(self):
        """Create mock execution context."""
        return create_mock_context()

    @pytest.fixture
    def sqlite_connection(self):
        """Create SQLite connection."""
        conn = create_sqlite_connection_with_table(
            "CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)"
        )
        yield conn
        try:
            conn.connection.close()
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_begin_transaction(self, execution_context, sqlite_connection):
        """Test beginning a transaction."""
        node = BeginTransactionNode(node_id="test_begin")
        node.set_input_value("connection", sqlite_connection)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["transaction"] == "started"
        conn = node.get_output_value("connection")
        assert conn.in_transaction is True

    @pytest.mark.asyncio
    async def test_begin_transaction_already_in_progress(
        self, execution_context, sqlite_connection
    ):
        """Test error when transaction already in progress."""
        sqlite_connection.in_transaction = True

        node = BeginTransactionNode(node_id="test_begin_dup")
        node.set_input_value("connection", sqlite_connection)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "already" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_commit_transaction(self, execution_context, sqlite_connection):
        """Test committing a transaction."""
        sqlite_connection.in_transaction = True

        node = CommitTransactionNode(node_id="test_commit")
        node.set_input_value("connection", sqlite_connection)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["transaction"] == "committed"
        conn = node.get_output_value("connection")
        assert conn.in_transaction is False

    @pytest.mark.asyncio
    async def test_rollback_transaction(self, execution_context, sqlite_connection):
        """Test rolling back a transaction."""
        sqlite_connection.in_transaction = True

        node = RollbackTransactionNode(node_id="test_rollback")
        node.set_input_value("connection", sqlite_connection)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["transaction"] == "rolled_back"
        conn = node.get_output_value("connection")
        assert conn.in_transaction is False

    @pytest.mark.asyncio
    async def test_transaction_no_connection_error(self, execution_context):
        """Test transaction nodes error without connection."""
        begin_node = BeginTransactionNode(node_id="test_begin_no_conn")
        begin_node.set_input_value("connection", None)

        result = await begin_node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()


class TestTableExistsNode:
    """Tests for TableExistsNode."""

    @pytest.fixture
    def execution_context(self):
        """Create mock execution context."""
        return create_mock_context()

    @pytest.fixture
    def sqlite_connection(self):
        """Create SQLite connection with test table."""
        conn = create_sqlite_connection_with_table(
            "CREATE TABLE existing_table (id INTEGER PRIMARY KEY)"
        )
        yield conn
        try:
            conn.connection.close()
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_table_exists_true(self, execution_context, sqlite_connection):
        """Test detecting existing table."""
        node = TableExistsNode(node_id="test_exists")
        node.set_input_value("connection", sqlite_connection)
        node.set_input_value("table_name", "existing_table")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["exists"] is True
        assert node.get_output_value("exists") is True

    @pytest.mark.asyncio
    async def test_table_exists_false(self, execution_context, sqlite_connection):
        """Test detecting non-existent table."""
        node = TableExistsNode(node_id="test_not_exists")
        node.set_input_value("connection", sqlite_connection)
        node.set_input_value("table_name", "nonexistent_table")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["exists"] is False
        assert node.get_output_value("exists") is False

    @pytest.mark.asyncio
    async def test_table_exists_no_table_name_error(
        self, execution_context, sqlite_connection
    ):
        """Test error when table name not provided."""
        node = TableExistsNode(node_id="test_no_name")
        node.set_input_value("connection", sqlite_connection)
        node.set_input_value("table_name", "")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()


class TestGetTableColumnsNode:
    """Tests for GetTableColumnsNode."""

    @pytest.fixture
    def execution_context(self):
        """Create mock execution context."""
        return create_mock_context()

    @pytest.fixture
    def sqlite_connection(self):
        """Create SQLite connection with test table."""
        conn = create_sqlite_connection_with_table("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER DEFAULT 0,
                email TEXT
            )
        """)
        yield conn
        try:
            conn.connection.close()
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_get_columns(self, execution_context, sqlite_connection):
        """Test getting table columns."""
        node = GetTableColumnsNode(node_id="test_columns")
        node.set_input_value("connection", sqlite_connection)
        node.set_input_value("table_name", "test_table")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["column_count"] == 4

        columns = node.get_output_value("columns")
        assert len(columns) == 4

        column_names = node.get_output_value("column_names")
        assert "id" in column_names
        assert "name" in column_names
        assert "age" in column_names
        assert "email" in column_names

    @pytest.mark.asyncio
    async def test_get_columns_includes_metadata(
        self, execution_context, sqlite_connection
    ):
        """Test column info includes type and nullable."""
        node = GetTableColumnsNode(node_id="test_metadata")
        node.set_input_value("connection", sqlite_connection)
        node.set_input_value("table_name", "test_table")

        result = await node.execute(execution_context)

        assert result["success"] is True
        columns = node.get_output_value("columns")

        id_col = next(c for c in columns if c["name"] == "id")
        assert id_col["primary_key"] is True
        assert "INTEGER" in id_col["type"]


class TestExecuteBatchNode:
    """Tests for ExecuteBatchNode."""

    @pytest.fixture
    def execution_context(self):
        """Create mock execution context."""
        return create_mock_context()

    @pytest.fixture
    def sqlite_connection(self):
        """Create SQLite connection with test table."""
        conn = create_sqlite_connection_with_table(
            "CREATE TABLE batch_test (id INTEGER PRIMARY KEY, value TEXT)"
        )
        yield conn
        try:
            conn.connection.close()
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_execute_batch_success(self, execution_context, sqlite_connection):
        """Test batch execution of multiple statements."""
        node = ExecuteBatchNode(node_id="test_batch")
        node.set_input_value("connection", sqlite_connection)
        node.set_input_value(
            "statements",
            [
                "INSERT INTO batch_test (value) VALUES ('one')",
                "INSERT INTO batch_test (value) VALUES ('two')",
                "INSERT INTO batch_test (value) VALUES ('three')",
            ],
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["statements"] == 3
        total_rows = node.get_output_value("total_rows_affected")
        assert total_rows == 3

    @pytest.mark.asyncio
    async def test_execute_batch_with_error_stops(
        self, execution_context, sqlite_connection
    ):
        """Test batch stops on error when stop_on_error is True."""
        node = ExecuteBatchNode(
            node_id="test_batch_error", config={"stop_on_error": True}
        )
        node.set_input_value("connection", sqlite_connection)
        node.set_input_value(
            "statements",
            [
                "INSERT INTO batch_test (value) VALUES ('one')",
                "INSERT INTO nonexistent_table VALUES (1)",  # Error
                "INSERT INTO batch_test (value) VALUES ('three')",
            ],
        )

        result = await node.execute(execution_context)

        assert result["success"] is False
        results = node.get_output_value("results")
        assert results[0]["success"] is True
        assert results[1]["success"] is False

    @pytest.mark.asyncio
    async def test_execute_batch_no_statements_error(
        self, execution_context, sqlite_connection
    ):
        """Test error when no statements provided."""
        node = ExecuteBatchNode(node_id="test_batch_empty")
        node.set_input_value("connection", sqlite_connection)
        node.set_input_value("statements", [])

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()


class TestDatabaseConnectionWrapper:
    """Tests for DatabaseConnection wrapper class."""

    def test_connection_init(self):
        """Test connection wrapper initialization."""
        mock_conn = Mock()
        db_conn = DatabaseConnection(
            db_type="sqlite",
            connection=mock_conn,
            connection_string="test.db",
            in_transaction=False,
        )

        assert db_conn.db_type == "sqlite"
        assert db_conn.connection == mock_conn
        assert db_conn.connection_string == "test.db"
        assert db_conn.in_transaction is False
        assert db_conn.cursor is None

    @pytest.mark.asyncio
    async def test_connection_close_async(self):
        """Test async close method."""
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        db_conn = DatabaseConnection("sqlite", mock_conn)
        db_conn.cursor = mock_cursor

        await db_conn.close()

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
        assert db_conn.cursor is None
        assert db_conn.connection is None

    @pytest.mark.asyncio
    async def test_connection_close_sync(self):
        """Test close with sync connection."""
        mock_conn = Mock()
        mock_conn.close = Mock()
        db_conn = DatabaseConnection("sqlite", mock_conn)

        await db_conn.close()

        mock_conn.close.assert_called_once()


class TestDatabaseNodesMockedDrivers:
    """Tests using mocked database drivers (asyncpg/aiomysql)."""

    @pytest.fixture
    def execution_context(self):
        """Create mock execution context."""
        return create_mock_context()

    @pytest.mark.asyncio
    @patch("casare_rpa.nodes.database_nodes.ASYNCPG_AVAILABLE", True)
    @patch("casare_rpa.nodes.database_nodes.asyncpg")
    async def test_postgresql_connect_mocked(self, mock_asyncpg, execution_context):
        """Test PostgreSQL connection with mocked asyncpg."""
        mock_conn = AsyncMock()
        mock_asyncpg.connect = AsyncMock(return_value=mock_conn)

        node = DatabaseConnectNode(node_id="test_pg")
        node.set_input_value("db_type", "postgresql")
        node.set_input_value("host", "localhost")
        node.set_input_value("port", 5432)
        node.set_input_value("database", "testdb")
        node.set_input_value("username", "user")
        node.set_input_value("password", "pass")

        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_asyncpg.connect.assert_called_once()

    @pytest.mark.asyncio
    @patch("casare_rpa.nodes.database_nodes.AIOMYSQL_AVAILABLE", True)
    @patch("casare_rpa.nodes.database_nodes.aiomysql")
    async def test_mysql_connect_mocked(self, mock_aiomysql, execution_context):
        """Test MySQL connection with mocked aiomysql."""
        mock_conn = AsyncMock()
        mock_aiomysql.connect = AsyncMock(return_value=mock_conn)

        node = DatabaseConnectNode(node_id="test_mysql")
        node.set_input_value("db_type", "mysql")
        node.set_input_value("host", "localhost")
        node.set_input_value("port", 3306)
        node.set_input_value("database", "testdb")
        node.set_input_value("username", "user")
        node.set_input_value("password", "pass")

        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_aiomysql.connect.assert_called_once()
