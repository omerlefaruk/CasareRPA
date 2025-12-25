"""
Browser alert/dialog handling node.

This module provides node for handling JavaScript dialogs:
- alert() - Simple message dialog
- confirm() - Yes/No confirmation dialog
- prompt() - Text input dialog
- beforeunload() - Navigation confirmation dialog

Uses Playwright's dialog handling with page.on('dialog') event.
"""

import asyncio
from typing import Any

from loguru import logger

from casare_rpa.config import DEFAULT_NODE_TIMEOUT
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.browser.browser_base import BrowserBaseNode
from casare_rpa.nodes.browser.property_constants import BROWSER_TIMEOUT


@properties(
    PropertyDef(
        "action",
        PropertyType.CHOICE,
        default="accept",
        choices=["accept", "dismiss"],
        label="Action",
        tooltip="Action to perform on the dialog",
        essential=True,
    ),
    PropertyDef(
        "prompt_text",
        PropertyType.STRING,
        default="",
        label="Prompt Text",
        placeholder="Text to enter in prompt dialog",
        tooltip="Text to enter when accepting a prompt dialog (ignored for alert/confirm)",
    ),
    BROWSER_TIMEOUT,
)
@node(category="browser")
class BrowserAlertHandleNode(BrowserBaseNode):
    """
    Handle JavaScript dialogs (alerts, confirms, prompts).

    Automatically handles the next JavaScript dialog that appears:
    - **accept**: Click OK/Yes on the dialog
    - **dismiss**: Click Cancel/No on the dialog
    - **prompt_text**: Text to enter for prompt dialogs

    The node waits for a dialog to appear within the timeout period,
    then performs the specified action and returns the dialog message.

    Example:
        # Click a button that triggers an alert
        ClickElementNode(selector="#alert-button")

        # Handle the alert
        BrowserAlertHandleNode(action="accept")

        # For prompt dialogs with text input
        BrowserAlertHandleNode(action="accept", prompt_text="Hello World")
    """

    def __init__(self, node_id: str, config: dict | None = None, **kwargs: Any) -> None:
        """Initialize BrowserAlertHandleNode."""
        super().__init__(node_id, config, **kwargs)

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Optional: can specify a selector to click before waiting for dialog
        self.add_input_port("trigger_selector", DataType.STRING, required=False)

        # Page passthrough
        self.add_page_passthrough_ports(required=False)

        # Outputs
        self.add_output_port("message", DataType.STRING)
        self.add_output_port("dialog_type", DataType.STRING)
        self.add_output_port("action_taken", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute the alert handling logic.

        Args:
            context: Execution context

        Returns:
            Execution result with dialog information
        """
        try:
            page = self.get_page(context)

            # Get parameters
            action = self.get_parameter("action", "accept")
            prompt_text = self.get_parameter("prompt_text", "")
            timeout = self.get_parameter("timeout", DEFAULT_NODE_TIMEOUT * 1000)
            trigger_selector = self.get_input_value("trigger_selector")

            # If trigger selector provided, click it first
            if trigger_selector:
                try:
                    await page.click(trigger_selector, timeout=5000)
                    logger.debug(f"Clicked trigger selector: {trigger_selector}")
                except Exception as e:
                    logger.warning(f"Failed to click trigger selector: {e}")

            # Set up dialog handler
            dialog_result: dict[str, Any] = {
                "message": "",
                "dialog_type": "",
                "action_taken": action,
                "success": False,
            }

            dialog_event = asyncio.create_task(self._wait_for_dialog(page))

            try:
                # Wait for dialog to appear
                dialog = await asyncio.wait_for(dialog_event, timeout=timeout / 1000)

                dialog_result["message"] = dialog.message
                dialog_result["dialog_type"] = dialog.type

                # Perform the action
                if action == "accept":
                    if dialog.type == "prompt" and prompt_text:
                        await dialog.accept(prompt_text)
                        logger.info(f"Accepted prompt dialog with text: {prompt_text}")
                    else:
                        await dialog.accept()
                        logger.info(f"Accepted {dialog.type} dialog")
                else:  # dismiss
                    await dialog.dismiss()
                    logger.info(f"Dismissed {dialog.type} dialog")

                dialog_result["success"] = True

            except TimeoutError:
                logger.warning(f"No dialog appeared within {timeout}ms")
                dialog_result["success"] = False
                dialog_result["message"] = "Timeout: No dialog appeared"

            # Set output values
            self.set_output_value("message", dialog_result["message"])
            self.set_output_value("dialog_type", dialog_result["dialog_type"])
            self.set_output_value("action_taken", dialog_result["action_taken"])
            self.set_output_value("success", dialog_result["success"])

            # Pass page through
            output_page = self.get_input_value("page") or context.get_active_page()
            if output_page:
                self.set_output_value("page", output_page)

            return self.success_result(
                data=dialog_result,
                next_nodes=["exec_out"] if dialog_result["success"] else [],
            )

        except Exception as e:
            logger.error(f"Alert handle failed: {e}")
            self.set_output_value("success", False)
            self.set_output_value("message", str(e))
            return self.error_result(e)

    async def _wait_for_dialog(self, page: Any) -> Any:
        """
        Wait for a dialog to appear.

        Args:
            page: Playwright Page instance

        Returns:
            Dialog object
        """
        future: asyncio.Future[Any] = asyncio.Future()

        def handler(dialog: Any) -> None:
            """Handle dialog event."""
            if not future.done():
                future.set_result(dialog)

        # Register one-time dialog handler
        page.once("dialog", handler)

        return await future
