"""
SQL Database Nodes for CasareRPA.

This module provides core nodes for connecting to and interacting with databases.
Supports SQLite (built-in), PostgreSQL, MySQL/MariaDB.

Nodes:
    - DatabaseConnectNode: Establish database connection
    - ExecuteQueryNode: Run SELECT queries and return results
    - ExecuteNonQueryNode: Run INSERT, UPDATE, DELETE statements
    - BeginTransactionNode: Start a database transaction
    - CommitTransactionNode: Commit the current transaction
    - RollbackTransactionNode: Rollback the current transaction
    - CloseDatabaseNode: Close database connection
    - ExecuteBatchNode: Execute multiple SQL statements as a batch
"""

from __future__ import annotations

import asyncio
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
    PortType,
)

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
        in_transaction: bool = False,
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
            if hasattr(self.cursor, "close"):
                if asyncio.iscoroutinefunction(self.cursor.close):
                    await self.cursor.close()
                else:
                    self.cursor.close()
            self.cursor = None

        if self.connection:
            if hasattr(self.connection, "close"):
                if asyncio.iscoroutinefunction(self.connection.close):
                    await self.connection.close()
                else:
                    self.connection.close()
            self.connection = None


@executable_node
@node_schema(
    PropertyDef(
        "db_type",
        PropertyType.CHOICE,
        default="sqlite",
        choices=["sqlite", "postgresql", "mysql"],
        label="Database Type",
        tooltip="Type of database to connect to",
    ),
    PropertyDef(
        "host",
        PropertyType.STRING,
        default="localhost",
        label="Host",
        tooltip="Database server host (PostgreSQL/MySQL)",
    ),
    PropertyDef(
        "port",
        PropertyType.INTEGER,
        default=5432,
        label="Port",
        tooltip="Database server port",
    ),
    PropertyDef(
        "database",
        PropertyType.STRING,
        default="",
        label="Database",
        tooltip="Database name or SQLite file path",
        placeholder=":memory: or /path/to/database.db",
    ),
    PropertyDef(
        "username",
        PropertyType.STRING,
        default="",
        label="Username",
        tooltip="Database username (PostgreSQL/MySQL)",
    ),
    PropertyDef(
        "password",
        PropertyType.STRING,
        default="",
        label="Password",
        tooltip="Database password (PostgreSQL/MySQL)",
    ),
    PropertyDef(
        "connection_string",
        PropertyType.STRING,
        default="",
        label="Connection String",
        tooltip="Full connection string (overrides individual parameters)",
    ),
    PropertyDef(
        "timeout",
        PropertyType.FLOAT,
        default=30.0,
        min_value=0.1,
        label="Timeout (seconds)",
        tooltip="Connection timeout in seconds",
    ),
    PropertyDef(
        "ssl",
        PropertyType.BOOLEAN,
        default=False,
        label="Use SSL",
        tooltip="Use SSL for connection (PostgreSQL/MySQL)",
    ),
    PropertyDef(
        "ssl_ca",
        PropertyType.STRING,
        default="",
        label="SSL CA Certificate",
        tooltip="Path to CA certificate for SSL",
    ),
    PropertyDef(
        "pool_size",
        PropertyType.INTEGER,
        default=5,
        min_value=1,
        label="Pool Size",
        tooltip="Connection pool size (PostgreSQL/MySQL)",
    ),
    PropertyDef(
        "auto_commit",
        PropertyType.BOOLEAN,
        default=True,
        label="Auto Commit",
        tooltip="Enable auto-commit mode",
    ),
    PropertyDef(
        "charset",
        PropertyType.STRING,
        default="utf8mb4",
        label="Character Set",
        tooltip="Character set (MySQL)",
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Retry Count",
        tooltip="Number of retry attempts on connection failure",
    ),
    PropertyDef(
        "retry_interval",
        PropertyType.INTEGER,
        default=2000,
        min_value=0,
        label="Retry Interval (ms)",
        tooltip="Delay between retry attempts in milliseconds",
    ),
)
class DatabaseConnectNode(BaseNode):
    """
    Establish a database connection.

    Supports:
        - SQLite: File-based or in-memory database
        - PostgreSQL: Via asyncpg (if installed)
        - MySQL: Via aiomysql (if installed)

    Config (via @node_schema):
        db_type: Database type (sqlite, postgresql, mysql)
        host: Database host
        port: Database port
        database: Database name or file path
        username: Database username
        password: Database password
        connection_string: Full connection string (optional)
        timeout: Connection timeout
        ssl: Use SSL connection
        ssl_ca: SSL CA certificate path
        pool_size: Connection pool size
        auto_commit: Auto-commit mode
        charset: Character set (MySQL)
        retry_count: Number of retries on failure
        retry_interval: Delay between retries (ms)

    Inputs:
        db_type, host, port, database, username, password, connection_string

    Outputs:
        connection, success, error
    """

    def __init__(
        self, node_id: str, name: str = "Database Connect", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DatabaseConnectNode"

    def _define_ports(self) -> None:
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
            db_type = self.get_parameter("db_type", "sqlite").lower()
            host = self.get_parameter("host", "localhost")
            port = self.get_parameter("port", 5432)
            database = self.get_parameter("database", "")
            username = self.get_parameter("username", "")
            password = self.get_parameter("password", "")
            connection_string = self.get_parameter("connection_string", "")
            retry_count = self.get_parameter("retry_count", 0)
            retry_interval = self.get_parameter("retry_interval", 2000)

            # Resolve {{variable}} patterns in connection parameters
            host = context.resolve_value(host)
            database = context.resolve_value(database)
            username = context.resolve_value(username)
            password = context.resolve_value(password)
            connection_string = context.resolve_value(connection_string)

            logger.info(f"Connecting to {db_type} database")

            last_error: Optional[Exception] = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(
                            f"Retry attempt {attempts - 1}/{retry_count} for database connection"
                        )

                    connection: Optional[DatabaseConnection] = None

                    if db_type == "sqlite":
                        connection = await self._connect_sqlite(database)
                    elif db_type == "postgresql":
                        connection = await self._connect_postgresql(
                            host, port, database, username, password, connection_string
                        )
                    elif db_type == "mysql":
                        connection = await self._connect_mysql(
                            host, port, database, username, password
                        )
                    else:
                        raise ValueError(f"Unsupported database type: {db_type}")

                    self.set_output_value("connection", connection)
                    self.set_output_value("success", True)
                    self.set_output_value("error", "")

                    logger.info(f"Connected to {db_type} database (attempt {attempts})")

                    self.status = NodeStatus.SUCCESS
                    return {
                        "success": True,
                        "data": {"db_type": db_type, "attempts": attempts},
                        "next_nodes": ["exec_out"],
                    }

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(
                            f"Database connection failed (attempt {attempts}): {e}"
                        )
                        await asyncio.sleep(retry_interval / 1000)
                    else:
                        break

            if last_error:
                raise last_error
            raise RuntimeError("Connection failed with no error captured")

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
        connection_string: str,
    ) -> DatabaseConnection:
        """Connect to PostgreSQL database."""
        if not ASYNCPG_AVAILABLE:
            raise ImportError(
                "asyncpg is required for PostgreSQL support. Install with: pip install asyncpg"
            )

        if connection_string:
            conn = await asyncpg.connect(connection_string)
        else:
            conn = await asyncpg.connect(
                host=host,
                port=int(port),
                database=database,
                user=username,
                password=password,
            )

        return DatabaseConnection(
            "postgresql", conn, f"postgresql://{host}:{port}/{database}"
        )

    async def _connect_mysql(
        self, host: str, port: int, database: str, username: str, password: str
    ) -> DatabaseConnection:
        """Connect to MySQL database."""
        if not AIOMYSQL_AVAILABLE:
            raise ImportError(
                "aiomysql is required for MySQL support. Install with: pip install aiomysql"
            )

        conn = await aiomysql.connect(
            host=host, port=int(port), db=database, user=username, password=password
        )

        return DatabaseConnection("mysql", conn, f"mysql://{host}:{port}/{database}")


