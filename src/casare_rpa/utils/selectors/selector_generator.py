"""
Selector Generator Re-export Module (Backward Compatibility).

DEPRECATED: Use casare_rpa.utils.selectors.SelectorFacade instead.

New implementations should use:
- casare_rpa.domain.entities.selector for models (SelectorType, SelectorStrategy, ElementFingerprint)
- casare_rpa.utils.selectors.SelectorFacade for generation logic

This module is kept for backward compatibility with older code.
"""

import warnings
from typing import Any

from casare_rpa.domain.entities.selector import (
    ElementFingerprint,
    SelectorStrategy,
    SelectorType,
)


class SmartSelectorGenerator:
    """
    DEPRECATED: Use SelectorFacade.generate_browser_fingerprint() or
    SelectorFacade.generate_desktop_fingerprint() instead.

    This class is kept for backward compatibility.
    """

    def __init__(self):
        warnings.warn(
            "SmartSelectorGenerator is deprecated. "
            "Use casare_rpa.utils.selectors.SelectorFacade instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        from casare_rpa.utils.selectors.selector_facade import get_selector_facade

        self._facade = get_selector_facade()

    def generate_browser_fingerprint(self, element_data: dict[str, Any]) -> ElementFingerprint:
        """Generate fingerprint from browser element data."""
        return self._facade.generate_browser_fingerprint(element_data)

    def generate_desktop_fingerprint(self, element_data: dict[str, Any]) -> ElementFingerprint:
        """Generate fingerprint from desktop element data (UIA)."""
        return self._facade.generate_desktop_fingerprint(element_data)


__all__ = [
    "SelectorType",
    "SelectorStrategy",
    "ElementFingerprint",
    "SmartSelectorGenerator",
]
