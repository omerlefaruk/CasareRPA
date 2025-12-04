# Node Functions

**Total:** 1562 functions

## casare_rpa.nodes

**File:** `src\casare_rpa\nodes\__init__.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__dir__` | - | `` | `List[str]` | DUNDER |
| `__getattr__` | - | `name: str` | `Any` | DUNDER |
| `_lazy_import` | - | `name: str` | `Type` | INTERNAL |
| `get_all_node_classes` | - | `` | `Dict[str, Type]` | UNUSED |
| `preload_nodes` | - | `node_names: List[str]` | `None` | UNUSED |


## casare_rpa.nodes.basic_nodes

**File:** `src\casare_rpa\nodes\basic_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | CommentNode | `self, node_id: str, name: str, ...` | `None` | DUNDER |
| `_define_ports` | CommentNode | `self` | `None` | INTERNAL |
| `_validate_config` | CommentNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | CommentNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `get_comment` | CommentNode | `self` | `str` | UNUSED |
| `set_comment` | CommentNode | `self, comment: str` | `None` | UNUSED |
| `__init__` | EndNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | EndNode | `self` | `None` | INTERNAL |
| `_validate_config` | EndNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | EndNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | StartNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | StartNode | `self` | `None` | INTERNAL |
| `_validate_config` | StartNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | StartNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.browser.browser_base

**File:** `src\casare_rpa\nodes\browser\browser_base.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async get_page_from_context` | - | `node: 'BrowserBaseNode', context: ExecutionContext, port_name: str` | `Any` | USED |
| `async highlight_element` | - | `page: Any, selector: str, timeout: int, ...` | `None` | USED |
| `async take_failure_screenshot` | - | `page: Any, screenshot_path: str, prefix: str` | `Optional[str]` | USED |
| `__init__` | BrowserBaseNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_validate_config` | BrowserBaseNode | `self` | `tuple[bool, str]` | INTERNAL |
| `add_page_input_port` | BrowserBaseNode | `self, required: bool` | `None` | USED |
| `add_page_output_port` | BrowserBaseNode | `self` | `None` | USED |
| `add_page_passthrough_ports` | BrowserBaseNode | `self, required: bool` | `None` | USED |
| `add_selector_input_port` | BrowserBaseNode | `self` | `None` | USED |
| `error_result` | BrowserBaseNode | `self, error: str | Exception, data: Optional[dict[str, Any]]` | `ExecutionResult` | USED |
| `async execute_with_retry` | BrowserBaseNode | `self, operation: Callable[[], Awaitable[T]], operation_name: str, ...` | `tuple[T, int]` | USED |
| `get_normalized_selector` | BrowserBaseNode | `self, context: ExecutionContext, param_name: str` | `str` | USED |
| `get_optional_normalized_selector` | BrowserBaseNode | `self, context: ExecutionContext, param_name: str` | `Optional[str]` | USED |
| `get_page` | BrowserBaseNode | `self, context: ExecutionContext` | `Any` | USED |
| `async get_page_async` | BrowserBaseNode | `self, context: ExecutionContext` | `Any` | UNUSED |
| `async highlight_if_enabled` | BrowserBaseNode | `self, page: Any, selector: str, ...` | `None` | USED |
| `async screenshot_on_failure` | BrowserBaseNode | `self, page: Any, prefix: str` | `Optional[str]` | USED |
| `success_result` | BrowserBaseNode | `self, data: dict[str, Any], next_nodes: Optional[list[str]]` | `ExecutionResult` | USED |
| `__init__` | PlaywrightError | `self, message: str, selector: Optional[str], ...` | `-` | DUNDER |


## casare_rpa.nodes.browser.property_constants

**File:** `src\casare_rpa\nodes\browser\property_constants.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_action_properties` | - | `` | `list[PropertyDef]` | UNUSED |
| `get_retry_properties` | - | `` | `list[PropertyDef]` | UNUSED |
| `get_screenshot_properties` | - | `` | `list[PropertyDef]` | UNUSED |
| `get_selector_properties` | - | `` | `list[PropertyDef]` | UNUSED |


## casare_rpa.nodes.browser_nodes

**File:** `src\casare_rpa\nodes\browser_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | CloseBrowserNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | CloseBrowserNode | `self` | `None` | INTERNAL |
| `_validate_config` | CloseBrowserNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async close_browser` | CloseBrowserNode | `` | `-` | UNUSED |
| `async execute` | CloseBrowserNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | DownloadFileNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | DownloadFileNode | `self` | `None` | INTERNAL |
| `download_file` | DownloadFileNode | `` | `-` | USED |
| `async execute` | DownloadFileNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | GetAllImagesNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | GetAllImagesNode | `self` | `None` | INTERNAL |
| `async execute` | GetAllImagesNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | LaunchBrowserNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | LaunchBrowserNode | `self` | `None` | INTERNAL |
| `_validate_config` | LaunchBrowserNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | LaunchBrowserNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | NewTabNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | NewTabNode | `self` | `None` | INTERNAL |
| `_validate_config` | NewTabNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | NewTabNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.control_flow_nodes

**File:** `src\casare_rpa\nodes\control_flow_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | BreakNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | BreakNode | `self` | `None` | INTERNAL |
| `async execute` | BreakNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | CatchNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | CatchNode | `self` | `None` | INTERNAL |
| `async execute` | CatchNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `set_paired_try` | CatchNode | `self, try_node_id: str` | `None` | USED |
| `__init__` | ContinueNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | ContinueNode | `self` | `None` | INTERNAL |
| `async execute` | ContinueNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | FinallyNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | FinallyNode | `self` | `None` | INTERNAL |
| `async execute` | FinallyNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `set_paired_try` | FinallyNode | `self, try_node_id: str` | `None` | USED |
| `__init__` | ForLoopEndNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | ForLoopEndNode | `self` | `None` | INTERNAL |
| `async execute` | ForLoopEndNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `set_paired_start` | ForLoopEndNode | `self, start_node_id: str` | `None` | USED |
| `__init__` | ForLoopStartNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | ForLoopStartNode | `self` | `None` | INTERNAL |
| `async execute` | ForLoopStartNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | IfNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | IfNode | `self` | `None` | INTERNAL |
| `async execute` | IfNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | MergeNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | MergeNode | `self` | `None` | INTERNAL |
| `async execute` | MergeNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | SwitchNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | SwitchNode | `self` | `None` | INTERNAL |
| `async execute` | SwitchNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | TryNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | TryNode | `self` | `None` | INTERNAL |
| `async execute` | TryNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | WhileLoopEndNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | WhileLoopEndNode | `self` | `None` | INTERNAL |
| `async execute` | WhileLoopEndNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `set_paired_start` | WhileLoopEndNode | `self, start_node_id: str` | `None` | USED |
| `__init__` | WhileLoopStartNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | WhileLoopStartNode | `self` | `None` | INTERNAL |
| `async execute` | WhileLoopStartNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.data_nodes

**File:** `src\casare_rpa\nodes\data_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ExtractTextNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ExtractTextNode | `self` | `None` | INTERNAL |
| `async execute` | ExtractTextNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `async perform_extraction` | ExtractTextNode | `` | `str` | UNUSED |
| `__init__` | GetAttributeNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | GetAttributeNode | `self` | `None` | INTERNAL |
| `async execute` | GetAttributeNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `async perform_get_attribute` | GetAttributeNode | `` | `str` | UNUSED |
| `__init__` | ScreenshotNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_build_screenshot_options` | ScreenshotNode | `self, timeout: int` | `dict` | INTERNAL |
| `_define_ports` | ScreenshotNode | `self` | `None` | INTERNAL |
| `_normalize_file_path` | ScreenshotNode | `self, file_path: str` | `str` | INTERNAL |
| `_validate_config` | ScreenshotNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | ScreenshotNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `async perform_screenshot` | ScreenshotNode | `` | `str` | UNUSED |


## casare_rpa.nodes.database.database_utils

**File:** `src\casare_rpa\nodes\database\database_utils.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `validate_sql_identifier` | - | `identifier: str, identifier_type: str` | `str` | USED |
| `__init__` | GetTableColumnsNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | GetTableColumnsNode | `self` | `None` | INTERNAL |
| `async _get_mysql_columns` | GetTableColumnsNode | `self, connection: DatabaseConnection, table_name: str` | `List[Dict[str, Any]]` | INTERNAL |
| `async _get_postgresql_columns` | GetTableColumnsNode | `self, connection: DatabaseConnection, table_name: str` | `List[Dict[str, Any]]` | INTERNAL |
| `async _get_sqlite_columns` | GetTableColumnsNode | `self, connection: DatabaseConnection, table_name: str` | `List[Dict[str, Any]]` | INTERNAL |
| `async execute` | GetTableColumnsNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | TableExistsNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `async _check_mysql` | TableExistsNode | `self, connection: DatabaseConnection, table_name: str` | `bool` | INTERNAL |
| `async _check_postgresql` | TableExistsNode | `self, connection: DatabaseConnection, table_name: str` | `bool` | INTERNAL |
| `async _check_sqlite` | TableExistsNode | `self, connection: DatabaseConnection, table_name: str` | `bool` | INTERNAL |
| `_define_ports` | TableExistsNode | `self` | `None` | INTERNAL |
| `async execute` | TableExistsNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.database.sql_nodes

**File:** `src\casare_rpa\nodes\database\sql_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | BeginTransactionNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | BeginTransactionNode | `self` | `None` | INTERNAL |
| `async execute` | BeginTransactionNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | CloseDatabaseNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | CloseDatabaseNode | `self` | `None` | INTERNAL |
| `async execute` | CloseDatabaseNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | CommitTransactionNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | CommitTransactionNode | `self` | `None` | INTERNAL |
| `async execute` | CommitTransactionNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | DatabaseConnectNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `async _connect_mysql` | DatabaseConnectNode | `self, host: str, port: int, ...` | `DatabaseConnection` | INTERNAL |
| `async _connect_postgresql` | DatabaseConnectNode | `self, host: str, port: int, ...` | `DatabaseConnection` | INTERNAL |
| `async _connect_sqlite` | DatabaseConnectNode | `self, database: str` | `DatabaseConnection` | INTERNAL |
| `_define_ports` | DatabaseConnectNode | `self` | `None` | INTERNAL |
| `async execute` | DatabaseConnectNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | DatabaseConnection | `self, db_type: str, connection: Any, ...` | `None` | DUNDER |
| `async acquire` | DatabaseConnection | `self` | `Any` | USED |
| `async close` | DatabaseConnection | `self` | `None` | USED |
| `async release` | DatabaseConnection | `self` | `None` | USED |
| `__init__` | ExecuteBatchNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ExecuteBatchNode | `self` | `None` | INTERNAL |
| `async execute` | ExecuteBatchNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ExecuteNonQueryNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ExecuteNonQueryNode | `self` | `None` | INTERNAL |
| `async _execute_mysql` | ExecuteNonQueryNode | `self, connection: DatabaseConnection, query: str, ...` | `Tuple[int, Optional[int]]` | INTERNAL |
| `async _execute_postgresql` | ExecuteNonQueryNode | `self, connection: DatabaseConnection, query: str, ...` | `Tuple[int, Optional[int]]` | INTERNAL |
| `async _execute_sqlite` | ExecuteNonQueryNode | `self, connection: DatabaseConnection, query: str, ...` | `Tuple[int, Optional[int]]` | INTERNAL |
| `async execute` | ExecuteNonQueryNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ExecuteQueryNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ExecuteQueryNode | `self` | `None` | INTERNAL |
| `async _execute_mysql` | ExecuteQueryNode | `self, connection: DatabaseConnection, query: str, ...` | `Tuple[List[Dict[str, Any]], List[str]]` | INTERNAL |
| `async _execute_postgresql` | ExecuteQueryNode | `self, connection: DatabaseConnection, query: str, ...` | `Tuple[List[Dict[str, Any]], List[str]]` | INTERNAL |
| `async _execute_sqlite` | ExecuteQueryNode | `self, connection: DatabaseConnection, query: str, ...` | `Tuple[List[Dict[str, Any]], List[str]]` | INTERNAL |
| `async execute` | ExecuteQueryNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | RollbackTransactionNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | RollbackTransactionNode | `self` | `None` | INTERNAL |
| `async execute` | RollbackTransactionNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.datetime_nodes

**File:** `src\casare_rpa\nodes\datetime_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | DateTimeAddNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | DateTimeAddNode | `self` | `None` | INTERNAL |
| `_validate_config` | DateTimeAddNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | DateTimeAddNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | DateTimeCompareNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | DateTimeCompareNode | `self` | `None` | INTERNAL |
| `_validate_config` | DateTimeCompareNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | DateTimeCompareNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `parse_dt` | DateTimeCompareNode | `val` | `-` | USED |
| `__init__` | DateTimeDiffNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | DateTimeDiffNode | `self` | `None` | INTERNAL |
| `_validate_config` | DateTimeDiffNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | DateTimeDiffNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `parse_dt` | DateTimeDiffNode | `val` | `-` | USED |
| `__init__` | FormatDateTimeNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | FormatDateTimeNode | `self` | `None` | INTERNAL |
| `_validate_config` | FormatDateTimeNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | FormatDateTimeNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | GetCurrentDateTimeNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | GetCurrentDateTimeNode | `self` | `None` | INTERNAL |
| `_validate_config` | GetCurrentDateTimeNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | GetCurrentDateTimeNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | GetTimestampNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | GetTimestampNode | `self` | `None` | INTERNAL |
| `_validate_config` | GetTimestampNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | GetTimestampNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ParseDateTimeNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ParseDateTimeNode | `self` | `None` | INTERNAL |
| `_validate_config` | ParseDateTimeNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | ParseDateTimeNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.desktop_nodes.application_nodes

