"""
Desktop Node Template

For nodes that use uiautomation for Windows desktop automation.
"""

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType


@properties(
    PropertyDef("window_name", PropertyType.STRING, required=True),
    PropertyDef("timeout", PropertyType.INTEGER, default=5000),
)
@node(category="desktop")
class DesktopNodeTemplate(BaseNode):
    """
    Template for desktop automation nodes.

    Inputs:
        window_name (DataType.STRING): Window title to find

    Outputs:
        found (DataType.BOOLEAN): Whether window was found
        handle (DataType.INTEGER): Window handle
    """

    def __init__(self):
        super().__init__(
            id="desktop_template",
            name="Desktop Template",
            category="desktop",
        )
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        self.add_input_port("window_name", DataType.STRING)
        self.add_input_port("timeout", DataType.INTEGER)

        self.add_output_port("found", DataType.BOOLEAN)
        self.add_output_port("handle", DataType.INTEGER)

    async def execute(self, context) -> dict:
        """Execute desktop automation."""
        try:
            window_name = self.get_parameter("window_name")
            timeout = self.get_parameter("timeout", 5000)

            # Import uiautomation for desktop automation
            from uiautomation import Control, FindWindow

            logger.info(f"Finding window: {window_name}")

            # Find window by name
            window = Control(ControlType="Window", Name=window_name)
            found = window.Exists(timeout / 1000)  # Convert to seconds

            if found:
                handle = window.NativeWindowHandle
                logger.info(f"Window found with handle: {handle}")
                self.set_output_value("found", True)
                self.set_output_value("handle", handle)
            else:
                logger.warning(f"Window not found: {window_name}")
                self.set_output_value("found", False)
                self.set_output_value("handle", 0)

            return {"success": True, "next_nodes": ["exec_out"]}

        except Exception as exc:
            logger.error(f"Desktop automation failed: {exc}")
            self.set_output_value("found", False)
            self.set_output_value("handle", 0)
            return {"success": False, "error": str(exc), "next_nodes": ["exec_out"]}
