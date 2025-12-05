"""
Form Field Node.

Defines a form field for batch filling. Does NOT execute typing -
just accumulates field definitions to be executed by FormFillerNode.

This enables visual workflow building where each field is a node,
but execution happens in a single batch for speed.
"""

from typing import Any, Dict, List

from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.browser.browser_base import BrowserBaseNode


@node_schema(
    PropertyDef(
        "selector",
        PropertyType.SELECTOR,
        default="",
        required=True,
        label="Field Selector",
        tooltip="CSS or XPath selector for the form field",
        placeholder="#email or input[name='email']",
        essential=True,
    ),
    PropertyDef(
        "value",
        PropertyType.STRING,
        default="",
        required=True,
        label="Value",
        tooltip="Value to fill. Use ${var} for variables.",
        placeholder="text or ${variable}",
        essential=True,
    ),
    PropertyDef(
        "field_type",
        PropertyType.CHOICE,
        default="text",
        choices=["text", "select", "checkbox", "radio"],
        label="Field Type",
        tooltip="Type of form field (affects how value is applied)",
    ),
    PropertyDef(
        "clear_first",
        PropertyType.BOOLEAN,
        default=True,
        label="Clear First",
        tooltip="Clear existing value before filling (text inputs only)",
    ),
)
@executable_node
class FormFieldNode(BrowserBaseNode):
    """
    Define a form field for batch filling.

    This node does NOT execute any browser action. It accumulates
    field definitions that are later executed by FormFillerNode.

    Usage:
        FormField → FormField → FormField → FormFiller
        (each FormField adds to the fields array, FormFiller executes all)

    Ports:
        Input:
            - page: Browser page (passthrough)
            - fields_in: Array of previous field definitions (optional)
        Output:
            - page: Browser page (passthrough)
            - fields_out: Array with this field added
            - field: This field's definition only
    """

    NODE_NAME = "Form Field"

    def __init__(self, node_id: str, name: str = "Form Field", **kwargs: Any) -> None:
        """Initialize the form field node."""
        config = kwargs.get("config", {})
        super().__init__(node_id, config, name=name)
        self.node_type = "FormFieldNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Page passthrough
        self.add_page_passthrough_ports()

        # Fields accumulator - input is optional (first node won't have it)
        self.add_input_port("fields_in", DataType.LIST, required=False)

        # Outputs
        self.add_output_port("fields_out", DataType.LIST)
        self.add_output_port("field", DataType.OBJECT)

    async def execute(self, context: ExecutionContext) -> Dict[str, Any]:
        """
        Accumulate field definition without executing.

        Args:
            context: Execution context

        Returns:
            ExecutionResult with accumulated fields
        """
        # Get page for passthrough (don't need it, but pass it along)
        try:
            page = self.get_page(context)
        except Exception:
            page = None  # OK if no page yet, just pass None through

        # Get field properties
        selector = self.get_parameter("selector", "").strip()
        value = self.get_parameter("value", "")
        field_type = self.get_parameter("field_type", "text")
        clear_first = self.get_parameter("clear_first", True)

        # Validate selector - empty selectors cause FormFiller to freeze
        if not selector:
            logger.warning("FormField: Empty selector, skipping field accumulation")
            # Still pass through fields_in so chain doesn't break
            fields_in = self.get_input_value("fields_in") or []
            self.set_output_value("page", page)
            self.set_output_value("fields_out", fields_in)
            self.set_output_value("field", None)
            return self.success_result(
                {
                    "skipped": True,
                    "reason": "empty_selector",
                    "total_fields": len(fields_in),
                }
            )

        # Resolve variable references in value
        resolved_value = context.resolve_value(value) if "${" in str(value) else value

        # Create field definition
        field_def = {
            "selector": selector,
            "value": resolved_value,
            "type": field_type,
            "clear_first": clear_first,
        }

        # Get previous fields (if any)
        fields_in = self.get_input_value("fields_in")
        if fields_in is None:
            fields_in = []
        elif not isinstance(fields_in, list):
            fields_in = [fields_in]

        # Accumulate
        fields_out = fields_in + [field_def]

        logger.debug(
            f"FormField accumulated: {selector} (total fields: {len(fields_out)})"
        )

        # Set outputs
        self.set_output_value("page", page)
        self.set_output_value("fields_out", fields_out)
        self.set_output_value("field", field_def)
        logger.info(f"FormField: set fields_out = {fields_out}")

        return self.success_result(
            {
                "field": field_def,
                "total_fields": len(fields_out),
            }
        )