**File:** `src\casare_rpa\nodes\desktop_nodes\application_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ActivateWindowNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | ActivateWindowNode | `self` | `None` | INTERNAL |
| `async execute` | ActivateWindowNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | CloseApplicationNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | CloseApplicationNode | `self` | `None` | INTERNAL |
| `async execute` | CloseApplicationNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | GetWindowListNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | GetWindowListNode | `self` | `None` | INTERNAL |
| `async execute` | GetWindowListNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | LaunchApplicationNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | LaunchApplicationNode | `self` | `None` | INTERNAL |
| `async execute` | LaunchApplicationNode | `self, context: Any` | `Dict[str, Any]` | USED |


## casare_rpa.nodes.desktop_nodes.desktop_base

**File:** `src\casare_rpa\nodes\desktop_nodes\desktop_base.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | DesktopNodeBase | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_get_default_config` | DesktopNodeBase | `self` | `Dict[str, Any]` | INTERNAL |
| `error_result` | DesktopNodeBase | `self, error: str` | `Dict[str, Any]` | USED |
| `async execute_with_retry` | DesktopNodeBase | `self, operation: Any, context: Any, ...` | `Dict[str, Any]` | USED |
| `get_desktop_context` | DesktopNodeBase | `self, context: Any` | `DesktopContext` | USED |
| `handle_error` | DesktopNodeBase | `self, error: Exception, operation: str` | `None` | USED |
| `require_desktop_context` | DesktopNodeBase | `self, context: Any` | `DesktopContext` | USED |
| `resolve_variable` | DesktopNodeBase | `self, context: Any, value: Any` | `Any` | USED |
| `success_result` | DesktopNodeBase | `self` | `Dict[str, Any]` | USED |
| `async find_element_from_inputs` | ElementInteractionMixin | `self, context: Any, desktop_ctx: DesktopContext, ...` | `Any` | USED |
| `get_window_from_input` | WindowOperationMixin | `self, raise_on_missing: bool` | `Any` | USED |


## casare_rpa.nodes.desktop_nodes.element_nodes

**File:** `src\casare_rpa\nodes\desktop_nodes\element_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ClickElementNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | ClickElementNode | `self` | `None` | INTERNAL |
| `async execute` | ClickElementNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | FindElementNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | FindElementNode | `self` | `None` | INTERNAL |
| `async execute` | FindElementNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | GetElementPropertyNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | GetElementPropertyNode | `self` | `None` | INTERNAL |
| `async execute` | GetElementPropertyNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | GetElementTextNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | GetElementTextNode | `self` | `None` | INTERNAL |
| `async execute` | GetElementTextNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | TypeTextNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | TypeTextNode | `self` | `None` | INTERNAL |
| `async execute` | TypeTextNode | `self, context: Any` | `Dict[str, Any]` | USED |


## casare_rpa.nodes.desktop_nodes.interaction_nodes

**File:** `src\casare_rpa\nodes\desktop_nodes\interaction_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | CheckCheckboxNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | CheckCheckboxNode | `self` | `None` | INTERNAL |
| `_element_type` | CheckCheckboxNode | `self` | `str` | INTERNAL |
| `async execute` | CheckCheckboxNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | ExpandTreeItemNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | ExpandTreeItemNode | `self` | `None` | INTERNAL |
| `_element_type` | ExpandTreeItemNode | `self` | `str` | INTERNAL |
| `async execute` | ExpandTreeItemNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `_element_type` | InteractionNodeBase | `self` | `str` | INTERNAL |
| `get_element_from_input` | InteractionNodeBase | `self` | `Any` | USED |
| `__init__` | ScrollElementNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | ScrollElementNode | `self` | `None` | INTERNAL |
| `async execute` | ScrollElementNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | SelectFromDropdownNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | SelectFromDropdownNode | `self` | `None` | INTERNAL |
| `_element_type` | SelectFromDropdownNode | `self` | `str` | INTERNAL |
| `async execute` | SelectFromDropdownNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | SelectRadioButtonNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | SelectRadioButtonNode | `self` | `None` | INTERNAL |
| `_element_type` | SelectRadioButtonNode | `self` | `str` | INTERNAL |
| `async execute` | SelectRadioButtonNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | SelectTabNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | SelectTabNode | `self` | `None` | INTERNAL |
| `_element_type` | SelectTabNode | `self` | `str` | INTERNAL |
| `async execute` | SelectTabNode | `self, context: Any` | `Dict[str, Any]` | USED |


## casare_rpa.nodes.desktop_nodes.mouse_keyboard_nodes

**File:** `src\casare_rpa\nodes\desktop_nodes\mouse_keyboard_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | DragMouseNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | DragMouseNode | `self` | `None` | INTERNAL |
| `_get_default_config` | DragMouseNode | `self` | `Dict[str, Any]` | INTERNAL |
| `async execute` | DragMouseNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | GetMousePositionNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | GetMousePositionNode | `self` | `None` | INTERNAL |
| `async execute` | GetMousePositionNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | MouseClickNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | MouseClickNode | `self` | `None` | INTERNAL |
| `async execute` | MouseClickNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | MoveMouseNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | MoveMouseNode | `self` | `None` | INTERNAL |
| `async execute` | MoveMouseNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | SendHotKeyNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | SendHotKeyNode | `self` | `None` | INTERNAL |
| `async execute` | SendHotKeyNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | SendKeysNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | SendKeysNode | `self` | `None` | INTERNAL |
| `async execute` | SendKeysNode | `self, context: Any` | `Dict[str, Any]` | USED |


## casare_rpa.nodes.desktop_nodes.office_nodes

**File:** `src\casare_rpa\nodes\desktop_nodes\office_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ExcelCloseNode | `self, node_id: str, config: Dict[str, Any], ...` | `-` | DUNDER |
| `_define_ports` | ExcelCloseNode | `self` | `-` | INTERNAL |
| `async execute` | ExcelCloseNode | `self, context` | `Dict[str, Any]` | USED |
| `__init__` | ExcelGetRangeNode | `self, node_id: str, config: Dict[str, Any], ...` | `-` | DUNDER |
| `_define_ports` | ExcelGetRangeNode | `self` | `-` | INTERNAL |
| `async execute` | ExcelGetRangeNode | `self, context` | `Dict[str, Any]` | USED |
| `__init__` | ExcelOpenNode | `self, node_id: str, config: Dict[str, Any], ...` | `-` | DUNDER |
| `_define_ports` | ExcelOpenNode | `self` | `-` | INTERNAL |
| `async execute` | ExcelOpenNode | `self, context` | `Dict[str, Any]` | USED |
| `__init__` | ExcelReadCellNode | `self, node_id: str, config: Dict[str, Any], ...` | `-` | DUNDER |
| `_define_ports` | ExcelReadCellNode | `self` | `-` | INTERNAL |
| `async execute` | ExcelReadCellNode | `self, context` | `Dict[str, Any]` | USED |
| `__init__` | ExcelWriteCellNode | `self, node_id: str, config: Dict[str, Any], ...` | `-` | DUNDER |
| `_define_ports` | ExcelWriteCellNode | `self` | `-` | INTERNAL |
| `async execute` | ExcelWriteCellNode | `self, context` | `Dict[str, Any]` | USED |
| `__init__` | OutlookGetInboxCountNode | `self, node_id: str, config: Dict[str, Any], ...` | `-` | DUNDER |
| `_define_ports` | OutlookGetInboxCountNode | `self` | `-` | INTERNAL |
| `async execute` | OutlookGetInboxCountNode | `self, context` | `Dict[str, Any]` | USED |
| `__init__` | OutlookReadEmailsNode | `self, node_id: str, config: Dict[str, Any], ...` | `-` | DUNDER |
| `_define_ports` | OutlookReadEmailsNode | `self` | `-` | INTERNAL |
| `async execute` | OutlookReadEmailsNode | `self, context` | `Dict[str, Any]` | USED |
| `__init__` | OutlookSendEmailNode | `self, node_id: str, config: Dict[str, Any], ...` | `-` | DUNDER |
| `_define_ports` | OutlookSendEmailNode | `self` | `-` | INTERNAL |
| `async execute` | OutlookSendEmailNode | `self, context` | `Dict[str, Any]` | USED |
| `__init__` | WordCloseNode | `self, node_id: str, config: Dict[str, Any], ...` | `-` | DUNDER |
| `_define_ports` | WordCloseNode | `self` | `-` | INTERNAL |
| `async execute` | WordCloseNode | `self, context` | `Dict[str, Any]` | USED |
| `__init__` | WordGetTextNode | `self, node_id: str, config: Dict[str, Any], ...` | `-` | DUNDER |
| `_define_ports` | WordGetTextNode | `self` | `-` | INTERNAL |
| `async execute` | WordGetTextNode | `self, context` | `Dict[str, Any]` | USED |
| `__init__` | WordOpenNode | `self, node_id: str, config: Dict[str, Any], ...` | `-` | DUNDER |
| `_define_ports` | WordOpenNode | `self` | `-` | INTERNAL |
| `async execute` | WordOpenNode | `self, context` | `Dict[str, Any]` | USED |
| `__init__` | WordReplaceTextNode | `self, node_id: str, config: Dict[str, Any], ...` | `-` | DUNDER |
| `_define_ports` | WordReplaceTextNode | `self` | `-` | INTERNAL |
| `async execute` | WordReplaceTextNode | `self, context` | `Dict[str, Any]` | USED |


## casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes

**File:** `src\casare_rpa\nodes\desktop_nodes\screenshot_ocr_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | CaptureElementImageNode | `self, node_id: str, config: Dict[str, Any], ...` | `-` | DUNDER |
| `_define_ports` | CaptureElementImageNode | `self` | `-` | INTERNAL |
| `async execute` | CaptureElementImageNode | `self, context` | `Dict[str, Any]` | USED |
| `__init__` | CaptureScreenshotNode | `self, node_id: str, config: Dict[str, Any], ...` | `-` | DUNDER |
| `_define_ports` | CaptureScreenshotNode | `self` | `-` | INTERNAL |
| `async execute` | CaptureScreenshotNode | `self, context` | `Dict[str, Any]` | USED |
| `__init__` | CompareImagesNode | `self, node_id: str, config: Dict[str, Any], ...` | `-` | DUNDER |
| `_define_ports` | CompareImagesNode | `self` | `-` | INTERNAL |
| `async execute` | CompareImagesNode | `self, context` | `Dict[str, Any]` | USED |
| `__init__` | OCRExtractTextNode | `self, node_id: str, config: Dict[str, Any], ...` | `-` | DUNDER |
| `_define_ports` | OCRExtractTextNode | `self` | `-` | INTERNAL |
| `async execute` | OCRExtractTextNode | `self, context` | `Dict[str, Any]` | USED |


## casare_rpa.nodes.desktop_nodes.wait_verification_nodes

**File:** `src\casare_rpa\nodes\desktop_nodes\wait_verification_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | VerifyElementExistsNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | VerifyElementExistsNode | `self` | `None` | INTERNAL |
| `_get_default_config` | VerifyElementExistsNode | `self` | `Dict[str, Any]` | INTERNAL |
| `async execute` | VerifyElementExistsNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | VerifyElementPropertyNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | VerifyElementPropertyNode | `self` | `None` | INTERNAL |
| `async execute` | VerifyElementPropertyNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | WaitForElementNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | WaitForElementNode | `self` | `None` | INTERNAL |
| `async execute` | WaitForElementNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | WaitForWindowNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | WaitForWindowNode | `self` | `None` | INTERNAL |
| `async execute` | WaitForWindowNode | `self, context: Any` | `Dict[str, Any]` | USED |


## casare_rpa.nodes.desktop_nodes.window_nodes

**File:** `src\casare_rpa\nodes\desktop_nodes\window_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | GetWindowPropertiesNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | GetWindowPropertiesNode | `self` | `None` | INTERNAL |
| `async execute` | GetWindowPropertiesNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | MaximizeWindowNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | MaximizeWindowNode | `self` | `None` | INTERNAL |
| `async do_maximize` | MaximizeWindowNode | `` | `-` | UNUSED |
| `async execute` | MaximizeWindowNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | MinimizeWindowNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | MinimizeWindowNode | `self` | `None` | INTERNAL |
| `async do_minimize` | MinimizeWindowNode | `` | `-` | UNUSED |
| `async execute` | MinimizeWindowNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | MoveWindowNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | MoveWindowNode | `self` | `None` | INTERNAL |
| `async do_move` | MoveWindowNode | `` | `-` | UNUSED |
| `async execute` | MoveWindowNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | ResizeWindowNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | ResizeWindowNode | `self` | `None` | INTERNAL |
| `async do_resize` | ResizeWindowNode | `` | `-` | UNUSED |
| `async execute` | ResizeWindowNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | RestoreWindowNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | RestoreWindowNode | `self` | `None` | INTERNAL |
| `async do_restore` | RestoreWindowNode | `` | `-` | UNUSED |
| `async execute` | RestoreWindowNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `__init__` | SetWindowStateNode | `self, node_id: Optional[str], config: Optional[Dict[str, Any]], ...` | `-` | DUNDER |
| `_define_ports` | SetWindowStateNode | `self` | `None` | INTERNAL |
| `async do_set_state` | SetWindowStateNode | `` | `-` | UNUSED |
| `async execute` | SetWindowStateNode | `self, context: Any` | `Dict[str, Any]` | USED |
| `get_window_from_input` | WindowNodeBase | `self` | `Any` | USED |


## casare_rpa.nodes.dict_nodes

