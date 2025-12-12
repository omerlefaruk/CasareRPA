"""
CasareRPA - Position Value Object

Immutable 2D position for node placement in workflow canvas.
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class Position:
    """
    Immutable 2D position value object.

    Used for node placement in workflow canvas.
    Being frozen ensures positions are hashable and can't be accidentally mutated.

    Attributes:
        x: X coordinate (horizontal position)
        y: Y coordinate (vertical position)
    """

    x: float
    y: float

    def move(self, dx: float, dy: float) -> "Position":
        """
        Create a new position moved by delta values.

        Args:
            dx: Delta X (horizontal movement)
            dy: Delta Y (vertical movement)

        Returns:
            New Position with updated coordinates
        """
        return Position(self.x + dx, self.y + dy)

    def distance_to(self, other: "Position") -> float:
        """
        Calculate Euclidean distance to another position.

        Args:
            other: Target position

        Returns:
            Distance between positions
        """
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def to_dict(self) -> Dict[str, float]:
        """
        Serialize to dictionary.

        Returns:
            Dictionary with x and y coordinates
        """
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Position":
        """
        Create Position from dictionary.

        Args:
            data: Dictionary with x and y keys

        Returns:
            Position instance
        """
        return cls(x=float(data.get("x", 0)), y=float(data.get("y", 0)))

    @classmethod
    def origin(cls) -> "Position":
        """Create position at origin (0, 0)."""
        return cls(x=0.0, y=0.0)

    def __str__(self) -> str:
        """Human-readable representation."""
        return f"({self.x}, {self.y})"


__all__ = ["Position"]
