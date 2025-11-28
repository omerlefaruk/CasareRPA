# Phase 4: Self-Healing Selector System

**Status**: Phase 4.1 Complete - Tier 1 Heuristic Healing
**Commit**: TBD
**Branch**: `feature/phase4-self-healing`

---

## Overview

Phase 4 implements a self-healing selector system that automatically recovers from UI changes without manual workflow maintenance. Uses a three-tier fallback approach:

1. **Tier 1 - Heuristic** (Phase 4.1): Multi-attribute fallback
2. **Tier 2 - Anchor-Based** (Phase 4.2): Spatial navigation from stable elements
3. **Tier 3 - Computer Vision** (Phase 4.3): Template matching fallback

---

## Phase 4.1: Tier 1 Heuristic Healing (Complete)

### Architecture

```
┌─────────────────────────────────────────────────┐
│            Domain Layer                         │
│  ┌───────────────────────────────────────────┐  │
│  │  SmartSelector                            │  │
│  │    - primary: SelectorAttribute           │  │
│  │    - fallbacks: List[SelectorAttribute]   │  │
│  │    - frame_path: Optional[List[str]]      │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │  HealingEvent                             │  │
│  │    - selector_id, tier, strategies        │  │
│  │    - healing_time_ms, workflow_name       │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │  HealingMetrics                           │  │
│  │    - total_uses, healing_events           │  │
│  │    - success_rate, fragility_score        │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│        Infrastructure Layer                     │
│  ┌───────────────────────────────────────────┐  │
│  │  HeuristicSelectorHealer                  │  │
│  │    - find_element() → (Locator, Event?)   │  │
│  │    - Tries primary + fallbacks            │  │
│  │    - Timeout: 400ms max                   │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │  HealingTelemetryService                  │  │
│  │    - record_healing_event()               │  │
│  │    - get_fragile_selectors()              │  │
│  │    - get_statistics()                     │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### Files Created

**Domain Layer**:
- `src/casare_rpa/domain/value_objects/selector.py` - SmartSelector, SelectorAttribute, SelectorStrategy
- `src/casare_rpa/domain/value_objects/healing_event.py` - HealingEvent, HealingMetrics, HealingTier

**Infrastructure Layer**:
- `src/casare_rpa/infrastructure/browser/selector_healer.py` - HeuristicSelectorHealer
- `src/casare_rpa/infrastructure/telemetry/healing_telemetry.py` - HealingTelemetryService

**Tests**:
- `tests/infrastructure/browser/test_selector_healer.py` - Healer tests
- `tests/infrastructure/telemetry/test_healing_telemetry.py` - Telemetry tests

---

## Selector Strategy Priority

```python
class SelectorStrategy(str, Enum):
    DATA_TESTID = "data-testid"  # Highest - semantic
    ID = "id"                     # High - unique
    ARIA_LABEL = "aria-label"     # Medium - accessibility
    TEXT = "text"                 # Medium - visible
    PLACEHOLDER = "placeholder"   # Medium - input hint
    ROLE = "role"                 # Low - semantic role
    CLASS = "class"               # Low - styling
    XPATH = "xpath"               # Lowest - structural
```

---

## Usage Example

### Creating Smart Selector

```python
from casare_rpa.domain.value_objects.selector import (
    create_smart_selector,
    SelectorStrategy
)

selector = create_smart_selector(
    id="btn-submit",
    primary_strategy=SelectorStrategy.DATA_TESTID,
    primary_value="submit-button",
    fallback_specs=[
        (SelectorStrategy.ID, "btnSubmit"),
        (SelectorStrategy.TEXT, "Submit"),
        (SelectorStrategy.CLASS, "btn-primary")
    ],
    name="Submit Button"
)
```

### Using Heuristic Healer

```python
from casare_rpa.infrastructure.browser import HeuristicSelectorHealer
from playwright.async_api import async_playwright

healer = HeuristicSelectorHealer()

