"""
UI Explorer Element Model.

Unified element representation for browser DOM and desktop UI elements.
Supports lazy loading of children for performance with deep hierarchies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ElementSource(Enum):
    """Source of the UI element."""

    BROWSER = "browser"
    DESKTOP = "desktop"


@dataclass
class UIExplorerElement:
    """
    Unified element representation for UI Explorer.

    Works with both browser DOM elements and desktop UIAutomation controls.
    Supports lazy loading of children for performance.

    Attributes:
        source: "browser" or "desktop"
        tag_or_control: HTML tag name (div, button) or Windows control type (Button, Edit)
        element_id: Unique identifier for this element (DOM id or AutomationId)
        name: Display name (text content, Name property, aria-label)
        attributes: All element attributes/properties
        rect: Bounding rectangle {x, y, width, height}
        children: List of child elements (lazy loaded)
        children_loaded: Whether children have been loaded
        parent: Reference to parent element
        raw_data: Original element data from browser/desktop
    """

    source: ElementSource
    tag_or_control: str
    element_id: str
    name: str
    attributes: dict[str, str] = field(default_factory=dict)
    rect: dict[str, int] | None = None
    children: list[UIExplorerElement] = field(default_factory=list)
    children_loaded: bool = False
    parent: UIExplorerElement | None = None
    raw_data: Any | None = field(default=None, repr=False)

    @property
    def display_name(self) -> str:
        """
        Get formatted display name for tree view.

        Format: {tag/control}: {name} [#{id}]
        Example: button: Submit [#submit-btn]
        """
        parts = [self.tag_or_control]

        if self.name:
            # Truncate long names
            display_name = self.name[:40]
            if len(self.name) > 40:
                display_name += "..."
            parts.append(f": {display_name}")

        if self.element_id:
            parts.append(f" [#{self.element_id}]")

        return "".join(parts)

    @property
    def short_name(self) -> str:
        """Get short display name without id."""
        if self.name:
            name = self.name[:30]
            if len(self.name) > 30:
                name += "..."
            return f"{self.tag_or_control}: {name}"
        return self.tag_or_control

    @property
    def css_classes(self) -> list[str]:
        """Get CSS classes (browser only)."""
        if self.source != ElementSource.BROWSER:
            return []
        class_str = self.attributes.get("class", "")
        return [c.strip() for c in class_str.split() if c.strip()]

    def get_attribute(self, name: str, default: str = "") -> str:
        """Get attribute value with default."""
        return self.attributes.get(name, default)

    def has_children_hint(self) -> bool:
        """
        Check if element likely has children (for lazy loading).

        Returns True for container-type elements, False for leaf elements.
        """
        if self.children_loaded:
            return len(self.children) > 0

        # Browser leaf elements
        browser_leaf_tags = {
            "input",
            "img",
            "br",
            "hr",
            "meta",
            "link",
            "area",
            "base",
            "col",
            "embed",
            "param",
            "source",
            "track",
            "wbr",
        }

        # Desktop leaf controls
        desktop_leaf_controls = {
            "Button",
            "Edit",
            "Text",
            "Image",
            "CheckBox",
            "RadioButton",
            "Hyperlink",
            "ProgressBar",
            "Slider",
            "Separator",
            "Thumb",
            "ScrollBar",
        }

        tag_lower = self.tag_or_control.lower()

        if self.source == ElementSource.BROWSER:
            return tag_lower not in browser_leaf_tags
        else:
            # Remove "Control" suffix for desktop
            control_name = self.tag_or_control
            if control_name.endswith("Control"):
                control_name = control_name[:-7]
            return control_name not in desktop_leaf_controls

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "source": self.source.value,
            "tag_or_control": self.tag_or_control,
            "element_id": self.element_id,
            "name": self.name,
            "attributes": self.attributes,
            "rect": self.rect,
            "children_loaded": self.children_loaded,
        }

    @classmethod
    def from_browser_data(
        cls,
        data: dict[str, Any],
        parent: UIExplorerElement | None = None,
    ) -> UIExplorerElement:
        """
        Create element from browser DOM data.

        Args:
            data: Dictionary with tag, id, className, attributes, rect, etc.
            parent: Parent element reference

        Returns:
            UIExplorerElement instance
        """
        tag = data.get("tag", data.get("tagName", "unknown")).lower()

        # Get element id
        element_id = data.get("id", "") or data.get("element_id", "")

        # Get display name (prefer text content, then aria-label, then id)
        name = ""
        text = data.get("text", data.get("textContent", ""))
        if text:
            # Clean up text content
            name = " ".join(text.split())[:50]
        elif data.get("aria-label"):
            name = data["aria-label"]
        elif data.get("title"):
            name = data["title"]
        elif data.get("placeholder"):
            name = data["placeholder"]
        elif data.get("alt"):
            name = data["alt"]

        # Build attributes dict
        attributes = {}
        if element_id:
            attributes["id"] = element_id
        if data.get("className") or data.get("class"):
            attributes["class"] = data.get("className", data.get("class", ""))
        if data.get("href"):
            attributes["href"] = data["href"]
        if data.get("src"):
            attributes["src"] = data["src"]
        if data.get("type"):
            attributes["type"] = data["type"]
        if data.get("name"):
            attributes["name"] = data["name"]
        if data.get("value"):
            attributes["value"] = data["value"]
        if data.get("data-testid"):
            attributes["data-testid"] = data["data-testid"]
        if data.get("role"):
            attributes["role"] = data["role"]
        if data.get("aria-label"):
            attributes["aria-label"] = data["aria-label"]

        # Copy any custom attributes
        for key, value in data.get("attributes", {}).items():
            if key not in attributes and value:
                attributes[key] = str(value)

        # Get bounding rect
        rect = data.get("rect", data.get("boundingRect"))
        if rect:
            rect = {
                "x": int(rect.get("x", rect.get("left", 0))),
                "y": int(rect.get("y", rect.get("top", 0))),
                "width": int(rect.get("width", 0)),
                "height": int(rect.get("height", 0)),
            }

        return cls(
            source=ElementSource.BROWSER,
            tag_or_control=tag,
            element_id=element_id,
            name=name,
            attributes=attributes,
            rect=rect,
            parent=parent,
            raw_data=data,
        )

    @classmethod
    def from_desktop_data(
        cls,
        data: dict[str, Any],
        parent: UIExplorerElement | None = None,
    ) -> UIExplorerElement:
        """
        Create element from desktop UIAutomation data.

        Args:
            data: Dictionary with ControlType, Name, AutomationId, etc.
            parent: Parent element reference

        Returns:
            UIExplorerElement instance
        """
        # Get control type
        control_type = data.get("ControlTypeName", data.get("control_type", "Unknown"))
        if control_type.endswith("Control"):
            control_type = control_type[:-7]

        # Get automation id
        element_id = data.get("AutomationId", data.get("automation_id", ""))

        # Get name
        name = data.get("Name", data.get("name", ""))

        # Build attributes
        attributes = {}
        if element_id:
            attributes["AutomationId"] = element_id
        if name:
            attributes["Name"] = name
        if data.get("ClassName"):
            attributes["ClassName"] = data["ClassName"]
        if data.get("ProcessId"):
            attributes["ProcessId"] = str(data["ProcessId"])
        if data.get("IsEnabled") is not None:
            attributes["IsEnabled"] = str(data["IsEnabled"])
        if data.get("IsOffscreen") is not None:
            attributes["IsOffscreen"] = str(data["IsOffscreen"])
        if data.get("LocalizedControlType"):
            attributes["LocalizedControlType"] = data["LocalizedControlType"]

        # Get bounding rect
        rect = data.get("rect", data.get("BoundingRectangle"))
        if rect:
            if isinstance(rect, dict):
                rect = {
                    "x": int(rect.get("x", rect.get("left", 0))),
                    "y": int(rect.get("y", rect.get("top", 0))),
                    "width": int(rect.get("width", 0)),
                    "height": int(rect.get("height", 0)),
                }

        return cls(
            source=ElementSource.DESKTOP,
            tag_or_control=control_type,
            element_id=element_id,
            name=name,
            attributes=attributes,
            rect=rect,
            parent=parent,
            raw_data=data,
        )

    @classmethod
    def from_desktop_element(
        cls,
        desktop_element: Any,
        parent: UIExplorerElement | None = None,
    ) -> UIExplorerElement:
        """
        Create from DesktopElement instance (casare_rpa.desktop.element).

        Args:
            desktop_element: DesktopElement instance
            parent: Parent element reference

        Returns:
            UIExplorerElement instance
        """
        # Extract properties from DesktopElement
        data = {
            "ControlTypeName": desktop_element.get_property("ControlTypeName") or "Unknown",
            "Name": desktop_element.get_property("Name") or "",
            "AutomationId": desktop_element.get_property("AutomationId") or "",
            "ClassName": desktop_element.get_property("ClassName") or "",
            "ProcessId": desktop_element.get_property("ProcessId"),
            "IsEnabled": desktop_element.is_enabled(),
            "IsOffscreen": not desktop_element.is_visible(),
        }

        element = cls.from_desktop_data(data, parent)
        element.raw_data = desktop_element
        return element
