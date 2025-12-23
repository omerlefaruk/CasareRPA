"""
CasareRPA - Database Super Node

Consolidates all database operations into a single configurable node.
Supports SQLite, PostgreSQL, and MySQL with connection pooling.
"""

from __future__ import annotations

import asyncio
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from loguru import logger

from casare_rpa.domain.credentials import CREDENTIAL_NAME_PROP, CredentialAwareMixin
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)

if TYPE_CHECKING:
    from casare_rpa.infrastructure.execution import ExecutionContext

# Import database utilities from sql_nodes
from casare_rpa.nodes.database.sql_nodes import (
    AIOMYSQL_AVAILABLE,
    AIOSQLITE_AVAILABLE,
    ASYNCPG_AVAILABLE,
    DatabaseConnection,
    _check_sql_injection_risk,
    _parse_postgresql_result,
)


class DatabaseAction(str, Enum):
    """Database operations."""

    CONNECT = "Connect"
    QUERY = "Query (SELECT)"
    EXECUTE = "Execute (INSERT/UPDATE/DELETE)"
    BEGIN_TRANSACTION = "Begin Transaction"
    COMMIT = "Commit"
    ROLLBACK = "Rollback"
    CLOSE = "Close Connection"
    BATCH = "Execute Batch"


@properties(
    PropertyDef(
        "action",
        PropertyType.CHOICE,
        default=DatabaseAction.QUERY.value,
        choices=[a.value for a in DatabaseAction],
        label="Action",
        tooltip="Database operation to perform",
        essential=True,
    ),
    # Connection properties (CONNECT action)
    CREDENTIAL_NAME_PROP,
    PropertyDef(
        "db_type",
        PropertyType.CHOICE,
        default="sqlite",
        choices=["sqlite", "postgresql", "mysql"],
        label="Database Type",
        tooltip="Type of database to connect to",
        display_when={"action": DatabaseAction.CONNECT.value},
    ),
    PropertyDef(
        "host",
        PropertyType.STRING,
        default="localhost",
        label="Host",
        tooltip="Database server host",
        display_when={"action": DatabaseAction.CONNECT.value},
    ),
    PropertyDef(
        "port",
        PropertyType.INTEGER,
        default=5432,
        label="Port",
        tooltip="Database server port",
        display_when={"action": DatabaseAction.CONNECT.value},
    ),
    PropertyDef(
        "database",
        PropertyType.STRING,
        default="",
        label="Database",
        tooltip="Database name or SQLite file path",
        placeholder=":memory: or /path/to/db.sqlite",
        display_when={"action": DatabaseAction.CONNECT.value},
    ),
    PropertyDef(
        "username",
        PropertyType.STRING,
        default="",
        label="Username",
        tooltip="Database username",
        tab="connection",
        display_when={"action": DatabaseAction.CONNECT.value},
    ),
    PropertyDef(
        "password",
        PropertyType.STRING,
        default="",
        label="Password",
        tooltip="Database password",
        tab="connection",
        display_when={"action": DatabaseAction.CONNECT.value},
    ),
    PropertyDef(
        "connection_string",
        PropertyType.STRING,
        default="",
        label="Connection String",
        tooltip="Full connection string (overrides individual parameters)",
        tab="connection",
        display_when={"action": DatabaseAction.CONNECT.value},
    ),
    PropertyDef(
        "pool_size",
        PropertyType.INTEGER,
        default=5,
        min_value=1,
        label="Pool Size",
        tooltip="Connection pool size",
        tab="advanced",
        display_when={"action": DatabaseAction.CONNECT.value},
    ),
    PropertyDef(
        "timeout",
        PropertyType.FLOAT,
        default=30.0,
        min_value=0.1,
        label="Timeout (seconds)",
        tooltip="Connection timeout",
        tab="advanced",
        display_when={"action": DatabaseAction.CONNECT.value},
    ),
    PropertyDef(
        "use_ssl",
        PropertyType.BOOLEAN,
        default=False,
        label="Use SSL",
        tooltip="Use SSL for connection",
        tab="advanced",
        display_when={"action": DatabaseAction.CONNECT.value},
    ),
    # Query properties (QUERY and EXECUTE actions)
    PropertyDef(
        "query",
        PropertyType.TEXT,
        default="",
        label="SQL Query",
        tooltip="SQL query or statement to execute",
        placeholder="SELECT * FROM users WHERE id = ?",
        display_when={"action": [DatabaseAction.QUERY.value, DatabaseAction.EXECUTE.value]},
    ),
    PropertyDef(
        "parameters",
        PropertyType.JSON,
        default=[],
        label="Query Parameters",
        tooltip="Parameterized query values (list for positional, dict for named)",
        display_when={"action": [DatabaseAction.QUERY.value, DatabaseAction.EXECUTE.value]},
    ),
    # Batch properties
    PropertyDef(
        "statements",
        PropertyType.JSON,
        default=[],
        label="SQL Statements",
        tooltip="List of SQL statements to execute as a batch",
        display_when={"action": DatabaseAction.BATCH.value},
    ),
    PropertyDef(
        "stop_on_error",
        PropertyType.BOOLEAN,
        default=True,
        label="Stop on Error",
        tooltip="Stop batch execution on first error",
        display_when={"action": DatabaseAction.BATCH.value},
    ),
    # Retry options (multiple actions)
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Retry Count",
        tooltip="Number of retry attempts on failure",
        tab="advanced",
    ),
    PropertyDef(
        "retry_interval",
        PropertyType.INTEGER,
        default=1000,
        min_value=0,
        label="Retry Interval (ms)",
        tooltip="Delay between retry attempts",
        tab="advanced",
    ),
)
@node(category="database")
class DatabaseSuperNode(CredentialAwareMixin, BaseNode):
    """
    Unified database operations node.

    Consolidates all database operations:
    - CONNECT: Establish database connection (SQLite, PostgreSQL, MySQL)
    - QUERY: Execute SELECT queries and return results
    - EXECUTE: Run INSERT, UPDATE, DELETE, DDL statements
    - BEGIN_TRANSACTION: Start a database transaction
    - COMMIT: Commit the current transaction
    - ROLLBACK: Rollback the current transaction
    - CLOSE: Close the database connection
    - BATCH: Execute multiple SQL statements

    Features:
    - Connection pooling for PostgreSQL and MySQL
    - Parameterized queries for SQL injection protection
    - Transaction support
    - Retry logic with configurable intervals
    - Credential resolution via vault
    """

    NODE_NAME = "Database"
    NODE_CATEGORY = "Data"
    NODE_DESCRIPTION = "Unified database operations (Connect, Query, Execute, Transaction)"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = self.NODE_NAME
        self.node_type = "DatabaseSuperNode"

    def _define_ports(self) -> None:
        """Define dynamic ports based on action."""
        # Execution ports
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_exec_output("exec_error")

        # Common input
        self.add_input_port("action", DataType.STRING, required=False)

        # Connection input (for all actions except CONNECT)
        self.add_input_port("connection", DataType.ANY, required=False)

        # Connect action inputs
        self.add_input_port("db_type", DataType.STRING, required=False)
        self.add_input_port("host", DataType.STRING, required=False)
        self.add_input_port("port", DataType.INTEGER, required=False)
        self.add_input_port("database", DataType.STRING, required=False)
        self.add_input_port("username", DataType.STRING, required=False)
        self.add_input_port("password", DataType.STRING, required=False)
        self.add_input_port("connection_string", DataType.STRING, required=False)

        # Query/Execute inputs
        self.add_input_port("query", DataType.STRING, required=False)
        self.add_input_port("parameters", DataType.LIST, required=False)

        # Batch inputs
        self.add_input_port("statements", DataType.LIST, required=False)

        # Outputs
        self.add_output_port("connection", DataType.ANY)
        self.add_output_port("results", DataType.LIST)
        self.add_output_port("row_count", DataType.INTEGER)
        self.add_output_port("columns", DataType.LIST)
        self.add_output_port("rows_affected", DataType.INTEGER)
        self.add_output_port("last_insert_id", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute the selected database action."""
        self.status = NodeStatus.RUNNING

        action = self.get_parameter("action", DatabaseAction.QUERY.value)

        handlers = {
            DatabaseAction.CONNECT.value: self._execute_connect,
            DatabaseAction.QUERY.value: self._execute_query,
            DatabaseAction.EXECUTE.value: self._execute_statement,
            DatabaseAction.BEGIN_TRANSACTION.value: self._execute_begin_transaction,
            DatabaseAction.COMMIT.value: self._execute_commit,
            DatabaseAction.ROLLBACK.value: self._execute_rollback,
            DatabaseAction.CLOSE.value: self._execute_close,
            DatabaseAction.BATCH.value: self._execute_batch,
        }

        handler = handlers.get(action)
        if not handler:
            return self._error_result(f"Unknown action: {action}")

        try:
            return await handler(context)
        except Exception as e:
            logger.error(f"Database {action} error: {e}")
            return self._error_result(str(e))

    async def _execute_connect(self, context: ExecutionContext) -> ExecutionResult:
        """Connect to database."""
        import sqlite3

        try:
            import aiosqlite
        except ImportError:
            aiosqlite = None

        db_type = self.get_parameter("db_type", "sqlite").lower()
        host = self.get_parameter("host", "localhost")
        port = self.get_parameter("port", 5432)
        database = self.get_parameter("database", "")
        pool_size = self.get_parameter("pool_size", 5)
        retry_count = self.get_parameter("retry_count", 0)
        retry_interval = self.get_parameter("retry_interval", 1000)

        # Resolve credentials
        username, password = await self.resolve_username_password(
            context,
            credential_name_param="credential_name",
            username_param="username",
            password_param="password",
            env_prefix="DB",
            required=False,
        )

        connection_string = (
            await self.resolve_credential(
                context,
                credential_name_param="credential_name",
                direct_param="connection_string",
                env_var="DATABASE_URL",
                credential_field="connection_string",
                required=False,
            )
            or ""
        )

        # Resolve variable patterns

        logger.info(f"Connecting to {db_type} database")

        last_error: Exception | None = None
        attempts = 0
        max_attempts = retry_count + 1

        while attempts < max_attempts:
            try:
                attempts += 1
                if attempts > 1:
                    logger.info(f"Retry attempt {attempts - 1}/{retry_count}")

                connection: DatabaseConnection | None = None

                if db_type == "sqlite":
                    if not database:
                        database = ":memory:"
                    if aiosqlite and AIOSQLITE_AVAILABLE:
                        conn = await aiosqlite.connect(database)
                        conn.row_factory = aiosqlite.Row
                    else:
                        conn = sqlite3.connect(database)
                        conn.row_factory = sqlite3.Row
                    connection = DatabaseConnection("sqlite", conn, database)

                elif db_type == "postgresql":
                    if not ASYNCPG_AVAILABLE:
                        raise ImportError("asyncpg required for PostgreSQL")
                    import asyncpg

                    if connection_string:
                        pool = await asyncpg.create_pool(
                            connection_string, min_size=1, max_size=pool_size
                        )
                    else:
                        pool = await asyncpg.create_pool(
                            host=host,
                            port=int(port),
                            database=database,
                            user=username,
                            password=password,
                            min_size=1,
                            max_size=pool_size,
                        )
                    connection = DatabaseConnection("postgresql", None, is_pool=True, pool=pool)

                elif db_type == "mysql":
                    if not AIOMYSQL_AVAILABLE:
                        raise ImportError("aiomysql required for MySQL")
                    import aiomysql

                    pool = await aiomysql.create_pool(
                        host=host,
                        port=int(port),
                        db=database,
                        user=username,
                        password=password,
                        minsize=1,
                        maxsize=pool_size,
                    )
                    connection = DatabaseConnection("mysql", None, is_pool=True, pool=pool)

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
                    "next_nodes": ["exec_out"],
                }

            except Exception as e:
                last_error = e
                if attempts < max_attempts:
                    await asyncio.sleep(retry_interval / 1000)
                else:
                    break

        if last_error:
            raise last_error
        raise RuntimeError("Connection failed")

    async def _execute_query(self, context: ExecutionContext) -> ExecutionResult:
        """Execute SELECT query."""
        connection: DatabaseConnection | None = self.get_input_value("connection")
        query = self.get_parameter("query", "")
        parameters = self.get_parameter("parameters", [])
        retry_count = self.get_parameter("retry_count", 0)
        retry_interval = self.get_parameter("retry_interval", 1000)

        if not connection:
            return self._error_result("Database connection is required")
        if not query:
            return self._error_result("Query is required")

        if hasattr(context, "resolve_value"):
            original_query = query
            _check_sql_injection_risk(original_query, query, "DatabaseSuperNode")

        logger.debug(f"Executing query: {query[:100]}...")

        last_error: Exception | None = None
        attempts = 0
        max_attempts = retry_count + 1

        while attempts < max_attempts:
            try:
                attempts += 1
                results: list[dict[str, Any]] = []
                columns: list[str] = []

                if connection.db_type == "sqlite":
                    results, columns = await self._query_sqlite(connection, query, parameters)
                elif connection.db_type == "postgresql":
                    results, columns = await self._query_postgresql(connection, query, parameters)
                elif connection.db_type == "mysql":
                    results, columns = await self._query_mysql(connection, query, parameters)

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
                    "next_nodes": ["exec_out"],
                }

            except Exception as e:
                last_error = e
                if attempts < max_attempts:
                    await asyncio.sleep(retry_interval / 1000)
                else:
                    break

        if last_error:
            raise last_error
        raise RuntimeError("Query failed")

    async def _execute_statement(self, context: ExecutionContext) -> ExecutionResult:
        """Execute INSERT/UPDATE/DELETE statement."""
        connection: DatabaseConnection | None = self.get_input_value("connection")
        query = self.get_parameter("query", "")
        parameters = self.get_parameter("parameters", [])
        retry_count = self.get_parameter("retry_count", 0)
        retry_interval = self.get_parameter("retry_interval", 1000)

        if not connection:
            return self._error_result("Database connection is required")
        if not query:
            return self._error_result("Query is required")

        if hasattr(context, "resolve_value"):
            original_query = query
            _check_sql_injection_risk(original_query, query, "DatabaseSuperNode")

        logger.debug(f"Executing statement: {query[:100]}...")

        last_error: Exception | None = None
        attempts = 0
        max_attempts = retry_count + 1

        while attempts < max_attempts:
            try:
                attempts += 1
                rows_affected = 0
                last_insert_id: int | None = None

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

                self.set_output_value("rows_affected", rows_affected)
                self.set_output_value("last_insert_id", last_insert_id or 0)
                self.set_output_value("success", True)
                self.set_output_value("error", "")

                logger.debug(f"Statement affected {rows_affected} rows")
                self.status = NodeStatus.SUCCESS
                return {
                    "success": True,
                    "data": {"rows_affected": rows_affected},
                    "next_nodes": ["exec_out"],
                }

            except Exception as e:
                last_error = e
                if attempts < max_attempts:
                    await asyncio.sleep(retry_interval / 1000)
                else:
                    break

        if last_error:
            raise last_error
        raise RuntimeError("Statement failed")

    async def _execute_begin_transaction(self, context: ExecutionContext) -> ExecutionResult:
        """Begin database transaction."""
        connection: DatabaseConnection | None = self.get_input_value("connection")

        if not connection:
            return self._error_result("Database connection is required")
        if connection.in_transaction:
            return self._error_result("Transaction already in progress")

        if connection.db_type == "postgresql":
            conn = await connection.acquire()
            connection._transaction = conn.transaction()
            await connection._transaction.start()
        elif connection.db_type == "mysql":
            conn = await connection.acquire()
            await conn.begin()

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

    async def _execute_commit(self, context: ExecutionContext) -> ExecutionResult:
        """Commit database transaction."""
        connection: DatabaseConnection | None = self.get_input_value("connection")

        if not connection:
            return self._error_result("Database connection is required")

        if connection.db_type == "sqlite":
            conn = connection.connection
            if AIOSQLITE_AVAILABLE:
                await conn.commit()
            else:
                conn.commit()
        elif connection.db_type == "postgresql":
            if connection._transaction:
                await connection._transaction.commit()
                connection._transaction = None
            await connection.release()
        elif connection.db_type == "mysql":
            conn = await connection.acquire()
            await conn.commit()
            await connection.release()

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

    async def _execute_rollback(self, context: ExecutionContext) -> ExecutionResult:
        """Rollback database transaction."""
        connection: DatabaseConnection | None = self.get_input_value("connection")

        if not connection:
            return self._error_result("Database connection is required")

        if connection.db_type == "sqlite":
            conn = connection.connection
            if AIOSQLITE_AVAILABLE:
                await conn.rollback()
            else:
                conn.rollback()
        elif connection.db_type == "postgresql":
            if connection._transaction:
                await connection._transaction.rollback()
                connection._transaction = None
            await connection.release()
        elif connection.db_type == "mysql":
            conn = await connection.acquire()
            await conn.rollback()
            await connection.release()

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

    async def _execute_close(self, context: ExecutionContext) -> ExecutionResult:
        """Close database connection."""
        connection: DatabaseConnection | None = self.get_input_value("connection")

        if not connection:
            return self._error_result("Database connection is required")

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

    async def _execute_batch(self, context: ExecutionContext) -> ExecutionResult:
        """Execute batch of SQL statements."""
        connection: DatabaseConnection | None = self.get_input_value("connection")
        statements = self.get_parameter("statements", [])
        stop_on_error = self.get_parameter("stop_on_error", True)
        retry_count = self.get_parameter("retry_count", 0)
        retry_interval = self.get_parameter("retry_interval", 1000)

        if not connection:
            return self._error_result("Database connection is required")
        if not statements:
            return self._error_result("Statements list is required")

        logger.debug(f"Executing batch of {len(statements)} statements")

        results: list[dict[str, Any]] = []
        total_rows = 0
        errors: list[str] = []

        pool_conn = None
        if connection.db_type in ("postgresql", "mysql"):
            pool_conn = await connection.acquire()

        try:
            for i, stmt in enumerate(statements):
                stmt_attempts = 0
                stmt_max_attempts = retry_count + 1
                stmt_success = False

                while stmt_attempts < stmt_max_attempts and not stmt_success:
                    try:
                        stmt_attempts += 1
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
                            result = await pool_conn.execute(stmt)
                            rows = _parse_postgresql_result(result)
                        elif connection.db_type == "mysql":
                            async with pool_conn.cursor() as cursor:
                                await cursor.execute(stmt)
                                rows = cursor.rowcount

                        results.append(
                            {
                                "statement": i,
                                "rows_affected": rows,
                                "success": True,
                            }
                        )
                        total_rows += rows
                        stmt_success = True

                    except Exception as e:
                        if stmt_attempts < stmt_max_attempts:
                            await asyncio.sleep(retry_interval / 1000)
                        else:
                            results.append(
                                {
                                    "statement": i,
                                    "rows_affected": 0,
                                    "success": False,
                                    "error": str(e),
                                }
                            )
                            errors.append(f"Statement {i}: {str(e)}")
                            if stop_on_error:
                                break

                if stop_on_error and not stmt_success:
                    break

            # Commit if not in transaction
            if not connection.in_transaction:
                if connection.db_type == "sqlite":
                    if AIOSQLITE_AVAILABLE:
                        await connection.connection.commit()
                    else:
                        connection.connection.commit()
                elif connection.db_type == "mysql" and pool_conn:
                    await pool_conn.commit()
        finally:
            if pool_conn and not connection.in_transaction:
                await connection.release()

        all_success = len(errors) == 0

        self.set_output_value("results", results)
        self.set_output_value("rows_affected", total_rows)
        self.set_output_value("success", all_success)
        self.set_output_value("error", "; ".join(errors) if errors else "")

        logger.debug(f"Batch: {len(statements)} statements, {total_rows} rows")
        self.status = NodeStatus.SUCCESS if all_success else NodeStatus.ERROR
        return {
            "success": all_success,
            "data": {"statements": len(statements), "rows_affected": total_rows},
            "next_nodes": ["exec_out"] if all_success else ["exec_error"],
        }

    # Database-specific query helpers
    async def _query_sqlite(
        self, connection: DatabaseConnection, query: str, parameters: list[Any]
    ) -> tuple:
        """Query SQLite database."""
        conn = connection.connection

        if AIOSQLITE_AVAILABLE:
            cursor = await conn.execute(query, parameters or [])
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            results = [dict(zip(columns, row, strict=False)) for row in rows]
        else:
            cursor = conn.execute(query, parameters or [])
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            results = [dict(zip(columns, row, strict=False)) for row in rows]

        return results, columns

    async def _query_postgresql(
        self, connection: DatabaseConnection, query: str, parameters: list[Any]
    ) -> tuple:
        """Query PostgreSQL database."""
        conn = await connection.acquire()
        try:
            rows = await conn.fetch(query, *parameters) if parameters else await conn.fetch(query)
            if rows:
                columns = list(rows[0].keys())
                results = [dict(row) for row in rows]
            else:
                columns = []
                results = []
            return results, columns
        finally:
            await connection.release()

    async def _query_mysql(
        self, connection: DatabaseConnection, query: str, parameters: list[Any]
    ) -> tuple:
        """Query MySQL database."""
        import aiomysql

        conn = await connection.acquire()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, parameters or [])
                rows = await cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
            return list(rows), columns
        finally:
            await connection.release()

    # Database-specific execute helpers
    async def _execute_sqlite(
        self, connection: DatabaseConnection, query: str, parameters: list[Any]
    ) -> tuple:
        """Execute statement on SQLite."""
        conn = connection.connection

        if AIOSQLITE_AVAILABLE:
            cursor = await conn.execute(query, parameters or [])
            if not connection.in_transaction:
                await conn.commit()
            return cursor.rowcount, cursor.lastrowid
        else:
            cursor = conn.execute(query, parameters or [])
            if not connection.in_transaction:
                conn.commit()
            return cursor.rowcount, cursor.lastrowid

    async def _execute_postgresql(
        self, connection: DatabaseConnection, query: str, parameters: list[Any]
    ) -> tuple:
        """Execute statement on PostgreSQL."""
        conn = await connection.acquire()
        try:
            result = (
                await conn.execute(query, *parameters) if parameters else await conn.execute(query)
            )
            rows_affected = _parse_postgresql_result(result)
            return rows_affected, None
        finally:
            if not connection.in_transaction:
                await connection.release()

    async def _execute_mysql(
        self, connection: DatabaseConnection, query: str, parameters: list[Any]
    ) -> tuple:
        """Execute statement on MySQL."""
        conn = await connection.acquire()
        try:
            async with conn.cursor() as cursor:
                await cursor.execute(query, parameters or [])
                if not connection.in_transaction:
                    await conn.commit()
                return cursor.rowcount, cursor.lastrowid
        finally:
            if not connection.in_transaction:
                await connection.release()

    def _error_result(self, error_msg: str) -> ExecutionResult:
        """Create error result."""
        self.set_output_value("success", False)
        self.set_output_value("error", error_msg)
        self.set_output_value("results", [])
        self.set_output_value("row_count", 0)
        self.set_output_value("rows_affected", 0)
        self.status = NodeStatus.ERROR
        return {"success": False, "error": error_msg, "next_nodes": ["exec_error"]}


__all__ = ["DatabaseSuperNode", "DatabaseAction"]
