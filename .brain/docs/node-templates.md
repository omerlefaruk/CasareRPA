# Node Templates & Generators

> Quick-start templates for creating atomic nodes following CasareRPA patterns.
> **MANDATORY**: Use these templates for ALL new nodes. They ensure consistency and proper registration.

## Modern Node Standard (2025)

**All nodes MUST follow Schema-Driven Logic:**

```python
@properties(
    PropertyDef("url", PropertyType.STRING, required=True),
    PropertyDef("timeout", PropertyType.INTEGER, default=30000),
)
@node(category="browser")
class MyNode(BaseNode):
    async def execute(self, context):
        # MODERN: get_parameter() checks port first, then config
        url = self.get_parameter("url")              # required
        timeout = self.get_parameter("timeout", 30000)  # optional

        # LEGACY (DON'T USE): self.config.get("timeout", 30000)
```

**Requirements:**
- `@properties()` decorator (REQUIRED - even if empty)
- `get_parameter()` for optional properties (dual-source access)
- Explicit DataType on all ports (ANY is valid for polymorphic)
- NO `self.config.get()` calls

**Audit compliance:** `python scripts/audit_node_modernization.py`

## Template Selection Guide

| Category | Base Class | Location | Use When |
|----------|------------|----------|----------|
| Browser | BrowserBaseNode | `nodes/browser/` | Web automation with Playwright |
| Desktop | DesktopNodeBase | `nodes/desktop_nodes/` | Windows UI automation |
| Data | BaseNode | `nodes/data_nodes.py` | Data transformation |
| Control Flow | BaseNode | `nodes/control_flow_nodes.py` | If/Loop/Try logic |
| File | BaseNode | `nodes/file/` | File operations |
| HTTP | BaseNode + UnifiedHttpClient | `nodes/http/` | API calls |
| Google | BaseNode | `nodes/google/` | Google services |
| System | BaseNode | `nodes/system/` | OS/Dialog operations |
| Variable | BaseNode | `nodes/variable_nodes.py` | Get/Set variables |
| String | BaseNode | `nodes/string_nodes.py` | String operations |
| List | BaseNode | `nodes/list_nodes.py` | List operations |
| Dict | BaseNode | `nodes/dict_nodes.py` | Dict operations |
| DateTime | BaseNode | `nodes/datetime_nodes.py` | Date/time operations |

---

## Template 1: Browser Node (Playwright)

**Use for**: Web page interactions, element operations, navigation

```python
"""
Browser {Operation} Node

{Brief description - single atomic operation on web page.}
"""

from typing import Any, Dict, Optional
from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.nodes.browser.browser_base import BrowserBaseNode
from casare_rpa.nodes.browser.property_constants import (
    BROWSER_SELECTOR,
    BROWSER_TIMEOUT,
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_SCREENSHOT_ON_FAIL,
)


@properties(
    BROWSER_SELECTOR,
    BROWSER_TIMEOUT,
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_SCREENSHOT_ON_FAIL,
)
@node(category="browser")
class {Operation}Node(BrowserBaseNode):
    """
    {One-line description of atomic operation}.

    Config (via @properties):
        selector: CSS/XPath selector for target element
        timeout: Operation timeout in ms (default: 30000)
        retry_count: Number of retries on failure (default: 0)
        retry_interval: Delay between retries in ms (default: 1000)
        screenshot_on_fail: Capture screenshot on error (default: False)

    Inputs:
        page: Playwright page object (passthrough)
        selector: Element selector (overrides config)

    Outputs:
        page: Playwright page object (passthrough)
        result: Operation result
    """

    # @category: browser
    # @requires: playwright
    # @ports: page, selector -> page, result

    NODE_NAME = "{Operation}"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "{Operation}",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "{Operation}Node"

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the browser operation."""
        page = self.get_page(context)
        # MODERN: get_parameter() for dual-source access
        selector = self.normalize_selector(self.get_parameter("selector"))
        timeout = self.get_parameter("timeout", 30000)

        if not selector:
            raise ValueError("Selector is required")

        logger.info(f"[{self.name}] {Operation} on: {selector}")

        try:
            locator = page.locator(selector)
            await locator.wait_for(state="visible", timeout=timeout)

            # ===== YOUR ATOMIC OPERATION HERE =====
            result = await locator.text_content()
            # ======================================

            logger.info(f"[{self.name}] Success")
            return self.success_result(page=page, result=result)

        except Exception as e:
            return self.error_result(f"{Operation} failed: {e}")
```

