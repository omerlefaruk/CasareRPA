# CasareRPA Selector Subsystem

## Overview

The selector subsystem provides comprehensive element identification and management for both web (browser) and desktop (Windows UIA) automation.

## Architecture

```
casare_rpa/utils/selectors/
├── selector_facade.py       # ★ UNIFIED ENTRY POINT ★
├── selector_manager.py      # Browser picker integration (Playwright)
├── selector_healing.py      # Heuristic self-healing
├── ai_selector_healer.py    # AI-enhanced healing (fuzzy, semantic, LLM)
├── selector_cache.py        # Caching layer for validation results
├── anchor_locator.py        # Anchor-based element location
├── wildcard_selector.py     # Wildcard pattern matching
├── element_snapshot.py      # Visual diff and snapshots
├── selector_injector.js     # Browser-side picker script
├── selector_normalizer.py   # (deprecated) → use SelectorFacade
└── selector_generator.py    # (deprecated) → use SelectorFacade
```

## Quick Start

```python
from casare_rpa.utils.selectors import SelectorFacade, normalize_selector

# Get singleton facade
facade = SelectorFacade.get_instance()

# Normalize any selector format
selector = facade.normalize("<input id='foo'/>")  # From UiPath XML
selector = facade.normalize("//div[@class='btn']")  # XPath
selector = facade.normalize(".btn-primary")  # CSS

# Validate selector
is_valid, error = facade.validate("button#submit")

# Test selector against page
result = await facade.test(page, "button.login")
print(f"Matches: {result.match_count}, Time: {result.execution_time_ms}ms")

# Heal broken selector
result = await facade.heal(page, "broken_selector", fingerprint, healing_context)
if result.success:
    print(f"Healed to: {result.healed_selector} (via {result.strategy_used})")
```

## Selector Types Supported

| Type | Format | Example |
|------|--------|---------|
| CSS | Standard CSS selectors | `.btn-primary`, `#login-form` |
| XPath | XML path expressions | `//div[@id='main']//button` |
| Text | Playwright text selector | `text=Login`, `text="Sign In"` |
| Case-insensitive text | itext prefix | `itext=submit` |
| Wildcard | Pattern with * or ? | `btn-*`, `input-??-field` |
| UiPath XML | Single/multi-element | `<webctrl tag='INPUT' id='user'/>` |
| ARIA | Accessibility selectors | `role=button[name="Submit"]` |
| Desktop UIA | Automation properties | `Name:Submit`, `AutomationId:btn_ok` |

## Self-Healing Pipeline

When a selector fails, the healing pipeline attempts recovery:

```
1. Original Selector (fast path)
   ↓ (fails)
2. Heuristic Healing
   - Attribute matching from fingerprint
   - Alternative selector strategies
   ↓ (fails)
3. Anchor-Based Healing
   - Find element relative to stable anchor
   ↓ (fails)
4. AI-Enhanced Healing
   - Fuzzy text matching
   - Semantic synonyms
   - LLM assistance (if configured)
   ↓ (fails)
5. Computer Vision Fallback
   - Template matching from screenshot
   - OCR-based location
```

## Canvas UI Integration

```python
from casare_rpa.presentation.canvas.selectors import UnifiedSelectorDialog

# Open the canonical selector dialog
dialog = UnifiedSelectorDialog(parent=self)
if dialog.exec():
    result = dialog.get_result()

    # Get primary selector
    selector = result.primary_selector

    # Get healing context for self-healing
    healing_context = result.healing_context

    # Get anchor configuration
    anchor_config = result.anchor_config
```

## Node Integration

Browser nodes automatically use the unified selector pipeline:

```python
from casare_rpa.nodes.browser.browser_base import BrowserBaseNode

class MyBrowserNode(BrowserBaseNode):
    async def execute(self, context):
        page = self.get_page(context)

        # Get normalized selector (uses SelectorFacade internally)
        selector = self.get_normalized_selector(context, "selector")

        # Find element with smart healing
        element, final_selector, method = await self.find_element_smart(
            page, context, selector
        )

        # method will be "anchor", "original", or healing tier name
```

## Caching

Selector validation results are cached for performance:

```python
facade = SelectorFacade.get_instance()

# Get cache statistics
stats = facade.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']:.1%}")

# Clear cache for a specific URL
cleared = facade.clear_cache(page_url="https://example.com")

# Enable/disable caching
facade.disable_cache()  # For debugging
facade.enable_cache()
```

## Migration Guide

### From selector_normalizer.py

```python
# OLD (deprecated)
from casare_rpa.utils.selectors.selector_normalizer import normalize_selector

# NEW
from casare_rpa.utils.selectors import normalize_selector
```

### From SelectorService

```python
# OLD
from casare_rpa.application.services.selector_service import SelectorService
result = SelectorService.normalize(selector)

# NEW
from casare_rpa.utils.selectors import SelectorFacade
facade = SelectorFacade.get_instance()
result = facade.normalize(selector)
```

### From Canvas Dialogs

```python
# OLD (deprecated)
from casare_rpa.presentation.canvas.selectors import ElementSelectorDialog

# NEW
from casare_rpa.presentation.canvas.selectors import UnifiedSelectorDialog
```

## Testing

```bash
# Run selector subsystem tests
pytest tests/unit/utils/selectors/ -v

# Run with coverage
pytest tests/unit/utils/selectors/ --cov=casare_rpa.utils.selectors
```