**File:** `src\casare_rpa\nodes\dict_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | CreateDictNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | CreateDictNode | `self` | `None` | INTERNAL |
| `async execute` | CreateDictNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | DictGetNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | DictGetNode | `self` | `None` | INTERNAL |
| `async execute` | DictGetNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | DictHasKeyNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | DictHasKeyNode | `self` | `None` | INTERNAL |
| `async execute` | DictHasKeyNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | DictItemsNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | DictItemsNode | `self` | `None` | INTERNAL |
| `async execute` | DictItemsNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | DictKeysNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | DictKeysNode | `self` | `None` | INTERNAL |
| `async execute` | DictKeysNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | DictMergeNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | DictMergeNode | `self` | `None` | INTERNAL |
| `async execute` | DictMergeNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | DictRemoveNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | DictRemoveNode | `self` | `None` | INTERNAL |
| `async execute` | DictRemoveNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | DictSetNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | DictSetNode | `self` | `None` | INTERNAL |
| `async execute` | DictSetNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | DictToJsonNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | DictToJsonNode | `self` | `None` | INTERNAL |
| `async execute` | DictToJsonNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | DictValuesNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | DictValuesNode | `self` | `None` | INTERNAL |
| `async execute` | DictValuesNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | GetPropertyNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | GetPropertyNode | `self` | `None` | INTERNAL |
| `async execute` | GetPropertyNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | JsonParseNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | JsonParseNode | `self` | `None` | INTERNAL |
| `async execute` | JsonParseNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.document.document_nodes

**File:** `src\casare_rpa\nodes\document\document_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ClassifyDocumentNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | ClassifyDocumentNode | `self` | `None` | INTERNAL |
| `async _execute_document` | ClassifyDocumentNode | `self, context: Any, manager: DocumentAIManager` | `ExecutionResult` | INTERNAL |
| `__init__` | DocumentBaseNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `async _execute_document` | DocumentBaseNode | `self, context: Any, manager: DocumentAIManager` | `ExecutionResult` | INTERNAL |
| `_get_api_key` | DocumentBaseNode | `self, context: Any` | `Optional[str]` | INTERNAL |
| `_get_document_manager` | DocumentBaseNode | `self, context: Any` | `DocumentAIManager` | INTERNAL |
| `_get_provider` | DocumentBaseNode | `self, context: Any` | `LLMProvider` | INTERNAL |
| `async execute` | DocumentBaseNode | `self, context: Any` | `ExecutionResult` | USED |
| `__init__` | ExtractFormNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | ExtractFormNode | `self` | `None` | INTERNAL |
| `async _execute_document` | ExtractFormNode | `self, context: Any, manager: DocumentAIManager` | `ExecutionResult` | INTERNAL |
| `__init__` | ExtractInvoiceNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | ExtractInvoiceNode | `self` | `None` | INTERNAL |
| `async _execute_document` | ExtractInvoiceNode | `self, context: Any, manager: DocumentAIManager` | `ExecutionResult` | INTERNAL |
| `__init__` | ExtractTableNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | ExtractTableNode | `self` | `None` | INTERNAL |
| `async _execute_document` | ExtractTableNode | `self, context: Any, manager: DocumentAIManager` | `ExecutionResult` | INTERNAL |
| `__init__` | ValidateExtractionNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | ValidateExtractionNode | `self` | `None` | INTERNAL |
| `async execute` | ValidateExtractionNode | `self, context: Any` | `ExecutionResult` | USED |


## casare_rpa.nodes.email.email_base

**File:** `src\casare_rpa\nodes\email\email_base.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `decode_header_value` | - | `value: str` | `str` | USED |
| `parse_email_message` | - | `msg: EmailMessage` | `Dict[str, Any]` | USED |


## casare_rpa.nodes.email.imap_nodes

**File:** `src\casare_rpa\nodes\email\imap_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | DeleteEmailNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | DeleteEmailNode | `self` | `None` | INTERNAL |
| `_delete_email_sync` | DeleteEmailNode | `` | `None` | INTERNAL |
| `async execute` | DeleteEmailNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | MarkEmailNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | MarkEmailNode | `self` | `None` | INTERNAL |
| `_mark_email_sync` | MarkEmailNode | `` | `None` | INTERNAL |
| `async execute` | MarkEmailNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | MoveEmailNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | MoveEmailNode | `self` | `None` | INTERNAL |
| `_move_email_sync` | MoveEmailNode | `` | `None` | INTERNAL |
| `async execute` | MoveEmailNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | SaveAttachmentNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | SaveAttachmentNode | `self` | `None` | INTERNAL |
| `_save_attachments_sync` | SaveAttachmentNode | `` | `list` | INTERNAL |
| `async execute` | SaveAttachmentNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.email.receive_nodes

**File:** `src\casare_rpa\nodes\email\receive_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | FilterEmailsNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | FilterEmailsNode | `self` | `None` | INTERNAL |
| `async execute` | FilterEmailsNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | GetEmailContentNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | GetEmailContentNode | `self` | `None` | INTERNAL |
| `async execute` | GetEmailContentNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ReadEmailsNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | ReadEmailsNode | `self` | `None` | INTERNAL |
| `_read_emails_sync` | ReadEmailsNode | `` | `list` | INTERNAL |
| `async execute` | ReadEmailsNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.email.send_nodes

**File:** `src\casare_rpa\nodes\email\send_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | SendEmailNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | SendEmailNode | `self` | `None` | INTERNAL |
| `_send_email_sync` | SendEmailNode | `` | `str` | INTERNAL |
| `async execute` | SendEmailNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.error_handling_nodes

**File:** `src\casare_rpa\nodes\error_handling_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | AssertNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | AssertNode | `self` | `None` | INTERNAL |
| `async execute` | AssertNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ErrorRecoveryNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | ErrorRecoveryNode | `self` | `None` | INTERNAL |
| `async execute` | ErrorRecoveryNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | LogErrorNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | LogErrorNode | `self` | `None` | INTERNAL |
| `async execute` | LogErrorNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | OnErrorNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | OnErrorNode | `self` | `None` | INTERNAL |
| `async execute` | OnErrorNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | RetryFailNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | RetryFailNode | `self` | `None` | INTERNAL |
| `async execute` | RetryFailNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | RetryNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | RetryNode | `self` | `None` | INTERNAL |
| `async execute` | RetryNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | RetrySuccessNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | RetrySuccessNode | `self` | `None` | INTERNAL |
| `async execute` | RetrySuccessNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ThrowErrorNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | ThrowErrorNode | `self` | `None` | INTERNAL |
| `async execute` | ThrowErrorNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | TryNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | TryNode | `self` | `None` | INTERNAL |
| `async execute` | TryNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | WebhookNotifyNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_build_payload` | WebhookNotifyNode | `self, format_type: str, message: str, ...` | `Dict[str, Any]` | INTERNAL |
| `_define_ports` | WebhookNotifyNode | `self` | `None` | INTERNAL |
| `async execute` | WebhookNotifyNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.file.directory_nodes

**File:** `src\casare_rpa\nodes\file\directory_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | CreateDirectoryNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | CreateDirectoryNode | `self` | `None` | INTERNAL |
| `_validate_config` | CreateDirectoryNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | CreateDirectoryNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ListDirectoryNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ListDirectoryNode | `self` | `None` | INTERNAL |
| `_validate_config` | ListDirectoryNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | ListDirectoryNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ListFilesNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ListFilesNode | `self` | `None` | INTERNAL |
| `_validate_config` | ListFilesNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | ListFilesNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.file.file_read_nodes

**File:** `src\casare_rpa\nodes\file\file_read_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ReadFileNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ReadFileNode | `self` | `None` | INTERNAL |
| `_validate_config` | ReadFileNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | ReadFileNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.file.file_security

**File:** `src\casare_rpa\nodes\file\file_security.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `validate_path_security` | - | `path: str | Path, operation: str, allow_dangerous: bool` | `Path` | USED |
| `validate_path_security_readonly` | - | `path: str | Path, operation: str, allow_dangerous: bool` | `Path` | USED |


## casare_rpa.nodes.file.file_system_nodes

**File:** `src\casare_rpa\nodes\file\file_system_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | CopyFileNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | CopyFileNode | `self` | `None` | INTERNAL |
| `_validate_config` | CopyFileNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | CopyFileNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | DeleteFileNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | DeleteFileNode | `self` | `None` | INTERNAL |
| `_validate_config` | DeleteFileNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | DeleteFileNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | MoveFileNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | MoveFileNode | `self` | `None` | INTERNAL |
| `_validate_config` | MoveFileNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | MoveFileNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.file.file_write_nodes

**File:** `src\casare_rpa\nodes\file\file_write_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | AppendFileNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | AppendFileNode | `self` | `None` | INTERNAL |
| `_validate_config` | AppendFileNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | AppendFileNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | WriteFileNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | WriteFileNode | `self` | `None` | INTERNAL |
| `_validate_config` | WriteFileNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | WriteFileNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.file.path_nodes

**File:** `src\casare_rpa\nodes\file\path_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | FileExistsNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | FileExistsNode | `self` | `None` | INTERNAL |
| `_validate_config` | FileExistsNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | FileExistsNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | GetFileInfoNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | GetFileInfoNode | `self` | `None` | INTERNAL |
| `_validate_config` | GetFileInfoNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | GetFileInfoNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | GetFileSizeNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | GetFileSizeNode | `self` | `None` | INTERNAL |
| `_validate_config` | GetFileSizeNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | GetFileSizeNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.file.structured_data

**File:** `src\casare_rpa\nodes\file\structured_data.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `validate_zip_entry` | - | `zip_path: str, entry_name: str` | `Path` | USED |
| `__init__` | ReadCSVNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ReadCSVNode | `self` | `None` | INTERNAL |
| `_validate_config` | ReadCSVNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | ReadCSVNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ReadJSONFileNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ReadJSONFileNode | `self` | `None` | INTERNAL |
| `_validate_config` | ReadJSONFileNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | ReadJSONFileNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | UnzipFilesNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | UnzipFilesNode | `self` | `None` | INTERNAL |
| `_validate_config` | UnzipFilesNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | UnzipFilesNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | WriteCSVNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | WriteCSVNode | `self` | `None` | INTERNAL |
| `_validate_config` | WriteCSVNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | WriteCSVNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | WriteJSONFileNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | WriteJSONFileNode | `self` | `None` | INTERNAL |
| `_validate_config` | WriteJSONFileNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | WriteJSONFileNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ZipFilesNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ZipFilesNode | `self` | `None` | INTERNAL |
| `_validate_config` | ZipFilesNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | ZipFilesNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.ftp_nodes

**File:** `src\casare_rpa\nodes\ftp_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | FTPConnectNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | FTPConnectNode | `self` | `None` | INTERNAL |
| `_validate_config` | FTPConnectNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | FTPConnectNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | FTPDeleteNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | FTPDeleteNode | `self` | `None` | INTERNAL |
| `_validate_config` | FTPDeleteNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | FTPDeleteNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | FTPDisconnectNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | FTPDisconnectNode | `self` | `None` | INTERNAL |
| `_validate_config` | FTPDisconnectNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | FTPDisconnectNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | FTPDownloadNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | FTPDownloadNode | `self` | `None` | INTERNAL |
| `_validate_config` | FTPDownloadNode | `self` | `tuple[bool, str]` | INTERNAL |
| `callback` | FTPDownloadNode | `data` | `-` | USED |
| `async execute` | FTPDownloadNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | FTPGetSizeNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | FTPGetSizeNode | `self` | `None` | INTERNAL |
| `_validate_config` | FTPGetSizeNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | FTPGetSizeNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | FTPListNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | FTPListNode | `self` | `None` | INTERNAL |
| `_validate_config` | FTPListNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | FTPListNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | FTPMakeDirNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | FTPMakeDirNode | `self` | `None` | INTERNAL |
| `_validate_config` | FTPMakeDirNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | FTPMakeDirNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | FTPRemoveDirNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | FTPRemoveDirNode | `self` | `None` | INTERNAL |
| `_validate_config` | FTPRemoveDirNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | FTPRemoveDirNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | FTPRenameNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | FTPRenameNode | `self` | `None` | INTERNAL |
| `_validate_config` | FTPRenameNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | FTPRenameNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | FTPUploadNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | FTPUploadNode | `self` | `None` | INTERNAL |
| `_validate_config` | FTPUploadNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | FTPUploadNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.google.calendar.calendar_events

**File:** `src\casare_rpa\nodes\google\calendar\calendar_events.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_parse_attendees` | - | `attendees_str: str` | `List[dict]` | INTERNAL |
| `_parse_datetime` | - | `value: Any` | `Optional[datetime]` | INTERNAL |
| `__init__` | CalendarCreateEventNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | CalendarCreateEventNode | `self` | `None` | INTERNAL |
| `async _execute_calendar` | CalendarCreateEventNode | `self, context: ExecutionContext, client: GoogleCalendarClient` | `ExecutionResult` | INTERNAL |
| `__init__` | CalendarDeleteEventNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | CalendarDeleteEventNode | `self` | `None` | INTERNAL |
| `async _execute_calendar` | CalendarDeleteEventNode | `self, context: ExecutionContext, client: GoogleCalendarClient` | `ExecutionResult` | INTERNAL |
| `__init__` | CalendarGetEventNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | CalendarGetEventNode | `self` | `None` | INTERNAL |
| `async _execute_calendar` | CalendarGetEventNode | `self, context: ExecutionContext, client: GoogleCalendarClient` | `ExecutionResult` | INTERNAL |
| `__init__` | CalendarGetFreeBusyNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | CalendarGetFreeBusyNode | `self` | `None` | INTERNAL |
| `async _execute_calendar` | CalendarGetFreeBusyNode | `self, context: ExecutionContext, client: GoogleCalendarClient` | `ExecutionResult` | INTERNAL |
| `__init__` | CalendarListEventsNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | CalendarListEventsNode | `self` | `None` | INTERNAL |
| `async _execute_calendar` | CalendarListEventsNode | `self, context: ExecutionContext, client: GoogleCalendarClient` | `ExecutionResult` | INTERNAL |
| `__init__` | CalendarMoveEventNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | CalendarMoveEventNode | `self` | `None` | INTERNAL |
| `async _execute_calendar` | CalendarMoveEventNode | `self, context: ExecutionContext, client: GoogleCalendarClient` | `ExecutionResult` | INTERNAL |
| `__init__` | CalendarQuickAddNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | CalendarQuickAddNode | `self` | `None` | INTERNAL |
| `async _execute_calendar` | CalendarQuickAddNode | `self, context: ExecutionContext, client: GoogleCalendarClient` | `ExecutionResult` | INTERNAL |
| `__init__` | CalendarUpdateEventNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | CalendarUpdateEventNode | `self` | `None` | INTERNAL |
| `async _execute_calendar` | CalendarUpdateEventNode | `self, context: ExecutionContext, client: GoogleCalendarClient` | `ExecutionResult` | INTERNAL |