---

## Template 2: Desktop Node (Windows UI Automation)

**Use for**: Windows application automation, UI element interaction

```python
"""
Desktop {Operation} Node

{Brief description - single atomic operation on Windows UI.}
"""

from typing import Any, Dict, Optional
from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.value_objects.types import DataType, NodeStatus
from casare_rpa.nodes.desktop_nodes.desktop_base import DesktopNodeBase
from casare_rpa.nodes.desktop_nodes.properties import (
    SELECTOR_PROP,
    TIMEOUT_PROP,
    THROW_ON_NOT_FOUND_PROP,
)


@properties(
    SELECTOR_PROP,
    TIMEOUT_PROP,
    THROW_ON_NOT_FOUND_PROP,
)
@node(category="desktop")
class {Operation}Node(DesktopNodeBase):
    """
    {One-line description of atomic operation}.

    Config (via @properties):
        selector: Element selector dict with strategy/value
        timeout: Operation timeout in seconds (default: 5.0)
        throw_on_not_found: Raise error if element not found (default: True)

    Inputs:
        window: Desktop window object from LaunchApplicationNode

    Outputs:
        result: Operation result
        success: Whether operation succeeded
    """

    # @category: desktop
    # @requires: pywin32, uiautomation
    # @ports: window -> result, success

    NODE_NAME = "{Operation}"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "{Operation}",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "{Operation}Node"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("window", DataType.ANY)
        self.add_output_port("result", DataType.ANY)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the desktop operation."""
        window = self.get_input_value("window")
        selector = self.get_parameter("selector", context)
        timeout = self.get_parameter("timeout", context)
        throw_on_not_found = self.get_parameter("throw_on_not_found", context)

        if not window:
            raise ValueError("Window is required. Connect from LaunchApplicationNode.")

        desktop_ctx = self.get_desktop_context(context)
        logger.info(f"[{self.name}] Performing {Operation}")

        try:
            # Find element if selector provided
            element = window
            if selector:
                element = window.find_child(selector, timeout=timeout)
                if not element and throw_on_not_found:
                    raise RuntimeError(f"Element not found: {selector}")

            # ===== YOUR ATOMIC OPERATION HERE =====
            result = element.get_text() if element else None
            # ======================================

            self.set_output_value("success", True)
            return self.success_result(result=result, success=True)

        except Exception as e:
            self.handle_error(e, f"{Operation}")
            return {"success": False, "data": {"success": False}, "next_nodes": []}
```

---

## Template 3: Control Flow Node

**Use for**: Conditionals, loops, error handling logic

