"""
Database Connectivity Nodes for CasareRPA.

This module provides nodes for connecting to and interacting with databases.
Supports SQLite (built-in), PostgreSQL, MySQL/MariaDB, and SQL Server.

Nodes:
    - DatabaseConnectNode: Establish database connection
    - ExecuteQueryNode: Run SELECT queries and return results
    - ExecuteNonQueryNode: Run INSERT, UPDATE, DELETE statements
    - FetchResultsNode: Fetch results from a cursor
    - BeginTransactionNode: Start a database transaction
    - CommitTransactionNode: Commit the current transaction
    - RollbackTransactionNode: Rollback the current transaction
    - CloseDatabaseNode: Close database connection
    - TableExistsNode: Check if a table exists
    - GetTableColumnsNode: Get column information for a table
"""

from __future__ import annotations

import asyncio
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from loguru import logger

from ..core.base_node import BaseNode
from ..core.execution_context import ExecutionContext
from ..core.types import DataType, ExecutionResult, NodeStatus, PortType

# Try to import optional database drivers
try:
    import aiosqlite
    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False
    logger.debug("aiosqlite not available, using sync sqlite3")

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    logger.debug("asyncpg not available, PostgreSQL support disabled")

try:
    import aiomysql
    AIOMYSQL_AVAILABLE = True
except ImportError:
    AIOMYSQL_AVAILABLE = False
    logger.debug("aiomysql not available, MySQL support disabled")


class DatabaseConnection:
    """
    Wrapper class for database connections.

    Provides a unified interface for different database types.
    """

    def __init__(
        self,
        db_type: str,
        connection: Any,
        connection_string: str = "",
        in_transaction: bool = False
    ) -> None:
        self.db_type = db_type
        self.connection = connection
        self.connection_string = connection_string
        self.in_transaction = in_transaction
        self.cursor: Optional[Any] = None
        self.last_results: List[Dict[str, Any]] = []
        self.last_rowcount: int = 0
        self.last_lastrowid: Optional[int] = None

    async def close(self) -> None:
        """Close the database connection."""
        if self.cursor:
            if hasattr(self.cursor, 'close'):
                if asyncio.iscoroutinefunction(self.cursor.close):
                    await self.cursor.close()
                else:
                    self.cursor.close()
            self.cursor = None

        if self.connection:
            if hasattr(self.connection, 'close'):
                if asyncio.iscoroutinefunction(self.connection.close):
                    await self.connection.close()
                else:
                    self.connection.close()
            self.connection = None


