"""
Selector Normalizer - Ensures selectors work with Playwright
Handles XPath, CSS, ARIA, data attributes, text selectors, etc.
"""

from typing import Tuple
from loguru import logger


def normalize_selector(selector: str) -> str:
    r"""
    Normalize any selector format to work with Playwright.

    Playwright selector syntax:
    - XPath: starts with '//' or has 'xpath=' prefix
    - CSS: default (no prefix) - #id, .class, [attr], tag, etc.
    - Text: 'text=...' prefix
    - ARIA: [aria-label="..."] or role attributes

    Args:
        selector: Raw selector string (XPath, CSS, ARIA, data-attr, etc.)

    Returns:
        Normalized selector that Playwright understands

    Examples:
        '//*[@id="test"]' -> '//*[@id="test"]'  (XPath with //)
        'xpath=//*[@id="test"]' -> 'xpath=//*[@id="test"]'  (already prefixed)
        '#myId' -> '#myId'  (CSS, no change)
        '[data-testid="btn"]' -> '[data-testid="btn"]'  (CSS, no change)
        'text=Click me' -> 'text=Click me'  (text selector, no change)
    """
    if not selector or not isinstance(selector, str):
        return selector

    selector = selector.strip()

    # 1. Already has xpath= prefix - keep as is
    if selector.startswith("xpath="):
        logger.debug(f"Selector has xpath= prefix: {selector}")
        return selector

    # 2. Already has text= prefix - keep as is
    if selector.startswith("text="):
        logger.debug(f"Selector has text= prefix: {selector}")
        return selector

    # 3. Already has >> combinator (Playwright chaining) - keep as is
    if ">>" in selector:
        logger.debug(f"Selector has >> combinator: {selector}")
        return selector

    # 4. XPath that starts with // - keep as is (Playwright understands this)
    if selector.startswith("//"):
        logger.debug(f"Selector is XPath with //: {selector}")
        return selector

    # 5. XPath that starts with /* - convert to // (our generator uses this)
    if selector.startswith("/*"):
        normalized = "//" + selector[2:]
        logger.debug(f"Converting XPath /* to //: {selector} -> {normalized}")
        return normalized

    # 6. XPath that starts with / but not // (absolute path) - add xpath= prefix
    if selector.startswith("/") and not selector.startswith("//"):
        # Absolute XPath like /html/body/div - needs xpath= prefix for Playwright
        normalized = f"xpath={selector}"
        logger.debug(
            f"Adding xpath= prefix to absolute path: {selector} -> {normalized}"
        )
        return normalized

    # 7. Check if it's a CSS attribute selector (starts with [ but no XPath functions)
    if selector.startswith("[") and not any(
        func in selector for func in ["contains(", "text()", "normalize-space("]
    ):
        # CSS attribute selector like [data-testid="btn"] or [aria-label="Search"]
        logger.debug(f"Treating as CSS attribute selector (no change): {selector}")
        return selector

    # 8. Check if it looks like XPath (contains @ or XPath functions)
    if "@" in selector or any(
        func in selector for func in ["contains(", "text()", "normalize-space("]
    ):
        # Looks like XPath but doesn't start with / - add // prefix
        if not selector.startswith("/"):
            normalized = f"//{selector}"
            logger.debug(
                f"Adding // prefix to XPath expression: {selector} -> {normalized}"
            )
            return normalized

    # 9. CSS selector (default) - no prefix needed
    # This includes: #id, .class, tag, [attr], etc.
    logger.debug(f"Treating as CSS selector (no change): {selector}")
    return selector


def detect_selector_type(selector: str) -> str:
    """
    Detect the type of selector.

    Args:
        selector: The selector string

    Returns:
        One of: 'xpath', 'css', 'text', 'unknown'
    """
    if not selector:
        return "unknown"

    selector = selector.strip()

    if selector.startswith("xpath="):
        return "xpath"
    if selector.startswith("text="):
        return "text"
    if selector.startswith("//") or (
        selector.startswith("/") and not selector.startswith("/[")
    ):
        return "xpath"

    # CSS attribute selector (starts with [ but no XPath functions)
    if selector.startswith("[") and not any(
        func in selector for func in ["@", "contains(", "text()", "normalize-space("]
    ):
        return "css"

    # XPath indicators
    if "@" in selector or any(
        func in selector for func in ["contains(", "text()", "normalize-space("]
    ):
        return "xpath"

    return "css"


def validate_selector_format(selector: str) -> Tuple[bool, str]:
    """
    Validate if a selector has valid format.

    Args:
        selector: The selector to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not selector:
        return False, "Selector cannot be empty"

    if not isinstance(selector, str):
        return False, "Selector must be a string"

    selector = selector.strip()

    # Check for balanced brackets (basic validation)
    if selector.count("[") != selector.count("]"):
        return False, "Unbalanced brackets in selector"

    if selector.count("(") != selector.count(")"):
        return False, "Unbalanced parentheses in selector"

    return True, ""
