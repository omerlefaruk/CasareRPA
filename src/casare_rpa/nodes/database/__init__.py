"""
Database Nodes Package for CasareRPA.

This package provides nodes for connecting to and interacting with databases.
Supports SQLite (built-in), PostgreSQL, MySQL/MariaDB.

Modules:
    - sql_nodes: Core database connection and query nodes
    - database_utils: Schema inspection and metadata nodes

Usage:
    from casare_rpa.nodes.database import (
        DatabaseConnectNode,
        ExecuteQueryNode,
        ExecuteNonQueryNode,
        TableExistsNode,
        GetTableColumnsNode,
    )
"""

# Re-export from sql_nodes
from casare_rpa.nodes.database.sql_nodes import (
    # Driver availability flags
    AIOSQLITE_AVAILABLE,
    ASYNCPG_AVAILABLE,
    AIOMYSQL_AVAILABLE,
    # Connection wrapper
    DatabaseConnection,
    # Core SQL nodes
    DatabaseConnectNode,
    ExecuteQueryNode,
    ExecuteNonQueryNode,
    BeginTransactionNode,
    CommitTransactionNode,
    RollbackTransactionNode,
    CloseDatabaseNode,
    ExecuteBatchNode,
)

# Re-export from database_utils
from casare_rpa.nodes.database.database_utils import (
    TableExistsNode,
    GetTableColumnsNode,
)


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
    # Utility nodes
    "TableExistsNode",
    "GetTableColumnsNode",
]
