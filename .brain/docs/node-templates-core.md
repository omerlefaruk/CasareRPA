# Core Node Templates

> Browser, Desktop, and Control Flow node templates for CasareRPA.
> **Category**: Core automation templates

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
        self.add_output_port("true", PortType.EXEC_OUTPUT, DataType.EXEC)
        self.add_output_port("false", PortType.EXEC_OUTPUT, DataType.EXEC)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the control flow operation."""
        condition = self.get_input_value("condition")
        if condition is None:
            expression = self.get_parameter("expression", context)
            if expression:
                condition = self._evaluate_expression(expression, context)
            else:
                condition = False

        logger.debug(f"[{self.name}] Condition evaluated to: {condition}")

        if condition:
            return {"success": True, "data": {}, "next_nodes": ["true"]}
        else:
            return {"success": True, "data": {}, "next_nodes": ["false"]}

    def _evaluate_expression(self, expression: str, context: Any) -> bool:
        """Evaluate boolean expression with context variables."""
        variables = getattr(context, "variables", {})
        for var_name, var_value in variables.items():
            expression = expression.replace(f"{{{{{var_name}}}}}", str(var_value))

        try:
            return bool(eval(expression))
        except Exception as e:
            logger.warning(f"[{self.name}] Expression eval failed: {e}")
            return False
```

## PropertyDef Quick Reference

| Type | Use Case | Example Value |
|------|----------|---------------|
| STRING | Single-line text | "https://example.com" |
| INTEGER | Whole numbers | 30000 |
| FLOAT | Decimal numbers | 5.0 |
| BOOLEAN | True/False | True |
| CHOICE | Dropdown selection | "GET" from ["GET", "POST"] |
| SELECTOR | CSS/XPath | "#submit-btn" |

## Common PropertyDef Constants

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

---

**See also**: `node-templates-data.md` | `node-templates-services.md` | `node-checklist.md`
