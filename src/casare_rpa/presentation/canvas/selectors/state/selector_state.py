"""
Centralized State for Element Selector Dialog.

Provides a single source of truth for all selector dialog state,
enabling reactive UI updates and clean separation of concerns.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from PySide6.QtCore import QObject, Signal


class PickingMode(Enum):
    """Available picking modes."""

    AUTO = auto()
    BROWSER = auto()
    DESKTOP = auto()
    OCR = auto()
    IMAGE = auto()


class ValidationStatus(Enum):
    """Selector validation status."""

    PENDING = auto()
    VALIDATING = auto()
    VALID = auto()
    INVALID = auto()
    ERROR = auto()


@dataclass
class AttributeRow:
    """
    A single attribute row in the selector builder.

    Attributes:
        name: Attribute name (e.g., "id", "class", "data-testid")
        value: Attribute value
        score: Reliability score 0-100
        enabled: Whether to include in generated selector
        selector_type: Type of selector this generates (css, xpath, etc.)
    """

    name: str
    value: str
    score: float
    enabled: bool = True
    selector_type: str = "css"
    description: str = ""

    @property
    def score_color(self) -> str:
        """Get color based on score: green (80+), yellow (60-79), red (<60)."""
        if self.score >= 80:
            return "#10b981"  # Green
        elif self.score >= 60:
            return "#fbbf24"  # Yellow
        return "#ef4444"  # Red


@dataclass
class ElementSelectorState:
    """
    Centralized state for element selector dialog.

    This dataclass holds all state needed by the dialog and its widgets.
    Changes to state trigger UI updates via the StateManager signals.
    """

    # Mode
    mode: PickingMode = PickingMode.AUTO
    is_picking: bool = False

    # Current element
    element_html: str = ""
    element_tag: str = ""
    element_id: str = ""
    element_classes: list[str] = field(default_factory=list)
    element_text: str = ""
    element_properties: dict[str, Any] = field(default_factory=dict)
    element_rect: dict[str, float] | None = None

    # Selector building
    attribute_rows: list[AttributeRow] = field(default_factory=list)
    generated_selector: str = ""
    selector_type: str = "css"
    match_count: int = 0
    is_unique: bool = False
    validation_status: ValidationStatus = ValidationStatus.PENDING
    validation_time_ms: float = 0.0

    # Anchor
    anchor_enabled: bool = False
    anchor_selector: str = ""
    anchor_tag: str = ""
    anchor_text: str = ""
    anchor_position: str = "left"
    anchor_stability: float = 0.0

    # Advanced options
    fuzzy_enabled: bool = False
    fuzzy_accuracy: float = 0.8
    fuzzy_match_type: str = "contains"
    fuzzy_text: str = ""

    cv_enabled: bool = False
    cv_element_type: str = "Button"
    cv_text: str = ""
    cv_accuracy: float = 0.8

    image_enabled: bool = False
    image_template: bytes | None = None
    image_accuracy: float = 0.8

    # Healing context capture
    capture_fingerprint: bool = True
    capture_spatial: bool = True
    capture_cv_template: bool = False

    # History
    recent_selectors: list[str] = field(default_factory=list)

    def has_element(self) -> bool:
        """Check if an element is currently selected."""
        return bool(self.element_tag or self.element_html)

    def has_anchor(self) -> bool:
        """Check if an anchor is configured."""
        return self.anchor_enabled and bool(self.anchor_selector)

    def get_enabled_attributes(self) -> list[AttributeRow]:
        """Get list of enabled attribute rows."""
        return [row for row in self.attribute_rows if row.enabled]

    def get_best_selector(self) -> str | None:
        """Get the highest-scoring enabled selector."""
        enabled = self.get_enabled_attributes()
        if not enabled:
            return self.generated_selector or None

        # Return selector with highest score
        best = max(enabled, key=lambda r: r.score)
        return best.value

    def to_healing_context(self) -> dict[str, Any]:
        """Build healing context dict from current state."""
        context = {}

        if self.capture_fingerprint:
            context["fingerprint"] = {
                "tag": self.element_tag,
                "id": self.element_id,
                "classes": self.element_classes.copy(),
                "text": self.element_text[:100] if self.element_text else "",
                "attributes": {row.name: row.value for row in self.attribute_rows if row.enabled},
            }

        if self.capture_spatial and self.has_anchor():
            context["spatial"] = {
                "anchor_selector": self.anchor_selector,
                "anchor_text": self.anchor_text,
                "position": self.anchor_position,
            }

        if self.capture_cv_template and self.image_template:
            import base64

            context["cv_template"] = {
                "image_base64": base64.b64encode(self.image_template).decode("utf-8"),
            }

        return context

    def clear_element(self) -> None:
        """Clear current element state."""
        self.element_html = ""
        self.element_tag = ""
        self.element_id = ""
        self.element_classes = []
        self.element_text = ""
        self.element_properties = {}
        self.element_rect = None
        self.attribute_rows = []
        self.generated_selector = ""
        self.match_count = 0
        self.is_unique = False
        self.validation_status = ValidationStatus.PENDING

    def clear_anchor(self) -> None:
        """Clear anchor state."""
        self.anchor_enabled = False
        self.anchor_selector = ""
        self.anchor_tag = ""
        self.anchor_text = ""
        self.anchor_position = "left"
        self.anchor_stability = 0.0


class StateManager(QObject):
    """
    Manages ElementSelectorState with Qt signals for reactive updates.

    Widgets subscribe to specific state changes and update accordingly.

    Example:
        manager = StateManager()
        manager.element_changed.connect(preview_widget.update_preview)
        manager.set_element(tag="button", id="submit", ...)
    """

    # Signals for state changes
    state_changed = Signal()  # Any state change
    mode_changed = Signal(PickingMode)
    picking_changed = Signal(bool)
    element_changed = Signal()
    selector_changed = Signal(str)
    attributes_changed = Signal(list)  # List[AttributeRow]
    validation_changed = Signal(ValidationStatus, int)  # status, match_count
    anchor_changed = Signal()
    advanced_changed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._state = ElementSelectorState()
        self._observers: list[Callable[[ElementSelectorState], None]] = []

    @property
    def state(self) -> ElementSelectorState:
        """Get current state (read-only access)."""
        return self._state

    def set_mode(self, mode: PickingMode) -> None:
        """Set picking mode."""
        if self._state.mode != mode:
            self._state.mode = mode
            self.mode_changed.emit(mode)
            self.state_changed.emit()

    def set_picking(self, is_picking: bool) -> None:
        """Set picking state."""
        if self._state.is_picking != is_picking:
            self._state.is_picking = is_picking
            self.picking_changed.emit(is_picking)
            self.state_changed.emit()

    def set_element(
        self,
        html: str = "",
        tag: str = "",
        element_id: str = "",
        classes: list[str] | None = None,
        text: str = "",
        properties: dict[str, Any] | None = None,
        rect: dict[str, float] | None = None) -> None:
        """Set current element data."""
        self._state.element_html = html
        self._state.element_tag = tag
        self._state.element_id = element_id
        self._state.element_classes = classes or []
        self._state.element_text = text
        self._state.element_properties = properties or {}
        self._state.element_rect = rect

        self.element_changed.emit()
        self.state_changed.emit()

    def set_attributes(self, rows: list[AttributeRow]) -> None:
        """Set attribute rows."""
        self._state.attribute_rows = rows
        self.attributes_changed.emit(rows)
        self.state_changed.emit()

    def toggle_attribute(self, index: int) -> None:
        """Toggle enabled state of attribute row."""
        if 0 <= index < len(self._state.attribute_rows):
            row = self._state.attribute_rows[index]
            row.enabled = not row.enabled
            self.attributes_changed.emit(self._state.attribute_rows)
            self.state_changed.emit()

    def set_generated_selector(self, selector: str, selector_type: str = "css") -> None:
        """Set the generated selector."""
        self._state.generated_selector = selector
        self._state.selector_type = selector_type
        self.selector_changed.emit(selector)
        self.state_changed.emit()

    def set_validation(
        self,
        status: ValidationStatus,
        match_count: int = 0,
        time_ms: float = 0.0) -> None:
        """Set validation results."""
        self._state.validation_status = status
        self._state.match_count = match_count
        self._state.is_unique = match_count == 1
        self._state.validation_time_ms = time_ms
        self.validation_changed.emit(status, match_count)
        self.state_changed.emit()

    def set_anchor(
        self,
        enabled: bool = False,
        selector: str = "",
        tag: str = "",
        text: str = "",
        position: str = "left",
        stability: float = 0.0) -> None:
        """Set anchor data."""
        self._state.anchor_enabled = enabled
        self._state.anchor_selector = selector
        self._state.anchor_tag = tag
        self._state.anchor_text = text
        self._state.anchor_position = position
        self._state.anchor_stability = stability
        self.anchor_changed.emit()
        self.state_changed.emit()

    def clear_anchor(self) -> None:
        """Clear anchor."""
        self._state.clear_anchor()
        self.anchor_changed.emit()
        self.state_changed.emit()

    def clear_element(self) -> None:
        """Clear current element."""
        self._state.clear_element()
        self.element_changed.emit()
        self.attributes_changed.emit([])
        self.state_changed.emit()

    def add_to_history(self, selector: str) -> None:
        """Add selector to history (max 20 items)."""
        if selector and selector not in self._state.recent_selectors:
            self._state.recent_selectors.insert(0, selector)
            self._state.recent_selectors = self._state.recent_selectors[:20]

    def get_state_snapshot(self) -> ElementSelectorState:
        """Get a copy of current state."""
        import copy

        return copy.deepcopy(self._state)


__all__ = [
    "ElementSelectorState",
    "AttributeRow",
    "ValidationStatus",
    "PickingMode",
    "StateManager",
]
