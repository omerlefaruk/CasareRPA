"""
Selector Validator Component.

Handles all selector validation logic:
- Testing selectors against browser/desktop contexts
- Uniqueness checking
- Performance metrics
- Wildcard pattern generation
- Text selector generation
"""

import re
from typing import Any, Dict, Optional, TYPE_CHECKING

from PySide6.QtCore import QObject, Signal
from loguru import logger

from casare_rpa.presentation.canvas.selectors.tabs.base_tab import (
    BaseSelectorTab,
    SelectorResult,
)

if TYPE_CHECKING:
    pass


class ValidationResult:
    """Result of selector validation."""

    def __init__(
        self,
        success: bool,
        count: int = 0,
        time_ms: float = 0.0,
        error: Optional[str] = None,
        is_unique: bool = False,
    ) -> None:
        self.success = success
        self.count = count
        self.time_ms = time_ms
        self.error = error
        self.is_unique = count == 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "count": self.count,
            "time_ms": self.time_ms,
            "error": self.error,
            "is_unique": self.is_unique,
        }

    @classmethod
    def from_error(cls, error: str) -> "ValidationResult":
        """Create error result."""
        return cls(success=False, error=error)

    @classmethod
    def from_count(cls, count: int, time_ms: float = 0.0) -> "ValidationResult":
        """Create success result with element count."""
        return cls(success=True, count=count, time_ms=time_ms)