async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()
    await page.goto("https://example.com")

    result = await healer.find_element(
        page=page,
        selector=selector,
        workflow_name="Example Workflow",
        node_id="node-123"
    )

    if result:
        locator, healing_event = result

        if healing_event is None:
            print("Primary succeeded - no healing")
        else:
            print(f"Healed using {healing_event.successful_strategy}")
            print(f"Healing time: {healing_event.healing_time_ms:.1f}ms")

            # Record event for telemetry
            from casare_rpa.infrastructure.telemetry import get_global_telemetry_service

            telemetry = get_global_telemetry_service()
            await telemetry.record_healing_event(healing_event)

        # Use locator
        await locator.click()
```

### Telemetry and Analytics

```python
from casare_rpa.infrastructure.telemetry import get_global_telemetry_service

telemetry = get_global_telemetry_service()

# Get fragile selectors
fragile = await telemetry.get_fragile_selectors(threshold=0.3, min_uses=10)

for metrics in fragile:
    print(f"Fragile: {metrics.selector_id}")
    print(f"  Fragility: {metrics.fragility_score:.2f}")
    print(f"  Success rate: {metrics.success_rate:.1%}")
    print(f"  Avg healing time: {metrics.avg_healing_time_ms:.1f}ms")

# Get overall statistics
stats = await telemetry.get_statistics()

print(f"Total selectors: {stats['total_selectors']}")
print(f"Healing events: {stats['total_healing_events']}")
print(f"Success rate: {stats['overall_success_rate']:.1%}")
print(f"Tier 1 successes: {stats['tier_breakdown']['tier1']}")
```

---

## Performance Targets

| Metric | Target | Actual (Phase 4.1) |
|--------|--------|---------------------|
| Tier 1 Timeout | 400ms | Configurable (default 400ms) |
| Per-Attempt Timeout | 100ms | Configurable (default 100ms) |
| Total Healing Budget | 1000ms | 400ms (tier 1 only) |
| Memory Overhead | Minimal | ~1KB per selector |

---

## Fragility Score Calculation

```python
healing_frequency = healing_events / total_uses
failure_rate = 1.0 - success_rate

# Weight by tier (tier 3 = more fragile)
tier_weight = (
    (tier1_successes * 0.3 + tier2_successes * 0.6 + tier3_successes * 1.0)
    / successful_heals
)

fragility_score = healing_frequency * failure_rate * tier_weight
```

**Interpretation**:
- `< 0.1`: Stable selector
- `0.1 - 0.3`: Moderate fragility
- `> 0.3`: Fragile - needs attention

---

## Test Coverage

```bash
cd /c/Users/Rau/Desktop/casare-aether
pytest tests/infrastructure/browser/test_selector_healer.py -v
pytest tests/infrastructure/telemetry/test_healing_telemetry.py -v
```

**Coverage**:
- SmartSelector value object (create, serialize, promote)
- Heuristic healing (primary, fallback, timeout enforcement)
- Telemetry (event recording, metrics, statistics)
- Fragile selector detection
- Concurrent access safety

---

## Future Phases

### Phase 4.2: Anchor-Based Healing (Pending)

**Goal**: Navigate from stable "anchor" elements to target

**Approach**:
- Define `AnchoredSelector` with spatial relationship
- Implement `AnchorBasedHealer` using Playwright locator chains
- Auto-detect stable anchors during recording

**Example**:
```python
selector = AnchoredSelector(
    id="dynamic-button",
    anchor_selector=SmartSelector(id="stable-header", ...),
    relationship=SpatialRelationship.BELOW,
    max_distance=200
)
```

### Phase 4.3: Computer Vision Fallback (Pending)

**Goal**: Template matching when selectors fail

**Approach**:
- OpenCV template matching with `cv2.matchTemplate`
- Perceptual hashing for fast similarity (`imagehash`)
- Template caching with TTL

**Dependencies**:
```bash
pip install opencv-python>=4.9.0 pillow>=10.2.0 imagehash>=4.3.1
```

---

## Next Steps

1. **Test Phase 4.1 in real workflows**
2. **Collect telemetry data** to validate fragility detection
3. **Design Phase 4.2 anchor system** based on real fragility patterns
4. **Merge to feature/aether-v3** via PR

---

**Last Updated**: 2025-11-28
**Phase**: 4.1 Complete
**Lines Added**: ~1,500 (domain + infra + tests + docs)
**Test Status**: All passing (SmartSelector, Healer, Telemetry)
