# Fallback Selector Pattern

## Pattern
Provide primary + backup selectors for critical elements. Try primary, fallback to backup if fails.

## Implementation

```python
from typing import List
from playwright.async_api import Page

class ElementFinder:
    """Find element using selector fallbacks."""

    async def find(
        self,
        page: Page,
        selectors: List[str],
        timeout: int = 5000,
    ):
        """Try each selector until one works."""
        for selector in selectors:
            try:
                element = await page.wait_for_selector(
                    selector,
                    timeout=timeout // len(selectors),  # Distribute timeout
                    state='visible'
                )
                if element:
                    logger.info(f"Found element with: {selector}")
                    return element
            except Exception:
                continue

        raise Exception(f"No element found. Tried: {selectors}")


# Usage
async def click_login_button(page: Page):
    finder = ElementFinder()

    # Try multiple selector strategies
    login_btn = await finder.find(page, [
        '[data-testid="login-button"]',           # Preferred: test attribute
        'button[type="submit"]',                   # Fallback: semantic
        'button:has-text("Log In")',               # Fallback: text-based
        '#login-form button',                      # Fallback: structural
    ])

    await login_btn.click()
```

## Versioned Selectors

```python
# For apps with known breaking changes
SELECTORS = {
    "v1": '[data-testid="old-login-btn"]',
    "v2": '[data-testid="login-button"]',
    "v3": 'button[type="submit"]',
}

async def get_button_for_version(page: Page, app_version: str):
    selector = SELECTORS.get(app_version, SELECTORS["v3"])
    return await page.wait_for_selector(selector)
```

## Document Why Fallback Exists

```python
# Selector fallback reason:
# Primary: [data-testid="submit"]
#   - May not be present in older deployments
# Fallback 1: button[type="submit"]
#   - Standard semantic, always present
# Fallback 2: button:has-text("Submit")
#   - Last resort, text changes in i18n
SUBMIT_SELECTORS = [
    '[data-testid="submit"]',
    'button[type="submit"]',
    'button:has-text("Submit")',
]
```

---

*When to Use*: Critical user flows (login, checkout, submit) where selector failure = blocked test.