```python
"""
{Operation} Control Flow Node

{Brief description - single control flow operation.}
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, NodeStatus, PortType


# Control flow specific property
EXPRESSION_PROP = PropertyDef(
    "expression",
    PropertyType.STRING,
    default="",
    label="Expression",
    tooltip="Boolean expression to evaluate (e.g., {{count}} > 0)",
    tab="properties",
)


@node_schema(EXPRESSION_PROP)
@executable_node
class {Operation}Node(BaseNode):
    """
    {One-line description of control flow operation}.

    Config (via @node_schema):
        expression: Boolean expression to evaluate

    Inputs:
        condition: Boolean condition (overrides expression)

    Outputs:
        true: Execution path when condition is true
        false: Execution path when condition is false
    """

    # @category: control_flow
    # @requires: none
    # @ports: condition -> true, false (exec ports)

    NODE_NAME = "{Operation}"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "{Operation}",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "{Operation}Node"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("condition", PortType.INPUT, DataType.BOOLEAN, required=False)
        # Note: exec_in/exec_out added by @executable_node
        # Additional exec outputs for branching
        self.add_output_port("true", PortType.EXEC_OUTPUT, DataType.EXEC)
        self.add_output_port("false", PortType.EXEC_OUTPUT, DataType.EXEC)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the control flow operation."""
        # Get condition from port or evaluate expression
        condition = self.get_input_value("condition")
        if condition is None:
            expression = self.get_parameter("expression", context)
            if expression:
                # Evaluate expression using context variables
                condition = self._evaluate_expression(expression, context)
            else:
                condition = False

        logger.debug(f"[{self.name}] Condition evaluated to: {condition}")

        # Return appropriate next nodes based on condition
        if condition:
            return {"success": True, "data": {}, "next_nodes": ["true"]}
        else:
            return {"success": True, "data": {}, "next_nodes": ["false"]}

    def _evaluate_expression(self, expression: str, context: Any) -> bool:
        """Evaluate boolean expression with context variables."""
        # Replace {{variable}} with actual values
        variables = getattr(context, "variables", {})
        for var_name, var_value in variables.items():
            expression = expression.replace(f"{{{{{var_name}}}}}", str(var_value))

        try:
            return bool(eval(expression))
        except Exception as e:
            logger.warning(f"[{self.name}] Expression eval failed: {e}")
            return False
```

---

## Template 4: File Operation Node

**Use for**: Reading, writing, copying, deleting files

```python
"""
File {Operation} Node

{Brief description - single atomic file operation.}
"""

from pathlib import Path
from typing import Any, Dict, Optional
from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, NodeStatus, PortType


# File operation properties
FILE_PATH_PROP = PropertyDef(
    "file_path",
    PropertyType.FILE_PATH,
    required=True,
    label="File Path",
    tooltip="Path to the file",
    tab="properties",
)

ENCODING_PROP = PropertyDef(
    "encoding",
    PropertyType.CHOICE,
    default="utf-8",
    choices=["utf-8", "utf-16", "ascii", "latin-1"],
    label="Encoding",
    tooltip="Text encoding for the file",
    tab="advanced",
)

CREATE_IF_NOT_EXISTS_PROP = PropertyDef(
    "create_if_not_exists",
    PropertyType.BOOLEAN,
    default=False,
    label="Create If Not Exists",
    tooltip="Create parent directories if they don't exist",
    tab="advanced",
)


@node_schema(
    FILE_PATH_PROP,
    ENCODING_PROP,
    CREATE_IF_NOT_EXISTS_PROP,
)
@executable_node
class File{Operation}Node(BaseNode):
    """
    {One-line description of file operation}.

    Config (via @node_schema):
        file_path: Path to the file (required)
        encoding: Text encoding (default: utf-8)
        create_if_not_exists: Create directories if needed (default: False)

    Inputs:
        file_path: File path (overrides config)
        content: Content to write (for write operations)

    Outputs:
        content: File content (for read operations)
        success: Whether operation succeeded
        file_path: Absolute path to the file
    """

    # @category: file
    # @requires: none
    # @ports: file_path, content -> content, success, file_path

    NODE_NAME = "File {Operation}"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "File {Operation}",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "File{Operation}Node"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port("content", PortType.INPUT, DataType.STRING, required=False)
        self.add_output_port("content", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("file_path", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the file operation."""
        file_path = self.get_parameter("file_path", context)
        encoding = self.get_parameter("encoding", context)
        create_dirs = self.get_parameter("create_if_not_exists", context)

        if not file_path:
            raise ValueError("File path is required")

        path = Path(file_path)
        logger.info(f"[{self.name}] {Operation} file: {path}")

        try:
            # Create directories if needed
            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)

            # ===== YOUR ATOMIC FILE OPERATION HERE =====
            # Example: Read file
            content = path.read_text(encoding=encoding)
            # Example: Write file
            # content = self.get_input_value("content")
            # path.write_text(content, encoding=encoding)
            # ============================================

            return self.success_result(
                content=content,
                success=True,
                file_path=str(path.absolute()),
            )

        except FileNotFoundError:
            logger.error(f"[{self.name}] File not found: {path}")
            self.status = NodeStatus.ERROR
            raise
        except Exception as e:
            logger.error(f"[{self.name}] File operation failed: {e}")
            self.status = NodeStatus.ERROR
            raise
```