## casare_rpa.nodes.google.calendar.calendar_manage

**File:** `src\casare_rpa\nodes\google\calendar\calendar_manage.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | CalendarCreateCalendarNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | CalendarCreateCalendarNode | `self` | `None` | INTERNAL |
| `async _execute_calendar` | CalendarCreateCalendarNode | `self, context: ExecutionContext, client: GoogleCalendarClient` | `ExecutionResult` | INTERNAL |
| `__init__` | CalendarDeleteCalendarNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | CalendarDeleteCalendarNode | `self` | `None` | INTERNAL |
| `async _execute_calendar` | CalendarDeleteCalendarNode | `self, context: ExecutionContext, client: GoogleCalendarClient` | `ExecutionResult` | INTERNAL |
| `__init__` | CalendarGetCalendarNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | CalendarGetCalendarNode | `self` | `None` | INTERNAL |
| `async _execute_calendar` | CalendarGetCalendarNode | `self, context: ExecutionContext, client: GoogleCalendarClient` | `ExecutionResult` | INTERNAL |
| `__init__` | CalendarListCalendarsNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | CalendarListCalendarsNode | `self` | `None` | INTERNAL |
| `async _execute_calendar` | CalendarListCalendarsNode | `self, context: ExecutionContext, client: GoogleCalendarClient` | `ExecutionResult` | INTERNAL |


## casare_rpa.nodes.google.docs.docs_read

**File:** `src\casare_rpa\nodes\google\docs\docs_read.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | DocsExportNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | DocsExportNode | `self` | `None` | INTERNAL |
| `async _execute_docs` | DocsExportNode | `self, context: ExecutionContext, client: GoogleDocsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | DocsGetDocumentNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | DocsGetDocumentNode | `self` | `None` | INTERNAL |
| `async _execute_docs` | DocsGetDocumentNode | `self, context: ExecutionContext, client: GoogleDocsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | DocsGetTextNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | DocsGetTextNode | `self` | `None` | INTERNAL |
| `async _execute_docs` | DocsGetTextNode | `self, context: ExecutionContext, client: GoogleDocsClient` | `ExecutionResult` | INTERNAL |


## casare_rpa.nodes.google.docs.docs_write

**File:** `src\casare_rpa\nodes\google\docs\docs_write.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | DocsAppendTextNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | DocsAppendTextNode | `self` | `None` | INTERNAL |
| `async _execute_docs` | DocsAppendTextNode | `self, context: ExecutionContext, client: GoogleDocsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | DocsApplyStyleNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | DocsApplyStyleNode | `self` | `None` | INTERNAL |
| `async _execute_docs` | DocsApplyStyleNode | `self, context: ExecutionContext, client: GoogleDocsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | DocsCreateDocumentNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | DocsCreateDocumentNode | `self` | `None` | INTERNAL |
| `async _execute_docs` | DocsCreateDocumentNode | `self, context: ExecutionContext, client: GoogleDocsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | DocsInsertImageNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | DocsInsertImageNode | `self` | `None` | INTERNAL |
| `async _execute_docs` | DocsInsertImageNode | `self, context: ExecutionContext, client: GoogleDocsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | DocsInsertTableNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | DocsInsertTableNode | `self` | `None` | INTERNAL |
| `async _execute_docs` | DocsInsertTableNode | `self, context: ExecutionContext, client: GoogleDocsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | DocsInsertTextNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | DocsInsertTextNode | `self` | `None` | INTERNAL |
| `async _execute_docs` | DocsInsertTextNode | `self, context: ExecutionContext, client: GoogleDocsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | DocsReplaceTextNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | DocsReplaceTextNode | `self` | `None` | INTERNAL |
| `async _execute_docs` | DocsReplaceTextNode | `self, context: ExecutionContext, client: GoogleDocsClient` | `ExecutionResult` | INTERNAL |


## casare_rpa.nodes.google.docs_nodes

**File:** `src\casare_rpa\nodes\google\docs_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async _get_docs_service` | - | `context: ExecutionContext, credential_name: str` | `Any` | INTERNAL |
| `_define_ports` | DocsBatchUpdateNode | `self` | `None` | INTERNAL |
| `async execute` | DocsBatchUpdateNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | DocsCreateDocumentNode | `self` | `None` | INTERNAL |
| `async execute` | DocsCreateDocumentNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | DocsDeleteContentNode | `self` | `None` | INTERNAL |
| `async execute` | DocsDeleteContentNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | DocsGetContentNode | `self` | `None` | INTERNAL |
| `async execute` | DocsGetContentNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | DocsGetDocumentNode | `self` | `None` | INTERNAL |
| `async execute` | DocsGetDocumentNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | DocsInsertImageNode | `self` | `None` | INTERNAL |
| `async execute` | DocsInsertImageNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | DocsInsertTableNode | `self` | `None` | INTERNAL |
| `async execute` | DocsInsertTableNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | DocsInsertTextNode | `self` | `None` | INTERNAL |
| `async execute` | DocsInsertTextNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | DocsReplaceTextNode | `self` | `None` | INTERNAL |
| `async execute` | DocsReplaceTextNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | DocsUpdateStyleNode | `self` | `None` | INTERNAL |
| `async execute` | DocsUpdateStyleNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.google.drive.drive_batch

**File:** `src\casare_rpa\nodes\google\drive\drive_batch.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async _execute_batch` | - | `session: aiohttp.ClientSession, access_token: str, builder: BatchRequestBuilder` | `List[Dict[str, Any]]` | INTERNAL |
| `_parse_batch_response` | - | `response_text: str, boundary: str` | `List[Dict[str, Any]]` | INTERNAL |
| `__init__` | BatchRequestBuilder | `self, boundary: Optional[str]` | `None` | DUNDER |
| `_add_part` | BatchRequestBuilder | `self, request: str` | `None` | INTERNAL |
| `add_copy` | BatchRequestBuilder | `self, file_id: str, body: Dict[str, Any]` | `None` | USED |
| `add_delete` | BatchRequestBuilder | `self, file_id: str` | `None` | USED |
| `add_update` | BatchRequestBuilder | `self, file_id: str, body: Dict[str, Any]` | `None` | USED |
| `build` | BatchRequestBuilder | `self` | `str` | USED |
| `content_type` | BatchRequestBuilder | `self` | `str` | UNUSED |
| `__init__` | DriveBatchCopyNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | DriveBatchCopyNode | `self` | `None` | INTERNAL |
| `async execute` | DriveBatchCopyNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | DriveBatchDeleteNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | DriveBatchDeleteNode | `self` | `None` | INTERNAL |
| `async execute` | DriveBatchDeleteNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | DriveBatchMoveNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | DriveBatchMoveNode | `self` | `None` | INTERNAL |
| `async _move_single_file` | DriveBatchMoveNode | `self, session: aiohttp.ClientSession, access_token: str, ...` | `Dict[str, Any]` | INTERNAL |
| `async execute` | DriveBatchMoveNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.google.drive.drive_files

**File:** `src\casare_rpa\nodes\google\drive\drive_files.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | DriveCopyFileNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | DriveCopyFileNode | `self` | `None` | INTERNAL |
| `async _execute_drive` | DriveCopyFileNode | `self, context: ExecutionContext, client: GoogleDriveClient` | `ExecutionResult` | INTERNAL |
| `__init__` | DriveDeleteFileNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | DriveDeleteFileNode | `self` | `None` | INTERNAL |
| `async _execute_drive` | DriveDeleteFileNode | `self, context: ExecutionContext, client: GoogleDriveClient` | `ExecutionResult` | INTERNAL |
| `__init__` | DriveDownloadFileNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | DriveDownloadFileNode | `self` | `None` | INTERNAL |
| `async _execute_drive` | DriveDownloadFileNode | `self, context: ExecutionContext, client: GoogleDriveClient` | `ExecutionResult` | INTERNAL |
| `__init__` | DriveGetFileNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | DriveGetFileNode | `self` | `None` | INTERNAL |
| `async _execute_drive` | DriveGetFileNode | `self, context: ExecutionContext, client: GoogleDriveClient` | `ExecutionResult` | INTERNAL |
| `__init__` | DriveMoveFileNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | DriveMoveFileNode | `self` | `None` | INTERNAL |
| `async _execute_drive` | DriveMoveFileNode | `self, context: ExecutionContext, client: GoogleDriveClient` | `ExecutionResult` | INTERNAL |
| `__init__` | DriveRenameFileNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | DriveRenameFileNode | `self` | `None` | INTERNAL |
| `async _execute_drive` | DriveRenameFileNode | `self, context: ExecutionContext, client: GoogleDriveClient` | `ExecutionResult` | INTERNAL |
| `__init__` | DriveUploadFileNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | DriveUploadFileNode | `self` | `None` | INTERNAL |
| `async _execute_drive` | DriveUploadFileNode | `self, context: ExecutionContext, client: GoogleDriveClient` | `ExecutionResult` | INTERNAL |


## casare_rpa.nodes.google.drive.drive_folders

**File:** `src\casare_rpa\nodes\google\drive\drive_folders.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | DriveCreateFolderNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | DriveCreateFolderNode | `self` | `None` | INTERNAL |
| `async _execute_drive` | DriveCreateFolderNode | `self, context: ExecutionContext, client: GoogleDriveClient` | `ExecutionResult` | INTERNAL |
| `__init__` | DriveListFilesNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | DriveListFilesNode | `self` | `None` | INTERNAL |
| `async _execute_drive` | DriveListFilesNode | `self, context: ExecutionContext, client: GoogleDriveClient` | `ExecutionResult` | INTERNAL |
| `__init__` | DriveSearchFilesNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | DriveSearchFilesNode | `self` | `None` | INTERNAL |
| `async _execute_drive` | DriveSearchFilesNode | `self, context: ExecutionContext, client: GoogleDriveClient` | `ExecutionResult` | INTERNAL |


## casare_rpa.nodes.google.drive.drive_share

**File:** `src\casare_rpa\nodes\google\drive\drive_share.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async _make_drive_request` | - | `session: aiohttp.ClientSession, method: str, endpoint: str, ...` | `Dict[str, Any]` | INTERNAL |
| `__init__` | DriveCreateShareLinkNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | DriveCreateShareLinkNode | `self` | `None` | INTERNAL |
| `async execute` | DriveCreateShareLinkNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | DriveGetPermissionsNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | DriveGetPermissionsNode | `self` | `None` | INTERNAL |
| `async execute` | DriveGetPermissionsNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | DriveRemoveShareNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | DriveRemoveShareNode | `self` | `None` | INTERNAL |
| `async execute` | DriveRemoveShareNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | DriveShareFileNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | DriveShareFileNode | `self` | `None` | INTERNAL |
| `async execute` | DriveShareFileNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.google.drive_nodes

**File:** `src\casare_rpa\nodes\google\drive_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | _NotImplementedDriveNode | `self, node_id: str` | `-` | DUNDER |
| `_define_ports` | _NotImplementedDriveNode | `self` | `None` | INTERNAL |
| `async execute` | _NotImplementedDriveNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.google.gmail.gmail_read

