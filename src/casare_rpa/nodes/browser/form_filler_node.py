"""
Form Filler Node.

Fills form fields automatically based on a field mapping configuration.
Supports text inputs, selects, checkboxes, radio buttons, and textareas.
"""

from typing import Any

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.browser.browser_base import BrowserBaseNode


@properties(
    PropertyDef(
        "form_selector",
        PropertyType.STRING,
        default="form",
        label="Form Selector",
        placeholder="form, #login-form, .signup-form",
        tooltip="CSS selector for the form element (default: first form on page)",
    ),
    PropertyDef(
        "field_mapping",
        PropertyType.JSON,
        required=True,
        label="Field Mapping",
        placeholder='{"#email": "{{email}}", "#password": "{{password}}"}',
        tooltip="JSON mapping of selectors to values. Supports variables like {{var}}, ${var}, or %var%.",
    ),
    PropertyDef(
        "fast_mode",
        PropertyType.BOOLEAN,
        default=False,
        label="Fast Mode",
        tooltip="Fill all fields in single JavaScript call (fastest, no events triggered)",
        essential=True,
    ),
    PropertyDef(
        "auto_submit",
        PropertyType.BOOLEAN,
        default=False,
        label="Auto Submit",
        tooltip="Automatically click submit button after filling fields",
    ),
    PropertyDef(
        "clear_first",
        PropertyType.BOOLEAN,
        default=True,
        label="Clear Fields First",
        tooltip="Clear existing values before filling (for text inputs)",
    ),
    PropertyDef(
        "wait_between_fields",
        PropertyType.INTEGER,
        default=0,
        label="Wait Between Fields (ms)",
        min_value=0,
        max_value=5000,
        tooltip="Delay between filling each field (ms). Useful for forms with validation.",
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=5000,
        label="Timeout (ms)",
        min_value=100,
        max_value=60000,
        tooltip="Timeout per field in milliseconds. Fast mode uses min(timeout, 500ms).",
    ),
)
@node(category="browser")
class FormFillerNode(BrowserBaseNode):
    """
    Fill form fields automatically.

    This node fills form fields based on a JSON mapping of selectors to values.
    It supports:
    - Text inputs (fill with text)
    - Password inputs (fill with text)
    - Select dropdowns (select by value or text)
    - Checkboxes (check/uncheck based on truthy value)
    - Radio buttons (check based on truthy value)
    - Textareas (fill with text)

    Variable substitution is supported using {{var}}, ${var}, or %var% syntax.
    """

    # @category: browser
    # @requires: none
    # @ports: field_mapping, fields_in -> fields_filled, form_data

    NODE_NAME = "Form Filler"

    def __init__(self, node_id: str, name: str = "Form Filler", **kwargs: Any) -> None:
        """Initialize the form filler node."""
        config = kwargs.get("config", {})
        super().__init__(node_id, config, name=name)
        self.node_type = "FormFillerNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_page_passthrough_ports()
        # Accept either dict (JSON config) or array (from FormFieldNode chain)
        self.add_input_port("field_mapping", DataType.OBJECT, required=False)
        self.add_input_port("fields_in", DataType.LIST, required=False)
        self.add_output_port("fields_filled", DataType.INTEGER)
        self.add_output_port("form_data", DataType.OBJECT)

    async def execute(self, context: ExecutionContext) -> dict[str, Any]:
        """
        Execute the form filling operation.

        Args:
            context: Execution context with page and variables

        Returns:
            ExecutionResult with success status and filled field count
        """
        try:
            page = self.get_page(context)
        except Exception as e:
            return self.error_result(f"Failed to get page: {e}")

        form_selector = self.get_parameter("form_selector", "form")
        auto_submit = self.get_parameter("auto_submit", False)
        clear_first = self.get_parameter("clear_first", True)
        wait_between = self.get_parameter("wait_between_fields", 0)
        timeout = self.get_parameter("timeout", 5000)
        fast_mode = self.get_parameter("fast_mode", False)

        # Get field mapping from input ports or config
        # Priority: fields_in (array from FormFieldNode) > field_mapping port > config
        fields_array = self.get_input_value("fields_in")
        logger.info(f"FormFiller: fields_in = {fields_array}, type = {type(fields_array)}")
        logger.info(
            f"FormFiller: input_ports = {list(self.input_ports.keys()) if hasattr(self, 'input_ports') else 'N/A'}"
        )
        mapping = None
        # Store per-field metadata (clear_first, type) when using fields_array
        field_metadata: dict[str, dict[str, Any]] = {}

        if fields_array and isinstance(fields_array, list):
            # Convert array format to dict format, preserving per-field metadata
            # Array format: [{"selector": "...", "value": "...", "type": "...", "clear_first": ...}, ...]
            mapping = {}
            for field in fields_array:
                if isinstance(field, dict) and "selector" in field:
                    selector = field["selector"]
                    mapping[selector] = field.get("value", "")
                    # Store per-field settings (clear_first defaults to global setting)
                    field_metadata[selector] = {
                        "clear_first": field.get("clear_first", clear_first),
                        "type": field.get("type", "text"),
                    }
            logger.info(f"Using {len(mapping)} fields from FormFieldNode chain")
        else:
            # Try field_mapping port or config
            mapping = self.get_input_value("field_mapping")
            if mapping is None:
                mapping = self.get_parameter("field_mapping", {})

        if not mapping:
            return self.error_result(
                "field_mapping is required. Connect FormFieldNode chain to fields_in "
                "or provide JSON mapping."
            )

        if isinstance(mapping, str):
            # Parse JSON string
            try:
                import json

                mapping = json.loads(mapping)
            except json.JSONDecodeError as e:
                return self.error_result(f"Invalid JSON in field_mapping: {e}")

        if not isinstance(mapping, dict):
            return self.error_result(
                f"field_mapping must be a dictionary, got {type(mapping).__name__}"
            )

        # Resolve all variable references and normalize selectors upfront
        from casare_rpa.utils.selectors.selector_normalizer import normalize_selector

        resolved_mapping: dict[str, Any] = {}
        resolved_metadata: dict[str, dict[str, Any]] = {}
        skipped_count = 0
        for selector, value in mapping.items():
            # Skip empty selectors - they cause timeouts
            if not selector or not selector.strip():
                skipped_count += 1
                logger.debug("Skipping empty selector")
                continue
            # Normalize CasareRPA selectors (webctrl, itext, etc.) to Playwright format
            normalized_selector = normalize_selector(selector)
            resolved_mapping[normalized_selector] = self._normalize_numeric_value(value)
            # Preserve metadata with normalized selector key
            if selector in field_metadata:
                resolved_metadata[normalized_selector] = field_metadata[selector]
            else:
                # Default metadata for JSON mapping mode
                resolved_metadata[normalized_selector] = {
                    "clear_first": clear_first,
                    "type": "text",
                }
            if normalized_selector != selector:
                logger.debug(
                    f"Normalized selector: {selector[:50]}... -> {normalized_selector[:50]}..."
                )

        if skipped_count > 0:
            logger.info(f"Skipped {skipped_count} empty selectors")

        if not resolved_mapping:
            logger.warning("No valid selectors to fill after filtering empty ones")
            self.set_output_value("page", page)
            self.set_output_value("fields_filled", 0)
            self.set_output_value("form_data", {})
            return self.success_result(
                {
                    "fields_filled": 0,
                    "skipped_empty": skipped_count,
                    "message": "No valid selectors to fill",
                }
            )

        try:
            # Fast mode: Single JavaScript call for all fields (fastest)
            if fast_mode:
                result = await self._batch_fill_javascript(
                    page, resolved_mapping, resolved_metadata
                )
                filled_count = result.get("filled", 0)
                filled_data = result.get("data", {})
                errors = result.get("errors", [])

                if errors:
                    logger.warning(f"Fast mode: {len(errors)} fields failed: {errors[:3]}")
                logger.info(
                    f"Fast mode: filled {filled_count}/{len(resolved_mapping)} fields via JS batch"
                )

                # Auto-fallback: If fast mode failed for most fields, try standard mode
                if filled_count < len(resolved_mapping) // 2 and len(resolved_mapping) > 0:
                    logger.warning(
                        f"Fast mode only filled {filled_count}/{len(resolved_mapping)}, falling back to standard mode"
                    )
                    # Get unfilled selectors
                    unfilled = {k: v for k, v in resolved_mapping.items() if k not in filled_data}
                    unfilled_meta = {
                        k: v for k, v in resolved_metadata.items() if k not in filled_data
                    }
                    if unfilled:
                        extra_count, extra_data = await self._fill_fields_standard(
                            page, unfilled, unfilled_meta, wait_between, timeout
                        )
                        filled_count += extra_count
                        filled_data.update(extra_data)
                        logger.info(
                            f"Fallback filled {extra_count} more fields (total: {filled_count})"
                        )
            else:
                # Standard mode: Fill fields one by one with Playwright
                filled_count, filled_data = await self._fill_fields_standard(
                    page, resolved_mapping, resolved_metadata, wait_between, timeout
                )

            # Auto-submit if configured
            if auto_submit and filled_count > 0:
                await self._submit_form(page, form_selector, timeout)

            # Set output ports
            self.set_output_value("page", page)
            self.set_output_value("fields_filled", filled_count)
            self.set_output_value("form_data", filled_data)

            return self.success_result(
                {
                    "fields_filled": filled_count,
                    "form_data": filled_data,
                    "auto_submitted": auto_submit,
                    "fast_mode": fast_mode,
                }
            )

        except Exception as e:
            logger.error(f"Form fill failed: {e}")
            await self.screenshot_on_failure(page, "form_fill_error")
            return self.error_result(str(e))

    async def _batch_fill_playwright(
        self,
        page: Any,
        mapping: dict[str, Any],
        metadata: dict[str, dict[str, Any]],
        timeout: int,
    ) -> dict[str, Any]:
        """
        Fast batch fill using Playwright locators with minimal waits.

        Uses Playwright to locate elements (supporting XPath, CSS, text selectors)
        then fills them with force=True and no_wait_after=True for speed.

        Args:
            page: Playwright Page instance
            mapping: Resolved field mapping (normalized_selector -> value)
            metadata: Per-field metadata (selector -> {clear_first, type})
            timeout: Timeout per field in ms

        Returns:
            Dict with filled count and data
        """
        import asyncio

        filled_count = 0
        filled_data: dict[str, Any] = {}
        errors: list = []

        # Fast mode uses aggressive timeouts - 500ms per field max
        fast_timeout = min(timeout, 500)

        # Collect all fill tasks
        async def fill_field(selector: str, value: Any) -> bool:
            nonlocal filled_count
            try:
                # Use Playwright's locator which handles XPath, CSS, text, etc.
                locator = page.locator(selector).first

                # Quick check if element exists (fast fail)
                try:
                    await locator.wait_for(state="attached", timeout=fast_timeout)
                except Exception:
                    # Element not found quickly - skip it
                    errors.append(f"{selector[:30]}...: not found within {fast_timeout}ms")
                    return False

                # Get per-field clear_first setting (defaults to True)
                field_meta = metadata.get(selector, {})
                should_clear = field_meta.get("clear_first", True)

                # Playwright fill() clears by default. Use type() to append without clearing.
                if should_clear:
                    # fill() auto-clears, so just one call needed
                    await locator.fill(
                        str(value), force=True, no_wait_after=True, timeout=fast_timeout
                    )
                else:
                    # Don't clear - use type() which appends to existing value
                    await locator.type(str(value), timeout=fast_timeout)

                filled_count += 1
                filled_data[selector] = value
                return True
            except Exception as e:
                errors.append(f"{selector[:30]}...: {e}")
                logger.debug(f"Failed to fill {selector[:50]}...: {e}")
                return False

        # Run all fills concurrently for maximum speed
        tasks = [fill_field(sel, val) for sel, val in mapping.items()]
        await asyncio.gather(*tasks, return_exceptions=True)

        if errors:
            logger.debug(f"Some fields failed ({len(errors)}): {errors[:3]}...")

        return {"filled": filled_count, "data": filled_data, "errors": errors}

    async def _batch_fill_javascript(
        self, page: Any, mapping: dict[str, Any], metadata: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Fill all form fields in a single JavaScript evaluate call.

        Fastest method - single browser round-trip for all fields.
        Supports both CSS selectors and XPath.

        Args:
            page: Playwright Page instance
            mapping: Resolved field mapping (selector -> value)
            metadata: Per-field metadata (selector -> {clear_first, type})

        Returns:
            Dict with filled count and data
        """
        # Build fields array with per-field settings
        fields_config = []
        for selector, value in mapping.items():
            field_meta = metadata.get(selector, {})
            fields_config.append(
                {
                    "selector": selector,
                    "value": str(value),
                    "clearFirst": field_meta.get("clear_first", True),
                    "isXPath": selector.startswith("//") or selector.startswith("xpath="),
                }
            )

        # JavaScript that fills all fields and returns results
        js_fill_script = """
        (fields) => {
            const results = { filled: 0, data: {}, errors: [] };

            // Helper to find element by CSS or XPath
            function findElement(selector, isXPath) {
                if (isXPath) {
                    // Remove xpath= prefix if present
                    const xpath = selector.startsWith('xpath=') ? selector.slice(6) : selector;
                    const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                    return result.singleNodeValue;
                } else {
                    return document.querySelector(selector);
                }
            }

            // Helper to set native value (works with React/Angular)
            function setNativeValue(el, value) {
                const valueSetter = Object.getOwnPropertyDescriptor(el, 'value')?.set;
                const prototype = Object.getPrototypeOf(el);
                const prototypeValueSetter = Object.getOwnPropertyDescriptor(prototype, 'value')?.set;

                if (valueSetter && valueSetter !== prototypeValueSetter) {
                    prototypeValueSetter.call(el, value);
                } else if (valueSetter) {
                    valueSetter.call(el, value);
                } else {
                    el.value = value;
                }
            }

            for (const field of fields) {
                try {
                    const el = findElement(field.selector, field.isXPath);
                    if (!el) {
                        results.errors.push(`Not found: ${field.selector.slice(0, 50)}...`);
                        continue;
                    }

                    const tagName = el.tagName.toLowerCase();
                    const inputType = el.type?.toLowerCase() || '';

                    if (tagName === 'select') {
                        // Select dropdown
                        const options = el.options;
                        let matched = false;
                        for (let i = 0; i < options.length; i++) {
                            if (options[i].value === field.value || options[i].text === field.value) {
                                el.selectedIndex = i;
                                matched = true;
                                break;
                            }
                        }
                        if (!matched) {
                            results.errors.push(`Option not found: ${field.value}`);
                            continue;
                        }
                    } else if (inputType === 'checkbox' || inputType === 'radio') {
                        const shouldCheck = Boolean(field.value) &&
                            !['false', '0', 'no', 'off', ''].includes(field.value.toLowerCase());
                        el.checked = shouldCheck;
                    } else {
                        // Text input, textarea
                        if (field.clearFirst) {
                            setNativeValue(el, '');
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                        }
                        setNativeValue(el, field.value);
                    }

                    // Dispatch events for frameworks (React, Angular, Vue)
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    el.dispatchEvent(new Event('blur', { bubbles: true }));

                    results.filled++;
                    results.data[field.selector] = field.value;
                } catch (err) {
                    results.errors.push(`Error: ${err.message}`);
                }
            }

            return results;
        }
        """

        result = await page.evaluate(js_fill_script, fields_config)

        # Log any errors
        for error in result.get("errors", []):
            logger.warning(error)

        return result

    async def _fill_fields_standard(
        self,
        page: Any,
        mapping: dict[str, Any],
        metadata: dict[str, dict[str, Any]],
        wait_between: int,
        timeout: int = 5000,
    ) -> tuple[int, dict[str, Any]]:
        """
        Fill fields one by one using standard Playwright methods.

        Args:
            page: Playwright Page instance
            mapping: Resolved field mapping
            metadata: Per-field metadata (selector -> {clear_first, type})
            wait_between: Delay between fields in ms
            timeout: Timeout per field in ms

        Returns:
            Tuple of (filled_count, filled_data)
        """
        import asyncio

        filled_count = 0
        filled_data: dict[str, Any] = {}

        # Use shorter timeout per field for faster failure - 1 second per field
        field_timeout = min(timeout, 1000)

        for selector, resolved_value in mapping.items():
            try:
                # Use locator with timeout for better control
                locator = page.locator(selector).first
                try:
                    await locator.wait_for(state="attached", timeout=field_timeout)
                except Exception:
                    logger.debug(f"Field not found within {field_timeout}ms: {selector[:50]}...")
                    continue

                # Get element handle for type detection
                element = await locator.element_handle()
                if not element:
                    continue

                # Get per-field clear_first setting (defaults to True)
                field_meta = metadata.get(selector, {})
                should_clear = field_meta.get("clear_first", True)

                # Get element info
                tag_name = await element.evaluate("e => e.tagName.toLowerCase()")
                input_type = await element.get_attribute("type") if tag_name == "input" else None

                # Fill based on element type
                if tag_name == "select":
                    await self._fill_select(element, resolved_value)
                elif input_type in ("checkbox", "radio"):
                    await self._fill_checkbox_radio(element, resolved_value)
                else:
                    # Text input, textarea, or other input types
                    await self._fill_text(element, resolved_value, should_clear)

                filled_count += 1
                filled_data[selector] = resolved_value
                logger.debug(f"Filled field {selector[:50]}...")

                # Wait between fields if configured
                if wait_between > 0:
                    await asyncio.sleep(wait_between / 1000)

            except Exception as field_error:
                logger.debug(f"Failed to fill field {selector[:50]}...: {field_error}")
                continue

        return filled_count, filled_data

    def _normalize_numeric_value(self, value: Any) -> Any:
        """
        Convert whole-number floats to integers for cleaner form input.

        Excel often stores numbers (like phone numbers) as floats,
        resulting in values like 40716543298.0 instead of 40716543298.
        This method converts such values to integers.

        Args:
            value: Value to normalize

        Returns:
            Normalized value (int if whole-number float, original otherwise)
        """
        if isinstance(value, float) and value.is_integer():
            return int(value)
        return value

    async def _fill_text(self, element: Any, value: Any, clear_first: bool) -> None:
        """
        Fill a text input or textarea.

        Args:
            element: Element handle
            value: Value to fill
            clear_first: Whether to clear existing value first
        """
        if clear_first:
            # fill() auto-clears, so just one call needed
            await element.fill(str(value))
        else:
            # Don't clear - use type() which appends to existing value
            await element.type(str(value))

    async def _fill_select(self, element: Any, value: Any) -> None:
        """
        Fill a select dropdown.

        Args:
            element: Element handle
            value: Value or text to select
        """
        # Try by value first, then by label
        try:
            await element.select_option(value=str(value))
        except Exception:
            try:
                await element.select_option(label=str(value))
            except Exception:
                # Try by index if numeric
                if isinstance(value, int):
                    await element.select_option(index=value)
                else:
                    raise

    async def _fill_checkbox_radio(self, element: Any, value: Any) -> None:
        """
        Fill a checkbox or radio button.

        Args:
            element: Element handle
            value: Truthy value to check/uncheck
        """
        should_check = bool(value) and str(value).lower() not in (
            "false",
            "0",
            "no",
            "off",
            "",
        )

        if should_check:
            await element.check()
        else:
            await element.uncheck()

    async def _submit_form(self, page: Any, form_selector: str, timeout: int) -> None:
        """
        Submit the form by clicking the submit button.

        Args:
            page: Playwright Page instance
            form_selector: CSS selector for the form
            timeout: Timeout in ms
        """
        # Find submit button within form or generic submit
        submit_selectors = [
            f'{form_selector} [type="submit"]',
            f'{form_selector} button:not([type="button"]):not([type="reset"])',
            f'{form_selector} input[type="submit"]',
            '[type="submit"]',
            'button:not([type="button"]):not([type="reset"])',
        ]

        for submit_selector in submit_selectors:
            submit_btn = await page.query_selector(submit_selector)
            if submit_btn:
                await submit_btn.click()
                # Wait for navigation or network idle
                try:
                    await page.wait_for_load_state("networkidle", timeout=timeout)
                except Exception:
                    # Page might not navigate, just continue
                    pass
                logger.debug(f"Form submitted using: {submit_selector}")
                return

        logger.warning("No submit button found for form")