---

## Template 5: HTTP/API Node

**Use for**: REST API calls, webhooks, external services

```python
"""
{Service} API Node

{Brief description - single atomic API operation.}
"""

from typing import Any, Dict, Optional
from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, NodeStatus, PortType
from casare_rpa.infrastructure.http import UnifiedHttpClient


# HTTP operation properties
URL_PROP = PropertyDef(
    "url",
    PropertyType.STRING,
    required=True,
    label="URL",
    tooltip="Full URL for the API endpoint",
    tab="properties",
)

METHOD_PROP = PropertyDef(
    "method",
    PropertyType.CHOICE,
    default="GET",
    choices=["GET", "POST", "PUT", "PATCH", "DELETE"],
    label="HTTP Method",
    tooltip="HTTP request method",
    tab="properties",
)

HEADERS_PROP = PropertyDef(
    "headers",
    PropertyType.JSON,
    default={},
    label="Headers",
    tooltip="HTTP headers as JSON object",
    tab="properties",
)

TIMEOUT_PROP = PropertyDef(
    "timeout",
    PropertyType.INTEGER,
    default=30000,
    min_value=1000,
    label="Timeout (ms)",
    tooltip="Request timeout in milliseconds",
    tab="advanced",
)


@node_schema(
    URL_PROP,
    METHOD_PROP,
    HEADERS_PROP,
    TIMEOUT_PROP,
)
@executable_node
class Http{Operation}Node(BaseNode):
    """
    {One-line description of HTTP operation}.

    Config (via @node_schema):
        url: API endpoint URL (required)
        method: HTTP method (default: GET)
        headers: HTTP headers as JSON (default: {})
        timeout: Request timeout in ms (default: 30000)

    Inputs:
        url: URL (overrides config)
        body: Request body data

    Outputs:
        response: Response body (JSON or text)
        status_code: HTTP status code
        headers: Response headers
    """

    # @category: http
    # @requires: UnifiedHttpClient
    # @ports: url, body -> response, status_code, headers

    NODE_NAME = "HTTP {Operation}"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "HTTP {Operation}",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "Http{Operation}Node"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("url", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port("body", PortType.INPUT, DataType.ANY, required=False)
        self.add_output_port("response", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("status_code", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("headers", PortType.OUTPUT, DataType.ANY)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the HTTP operation."""
        url = self.get_parameter("url", context)
        method = self.get_parameter("method", context)
        headers = self.get_parameter("headers", context) or {}
        timeout = self.get_parameter("timeout", context) / 1000  # Convert to seconds
        body = self.get_input_value("body")

        if not url:
            raise ValueError("URL is required")

        logger.info(f"[{self.name}] {method} {url}")

        try:
            async with UnifiedHttpClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body if body else None,
                    timeout=timeout,
                )

                # Try to parse as JSON, fallback to text
                try:
                    response_data = await response.json()
                except Exception:
                    response_data = await response.text()

                status = response.status_code
                resp_headers = dict(response.headers)

            logger.info(f"[{self.name}] Response status: {status}")
            return self.success_result(
                response=response_data,
                status_code=status,
                headers=resp_headers,
            )

        except Exception as e:
            logger.error(f"[{self.name}] HTTP request failed: {e}")
            self.status = NodeStatus.ERROR
            raise
```

---

## Template 6: Google Service Node

**Use for**: Gmail, Sheets, Calendar, Drive operations

