"""
Form Auto-Detection Module.

Provides functionality to detect forms and form fields on web pages.
Used by FormFillerNode and DetectFormsNode for intelligent form handling.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from playwright.async_api import Page


@dataclass
class FormField:
    """Represents a detected form field."""

    selector: str
    """CSS/ID selector for the field."""

    field_type: str
    """Field type: text, email, password, select, checkbox, radio, textarea, etc."""

    name: str
    """Field name attribute."""

    label: Optional[str] = None
    """Associated label text (from <label> element)."""

    placeholder: Optional[str] = None
    """Placeholder text attribute."""

    required: bool = False
    """Whether the field is required."""

    value: Optional[str] = None
    """Current field value."""

    options: List[str] = field(default_factory=list)
    """Available options for select/radio/checkbox fields."""

    id: Optional[str] = None
    """Field id attribute."""

    autocomplete: Optional[str] = None
    """Autocomplete attribute hint."""


@dataclass
class DetectedForm:
    """Represents a detected form on the page."""

    selector: str
    """CSS/ID selector for the form."""

    action: Optional[str]
    """Form action URL."""

    method: str
    """Form method (GET/POST)."""

    fields: List[FormField]
    """List of detected fields within the form."""

    submit_selector: Optional[str] = None
    """Selector for the submit button."""

    name: Optional[str] = None
    """Form name attribute."""

    id: Optional[str] = None
    """Form id attribute."""


# JavaScript for detecting forms on the page
FORM_DETECTION_SCRIPT = """() => {
    const forms = Array.from(document.querySelectorAll("form"));

    return forms.map((form, formIndex) => {
        // Build form selector
        let formSelector = "form";
        if (form.id) {
            formSelector = "#" + CSS.escape(form.id);
        } else if (form.name) {
            formSelector = `form[name="${CSS.escape(form.name)}"]`;
        } else {
            formSelector = `form:nth-of-type(${formIndex + 1})`;
        }

        // Detect all form fields
        const inputs = Array.from(form.querySelectorAll("input, select, textarea"));
        const fields = inputs.map(el => {
            // Find associated label
            let label = null;
            if (el.id) {
                const labelEl = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
                label = labelEl?.innerText?.trim() || null;
            }
            if (!label && el.closest("label")) {
                // Get label text excluding input value
                const labelEl = el.closest("label");
                const clone = labelEl.cloneNode(true);
                clone.querySelectorAll("input, select, textarea").forEach(n => n.remove());
                label = clone.innerText?.trim() || null;
            }

            // Build field selector
            let fieldSelector = "";
            if (el.id) {
                fieldSelector = "#" + CSS.escape(el.id);
            } else if (el.name) {
                fieldSelector = `[name="${CSS.escape(el.name)}"]`;
            } else {
                const tagName = el.tagName.toLowerCase();
                const type = el.type || "";
                fieldSelector = type ? `${tagName}[type="${type}"]` : tagName;
            }

            // Get options for select elements
            const options = [];
            if (el.tagName === "SELECT") {
                Array.from(el.options).forEach(opt => {
                    if (opt.value) {
                        options.push(opt.text || opt.value);
                    }
                });
            }

            // Get current value
            let currentValue = null;
            if (el.type === "checkbox" || el.type === "radio") {
                currentValue = el.checked ? "checked" : "";
            } else if (el.tagName === "SELECT") {
                currentValue = el.options[el.selectedIndex]?.text || "";
            } else {
                currentValue = el.value || "";
            }

            return {
                selector: fieldSelector,
                type: el.type || el.tagName.toLowerCase(),
                name: el.name || "",
                label: label,
                placeholder: el.placeholder || null,
                required: el.required || false,
                value: currentValue,
                options: options,
                id: el.id || null,
                autocomplete: el.autocomplete || null
            };
        });

        // Find submit button
        let submitSelector = null;
        const submitBtn = form.querySelector(
            '[type="submit"], button:not([type="button"]):not([type="reset"])'
        );
        if (submitBtn) {
            if (submitBtn.id) {
                submitSelector = "#" + CSS.escape(submitBtn.id);
            } else if (submitBtn.name) {
                submitSelector = `[name="${CSS.escape(submitBtn.name)}"]`;
            } else {
                submitSelector = '[type="submit"], button:not([type="button"])';
            }
        }

        return {
            selector: formSelector,
            action: form.action || null,
            method: (form.method || "GET").toUpperCase(),
            fields: fields,
            submitSelector: submitSelector,
            name: form.name || null,
            id: form.id || null
        };
    });
}"""


# JavaScript for detecting fields in a container (not necessarily in a form)
FIELD_DETECTION_SCRIPT = """(container) => {
    const root = document.querySelector(container) || document.body;
    const elements = Array.from(root.querySelectorAll("input, select, textarea"));

    return elements.map(el => {
        // Find associated label
        let label = null;
        if (el.id) {
            const labelEl = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
            label = labelEl?.innerText?.trim() || null;
        }
        if (!label && el.closest("label")) {
            const labelEl = el.closest("label");
            const clone = labelEl.cloneNode(true);
            clone.querySelectorAll("input, select, textarea").forEach(n => n.remove());
            label = clone.innerText?.trim() || null;
        }

        // Build selector
        let selector = "";
        if (el.id) {
            selector = "#" + CSS.escape(el.id);
        } else if (el.name) {
            selector = `[name="${CSS.escape(el.name)}"]`;
        } else {
            const tagName = el.tagName.toLowerCase();
            const type = el.type || "";
            selector = type ? `${tagName}[type="${type}"]` : tagName;
        }

        // Get options for select elements
        const options = [];
        if (el.tagName === "SELECT") {
            Array.from(el.options).forEach(opt => {
                if (opt.value) {
                    options.push(opt.text || opt.value);
                }
            });
        }

        return {
            selector: selector,
            type: el.type || el.tagName.toLowerCase(),
            name: el.name || "",
            label: label,
            placeholder: el.placeholder || null,
            required: el.required || false,
            options: options,
            id: el.id || null,
            autocomplete: el.autocomplete || null
        };
    });
}"""


class FormDetector:
    """
    Auto-detect forms and fields on a web page.

    Provides methods to:
    - Detect all forms on a page with their fields
    - Detect input fields within a specific container
    - Parse form field metadata (labels, types, options)

    Usage:
        detector = FormDetector()
        forms = await detector.detect_forms(page)

        for form in forms:
            print(f"Form: {form.selector}")
            for field in form.fields:
                print(f"  - {field.name}: {field.field_type} ({field.label})")
    """

    async def detect_forms(self, page: "Page") -> List[DetectedForm]:
        """
        Find all forms on the page.

        Args:
            page: Playwright Page instance

        Returns:
            List of DetectedForm objects with their fields
        """
        try:
            forms_data = await page.evaluate(FORM_DETECTION_SCRIPT)
            forms = [self._parse_form(f) for f in forms_data]
            logger.debug(f"Detected {len(forms)} forms on page")
            return forms
        except Exception as e:
            logger.error(f"Failed to detect forms: {e}")
            return []

    async def detect_fields(
        self, page: "Page", container: str = "body"
    ) -> List[FormField]:
        """
        Detect input fields within a container.

        This method finds all input, select, and textarea elements
        within the specified container, regardless of whether they
        are inside a form element.

        Args:
            page: Playwright Page instance
            container: CSS selector for the container (default: "body")

        Returns:
            List of FormField objects
        """
        try:
            fields_data = await page.evaluate(FIELD_DETECTION_SCRIPT, container)
            fields = [self._parse_field(f) for f in fields_data]
            logger.debug(f"Detected {len(fields)} fields in {container}")
            return fields
        except Exception as e:
            logger.error(f"Failed to detect fields in {container}: {e}")
            return []

    async def get_form_by_selector(
        self, page: "Page", selector: str
    ) -> Optional[DetectedForm]:
        """
        Get a specific form by its selector.

        Args:
            page: Playwright Page instance
            selector: CSS selector for the form

        Returns:
            DetectedForm if found, None otherwise
        """
        forms = await self.detect_forms(page)
        for form in forms:
            if form.selector == selector or form.id == selector.lstrip("#"):
                return form
        return None

    async def find_field_by_label(
        self, page: "Page", label_text: str, container: str = "body"
    ) -> Optional[FormField]:
        """
        Find a field by its label text.

        Args:
            page: Playwright Page instance
            label_text: The label text to search for (case-insensitive)
            container: Container to search within

        Returns:
            FormField if found, None otherwise
        """
        fields = await self.detect_fields(page, container)
        label_lower = label_text.lower()
        for form_field in fields:
            if form_field.label and label_lower in form_field.label.lower():
                return form_field
        return None

    async def find_field_by_name(
        self, page: "Page", field_name: str, container: str = "body"
    ) -> Optional[FormField]:
        """
        Find a field by its name attribute.

        Args:
            page: Playwright Page instance
            field_name: The name attribute to search for
            container: Container to search within

        Returns:
            FormField if found, None otherwise
        """
        fields = await self.detect_fields(page, container)
        for form_field in fields:
            if form_field.name == field_name:
                return form_field
        return None

    def _parse_form(self, data: Dict[str, Any]) -> DetectedForm:
        """
        Parse form data from JavaScript evaluation.

        Args:
            data: Raw form data dictionary

        Returns:
            DetectedForm instance
        """
        return DetectedForm(
            selector=data.get("selector", "form"),
            action=data.get("action"),
            method=data.get("method", "GET"),
            fields=[self._parse_field(f) for f in data.get("fields", [])],
            submit_selector=data.get("submitSelector"),
            name=data.get("name"),
            id=data.get("id"),
        )

    def _parse_field(self, data: Dict[str, Any]) -> FormField:
        """
        Parse field data from JavaScript evaluation.

        Args:
            data: Raw field data dictionary

        Returns:
            FormField instance
        """
        return FormField(
            selector=data.get("selector", ""),
            field_type=data.get("type", "text"),
            name=data.get("name", ""),
            label=data.get("label"),
            placeholder=data.get("placeholder"),
            required=data.get("required", False),
            value=data.get("value"),
            options=data.get("options", []),
            id=data.get("id"),
            autocomplete=data.get("autocomplete"),
        )
