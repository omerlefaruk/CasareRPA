"""Wildcard selector pattern support.

Converts wildcard patterns to valid CSS selectors for use with Playwright.
"""

import re
from typing import List
from loguru import logger


class WildcardSelector:
    """Convert wildcard patterns to valid CSS selectors.

    Supported patterns:
    - btn-* -> [class*="btn-"]
    - *-submit -> [class$="-submit"]
    - #user-* -> [id^="user-"]
    - .nav-*-item -> [class*="nav-"][class*="-item"]
    - [name=field*] -> [name^="field"]
    - [data-*] -> [data-*] (native CSS)
    - input#field-* -> input[id^="field-"]
    - button.btn-* -> button[class*="btn-"]
    """

    # Characters that indicate wildcards
    WILDCARD_CHARS = {"*", "?"}

    @classmethod
    def has_wildcard(cls, selector: str) -> bool:
        """Check if selector contains wildcard patterns.

        Args:
            selector: CSS selector string to check

        Returns:
            True if selector contains wildcard characters
        """
        if not selector:
            return False
        return any(c in selector for c in cls.WILDCARD_CHARS)

    @classmethod
    def parse(cls, pattern: str) -> str:
        """Convert wildcard pattern to CSS selector.

        Args:
            pattern: Wildcard pattern string

        Returns:
            Valid CSS selector that Playwright understands

        Examples:
            >>> WildcardSelector.parse("#user-*")
            '[id^="user-"]'
            >>> WildcardSelector.parse(".btn-*")
            '[class*="btn-"]'
            >>> WildcardSelector.parse("*-submit")
            '[class$="-submit"]'
        """
        if not pattern:
            return pattern

        if not cls.has_wildcard(pattern):
            return pattern

        result = pattern
        original = pattern

        # Handle tag#id-* patterns: input#field-* -> input[id^="field-"]
        tag_id_match = re.match(
            r"^([a-zA-Z][a-zA-Z0-9]*)?#([a-zA-Z_-][a-zA-Z0-9_-]*)\*$", result
        )
        if tag_id_match:
            tag = tag_id_match.group(1) or ""
            prefix = tag_id_match.group(2)
            result = f'{tag}[id^="{prefix}"]'
            logger.debug(f"Wildcard: '{original}' -> '{result}'")
            return result

        # Handle tag.class-* patterns: button.btn-* -> button[class*="btn-"]
        tag_class_match = re.match(
            r"^([a-zA-Z][a-zA-Z0-9]*)\.([a-zA-Z_-][a-zA-Z0-9_-]*)\*$", result
        )
        if tag_class_match:
            tag = tag_class_match.group(1) or ""
            prefix = tag_class_match.group(2)
            result = f'{tag}[class*="{prefix}"]'
            logger.debug(f"Wildcard: '{original}' -> '{result}'")
            return result

        # Handle ID wildcards: #user-* -> [id^="user-"]
        id_prefix_match = re.match(r"^#([a-zA-Z_-][a-zA-Z0-9_-]*)\*$", result)
        if id_prefix_match:
            prefix = id_prefix_match.group(1)
            result = f'[id^="{prefix}"]'
            logger.debug(f"Wildcard: '{original}' -> '{result}'")
            return result

        # Handle #*-suffix: #*-panel -> [id$="-panel"]
        id_suffix_match = re.match(r"^#\*([a-zA-Z0-9_-]+)$", result)
        if id_suffix_match:
            suffix = id_suffix_match.group(1)
            result = f'[id$="{suffix}"]'
            logger.debug(f"Wildcard: '{original}' -> '{result}'")
            return result

        # Handle class wildcards: .btn-* -> [class*="btn-"]
        class_prefix_match = re.match(r"^\.([a-zA-Z_-][a-zA-Z0-9_-]*)\*$", result)
        if class_prefix_match:
            prefix = class_prefix_match.group(1)
            result = f'[class*="{prefix}"]'
            logger.debug(f"Wildcard: '{original}' -> '{result}'")
            return result

        # Handle .*-suffix: .*-active -> [class$="-active"]
        class_suffix_match = re.match(r"^\.\*([a-zA-Z0-9_-]+)$", result)
        if class_suffix_match:
            suffix = class_suffix_match.group(1)
            result = f'[class$="{suffix}"]'
            logger.debug(f"Wildcard: '{original}' -> '{result}'")
            return result

        # Handle *-suffix without prefix: *-submit -> [class$="-submit"]
        suffix_only_match = re.match(r"^\*([a-zA-Z_-][a-zA-Z0-9_-]*)$", result)
        if suffix_only_match:
            suffix = suffix_only_match.group(1)
            result = f'[class$="{suffix}"]'
            logger.debug(f"Wildcard: '{original}' -> '{result}'")
            return result

        # Handle prefix-*-suffix patterns: nav-*-item -> [class*="nav-"][class*="-item"]
        middle_wildcard_match = re.match(
            r"^([a-zA-Z_-][a-zA-Z0-9_-]*)\*([a-zA-Z0-9_-]+)$", result
        )
        if middle_wildcard_match:
            prefix = middle_wildcard_match.group(1)
            suffix = middle_wildcard_match.group(2)
            result = f'[class*="{prefix}"][class*="{suffix}"]'
            logger.debug(f"Wildcard: '{original}' -> '{result}'")
            return result

        # Handle attribute wildcards: [name=field*] -> [name^="field"]
        attr_prefix_match = re.match(
            r"^\[([a-zA-Z_-][a-zA-Z0-9_-]*)=([^\]]+)\*\]$", result
        )
        if attr_prefix_match:
            attr_name = attr_prefix_match.group(1)
            attr_value = attr_prefix_match.group(2).strip("\"'")
            result = f'[{attr_name}^="{attr_value}"]'
            logger.debug(f"Wildcard: '{original}' -> '{result}'")
            return result

        # Handle attribute suffix wildcards: [name=*field] -> [name$="field"]
        attr_suffix_match = re.match(
            r"^\[([a-zA-Z_-][a-zA-Z0-9_-]*)=\*([^\]]+)\]$", result
        )
        if attr_suffix_match:
            attr_name = attr_suffix_match.group(1)
            attr_value = attr_suffix_match.group(2).strip("\"'")
            result = f'[{attr_name}$="{attr_value}"]'
            logger.debug(f"Wildcard: '{original}' -> '{result}'")
            return result

        # Handle [data-*] - already valid CSS (attribute presence with wildcard)
        if re.match(r"^\[data-\*\]$", result):
            logger.debug(f"Wildcard: '{original}' -> '{result}' (data-* preserved)")
            return result

        # Handle ? wildcards for single character (less common)
        # Replace ? with . for regex-like single char match
        # This is complex for CSS, convert to contains for simplicity
        if "?" in result:
            # For now, treat ? as * for CSS compatibility
            result = result.replace("?", "*")
            # Re-parse with * instead
            if cls.has_wildcard(result) and result != original:
                return cls.parse(result)

        logger.debug(f"Wildcard: '{original}' -> '{result}'")
        return result

    @classmethod
    def expand(cls, pattern: str) -> List[str]:
        """Generate multiple selector variants from pattern.

        Useful for fallback matching when the primary selector doesn't work.

        Args:
            pattern: Wildcard pattern string

        Returns:
            List of possible CSS selectors, ordered by specificity

        Examples:
            >>> WildcardSelector.expand(".btn-*")
            ['[class*="btn-"]', '[class^="btn-"]', '[class$="btn-"]']
        """
        if not pattern:
            return [pattern] if pattern else []

        if not cls.has_wildcard(pattern):
            return [pattern]

        variants: List[str] = []

        # Add parsed version first
        parsed = cls.parse(pattern)
        if parsed != pattern:
            variants.append(parsed)

        # Add common expansions for class patterns
        if pattern.startswith(".") and "*" in pattern:
            base = pattern[1:].replace("*", "")
            if base:
                variants.extend(
                    [
                        f'[class^="{base}"]',
                        f'[class*="{base}"]',
                        f'[class$="{base}"]',
                    ]
                )

        # Add common expansions for ID patterns
        if pattern.startswith("#") and "*" in pattern:
            base = pattern[1:].replace("*", "")
            if base:
                variants.extend(
                    [
                        f'[id^="{base}"]',
                        f'[id*="{base}"]',
                        f'[id$="{base}"]',
                    ]
                )

        # Remove duplicates while preserving order
        seen = set()
        unique_variants = []
        for v in variants:
            if v not in seen:
                seen.add(v)
                unique_variants.append(v)

        return unique_variants if unique_variants else [pattern]

    @classmethod
    def is_valid_wildcard_pattern(cls, pattern: str) -> bool:
        """Validate if pattern is a valid wildcard selector.

        Args:
            pattern: Pattern to validate

        Returns:
            True if pattern is valid, False otherwise
        """
        if not pattern or not isinstance(pattern, str):
            return False

        if not cls.has_wildcard(pattern):
            return True  # Not a wildcard pattern, but valid

        # Check for obviously invalid patterns
        if pattern.count("*") > 2:
            return False  # Too many wildcards

        # Check balanced brackets
        if pattern.count("[") != pattern.count("]"):
            return False

        return True


def normalize_selector_with_wildcards(selector: str) -> str:
    """Normalize selector, expanding wildcards if present.

    Convenience function that handles wildcard expansion as part of
    selector normalization.

    Args:
        selector: Selector string that may contain wildcards

    Returns:
        Normalized CSS selector with wildcards expanded
    """
    if not selector:
        return selector

    if WildcardSelector.has_wildcard(selector):
        return WildcardSelector.parse(selector)

    return selector