```python
"""
Google {Service} {Operation} Node

{Brief description - single atomic Google service operation.}
"""

from typing import Any, Dict, Optional
from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, NodeStatus, PortType


# Google service properties
CREDENTIAL_NAME_PROP = PropertyDef(
    "credential_name",
    PropertyType.STRING,
    default="",
    label="Credential Name",
    tooltip="Name of stored Google credential (leave empty for default)",
    tab="connection",
)

SPREADSHEET_ID_PROP = PropertyDef(
    "spreadsheet_id",
    PropertyType.STRING,
    required=True,
    label="Spreadsheet ID",
    tooltip="Google Sheets spreadsheet ID from URL",
    tab="properties",
)

RANGE_PROP = PropertyDef(
    "range",
    PropertyType.STRING,
    default="Sheet1!A1",
    label="Range",
    tooltip="Cell range in A1 notation (e.g., Sheet1!A1:D10)",
    tab="properties",
)


@node_schema(
    CREDENTIAL_NAME_PROP,
    SPREADSHEET_ID_PROP,
    RANGE_PROP,
)
@executable_node
class Google{Service}{Operation}Node(BaseNode):
    """
    {One-line description of Google operation}.

    Config (via @node_schema):
        credential_name: Stored credential name (optional)
        spreadsheet_id: Google Sheets ID (required)
        range: Cell range in A1 notation

    Inputs:
        spreadsheet_id: Spreadsheet ID (overrides config)
        data: Data to write (for write operations)

    Outputs:
        data: Retrieved data (for read operations)
        success: Whether operation succeeded
    """

    # @category: google
    # @requires: google-api-python-client
    # @ports: spreadsheet_id, data -> data, success

    NODE_NAME = "Google {Service} {Operation}"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Google {Service} {Operation}",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "Google{Service}{Operation}Node"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("spreadsheet_id", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port("data", PortType.INPUT, DataType.ANY, required=False)
        self.add_output_port("data", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the Google service operation."""
        credential_name = self.get_parameter("credential_name", context)
        spreadsheet_id = self.get_parameter("spreadsheet_id", context)
        range_str = self.get_parameter("range", context)

        if not spreadsheet_id:
            raise ValueError("Spreadsheet ID is required")

        logger.info(f"[{self.name}] Accessing Google {Service}: {spreadsheet_id}")

        try:
            # Get Google credentials from credential store
            from casare_rpa.infrastructure.credentials import get_credential
            creds = get_credential(credential_name or "google_default")

            # ===== YOUR ATOMIC GOOGLE OPERATION HERE =====
            # Example: Read from Sheets
            # service = build("sheets", "v4", credentials=creds)
            # result = service.spreadsheets().values().get(
            #     spreadsheetId=spreadsheet_id,
            #     range=range_str
            # ).execute()
            # data = result.get("values", [])
            data = []
            # =============================================

            return self.success_result(data=data, success=True)

        except Exception as e:
            logger.error(f"[{self.name}] Google operation failed: {e}")
            self.status = NodeStatus.ERROR
            raise
```

---

## Template 7: System/Dialog Node

**Use for**: Message boxes, tooltips, OS operations

```python
"""
System {Operation} Node

{Brief description - single atomic system operation.}
"""

from typing import Any, Dict, Optional
from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, NodeStatus, PortType


# System/Dialog properties
MESSAGE_PROP = PropertyDef(
    "message",
    PropertyType.TEXT,
    default="",
    label="Message",
    tooltip="Message to display",
    tab="properties",
)

TITLE_PROP = PropertyDef(
    "title",
    PropertyType.STRING,
    default="CasareRPA",
    label="Title",
    tooltip="Dialog title",
    tab="properties",
)

ICON_PROP = PropertyDef(
    "icon",
    PropertyType.CHOICE,
    default="info",
    choices=["info", "warning", "error", "success", "question"],
    label="Icon",
    tooltip="Icon to display",
    tab="properties",
)

DURATION_PROP = PropertyDef(
    "duration",
    PropertyType.INTEGER,
    default=3000,
    min_value=500,
    label="Duration (ms)",
    tooltip="Display duration in milliseconds",
    tab="properties",
)


@node_schema(
    MESSAGE_PROP,
    TITLE_PROP,
    ICON_PROP,
    DURATION_PROP,
)
@executable_node
class {Operation}Node(BaseNode):
    """
    {One-line description of system operation}.

    Config (via @node_schema):
        message: Message to display
        title: Dialog title (default: CasareRPA)
        icon: Icon type (default: info)
        duration: Display duration in ms (default: 3000)

    Inputs:
        message: Message (overrides config)

    Outputs:
        success: Whether operation succeeded
        user_response: User's response (for dialogs with input)
    """

    # @category: system
    # @requires: PySide6
    # @ports: message -> success, user_response

    NODE_NAME = "{Operation}"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "{Operation}",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "{Operation}Node"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("message", PortType.INPUT, DataType.STRING, required=False)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("user_response", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the system operation."""
        message = self.get_parameter("message", context)
        title = self.get_parameter("title", context)
        icon = self.get_parameter("icon", context)
        duration = self.get_parameter("duration", context)

        if not message:
            raise ValueError("Message is required")

        logger.info(f"[{self.name}] Displaying: {message[:50]}...")

        try:
            # ===== YOUR ATOMIC SYSTEM OPERATION HERE =====
            # Example: Show tooltip
            from PySide6.QtWidgets import QToolTip
            from PySide6.QtCore import QPoint
            # QToolTip.showText(QPoint(100, 100), message)

            # Example: Message box
            # from PySide6.QtWidgets import QMessageBox
            # QMessageBox.information(None, title, message)
            # =============================================

            return self.success_result(success=True, user_response="")

        except Exception as e:
            logger.error(f"[{self.name}] System operation failed: {e}")
            self.status = NodeStatus.ERROR
            raise
```

