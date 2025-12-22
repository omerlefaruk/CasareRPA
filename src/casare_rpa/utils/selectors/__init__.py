"""
CasareRPA Selector Utilities.

Unified selector subsystem providing:
- Normalization: Convert any selector format to Playwright-compatible
- Validation: Check selector syntax and format
- Generation: Create selectors from element data (browser/desktop)
- Healing: Self-heal broken selectors using multiple strategies
- Caching: Cache selector validation results for performance
- Picker: Browser element picker integration

Primary Entry Point:
    from casare_rpa.utils.selectors import SelectorFacade
    facade = SelectorFacade.get_instance()

Convenience Functions:
    from casare_rpa.utils.selectors import normalize_selector, validate_selector
"""

# =============================================================================
# Unified Facade (Primary API)
# =============================================================================

from casare_rpa.utils.selectors.selector_facade import (
    SelectorFacade,
    SelectorTestResult,
    HealingResult,
    get_selector_facade,
    normalize_selector,
    validate_selector,
    test_selector,
    heal_selector,
)

# =============================================================================
# AI-Enhanced Healing
# =============================================================================

from casare_rpa.utils.selectors.ai_selector_healer import (
    AISelectorHealer,
    AIHealingResult,
    FuzzyMatcher,
    SemanticMatcher,
    RegexPatternMatcher,
    HealingStrategy,
    UI_SYNONYMS,
)

# =============================================================================
# Anchor-Based Location
# =============================================================================

from casare_rpa.utils.selectors.anchor_locator import (
    AnchorLocator,
    AnchorCandidate,
    STABLE_ANCHOR_TAGS,
)

# =============================================================================
# Element Snapshots (Visual Diff)
# =============================================================================

from casare_rpa.utils.selectors.element_snapshot import (
    ElementSnapshot,
    ElementDiff,
    SnapshotManager,
)

# =============================================================================
# Legacy/Backward Compatibility
# =============================================================================

from casare_rpa.utils.selectors.selector_manager import (
    parse_xml_selector,
)
from casare_rpa.utils.selectors.wildcard_selector import (
    WildcardSelector,
    normalize_selector_with_wildcards,
)

__all__ = [
    # Unified Facade (PRIMARY API)
    "SelectorFacade",
    "SelectorTestResult",
    "HealingResult",
    "get_selector_facade",
    "normalize_selector",
    "validate_selector",
    "test_selector",
    "heal_selector",
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
    # Selector parsing (legacy)
    "parse_xml_selector",
    # Wildcard selectors
    "WildcardSelector",
    "normalize_selector_with_wildcards",
]

# =============================================================================
# Direct Submodule Access
# =============================================================================
# For advanced use cases, import directly from submodules:
#
# from casare_rpa.utils.selectors.selector_cache import SelectorCache
# from casare_rpa.utils.selectors.selector_manager import SelectorManager
# from casare_rpa.utils.selectors.selector_healing import SelectorHealer