class SelectorValidator(QObject):
    """
    Validates selectors and generates selector patterns.

    Provides:
    - Async selector testing against browser/desktop
    - Uniqueness validation
    - Wildcard pattern generation
    - itext= selector generation
    - Performance timing

    Signals:
        validation_completed: Emitted when validation finishes (ValidationResult)
        status_changed: Emitted when status changes (str)
    """

    validation_completed = Signal(object)
    status_changed = Signal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._tabs: Dict[str, BaseSelectorTab] = {}
        self._current_mode: str = "browser"

    def register_tab(self, mode: str, tab: BaseSelectorTab) -> None:
        """Register a tab for validation operations."""
        self._tabs[mode] = tab

    def set_current_mode(self, mode: str) -> None:
        """Set the current validation mode."""
        self._current_mode = mode

    async def validate_selector(
        self,
        selector: str,
        selector_type: str = "xpath",
        mode: Optional[str] = None,
    ) -> ValidationResult:
        """
        Validate a selector against the current context.

        Args:
            selector: The selector string to validate
            selector_type: Type of selector (xpath, css, aria, etc.)
            mode: Optional mode override

        Returns:
            ValidationResult with success, count, timing info
        """
        if not selector:
            return ValidationResult.from_error("No selector to validate")

        validate_mode = mode or self._current_mode
        tab = self._tabs.get(validate_mode)

        if not tab:
            return ValidationResult.from_error(f"No tab for mode: {validate_mode}")

        try:
            result = await tab.test_selector(selector, selector_type)

            if result.get("success"):
                count = result.get("count", 0)
                time_ms = result.get("time_ms", 0.0)
                validation = ValidationResult.from_count(count, time_ms)
                self.validation_completed.emit(validation)
                return validation
            else:
                error = result.get("error", "Unknown error")
                validation = ValidationResult.from_error(error)
                self.validation_completed.emit(validation)
                return validation

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            validation = ValidationResult.from_error(str(e))
            self.validation_completed.emit(validation)
            return validation

    async def highlight_selector(
        self,
        selector: str,
        selector_type: str = "xpath",
        mode: Optional[str] = None,
    ) -> bool:
        """
        Highlight elements matching selector in the target context.

        Args:
            selector: The selector to highlight
            selector_type: Type of selector
            mode: Optional mode override

        Returns:
            True if highlighting succeeded
        """
        highlight_mode = mode or self._current_mode
        tab = self._tabs.get(highlight_mode)

        if not tab:
            return False

        try:
            return await tab.highlight_selector(selector, selector_type)
        except Exception as e:
            logger.error(f"Highlight failed: {e}")
            return False

    def generate_wildcard_selector(self, selector: str) -> Optional[str]:
        """
        Generate a wildcard version of a selector.

        Converts dynamic parts (IDs with numbers, indexed positions, etc.)
        to wildcard patterns for more resilient matching.

        Args:
            selector: Original selector

        Returns:
            Wildcard selector or None if no conversion possible
        """
        if not selector:
            return None

        wildcard = selector
        original = selector

        # Convert ID patterns with numbers: #user-123 -> #user-*
        wildcard = re.sub(r"#([a-zA-Z_-]+)[-_]?\d+", r"#\1-*", wildcard)

        # Convert dynamic class patterns: .btn-primary-42 -> .btn-*
        wildcard = re.sub(r"\.([a-zA-Z]+)[-_]\d+", r".\1-*", wildcard)

        # Convert numbered index patterns: [1] -> [*]
        wildcard = re.sub(r"\[(\d+)\]", r"[*]", wildcard)

        # Convert nth-child with numbers: nth-child(3) -> nth-child(*)
        wildcard = re.sub(r"nth-child\(\d+\)", "nth-child(*)", wildcard)

        # Convert data attributes with GUIDs/UUIDs
        wildcard = re.sub(
            r'(data-[a-zA-Z-]+)="[a-f0-9-]{8,}"',
            r'\1="*"',
            wildcard,
            flags=re.IGNORECASE,
        )

        # Convert session/token-like attributes
        wildcard = re.sub(
            r'(data-[a-zA-Z-]+)="[a-zA-Z0-9]{16,}"',
            r'\1="*"',
            wildcard,
        )

        if wildcard != original:
            logger.info(f"Generated wildcard: {original[:30]} -> {wildcard[:30]}")
            return wildcard

        return None

    def generate_text_selector(
        self,
        text: str,
        element_type: str = "*",
    ) -> SelectorResult:
        """
        Generate an itext= selector for case-insensitive text matching.

        Args:
            text: The text to search for
            element_type: HTML element type (* for any)

        Returns:
            SelectorResult with the generated selector
        """
        if not text:
            raise ValueError("Text cannot be empty")

        if element_type == "*":
            selector = f"itext={text}"
        else:
            selector = f"itext={element_type}:{text}"

        logger.info(f"Generated itext selector: {selector}")

        return SelectorResult(
            selector_value=selector,
            selector_type="itext",
            confidence=0.7,
            is_unique=False,
            metadata={
                "search_text": text,
                "element_type": element_type,
            },
        )

    def build_result_with_metadata(
        self,
        selector: str,
        selector_type: str,
        confidence: float,
        is_unique: bool,
        fuzzy_settings: Optional[Dict[str, Any]] = None,
        cv_settings: Optional[Dict[str, Any]] = None,
        image_settings: Optional[Dict[str, Any]] = None,
        anchor_data: Optional[Dict[str, Any]] = None,
    ) -> SelectorResult:
        """
        Build a complete SelectorResult with all metadata.

        Args:
            selector: The selector value
            selector_type: Type of selector
            confidence: Confidence score 0.0-1.0
            is_unique: Whether selector is unique
            fuzzy_settings: Fuzzy matching settings
            cv_settings: Computer vision settings
            image_settings: Image matching settings
            anchor_data: Anchor configuration

        Returns:
            Complete SelectorResult
        """
        metadata: Dict[str, Any] = {}

        if fuzzy_settings:
            metadata["fuzzy_accuracy"] = fuzzy_settings.get("accuracy", 0.8)
            metadata["fuzzy_innertext"] = fuzzy_settings.get("innertext", "")
            metadata["fuzzy_match_type"] = fuzzy_settings.get("match_type", "Contains")

        if cv_settings:
            metadata["cv_accuracy"] = cv_settings.get("accuracy", 0.8)
            metadata["cv_element_type"] = cv_settings.get("element_type", "Any")
            metadata["cv_text"] = cv_settings.get("text", "")

        if image_settings:
            metadata["image_accuracy"] = image_settings.get("accuracy", 0.8)

        if anchor_data:
            metadata["anchor"] = anchor_data

        return SelectorResult(
            selector_value=selector,
            selector_type=selector_type,
            confidence=confidence,
            is_unique=is_unique,
            metadata=metadata,
        )

    def format_validation_message(self, result: ValidationResult) -> str:
        """
        Format a validation result as a user-friendly message.

        Args:
            result: The validation result

        Returns:
            Formatted message string
        """
        if not result.success:
            return f"Error: {result.error}"

        if result.count == 0:
            return "No elements found"
        elif result.count == 1:
            return f"Found exactly 1 element ({result.time_ms:.1f}ms)"
        else:
            return (
                f"Found {result.count} elements - not unique ({result.time_ms:.1f}ms)"
            )

    def get_validation_style(self, result: ValidationResult) -> str:
        """
        Get CSS style for validation result display.

        Args:
            result: The validation result

        Returns:
            CSS style string
        """
        if not result.success:
            return (
                "padding: 8px; background: #3d1e1e; color: #ef4444; border-radius: 4px;"
            )

        if result.count == 0:
            return (
                "padding: 8px; background: #3d1e1e; color: #ef4444; border-radius: 4px;"
            )
        elif result.count == 1:
            return (
                "padding: 8px; background: #1e3d2e; color: #10b981; border-radius: 4px;"
            )
        else:
            return (
                "padding: 8px; background: #3d3520; color: #fbbf24; border-radius: 4px;"
            )
