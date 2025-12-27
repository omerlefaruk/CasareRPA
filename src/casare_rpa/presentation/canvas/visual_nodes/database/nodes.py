"""Visual nodes for database category."""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.database.database_super_node import (
    DatabaseAction,
    DatabaseSuperNode,
)
from casare_rpa.nodes.database.database_utils import (
    GetTableColumnsNode,
    TableExistsNode,
)

# Import logic layer nodes
from casare_rpa.nodes.database.sql_nodes import (
    AIOMYSQL_AVAILABLE,
    AIOSQLITE_AVAILABLE,
    ASYNCPG_AVAILABLE,
    BeginTransactionNode,
    CloseDatabaseNode,
    CommitTransactionNode,
    DatabaseConnectNode,
    ExecuteBatchNode,
    ExecuteNonQueryNode,
    ExecuteQueryNode,
    RollbackTransactionNode,
)
from casare_rpa.presentation.canvas.theme_system import THEME
from casare_rpa.presentation.canvas.theme_system import TOKENS
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode

# =============================================================================
# Database Nodes - Core Operations
# =============================================================================


class VisualDatabaseConnectNode(VisualNode):
    """Visual representation of DatabaseConnectNode.

    Widgets auto-generated from DatabaseConnectNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Database Connect"
    NODE_CATEGORY = "database/connection"

    def __init__(self) -> None:
        super().__init__()
        # Apply database connection node styling
        self._apply_database_node_style()
        # Widgets auto-generated from @properties on DatabaseConnectNode

    def get_node_class(self) -> type:
        return DatabaseConnectNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_output("connection_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)

    def _apply_database_node_style(self) -> None:
        """Apply specific styling for database connection node."""
        from casare_rpa.presentation.canvas.theme_system.utils import _hex_to_qcolor

        # Use database-themed color (blue accent for connections)
        accent_color = _hex_to_qcolor(THEME.primary)
        self.model.border_color = (
            accent_color.red(),
            accent_color.green(),
            accent_color.blue(),
            255,
        )

        # Set node color to slightly lighter background
        bg_color = _hex_to_qcolor(THEME.bg_surface)
        self.model.color = (
            bg_color.red(),
            bg_color.green(),
            bg_color.blue(),
            TOKENS.sizes.panel_min_width,
        )

        self.model.border_width = TOKENS.radius.sm


class VisualExecuteQueryNode(VisualNode):
    """Visual representation of ExecuteQueryNode.

    Widgets auto-generated from ExecuteQueryNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Execute Query"
    NODE_CATEGORY = "database/query"

    def __init__(self) -> None:
        super().__init__()
        # Apply database query node styling
        self._apply_database_node_style()

    def get_node_class(self) -> type:
        return ExecuteQueryNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("connection_id", DataType.STRING)
        self.add_typed_input("query", DataType.TEXT)
        self.add_typed_input("parameters", DataType.DICT, required=False)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.DICT)
        self.add_typed_output("rows_affected", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)

    def _apply_database_node_style(self) -> None:
        """Apply specific styling for database query node."""
        from casare_rpa.presentation.canvas.theme_system.utils import _hex_to_qcolor

        # Use database-themed color (blue for queries)
        accent_color = _hex_to_qcolor(THEME.primary)
        self.model.border_color = (
            accent_color.red(),
            accent_color.green(),
            accent_color.blue(),
            255,
        )

        # Set node color to slightly lighter background
        bg_color = _hex_to_qcolor(THEME.bg_surface)
        self.model.color = (
            bg_color.red(),
            bg_color.green(),
            bg_color.blue(),
            TOKENS.sizes.panel_min_width,
        )

        self.model.border_width = TOKENS.radius.sm


class VisualExecuteNonQueryNode(VisualNode):
    """Visual representation of ExecuteNonQueryNode.

    Widgets auto-generated from ExecuteNonQueryNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Execute Non-Query"
    NODE_CATEGORY = "database/query"

    def __init__(self) -> None:
        super().__init__()
        # Apply database query node styling
        self._apply_database_node_style()

    def get_node_class(self) -> type:
        return ExecuteNonQueryNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("connection_id", DataType.STRING)
        self.add_typed_input("query", DataType.TEXT)
        self.add_typed_input("parameters", DataType.DICT, required=False)
        self.add_exec_output("exec_out")
        self.add_typed_output("rows_affected", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)

    def _apply_database_node_style(self) -> None:
        """Apply specific styling for database non-query node."""
        from casare_rpa.presentation.canvas.theme_system.utils import _hex_to_qcolor

        # Use database-themed color (blue for operations)
        accent_color = _hex_to_qcolor(THEME.primary)
        self.model.border_color = (
            accent_color.red(),
            accent_color.green(),
            accent_color.blue(),
            255,
        )

        # Set node color to slightly lighter background
        bg_color = _hex_to_qcolor(THEME.bg_surface)
        self.model.color = (
            bg_color.red(),
            bg_color.green(),
            bg_color.blue(),
            TOKENS.sizes.panel_min_width,
        )

        self.model.border_width = TOKENS.radius.sm


class VisualExecuteBatchNode(VisualNode):
    """Visual representation of ExecuteBatchNode.

    Widgets auto-generated from ExecuteBatchNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Execute Batch"
    NODE_CATEGORY = "database/query"

    def __init__(self) -> None:
        super().__init__()
        # Apply database batch node styling
        self._apply_database_batch_style()

    def get_node_class(self) -> type:
        return ExecuteBatchNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("connection_id", DataType.STRING)
        self.add_typed_input("queries", DataType.LIST[DataType.TEXT])
        self.add_exec_output("exec_out")
        self.add_typed_output("results", DataType.LIST[DataType.DICT])
        self.add_typed_output("total_rows_affected", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)

    def _apply_database_batch_style(self) -> None:
        """Apply specific styling for database batch node."""
        from casare_rpa.presentation.canvas.theme_system.utils import _hex_to_qcolor

        # Use purple accent for batch operations
        accent_color = _hex_to_qcolor(THEME.primary)
        self.model.border_color = (
            accent_color.red(),
            accent_color.green(),
            accent_color.blue(),
            255,
        )

        # Set node color to slightly lighter background
        bg_color = _hex_to_qcolor(THEME.bg_surface)
        self.model.color = (
            bg_color.red(),
            bg_color.green(),
            bg_color.blue(),
            TOKENS.sizes.panel_min_width,
        )

        self.model.border_width = TOKENS.radius.sm


