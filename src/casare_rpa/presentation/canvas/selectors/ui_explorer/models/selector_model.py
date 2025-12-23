"""
Selector Model for UI Explorer.

Manages selector attribute state and provides XML/selector string generation.
Uses Qt signals for reactive updates to UI panels.
"""

from dataclasses import dataclass
from typing import Any

from loguru import logger
from PySide6.QtCore import QObject, Signal

from casare_rpa.presentation.canvas.selectors.ui_explorer.models.element_model import (
    ElementSource,
    UIExplorerElement,
)


@dataclass
class SelectorAttribute:
    """
    Single attribute in selector.

    Represents an element attribute that can be included/excluded
    from the final selector string.

    Attributes:
        name: Attribute name (e.g., "id", "class", "tag")
        value: Attribute value
        included: Whether attribute is included in selector
        required: Whether attribute cannot be unchecked (e.g., tag is always required)
        editable: Whether the value can be edited by user
        computed: Whether value was computed/derived (vs direct attribute)
    """

    name: str
    value: str
    included: bool = False
    required: bool = False
    editable: bool = True
    computed: bool = False

    def __post_init__(self) -> None:
        """Ensure required attributes are always included."""
        if self.required:
            self.included = True

    @property
    def display_value(self) -> str:
        """Get display value, showing (empty) for empty values."""
        if not self.value:
            return "(empty)"
        # Truncate long values
        if len(self.value) > 60:
            return self.value[:57] + "..."
        return self.value

    @property
    def is_empty(self) -> bool:
        """Check if value is empty or None."""
        return not self.value or self.value == "(empty)"


# Full UiPath-style browser attributes
BROWSER_ATTRIBUTES = [
    # Core identification
    "tag",
    "id",
    "name",
    "class",
    "cls",
    # CSS/XPath
    "css-selector",
    "xpath",
    # Text content
    "innertext",
    "visibleinnertext",
    "title",
    # Accessibility
    "aaname",
    "aastate",
    "role",
    "aria-label",
    # Hierarchy
    "parentid",
    "parentclass",
    "parentname",
    "isleaf",
    "idx",
    # Data attributes
    "data-testid",
    "data-id",
    "data-name",
    # State
    "type",
    "value",
    "placeholder",
    "href",
    "src",
    "alt",
]

# Full UiPath-style desktop attributes
DESKTOP_ATTRIBUTES = [
    # Core
    "ControlType",
    "AutomationId",
    "Name",
    "ClassName",
    # Accessibility
    "aaname",
    "aastate",
    # Application
    "app",
    "AppPath",
    "ProcessId",
    # Hierarchy
    "parentid",
    "parentclass",
    "isleaf",
    "idx",
    # State
    "IsEnabled",
    "IsOffscreen",
    "HasKeyboardFocus",
    # Additional
    "LocalizedControlType",
    "AccessKey",
    "AcceleratorKey",
]

# Priority order for browser attributes (used for sorting)
BROWSER_ATTRIBUTE_PRIORITY = [
    "tag",
    "id",
    "data-testid",
    "name",
    "type",
    "value",  # High priority for inputs/buttons (input[value="Submit"])
    "class",
    "cls",
    "role",
    "aria-label",
    "aaname",
    "aastate",
    "href",
    "src",
    "alt",
    "title",
    "placeholder",
    "innertext",
    "visibleinnertext",
    "parentid",
    "parentclass",
    "parentname",
    "isleaf",
    "idx",
    "css-selector",
    "xpath",
]

# Priority order for desktop attributes (used for sorting)
DESKTOP_ATTRIBUTE_PRIORITY = [
    "ControlType",
    "AutomationId",
    "Name",
    "ClassName",
    "aaname",
    "aastate",
    "app",
    "AppPath",
    "ProcessId",
    "parentid",
    "parentclass",
    "isleaf",
    "idx",
    "IsEnabled",
    "IsOffscreen",
    "HasKeyboardFocus",
    "LocalizedControlType",
    "AccessKey",
    "AcceleratorKey",
]

# Attributes that are always required
REQUIRED_ATTRIBUTES = {"tag", "ControlType"}

# Attributes that should be included by default
DEFAULT_INCLUDED = {
    "tag",
    "id",
    "data-testid",
    "name",
    "class",
    "type",
    "value",  # Important for submit buttons (input[value="Submit"])
    "ControlType",
    "AutomationId",
    "Name",
}


