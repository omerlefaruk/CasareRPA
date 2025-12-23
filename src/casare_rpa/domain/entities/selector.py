"""
Canonical Selector Model for CasareRPA.

Supports both browser (XPath, CSS, ARIA) and desktop (UIA) targets.
Used for unified element identification and self-healing.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SelectorTarget(Enum):
    """Target environment for the selector"""

    BROWSER = "browser"
    DESKTOP = "desktop"
    MOBILE = "mobile"  # For future expansion
    JAVA = "java"  # For future expansion


class SelectorType(Enum):
    """Types of selectors supported by CasareRPA"""

    # Browser types
    XPATH = "xpath"
    CSS = "css"
    ARIA = "aria"
    TEXT = "text"
    DATA_ATTR = "data_attr"

    # Desktop types (UIA)
    UIA_NAME = "name"
    UIA_AUTOMATION_ID = "automation_id"
    UIA_CLASS_NAME = "class_name"
    UIA_CONTROL_TYPE = "control_type"
    UIA_XPATH = "xpath_desktop"  # Desktop-specific XPath

    # Generic
    IMAGE = "image"  # Computer Vision fallback
    OCR = "ocr"  # Text-based visual search


@dataclass
class SelectorStrategy:
    """A single selector strategy with metadata"""

    selector_type: SelectorType
    value: str
    target: SelectorTarget = SelectorTarget.BROWSER
    score: float = 0.0  # 0-100, higher is better
    is_unique: bool = False
    execution_time_ms: float = 0.0
    last_validated: float | None = None
    failure_count: int = 0

    def __lt__(self, other):
        """Compare by score for sorting"""
        return self.score < other.score


@dataclass
class ElementFingerprint:
    """
    Stores multiple selector strategies for self-healing.
    Used to identify the same UI element across different versions of an application.
    """

    target: SelectorTarget
    tag_name: str  # HTML tag or Desktop ControlType
    element_id: str | None = None
    name: str | None = None
    class_names: list[str] = field(default_factory=list)
    text_content: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)

    # Multiple selector strategies ranked by reliability
    selectors: list[SelectorStrategy] = field(default_factory=list)

    # Visual/structural fingerprint
    rect: dict[str, float] = field(default_factory=dict)
    parent_info: dict[str, Any] | None = None
    sibling_count: int = 0

    # Screenshot of the element (optional, for validation/debug)
    screenshot_path: str | None = None

    def get_primary_selector(self) -> SelectorStrategy | None:
        """Get the best selector strategy"""
        if not self.selectors:
            return None
        # Sort by score descending, then by failure count ascending
        return sorted(self.selectors, key=lambda s: (-s.score, s.failure_count))[0]

    def get_fallback_selectors(self) -> list[SelectorStrategy]:
        """Get all selectors except primary, sorted by reliability"""
        if len(self.selectors) <= 1:
            return []
        sorted_selectors = sorted(self.selectors, key=lambda s: (-s.score, s.failure_count))
        return sorted_selectors[1:]

    def promote_selector(self, selector: SelectorStrategy):
        """Promote a working fallback selector"""
        if selector in self.selectors:
            selector.score = min(100.0, selector.score + 10.0)
            selector.failure_count = 0

    def demote_selector(self, selector: SelectorStrategy):
        """Demote a failing selector"""
        if selector in self.selectors:
            selector.failure_count += 1
            selector.score = max(0.0, selector.score - 5.0)

    def to_dict(self) -> dict[str, Any]:
        """Convert fingerprint to dictionary for serialization"""
        return {
            "target": self.target.value,
            "tag_name": self.tag_name,
            "element_id": self.element_id,
            "name": self.name,
            "class_names": self.class_names,
            "text_content": self.text_content,
            "attributes": self.attributes,
            "rect": self.rect,
            "selectors": [
                {
                    "type": s.selector_type.value,
                    "value": s.value,
                    "score": s.score,
                    "is_unique": s.is_unique,
                }
                for s in self.selectors
            ],
            "parent_info": self.parent_info,
            "sibling_count": self.sibling_count,
        }
