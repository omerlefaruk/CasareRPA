"""
Selector Normalizer - Ensures selectors work with Playwright
Handles XPath, CSS, ARIA, data attributes, text selectors, XML format, wildcards, etc.
"""

from typing import Tuple
from loguru import logger

from casare_rpa.utils.selectors.wildcard_selector import WildcardSelector


def _build_itext_xpath(text: str, element: str = "*") -> str:
    """
    Build case-insensitive text XPath using translate().

    Args:
        text: Text to search for
        element: Element tag (default: * for any)

    Returns:
        XPath like //*[contains(translate(., 'TEXT', 'text'), 'text')]
    """
    upper = text.upper()
    lower = text.lower()
    return f"//{element}[contains(translate(., '{upper}', '{lower}'), '{lower}')]"


def normalize_selector(selector: str) -> str:
    r"""
    Normalize any selector format to work with Playwright.

    Playwright selector syntax:
    - XPath: starts with '//' or has 'xpath=' prefix
    - CSS: default (no prefix) - #id, .class, [attr], tag, etc.
    - Text: 'text=...' prefix
    - ARIA: [aria-label="..."] or role attributes
    - itext: 'itext=...' case-insensitive text (converted to XPath)

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
        'itext=Start' -> '//*[contains(translate(...), 'start')]'  (case-insensitive)
        'itext=button:Start' -> '//button[contains(translate(...), 'start')]'
    """
    if not selector or not isinstance(selector, str):
        return selector

    selector = selector.strip()

    # 0. UiPath-style XML selector: <webctrl .../> or <input id='x' />
    if selector.startswith("<"):
        from casare_rpa.utils.selectors.selector_manager import parse_xml_selector

        parsed, sel_type = parse_xml_selector(selector)
        logger.debug(
            f"Converting XML selector to {sel_type}: {selector[:50]}... -> {parsed[:50]}..."
        )
        # Recursively normalize the parsed result
        return normalize_selector(parsed)

    # 0.5. Wildcard patterns: btn-*, #user-*, .nav-*-item, [name=field*]
    if WildcardSelector.has_wildcard(selector):
        normalized = WildcardSelector.parse(selector)
        if normalized != selector:
            logger.debug(f"Expanded wildcard selector: {selector} -> {normalized}")
            # Recursively normalize in case the result needs further processing
            return normalize_selector(normalized)

    # 1. Case-insensitive text selector: itext=Text or itext=tag:Text
    if selector.startswith("itext="):
        value = selector[6:]  # Remove 'itext=' prefix
        if ":" in value:
            # Format: itext=button:Start -> //button[contains(...)]
            element, text = value.split(":", 1)
            element = element.strip() or "*"
            text = text.strip()
        else:
            element = "*"
            text = value.strip()

        if text:
            normalized = _build_itext_xpath(text, element)
            logger.debug(f"Converting itext selector: {selector} -> {normalized}")
            return normalized
        return selector

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
        One of: 'xpath', 'css', 'text', 'itext', 'wildcard', 'unknown'
    """
    if not selector:
        return "unknown"

    selector = selector.strip()

    if selector.startswith("xpath="):
        return "xpath"
    if selector.startswith("text="):
        return "text"
    if selector.startswith("itext="):
        return "itext"
    if WildcardSelector.has_wildcard(selector):
        return "wildcard"
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