class SelectorModel(QObject):
    """
    Manages selector state for UI Explorer.

    Tracks which attributes are included in the selector and
    provides methods for generating XML/selector strings.

    Signals:
        changed: Emitted when any attribute changes
        attribute_toggled: Emitted when an attribute is toggled (name, included)
        preview_updated: Emitted when preview string changes (xml_string)
    """

    changed = Signal()
    attribute_toggled = Signal(str, bool)  # name, included
    preview_updated = Signal(str)  # xml_string

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize the selector model."""
        super().__init__(parent)

        self._attributes: list[SelectorAttribute] = []
        self._element: UIExplorerElement | None = None
        self._source: ElementSource | None = None

    @property
    def attributes(self) -> list[SelectorAttribute]:
        """Get list of all attributes."""
        return self._attributes

    @property
    def element(self) -> UIExplorerElement | None:
        """Get the current element."""
        return self._element

    @property
    def source(self) -> ElementSource | None:
        """Get the element source (browser/desktop)."""
        return self._source

    def load_from_element(self, element: UIExplorerElement) -> None:
        """
        Load attributes from a UIExplorerElement.

        Creates SelectorAttribute objects for all element attributes,
        sorted by priority for the element type.

        Args:
            element: UIExplorerElement to load from
        """
        self._element = element
        self._source = element.source
        self._attributes.clear()

        # Determine priority order based on source
        if element.source == ElementSource.BROWSER:
            priority = BROWSER_ATTRIBUTE_PRIORITY
        else:
            priority = DESKTOP_ATTRIBUTE_PRIORITY

        # Build attributes dict combining tag/control with other attrs
        attrs_dict: dict[str, str] = {}

        # Add tag/control type first
        if element.source == ElementSource.BROWSER:
            attrs_dict["tag"] = element.tag_or_control
        else:
            attrs_dict["ControlType"] = element.tag_or_control

        # Add element_id if present
        if element.element_id:
            if element.source == ElementSource.BROWSER:
                attrs_dict["id"] = element.element_id
            else:
                attrs_dict["AutomationId"] = element.element_id

        # Add name if present
        if element.name:
            if element.source == ElementSource.BROWSER:
                attrs_dict["innertext"] = element.name
            else:
                attrs_dict["Name"] = element.name

        # Add all other attributes
        for name, value in element.attributes.items():
            if name not in attrs_dict and value:
                attrs_dict[name] = str(value)

        # Sort attributes by priority
        sorted_attrs = []
        for name in priority:
            if name in attrs_dict:
                sorted_attrs.append((name, attrs_dict.pop(name)))

        # Add remaining attributes alphabetically
        for name in sorted(attrs_dict.keys()):
            sorted_attrs.append((name, attrs_dict[name]))

        # Create SelectorAttribute objects
        for name, value in sorted_attrs:
            is_required = name in REQUIRED_ATTRIBUTES
            is_included = name in DEFAULT_INCLUDED or is_required

            # Special case: include id/AutomationId if present
            if name in ("id", "AutomationId") and value:
                is_included = True

            attr = SelectorAttribute(
                name=name,
                value=value,
                included=is_included,
                required=is_required,
                editable=name not in ("tag", "ControlType"),
                computed=name in ("css-selector", "xpath"),
            )
            self._attributes.append(attr)

        logger.debug(f"Loaded {len(self._attributes)} attributes from element")

        # Emit signals
        self.changed.emit()
        self._emit_preview_update()

    def load_from_dict(self, element_data: dict[str, Any]) -> None:
        """
        Load attributes from an element data dictionary.

        Args:
            element_data: Element data dict with source, tag_or_control, attributes, etc.
        """
        source = element_data.get("source", "browser")
        if source == "browser" or source == ElementSource.BROWSER:
            element = UIExplorerElement.from_browser_data(element_data)
        else:
            element = UIExplorerElement.from_desktop_data(element_data)

        self.load_from_element(element)

    def toggle_attribute(self, name: str) -> bool:
        """
        Toggle inclusion of an attribute.

        Args:
            name: Attribute name to toggle

        Returns:
            New inclusion state, or False if attribute not found or required
        """
        for attr in self._attributes:
            if attr.name == name:
                if attr.required:
                    logger.debug(f"Cannot toggle required attribute: {name}")
                    return True  # Required attrs are always included

                attr.included = not attr.included
                logger.debug(f"Toggled attribute {name}: {attr.included}")

                self.attribute_toggled.emit(name, attr.included)
                self.changed.emit()
                self._emit_preview_update()
                return attr.included

        logger.warning(f"Attribute not found: {name}")
        return False

    def set_attribute_included(self, name: str, included: bool) -> bool:
        """
        Set inclusion state of an attribute.

        Args:
            name: Attribute name
            included: Whether to include

        Returns:
            True if successful, False if not found or required
        """
        for attr in self._attributes:
            if attr.name == name:
                if attr.required and not included:
                    logger.debug(f"Cannot exclude required attribute: {name}")
                    return False

                if attr.included != included:
                    attr.included = included
                    logger.debug(f"Set attribute {name} included: {included}")

                    self.attribute_toggled.emit(name, included)
                    self.changed.emit()
                    self._emit_preview_update()
                return True

        logger.warning(f"Attribute not found: {name}")
        return False

    def set_attribute_value(self, name: str, value: str) -> bool:
        """
        Update an attribute's value.

        Args:
            name: Attribute name
            value: New value

        Returns:
            True if successful
        """
        for attr in self._attributes:
            if attr.name == name:
                if not attr.editable:
                    logger.debug(f"Cannot edit non-editable attribute: {name}")
                    return False

                if attr.value != value:
                    attr.value = value
                    logger.debug(f"Updated attribute {name} value")

                    self.changed.emit()
                    self._emit_preview_update()
                return True

        return False

    def get_attribute(self, name: str) -> SelectorAttribute | None:
        """
        Get attribute by name.

        Args:
            name: Attribute name

        Returns:
            SelectorAttribute or None
        """
        for attr in self._attributes:
            if attr.name == name:
                return attr
        return None

    def get_included_attributes(self) -> list[SelectorAttribute]:
        """
        Get list of included attributes only.

        Returns:
            List of SelectorAttribute objects that are included
        """
        return [attr for attr in self._attributes if attr.included]

    def get_included_names(self) -> list[str]:
        """
        Get list of included attribute names.

        Returns:
            List of attribute names that are included
        """
        return [attr.name for attr in self._attributes if attr.included]

    def include_all(self) -> None:
        """Include all non-empty attributes."""
        for attr in self._attributes:
            if not attr.is_empty:
                attr.included = True
                self.attribute_toggled.emit(attr.name, True)

        self.changed.emit()
        self._emit_preview_update()

    def include_minimum(self) -> None:
        """Include only required and high-priority unique attributes."""
        for attr in self._attributes:
            if attr.required:
                attr.included = True
            elif attr.name in ("id", "AutomationId", "data-testid") and not attr.is_empty:
                attr.included = True
            else:
                attr.included = False
            self.attribute_toggled.emit(attr.name, attr.included)

        self.changed.emit()
        self._emit_preview_update()

    def clear(self) -> None:
        """Clear all attributes."""
        self._attributes.clear()
        self._element = None
        self._source = None
        self.changed.emit()
        self.preview_updated.emit("")

    def to_xml(self) -> str:
        """
        Generate UiPath-style XML selector string.

        Returns:
            XML-formatted selector string
        """
        if not self._attributes:
            return ""

        included = self.get_included_attributes()
        if not included:
            return ""

        # Get tag/control type
        tag = "element"
        for attr in included:
            if attr.name == "tag":
                tag = attr.value
                break
            elif attr.name == "ControlType":
                tag = attr.value
                break

        # Build attribute string
        attr_parts = []
        for attr in included:
            if attr.name in ("tag", "ControlType"):
                continue  # Tag is the element name
            if attr.value and attr.value != "(empty)":
                # Escape quotes
                escaped = attr.value.replace("'", "&apos;").replace('"', "&quot;")
                attr_parts.append(f"{attr.name}='{escaped}'")

        attrs_str = " ".join(attr_parts)
        if attrs_str:
            return f"<{tag} {attrs_str} />"
        return f"<{tag} />"

    def to_selector_string(self) -> str:
        """
        Generate CSS/XPath-style selector string.

        Returns:
            Selector string
        """
        if not self._attributes or not self._element:
            return ""

        included = self.get_included_attributes()
        if not included:
            return ""

        # For browser, generate CSS-like selector
        if self._source == ElementSource.BROWSER:
            return self._to_css_selector(included)
        else:
            return self._to_uia_selector(included)

    def _to_css_selector(self, included: list[SelectorAttribute]) -> str:
        """Generate CSS selector from included attributes."""
        parts = []

        # Get tag
        tag = ""
        for attr in included:
            if attr.name == "tag":
                tag = attr.value
                break

        # Start with tag if present
        if tag:
            parts.append(tag)

        # Add id (highest priority)
        for attr in included:
            if attr.name == "id" and not attr.is_empty:
                parts.append(f"#{attr.value}")
                break

        # For inputs/buttons without id, prioritize value, type, name attributes
        if tag and tag.lower() in ("input", "button") and not any("#" in p for p in parts):
            # Check for value (great for submit buttons)
            for attr in included:
                if attr.name == "value" and not attr.is_empty:
                    parts.append(f'[value="{attr.value}"]')
                    return "".join(parts)  # value alone is often unique enough

            # Check for type
            for attr in included:
                if attr.name == "type" and not attr.is_empty:
                    parts.append(f'[type="{attr.value}"]')
                    break

            # Check for name
            for attr in included:
                if attr.name == "name" and not attr.is_empty:
                    parts.append(f'[name="{attr.value}"]')
                    break

        # Add classes
        for attr in included:
            if attr.name == "class" and not attr.is_empty:
                for cls in attr.value.split():
                    if cls:
                        parts.append(f".{cls}")
                break

        # Add other attributes
        for attr in included:
            if attr.name in (
                "tag",
                "id",
                "class",
                "innertext",
                "value",
                "type",
                "name",
            ):
                continue
            if not attr.is_empty:
                parts.append(f"[{attr.name}='{attr.value}']")

        return "".join(parts) if parts else ""

    def _to_uia_selector(self, included: list[SelectorAttribute]) -> str:
        """Generate UIA selector from included attributes."""
        parts = []

        for attr in included:
            if not attr.is_empty:
                parts.append(f"{attr.name}={attr.value}")

        return " AND ".join(parts) if parts else ""

    def _emit_preview_update(self) -> None:
        """Emit preview update signal with current XML."""
        xml = self.to_xml()
        self.preview_updated.emit(xml)
