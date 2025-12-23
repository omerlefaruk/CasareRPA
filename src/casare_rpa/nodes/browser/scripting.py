"""
Browser scripting nodes.

This module provides nodes for executing custom scripts within the browser context.
"""

from typing import Any

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.browser.browser_base import BrowserBaseNode
from casare_rpa.nodes.browser.property_constants import (
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_TIMEOUT,
)
from casare_rpa.utils import safe_int
from casare_rpa.utils.resilience import retry_operation


@properties(
    PropertyDef(
        "script",
        PropertyType.CODE,
        default="",
        required=True,
        label="Python Script",
        tooltip="Python code to execute. 'page' is available as a local variable.",
        placeholder="# Example:\n# page.click('#my-id')",
        essential=True,
    ),
    BROWSER_TIMEOUT,
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
)
@node(category="browser")
class BrowserRunScriptNode(BrowserBaseNode):
    """
    Execute custom Python script with browser access.

    Allows running arbitrary Python code with access to the Playwright 'page' object.
    Useful for complex interactions, frame handling, or unsupported actions.

    Config (via @properties):
        script: Python code to execute
        timeout: Execution timeout in milliseconds
        retry_count: Number of retries on failure
        retry_interval: Delay between retries in ms

    Inputs:
        page: Browser page instance
        script: Script override (optional)

    Outputs:
        page: Browser page instance (passthrough)
        result: Return value of the script (if any)
    """

    # @category: browser
    # @requires: none
    # @ports: page, script -> page, result

    def __init__(
        self,
        node_id: str,
        name: str = "Browser Script",
        **kwargs,
    ) -> None:
        """Initialize browser script node."""
        super().__init__(node_id, name=name, **kwargs)
        self.node_type = "BrowserRunScriptNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_page_passthrough_ports()
        self.add_input_port("script", DataType.STRING)
        self.add_output_port("result", DataType.ANY)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute browser script."""
        self.status = NodeStatus.RUNNING

        try:
            page = self.get_page(context)

            # Get parameters (handles both port and config)
            script = self.get_parameter("script", "")

            if not script:
                raise ValueError("Script is required")

            safe_int(
                self.get_parameter("timeout", 30000),
                30000,
            )

            logger.info("Executing custom browser script")

            async def perform_script() -> Any:
                # Prepare execution environment
                local_scope = {
                    "page": page,
                    "logger": logger,
                    "context": context,
                    "result": None,
                }

                # Execute script
                # We wrap it in an async function definition to allow 'await' usage if the user writes async code
                # But 'exec' doesn't support top-level await easily without wrapping.
                # However, since we are inside an async function, we can't easily eval async code without parsed AST.
                # Simplified approach: Use exec, user must use 'await' if needed? No, exec doesn't allow 'await' outside async def.

                # To allow 'await' in user script, we wrap it in an async function and call it.
                wrapped_script = f"""
async def _user_script(page, logger, context):
    result = None
    try:
{self._indent_script(script)}
    except Exception as e:
        raise e
    return locals().get('result', None)
"""
                exec(wrapped_script, local_scope)
                _user_script = local_scope["_user_script"]

                return await _user_script(page, logger, context)

            result_value = await retry_operation(
                perform_script,
                max_attempts=safe_int(self.get_parameter("retry_count", 0), 0) + 1,
                delay_seconds=safe_int(self.get_parameter("retry_interval", 1000), 1000) / 1000,
                operation_name="custom browser script",
            )

            self.set_output_value("page", page)
            self.set_output_value("result", result_value)

            return self.success_result(
                {"executed": True, "result_type": type(result_value).__name__}
            )

        except Exception as e:
            return self.error_result(e)

    def _indent_script(self, script: str, indent: str = "        ") -> str:
        """Indent script lines for wrapping."""
        lines = script.split("\n")
        return "\n".join(f"{indent}{line}" for line in lines)
