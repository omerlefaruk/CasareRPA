"""
Base Tab for Unified Selector Dialog.

Abstract base class defining the interface for all selector tabs.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

if TYPE_CHECKING:
    from playwright.async_api import Page


@dataclass
class AnchorData:
    """Anchor data for reliable element location."""

    selector: str
    """CSS/XPath selector for anchor element."""

    position: str
    """Position of target relative to anchor: left, right, above, below, inside, near."""

    tag_name: str = ""
    """HTML tag name of anchor element."""

    text_content: str = ""
    """Visible text content of anchor."""

    stability_score: float = 0.0
    """Stability score 0.0-1.0."""

    attributes: dict[str, str] = field(default_factory=dict)
    """Anchor element attributes."""

    offset_x: int = 0
    """Horizontal offset in pixels from anchor to target."""

    offset_y: int = 0
    """Vertical offset in pixels from anchor to target."""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "selector": self.selector,
            "position": self.position,
            "tag_name": self.tag_name,
            "text_content": self.text_content,
            "stability_score": self.stability_score,
            "attributes": self.attributes.copy(),
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnchorData":
        """Create from dictionary."""
        return cls(
            selector=data.get("selector", ""),
            position=data.get("position", "near"),
            tag_name=data.get("tag_name", ""),
            text_content=data.get("text_content", ""),
            stability_score=data.get("stability_score", 0.0),
            attributes=data.get("attributes", {}),
            offset_x=data.get("offset_x", 0),
            offset_y=data.get("offset_y", 0),
        )


@dataclass
class SelectorResult:
    """Result from selector tab."""

    selector_value: str
    """The selector string."""

    selector_type: str
    """Type: css, xpath, aria, automation_id, ocr, image, etc."""

    confidence: float
    """Confidence score 0.0-1.0."""

    is_unique: bool = True
    """Whether selector matches exactly one element."""

    healing_context: dict[str, Any] = field(default_factory=dict)
    """Optional healing context for runtime resilience."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata (element info, match details, etc.)."""

    anchor: AnchorData | None = None
    """Optional anchor element for reliable location."""

    fallback_selectors: list[str] = field(default_factory=list)
    """Fallback selectors to try if primary fails."""

    def has_anchor(self) -> bool:
        """Check if an anchor is configured."""
        return self.anchor is not None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "selector_value": self.selector_value,
            "selector_type": self.selector_type,
            "confidence": self.confidence,
            "is_unique": self.is_unique,
            "healing_context": self.healing_context,
            "metadata": self.metadata,
            "fallback_selectors": self.fallback_selectors,
        }
        if self.anchor:
            result["anchor"] = self.anchor.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SelectorResult":
        """Create from dictionary."""
        anchor = None
        if data.get("anchor"):
            anchor = AnchorData.from_dict(data["anchor"])

        return cls(
            selector_value=data.get("selector_value", ""),
            selector_type=data.get("selector_type", "css"),
            confidence=data.get("confidence", 0.0),
            is_unique=data.get("is_unique", True),
            healing_context=data.get("healing_context", {}),
            metadata=data.get("metadata", {}),
            anchor=anchor,
            fallback_selectors=data.get("fallback_selectors", []),
        )


@dataclass
class SelectorStrategy:
    """A generated selector strategy with metadata."""

    value: str
    """Selector value."""

    selector_type: str
    """Type of selector."""

    score: float
    """Reliability score 0-100."""

    is_unique: bool = False
    """Validated as unique."""

    description: str = ""
    """Human-readable description."""


class BaseSelectorTab(QWidget):
    """
    Abstract base class for selector dialog tabs.

    Each tab implements a different selection method:
    - Browser: CSS/XPath/ARIA selectors
    - Desktop: AutomationId/Name/Path selectors
    - OCR: Text-based finding
    - Image: Template matching

    Signals:
        selector_picked: Emitted when user picks a selector
        selectors_generated: Emitted when selector strategies are generated
        status_changed: Emitted when status message changes
    """

    # Signals
    selector_picked = Signal(object)  # SelectorResult
    selectors_generated = Signal(list)  # List[SelectorStrategy]
    status_changed = Signal(str)  # Status message

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_result: SelectorResult | None = None
        self._strategies: list[SelectorStrategy] = []
        self._is_active = False

    @property
    def tab_name(self) -> str:
        """Display name for the tab."""
        raise NotImplementedError("Subclass must implement tab_name")

    @property
    def tab_icon(self) -> str:
        """Icon emoji for the tab."""
        raise NotImplementedError("Subclass must implement tab_icon")

    def setup_ui(self) -> None:
        """Setup the tab UI. Called by subclass __init__."""
        raise NotImplementedError("Subclass must implement setup_ui")

    async def start_picking(self) -> None:
        """
        Start element picking mode.

        Should activate whatever picking mechanism is appropriate
        (browser overlay, desktop overlay, etc.)
        """
        raise NotImplementedError("Subclass must implement start_picking")

    async def stop_picking(self) -> None:
        """Stop element picking mode."""
        raise NotImplementedError("Subclass must implement stop_picking")

    def get_current_selector(self) -> SelectorResult | None:
        """Get the currently selected/configured selector."""
        raise NotImplementedError("Subclass must implement get_current_selector")

    def get_strategies(self) -> list[SelectorStrategy]:
        """Get all generated selector strategies."""
        raise NotImplementedError("Subclass must implement get_strategies")

    def set_active(self, active: bool) -> None:
        """Called when tab becomes active/inactive."""
        self._is_active = active

    @property
    def is_active(self) -> bool:
        """Whether this tab is currently active."""
        return self._is_active

    def set_browser_page(self, page: "Page") -> None:
        """
        Set the browser page for browser-related operations.

        Override in tabs that need browser access.
        """
        pass

    def set_target_node(self, node: Any, property_name: str) -> None:
        """
        Set target node for auto-pasting selector.

        Args:
            node: Visual node to update
            property_name: Property to set (e.g., "selector")
        """
        pass

    def validate_selector(self, selector: str, selector_type: str) -> dict[str, Any]:
        """
        Validate a selector and return results.

        Override in subclasses for specific validation logic.

        Returns:
            Dict with keys: success, count, time_ms, error
        """
        return {"success": False, "error": "Not implemented"}

    async def test_selector(self, selector: str, selector_type: str) -> dict[str, Any]:
        """
        Test selector against current context (browser page, desktop, etc.)

        Override in subclasses.

        Returns:
            Dict with keys: success, count, time_ms, error
        """
        return {"success": False, "error": "Not implemented"}

    async def highlight_selector(self, selector: str, selector_type: str) -> bool:
        """
        Highlight elements matching selector.

        Override in subclasses.

        Returns:
            True if highlighting was successful.
        """
        return False

    def clear(self) -> None:
        """Clear current selection and UI state."""
        self._current_result = None
        self._strategies = []

    def _emit_status(self, message: str) -> None:
        """Emit status change signal."""
        self.status_changed.emit(message)
