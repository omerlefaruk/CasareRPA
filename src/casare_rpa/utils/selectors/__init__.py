"""Selector utilities."""

from .ai_selector_healer import (
    AISelectorHealer,
    AIHealingResult,
    FuzzyMatcher,
    SemanticMatcher,
    RegexPatternMatcher,
    HealingStrategy,
    UI_SYNONYMS,
)

__all__ = [
    "AISelectorHealer",
    "AIHealingResult",
    "FuzzyMatcher",
    "SemanticMatcher",
    "RegexPatternMatcher",
    "HealingStrategy",
    "UI_SYNONYMS",
]

# Individual imports can be done directly from submodules:
# from casare_rpa.utils.selectors.selector_cache import SelectorCache
# from casare_rpa.utils.selectors.selector_manager import SelectorManager