---

## Template 8: String Operation Node

**Use for**: String manipulation, parsing, formatting

```python
"""
String {Operation} Node

{Brief description - single atomic string operation.}
"""

from typing import Any, Dict, Optional
from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, NodeStatus, PortType


# String operation properties
CASE_SENSITIVE_PROP = PropertyDef(
    "case_sensitive",
    PropertyType.BOOLEAN,
    default=True,
    label="Case Sensitive",
    tooltip="Whether operation is case-sensitive",
    tab="properties",
)

PATTERN_PROP = PropertyDef(
    "pattern",
    PropertyType.STRING,
    default="",
    label="Pattern",
    tooltip="Search pattern or regex",
    tab="properties",
)


@node_schema(CASE_SENSITIVE_PROP, PATTERN_PROP)
@executable_node
class String{Operation}Node(BaseNode):
    """
    {One-line description of string operation}.

    Config (via @node_schema):
        case_sensitive: Case-sensitive operation (default: True)
        pattern: Search pattern or regex

    Inputs:
        text: Input string to process

    Outputs:
        result: Processed string result
        success: Whether operation succeeded
    """

    # @category: string
    # @requires: none
    # @ports: text -> result, success

    NODE_NAME = "String {Operation}"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "String {Operation}",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "String{Operation}Node"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("text", PortType.INPUT, DataType.STRING)
        self.add_output_port("result", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the string operation."""
        text = self.get_input_value("text")
        case_sensitive = self.get_parameter("case_sensitive", context)
        pattern = self.get_parameter("pattern", context)

        if text is None:
            raise ValueError("Input text is required")

        logger.debug(f"[{self.name}] Processing string of length {len(text)}")

        try:
            # ===== YOUR ATOMIC STRING OPERATION HERE =====
            result = text.upper()  # Example: uppercase
            # =============================================

            return self.success_result(result=result, success=True)

        except Exception as e:
            logger.error(f"[{self.name}] String operation failed: {e}")
            self.status = NodeStatus.ERROR
            raise
```

---

## Template 9: List Operation Node

**Use for**: List manipulation, filtering, sorting

