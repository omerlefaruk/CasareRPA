"""Visual nodes for database category."""

from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


class VisualDatabaseConnectNode(VisualNode):
    """Visual representation of DatabaseConnectNode."""

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Database Connect"
    NODE_CATEGORY = "database"
    CASARE_NODE_MODULE = "database_nodes"

    def __init__(self) -> None:
        """Initialize Database Connect node."""
        super().__init__()
        self.add_combo_menu(
            "db_type",
            "Database Type",
            items=["sqlite", "postgresql", "mysql"],
            tab="config",
        )
        self.add_text_input("host", "Host", text="localhost", tab="inputs")
        self.create_property("port", 5432, widget_type=2, tab="inputs")
        self.add_text_input("database", "Database", text="", tab="inputs")
        self.add_text_input("username", "Username", text="", tab="inputs")
        self.add_text_input("password", "Password", text="", tab="inputs")
        self.create_property("timeout", 30.0, widget_type=2, tab="config")
        # Advanced options
        self.create_property("ssl", False, widget_type=1, tab="advanced")
        self.add_text_input(
            "ssl_ca", "SSL CA Path", placeholder_text="Optional", tab="advanced"
        )
        self.add_text_input(
            "pool_size", "Pool Size", placeholder_text="5", tab="advanced"
        )
        self.create_property("auto_commit", True, widget_type=1, tab="advanced")
        self.add_text_input("charset", "Charset", text="utf8mb4", tab="advanced")
        # Retry options
        self.add_text_input(
            "retry_count", "Retry Count", placeholder_text="0", tab="advanced"
        )
        self.add_text_input(
            "retry_interval",
            "Retry Interval (s)",
            placeholder_text="1.0",
            tab="advanced",
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("db_type")
        self.add_input("host")
        self.add_input("database")
        self.add_input("username")
        self.add_input("password")
        self.add_output("exec_out")
        self.add_output("connection")
        self.add_output("success")
        self.add_output("error")


class VisualExecuteQueryNode(VisualNode):
    """Visual representation of ExecuteQueryNode."""

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Execute Query"
    NODE_CATEGORY = "database"
    CASARE_NODE_MODULE = "database_nodes"

    def __init__(self) -> None:
        """Initialize Execute Query node."""
        super().__init__()
        self.add_text_input("query", "SQL Query", text="", tab="inputs")
        # Retry options
        self.add_text_input(
            "retry_count", "Retry Count", placeholder_text="0", tab="advanced"
        )
        self.add_text_input(
            "retry_interval",
            "Retry Interval (s)",
            placeholder_text="1.0",
            tab="advanced",
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("connection")
        self.add_input("query")
        self.add_input("parameters")
        self.add_output("exec_out")
        self.add_output("results")
        self.add_output("row_count")
        self.add_output("columns")
        self.add_output("success")
        self.add_output("error")


class VisualExecuteNonQueryNode(VisualNode):
    """Visual representation of ExecuteNonQueryNode."""

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Execute Non-Query"
    NODE_CATEGORY = "database"
    CASARE_NODE_MODULE = "database_nodes"

    def __init__(self) -> None:
        """Initialize Execute Non-Query node."""
        super().__init__()
        self.add_text_input("query", "SQL Statement", text="", tab="inputs")
        # Retry options
        self.add_text_input(
            "retry_count", "Retry Count", placeholder_text="0", tab="advanced"
        )
        self.add_text_input(
            "retry_interval",
            "Retry Interval (s)",
            placeholder_text="1.0",
            tab="advanced",
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("connection")
        self.add_input("query")
        self.add_input("parameters")
        self.add_output("exec_out")
        self.add_output("rows_affected")
        self.add_output("last_insert_id")
        self.add_output("success")
        self.add_output("error")


class VisualBeginTransactionNode(VisualNode):
    """Visual representation of BeginTransactionNode."""

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Begin Transaction"
    NODE_CATEGORY = "database"
    CASARE_NODE_MODULE = "database_nodes"

    def __init__(self) -> None:
        """Initialize Begin Transaction node."""
        super().__init__()

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("connection")
        self.add_output("exec_out")
        self.add_output("connection")
        self.add_output("success")
        self.add_output("error")


class VisualCommitTransactionNode(VisualNode):
    """Visual representation of CommitTransactionNode."""

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Commit Transaction"
    NODE_CATEGORY = "database"
    CASARE_NODE_MODULE = "database_nodes"

    def __init__(self) -> None:
        """Initialize Commit Transaction node."""
        super().__init__()

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("connection")
        self.add_output("exec_out")
        self.add_output("connection")
        self.add_output("success")
        self.add_output("error")


class VisualRollbackTransactionNode(VisualNode):
    """Visual representation of RollbackTransactionNode."""

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Rollback Transaction"
    NODE_CATEGORY = "database"
    CASARE_NODE_MODULE = "database_nodes"

    def __init__(self) -> None:
        """Initialize Rollback Transaction node."""
        super().__init__()

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("connection")
        self.add_output("exec_out")
        self.add_output("connection")
        self.add_output("success")
        self.add_output("error")


class VisualCloseDatabaseNode(VisualNode):
    """Visual representation of CloseDatabaseNode."""

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Close Database"
    NODE_CATEGORY = "database"
    CASARE_NODE_MODULE = "database_nodes"

    def __init__(self) -> None:
        """Initialize Close Database node."""
        super().__init__()

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("connection")
        self.add_output("exec_out")
        self.add_output("success")
        self.add_output("error")


class VisualTableExistsNode(VisualNode):
    """Visual representation of TableExistsNode."""

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Table Exists"
    NODE_CATEGORY = "database"
    CASARE_NODE_MODULE = "database_nodes"

    def __init__(self) -> None:
        """Initialize Table Exists node."""
        super().__init__()
        self.add_text_input("table_name", "Table Name", text="", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("connection")
        self.add_input("table_name")
        self.add_output("exec_out")
        self.add_output("exists")
        self.add_output("success")
        self.add_output("error")


class VisualGetTableColumnsNode(VisualNode):
    """Visual representation of GetTableColumnsNode."""

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Get Table Columns"
    NODE_CATEGORY = "database"
    CASARE_NODE_MODULE = "database_nodes"

    def __init__(self) -> None:
        """Initialize Get Table Columns node."""
        super().__init__()
        self.add_text_input("table_name", "Table Name", text="", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("connection")
        self.add_input("table_name")
        self.add_output("exec_out")
        self.add_output("columns")
        self.add_output("column_names")
        self.add_output("success")
        self.add_output("error")


class VisualExecuteBatchNode(VisualNode):
    """Visual representation of ExecuteBatchNode."""

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Execute Batch"
    NODE_CATEGORY = "database"
    CASARE_NODE_MODULE = "database_nodes"

    def __init__(self) -> None:
        """Initialize Execute Batch node."""
        super().__init__()
        self.create_property("stop_on_error", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("connection")
        self.add_input("statements")
        self.add_output("exec_out")
        self.add_output("results")
        self.add_output("total_rows_affected")
        self.add_output("success")
        self.add_output("error")


# HTTP/REST API Nodes