@executable_node
@node_schema(
    PropertyDef(
        "query",
        PropertyType.STRING,
        default="",
        label="SQL Query",
        tooltip="SELECT query to execute",
        placeholder="SELECT * FROM users WHERE id = ?",
    ),
    PropertyDef(
        "parameters",
        PropertyType.LIST,
        default=[],
        label="Query Parameters",
        tooltip="Parameterized query values (for safe queries)",
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Retry Count",
        tooltip="Number of retry attempts on failure",
    ),
    PropertyDef(
        "retry_interval",
        PropertyType.INTEGER,
        default=1000,
        min_value=0,
        label="Retry Interval (ms)",
        tooltip="Delay between retry attempts in milliseconds",
    ),
)
class ExecuteQueryNode(BaseNode):
    """
    Execute a SELECT query and return results.

    Config (via @node_schema):
        query: SQL SELECT query
        parameters: Query parameters for parameterized queries
        retry_count: Number of retries on failure
        retry_interval: Delay between retries (ms)

    Inputs:
        connection, query, parameters

    Outputs:
        results, row_count, columns, success, error
    """

    def __init__(
        self, node_id: str, name: str = "Execute Query", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ExecuteQueryNode"

    def _define_ports(self) -> None:
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
            connection: Optional[DatabaseConnection] = self.get_input_value(
                "connection"
            )
            query = self.get_parameter("query", "")
            parameters = self.get_parameter("parameters", [])
            retry_count = self.get_parameter("retry_count", 0)
            retry_interval = self.get_parameter("retry_interval", 1000)

            if not connection:
                raise ValueError("Database connection is required")
            if not query:
                raise ValueError("Query is required")

            # Resolve {{variable}} patterns in query
            query = context.resolve_value(query)

            logger.debug(f"Executing query: {query[:100]}...")

            last_error: Optional[Exception] = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(
                            f"Retry attempt {attempts - 1}/{retry_count} for query"
                        )

                    results: List[Dict[str, Any]] = []
                    columns: List[str] = []

                    if connection.db_type == "sqlite":
                        results, columns = await self._execute_sqlite(
                            connection, query, parameters
                        )
                    elif connection.db_type == "postgresql":
                        results, columns = await self._execute_postgresql(
                            connection, query, parameters
                        )
                    elif connection.db_type == "mysql":
                        results, columns = await self._execute_mysql(
                            connection, query, parameters
                        )

                    connection.last_results = results

                    self.set_output_value("results", results)
                    self.set_output_value("row_count", len(results))
                    self.set_output_value("columns", columns)
                    self.set_output_value("success", True)
                    self.set_output_value("error", "")

                    logger.debug(
                        f"Query returned {len(results)} rows (attempt {attempts})"
                    )

                    self.status = NodeStatus.SUCCESS
                    return {
                        "success": True,
                        "data": {"row_count": len(results), "attempts": attempts},
                        "next_nodes": ["exec_out"],
                    }

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(
                            f"Query execution failed (attempt {attempts}): {e}"
                        )
                        await asyncio.sleep(retry_interval / 1000)
                    else:
                        break

            if last_error:
                raise last_error
            raise RuntimeError("Query failed with no error captured")

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
        self, connection: DatabaseConnection, query: str, parameters: List[Any]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Execute query on SQLite."""
        conn = connection.connection

        if AIOSQLITE_AVAILABLE:
            cursor = await conn.execute(query, parameters or [])
            rows = await cursor.fetchall()
            columns = (
                [desc[0] for desc in cursor.description] if cursor.description else []
            )
            results = [dict(zip(columns, row)) for row in rows]
        else:
            cursor = conn.execute(query, parameters or [])
            rows = cursor.fetchall()
            columns = (
                [desc[0] for desc in cursor.description] if cursor.description else []
            )
            results = [dict(zip(columns, row)) for row in rows]

        return results, columns

    async def _execute_postgresql(
        self, connection: DatabaseConnection, query: str, parameters: List[Any]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Execute query on PostgreSQL."""
        conn = connection.connection

        # asyncpg uses $1, $2 for parameters
        rows = (
            await conn.fetch(query, *parameters)
            if parameters
            else await conn.fetch(query)
        )

        if rows:
            columns = list(rows[0].keys())
            results = [dict(row) for row in rows]
        else:
            columns = []
            results = []

        return results, columns

    async def _execute_mysql(
        self, connection: DatabaseConnection, query: str, parameters: List[Any]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Execute query on MySQL."""
        conn = connection.connection

        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, parameters or [])
            rows = await cursor.fetchall()
            columns = (
                [desc[0] for desc in cursor.description] if cursor.description else []
            )

        return list(rows), columns


@executable_node
@node_schema(
    PropertyDef(
        "query",
        PropertyType.STRING,
        default="",
        label="SQL Statement",
        tooltip="INSERT, UPDATE, DELETE, or DDL statement",
        placeholder="INSERT INTO users (name) VALUES (?)",
    ),
    PropertyDef(
        "parameters",
        PropertyType.LIST,
        default=[],
        label="Query Parameters",
        tooltip="Parameterized query values (for safe queries)",
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Retry Count",
        tooltip="Number of retry attempts on failure",
    ),
    PropertyDef(
        "retry_interval",
        PropertyType.INTEGER,
        default=1000,
        min_value=0,
        label="Retry Interval (ms)",
        tooltip="Delay between retry attempts in milliseconds",
    ),
)
class ExecuteNonQueryNode(BaseNode):
    """
    Execute INSERT, UPDATE, DELETE, or DDL statements.

    Config (via @node_schema):
        query: SQL statement
        parameters: Query parameters for parameterized queries
        retry_count: Number of retries on failure
        retry_interval: Delay between retries (ms)

    Inputs:
        connection, query, parameters

    Outputs:
        rows_affected, last_insert_id, success, error
    """

    def __init__(
        self, node_id: str, name: str = "Execute Non-Query", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ExecuteNonQueryNode"

    def _define_ports(self) -> None:
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
            connection: Optional[DatabaseConnection] = self.get_input_value(
                "connection"
            )
            query = self.get_parameter("query", "")
            parameters = self.get_parameter("parameters", [])
            retry_count = self.get_parameter("retry_count", 0)
            retry_interval = self.get_parameter("retry_interval", 1000)

            if not connection:
                raise ValueError("Database connection is required")
            if not query:
                raise ValueError("Query is required")

            # Resolve {{variable}} patterns in query
            query = context.resolve_value(query)

            logger.debug(f"Executing statement: {query[:100]}...")

            last_error: Optional[Exception] = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(
                            f"Retry attempt {attempts - 1}/{retry_count} for statement"
                        )

                    rows_affected = 0
                    last_insert_id: Optional[int] = None

                    if connection.db_type == "sqlite":
                        rows_affected, last_insert_id = await self._execute_sqlite(
                            connection, query, parameters
                        )
                    elif connection.db_type == "postgresql":
                        rows_affected, last_insert_id = await self._execute_postgresql(
                            connection, query, parameters
                        )
                    elif connection.db_type == "mysql":
                        rows_affected, last_insert_id = await self._execute_mysql(
                            connection, query, parameters
                        )

                    connection.last_rowcount = rows_affected
                    connection.last_lastrowid = last_insert_id

                    self.set_output_value("rows_affected", rows_affected)
                    self.set_output_value("last_insert_id", last_insert_id)
                    self.set_output_value("success", True)
                    self.set_output_value("error", "")

                    logger.debug(
                        f"Statement affected {rows_affected} rows (attempt {attempts})"
                    )

                    self.status = NodeStatus.SUCCESS
                    return {
                        "success": True,
                        "data": {"rows_affected": rows_affected, "attempts": attempts},
                        "next_nodes": ["exec_out"],
                    }

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(
                            f"Statement execution failed (attempt {attempts}): {e}"
                        )
                        await asyncio.sleep(retry_interval / 1000)
                    else:
                        break

            if last_error:
                raise last_error
            raise RuntimeError("Statement failed with no error captured")

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
        self, connection: DatabaseConnection, query: str, parameters: List[Any]
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
        self, connection: DatabaseConnection, query: str, parameters: List[Any]
    ) -> Tuple[int, Optional[int]]:
        """Execute non-query on PostgreSQL."""
        conn = connection.connection

        # asyncpg returns status string like "INSERT 0 1" or "UPDATE 5"
        result = (
            await conn.execute(query, *parameters)
            if parameters
            else await conn.execute(query)
        )

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
        self, connection: DatabaseConnection, query: str, parameters: List[Any]
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


@executable_node
class BeginTransactionNode(BaseNode):
    """
    Begin a database transaction.

    Inputs:
        connection: Database connection

    Outputs:
        connection: Connection with active transaction
        success: True if transaction started
        error: Error message if failed
    """

    def __init__(
        self, node_id: str, name: str = "Begin Transaction", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "BeginTransactionNode"

    def _define_ports(self) -> None:
        self.add_input_port("connection", PortType.INPUT, DataType.ANY)

        self.add_output_port("connection", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING
        connection: Optional[DatabaseConnection] = None

        try:
            connection = self.get_input_value("connection")

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
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = f"Begin transaction error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("connection", connection)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


@executable_node
class CommitTransactionNode(BaseNode):
    """
    Commit the current database transaction.

    Inputs:
        connection: Database connection with active transaction

    Outputs:
        connection: Connection (transaction ended)
        success: True if commit succeeded
        error: Error message if failed
    """

    def __init__(
        self, node_id: str, name: str = "Commit Transaction", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "CommitTransactionNode"

    def _define_ports(self) -> None:
        self.add_input_port("connection", PortType.INPUT, DataType.ANY)

        self.add_output_port("connection", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING
        connection: Optional[DatabaseConnection] = None

        try:
            connection = self.get_input_value("connection")

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
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = f"Commit transaction error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("connection", connection)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


@executable_node
class RollbackTransactionNode(BaseNode):
    """
    Rollback the current database transaction.

    Inputs:
        connection: Database connection with active transaction

    Outputs:
        connection: Connection (transaction ended)
        success: True if rollback succeeded
        error: Error message if failed
    """

    def __init__(
        self, node_id: str, name: str = "Rollback Transaction", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RollbackTransactionNode"

    def _define_ports(self) -> None:
        self.add_input_port("connection", PortType.INPUT, DataType.ANY)

        self.add_output_port("connection", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING
        connection: Optional[DatabaseConnection] = None

        try:
            connection = self.get_input_value("connection")

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
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = f"Rollback transaction error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("connection", connection)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


@executable_node
class CloseDatabaseNode(BaseNode):
    """
    Close a database connection.

    Inputs:
        connection: Database connection to close

    Outputs:
        success: True if connection closed
        error: Error message if failed
    """

    def __init__(
        self, node_id: str, name: str = "Close Database", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "CloseDatabaseNode"

    def _define_ports(self) -> None:
        self.add_input_port("connection", PortType.INPUT, DataType.ANY)

        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            connection: Optional[DatabaseConnection] = self.get_input_value(
                "connection"
            )

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
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = f"Close connection error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


@executable_node
@node_schema(
    PropertyDef(
        "statements",
        PropertyType.LIST,
        default=[],
        label="SQL Statements",
        tooltip="List of SQL statements to execute as a batch",
    ),
    PropertyDef(
        "stop_on_error",
        PropertyType.BOOLEAN,
        default=True,
        label="Stop on Error",
        tooltip="Stop batch execution on first error",
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Retry Count (per statement)",
        tooltip="Number of retry attempts per statement on failure",
    ),
    PropertyDef(
        "retry_interval",
        PropertyType.INTEGER,
        default=1000,
        min_value=0,
        label="Retry Interval (ms)",
        tooltip="Delay between retry attempts in milliseconds",
    ),
)
class ExecuteBatchNode(BaseNode):
    """
    Execute multiple SQL statements as a batch.

    Config (via @node_schema):
        statements: List of SQL statements
        stop_on_error: Stop on first error
        retry_count: Number of retries per statement
        retry_interval: Delay between retries (ms)

    Inputs:
        connection, statements

    Outputs:
        results, total_rows_affected, success, error
    """

    def __init__(
        self, node_id: str, name: str = "Execute Batch", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ExecuteBatchNode"

    def _define_ports(self) -> None:
        self.add_input_port("connection", PortType.INPUT, DataType.ANY)
        self.add_input_port("statements", PortType.INPUT, DataType.LIST)

        self.add_output_port("results", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("total_rows_affected", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            connection: Optional[DatabaseConnection] = self.get_input_value(
                "connection"
            )
            statements = self.get_parameter("statements", [])
            stop_on_error = self.get_parameter("stop_on_error", True)
            retry_count = self.get_parameter("retry_count", 0)
            retry_interval = self.get_parameter("retry_interval", 1000)

            if not connection:
                raise ValueError("Database connection is required")
            if not statements:
                raise ValueError("Statements list is required")

            logger.debug(f"Executing batch of {len(statements)} statements")

            results: List[Dict[str, Any]] = []
            total_rows = 0
            errors: List[str] = []

            for i, stmt in enumerate(statements):
                # Per-statement retry logic
                stmt_attempts = 0
                stmt_max_attempts = retry_count + 1
                stmt_success = False

                while stmt_attempts < stmt_max_attempts and not stmt_success:
                    try:
                        stmt_attempts += 1
                        if stmt_attempts > 1:
                            logger.info(
                                f"Retry attempt {stmt_attempts - 1}/{retry_count} for statement {i}"
                            )

                        rows = 0
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

                        results.append(
                            {
                                "statement": i,
                                "rows_affected": rows,
                                "success": True,
                                "attempts": stmt_attempts,
                            }
                        )
                        total_rows += rows
                        stmt_success = True

                    except Exception as e:
                        if stmt_attempts < stmt_max_attempts:
                            logger.warning(
                                f"Statement {i} failed (attempt {stmt_attempts}): {e}"
                            )
                            await asyncio.sleep(retry_interval / 1000)
                        else:
                            # All retries exhausted for this statement
                            results.append(
                                {
                                    "statement": i,
                                    "rows_affected": 0,
                                    "success": False,
                                    "error": str(e),
                                    "attempts": stmt_attempts,
                                }
                            )
                            errors.append(f"Statement {i}: {str(e)}")
                            if stop_on_error:
                                break

                # If stop_on_error and we had an error, break outer loop
                if stop_on_error and not stmt_success:
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

            logger.debug(
                f"Batch executed {len(statements)} statements, {total_rows} rows affected"
            )

            self.status = NodeStatus.SUCCESS if all_success else NodeStatus.ERROR
            return {
                "success": all_success,
                "data": {"statements": len(statements), "rows_affected": total_rows},
                "next_nodes": ["exec_out"] if all_success else [],
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
    # Driver availability flags
    "AIOSQLITE_AVAILABLE",
    "ASYNCPG_AVAILABLE",
    "AIOMYSQL_AVAILABLE",
    # Connection wrapper
    "DatabaseConnection",
    # Core SQL nodes
    "DatabaseConnectNode",
    "ExecuteQueryNode",
    "ExecuteNonQueryNode",
    "BeginTransactionNode",
    "CommitTransactionNode",
    "RollbackTransactionNode",
    "CloseDatabaseNode",
    "ExecuteBatchNode",
]
