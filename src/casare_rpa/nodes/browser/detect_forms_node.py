"""
Detect Forms Node.

Detects all forms and form fields on a web page.
Outputs structured data about forms, fields, and their attributes.
"""

from typing import Any, Dict, List

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.infrastructure.browser.form_detector import FormDetector, DetectedForm
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.browser.browser_base import BrowserBaseNode


@properties(
    PropertyDef(
        "container",
        PropertyType.STRING,
        default="body",
        label="Container Selector",
        placeholder="body, #main-content, .form-container",
        tooltip="CSS selector for container to search within (default: entire page)",
    ),
    PropertyDef(
        "include_hidden",
        PropertyType.BOOLEAN,
        default=False,
        label="Include Hidden Fields",
        tooltip="Include hidden input fields in detection results",
    ),
    PropertyDef(
        "output_variable",
        PropertyType.STRING,
        default="",
        label="Output Variable",
        placeholder="detected_forms",
        tooltip="Variable name to store the detected forms (optional)",
    ),
)
@node(category="browser")
class DetectFormsNode(BrowserBaseNode):
    """
    Detect all forms and form fields on a page.

    This node scans the page for form elements and extracts:
    - Form attributes (action, method, id, name)
    - All input fields with their properties
    - Field labels, placeholders, and types
    - Select options
    - Submit button selectors

    Output:
    - forms: List of detected forms with their fields
    - form_count: Number of forms found
    - field_count: Total number of fields found
    """

    # @category: browser
    # @requires: none
    # @ports: none -> forms, form_count, field_count, fields

    NODE_NAME = "Detect Forms"

    def __init__(self, node_id: str, name: str = "Detect Forms", **kwargs: Any) -> None:
        """Initialize the detect forms node."""
        config = kwargs.get("config", {})
        super().__init__(node_id, config, name=name)
        self.node_type = "DetectFormsNode"
        self._detector = FormDetector()

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_page_passthrough_ports()
        self.add_output_port("forms", DataType.LIST)
        self.add_output_port("form_count", DataType.INTEGER)
        self.add_output_port("field_count", DataType.INTEGER)
        self.add_output_port("fields", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> Dict[str, Any]:
        """
        Execute form detection.

        Args:
            context: Execution context with page

        Returns:
            ExecutionResult with detected forms data
        """
        try:
            page = self.get_page(context)
        except Exception as e:
            return self.error_result(f"Failed to get page: {e}")

        container = self.get_parameter("container", "body")
        include_hidden = self.get_parameter("include_hidden", False)
        output_variable = self.get_parameter("output_variable", "")

        try:
            # Detect all forms on the page
            detected_forms = await self._detector.detect_forms(page)

            # Also detect standalone fields in the container
            all_fields = await self._detector.detect_fields(page, container)

            # Convert to serializable dictionaries
            forms_data = self._forms_to_dict(detected_forms, include_hidden)
            fields_data = self._fields_to_dict(all_fields, include_hidden)

            form_count = len(forms_data)
            field_count = sum(len(f.get("fields", [])) for f in forms_data)
            total_fields = len(fields_data)

            # Set output ports
            self.set_output_value("page", page)
            self.set_output_value("forms", forms_data)
            self.set_output_value("form_count", form_count)
            self.set_output_value("field_count", field_count)
            self.set_output_value("fields", fields_data)

            # Store in variable if specified
            if output_variable:
                context.set_variable(
                    output_variable,
                    {
                        "forms": forms_data,
                        "form_count": form_count,
                        "field_count": field_count,
                        "fields": fields_data,
                    },
                )

            logger.info(
                f"Detected {form_count} forms with {field_count} fields, "
                f"{total_fields} total fields in container"
            )

            return self.success_result(
                {
                    "form_count": form_count,
                    "field_count": field_count,
                    "total_fields": total_fields,
                    "forms": forms_data,
                }
            )

        except Exception as e:
            logger.error(f"Form detection failed: {e}")
            await self.screenshot_on_failure(page, "form_detect_error")
            return self.error_result(str(e))

    def _forms_to_dict(
        self, forms: List[DetectedForm], include_hidden: bool
    ) -> List[Dict[str, Any]]:
        """
        Convert DetectedForm objects to serializable dictionaries.

        Args:
            forms: List of DetectedForm objects
            include_hidden: Whether to include hidden fields

        Returns:
            List of form dictionaries
        """
        result = []
        for form in forms:
            fields = form.fields
            if not include_hidden:
                fields = [f for f in fields if f.field_type != "hidden"]

            result.append(
                {
                    "selector": form.selector,
                    "action": form.action,
                    "method": form.method,
                    "name": form.name,
                    "id": form.id,
                    "submit_selector": form.submit_selector,
                    "fields": [self._field_to_dict(f) for f in fields],
                }
            )
        return result

    def _fields_to_dict(self, fields: List, include_hidden: bool) -> List[Dict[str, Any]]:
        """
        Convert FormField objects to serializable dictionaries.

        Args:
            fields: List of FormField objects
            include_hidden: Whether to include hidden fields

        Returns:
            List of field dictionaries
        """
        if not include_hidden:
            fields = [f for f in fields if f.field_type != "hidden"]

        return [self._field_to_dict(f) for f in fields]

    def _field_to_dict(self, field) -> Dict[str, Any]:
        """
        Convert a single FormField to dictionary.

        Args:
            field: FormField object

        Returns:
            Field dictionary
        """
        return {
            "selector": field.selector,
            "type": field.field_type,
            "name": field.name,
            "label": field.label,
            "placeholder": field.placeholder,
            "required": field.required,
            "value": field.value,
            "options": field.options,
            "id": field.id,
            "autocomplete": field.autocomplete,
        }
