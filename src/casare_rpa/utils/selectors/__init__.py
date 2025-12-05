"""Selector utilities."""

from casare_rpa.utils.selectors.ai_selector_healer import (
    AISelectorHealer,
    AIHealingResult,
    FuzzyMatcher,
    SemanticMatcher,
    RegexPatternMatcher,
    HealingStrategy,
    UI_SYNONYMS,
)
from casare_rpa.utils.selectors.anchor_locator import (
    AnchorLocator,
    AnchorCandidate,
    STABLE_ANCHOR_TAGS,
)
from casare_rpa.utils.selectors.element_snapshot import (
    ElementSnapshot,
    ElementDiff,
    SnapshotManager,
)
from casare_rpa.utils.selectors.selector_manager import (
    parse_xml_selector,
)
from casare_rpa.utils.selectors.wildcard_selector import (
    WildcardSelector,
    normalize_selector_with_wildcards,
)

__all__ = [
    # AI Selector Healer
    "AISelectorHealer",
    "AIHealingResult",
    "FuzzyMatcher",
    "SemanticMatcher",
    "RegexPatternMatcher",
    "HealingStrategy",
    "UI_SYNONYMS",
    # Anchor Locator
    "AnchorLocator",
    "AnchorCandidate",
    "STABLE_ANCHOR_TAGS",
    # Element Snapshot (Visual Diff)
    "ElementSnapshot",
    "ElementDiff",
    "SnapshotManager",
    # Selector parsing
    "parse_xml_selector",
    # Wildcard selectors
    "WildcardSelector",
    "normalize_selector_with_wildcards",
]

# Individual imports can be done directly from submodules:
# from casare_rpa.utils.selectors.selector_cache import SelectorCache
# from casare_rpa.utils.selectors.selector_manager import SelectorManager
