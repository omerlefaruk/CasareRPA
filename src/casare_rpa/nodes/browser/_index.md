# Browser Package Index

Browser automation base classes and utilities.

## Files

| File | Purpose | Key Exports |
|------|---------|-------------|
| `__init__.py` | Package exports | BrowserBaseNode, get_page_from_context |
| `browser_base.py` | Base class | BrowserBaseNode |
| `property_constants.py` | Shared properties | BROWSER_TIMEOUT, BROWSER_SELECTOR |
| `smart_selector_node.py` | AI selectors | SmartSelectorNode |
| `form_filler_node.py` | Form automation | FormFillerNode |
| `table_scraper_node.py` | Table extraction | TableScraperNode |
| `evaluate_node.py` | JavaScript execution | BrowserEvaluateNode |
| `detect_forms_node.py` | Form detection | DetectFormsNode |
| `visual_find_node.py` | Visual matching | VisualFindNode |

## Entry Points

```python
from casare_rpa.nodes.browser import (
    BrowserBaseNode,
    get_page_from_context,
    take_failure_screenshot,
    BROWSER_TIMEOUT,
    BROWSER_SELECTOR,
)
```

## Key Patterns

All browser nodes should:
1. Extend `BrowserBaseNode`
2. Use `get_page_from_context(context)` for page access
3. Use property constants for common settings
4. Call `take_failure_screenshot` on errors
