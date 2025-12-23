"""
Selector Validator

Real-time validation of desktop selectors with performance metrics
and visual feedback.
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import uiautomation as auto
from loguru import logger

from casare_rpa.desktop.element import DesktopElement
from casare_rpa.desktop.selector import find_element, find_elements, parse_selector


class ValidationStatus(Enum):
    """Validation result status"""

    VALID_UNIQUE = "valid_unique"  # Found exactly 1 element
    VALID_MULTIPLE = "valid_multiple"  # Found multiple elements
    NOT_FOUND = "not_found"  # Found 0 elements
    ERROR = "error"  # Validation error


@dataclass
class ValidationResult:
    """
    Result of selector validation
    """

    status: ValidationStatus
    element_count: int
    execution_time_ms: float
    error_message: str | None = None
    elements: list[DesktopElement] | None = None

    @property
    def is_valid(self) -> bool:
        """Check if selector is valid (finds at least one element)"""
        return self.status in [
            ValidationStatus.VALID_UNIQUE,
            ValidationStatus.VALID_MULTIPLE,
        ]

    @property
    def is_unique(self) -> bool:
        """Check if selector is unique (finds exactly one element)"""
        return self.status == ValidationStatus.VALID_UNIQUE

    @property
    def icon(self) -> str:
        """Get status icon"""
        return {
            ValidationStatus.VALID_UNIQUE: "✓",
            ValidationStatus.VALID_MULTIPLE: "⚠",
            ValidationStatus.NOT_FOUND: "✗",
            ValidationStatus.ERROR: "❌",
        }.get(self.status, "?")

    @property
    def color(self) -> str:
        """Get status color (hex)"""
        return {
            ValidationStatus.VALID_UNIQUE: "#10b981",  # Green
            ValidationStatus.VALID_MULTIPLE: "#fbbf24",  # Yellow
            ValidationStatus.NOT_FOUND: "#ef4444",  # Red
            ValidationStatus.ERROR: "#dc2626",  # Dark red
        }.get(self.status, "#888888")

    @property
    def message(self) -> str:
        """Get human-readable status message"""
        if self.status == ValidationStatus.VALID_UNIQUE:
            return f"✓ Found exactly 1 element ({self.execution_time_ms:.1f}ms)"
        elif self.status == ValidationStatus.VALID_MULTIPLE:
            return f"⚠ Found {self.element_count} elements - not unique ({self.execution_time_ms:.1f}ms)"
        elif self.status == ValidationStatus.NOT_FOUND:
            return f"✗ No elements found ({self.execution_time_ms:.1f}ms)"
        elif self.status == ValidationStatus.ERROR:
            return f"❌ Error: {self.error_message}"
        return "Unknown status"


class SelectorValidator:
    """
    Validates desktop selectors in real-time
    """

    def __init__(self, parent_control: auto.Control | None = None):
        """
        Initialize validator

        Args:
            parent_control: Parent control to search within (None = desktop root)
        """
        self.parent_control = parent_control or auto.GetRootControl()
        logger.debug("Selector validator initialized")

    def validate(self, selector: dict[str, Any], find_all: bool = False) -> ValidationResult:
        """
        Validate a selector.

        Args:
            selector: Selector dictionary to validate
            find_all: If True, find all matching elements; if False, stop at first match

        Returns:
            ValidationResult with status and metrics
        """
        logger.debug(f"Validating selector: {selector}")

        start_time = time.time()

        try:
            # Parse selector first
            parse_selector(selector)

            if find_all:
                # Find all matching elements
                elements = find_elements(self.parent_control, selector, max_depth=10)
                count = len(elements)

                execution_time = (time.time() - start_time) * 1000

                if count == 0:
                    status = ValidationStatus.NOT_FOUND
                elif count == 1:
                    status = ValidationStatus.VALID_UNIQUE
                else:
                    status = ValidationStatus.VALID_MULTIPLE

                return ValidationResult(
                    status=status,
                    element_count=count,
                    execution_time_ms=execution_time,
                    elements=elements,
                )

            else:
                # Find first matching element
                try:
                    element = find_element(self.parent_control, selector, timeout=2.0)
                    execution_time = (time.time() - start_time) * 1000

                    # Found one - but is it unique?
                    # Quick check by trying to find second element
                    all_elements = find_elements(self.parent_control, selector, max_depth=10)
                    count = len(all_elements)

                    if count == 1:
                        status = ValidationStatus.VALID_UNIQUE
                    else:
                        status = ValidationStatus.VALID_MULTIPLE

                    return ValidationResult(
                        status=status,
                        element_count=count,
                        execution_time_ms=execution_time,
                        elements=[element] if element else [],
                    )

                except ValueError:
                    # Element not found
                    execution_time = (time.time() - start_time) * 1000
                    return ValidationResult(
                        status=ValidationStatus.NOT_FOUND,
                        element_count=0,
                        execution_time_ms=execution_time,
                        elements=[],
                    )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = str(e)
            logger.error(f"Selector validation error: {error_msg}")

            return ValidationResult(
                status=ValidationStatus.ERROR,
                element_count=0,
                execution_time_ms=execution_time,
                error_message=error_msg,
            )

    def validate_multiple(self, selectors: list[dict[str, Any]]) -> list[ValidationResult]:
        """
        Validate multiple selectors.

        Args:
            selectors: List of selector dictionaries

        Returns:
            List of ValidationResult objects
        """
        logger.info(f"Validating {len(selectors)} selectors")
        results = []

        for selector in selectors:
            result = self.validate(selector, find_all=True)
            results.append(result)

        # Log summary
        unique_count = sum(1 for r in results if r.is_unique)
        valid_count = sum(1 for r in results if r.is_valid)
        logger.info(
            f"Validation complete: {unique_count} unique, {valid_count} valid, {len(selectors)} total"
        )

        return results

    def quick_check(self, selector: dict[str, Any]) -> bool:
        """
        Quick check if selector finds at least one element.

        Args:
            selector: Selector dictionary

        Returns:
            True if at least one element found
        """
        try:
            element = find_element(self.parent_control, selector, timeout=1.0)
            return element is not None
        except Exception:
            return False

    def highlight_matches(self, selector: dict[str, Any], max_count: int = 10):
        """
        Highlight all elements matching selector (for debugging).

        Args:
            selector: Selector dictionary
            max_count: Maximum number of elements to highlight

        Note:
            This is a stub - actual highlighting would require additional UI support
        """
        try:
            elements = find_elements(self.parent_control, selector, max_depth=10)
            elements = elements[:max_count]

            logger.info(f"Found {len(elements)} elements to highlight")

            # Visual highlighting via overlay rectangles or element flashing not implemented
            # Logging element bounds as fallback for debugging
            for i, element in enumerate(elements):
                bounds = element.get_bounding_rect()
                logger.debug(f"Element {i+1}: {bounds}")

        except Exception as e:
            logger.error(f"Failed to highlight matches: {e}")

    def get_element_at_position(self, x: int, y: int) -> DesktopElement | None:
        """
        Get element at screen position.

        Args:
            x: Screen X coordinate
            y: Screen Y coordinate

        Returns:
            DesktopElement if found, None otherwise
        """
        try:
            control = auto.ControlFromPoint(x, y)
            if control:
                return DesktopElement(control)
        except Exception as e:
            logger.warning(f"Failed to get element at position ({x}, {y}): {e}")

        return None


def validate_selector_sync(
    selector: dict[str, Any], parent_control: auto.Control | None = None
) -> ValidationResult:
    """
    Convenience function to validate a selector synchronously.

    Args:
        selector: Selector dictionary
        parent_control: Parent control to search within

    Returns:
        ValidationResult
    """
    validator = SelectorValidator(parent_control)
    return validator.validate(selector, find_all=True)
