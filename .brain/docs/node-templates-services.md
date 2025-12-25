# Service/API Node Templates

> HTTP, Google, System, and Dialog node templates for CasareRPA.
> **Category**: External service integration templates

## Modern Node Standard (2025)

**All nodes MUST follow Schema-Driven Logic:**

```python
@properties(
    PropertyDef("url", PropertyType.STRING, required=True),
    PropertyDef("timeout", PropertyType.INTEGER, default=30000),
)
@node(category="http")
class MyNode(BaseNode):
    async def execute(self, context):
        url = self.get_parameter("url")              # required
        timeout = self.get_parameter("timeout", 30000)  # optional

        # LEGACY (DON'T USE): self.config.get("timeout", 30000)
```

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
            data = []
            # =============================================

            return self.success_result(data=data, success=True)

        except Exception as e:
            logger.error(f"[{self.name}] Google operation failed: {e}")
            self.status = NodeStatus.ERROR
            raise
```

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
            # from PySide6.QtWidgets import QToolTip
            # from PySide6.QtCore import QPoint
            # QToolTip.showText(QPoint(100, 100), message)
            # =============================================

            return self.success_result(success=True, user_response="")

        except Exception as e:
            logger.error(f"[{self.name}] System operation failed: {e}")
            self.status = NodeStatus.ERROR
            raise
```

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

## PropertyDef Quick Reference

| Type | Use Case | Example Value |
|------|----------|---------------|
| STRING | Single-line text | "https://api.example.com" |
| TEXT | Multi-line text | JSON body content |
| INTEGER | Whole numbers | 30000 |
| BOOLEAN | True/False | True |
| CHOICE | Dropdown selection | "GET" from ["GET", "POST"] |
| JSON | Structured data | {"Authorization": "Bearer xxx"} |

## Common Patterns

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

---

**See also**: `node-templates-core.md` | `node-templates-data.md` | `node-checklist.md`