**File:** `src\casare_rpa\nodes\google\gmail\gmail_read.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | GmailGetAttachmentNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | GmailGetAttachmentNode | `self` | `None` | INTERNAL |
| `async _execute_gmail` | GmailGetAttachmentNode | `self, context: ExecutionContext, client: GmailClient` | `ExecutionResult` | INTERNAL |
| `__init__` | GmailGetEmailNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | GmailGetEmailNode | `self` | `None` | INTERNAL |
| `async _execute_gmail` | GmailGetEmailNode | `self, context: ExecutionContext, client: GmailClient` | `ExecutionResult` | INTERNAL |
| `__init__` | GmailGetThreadNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | GmailGetThreadNode | `self` | `None` | INTERNAL |
| `async _execute_gmail` | GmailGetThreadNode | `self, context: ExecutionContext, client: GmailClient` | `ExecutionResult` | INTERNAL |
| `__init__` | GmailSearchEmailsNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | GmailSearchEmailsNode | `self` | `None` | INTERNAL |
| `async _execute_gmail` | GmailSearchEmailsNode | `self, context: ExecutionContext, client: GmailClient` | `ExecutionResult` | INTERNAL |


## casare_rpa.nodes.google.gmail.gmail_send

**File:** `src\casare_rpa\nodes\google\gmail\gmail_send.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_parse_email_list` | - | `email_string: str` | `list[str]` | INTERNAL |
| `__init__` | GmailCreateDraftNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | GmailCreateDraftNode | `self` | `None` | INTERNAL |
| `async _execute_gmail` | GmailCreateDraftNode | `self, context: ExecutionContext, client: GmailClient` | `ExecutionResult` | INTERNAL |
| `__init__` | GmailForwardEmailNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | GmailForwardEmailNode | `self` | `None` | INTERNAL |
| `async _execute_gmail` | GmailForwardEmailNode | `self, context: ExecutionContext, client: GmailClient` | `ExecutionResult` | INTERNAL |
| `__init__` | GmailReplyToEmailNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | GmailReplyToEmailNode | `self` | `None` | INTERNAL |
| `async _execute_gmail` | GmailReplyToEmailNode | `self, context: ExecutionContext, client: GmailClient` | `ExecutionResult` | INTERNAL |
| `__init__` | GmailSendEmailNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | GmailSendEmailNode | `self` | `None` | INTERNAL |
| `async _execute_gmail` | GmailSendEmailNode | `self, context: ExecutionContext, client: GmailClient` | `ExecutionResult` | INTERNAL |
| `__init__` | GmailSendWithAttachmentNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | GmailSendWithAttachmentNode | `self` | `None` | INTERNAL |
| `async _execute_gmail` | GmailSendWithAttachmentNode | `self, context: ExecutionContext, client: GmailClient` | `ExecutionResult` | INTERNAL |


## casare_rpa.nodes.google.gmail_nodes

**File:** `src\casare_rpa\nodes\google\gmail_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_create_message` | - | `to: str, subject: str, body: str, ...` | `Dict[str, str]` | INTERNAL |
| `_create_message_with_attachment` | - | `to: str, subject: str, body: str, ...` | `Dict[str, str]` | INTERNAL |
| `async _get_gmail_service` | - | `context: ExecutionContext, credential_name: str` | `Any` | INTERNAL |
| `_define_ports` | GmailAddLabelNode | `self` | `None` | INTERNAL |
| `async execute` | GmailAddLabelNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | GmailArchiveEmailNode | `self` | `None` | INTERNAL |
| `async execute` | GmailArchiveEmailNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | GmailBatchDeleteNode | `self` | `None` | INTERNAL |
| `async execute` | GmailBatchDeleteNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | GmailBatchModifyNode | `self` | `None` | INTERNAL |
| `async execute` | GmailBatchModifyNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | GmailBatchSendNode | `self` | `None` | INTERNAL |
| `async execute` | GmailBatchSendNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | GmailCreateDraftNode | `self` | `None` | INTERNAL |
| `async execute` | GmailCreateDraftNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | GmailDeleteEmailNode | `self` | `None` | INTERNAL |
| `async execute` | GmailDeleteEmailNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | GmailGetEmailNode | `self` | `None` | INTERNAL |
| `async execute` | GmailGetEmailNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | GmailGetLabelsNode | `self` | `None` | INTERNAL |
| `async execute` | GmailGetLabelsNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | GmailGetThreadNode | `self` | `None` | INTERNAL |
| `async execute` | GmailGetThreadNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | GmailListEmailsNode | `self` | `None` | INTERNAL |
| `async execute` | GmailListEmailsNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | GmailMarkAsReadNode | `self` | `None` | INTERNAL |
| `async execute` | GmailMarkAsReadNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | GmailMarkAsUnreadNode | `self` | `None` | INTERNAL |
| `async execute` | GmailMarkAsUnreadNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | GmailModifyLabelsNode | `self` | `None` | INTERNAL |
| `async execute` | GmailModifyLabelsNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | GmailMoveToTrashNode | `self` | `None` | INTERNAL |
| `async execute` | GmailMoveToTrashNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | GmailRemoveLabelNode | `self` | `None` | INTERNAL |
| `async execute` | GmailRemoveLabelNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | GmailSearchEmailsNode | `self` | `None` | INTERNAL |
| `async execute` | GmailSearchEmailsNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | GmailSendDraftNode | `self` | `None` | INTERNAL |
| `async execute` | GmailSendDraftNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | GmailSendEmailNode | `self` | `None` | INTERNAL |
| `async execute` | GmailSendEmailNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | GmailSendWithAttachmentNode | `self` | `None` | INTERNAL |
| `async execute` | GmailSendWithAttachmentNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | GmailStarEmailNode | `self` | `None` | INTERNAL |
| `async execute` | GmailStarEmailNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | GmailTrashEmailNode | `self` | `None` | INTERNAL |
| `async execute` | GmailTrashEmailNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.google.google_base

**File:** `src\casare_rpa\nodes\google\google_base.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `get_calendar_scopes` | - | `readonly: bool` | `List[str]` | UNUSED |
| `get_docs_scopes` | - | `readonly: bool` | `List[str]` | UNUSED |
| `get_drive_scopes` | - | `readonly: bool, file_only: bool` | `List[str]` | UNUSED |
| `get_gmail_scopes` | - | `readonly: bool` | `List[str]` | UNUSED |
| `get_sheets_scopes` | - | `readonly: bool` | `List[str]` | UNUSED |
| `_define_calendar_id_port` | CalendarBaseNode | `self` | `None` | INTERNAL |
| `async _execute_calendar` | CalendarBaseNode | `self, context: ExecutionContext, client: GoogleAPIClient, ...` | `ExecutionResult` | INTERNAL |
| `async _execute_google` | CalendarBaseNode | `self, context: ExecutionContext, client: GoogleAPIClient` | `ExecutionResult` | INTERNAL |
| `_get_calendar_id` | CalendarBaseNode | `self, context: ExecutionContext, default: str` | `str` | INTERNAL |
| `_define_document_id_port` | DocsBaseNode | `self` | `None` | INTERNAL |
| `async _execute_docs` | DocsBaseNode | `self, context: ExecutionContext, client: GoogleAPIClient, ...` | `ExecutionResult` | INTERNAL |
| `async _execute_google` | DocsBaseNode | `self, context: ExecutionContext, client: GoogleAPIClient` | `ExecutionResult` | INTERNAL |
| `_get_document_id` | DocsBaseNode | `self, context: ExecutionContext` | `str` | INTERNAL |
| `_define_file_id_port` | DriveBaseNode | `self` | `None` | INTERNAL |
| `async _execute_drive` | DriveBaseNode | `self, context: ExecutionContext, client: GoogleAPIClient, ...` | `ExecutionResult` | INTERNAL |
| `async _execute_google` | DriveBaseNode | `self, context: ExecutionContext, client: GoogleAPIClient` | `ExecutionResult` | INTERNAL |
| `_get_file_id` | DriveBaseNode | `self, context: ExecutionContext` | `str` | INTERNAL |
| `get_mime_type_from_extension` | DriveBaseNode | `file_path: str` | `str` | UNUSED |
| `is_google_workspace_type` | DriveBaseNode | `mime_type: str` | `bool` | UNUSED |
| `async _execute_gmail` | GmailBaseNode | `self, context: ExecutionContext, client: GoogleAPIClient, ...` | `ExecutionResult` | INTERNAL |
| `async _execute_google` | GmailBaseNode | `self, context: ExecutionContext, client: GoogleAPIClient` | `ExecutionResult` | INTERNAL |
| `__init__` | GoogleBaseNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_common_input_ports` | GoogleBaseNode | `self` | `None` | INTERNAL |
| `_define_common_output_ports` | GoogleBaseNode | `self` | `None` | INTERNAL |
| `async _execute_google` | GoogleBaseNode | `self, context: ExecutionContext, client: GoogleAPIClient` | `ExecutionResult` | INTERNAL |
| `async _get_credentials` | GoogleBaseNode | `self, context: ExecutionContext` | `GoogleCredentials` | INTERNAL |
| `async _get_google_client` | GoogleBaseNode | `self, context: ExecutionContext` | `GoogleAPIClient` | INTERNAL |
| `_set_error_outputs` | GoogleBaseNode | `self, error_msg: str, error_code: int` | `None` | INTERNAL |
| `_set_success_outputs` | GoogleBaseNode | `self` | `None` | INTERNAL |
| `async execute` | GoogleBaseNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_sheet_name_port` | SheetsBaseNode | `self` | `None` | INTERNAL |
| `_define_spreadsheet_id_port` | SheetsBaseNode | `self` | `None` | INTERNAL |
| `async _execute_google` | SheetsBaseNode | `self, context: ExecutionContext, client: GoogleAPIClient` | `ExecutionResult` | INTERNAL |
| `async _execute_sheets` | SheetsBaseNode | `self, context: ExecutionContext, client: GoogleAPIClient, ...` | `ExecutionResult` | INTERNAL |
| `_get_sheet_name` | SheetsBaseNode | `self, context: ExecutionContext, default: str` | `str` | INTERNAL |
| `_get_spreadsheet_id` | SheetsBaseNode | `self, context: ExecutionContext` | `str` | INTERNAL |
| `build_a1_range` | SheetsBaseNode | `cls, sheet_name: Optional[str], start_cell: Optional[str], ...` | `str` | USED |
| `cell_to_indices` | SheetsBaseNode | `cls, cell: str` | `tuple` | UNUSED |
| `column_letter_to_index` | SheetsBaseNode | `column: str` | `int` | USED |
| `index_to_column_letter` | SheetsBaseNode | `index: int` | `str` | USED |
| `indices_to_cell` | SheetsBaseNode | `cls, row: int, col: int` | `str` | USED |


## casare_rpa.nodes.google.sheets.sheets_batch

**File:** `src\casare_rpa\nodes\google\sheets\sheets_batch.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | SheetsBatchClearNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsBatchClearNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsBatchClearNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | SheetsBatchGetNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsBatchGetNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsBatchGetNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | SheetsBatchUpdateNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsBatchUpdateNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsBatchUpdateNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |


## casare_rpa.nodes.google.sheets.sheets_manage

**File:** `src\casare_rpa\nodes\google\sheets\sheets_manage.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | SheetsAddSheetNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsAddSheetNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsAddSheetNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | SheetsCopySheetNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsCopySheetNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsCopySheetNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | SheetsCreateSpreadsheetNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsCreateSpreadsheetNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsCreateSpreadsheetNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | SheetsDeleteSheetNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsDeleteSheetNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsDeleteSheetNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | SheetsDuplicateSheetNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsDuplicateSheetNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsDuplicateSheetNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | SheetsGetSpreadsheetNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsGetSpreadsheetNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsGetSpreadsheetNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | SheetsRenameSheetNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsRenameSheetNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsRenameSheetNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |


## casare_rpa.nodes.google.sheets.sheets_read

**File:** `src\casare_rpa\nodes\google\sheets\sheets_read.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | SheetsGetCellNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsGetCellNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsGetCellNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | SheetsGetColumnNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsGetColumnNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsGetColumnNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | SheetsGetRangeNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsGetRangeNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsGetRangeNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | SheetsGetRowNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsGetRowNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsGetRowNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | SheetsGetSheetInfoNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsGetSheetInfoNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsGetSheetInfoNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | SheetsSearchNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsSearchNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsSearchNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |


## casare_rpa.nodes.google.sheets.sheets_write

**File:** `src\casare_rpa\nodes\google\sheets\sheets_write.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | SheetsAppendRowNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsAppendRowNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsAppendRowNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | SheetsClearRangeNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsClearRangeNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsClearRangeNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | SheetsDeleteRowNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsDeleteRowNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsDeleteRowNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | SheetsInsertRowNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsInsertRowNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsInsertRowNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | SheetsUpdateRowNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsUpdateRowNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsUpdateRowNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | SheetsWriteCellNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsWriteCellNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsWriteCellNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |
| `__init__` | SheetsWriteRangeNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | SheetsWriteRangeNode | `self` | `None` | INTERNAL |
| `async _execute_sheets` | SheetsWriteRangeNode | `self, context: ExecutionContext, client: GoogleSheetsClient` | `ExecutionResult` | INTERNAL |


## casare_rpa.nodes.google.sheets_nodes

**File:** `src\casare_rpa\nodes\google\sheets_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `async _get_sheets_service` | - | `context: ExecutionContext, credential_name: str` | `Any` | INTERNAL |
| `_parse_range` | - | `spreadsheet_id: str, range_notation: str` | `str` | INTERNAL |
| `_define_ports` | SheetsAddSheetNode | `self` | `None` | INTERNAL |
| `async execute` | SheetsAddSheetNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | SheetsAppendRowNode | `self` | `None` | INTERNAL |
| `async execute` | SheetsAppendRowNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | SheetsAutoResizeNode | `self` | `None` | INTERNAL |
| `async execute` | SheetsAutoResizeNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | SheetsBatchClearNode | `self` | `None` | INTERNAL |
| `async execute` | SheetsBatchClearNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | SheetsBatchGetNode | `self` | `None` | INTERNAL |
| `async execute` | SheetsBatchGetNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | SheetsBatchUpdateNode | `self` | `None` | INTERNAL |
| `async execute` | SheetsBatchUpdateNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | SheetsClearRangeNode | `self` | `None` | INTERNAL |
| `async execute` | SheetsClearRangeNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | SheetsCreateSpreadsheetNode | `self` | `None` | INTERNAL |
| `async execute` | SheetsCreateSpreadsheetNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | SheetsDeleteColumnNode | `self` | `None` | INTERNAL |
| `async execute` | SheetsDeleteColumnNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | SheetsDeleteRowNode | `self` | `None` | INTERNAL |
| `async execute` | SheetsDeleteRowNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | SheetsDeleteSheetNode | `self` | `None` | INTERNAL |
| `async execute` | SheetsDeleteSheetNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | SheetsDuplicateSheetNode | `self` | `None` | INTERNAL |
| `async execute` | SheetsDuplicateSheetNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | SheetsFormatCellsNode | `self` | `None` | INTERNAL |
| `async execute` | SheetsFormatCellsNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | SheetsGetCellNode | `self` | `None` | INTERNAL |
| `async execute` | SheetsGetCellNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | SheetsGetRangeNode | `self` | `None` | INTERNAL |
| `async execute` | SheetsGetRangeNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | SheetsGetSpreadsheetNode | `self` | `None` | INTERNAL |
| `async execute` | SheetsGetSpreadsheetNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | SheetsInsertColumnNode | `self` | `None` | INTERNAL |
| `async execute` | SheetsInsertColumnNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | SheetsInsertRowNode | `self` | `None` | INTERNAL |
| `async execute` | SheetsInsertRowNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | SheetsRenameSheetNode | `self` | `None` | INTERNAL |
| `async execute` | SheetsRenameSheetNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | SheetsSetCellNode | `self` | `None` | INTERNAL |
| `async execute` | SheetsSetCellNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `_define_ports` | SheetsWriteRangeNode | `self` | `None` | INTERNAL |
| `async execute` | SheetsWriteRangeNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.http.http_advanced

**File:** `src\casare_rpa\nodes\http\http_advanced.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | BuildUrlNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | BuildUrlNode | `self` | `None` | INTERNAL |
| `async execute` | BuildUrlNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | HttpDownloadFileNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | HttpDownloadFileNode | `self` | `None` | INTERNAL |
| `async execute` | HttpDownloadFileNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | HttpUploadFileNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | HttpUploadFileNode | `self` | `None` | INTERNAL |
| `async execute` | HttpUploadFileNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ParseJsonResponseNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ParseJsonResponseNode | `self` | `None` | INTERNAL |
| `_extract_path` | ParseJsonResponseNode | `self, data: Any, path: str` | `Any` | INTERNAL |
| `async execute` | ParseJsonResponseNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | SetHttpHeadersNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | SetHttpHeadersNode | `self` | `None` | INTERNAL |
| `async execute` | SetHttpHeadersNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.http.http_auth

