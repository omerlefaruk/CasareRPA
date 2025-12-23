"""
Anchor Model for UI Explorer.

Defines data structures for UiPath-style anchor-based element location.
Anchors are stable reference elements used to reliably locate target elements
even when the UI changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from loguru import logger
from PySide6.QtCore import QObject, Signal


class AnchorPosition(Enum):
    """
    Position of target relative to anchor element.

    Describes where the target element is located relative to the anchor.
    """

    LEFT = "left"
    """Target is to the left of the anchor."""

    RIGHT = "right"
    """Target is to the right of the anchor."""

    ABOVE = "above"
    """Target is above the anchor."""

    BELOW = "below"
    """Target is below the anchor."""

    INSIDE = "inside"
    """Target is inside/contained by the anchor."""

    NEAR = "near"
    """Target is nearby but no specific direction."""


class AnchorStrategy(Enum):
    """
    Strategy for using anchors in element location.
    """

    NONE = "none"
    """No anchor - use primary selector only."""

    SINGLE = "single"
    """Use a single anchor element."""

    MULTI = "multi"
    """Use multiple anchors for redundancy."""

    AUTO = "auto"
    """Auto-detect the best anchor strategy."""


@dataclass
class AnchorElementData:
    """
    Data representing an anchor element.

    Captures all information needed to locate and use an anchor element
    for reliable target element location.
    """

    selector: str
    """CSS/XPath selector for the anchor element."""

    position: AnchorPosition
    """Position of target relative to this anchor."""

    tag_name: str = ""
    """HTML tag name (e.g., 'label', 'h2', 'span')."""

    text_content: str = ""
    """Visible text content of the anchor."""

    offset_x: int = 0
    """Horizontal offset in pixels from anchor to target."""

    offset_y: int = 0
    """Vertical offset in pixels from anchor to target."""

    attributes: dict[str, str] = field(default_factory=dict)
    """Element attributes (id, class, data-testid, etc.)."""

    fingerprint: dict[str, Any] | None = None
    """Element fingerprint for healing/matching."""

    stability_score: float = 0.0
    """Stability score 0.0-1.0 indicating anchor reliability."""

    @property
    def display_name(self) -> str:
        """Get human-readable display name for the anchor."""
        if self.text_content:
            text = self.text_content[:30]
            if len(self.text_content) > 30:
                text += "..."
            return f"{self.tag_name}: {text}"
        if self.attributes.get("id"):
            return f"{self.tag_name}#{self.attributes['id']}"
        return self.tag_name or "unknown"

    @property
    def is_stable(self) -> bool:
        """Check if anchor is considered stable (>= 0.7 score)."""
        return self.stability_score >= 0.7

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "selector": self.selector,
            "position": self.position.value,
            "tag_name": self.tag_name,
            "text_content": self.text_content,
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
            "attributes": self.attributes.copy(),
            "fingerprint": self.fingerprint,
            "stability_score": self.stability_score,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnchorElementData:
        """Create from dictionary."""
        position_str = data.get("position", "near")
        try:
            position = AnchorPosition(position_str)
        except ValueError:
            position = AnchorPosition.NEAR

        return cls(
            selector=data.get("selector", ""),
            position=position,
            tag_name=data.get("tag_name", ""),
            text_content=data.get("text_content", ""),
            offset_x=data.get("offset_x", 0),
            offset_y=data.get("offset_y", 0),
            attributes=data.get("attributes", {}),
            fingerprint=data.get("fingerprint"),
            stability_score=data.get("stability_score", 0.0),
        )


@dataclass
class AnchorConfiguration:
    """
    Complete anchor configuration for a target element.

    Combines anchor strategy with one or more anchor elements.
    """

    strategy: AnchorStrategy
    """The anchor strategy to use."""

    anchors: list[AnchorElementData] = field(default_factory=list)
    """List of anchor elements (may be empty for NONE strategy)."""

    auto_detected: bool = False
    """Whether anchors were auto-detected vs manually picked."""

    confidence: float = 0.0
    """Overall confidence in the anchor configuration."""

    @property
    def has_anchor(self) -> bool:
        """Check if any anchor is configured."""
        return len(self.anchors) > 0

    @property
    def primary_anchor(self) -> AnchorElementData | None:
        """Get the primary (first) anchor if available."""
        return self.anchors[0] if self.anchors else None

    def add_anchor(self, anchor: AnchorElementData) -> None:
        """Add an anchor element."""
        self.anchors.append(anchor)
        self._recalculate_confidence()

    def remove_anchor(self, index: int) -> bool:
        """Remove anchor at index. Returns True if removed."""
        if 0 <= index < len(self.anchors):
            self.anchors.pop(index)
            self._recalculate_confidence()
            return True
        return False

    def clear_anchors(self) -> None:
        """Remove all anchors."""
        self.anchors.clear()
        self.confidence = 0.0

    def _recalculate_confidence(self) -> None:
        """Recalculate overall confidence based on anchors."""
        if not self.anchors:
            self.confidence = 0.0
            return

        # Average stability scores weighted by position
        total = sum(a.stability_score for a in self.anchors)
        self.confidence = total / len(self.anchors)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "strategy": self.strategy.value,
            "anchors": [a.to_dict() for a in self.anchors],
            "auto_detected": self.auto_detected,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnchorConfiguration:
        """Create from dictionary."""
        strategy_str = data.get("strategy", "none")
        try:
            strategy = AnchorStrategy(strategy_str)
        except ValueError:
            strategy = AnchorStrategy.NONE

        anchors = [AnchorElementData.from_dict(a) for a in data.get("anchors", [])]

        return cls(
            strategy=strategy,
            anchors=anchors,
            auto_detected=data.get("auto_detected", False),
            confidence=data.get("confidence", 0.0),
        )


class AnchorModel(QObject):
    """
    Qt model for managing anchor state in UI Explorer.

    Provides signals for reactive UI updates and methods for
    anchor manipulation.

    Signals:
        changed: Emitted when any anchor configuration changes
        anchor_added: Emitted when an anchor is added (index)
        anchor_removed: Emitted when an anchor is removed (index)
        strategy_changed: Emitted when strategy changes (strategy)
    """

    changed = Signal()
    anchor_added = Signal(int)  # index
    anchor_removed = Signal(int)  # index
    strategy_changed = Signal(str)  # strategy value

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize the anchor model."""
        super().__init__(parent)
        self._config = AnchorConfiguration(strategy=AnchorStrategy.NONE)
        self._is_picking = False

    @property
    def configuration(self) -> AnchorConfiguration:
        """Get the current anchor configuration."""
        return self._config

    @property
    def strategy(self) -> AnchorStrategy:
        """Get the current anchor strategy."""
        return self._config.strategy

    @strategy.setter
    def strategy(self, value: AnchorStrategy) -> None:
        """Set the anchor strategy."""
        if self._config.strategy != value:
            self._config.strategy = value
            self.strategy_changed.emit(value.value)
            self.changed.emit()

    @property
    def has_anchor(self) -> bool:
        """Check if any anchor is configured."""
        return self._config.has_anchor

    @property
    def anchors(self) -> list[AnchorElementData]:
        """Get list of anchor elements."""
        return self._config.anchors

    @property
    def primary_anchor(self) -> AnchorElementData | None:
        """Get the primary anchor."""
        return self._config.primary_anchor

    @property
    def is_picking(self) -> bool:
        """Check if anchor picking mode is active."""
        return self._is_picking

    @is_picking.setter
    def is_picking(self, value: bool) -> None:
        """Set anchor picking mode state."""
        self._is_picking = value

    def set_anchor(self, anchor: AnchorElementData) -> None:
        """
        Set a single anchor (replaces any existing).

        Args:
            anchor: The anchor element to set
        """
        self._config.anchors = [anchor]
        self._config.strategy = AnchorStrategy.SINGLE
        self._config._recalculate_confidence()
        self.anchor_added.emit(0)
        self.strategy_changed.emit(AnchorStrategy.SINGLE.value)
        self.changed.emit()
        logger.debug(f"Anchor set: {anchor.display_name}")

    def add_anchor(self, anchor: AnchorElementData) -> int:
        """
        Add an anchor element.

        Args:
            anchor: The anchor element to add

        Returns:
            Index of the added anchor
        """
        index = len(self._config.anchors)
        self._config.add_anchor(anchor)

        # Auto-adjust strategy
        if len(self._config.anchors) == 1:
            self._config.strategy = AnchorStrategy.SINGLE
        else:
            self._config.strategy = AnchorStrategy.MULTI

        self.anchor_added.emit(index)
        self.strategy_changed.emit(self._config.strategy.value)
        self.changed.emit()
        logger.debug(f"Anchor added at index {index}: {anchor.display_name}")
        return index

    def remove_anchor(self, index: int) -> bool:
        """
        Remove an anchor at index.

        Args:
            index: Index of anchor to remove

        Returns:
            True if removed successfully
        """
        if self._config.remove_anchor(index):
            # Auto-adjust strategy
            if len(self._config.anchors) == 0:
                self._config.strategy = AnchorStrategy.NONE
            elif len(self._config.anchors) == 1:
                self._config.strategy = AnchorStrategy.SINGLE

            self.anchor_removed.emit(index)
            self.strategy_changed.emit(self._config.strategy.value)
            self.changed.emit()
            logger.debug(f"Anchor removed at index {index}")
            return True
        return False

    def clear(self) -> None:
        """Clear all anchors."""
        count = len(self._config.anchors)
        self._config.clear_anchors()
        self._config.strategy = AnchorStrategy.NONE

        for i in range(count - 1, -1, -1):
            self.anchor_removed.emit(i)

        self.strategy_changed.emit(AnchorStrategy.NONE.value)
        self.changed.emit()
        logger.debug("All anchors cleared")

    def load_from_dict(self, data: dict[str, Any]) -> None:
        """
        Load anchor configuration from dictionary.

        Args:
            data: Dictionary with anchor configuration
        """
        self._config = AnchorConfiguration.from_dict(data)
        self.changed.emit()
        logger.debug(f"Loaded anchor config with {len(self._config.anchors)} anchors")

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation of anchor configuration
        """
        return self._config.to_dict()

    def update_position(
        self,
        index: int,
        position: AnchorPosition,
        offset_x: int = 0,
        offset_y: int = 0,
    ) -> bool:
        """
        Update anchor position settings.

        Args:
            index: Anchor index
            position: New position
            offset_x: Horizontal offset
            offset_y: Vertical offset

        Returns:
            True if updated successfully
        """
        if 0 <= index < len(self._config.anchors):
            anchor = self._config.anchors[index]
            anchor.position = position
            anchor.offset_x = offset_x
            anchor.offset_y = offset_y
            self.changed.emit()
            return True
        return False


# Convenience constants for common anchor tags
STABLE_ANCHOR_TAGS = frozenset(
    [
        "label",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "legend",
        "caption",
        "figcaption",
        "th",
    ]
)

LANDMARK_ROLES = frozenset(
    [
        "banner",
        "navigation",
        "main",
        "complementary",
        "contentinfo",
        "search",
        "form",
        "region",
    ]
)


def calculate_anchor_stability(
    tag_name: str,
    attributes: dict[str, str],
    text_content: str,
) -> float:
    """
    Calculate stability score for a potential anchor element.

    Args:
        tag_name: HTML tag name
        attributes: Element attributes
        text_content: Visible text content

    Returns:
        Stability score 0.0-1.0
    """
    score = 0.0

    # Tag-based stability
    tag_lower = tag_name.lower()
    if tag_lower in ("label", "legend"):
        score += 0.30
    elif tag_lower in ("h1", "h2", "h3"):
        score += 0.25
    elif tag_lower in ("h4", "h5", "h6", "th", "caption"):
        score += 0.20
    elif tag_lower in ("figcaption",):
        score += 0.15
    else:
        score += 0.05

    # Attribute-based stability
    if attributes.get("id"):
        score += 0.20
    if attributes.get("data-testid"):
        score += 0.25
    if attributes.get("aria-label"):
        score += 0.15
    if attributes.get("for"):
        score += 0.20  # label[for] is very reliable
    if attributes.get("role") in LANDMARK_ROLES:
        score += 0.15

    # Text content stability
    if text_content:
        text_len = len(text_content.strip())
        if 2 < text_len < 50:
            score += 0.15  # Reasonable text length
        elif text_len >= 50:
            score += 0.05  # Long text is less reliable

    return min(1.0, score)


__all__ = [
    "AnchorPosition",
    "AnchorStrategy",
    "AnchorElementData",
    "AnchorConfiguration",
    "AnchorModel",
    "STABLE_ANCHOR_TAGS",
    "LANDMARK_ROLES",
    "calculate_anchor_stability",
]