# =============================================================================
# Database Nodes - Transaction Management
# =============================================================================


class VisualBeginTransactionNode(VisualNode):
    """Visual representation of BeginTransactionNode.

    Widgets auto-generated from BeginTransactionNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Begin Transaction"
    NODE_CATEGORY = "database/transaction"

    def __init__(self) -> None:
        super().__init__()
        # Apply transaction node styling
        self._apply_transaction_node_style()

    def get_node_class(self) -> type:
        return BeginTransactionNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("connection_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("transaction_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)

    def _apply_transaction_node_style(self) -> None:
        """Apply specific styling for transaction node."""
        from casare_rpa.presentation.canvas.theme_system.utils import _hex_to_qcolor

        # Use teal accent for transaction operations
        accent_color = _hex_to_qcolor(THEME.primary_success)
        self.model.border_color = (
            accent_color.red(),
            accent_color.green(),
            accent_color.blue(),
            255,
        )

        # Set node color to slightly lighter background
        bg_color = _hex_to_qcolor(THEME.bg_surface)
        self.model.color = (
            bg_color.red(),
            bg_color.green(),
            bg_color.blue(),
            TOKENS.sizes.panel_min_width,
        )

        self.model.border_width = TOKENS.radius.sm


class VisualCommitTransactionNode(VisualNode):
    """Visual representation of CommitTransactionNode.

    Widgets auto-generated from CommitTransactionNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Commit Transaction"
    NODE_CATEGORY = "database/transaction"

    def __init__(self) -> None:
        super().__init__()
        # Apply transaction node styling
        self._apply_transaction_node_style()

    def get_node_class(self) -> type:
        return CommitTransactionNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("connection_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)

    def _apply_transaction_node_style(self) -> None:
        """Apply specific styling for transaction node."""
        from casare_rpa.presentation.canvas.theme_system.utils import _hex_to_qcolor

        # Use teal accent for transaction operations
        accent_color = _hex_to_qcolor(THEME.success)
        self.model.border_color = (
            accent_color.red(),
            accent_color.green(),
            accent_color.blue(),
            255,
        )

        # Set node color to slightly lighter background
        bg_color = _hex_to_qcolor(THEME.bg_surface)
        self.model.color = (
            bg_color.red(),
            bg_color.green(),
            bg_color.blue(),
            TOKENS.sizes.panel_min_width,
        )

        self.model.border_width = TOKENS.radius.sm


class VisualRollbackTransactionNode(VisualNode):
    """Visual representation of RollbackTransactionNode.

    Widgets auto-generated from RollbackTransactionNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Rollback Transaction"
    NODE_CATEGORY = "database/transaction"

    def __init__(self) -> None:
        super().__init__()
        # Apply rollback node styling
        self._apply_rollback_node_style()

    def get_node_class(self) -> type:
        return RollbackTransactionNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("connection_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)

    def _apply_rollback_node_style(self) -> None:
        """Apply specific styling for rollback node."""
        from casare_rpa.presentation.canvas.theme_system.utils import _hex_to_qcolor

        # Use warning accent for rollback operations
        accent_color = _hex_to_qcolor(THEME.warning)
        self.model.border_color = (
            accent_color.red(),
            accent_color.green(),
            accent_color.blue(),
            255,
        )

        # Set node color to slightly lighter background
        bg_color = _hex_to_qcolor(THEME.bg_surface)
        self.model.color = (
            bg_color.red(),
            bg_color.green(),
            bg_color.blue(),
            TOKENS.sizes.panel_min_width,
        )

        self.model.border_width = TOKENS.radius.sm


class VisualCloseDatabaseNode(VisualNode):
    """Visual representation of CloseDatabaseNode.

    Widgets auto-generated from CloseDatabaseNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Close Connection"
    NODE_CATEGORY = "database/connection"

    def __init__(self) -> None:
        super().__init__()
        # Apply close connection node styling
        self._apply_close_node_style()

    def get_node_class(self) -> type:
        return CloseDatabaseNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("connection_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)

    def _apply_close_node_style(self) -> None:
        """Apply specific styling for close connection node."""
        from casare_rpa.presentation.canvas.theme_system.utils import _hex_to_qcolor

        # Use error accent for close operations
        accent_color = _hex_to_qcolor(THEME.error)
        self.model.border_color = (
            accent_color.red(),
            accent_color.green(),
            accent_color.blue(),
            255,
        )

        # Set node color to slightly lighter background
        bg_color = _hex_to_qcolor(THEME.bg_surface)
        self.model.color = (
            bg_color.red(),
            bg_color.green(),
            bg_color.blue(),
            TOKENS.sizes.panel_min_width,
        )

        self.model.border_width = TOKENS.radius.sm


# =============================================================================
# Database Nodes - Utilities
# =============================================================================


class VisualTableExistsNode(VisualNode):
    """Visual representation of TableExistsNode.

    Widgets auto-generated from TableExistsNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Table Exists"
    NODE_CATEGORY = "database/utility"

    def __init__(self) -> None:
        super().__init__()
        # Apply utility node styling
        self._apply_utility_node_style()

    def get_node_class(self) -> type:
        return TableExistsNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("connection_id", DataType.STRING)
        self.add_typed_input("table_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("exists", DataType.BOOLEAN)
        self.add_typed_output("success", DataType.BOOLEAN)

    def _apply_utility_node_style(self) -> None:
        """Apply specific styling for utility node."""
        from casare_rpa.presentation.canvas.theme_system.utils import _hex_to_qcolor

        # Use muted accent for utility operations
        accent_color = _hex_to_qcolor(THEME.text_muted)
        self.model.border_color = (
            accent_color.red(),
            accent_color.green(),
            accent_color.blue(),
            255,
        )

        # Set node color to slightly lighter background
        bg_color = _hex_to_qcolor(THEME.bg_surface)
        self.model.color = (
            bg_color.red(),
            bg_color.green(),
            bg_color.blue(),
            TOKENS.sizes.panel_min_width,
        )

        self.model.border_width = TOKENS.radius.sm


class VisualGetTableColumnsNode(VisualNode):
    """Visual representation of GetTableColumnsNode.

    Widgets auto-generated from GetTableColumnsNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Get Table Columns"
    NODE_CATEGORY = "database/utility"

    def __init__(self) -> None:
        super().__init__()
        # Apply utility node styling
        self._apply_utility_node_style()

    def get_node_class(self) -> type:
        return GetTableColumnsNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("connection_id", DataType.STRING)
        self.add_typed_input("table_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("columns", DataType.LIST[DataType.DICT])
        self.add_typed_output("success", DataType.BOOLEAN)

    def _apply_utility_node_style(self) -> None:
        """Apply specific styling for utility node."""
        from casare_rpa.presentation.canvas.theme_system.utils import _hex_to_qcolor

        # Use muted accent for utility operations
        accent_color = _hex_to_qcolor(THEME.text_muted)
        self.model.border_color = (
            accent_color.red(),
            accent_color.green(),
            accent_color.blue(),
            255,
        )

        # Set node color to slightly lighter background
        bg_color = _hex_to_qcolor(THEME.bg_surface)
        self.model.color = (
            bg_color.red(),
            bg_color.green(),
            bg_color.blue(),
            TOKENS.sizes.panel_min_width,
        )

        self.model.border_width = TOKENS.radius.sm


# =============================================================================
# Database Super Node
# =============================================================================


class VisualDatabaseSuperNode(VisualNode):
    """Visual representation of DatabaseSuperNode.

    Widgets auto-generated from DatabaseSuperNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Database Super Node"
    NODE_CATEGORY = "database/super"

    def __init__(self) -> None:
        super().__init__()
        # Apply super node styling
        self._apply_super_node_style()

    def get_node_class(self) -> type:
        return DatabaseSuperNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_output("connection_id", DataType.STRING)
        self.add_typed_output("result", DataType.DICT)
        self.add_exec_output("exec_out")

    def _apply_super_node_style(self) -> None:
        """Apply specific styling for super node."""
        from casare_rpa.presentation.canvas.theme_system.utils import _hex_to_qcolor

        # Use purple accent for super nodes
        accent_color = _hex_to_qcolor(THEME.primary)
        self.model.border_color = (
            accent_color.red(),
            accent_color.green(),
            accent_color.blue(),
            255,
        )

        # Use gradient effect for super nodes
        bg_color = _hex_to_qcolor(THEME.bg_component)
        self.model.color = (
            bg_color.red(),
            bg_color.green(),
            bg_color.blue(),
            220,
        )

        # Thicker border for super nodes
        self.model.border_width = TOKENS.sizes.button_sm

        # Make node slightly larger
        self.model.width = TOKENS.sizes.panel_default_width
        self.model.height = TOKENS.sizes.panel_min_width
