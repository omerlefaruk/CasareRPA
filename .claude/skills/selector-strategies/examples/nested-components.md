# Nested Component Selectors

## Scenario
Click a button inside a card, where there are multiple similar cards on page.

## Good

```python
# Anchor to specific card by unique identifier, then descend
CARD = '[data-testid="product-card-12345"]'
BUY_BUTTON = f'{CARD} [data-testid="buy-button"]'

# Or use aria-label for card identification
CARD = '[aria-label="Product: Wireless Mouse"]'
BUY_BUTTON = f'{CARD} button:has-text("Buy")'

# XPath for traversing up then down
BUY_BUTTON_XPATH = '//div[@data-product-id="12345"]//button[text()="Buy"]'
```

## Bad

```python
# Assumes card position - breaks with responsive layout
CARD = 'div.products-grid div:nth-child(3)'

# Deep traversal - any structural change breaks it
BUY_BUTTON = 'div.container > div.row > div.col-md-4 > div.card > div.card-body > button.btn-primary'

# Relies on adjacent text that might change
BUY_BUTTON = 'button + span:has-text("$29.99")'
```

## Also Good: Sibling Navigation

```python
# From product title element to nearby button
PRODUCT_TITLE = '[data-testid="product-title"]'
BUY_BUTTON = f'{PRODUCT_TITLE} ~ div [data-testid="buy-button"]'

# XPath following-sibling
BUY_BUTTON_XPATH = '//*[@data-testid="product-title"]/following-sibling::div//button[@data-testid="buy-button"]'
```

---

*Why Good Works*: Card identification is independent of layout. Card can move anywhere on page, selector still finds it.