```python
"""
List {Operation} Node

{Brief description - single atomic list operation.}
"""

from typing import Any, Dict, List as ListType, Optional
from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, NodeStatus, PortType


# List operation properties
INDEX_PROP = PropertyDef(
    "index",
    PropertyType.INTEGER,
    default=0,
    label="Index",
    tooltip="Index position (0-based)",
    tab="properties",
)

REVERSE_PROP = PropertyDef(
    "reverse",
    PropertyType.BOOLEAN,
    default=False,
    label="Reverse",
    tooltip="Reverse the operation",
    tab="properties",
)


@node_schema(INDEX_PROP, REVERSE_PROP)
@executable_node
class List{Operation}Node(BaseNode):
    """
    {One-line description of list operation}.

    Config (via @node_schema):
        index: Index position for operation (default: 0)
        reverse: Reverse the operation (default: False)

    Inputs:
        list: Input list to process
        item: Item for add/insert operations

    Outputs:
        result: Processed list or extracted item
        count: Number of items in result
    """

    # @category: list
    # @requires: none
    # @ports: list, item -> result, count

    NODE_NAME = "List {Operation}"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "List {Operation}",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "List{Operation}Node"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("list", PortType.INPUT, DataType.LIST)
        self.add_input_port("item", PortType.INPUT, DataType.ANY, required=False)
        self.add_output_port("result", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the list operation."""
        input_list = self.get_input_value("list")
        item = self.get_input_value("item")
        index = self.get_parameter("index", context)
        reverse = self.get_parameter("reverse", context)

        if input_list is None:
            input_list = []

        logger.debug(f"[{self.name}] Processing list of {len(input_list)} items")

        try:
            # ===== YOUR ATOMIC LIST OPERATION HERE =====
            result = sorted(input_list, reverse=reverse)  # Example: sort
            # =============================================

            count = len(result) if isinstance(result, list) else 1
            return self.success_result(result=result, count=count)

        except Exception as e:
            logger.error(f"[{self.name}] List operation failed: {e}")
            self.status = NodeStatus.ERROR
            raise
```

---

## Template 10: Variable Node

**Use for**: Getting/setting workflow variables

```python
"""
{Operation} Variable Node

{Brief description - single atomic variable operation.}
"""

from typing import Any, Dict, Optional
from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, NodeStatus, PortType


# Variable operation properties
VARIABLE_NAME_PROP = PropertyDef(
    "variable_name",
    PropertyType.STRING,
    required=True,
    label="Variable Name",
    tooltip="Name of the workflow variable",
    tab="properties",
)

DEFAULT_VALUE_PROP = PropertyDef(
    "default_value",
    PropertyType.STRING,
    default="",
    label="Default Value",
    tooltip="Default value if variable not found",
    tab="properties",
)

VARIABLE_TYPE_PROP = PropertyDef(
    "variable_type",
    PropertyType.CHOICE,
    default="String",
    choices=["String", "Integer", "Float", "Boolean", "List", "Dict"],
    label="Variable Type",
    tooltip="Type to cast the value to",
    tab="properties",
)


@node_schema(
    VARIABLE_NAME_PROP,
    DEFAULT_VALUE_PROP,
    VARIABLE_TYPE_PROP,
)
@executable_node
class {Operation}VariableNode(BaseNode):
    """
    {One-line description of variable operation}.

    Config (via @node_schema):
        variable_name: Name of variable (required)
        default_value: Default if not found
        variable_type: Type to cast to (default: String)

    Inputs:
        value: Value to set (for set operations)
        variable_name: Name (overrides config)

    Outputs:
        value: The variable value
    """

    # @category: variable
    # @requires: none
    # @ports: value, variable_name -> value

    NODE_NAME = "{Operation} Variable"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "{Operation} Variable",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "{Operation}VariableNode"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("value", PortType.INPUT, DataType.ANY, required=False)
        self.add_input_port("variable_name", PortType.INPUT, DataType.STRING, required=False)
        self.add_output_port("value", PortType.OUTPUT, DataType.ANY)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the variable operation."""
        var_name = self.get_parameter("variable_name", context)
        default = self.get_parameter("default_value", context)
        var_type = self.get_parameter("variable_type", context)

        if not var_name:
            raise ValueError("Variable name is required")

        logger.debug(f"[{self.name}] {Operation} variable: {var_name}")

        try:
            # ===== YOUR ATOMIC VARIABLE OPERATION HERE =====
            # Get operation
            variables = getattr(context, "variables", {})
            value = variables.get(var_name, default)

            # Set operation
            # value = self.get_input_value("value")
            # context.variables[var_name] = value
            # ===============================================

            # Cast to type
            value = self._cast_value(value, var_type)

            return self.success_result(value=value)

        except Exception as e:
            logger.error(f"[{self.name}] Variable operation failed: {e}")
            self.status = NodeStatus.ERROR
            raise

    def _cast_value(self, value: Any, var_type: str) -> Any:
        """Cast value to specified type."""
        if value is None:
            return None
        if var_type == "Integer":
            return int(value)
        elif var_type == "Float":
            return float(value)
        elif var_type == "Boolean":
            return bool(value)
        elif var_type == "List":
            return list(value) if not isinstance(value, list) else value
        elif var_type == "Dict":
            return dict(value) if not isinstance(value, dict) else value
        return str(value)
```

