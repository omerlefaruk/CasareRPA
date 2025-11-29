"""
Anchor-Based Selector Healing Models.

Defines data structures for spatial relationship detection and anchor-based healing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class SpatialRelation(Enum):
    """
    Spatial relationships between elements.

    Used to describe the position of a target element relative to an anchor.
    """

    NEAR = "near"
    """Target is within close proximity (configurable threshold)."""

    ABOVE = "above"
    """Target is above the anchor element."""

    BELOW = "below"
    """Target is below the anchor element."""

    LEFT_OF = "left-of"
    """Target is to the left of the anchor element."""

    RIGHT_OF = "right-of"
    """Target is to the right of the anchor element."""

    INSIDE = "inside"
    """Target is contained within the anchor element."""

    CONTAINS = "contains"
    """Target contains the anchor element."""

    ADJACENT = "adjacent"
    """Target is immediately adjacent (DOM sibling)."""


@dataclass
class BoundingRect:
    """
    Bounding rectangle of an element.

    Represents the position and size of an element in the viewport.
    """

    x: float
    """X coordinate of the top-left corner."""

    y: float
    """Y coordinate of the top-left corner."""

    width: float
    """Width of the element."""

    height: float
    """Height of the element."""

    @property
    def center_x(self) -> float:
        """Get the X coordinate of the center."""
        return self.x + (self.width / 2)

    @property
    def center_y(self) -> float:
        """Get the Y coordinate of the center."""
        return self.y + (self.height / 2)

    @property
    def right(self) -> float:
        """Get the X coordinate of the right edge."""
        return self.x + self.width

    @property
    def bottom(self) -> float:
        """Get the Y coordinate of the bottom edge."""
        return self.y + self.height

    def distance_to(self, other: BoundingRect) -> float:
        """
        Calculate the distance between centers of two rectangles.

        Args:
            other: Another bounding rectangle.

        Returns:
            Euclidean distance between centers.
        """
        dx = self.center_x - other.center_x
        dy = self.center_y - other.center_y
        return (dx**2 + dy**2) ** 0.5

    def edge_distance_to(self, other: BoundingRect) -> float:
        """
        Calculate the minimum distance between edges of two rectangles.

        Args:
            other: Another bounding rectangle.

        Returns:
            Minimum edge-to-edge distance (0 if overlapping).
        """
        dx = max(0, max(self.x - other.right, other.x - self.right))
        dy = max(0, max(self.y - other.bottom, other.y - self.bottom))
        return (dx**2 + dy**2) ** 0.5

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> BoundingRect:
        """Create from dictionary."""
        return cls(
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 0.0),
            height=data.get("height", 0.0),
        )

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }


@dataclass
class AnchorElement:
    """
    Represents a stable anchor element for relative positioning.

    Anchors are elements that are unlikely to change (labels, headings, logos)
    and can be used to locate nearby target elements.
    """

    selector: str
    """Playwright-compatible selector for this anchor."""

    tag_name: str
    """HTML tag name."""

    text_content: str
    """Visible text content (for labels, headings)."""

    rect: BoundingRect
    """Bounding rectangle of the anchor."""

    stability_score: float
    """Score indicating how stable this anchor is (0.0-1.0)."""

    attributes: Dict[str, str] = field(default_factory=dict)
    """Key attributes (id, data-testid, aria-label, etc.)."""

    is_landmark: bool = False
    """Whether this element is an ARIA landmark."""

    @property
    def is_stable(self) -> bool:
        """Check if this anchor is considered stable."""
        return self.stability_score >= 0.7

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "selector": self.selector,
            "tag_name": self.tag_name,
            "text_content": self.text_content,
            "rect": self.rect.to_dict(),
            "stability_score": self.stability_score,
            "attributes": self.attributes,
            "is_landmark": self.is_landmark,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AnchorElement:
        """Create from dictionary."""
        return cls(
            selector=data.get("selector", ""),
            tag_name=data.get("tag_name", ""),
            text_content=data.get("text_content", ""),
            rect=BoundingRect.from_dict(data.get("rect", {})),
            stability_score=data.get("stability_score", 0.0),
            attributes=data.get("attributes", {}),
            is_landmark=data.get("is_landmark", False),
        )


@dataclass
class SpatialContext:
    """
    Describes the spatial context of a target element relative to anchors.

    Captures multiple anchor relationships that can be used to relocate
    the target when its primary selector fails.
    """

    anchor_relations: List[Tuple[AnchorElement, SpatialRelation, float]]
    """List of (anchor, relation, distance) tuples."""

    dom_path: str
    """Relative DOM path from nearest structural landmark."""

    visual_quadrant: str
    """Screen quadrant: 'top-left', 'top-right', 'bottom-left', 'bottom-right'."""

    container_selector: Optional[str] = None
    """Selector for the containing section/form/article."""

    def get_best_anchor(self) -> Optional[Tuple[AnchorElement, SpatialRelation, float]]:
        """
        Get the most reliable anchor relationship.

        Returns:
            Tuple of (anchor, relation, distance) or None.
        """
        if not self.anchor_relations:
            return None

        # Sort by anchor stability descending, then by distance ascending
        sorted_relations = sorted(
            self.anchor_relations, key=lambda r: (-r[0].stability_score, r[2])
        )
        return sorted_relations[0]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "anchor_relations": [
                {
                    "anchor": anchor.to_dict(),
                    "relation": relation.value,
                    "distance": distance,
                }
                for anchor, relation, distance in self.anchor_relations
            ],
            "dom_path": self.dom_path,
            "visual_quadrant": self.visual_quadrant,
            "container_selector": self.container_selector,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SpatialContext:
        """Create from dictionary."""
        relations = []
        for rel_data in data.get("anchor_relations", []):
            anchor = AnchorElement.from_dict(rel_data.get("anchor", {}))
            relation = SpatialRelation(rel_data.get("relation", "near"))
            distance = rel_data.get("distance", 0.0)
            relations.append((anchor, relation, distance))

        return cls(
            anchor_relations=relations,
            dom_path=data.get("dom_path", ""),
            visual_quadrant=data.get("visual_quadrant", ""),
            container_selector=data.get("container_selector"),
        )


@dataclass
class AnchorHealingResult:
    """
    Result of an anchor-based healing attempt.

    Contains the healed selector and metadata about the healing process.
    """

    success: bool
    """Whether healing was successful."""

    original_selector: str
    """The original selector that failed."""

    healed_selector: str
    """The healed selector (if successful)."""

    confidence: float
    """Confidence score (0.0 to 1.0)."""

    anchor_used: Optional[AnchorElement] = None
    """The anchor element used for healing."""

    relation_used: Optional[SpatialRelation] = None
    """The spatial relation used."""

    strategy: str = "anchor"
    """Healing strategy identifier."""

    candidates: List[Tuple[str, float]] = field(default_factory=list)
    """Alternative selectors with confidence scores."""

    healing_time_ms: float = 0.0
    """Time taken for healing in milliseconds."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "original_selector": self.original_selector,
            "healed_selector": self.healed_selector,
            "confidence": self.confidence,
            "anchor_used": self.anchor_used.to_dict() if self.anchor_used else None,
            "relation_used": self.relation_used.value if self.relation_used else None,
            "strategy": self.strategy,
            "candidates": self.candidates,
            "healing_time_ms": self.healing_time_ms,
        }


__all__ = [
    "SpatialRelation",
    "BoundingRect",
    "AnchorElement",
    "SpatialContext",
    "AnchorHealingResult",
]