**File:** `src\casare_rpa\nodes\http\http_auth.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | HttpAuthNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | HttpAuthNode | `self` | `None` | INTERNAL |
| `async execute` | HttpAuthNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | OAuth2AuthorizeNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | OAuth2AuthorizeNode | `self` | `None` | INTERNAL |
| `async execute` | OAuth2AuthorizeNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | OAuth2CallbackServerNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | OAuth2CallbackServerNode | `self` | `None` | INTERNAL |
| `async callback_handler` | OAuth2CallbackServerNode | `request: web.Request` | `web.Response` | UNUSED |
| `async execute` | OAuth2CallbackServerNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | OAuth2TokenExchangeNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | OAuth2TokenExchangeNode | `self` | `None` | INTERNAL |
| `async execute` | OAuth2TokenExchangeNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | OAuth2TokenValidateNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | OAuth2TokenValidateNode | `self` | `None` | INTERNAL |
| `async execute` | OAuth2TokenValidateNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.http.http_base

**File:** `src\casare_rpa\nodes\http\http_base.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `_is_private_ip` | - | `ip_str: str` | `bool` | INTERNAL |
| `validate_url_for_ssrf` | - | `url: str, allow_internal: bool, allow_private_ips: bool` | `str` | USED |
| `__init__` | HttpBaseNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_common_input_ports` | HttpBaseNode | `self, include_body: bool` | `None` | INTERNAL |
| `_define_common_output_ports` | HttpBaseNode | `self` | `None` | INTERNAL |
| `_get_http_method` | HttpBaseNode | `self` | `str` | INTERNAL |
| `_has_request_body` | HttpBaseNode | `self` | `bool` | INTERNAL |
| `async _make_request` | HttpBaseNode | `self, session: aiohttp.ClientSession, url: str, ...` | `tuple[str, int, Dict[str, str]]` | INTERNAL |
| `_parse_json_param` | HttpBaseNode | `self, value: Any, default: Any` | `Any` | INTERNAL |
| `_prepare_request_body` | HttpBaseNode | `self, body: Any` | `Optional[str]` | INTERNAL |
| `_set_error_outputs` | HttpBaseNode | `self, error_msg: str` | `None` | INTERNAL |
| `_set_success_outputs` | HttpBaseNode | `self, response_body: str, status_code: int, ...` | `None` | INTERNAL |
| `async execute` | HttpBaseNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.http.http_basic

**File:** `src\casare_rpa\nodes\http\http_basic.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | HttpRequestNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | HttpRequestNode | `self` | `None` | INTERNAL |
| `_get_http_method` | HttpRequestNode | `self` | `str` | INTERNAL |
| `_has_request_body` | HttpRequestNode | `self` | `bool` | INTERNAL |


## casare_rpa.nodes.interaction_nodes

**File:** `src\casare_rpa\nodes\interaction_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ClickElementNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_build_click_options` | ClickElementNode | `self, timeout: int, button: str, ...` | `dict` | INTERNAL |
| `_define_ports` | ClickElementNode | `self` | `None` | INTERNAL |
| `async execute` | ClickElementNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `async perform_click` | ClickElementNode | `` | `bool` | UNUSED |
| `__init__` | SelectDropdownNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_build_select_options` | SelectDropdownNode | `self, timeout: int, force: bool, ...` | `dict` | INTERNAL |
| `_define_ports` | SelectDropdownNode | `self` | `None` | INTERNAL |
| `async execute` | SelectDropdownNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `async perform_select` | SelectDropdownNode | `` | `bool` | UNUSED |
| `__init__` | TypeTextNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_build_fill_options` | TypeTextNode | `self, timeout: int, force: bool, ...` | `dict` | INTERNAL |
| `_define_ports` | TypeTextNode | `self` | `None` | INTERNAL |
| `async execute` | TypeTextNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `async perform_type` | TypeTextNode | `` | `bool` | UNUSED |


## casare_rpa.nodes.list_nodes

**File:** `src\casare_rpa\nodes\list_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | CreateListNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | CreateListNode | `self` | `None` | INTERNAL |
| `async execute` | CreateListNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ListAppendNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ListAppendNode | `self` | `None` | INTERNAL |
| `async execute` | ListAppendNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ListContainsNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ListContainsNode | `self` | `None` | INTERNAL |
| `async execute` | ListContainsNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ListFilterNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ListFilterNode | `self` | `None` | INTERNAL |
| `async execute` | ListFilterNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `get_item_value` | ListFilterNode | `item: Any` | `Any` | USED |
| `matches` | ListFilterNode | `item: Any` | `bool` | USED |
| `__init__` | ListFlattenNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ListFlattenNode | `self` | `None` | INTERNAL |
| `async execute` | ListFlattenNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `flatten` | ListFlattenNode | `items: Any, current_depth: int` | `list` | USED |
| `__init__` | ListGetItemNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ListGetItemNode | `self` | `None` | INTERNAL |
| `async execute` | ListGetItemNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ListJoinNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ListJoinNode | `self` | `None` | INTERNAL |
| `async execute` | ListJoinNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ListLengthNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ListLengthNode | `self` | `None` | INTERNAL |
| `async execute` | ListLengthNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ListMapNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ListMapNode | `self` | `None` | INTERNAL |
| `apply_transform` | ListMapNode | `item: Any` | `Any` | USED |
| `async execute` | ListMapNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ListReduceNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ListReduceNode | `self` | `None` | INTERNAL |
| `async execute` | ListReduceNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ListReverseNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ListReverseNode | `self` | `None` | INTERNAL |
| `async execute` | ListReverseNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ListSliceNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ListSliceNode | `self` | `None` | INTERNAL |
| `async execute` | ListSliceNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ListSortNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ListSortNode | `self` | `None` | INTERNAL |
| `async execute` | ListSortNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `get_key` | ListSortNode | `item: Any` | `Any` | USED |
| `__init__` | ListUniqueNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ListUniqueNode | `self` | `None` | INTERNAL |
| `async execute` | ListUniqueNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.llm.llm_base

**File:** `src\casare_rpa\nodes\llm\llm_base.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | LLMBaseNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_common_input_ports` | LLMBaseNode | `self` | `None` | INTERNAL |
| `_define_common_output_ports` | LLMBaseNode | `self` | `None` | INTERNAL |
| `async _execute_llm` | LLMBaseNode | `self, context: ExecutionContext, manager: LLMResourceManager` | `ExecutionResult` | INTERNAL |
| `async _get_api_key` | LLMBaseNode | `self, context: ExecutionContext` | `Optional[str]` | INTERNAL |
| `async _get_llm_manager` | LLMBaseNode | `self, context: ExecutionContext` | `LLMResourceManager` | INTERNAL |
| `_get_provider` | LLMBaseNode | `self, context: ExecutionContext` | `LLMProvider` | INTERNAL |
| `_set_error_outputs` | LLMBaseNode | `self, error_msg: str` | `None` | INTERNAL |
| `_set_success_outputs` | LLMBaseNode | `self, response: str, tokens_used: int, ...` | `None` | INTERNAL |
| `async execute` | LLMBaseNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.llm.llm_nodes

**File:** `src\casare_rpa\nodes\llm\llm_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | LLMChatNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | LLMChatNode | `self` | `None` | INTERNAL |
| `async _execute_llm` | LLMChatNode | `self, context: ExecutionContext, manager: LLMResourceManager` | `ExecutionResult` | INTERNAL |
| `__init__` | LLMClassifyNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | LLMClassifyNode | `self` | `None` | INTERNAL |
| `async _execute_llm` | LLMClassifyNode | `self, context: ExecutionContext, manager: LLMResourceManager` | `ExecutionResult` | INTERNAL |
| `__init__` | LLMCompletionNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | LLMCompletionNode | `self` | `None` | INTERNAL |
| `async _execute_llm` | LLMCompletionNode | `self, context: ExecutionContext, manager: LLMResourceManager` | `ExecutionResult` | INTERNAL |
| `__init__` | LLMExtractDataNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | LLMExtractDataNode | `self` | `None` | INTERNAL |
| `async _execute_llm` | LLMExtractDataNode | `self, context: ExecutionContext, manager: LLMResourceManager` | `ExecutionResult` | INTERNAL |
| `__init__` | LLMSummarizeNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | LLMSummarizeNode | `self` | `None` | INTERNAL |
| `async _execute_llm` | LLMSummarizeNode | `self, context: ExecutionContext, manager: LLMResourceManager` | `ExecutionResult` | INTERNAL |
| `__init__` | LLMTranslateNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | LLMTranslateNode | `self` | `None` | INTERNAL |
| `async _execute_llm` | LLMTranslateNode | `self, context: ExecutionContext, manager: LLMResourceManager` | `ExecutionResult` | INTERNAL |


## casare_rpa.nodes.math_nodes

**File:** `src\casare_rpa\nodes\math_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ComparisonNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ComparisonNode | `self` | `None` | INTERNAL |
| `async execute` | ComparisonNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | MathOperationNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | MathOperationNode | `self` | `None` | INTERNAL |
| `async execute` | MathOperationNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.messaging.telegram.telegram_actions

**File:** `src\casare_rpa\nodes\messaging\telegram\telegram_actions.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | TelegramAnswerCallbackNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | TelegramAnswerCallbackNode | `self` | `None` | INTERNAL |
| `async _execute_telegram` | TelegramAnswerCallbackNode | `self, context: ExecutionContext, client: TelegramClient` | `ExecutionResult` | INTERNAL |
| `__init__` | TelegramDeleteMessageNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | TelegramDeleteMessageNode | `self` | `None` | INTERNAL |
| `async _execute_telegram` | TelegramDeleteMessageNode | `self, context: ExecutionContext, client: TelegramClient` | `ExecutionResult` | INTERNAL |
| `__init__` | TelegramEditMessageNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | TelegramEditMessageNode | `self` | `None` | INTERNAL |
| `async _execute_telegram` | TelegramEditMessageNode | `self, context: ExecutionContext, client: TelegramClient` | `ExecutionResult` | INTERNAL |
| `__init__` | TelegramGetUpdatesNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | TelegramGetUpdatesNode | `self` | `None` | INTERNAL |
| `async _execute_telegram` | TelegramGetUpdatesNode | `self, context: ExecutionContext, client: TelegramClient` | `ExecutionResult` | INTERNAL |
| `__init__` | TelegramSendMediaGroupNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | TelegramSendMediaGroupNode | `self` | `None` | INTERNAL |
| `async _execute_telegram` | TelegramSendMediaGroupNode | `self, context: ExecutionContext, client: TelegramClient` | `ExecutionResult` | INTERNAL |


## casare_rpa.nodes.messaging.telegram.telegram_base

**File:** `src\casare_rpa\nodes\messaging\telegram\telegram_base.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | TelegramBaseNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_common_input_ports` | TelegramBaseNode | `self` | `None` | INTERNAL |
| `_define_common_output_ports` | TelegramBaseNode | `self` | `None` | INTERNAL |
| `async _execute_telegram` | TelegramBaseNode | `self, context: ExecutionContext, client: TelegramClient` | `ExecutionResult` | INTERNAL |
| `async _get_bot_token` | TelegramBaseNode | `self, context: ExecutionContext` | `Optional[str]` | INTERNAL |
| `_get_chat_id` | TelegramBaseNode | `self, context: ExecutionContext` | `str` | INTERNAL |
| `async _get_telegram_client` | TelegramBaseNode | `self, context: ExecutionContext` | `TelegramClient` | INTERNAL |
| `_set_error_outputs` | TelegramBaseNode | `self, error_msg: str` | `None` | INTERNAL |
| `_set_success_outputs` | TelegramBaseNode | `self, message_id: int, chat_id: int` | `None` | INTERNAL |
| `async execute` | TelegramBaseNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.messaging.telegram.telegram_send

