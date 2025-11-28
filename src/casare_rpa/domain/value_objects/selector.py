"""
CasareRPA - Domain Value Object: Selector

Smart selector system with multi-attribute fallback strategies.
Used for resilient element location in browser automation.

This is PURE domain - no infrastructure dependencies:
- Serializable via Pydantic
- Immutable value objects
- No async/await
- No Playwright/browser operations
"""

from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class SelectorStrategy(str, Enum):
    """Selector strategy types ordered by reliability."""

    DATA_TESTID = "data-testid"  # Highest priority - semantic identifier
    ID = "id"  # High priority - unique identifier
    ARIA_LABEL = "aria-label"  # Medium priority - accessibility
    TEXT = "text"  # Medium priority - visible text
    PLACEHOLDER = "placeholder"  # Medium priority - input hint
    ROLE = "role"  # Low priority - semantic role
    CLASS = "class"  # Low priority - styling-based
    XPATH = "xpath"  # Lowest priority - structural


class SelectorAttribute(BaseModel):
    """
    Single selector attribute with strategy and value.

    Example:
        SelectorAttribute(
            strategy=SelectorStrategy.DATA_TESTID,
            value="submit-button"
        )
    """

    strategy: SelectorStrategy = Field(..., description="Selector strategy type")
    value: str = Field(..., description="Selector value")

    class Config:
        frozen = True  # Immutable


class SmartSelector(BaseModel):
    """
    Multi-attribute selector with fallback strategies.

    Provides tier-1 healing by trying multiple attributes in priority order.

    Example:
        SmartSelector(
            id="btn-submit",
            primary=SelectorAttribute(
                strategy=SelectorStrategy.DATA_TESTID,
                value="submit-button"
            ),
            fallbacks=[
                SelectorAttribute(strategy=SelectorStrategy.ID, value="btnSubmit"),
                SelectorAttribute(strategy=SelectorStrategy.TEXT, value="Submit"),
                SelectorAttribute(strategy=SelectorStrategy.CLASS, value="btn-primary")
            ]
        )
    """

    # Identity
    id: str = Field(..., description="Unique selector ID")
    name: Optional[str] = Field(None, description="Human-readable name")

    # Selector attributes
    primary: SelectorAttribute = Field(
        ..., description="Primary selector (highest priority)"
    )
    fallbacks: List[SelectorAttribute] = Field(
        default_factory=list, description="Fallback selectors in priority order"
    )

    # Frame/shadow DOM context
    frame_path: Optional[List[str]] = Field(
        None, description="Path through iframes (selector for each level)"
    )
    shadow_root_path: Optional[List[str]] = Field(
        None, description="Path through shadow roots (selector for each host)"
    )

    # Metadata
    description: Optional[str] = Field(None, description="Selector description")
    tags: List[str] = Field(
        default_factory=list, description="Selector tags for organization"
    )

    class Config:
        frozen = False  # Allow updates for healing
        validate_assignment = True

    def get_all_attributes(self) -> List[SelectorAttribute]:
        """Get all selector attributes in priority order."""
        return [self.primary] + self.fallbacks

    def to_playwright_selector(
        self, strategy: Optional[SelectorStrategy] = None
    ) -> str:
        """
        Convert to Playwright selector string.

        Args:
            strategy: Specific strategy to use, or None for primary

        Returns:
            Playwright selector string
        """
        if strategy is None:
            attr = self.primary
        else:
            attr = next(
                (a for a in self.get_all_attributes() if a.strategy == strategy),
                self.primary,
            )

        match attr.strategy:
            case SelectorStrategy.DATA_TESTID:
                return f"[data-testid='{attr.value}']"
            case SelectorStrategy.ID:
                return f"#{attr.value}"
            case SelectorStrategy.ARIA_LABEL:
                return f"[aria-label='{attr.value}']"
            case SelectorStrategy.TEXT:
                return f"text='{attr.value}'"
            case SelectorStrategy.PLACEHOLDER:
                return f"[placeholder='{attr.value}']"
            case SelectorStrategy.ROLE:
                return f"role={attr.value}"
            case SelectorStrategy.CLASS:
                return f".{attr.value}"
            case SelectorStrategy.XPATH:
                return f"xpath={attr.value}"
            case _:
                return attr.value

    def add_fallback(self, attribute: SelectorAttribute) -> "SmartSelector":
        """
        Add a fallback attribute (returns new instance).

        Args:
            attribute: Fallback attribute to add

        Returns:
            New SmartSelector with added fallback
        """
        new_fallbacks = self.fallbacks.copy()
        new_fallbacks.append(attribute)

        return self.model_copy(update={"fallbacks": new_fallbacks})

    def promote_fallback(self, strategy: SelectorStrategy) -> "SmartSelector":
        """
        Promote a fallback to primary (healing learned preference).

        Args:
            strategy: Strategy to promote

        Returns:
            New SmartSelector with promoted fallback
        """
        # Find the fallback to promote
        new_fallback = next((a for a in self.fallbacks if a.strategy == strategy), None)

        if new_fallback is None:
            return self  # No change if not found

        # Move current primary to fallbacks
        new_fallbacks = [self.primary] + [
            a for a in self.fallbacks if a.strategy != strategy
        ]

        return self.model_copy(
            update={"primary": new_fallback, "fallbacks": new_fallbacks}
        )

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict) -> "SmartSelector":
        """Deserialize from dictionary."""
        return cls(**data)

    @classmethod
    def from_simple(
        cls,
        id: str,
        selector_string: str,
        strategy: SelectorStrategy = SelectorStrategy.DATA_TESTID,
    ) -> "SmartSelector":
        """
        Create SmartSelector from simple selector string.

        Args:
            id: Selector ID
            selector_string: Simple selector value
            strategy: Strategy type

        Returns:
            SmartSelector with single attribute
        """
        return cls(
            id=id, primary=SelectorAttribute(strategy=strategy, value=selector_string)
        )


# ============================================================================
# Factory Functions
# ============================================================================


def create_smart_selector(
    id: str,
    primary_strategy: SelectorStrategy,
    primary_value: str,
    fallback_specs: Optional[List[tuple[SelectorStrategy, str]]] = None,
    name: Optional[str] = None,
    frame_path: Optional[List[str]] = None,
) -> SmartSelector:
    """
    Create SmartSelector with primary and fallback attributes.

    Args:
        id: Selector ID
        primary_strategy: Primary selector strategy
        primary_value: Primary selector value
        fallback_specs: List of (strategy, value) tuples for fallbacks
        name: Optional human-readable name
        frame_path: Optional iframe path

    Returns:
        SmartSelector instance
    """
    primary = SelectorAttribute(strategy=primary_strategy, value=primary_value)

    fallbacks = []
    if fallback_specs:
        fallbacks = [
            SelectorAttribute(strategy=strategy, value=value)
            for strategy, value in fallback_specs
        ]

    return SmartSelector(
        id=id, name=name, primary=primary, fallbacks=fallbacks, frame_path=frame_path
    )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "SelectorStrategy",
    "SelectorAttribute",
    "SmartSelector",
    "create_smart_selector",
]
