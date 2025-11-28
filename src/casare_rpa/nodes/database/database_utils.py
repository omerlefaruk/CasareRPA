"""
Database Utility Nodes for CasareRPA.

This module provides utility nodes for database schema inspection and metadata.

Nodes:
    - TableExistsNode: Check if a table exists
    - GetTableColumnsNode: Get column information for a table
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from loguru import logger

from ...core.base_node import BaseNode
from ...core.execution_context import ExecutionContext
from ...core.types import DataType, ExecutionResult, NodeStatus, PortType

from .sql_nodes import (
    DatabaseConnection,
    AIOSQLITE_AVAILABLE,
    ASYNCPG_AVAILABLE,
    AIOMYSQL_AVAILABLE,
)

# Import aiomysql for DictCursor if available
if AIOMYSQL_AVAILABLE:
    import aiomysql


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
            connection: Optional[DatabaseConnection] = self.get_input_value(
                "connection"
            )
            table_name = self.get_input_value("table_name") or self.config.get(
                "table_name", ""
            )

            if not connection:
                raise ValueError("Database connection is required")
            if not table_name:
                raise ValueError("Table name is required")

            # Resolve {{variable}} patterns in table_name
            table_name = context.resolve_value(table_name)

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
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = f"Table exists check error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("exists", False)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

    async def _check_sqlite(
        self, connection: DatabaseConnection, table_name: str
    ) -> bool:
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

    async def _check_postgresql(
        self, connection: DatabaseConnection, table_name: str
    ) -> bool:
        """Check if table exists in PostgreSQL."""
        conn = connection.connection
        query = "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = $1)"
        result = await conn.fetchval(query, table_name)
        return result

    async def _check_mysql(
        self, connection: DatabaseConnection, table_name: str
    ) -> bool:
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

    def __init__(
        self, node_id: str, name: str = "Get Table Columns", **kwargs: Any
    ) -> None:
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
            connection: Optional[DatabaseConnection] = self.get_input_value(
                "connection"
            )
            table_name = self.get_input_value("table_name") or self.config.get(
                "table_name", ""
            )

            if not connection:
                raise ValueError("Database connection is required")
            if not table_name:
                raise ValueError("Table name is required")

            # Resolve {{variable}} patterns in table_name
            table_name = context.resolve_value(table_name)

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
                "next_nodes": ["exec_out"],
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
        self, connection: DatabaseConnection, table_name: str
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
            columns.append(
                {
                    "name": row[1],
                    "type": row[2],
                    "nullable": not row[3],
                    "default": row[4],
                    "primary_key": bool(row[5]),
                }
            )

        return columns

    async def _get_postgresql_columns(
        self, connection: DatabaseConnection, table_name: str
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
            columns.append(
                {
                    "name": row["column_name"],
                    "type": row["data_type"],
                    "nullable": row["is_nullable"] == "YES",
                    "default": row["column_default"],
                    "primary_key": False,  # Would need additional query
                }
            )

        return columns

    async def _get_mysql_columns(
        self, connection: DatabaseConnection, table_name: str
    ) -> List[Dict[str, Any]]:
        """Get column info for MySQL table."""
        conn = connection.connection
        query = f"DESCRIBE {table_name}"

        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query)
            rows = await cursor.fetchall()

        columns = []
        for row in rows:
            columns.append(
                {
                    "name": row["Field"],
                    "type": row["Type"],
                    "nullable": row["Null"] == "YES",
                    "default": row["Default"],
                    "primary_key": row["Key"] == "PRI",
                }
            )

        return columns


# Export all utility node classes
__all__ = [
    "TableExistsNode",
    "GetTableColumnsNode",
]
