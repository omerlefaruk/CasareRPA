"""
Anchor Configuration for Browser Nodes.

Defines the data structure for anchor-based element location.
Anchors are stable reference elements (labels, headings) used to
reliably find dynamic target elements relative to their position.
"""

from dataclasses import dataclass
from typing import Dict, Any
import json

from loguru import logger


@dataclass
class NodeAnchorConfig:
    """
    Configuration for anchor-based element location.

    Attributes:
        enabled: Whether to use anchor-based location
        selector: CSS/XPath selector for the anchor element
        position: Position of target relative to anchor (left, right, above, below, near)
        text: Display text of anchor (for UI preview)
        offset_x: Horizontal pixel offset from anchor to target
        offset_y: Vertical pixel offset from anchor to target
        tag_name: HTML tag of anchor element
        stability_score: 0.0-1.0 reliability score
    """

    enabled: bool = False
    selector: str = ""
    position: str = "near"  # left, right, above, below, near, inside
    text: str = ""
    offset_x: int = 0
    offset_y: int = 0
    tag_name: str = ""
    stability_score: float = 0.0

    @classmethod
    def from_json(cls, json_str: str) -> "NodeAnchorConfig":
        """
        Create config from JSON string.

        Args:
            json_str: JSON string or empty string

        Returns:
            NodeAnchorConfig instance
        """
        if not json_str or not json_str.strip():
            return cls()

        try:
            data = json.loads(json_str)
            return cls(
                enabled=data.get("enabled", False),
                selector=data.get("selector", ""),
                position=data.get("position", "near"),
                text=data.get("text", ""),
                offset_x=data.get("offset_x", 0),
                offset_y=data.get("offset_y", 0),
                tag_name=data.get("tag_name", ""),
                stability_score=data.get("stability_score", 0.0),
            )
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid anchor config JSON: {e}")
            return cls()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NodeAnchorConfig":
        """
        Create config from dictionary.

        Args:
            data: Dictionary with anchor config fields

        Returns:
            NodeAnchorConfig instance
        """
        if not data:
            return cls()

        return cls(
            enabled=data.get("enabled", False),
            selector=data.get("selector", ""),
            position=data.get("position", "near"),
            text=data.get("text", ""),
            offset_x=data.get("offset_x", 0),
            offset_y=data.get("offset_y", 0),
            tag_name=data.get("tag_name", ""),
            stability_score=data.get("stability_score", 0.0),
        )

    def to_json(self) -> str:
        """
        Convert config to JSON string.

        Returns:
            JSON string representation
        """
        if not self.enabled and not self.selector:
            return ""

        return json.dumps(self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert config to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "enabled": self.enabled,
            "selector": self.selector,
            "position": self.position,
            "text": self.text,
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
            "tag_name": self.tag_name,
            "stability_score": self.stability_score,
        }

    @property
    def is_valid(self) -> bool:
        """Check if config has valid anchor data."""
        return self.enabled and bool(self.selector)

    @property
    def display_text(self) -> str:
        """Get human-readable display text."""
        if not self.selector:
            return "No anchor"

        if self.text:
            return (
                f'{self.tag_name or "element"}: "{self.text[:30]}..."'
                if len(self.text) > 30
                else f'{self.tag_name or "element"}: "{self.text}"'
            )

        return self.selector[:50] + "..." if len(self.selector) > 50 else self.selector

    def __bool__(self) -> bool:
        """Return True if anchor is enabled and has selector."""
        return self.is_valid
