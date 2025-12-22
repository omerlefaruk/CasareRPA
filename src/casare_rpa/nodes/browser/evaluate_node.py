"""
Browser Evaluate Node - Execute JavaScript code in the browser page context.

Provides functionality to execute arbitrary JavaScript code via Playwright's
page.evaluate() and return the result. Supports passing arguments to the
script and optional JSON parsing of results.

All nodes extend BrowserBaseNode for consistent patterns:
- Page access from context
- Retry logic
- Screenshot on failure
- Error handling

Example Usage:
    # Simple script returning a value
    script = "document.title"
    # Returns: "My Page Title"

    # Script with argument
    script = "(selector) => document.querySelector(selector)?.innerText"
    arg = "#header"
    # Returns: "Header Text"

    # Complex extraction with argument object
    script = '''
    (config) => {
        const cards = document.querySelectorAll(config.selector);
        return Array.from(cards).map(card => ({
            name: card.querySelector(config.nameSelector)?.innerText?.trim(),
            price: card.querySelector(config.priceSelector)?.innerText?.trim()
        }));
    }
    '''
    arg = {
        "selector": "[class*='productCard']",
        "nameSelector": ".title",
        "priceSelector": ".price"
    }
    # Returns: [{"name": "Product 1", "price": "$10"}, ...]
"""

import json
from typing import Any

from loguru import logger

from casare_rpa.config import DEFAULT_NODE_TIMEOUT
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
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_SCREENSHOT_PATH,
    BROWSER_TIMEOUT,
)
from casare_rpa.utils import safe_int
from casare_rpa.utils.resilience import retry_operation