**File:** `src\casare_rpa\nodes\messaging\telegram\telegram_send.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | TelegramSendDocumentNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | TelegramSendDocumentNode | `self` | `None` | INTERNAL |
| `async _execute_telegram` | TelegramSendDocumentNode | `self, context: ExecutionContext, client: TelegramClient` | `ExecutionResult` | INTERNAL |
| `__init__` | TelegramSendLocationNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | TelegramSendLocationNode | `self` | `None` | INTERNAL |
| `async _execute_telegram` | TelegramSendLocationNode | `self, context: ExecutionContext, client: TelegramClient` | `ExecutionResult` | INTERNAL |
| `__init__` | TelegramSendMessageNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | TelegramSendMessageNode | `self` | `None` | INTERNAL |
| `async _execute_telegram` | TelegramSendMessageNode | `self, context: ExecutionContext, client: TelegramClient` | `ExecutionResult` | INTERNAL |
| `__init__` | TelegramSendPhotoNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | TelegramSendPhotoNode | `self` | `None` | INTERNAL |
| `async _execute_telegram` | TelegramSendPhotoNode | `self, context: ExecutionContext, client: TelegramClient` | `ExecutionResult` | INTERNAL |


## casare_rpa.nodes.messaging.whatsapp.whatsapp_base

**File:** `src\casare_rpa\nodes\messaging\whatsapp\whatsapp_base.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | WhatsAppBaseNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_common_input_ports` | WhatsAppBaseNode | `self` | `None` | INTERNAL |
| `_define_common_output_ports` | WhatsAppBaseNode | `self` | `None` | INTERNAL |
| `async _execute_whatsapp` | WhatsAppBaseNode | `self, context: ExecutionContext, client: WhatsAppClient` | `ExecutionResult` | INTERNAL |
| `async _get_access_token` | WhatsAppBaseNode | `self, context: ExecutionContext` | `Optional[str]` | INTERNAL |
| `async _get_phone_number_id` | WhatsAppBaseNode | `self, context: ExecutionContext` | `Optional[str]` | INTERNAL |
| `_get_recipient` | WhatsAppBaseNode | `self, context: ExecutionContext` | `str` | INTERNAL |
| `async _get_whatsapp_client` | WhatsAppBaseNode | `self, context: ExecutionContext` | `WhatsAppClient` | INTERNAL |
| `_set_error_outputs` | WhatsAppBaseNode | `self, error_msg: str` | `None` | INTERNAL |
| `_set_success_outputs` | WhatsAppBaseNode | `self, message_id: str, phone_number: str` | `None` | INTERNAL |
| `async execute` | WhatsAppBaseNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.messaging.whatsapp.whatsapp_send

**File:** `src\casare_rpa\nodes\messaging\whatsapp\whatsapp_send.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | WhatsAppSendDocumentNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | WhatsAppSendDocumentNode | `self` | `None` | INTERNAL |
| `async _execute_whatsapp` | WhatsAppSendDocumentNode | `self, context: ExecutionContext, client: WhatsAppClient` | `ExecutionResult` | INTERNAL |
| `__init__` | WhatsAppSendImageNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | WhatsAppSendImageNode | `self` | `None` | INTERNAL |
| `async _execute_whatsapp` | WhatsAppSendImageNode | `self, context: ExecutionContext, client: WhatsAppClient` | `ExecutionResult` | INTERNAL |
| `__init__` | WhatsAppSendInteractiveNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | WhatsAppSendInteractiveNode | `self` | `None` | INTERNAL |
| `async _execute_whatsapp` | WhatsAppSendInteractiveNode | `self, context: ExecutionContext, client: WhatsAppClient` | `ExecutionResult` | INTERNAL |
| `__init__` | WhatsAppSendLocationNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | WhatsAppSendLocationNode | `self` | `None` | INTERNAL |
| `async _execute_whatsapp` | WhatsAppSendLocationNode | `self, context: ExecutionContext, client: WhatsAppClient` | `ExecutionResult` | INTERNAL |
| `__init__` | WhatsAppSendMessageNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | WhatsAppSendMessageNode | `self` | `None` | INTERNAL |
| `async _execute_whatsapp` | WhatsAppSendMessageNode | `self, context: ExecutionContext, client: WhatsAppClient` | `ExecutionResult` | INTERNAL |
| `__init__` | WhatsAppSendTemplateNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | WhatsAppSendTemplateNode | `self` | `None` | INTERNAL |
| `async _execute_whatsapp` | WhatsAppSendTemplateNode | `self, context: ExecutionContext, client: WhatsAppClient` | `ExecutionResult` | INTERNAL |
| `__init__` | WhatsAppSendVideoNode | `self, node_id: str` | `None` | DUNDER |
| `_define_ports` | WhatsAppSendVideoNode | `self` | `None` | INTERNAL |
| `async _execute_whatsapp` | WhatsAppSendVideoNode | `self, context: ExecutionContext, client: WhatsAppClient` | `ExecutionResult` | INTERNAL |


## casare_rpa.nodes.navigation_nodes

**File:** `src\casare_rpa\nodes\navigation_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | GoBackNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | GoBackNode | `self` | `None` | INTERNAL |
| `_validate_config` | GoBackNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | GoBackNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | GoForwardNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | GoForwardNode | `self` | `None` | INTERNAL |
| `_validate_config` | GoForwardNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | GoForwardNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | GoToURLNode | `self, node_id: str, name: str, ...` | `None` | DUNDER |
| `_define_ports` | GoToURLNode | `self` | `None` | INTERNAL |
| `_validate_config` | GoToURLNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | GoToURLNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | RefreshPageNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | RefreshPageNode | `self` | `None` | INTERNAL |
| `_validate_config` | RefreshPageNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | RefreshPageNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.parallel_nodes

**File:** `src\casare_rpa\nodes\parallel_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ForkNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | ForkNode | `self` | `None` | INTERNAL |
| `async execute` | ForkNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `set_paired_join` | ForkNode | `self, join_node_id: str` | `None` | USED |
| `__init__` | JoinNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | JoinNode | `self` | `None` | INTERNAL |
| `async execute` | JoinNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `set_paired_fork` | JoinNode | `self, fork_node_id: str` | `None` | USED |
| `__init__` | ParallelForEachNode | `self, node_id: str, config: Optional[dict]` | `None` | DUNDER |
| `_define_ports` | ParallelForEachNode | `self` | `None` | INTERNAL |
| `async execute` | ParallelForEachNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.pdf_nodes

**File:** `src\casare_rpa\nodes\pdf_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ExtractPDFPagesNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ExtractPDFPagesNode | `self` | `None` | INTERNAL |
| `_validate_config` | ExtractPDFPagesNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | ExtractPDFPagesNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | GetPDFInfoNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | GetPDFInfoNode | `self` | `None` | INTERNAL |
| `_validate_config` | GetPDFInfoNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | GetPDFInfoNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | MergePDFsNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | MergePDFsNode | `self` | `None` | INTERNAL |
| `_validate_config` | MergePDFsNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | MergePDFsNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | PDFToImagesNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | PDFToImagesNode | `self` | `None` | INTERNAL |
| `_validate_config` | PDFToImagesNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | PDFToImagesNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ReadPDFTextNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ReadPDFTextNode | `self` | `None` | INTERNAL |
| `_validate_config` | ReadPDFTextNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | ReadPDFTextNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | SplitPDFNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | SplitPDFNode | `self` | `None` | INTERNAL |
| `_validate_config` | SplitPDFNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | SplitPDFNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.random_nodes

**File:** `src\casare_rpa\nodes\random_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | RandomChoiceNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | RandomChoiceNode | `self` | `None` | INTERNAL |
| `_validate_config` | RandomChoiceNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | RandomChoiceNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | RandomNumberNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | RandomNumberNode | `self` | `None` | INTERNAL |
| `_validate_config` | RandomNumberNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | RandomNumberNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | RandomStringNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | RandomStringNode | `self` | `None` | INTERNAL |
| `_validate_config` | RandomStringNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | RandomStringNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | RandomUUIDNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | RandomUUIDNode | `self` | `None` | INTERNAL |
| `_validate_config` | RandomUUIDNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | RandomUUIDNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ShuffleListNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ShuffleListNode | `self` | `None` | INTERNAL |
| `_validate_config` | ShuffleListNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | ShuffleListNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.script_nodes

**File:** `src\casare_rpa\nodes\script_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | EvalExpressionNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | EvalExpressionNode | `self` | `None` | INTERNAL |
| `_validate_config` | EvalExpressionNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | EvalExpressionNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | RunBatchScriptNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | RunBatchScriptNode | `self` | `None` | INTERNAL |
| `_validate_config` | RunBatchScriptNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | RunBatchScriptNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | RunJavaScriptNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | RunJavaScriptNode | `self` | `None` | INTERNAL |
| `_validate_config` | RunJavaScriptNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | RunJavaScriptNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | RunPythonFileNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | RunPythonFileNode | `self` | `None` | INTERNAL |
| `_validate_config` | RunPythonFileNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | RunPythonFileNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | RunPythonScriptNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | RunPythonScriptNode | `self` | `None` | INTERNAL |
| `_run_inline` | RunPythonScriptNode | `self, code: str, variables: Dict[str, Any]` | `tuple[Any, str, str]` | INTERNAL |
| `async _run_isolated` | RunPythonScriptNode | `self, code: str, variables: Dict[str, Any], ...` | `tuple[Any, str, str]` | INTERNAL |
| `_validate_config` | RunPythonScriptNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | RunPythonScriptNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.string_nodes

**File:** `src\casare_rpa\nodes\string_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ConcatenateNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ConcatenateNode | `self` | `None` | INTERNAL |
| `async execute` | ConcatenateNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | FormatStringNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | FormatStringNode | `self` | `None` | INTERNAL |
| `async execute` | FormatStringNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | RegexMatchNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | RegexMatchNode | `self` | `None` | INTERNAL |
| `async execute` | RegexMatchNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | RegexReplaceNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | RegexReplaceNode | `self` | `None` | INTERNAL |
| `async execute` | RegexReplaceNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.system.clipboard_nodes

**File:** `src\casare_rpa\nodes\system\clipboard_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ClipboardClearNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ClipboardClearNode | `self` | `None` | INTERNAL |
| `_validate_config` | ClipboardClearNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | ClipboardClearNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ClipboardCopyNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ClipboardCopyNode | `self` | `None` | INTERNAL |
| `_validate_config` | ClipboardCopyNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | ClipboardCopyNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ClipboardPasteNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ClipboardPasteNode | `self` | `None` | INTERNAL |
| `_validate_config` | ClipboardPasteNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | ClipboardPasteNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.system.command_nodes

**File:** `src\casare_rpa\nodes\system\command_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | RunCommandNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | RunCommandNode | `self` | `None` | INTERNAL |
| `async execute` | RunCommandNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | RunPowerShellNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | RunPowerShellNode | `self` | `None` | INTERNAL |
| `async execute` | RunPowerShellNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.system.dialog_nodes

**File:** `src\casare_rpa\nodes\system\dialog_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | InputDialogNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | InputDialogNode | `self` | `None` | INTERNAL |
| `async execute` | InputDialogNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `on_finished` | InputDialogNode | `result_code` | `-` | UNUSED |
| `__init__` | MessageBoxNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | MessageBoxNode | `self` | `None` | INTERNAL |
| `_play_system_sound` | MessageBoxNode | `self, icon_type: str` | `None` | INTERNAL |
| `async _show_qt_dialog` | MessageBoxNode | `self, title: str, message: str, ...` | `tuple[str, bool]` | INTERNAL |
| `_show_windows_dialog` | MessageBoxNode | `self, title: str, message: str, ...` | `tuple[str, bool]` | INTERNAL |
| `auto_close_timer` | MessageBoxNode | `` | `-` | UNUSED |
| `async execute` | MessageBoxNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `on_finished` | MessageBoxNode | `button_result` | `-` | UNUSED |
| `on_timeout` | MessageBoxNode | `` | `-` | UNUSED |
| `__init__` | TooltipNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | TooltipNode | `self` | `None` | INTERNAL |
| `async execute` | TooltipNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.system.service_nodes

**File:** `src\casare_rpa\nodes\system\service_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | GetServiceStatusNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | GetServiceStatusNode | `self` | `None` | INTERNAL |
| `async execute` | GetServiceStatusNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ListServicesNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ListServicesNode | `self` | `None` | INTERNAL |
| `async execute` | ListServicesNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | RestartServiceNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | RestartServiceNode | `self` | `None` | INTERNAL |
| `async execute` | RestartServiceNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | StartServiceNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | StartServiceNode | `self` | `None` | INTERNAL |
| `async execute` | StartServiceNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | StopServiceNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | StopServiceNode | `self` | `None` | INTERNAL |
| `async execute` | StopServiceNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.text_nodes

**File:** `src\casare_rpa\nodes\text_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | TextCaseNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | TextCaseNode | `self` | `None` | INTERNAL |
| `_validate_config` | TextCaseNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | TextCaseNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | TextContainsNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | TextContainsNode | `self` | `None` | INTERNAL |
| `_validate_config` | TextContainsNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | TextContainsNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | TextCountNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | TextCountNode | `self` | `None` | INTERNAL |
| `_validate_config` | TextCountNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | TextCountNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | TextEndsWithNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | TextEndsWithNode | `self` | `None` | INTERNAL |
| `_validate_config` | TextEndsWithNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | TextEndsWithNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | TextExtractNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | TextExtractNode | `self` | `None` | INTERNAL |
| `_validate_config` | TextExtractNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | TextExtractNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | TextJoinNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | TextJoinNode | `self` | `None` | INTERNAL |
| `_validate_config` | TextJoinNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | TextJoinNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | TextLinesNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | TextLinesNode | `self` | `None` | INTERNAL |
| `_validate_config` | TextLinesNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | TextLinesNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | TextPadNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | TextPadNode | `self` | `None` | INTERNAL |
| `_validate_config` | TextPadNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | TextPadNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | TextReplaceNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | TextReplaceNode | `self` | `None` | INTERNAL |
| `_validate_config` | TextReplaceNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | TextReplaceNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | TextReverseNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | TextReverseNode | `self` | `None` | INTERNAL |
| `_validate_config` | TextReverseNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | TextReverseNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | TextSplitNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | TextSplitNode | `self` | `None` | INTERNAL |
| `_validate_config` | TextSplitNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | TextSplitNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | TextStartsWithNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | TextStartsWithNode | `self` | `None` | INTERNAL |
| `_validate_config` | TextStartsWithNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | TextStartsWithNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | TextSubstringNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | TextSubstringNode | `self` | `None` | INTERNAL |
| `_validate_config` | TextSubstringNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | TextSubstringNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | TextTrimNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | TextTrimNode | `self` | `None` | INTERNAL |
| `_validate_config` | TextTrimNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | TextTrimNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.trigger_nodes.app_event_trigger_node

**File:** `src\casare_rpa\nodes\trigger_nodes\app_event_trigger_node.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | AppEventTriggerNode | `self, node_id: str, config: Optional[Dict]` | `None` | DUNDER |
| `_define_payload_ports` | AppEventTriggerNode | `self` | `None` | INTERNAL |
| `get_trigger_config` | AppEventTriggerNode | `self` | `Dict[str, Any]` | USED |
| `get_trigger_type` | AppEventTriggerNode | `self` | `TriggerType` | USED |


## casare_rpa.nodes.trigger_nodes.base_trigger_node