---

## Visual Node Template (All Categories)

```python
"""
Visual node for {Category}{Operation}Node.
"""

from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


class Visual{Category}{Operation}Node(VisualNode):
    """Visual representation of {Category}{Operation}Node."""

    __identifier__ = "casare_rpa.{category}"
    NODE_NAME = "{Category} {Operation}"
    NODE_CATEGORY = "{category}"
    # CASARE_NODE_CLASS auto-derived from class name

    def __init__(self) -> None:
        super().__init__()
        # Widgets are auto-generated by @node_schema decorator
        # Only add custom widgets here if absolutely necessary
```

---

## PropertyDef Quick Reference

| Type | Use Case | Example Value |
|------|----------|---------------|
| STRING | Single-line text | "https://example.com" |
| TEXT | Multi-line text | "Line 1\nLine 2" |
| INTEGER | Whole numbers | 30000 |
| FLOAT | Decimal numbers | 5.0 |
| BOOLEAN | True/False | True |
| CHOICE | Dropdown selection | "GET" from ["GET", "POST"] |
| JSON | Structured data | {"key": "value"} |
| FILE_PATH | File picker | "C:/data/file.txt" |
| DIRECTORY_PATH | Folder picker | "C:/data/" |
| CODE | Code editor | "x = 1 + 2" |
| SELECTOR | CSS/XPath | "#submit-btn" |

---

## Registration Checklist

After creating your node, complete ALL steps:

### Logic Node Registration
1. [ ] Create in `src/casare_rpa/nodes/{category}/`
2. [ ] Export from `src/casare_rpa/nodes/{category}/__init__.py`
3. [ ] Add to `_NODE_REGISTRY` in `src/casare_rpa/nodes/__init__.py`
4. [ ] Add to `NODE_TYPE_MAP` in `src/casare_rpa/utils/workflow/workflow_loader.py`

### Visual Node Registration
5. [ ] Create in `src/casare_rpa/presentation/canvas/visual_nodes/{category}/`
6. [ ] Export from `visual_nodes/{category}/__init__.py`
7. [ ] Export from `visual_nodes/__init__.py` (add to `__all__`)

### Documentation & Testing
8. [ ] Write tests in `tests/nodes/{category}/test_*.py`
9. [ ] Update `src/casare_rpa/nodes/_index.md` with node documentation

---

## Common PropertyDef Constants

Reuse these constants from existing modules:

### Browser Constants
```python
from casare_rpa.nodes.browser.property_constants import (
    BROWSER_SELECTOR,
    BROWSER_TIMEOUT,
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_WAIT_UNTIL,
)
```

### Desktop Constants
```python
from casare_rpa.nodes.desktop_nodes.properties import (
    SELECTOR_PROP,
    TIMEOUT_PROP,
    TIMEOUT_LONG_PROP,
    THROW_ON_NOT_FOUND_PROP,
    SIMULATE_PROP,
    KEEP_OPEN_PROP,
)
```

### Common Patterns
```python
# Variable name for storing results
VARIABLE_NAME_PROP = PropertyDef(
    "variable_name",
    PropertyType.STRING,
    default="",
    label="Store In Variable",
    tooltip="Variable name to store result",
    tab="advanced",
)

# Retry configuration
RETRY_COUNT_PROP = PropertyDef(
    "retry_count",
    PropertyType.INTEGER,
    default=0,
    min_value=0,
    label="Retry Count",
    tooltip="Number of retries on failure",
    tab="advanced",
)
```
