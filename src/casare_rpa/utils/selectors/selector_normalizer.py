"""
Selector Normalizer (Backward Compatibility Module).

DEPRECATED: Use casare_rpa.utils.selectors.SelectorFacade instead.

New code should use:
    from casare_rpa.utils.selectors import normalize_selector, validate_selector

This module is kept for backward compatibility with older code that imports from here.
"""

import warnings
from typing import Tuple

# Import from facade for implementation
from casare_rpa.utils.selectors.selector_facade import (
    get_selector_facade,
)


def normalize_selector(selector: str) -> str:
    """
    Normalize any selector format to work with Playwright.

    DEPRECATED: Use casare_rpa.utils.selectors.normalize_selector instead.

    This function is kept for backward compatibility.
    """
    warnings.warn(
        "normalize_selector from selector_normalizer is deprecated. "
        "Use casare_rpa.utils.selectors.normalize_selector instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_selector_facade().normalize(selector)


def detect_selector_type(selector: str) -> str:
    """
    Detect the type of selector.

    DEPRECATED: Use SelectorFacade.detect_type() instead.

    Args:
        selector: Selector string

    Returns:
        Type string: "xpath", "css", "text", "itext", "wildcard", or "unknown"
    """
    warnings.warn(
        "detect_selector_type from selector_normalizer is deprecated. "
        "Use SelectorFacade.detect_type() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_selector_facade().detect_type(selector)


def validate_selector_format(selector: str) -> tuple[bool, str]:
    """
    Validate if a selector has valid format.

    DEPRECATED: Use casare_rpa.utils.selectors.validate_selector instead.

    Args:
        selector: Selector string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    warnings.warn(
        "validate_selector_format from selector_normalizer is deprecated. "
        "Use casare_rpa.utils.selectors.validate_selector instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_selector_facade().validate(selector)
