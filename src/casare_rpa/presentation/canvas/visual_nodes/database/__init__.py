"""
Database Visual Nodes Package for CasareRPA.

This package provides visual representations of database nodes for the canvas.
Includes all database connection, query, and utility nodes with proper theming.

Modules:
    - nodes: Main visual node implementations

Exported Classes:
    - VisualDatabaseConnectNode
    - VisualExecuteQueryNode
    - VisualExecuteNonQueryNode
    - VisualBeginTransactionNode
    - VisualCommitTransactionNode
    - VisualRollbackTransactionNode
    - VisualCloseDatabaseNode
    - VisualExecuteBatchNode
    - VisualTableExistsNode
    - VisualGetTableColumnsNode
    - VisualDatabaseSuperNode
"""

from .nodes import (
    VisualBeginTransactionNode,
    VisualCloseDatabaseNode,
    VisualCommitTransactionNode,
    # Core database visual nodes
    VisualDatabaseConnectNode,
    # Super node
    VisualDatabaseSuperNode,
    VisualExecuteBatchNode,
    VisualExecuteNonQueryNode,
    VisualExecuteQueryNode,
    VisualGetTableColumnsNode,
    VisualRollbackTransactionNode,
    # Utility visual nodes
    VisualTableExistsNode,
)

__all__ = [
    # Core database visual nodes
    "VisualDatabaseConnectNode",
    "VisualExecuteQueryNode",
    "VisualExecuteNonQueryNode",
    "VisualBeginTransactionNode",
    "VisualCommitTransactionNode",
    "VisualRollbackTransactionNode",
    "VisualCloseDatabaseNode",
    "VisualExecuteBatchNode",
    # Utility visual nodes
    "VisualTableExistsNode",
    "VisualGetTableColumnsNode",
    # Super node
    "VisualDatabaseSuperNode",
]
