# AI-Powered Selector Healing Plan

**Status**: COMPLETE
**Created**: 2025-12-01
**Priority**: HIGH (reliability improvement)

## Overview

Enhance the existing selector healing infrastructure with AI-powered capabilities for semantic matching, fuzzy attribute comparison, and LLM-based element understanding.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Healing Layer                          │
├─────────────────────────────────────────────────────────────┤
│  AISelectorHealer                                            │
│  ├── SemanticTextMatcher    - LLM/embedding text similarity │
│  ├── FuzzyAttributeMatcher  - Levenshtein, regex patterns   │
│  ├── StructuralMatcher      - DOM tree similarity           │
│  └── ConfidenceOptimizer    - Adaptive thresholds           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Existing Infrastructure                   │
├─────────────────────────────────────────────────────────────┤
│  SelectorHealingChain                                        │
│  ├── Tier 0: Original selector                              │
│  ├── Tier 1: Heuristic healing (SelectorHealer)             │
│  ├── Tier 1.5: AI-Enhanced healing (NEW)                    │
│  ├── Tier 2: Anchor-based healing (AnchorHealer)            │
│  └── Tier 3: CV healing (CVHealer)                          │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Tasks

### Phase 1: Fuzzy Matching (Core) - IN PROGRESS
- [ ] Create `src/casare_rpa/utils/selectors/ai_selector_healer.py`
  - FuzzyMatcher class (Levenshtein, Jaro-Winkler)
  - Enhanced text similarity with synonyms
  - Regex pattern matching for dynamic attributes
  - Weighted multi-attribute scoring

### Phase 2: Semantic Matching (LLM-Optional)
- [ ] Add semantic text comparison
  - "Sign In" ≈ "Log In" ≈ "Login"
  - Use LLM for complex semantic matching (optional)
  - Local synonym dictionary for common UI terms

### Phase 3: Adaptive Confidence
- [ ] Dynamic confidence thresholds
  - Page complexity scoring
  - Element criticality levels
  - Historical success rate adjustment

### Phase 4: Node Integration
- [ ] Wire healing into browser nodes
- [ ] Wire healing into desktop nodes
- [ ] Add healing config to execution context

### Phase 5: Tests
- [ ] Unit tests for fuzzy matching
- [ ] Integration tests with mock pages
- [ ] Performance benchmarks

## Technical Specifications

### AISelectorHealer Class

```python
class AISelectorHealer:
    """AI-enhanced selector healing with fuzzy and semantic matching."""

    def __init__(
        self,
        min_confidence: float = 0.6,
        use_llm: bool = False,
        llm_manager: Optional[LLMResourceManager] = None,
    )

    async def heal(
        self,
        page: Page,
        selector: str,
        fingerprint: Optional[Dict] = None,
    ) -> AIHealingResult

    def fuzzy_text_match(self, text1: str, text2: str) -> float
    def fuzzy_attribute_match(self, attrs1: Dict, attrs2: Dict) -> float
    async def semantic_match(self, text1: str, text2: str) -> float
```

### AIHealingResult

```python
@dataclass
class AIHealingResult:
    success: bool
    original_selector: str
    healed_selector: str
    confidence: float
    strategy_used: str  # "fuzzy", "semantic", "structural"
    match_details: Dict[str, float]  # per-attribute scores
    alternatives: List[Tuple[str, float]]
    llm_used: bool
```

### UI Term Synonyms (Built-in)

```python
UI_SYNONYMS = {
    "sign_in": ["login", "log in", "sign in", "signin"],
    "sign_up": ["register", "create account", "sign up", "signup"],
    "submit": ["send", "confirm", "ok", "done", "continue", "next"],
    "cancel": ["close", "dismiss", "back", "abort"],
    "search": ["find", "lookup", "query"],
    "delete": ["remove", "trash", "discard"],
    "edit": ["modify", "change", "update"],
    "save": ["store", "apply", "keep"],
}
```

## Fuzzy Matching Algorithms

1. **Levenshtein Distance** - Edit distance for typos
2. **Jaro-Winkler** - Prefix-weighted similarity
3. **Token Set Ratio** - Word-level matching (order-independent)
4. **Regex Patterns** - For dynamic IDs like `btn-12345` → `btn-\d+`

## Dependencies

```toml
# Already available in Python stdlib or existing deps
# No new dependencies required for core fuzzy matching

# Optional for advanced matching:
rapidfuzz = "^3.0.0"  # Fast fuzzy matching (optional)
```

## Integration Points

1. **SelectorHealer._calculate_similarity()** - Enhance with fuzzy matching
2. **SelectorHealer._text_similarity()** - Add semantic matching
3. **SelectorHealingChain** - Add AI tier between heuristic and anchor
4. **BrowserNodes** - Wrap selector lookups with healing

## Success Metrics

- Selector healing success rate: 80%+ (up from ~60%)
- Semantic match accuracy: 90%+ for common UI terms
- Healing latency: <200ms for fuzzy, <500ms for LLM

## Unresolved Questions

1. Should LLM be used for all semantic matches or only fallback?
2. Cache semantic similarity results? (likely yes)
3. Persist learned patterns for future sessions?