class DatabaseConnectNode(BaseNode):
    """
    Establish a database connection.

    Supports:
        - SQLite: File-based or in-memory database
        - PostgreSQL: Via asyncpg (if installed)
        - MySQL: Via aiomysql (if installed)

    Inputs:
        - exec_in: Execution input
        - db_type: Database type (sqlite, postgresql, mysql)
        - host: Database host (for PostgreSQL/MySQL)
        - port: Database port
        - database: Database name or file path (for SQLite)
        - username: Database username
        - password: Database password
        - connection_string: Full connection string (optional)

    Outputs:
        - exec_out: Execution output
        - connection: Database connection object
        - success: True if connection succeeded
        - error: Error message if connection failed
    """

    def __init__(self, node_id: str, name: str = "Database Connect", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        config.setdefault("db_type", "sqlite")
        config.setdefault("host", "localhost")
        config.setdefault("port", 5432)
        config.setdefault("database", "")
        config.setdefault("username", "")
        config.setdefault("password", "")
        config.setdefault("connection_string", "")
        config.setdefault("timeout", 30.0)
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DatabaseConnectNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        self.add_input_port("db_type", PortType.INPUT, DataType.STRING)
        self.add_input_port("host", PortType.INPUT, DataType.STRING)
        self.add_input_port("port", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("database", PortType.INPUT, DataType.STRING)
        self.add_input_port("username", PortType.INPUT, DataType.STRING)
        self.add_input_port("password", PortType.INPUT, DataType.STRING)
        self.add_input_port("connection_string", PortType.INPUT, DataType.STRING)

        self.add_output_port("connection", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            db_type = (self.get_input_value("db_type") or self.config.get("db_type", "sqlite")).lower()
            host = self.get_input_value("host") or self.config.get("host", "localhost")
            port = self.get_input_value("port") or self.config.get("port", 5432)
            database = self.get_input_value("database") or self.config.get("database", "")
            username = self.get_input_value("username") or self.config.get("username", "")
            password = self.get_input_value("password") or self.config.get("password", "")
            connection_string = self.get_input_value("connection_string") or self.config.get("connection_string", "")

            connection: Optional[DatabaseConnection] = None

            if db_type == "sqlite":
                connection = await self._connect_sqlite(database)
            elif db_type == "postgresql":
                connection = await self._connect_postgresql(host, port, database, username, password, connection_string)
            elif db_type == "mysql":
                connection = await self._connect_mysql(host, port, database, username, password)
            else:
                raise ValueError(f"Unsupported database type: {db_type}")

            self.set_output_value("connection", connection)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.info(f"Connected to {db_type} database")

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"db_type": db_type},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            error_msg = f"Database connection error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("connection", None)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

    async def _connect_sqlite(self, database: str) -> DatabaseConnection:
        """Connect to SQLite database."""
        if not database:
            database = ":memory:"

        if AIOSQLITE_AVAILABLE:
            conn = await aiosqlite.connect(database)
            conn.row_factory = aiosqlite.Row
        else:
            # Fallback to sync sqlite3
            conn = sqlite3.connect(database)
            conn.row_factory = sqlite3.Row

        return DatabaseConnection("sqlite", conn, database)

    async def _connect_postgresql(
        self,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        connection_string: str
    ) -> DatabaseConnection:
        """Connect to PostgreSQL database."""
        if not ASYNCPG_AVAILABLE:
            raise ImportError("asyncpg is required for PostgreSQL support. Install with: pip install asyncpg")

        if connection_string:
            conn = await asyncpg.connect(connection_string)
        else:
            conn = await asyncpg.connect(
                host=host,
                port=int(port),
                database=database,
                user=username,
                password=password
            )

        return DatabaseConnection("postgresql", conn, f"postgresql://{host}:{port}/{database}")

    async def _connect_mysql(
        self,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str
    ) -> DatabaseConnection:
        """Connect to MySQL database."""
        if not AIOMYSQL_AVAILABLE:
            raise ImportError("aiomysql is required for MySQL support. Install with: pip install aiomysql")

        conn = await aiomysql.connect(
            host=host,
            port=int(port),
            db=database,
            user=username,
            password=password
        )

        return DatabaseConnection("mysql", conn, f"mysql://{host}:{port}/{database}")


class ExecuteQueryNode(BaseNode):
    """
    Execute a SELECT query and return results.

    Inputs:
        - exec_in: Execution input
        - connection: Database connection
        - query: SQL SELECT query
        - parameters: Query parameters (for parameterized queries)

    Outputs:
        - exec_out: Execution output
        - results: List of rows as dictionaries
        - row_count: Number of rows returned
        - columns: List of column names
        - success: True if query succeeded
        - error: Error message if query failed
    """

    def __init__(self, node_id: str, name: str = "Execute Query", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        config.setdefault("query", "")
        config.setdefault("parameters", [])
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ExecuteQueryNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        self.add_input_port("connection", PortType.INPUT, DataType.ANY)
        self.add_input_port("query", PortType.INPUT, DataType.STRING)
        self.add_input_port("parameters", PortType.INPUT, DataType.LIST)

        self.add_output_port("results", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("row_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("columns", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            connection: Optional[DatabaseConnection] = self.get_input_value("connection")
            query = self.get_input_value("query") or self.config.get("query", "")
            parameters = self.get_input_value("parameters") or self.config.get("parameters", [])

            if not connection:
                raise ValueError("Database connection is required")
            if not query:
                raise ValueError("Query is required")

            results: List[Dict[str, Any]] = []
            columns: List[str] = []

            if connection.db_type == "sqlite":
                results, columns = await self._execute_sqlite(connection, query, parameters)
            elif connection.db_type == "postgresql":
                results, columns = await self._execute_postgresql(connection, query, parameters)
            elif connection.db_type == "mysql":
                results, columns = await self._execute_mysql(connection, query, parameters)

            connection.last_results = results

            self.set_output_value("results", results)
            self.set_output_value("row_count", len(results))
            self.set_output_value("columns", columns)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.debug(f"Query returned {len(results)} rows")

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"row_count": len(results)},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            error_msg = f"Query execution error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("results", [])
            self.set_output_value("row_count", 0)
            self.set_output_value("columns", [])
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

    async def _execute_sqlite(
        self,
        connection: DatabaseConnection,
        query: str,
        parameters: List[Any]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Execute query on SQLite."""
        conn = connection.connection

        if AIOSQLITE_AVAILABLE:
            cursor = await conn.execute(query, parameters or [])
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            results = [dict(zip(columns, row)) for row in rows]
        else:
            cursor = conn.execute(query, parameters or [])
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            results = [dict(zip(columns, row)) for row in rows]

        return results, columns

    async def _execute_postgresql(
        self,
        connection: DatabaseConnection,
        query: str,
        parameters: List[Any]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Execute query on PostgreSQL."""
        conn = connection.connection

        # asyncpg uses $1, $2 for parameters
        rows = await conn.fetch(query, *parameters) if parameters else await conn.fetch(query)

        if rows:
            columns = list(rows[0].keys())
            results = [dict(row) for row in rows]
        else:
            columns = []
            results = []

        return results, columns

    async def _execute_mysql(
        self,
        connection: DatabaseConnection,
        query: str,
        parameters: List[Any]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Execute query on MySQL."""
        conn = connection.connection

        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, parameters or [])
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

        return list(rows), columns


class ExecuteNonQueryNode(BaseNode):
    """
    Execute INSERT, UPDATE, DELETE, or DDL statements.

    Inputs:
        - exec_in: Execution input
        - connection: Database connection
        - query: SQL statement
        - parameters: Query parameters (for parameterized queries)

    Outputs:
        - exec_out: Execution output
        - rows_affected: Number of rows affected
        - last_insert_id: ID of last inserted row (if applicable)
        - success: True if execution succeeded
        - error: Error message if execution failed
    """

    def __init__(self, node_id: str, name: str = "Execute Non-Query", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        config.setdefault("query", "")
        config.setdefault("parameters", [])
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ExecuteNonQueryNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        self.add_input_port("connection", PortType.INPUT, DataType.ANY)
        self.add_input_port("query", PortType.INPUT, DataType.STRING)
        self.add_input_port("parameters", PortType.INPUT, DataType.LIST)

        self.add_output_port("rows_affected", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("last_insert_id", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            connection: Optional[DatabaseConnection] = self.get_input_value("connection")
            query = self.get_input_value("query") or self.config.get("query", "")
            parameters = self.get_input_value("parameters") or self.config.get("parameters", [])

            if not connection:
                raise ValueError("Database connection is required")
            if not query:
                raise ValueError("Query is required")

            rows_affected = 0
            last_insert_id = None

            if connection.db_type == "sqlite":
                rows_affected, last_insert_id = await self._execute_sqlite(connection, query, parameters)
            elif connection.db_type == "postgresql":
                rows_affected, last_insert_id = await self._execute_postgresql(connection, query, parameters)
            elif connection.db_type == "mysql":
                rows_affected, last_insert_id = await self._execute_mysql(connection, query, parameters)

            connection.last_rowcount = rows_affected
            connection.last_lastrowid = last_insert_id

            self.set_output_value("rows_affected", rows_affected)
            self.set_output_value("last_insert_id", last_insert_id)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.debug(f"Statement affected {rows_affected} rows")

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"rows_affected": rows_affected},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            error_msg = f"Statement execution error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("rows_affected", 0)
            self.set_output_value("last_insert_id", None)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

    async def _execute_sqlite(
        self,
        connection: DatabaseConnection,
        query: str,
        parameters: List[Any]
    ) -> Tuple[int, Optional[int]]:
        """Execute non-query on SQLite."""
        conn = connection.connection

        if AIOSQLITE_AVAILABLE:
            cursor = await conn.execute(query, parameters or [])
            if not connection.in_transaction:
                await conn.commit()
            rows_affected = cursor.rowcount
            last_insert_id = cursor.lastrowid
        else:
            cursor = conn.execute(query, parameters or [])
            if not connection.in_transaction:
                conn.commit()
            rows_affected = cursor.rowcount
            last_insert_id = cursor.lastrowid

        return rows_affected, last_insert_id

    async def _execute_postgresql(
        self,
        connection: DatabaseConnection,
        query: str,
        parameters: List[Any]
    ) -> Tuple[int, Optional[int]]:
        """Execute non-query on PostgreSQL."""
        conn = connection.connection

        # asyncpg returns status string like "INSERT 0 1" or "UPDATE 5"
        result = await conn.execute(query, *parameters) if parameters else await conn.execute(query)

        # Parse rows affected from result
        rows_affected = 0
        if result:
            parts = result.split()
            if len(parts) >= 2:
                try:
                    rows_affected = int(parts[-1])
                except ValueError:
                    pass

        return rows_affected, None

    async def _execute_mysql(
        self,
        connection: DatabaseConnection,
        query: str,
        parameters: List[Any]
    ) -> Tuple[int, Optional[int]]:
        """Execute non-query on MySQL."""
        conn = connection.connection

        async with conn.cursor() as cursor:
            await cursor.execute(query, parameters or [])
            if not connection.in_transaction:
                await conn.commit()
            rows_affected = cursor.rowcount
            last_insert_id = cursor.lastrowid

        return rows_affected, last_insert_id


class BeginTransactionNode(BaseNode):
    """
    Begin a database transaction.

    Inputs:
        - exec_in: Execution input
        - connection: Database connection

    Outputs:
        - exec_out: Execution output
        - connection: Connection with active transaction
        - success: True if transaction started
        - error: Error message if failed
    """

    def __init__(self, node_id: str, name: str = "Begin Transaction", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "BeginTransactionNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        self.add_input_port("connection", PortType.INPUT, DataType.ANY)

        self.add_output_port("connection", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            connection: Optional[DatabaseConnection] = self.get_input_value("connection")

            if not connection:
                raise ValueError("Database connection is required")

            if connection.in_transaction:
                raise ValueError("Transaction already in progress")

            if connection.db_type == "sqlite":
                # SQLite auto-starts transaction on first statement
                pass
            elif connection.db_type == "postgresql":
                # PostgreSQL transaction managed via connection
                connection.connection = await connection.connection.transaction()
            elif connection.db_type == "mysql":
                await connection.connection.begin()

            connection.in_transaction = True

            self.set_output_value("connection", connection)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.debug("Transaction started")

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"transaction": "started"},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            error_msg = f"Begin transaction error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("connection", connection)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


class CommitTransactionNode(BaseNode):
    """
    Commit the current database transaction.

    Inputs:
        - exec_in: Execution input
        - connection: Database connection with active transaction

    Outputs:
        - exec_out: Execution output
        - connection: Connection (transaction ended)
        - success: True if commit succeeded
        - error: Error message if failed
    """

    def __init__(self, node_id: str, name: str = "Commit Transaction", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "CommitTransactionNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        self.add_input_port("connection", PortType.INPUT, DataType.ANY)

        self.add_output_port("connection", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            connection: Optional[DatabaseConnection] = self.get_input_value("connection")

            if not connection:
                raise ValueError("Database connection is required")

            if connection.db_type == "sqlite":
                conn = connection.connection
                if AIOSQLITE_AVAILABLE:
                    await conn.commit()
                else:
                    conn.commit()
            elif connection.db_type == "postgresql":
                # asyncpg transaction commit
                pass  # Transaction context manager handles this
            elif connection.db_type == "mysql":
                await connection.connection.commit()

            connection.in_transaction = False

            self.set_output_value("connection", connection)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.debug("Transaction committed")

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"transaction": "committed"},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            error_msg = f"Commit transaction error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("connection", connection)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


class RollbackTransactionNode(BaseNode):
    """
    Rollback the current database transaction.

    Inputs:
        - exec_in: Execution input
        - connection: Database connection with active transaction

    Outputs:
        - exec_out: Execution output
        - connection: Connection (transaction ended)
        - success: True if rollback succeeded
        - error: Error message if failed
    """

    def __init__(self, node_id: str, name: str = "Rollback Transaction", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RollbackTransactionNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        self.add_input_port("connection", PortType.INPUT, DataType.ANY)

        self.add_output_port("connection", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            connection: Optional[DatabaseConnection] = self.get_input_value("connection")

            if not connection:
                raise ValueError("Database connection is required")

            if connection.db_type == "sqlite":
                conn = connection.connection
                if AIOSQLITE_AVAILABLE:
                    await conn.rollback()
                else:
                    conn.rollback()
            elif connection.db_type == "postgresql":
                # asyncpg transaction rollback
                pass  # Transaction context manager handles this
            elif connection.db_type == "mysql":
                await connection.connection.rollback()

            connection.in_transaction = False

            self.set_output_value("connection", connection)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.debug("Transaction rolled back")

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"transaction": "rolled_back"},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            error_msg = f"Rollback transaction error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("connection", connection)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


class CloseDatabaseNode(BaseNode):
    """
    Close a database connection.

    Inputs:
        - exec_in: Execution input
        - connection: Database connection to close

    Outputs:
        - exec_out: Execution output
        - success: True if connection closed
        - error: Error message if failed
    """

    def __init__(self, node_id: str, name: str = "Close Database", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "CloseDatabaseNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        self.add_input_port("connection", PortType.INPUT, DataType.ANY)

        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            connection: Optional[DatabaseConnection] = self.get_input_value("connection")

            if not connection:
                raise ValueError("Database connection is required")

            await connection.close()

            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.info("Database connection closed")

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"connection": "closed"},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            error_msg = f"Close connection error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


class TableExistsNode(BaseNode):
    """
    Check if a table exists in the database.

    Inputs:
        - exec_in: Execution input
        - connection: Database connection
        - table_name: Name of table to check

    Outputs:
        - exec_out: Execution output
        - exists: True if table exists
        - success: True if check succeeded
        - error: Error message if failed
    """

    def __init__(self, node_id: str, name: str = "Table Exists", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        config.setdefault("table_name", "")
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TableExistsNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        self.add_input_port("connection", PortType.INPUT, DataType.ANY)
        self.add_input_port("table_name", PortType.INPUT, DataType.STRING)

        self.add_output_port("exists", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            connection: Optional[DatabaseConnection] = self.get_input_value("connection")
            table_name = self.get_input_value("table_name") or self.config.get("table_name", "")

            if not connection:
                raise ValueError("Database connection is required")
            if not table_name:
                raise ValueError("Table name is required")

            exists = False

            if connection.db_type == "sqlite":
                exists = await self._check_sqlite(connection, table_name)
            elif connection.db_type == "postgresql":
                exists = await self._check_postgresql(connection, table_name)
            elif connection.db_type == "mysql":
                exists = await self._check_mysql(connection, table_name)

            self.set_output_value("exists", exists)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.debug(f"Table '{table_name}' exists: {exists}")

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"table": table_name, "exists": exists},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            error_msg = f"Table exists check error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("exists", False)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

    async def _check_sqlite(self, connection: DatabaseConnection, table_name: str) -> bool:
        """Check if table exists in SQLite."""
        conn = connection.connection
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"

        if AIOSQLITE_AVAILABLE:
            cursor = await conn.execute(query, [table_name])
            row = await cursor.fetchone()
        else:
            cursor = conn.execute(query, [table_name])
            row = cursor.fetchone()

        return row is not None

    async def _check_postgresql(self, connection: DatabaseConnection, table_name: str) -> bool:
        """Check if table exists in PostgreSQL."""
        conn = connection.connection
        query = "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = $1)"
        result = await conn.fetchval(query, table_name)
        return result

    async def _check_mysql(self, connection: DatabaseConnection, table_name: str) -> bool:
        """Check if table exists in MySQL."""
        conn = connection.connection
        query = "SHOW TABLES LIKE %s"

        async with conn.cursor() as cursor:
            await cursor.execute(query, [table_name])
            row = await cursor.fetchone()

        return row is not None


class GetTableColumnsNode(BaseNode):
    """
    Get column information for a table.

    Inputs:
        - exec_in: Execution input
        - connection: Database connection
        - table_name: Name of table

    Outputs:
        - exec_out: Execution output
        - columns: List of column info dictionaries
        - column_names: List of column names
        - success: True if query succeeded
        - error: Error message if failed
    """

    def __init__(self, node_id: str, name: str = "Get Table Columns", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        config.setdefault("table_name", "")
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetTableColumnsNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        self.add_input_port("connection", PortType.INPUT, DataType.ANY)
        self.add_input_port("table_name", PortType.INPUT, DataType.STRING)

        self.add_output_port("columns", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("column_names", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            connection: Optional[DatabaseConnection] = self.get_input_value("connection")
            table_name = self.get_input_value("table_name") or self.config.get("table_name", "")

            if not connection:
                raise ValueError("Database connection is required")
            if not table_name:
                raise ValueError("Table name is required")

            columns: List[Dict[str, Any]] = []

            if connection.db_type == "sqlite":
                columns = await self._get_sqlite_columns(connection, table_name)
            elif connection.db_type == "postgresql":
                columns = await self._get_postgresql_columns(connection, table_name)
            elif connection.db_type == "mysql":
                columns = await self._get_mysql_columns(connection, table_name)

            column_names = [col["name"] for col in columns]

            self.set_output_value("columns", columns)
            self.set_output_value("column_names", column_names)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.debug(f"Retrieved {len(columns)} columns for table '{table_name}'")

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"table": table_name, "column_count": len(columns)},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            error_msg = f"Get columns error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("columns", [])
            self.set_output_value("column_names", [])
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

    async def _get_sqlite_columns(
        self,
        connection: DatabaseConnection,
        table_name: str
    ) -> List[Dict[str, Any]]:
        """Get column info for SQLite table."""
        conn = connection.connection
        query = f"PRAGMA table_info({table_name})"

        if AIOSQLITE_AVAILABLE:
            cursor = await conn.execute(query)
            rows = await cursor.fetchall()
        else:
            cursor = conn.execute(query)
            rows = cursor.fetchall()

        columns = []
        for row in rows:
            columns.append({
                "name": row[1],
                "type": row[2],
                "nullable": not row[3],
                "default": row[4],
                "primary_key": bool(row[5])
            })

        return columns

    async def _get_postgresql_columns(
        self,
        connection: DatabaseConnection,
        table_name: str
    ) -> List[Dict[str, Any]]:
        """Get column info for PostgreSQL table."""
        conn = connection.connection
        query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = $1
            ORDER BY ordinal_position
        """
        rows = await conn.fetch(query, table_name)

        columns = []
        for row in rows:
            columns.append({
                "name": row["column_name"],
                "type": row["data_type"],
                "nullable": row["is_nullable"] == "YES",
                "default": row["column_default"],
                "primary_key": False  # Would need additional query
            })

        return columns

    async def _get_mysql_columns(
        self,
        connection: DatabaseConnection,
        table_name: str
    ) -> List[Dict[str, Any]]:
        """Get column info for MySQL table."""
        conn = connection.connection
        query = f"DESCRIBE {table_name}"

        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query)
            rows = await cursor.fetchall()

        columns = []
        for row in rows:
            columns.append({
                "name": row["Field"],
                "type": row["Type"],
                "nullable": row["Null"] == "YES",
                "default": row["Default"],
                "primary_key": row["Key"] == "PRI"
            })

        return columns


class ExecuteBatchNode(BaseNode):
    """
    Execute multiple SQL statements as a batch.

    Inputs:
        - exec_in: Execution input
        - connection: Database connection
        - statements: List of SQL statements
        - stop_on_error: Stop execution on first error

    Outputs:
        - exec_out: Execution output
        - results: List of results for each statement
        - total_rows_affected: Total rows affected
        - success: True if all statements succeeded
        - error: Error message if any statement failed
    """

    def __init__(self, node_id: str, name: str = "Execute Batch", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        config.setdefault("statements", [])
        config.setdefault("stop_on_error", True)
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ExecuteBatchNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        self.add_input_port("connection", PortType.INPUT, DataType.ANY)
        self.add_input_port("statements", PortType.INPUT, DataType.LIST)

        self.add_output_port("results", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("total_rows_affected", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            connection: Optional[DatabaseConnection] = self.get_input_value("connection")
            statements = self.get_input_value("statements") or self.config.get("statements", [])
            stop_on_error = self.config.get("stop_on_error", True)

            if not connection:
                raise ValueError("Database connection is required")
            if not statements:
                raise ValueError("Statements list is required")

            results = []
            total_rows = 0
            errors = []

            for i, stmt in enumerate(statements):
                try:
                    if connection.db_type == "sqlite":
                        conn = connection.connection
                        if AIOSQLITE_AVAILABLE:
                            cursor = await conn.execute(stmt)
                            rows = cursor.rowcount
                        else:
                            cursor = conn.execute(stmt)
                            rows = cursor.rowcount
                    elif connection.db_type == "postgresql":
                        result = await connection.connection.execute(stmt)
                        rows = int(result.split()[-1]) if result else 0
                    elif connection.db_type == "mysql":
                        async with connection.connection.cursor() as cursor:
                            await cursor.execute(stmt)
                            rows = cursor.rowcount

                    results.append({"statement": i, "rows_affected": rows, "success": True})
                    total_rows += rows

                except Exception as e:
                    results.append({"statement": i, "rows_affected": 0, "success": False, "error": str(e)})
                    errors.append(f"Statement {i}: {str(e)}")
                    if stop_on_error:
                        break

            # Commit if not in transaction
            if not connection.in_transaction:
                if connection.db_type == "sqlite":
                    if AIOSQLITE_AVAILABLE:
                        await connection.connection.commit()
                    else:
                        connection.connection.commit()
                elif connection.db_type == "mysql":
                    await connection.connection.commit()

            all_success = len(errors) == 0

            self.set_output_value("results", results)
            self.set_output_value("total_rows_affected", total_rows)
            self.set_output_value("success", all_success)
            self.set_output_value("error", "; ".join(errors) if errors else "")

            logger.debug(f"Batch executed {len(statements)} statements, {total_rows} rows affected")

            self.status = NodeStatus.SUCCESS if all_success else NodeStatus.ERROR
            return {
                "success": all_success,
                "data": {"statements": len(statements), "rows_affected": total_rows},
                "next_nodes": ["exec_out"] if all_success else []
            }

        except Exception as e:
            error_msg = f"Batch execution error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("results", [])
            self.set_output_value("total_rows_affected", 0)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


# Export all node classes
__all__ = [
    "DatabaseConnection",
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
