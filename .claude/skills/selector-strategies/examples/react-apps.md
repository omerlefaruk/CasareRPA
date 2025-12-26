# React/SPA App Selectors

## Scenario
Single-page app with dynamically rendered components, often using CSS-in-JS with unstable classes.

## Good

```python
# data-testid - explicitly for testing
BUTTON = '[data-testid="submit-button"]'
MODAL = '[data-testid="confirmation-modal"]'

# aria attributes for accessibility
CLOSE_BUTTON = 'button[aria-label="Close modal"]'
DIALOG = '[role="dialog"]'

# Semantic HTML + stable attributes
SUBMIT = 'form[id="checkout-form"] button[type="submit"]'
INPUT = 'input[name="email"][required]'

# Playwright's locators (best for React)
await page.get_by_test_id("submit-button").click()
await page.get_by_role("button", name="Submit").click()
await page.get_by_label("Email").fill("user@example.com")
```

## Bad

```python
# CSS-in-JS classes are hash-generated, change every build
BUTTON = '.css-1a2b3c4-button'  # Changes on deployment
CONTAINER = '.MuiBox-root-jss123'  # Material-UI - unstable

# Dynamic IDs from rendering
ELEMENT = '#root-12345-child-67890'  # Generated IDs

# Class chains into styled-components
BUTTON = '.sc-bdVaJa.bVfhSs button'  # Obfuscated class names
```

## Fallback When No Test IDs

```python
# Chain semantic attributes
BUTTON = 'form[action="/checkout"] button[type="submit"]'

# Use visible text (Playwright locators do this well)
BUTTON = 'button:has-text("Complete Purchase")'

# XPath with multiple conditions
INPUT_XPATH = '//input[@type="email" and @placeholder="Enter email"]'
```

---

*Why Good Works*: React apps frequently change class names due to hot reloading, build processes, and CSS-in-JS. Test attributes never change for styling reasons.