**File:** `src\casare_rpa\nodes\trigger_nodes\base_trigger_node.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `trigger_node` | - | `cls: Type` | `Type` | UNUSED |
| `__init__` | BaseTriggerNode | `self, node_id: NodeId, config: Optional[NodeConfig]` | `None` | DUNDER |
| `_define_payload_ports` | BaseTriggerNode | `self` | `None` | INTERNAL |
| `_define_ports` | BaseTriggerNode | `self` | `None` | INTERNAL |
| `create_trigger_config` | BaseTriggerNode | `self, workflow_id: str, scenario_id: str, ...` | `BaseTriggerConfig` | USED |
| `create_trigger_instance` | BaseTriggerNode | `self, workflow_id: str, scenario_id: str, ...` | `Optional[BaseTrigger]` | UNUSED |
| `async execute` | BaseTriggerNode | `self, context: Any` | `ExecutionResult` | USED |
| `get_trigger_config` | BaseTriggerNode | `self` | `Dict[str, Any]` | USED |
| `get_trigger_instance` | BaseTriggerNode | `self` | `Optional[BaseTrigger]` | UNUSED |
| `get_trigger_type` | BaseTriggerNode | `self` | `TriggerType` | USED |
| `is_listening` | BaseTriggerNode | `self` | `bool` | UNUSED |
| `populate_from_trigger_event` | BaseTriggerNode | `self, payload: Dict[str, Any]` | `None` | UNUSED |
| `set_listening` | BaseTriggerNode | `self, listening: bool` | `None` | USED |


## casare_rpa.nodes.trigger_nodes.calendar_trigger_node

**File:** `src\casare_rpa\nodes\trigger_nodes\calendar_trigger_node.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | CalendarTriggerNode | `self, node_id: str, config: Optional[Dict]` | `None` | DUNDER |
| `_define_payload_ports` | CalendarTriggerNode | `self` | `None` | INTERNAL |
| `get_trigger_config` | CalendarTriggerNode | `self` | `Dict[str, Any]` | USED |
| `get_trigger_type` | CalendarTriggerNode | `self` | `TriggerType` | USED |


## casare_rpa.nodes.trigger_nodes.chat_trigger_node

**File:** `src\casare_rpa\nodes\trigger_nodes\chat_trigger_node.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ChatTriggerNode | `self, node_id: str, config: Optional[Dict]` | `None` | DUNDER |
| `_define_payload_ports` | ChatTriggerNode | `self` | `None` | INTERNAL |
| `get_trigger_config` | ChatTriggerNode | `self` | `Dict[str, Any]` | USED |
| `get_trigger_type` | ChatTriggerNode | `self` | `TriggerType` | USED |


## casare_rpa.nodes.trigger_nodes.drive_trigger_node

**File:** `src\casare_rpa\nodes\trigger_nodes\drive_trigger_node.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | DriveTriggerNode | `self, node_id: str, config: Optional[Dict]` | `None` | DUNDER |
| `_define_payload_ports` | DriveTriggerNode | `self` | `None` | INTERNAL |
| `get_trigger_config` | DriveTriggerNode | `self` | `Dict[str, Any]` | USED |
| `get_trigger_type` | DriveTriggerNode | `self` | `TriggerType` | USED |


## casare_rpa.nodes.trigger_nodes.email_trigger_node

**File:** `src\casare_rpa\nodes\trigger_nodes\email_trigger_node.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | EmailTriggerNode | `self, node_id: str, config: Optional[Dict]` | `None` | DUNDER |
| `_define_payload_ports` | EmailTriggerNode | `self` | `None` | INTERNAL |
| `get_trigger_config` | EmailTriggerNode | `self` | `Dict[str, Any]` | USED |
| `get_trigger_type` | EmailTriggerNode | `self` | `TriggerType` | USED |


## casare_rpa.nodes.trigger_nodes.error_trigger_node

**File:** `src\casare_rpa\nodes\trigger_nodes\error_trigger_node.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ErrorTriggerNode | `self, node_id: str, config: Optional[Dict]` | `None` | DUNDER |
| `_define_payload_ports` | ErrorTriggerNode | `self` | `None` | INTERNAL |
| `get_trigger_config` | ErrorTriggerNode | `self` | `Dict[str, Any]` | USED |
| `get_trigger_type` | ErrorTriggerNode | `self` | `TriggerType` | USED |


## casare_rpa.nodes.trigger_nodes.file_watch_trigger_node

**File:** `src\casare_rpa\nodes\trigger_nodes\file_watch_trigger_node.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | FileWatchTriggerNode | `self, node_id: str, config: Optional[Dict]` | `None` | DUNDER |
| `_define_payload_ports` | FileWatchTriggerNode | `self` | `None` | INTERNAL |
| `get_trigger_config` | FileWatchTriggerNode | `self` | `Dict[str, Any]` | USED |
| `get_trigger_type` | FileWatchTriggerNode | `self` | `TriggerType` | USED |


## casare_rpa.nodes.trigger_nodes.form_trigger_node

**File:** `src\casare_rpa\nodes\trigger_nodes\form_trigger_node.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | FormTriggerNode | `self, node_id: str, config: Optional[Dict]` | `None` | DUNDER |
| `_define_payload_ports` | FormTriggerNode | `self` | `None` | INTERNAL |
| `get_trigger_config` | FormTriggerNode | `self` | `Dict[str, Any]` | USED |
| `get_trigger_type` | FormTriggerNode | `self` | `TriggerType` | USED |


## casare_rpa.nodes.trigger_nodes.gmail_trigger_node

**File:** `src\casare_rpa\nodes\trigger_nodes\gmail_trigger_node.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | GmailTriggerNode | `self, node_id: str, config: Optional[Dict]` | `None` | DUNDER |
| `_define_payload_ports` | GmailTriggerNode | `self` | `None` | INTERNAL |
| `get_trigger_config` | GmailTriggerNode | `self` | `Dict[str, Any]` | USED |
| `get_trigger_type` | GmailTriggerNode | `self` | `TriggerType` | USED |


## casare_rpa.nodes.trigger_nodes.rss_feed_trigger_node

**File:** `src\casare_rpa\nodes\trigger_nodes\rss_feed_trigger_node.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | RSSFeedTriggerNode | `self, node_id: str, config: Optional[Dict]` | `None` | DUNDER |
| `_define_payload_ports` | RSSFeedTriggerNode | `self` | `None` | INTERNAL |
| `get_trigger_config` | RSSFeedTriggerNode | `self` | `Dict[str, Any]` | USED |
| `get_trigger_type` | RSSFeedTriggerNode | `self` | `TriggerType` | USED |


## casare_rpa.nodes.trigger_nodes.schedule_trigger_node

**File:** `src\casare_rpa\nodes\trigger_nodes\schedule_trigger_node.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | ScheduleTriggerNode | `self, node_id: str, config: Optional[Dict]` | `None` | DUNDER |
| `_define_payload_ports` | ScheduleTriggerNode | `self` | `None` | INTERNAL |
| `get_trigger_config` | ScheduleTriggerNode | `self` | `Dict[str, Any]` | USED |
| `get_trigger_type` | ScheduleTriggerNode | `self` | `TriggerType` | USED |


## casare_rpa.nodes.trigger_nodes.sheets_trigger_node

**File:** `src\casare_rpa\nodes\trigger_nodes\sheets_trigger_node.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | SheetsTriggerNode | `self, node_id: str, config: Optional[Dict]` | `None` | DUNDER |
| `_define_payload_ports` | SheetsTriggerNode | `self` | `None` | INTERNAL |
| `get_trigger_config` | SheetsTriggerNode | `self` | `Dict[str, Any]` | USED |
| `get_trigger_type` | SheetsTriggerNode | `self` | `TriggerType` | USED |


## casare_rpa.nodes.trigger_nodes.sse_trigger_node

**File:** `src\casare_rpa\nodes\trigger_nodes\sse_trigger_node.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | SSETriggerNode | `self, node_id: str, config: Optional[Dict]` | `None` | DUNDER |
| `_define_payload_ports` | SSETriggerNode | `self` | `None` | INTERNAL |
| `get_trigger_config` | SSETriggerNode | `self` | `Dict[str, Any]` | USED |
| `get_trigger_type` | SSETriggerNode | `self` | `TriggerType` | USED |


## casare_rpa.nodes.trigger_nodes.telegram_trigger_node

**File:** `src\casare_rpa\nodes\trigger_nodes\telegram_trigger_node.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | TelegramTriggerNode | `self, node_id: str, config: Optional[Dict]` | `None` | DUNDER |
| `_define_payload_ports` | TelegramTriggerNode | `self` | `None` | INTERNAL |
| `get_trigger_config` | TelegramTriggerNode | `self` | `Dict[str, Any]` | USED |
| `get_trigger_type` | TelegramTriggerNode | `self` | `TriggerType` | USED |


## casare_rpa.nodes.trigger_nodes.webhook_trigger_node

**File:** `src\casare_rpa\nodes\trigger_nodes\webhook_trigger_node.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | WebhookTriggerNode | `self, node_id: str, config: Optional[Dict]` | `None` | DUNDER |
| `_define_payload_ports` | WebhookTriggerNode | `self` | `None` | INTERNAL |
| `get_trigger_config` | WebhookTriggerNode | `self` | `Dict[str, Any]` | USED |
| `get_trigger_type` | WebhookTriggerNode | `self` | `TriggerType` | USED |
| `get_webhook_url` | WebhookTriggerNode | `self, base_url: str` | `str` | USED |


## casare_rpa.nodes.trigger_nodes.whatsapp_trigger_node

**File:** `src\casare_rpa\nodes\trigger_nodes\whatsapp_trigger_node.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | WhatsAppTriggerNode | `self, node_id: str, config: Optional[Dict]` | `None` | DUNDER |
| `_define_payload_ports` | WhatsAppTriggerNode | `self` | `None` | INTERNAL |
| `get_trigger_config` | WhatsAppTriggerNode | `self` | `Dict[str, Any]` | USED |
| `get_trigger_type` | WhatsAppTriggerNode | `self` | `TriggerType` | USED |


## casare_rpa.nodes.trigger_nodes.workflow_call_trigger_node

**File:** `src\casare_rpa\nodes\trigger_nodes\workflow_call_trigger_node.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | WorkflowCallTriggerNode | `self, node_id: str, config: Optional[Dict]` | `None` | DUNDER |
| `_define_payload_ports` | WorkflowCallTriggerNode | `self` | `None` | INTERNAL |
| `get_trigger_config` | WorkflowCallTriggerNode | `self` | `Dict[str, Any]` | USED |
| `get_trigger_type` | WorkflowCallTriggerNode | `self` | `TriggerType` | USED |


## casare_rpa.nodes.utility_nodes

**File:** `src\casare_rpa\nodes\utility_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | HttpRequestNode | `self, node_id: str, name: str, ...` | `None` | DUNDER |
| `_define_ports` | HttpRequestNode | `self` | `None` | INTERNAL |
| `async execute` | HttpRequestNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | LogNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | LogNode | `self` | `None` | INTERNAL |
| `async execute` | LogNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | TransformNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | TransformNode | `self` | `None` | INTERNAL |
| `_transform` | TransformNode | `self, value: Any, transform_type: str, ...` | `Any` | INTERNAL |
| `async execute` | TransformNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ValidateNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ValidateNode | `self` | `None` | INTERNAL |
| `_validate` | ValidateNode | `self, value: Any, validation_type: str, ...` | `tuple[bool, str]` | INTERNAL |
| `async execute` | ValidateNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.variable_nodes

**File:** `src\casare_rpa\nodes\variable_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | GetVariableNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | GetVariableNode | `self` | `None` | INTERNAL |
| `async execute` | GetVariableNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | IncrementVariableNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | IncrementVariableNode | `self` | `None` | INTERNAL |
| `async execute` | IncrementVariableNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | SetVariableNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | SetVariableNode | `self` | `None` | INTERNAL |
| `async execute` | SetVariableNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.wait_nodes

**File:** `src\casare_rpa\nodes\wait_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | WaitForElementNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | WaitForElementNode | `self` | `None` | INTERNAL |
| `_validate_config` | WaitForElementNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | WaitForElementNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | WaitForNavigationNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | WaitForNavigationNode | `self` | `None` | INTERNAL |
| `_validate_config` | WaitForNavigationNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | WaitForNavigationNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | WaitNode | `self, node_id: str, name: str, ...` | `None` | DUNDER |
| `_define_ports` | WaitNode | `self` | `None` | INTERNAL |
| `_validate_config` | WaitNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | WaitNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |


## casare_rpa.nodes.xml_nodes

**File:** `src\casare_rpa\nodes\xml_nodes.py`

| Function | Class | Parameters | Returns | Status |
|----------|-------|------------|---------|--------|
| `__init__` | GetXMLAttributeNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | GetXMLAttributeNode | `self` | `None` | INTERNAL |
| `_validate_config` | GetXMLAttributeNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | GetXMLAttributeNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | GetXMLElementNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | GetXMLElementNode | `self` | `None` | INTERNAL |
| `_validate_config` | GetXMLElementNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | GetXMLElementNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | JsonToXMLNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | JsonToXMLNode | `self` | `None` | INTERNAL |
| `_validate_config` | JsonToXMLNode | `self` | `tuple[bool, str]` | INTERNAL |
| `dict_to_xml` | JsonToXMLNode | `data, parent` | `-` | USED |
| `async execute` | JsonToXMLNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ParseXMLNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ParseXMLNode | `self` | `None` | INTERNAL |
| `_validate_config` | ParseXMLNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | ParseXMLNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | ReadXMLFileNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | ReadXMLFileNode | `self` | `None` | INTERNAL |
| `_validate_config` | ReadXMLFileNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | ReadXMLFileNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | WriteXMLFileNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | WriteXMLFileNode | `self` | `None` | INTERNAL |
| `_validate_config` | WriteXMLFileNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | WriteXMLFileNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | XMLToJsonNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | XMLToJsonNode | `self` | `None` | INTERNAL |
| `_validate_config` | XMLToJsonNode | `self` | `tuple[bool, str]` | INTERNAL |
| `element_to_dict` | XMLToJsonNode | `elem` | `-` | USED |
| `async execute` | XMLToJsonNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
| `__init__` | XPathQueryNode | `self, node_id: str, name: str` | `None` | DUNDER |
| `_define_ports` | XPathQueryNode | `self` | `None` | INTERNAL |
| `_validate_config` | XPathQueryNode | `self` | `tuple[bool, str]` | INTERNAL |
| `async execute` | XPathQueryNode | `self, context: ExecutionContext` | `ExecutionResult` | USED |