@properties(
    PropertyDef(
        "script",
        PropertyType.CODE,
        default="",
        label="JavaScript Code",
        tooltip="JavaScript code to execute in browser context. Can be an expression or arrow function.",
        placeholder="document.title or (arg) => { return arg.value; }",
        essential=True,
    ),
    PropertyDef(
        "wait_for_selector",
        PropertyType.SELECTOR,
        default="",
        label="Wait for Selector",
        tooltip="Optional: Wait for this selector to be present before executing script",
        placeholder="#content, .loaded",
        tab="advanced",
    ),
    PropertyDef(
        "return_json",
        PropertyType.BOOLEAN,
        default=True,
        label="Parse as JSON",
        tooltip="Attempt to parse the result as JSON if it's a string",
    ),
    PropertyDef(
        "store_variable",
        PropertyType.STRING,
        default="",
        label="Store in Variable",
        tooltip="Variable name to store the result in context (optional)",
        placeholder="extracted_data",
    ),
    BROWSER_TIMEOUT,
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_SCREENSHOT_PATH,
)
@node(category="browser")
class BrowserEvaluateNode(BrowserBaseNode):
    """
    Browser Evaluate Node - execute JavaScript code in browser page context.

    Executes arbitrary JavaScript using Playwright's page.evaluate() and
    returns the result. Supports passing arguments and optional JSON parsing.

    Config (via @properties):
        script: JavaScript code to execute
        wait_for_selector: Optional selector to wait for before execution
        return_json: Whether to parse string results as JSON
        store_variable: Variable name to store result in context
        timeout: Timeout in milliseconds
        retry_count: Retry attempts
        retry_interval: Delay between retries
        screenshot_on_fail: Take screenshot on failure
        screenshot_path: Path for screenshot

    Inputs:
        page: Browser page instance
        script: JavaScript code override (takes precedence over property)
        arg: Argument to pass to script (available as first param in JS)

    Outputs:
        result: The value returned by the JavaScript code
        success: Whether execution succeeded
        error: Error message if failed (empty on success)
    """

    # @category: browser
    # @requires: none
    # @ports: page, script, arg -> result, success, error

    def __init__(
        self,
        node_id: str,
        name: str = "Browser Evaluate",
        **kwargs: Any,
    ) -> None:
        """Initialize browser evaluate node."""
        config = kwargs.get("config", {})
        super().__init__(node_id, config, name=name)
        self.node_type = "BrowserEvaluateNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_page_input_port()
        self.add_input_port("script", DataType.STRING, required=False)
        self.add_input_port("arg", DataType.ANY, required=False)
        self.add_output_port("result", DataType.ANY)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute JavaScript code in browser page context.

        Args:
            context: Execution context with page and variables

        Returns:
            ExecutionResult with result data or error
        """
        self.status = NodeStatus.RUNNING

        try:
            page = self.get_page(context)

            # Get script from input port or property (input takes precedence)
            script = self.get_input_value("script")
            if not script:
                script = self.get_parameter("script", "")

            # Resolve variables in script
            if script:
                script = context.resolve_value(script)
            if not script or not script.strip():
                self.set_output_value("success", False)
                self.set_output_value("error", "Script is required")
                self.set_output_value("result", None)
                return self.error_result("Script is required")

            # Get argument (can be any type)
            arg = self.get_input_value("arg")

            # Get other parameters
            wait_selector = self.get_parameter("wait_for_selector", "")
            return_json = self.get_parameter("return_json", True)
            store_variable = self.get_parameter("store_variable", "")
            timeout = safe_int(
                self.get_parameter("timeout", DEFAULT_NODE_TIMEOUT * 1000),
                DEFAULT_NODE_TIMEOUT * 1000,
            )

            logger.info("Executing JavaScript in browser context")
            logger.debug(f"Script: {script[:100]}{'...' if len(script) > 100 else ''}")

            async def perform_evaluate() -> Any:
                """Execute the JavaScript evaluation."""
                # Wait for optional selector before execution
                if wait_selector and wait_selector.strip():
                    resolved_selector = context.resolve_value(wait_selector)
                    logger.debug(f"Waiting for selector: {resolved_selector}")
                    await page.wait_for_selector(
                        resolved_selector, timeout=timeout, state="attached"
                    )

                # Execute JavaScript with or without argument
                if arg is not None:
                    result = await page.evaluate(script, arg)
                else:
                    result = await page.evaluate(script)

                return result

            # Execute with retry support
            operation_result = await retry_operation(
                perform_evaluate,
                max_attempts=self.get_parameter("retry_count", 0) + 1,
                delay_seconds=self.get_parameter("retry_interval", 1000) / 1000,
                operation_name="evaluate JavaScript",
            )

            if operation_result.success:
                result = operation_result.value

                # Attempt JSON parsing if enabled and result is a string
                if return_json and isinstance(result, str):
                    result = self._try_parse_json(result)

                # Store in context variable if requested
                if store_variable and store_variable.strip():
                    context.set_variable(store_variable, result)
                    logger.debug(f"Stored result in variable: {store_variable}")

                # Set output port values
                self.set_output_value("result", result)
                self.set_output_value("success", True)
                self.set_output_value("error", "")

                logger.info(
                    f"JavaScript execution completed "
                    f"(result type: {type(result).__name__}, "
                    f"attempts: {operation_result.attempts})"
                )

                return self.success_result(
                    {
                        "result": result,
                        "result_type": type(result).__name__,
                        "variable": store_variable if store_variable else None,
                        "attempts": operation_result.attempts,
                    }
                )

            # Retry failed
            await self.screenshot_on_failure(page, "evaluate_fail")
            error_msg = str(operation_result.last_error or "JavaScript execution failed")
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.set_output_value("result", None)
            raise operation_result.last_error or RuntimeError(error_msg)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"JavaScript execution failed: {error_msg}")
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.set_output_value("result", None)
            return self.error_result(e)

    def _try_parse_json(self, value: str) -> Any:
        """
        Attempt to parse a string as JSON.

        Args:
            value: String value to parse

        Returns:
            Parsed JSON object/array, or original string if parsing fails
        """
        if not value or not value.strip():
            return value

        # Check if it looks like JSON
        stripped = value.strip()
        if not (
            (stripped.startswith("{") and stripped.endswith("}"))
            or (stripped.startswith("[") and stripped.endswith("]"))
        ):
            return value

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            logger.debug("Result looks like JSON but failed to parse, returning as string")
            return value

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        self.get_parameter("script", "")
        # Script can be empty if provided via input port
        # No strict validation needed here
        return True, ""
