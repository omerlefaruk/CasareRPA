# Dropdown Menu Selectors

## Scenario
Interact with dropdown menus (often implemented as `ul/li`, `div` with `role="menuitem"`, or custom dropdowns).

## Good

```python
# Use ARIA roles when available
MENU_BUTTON = 'button[aria-haspopup="menu"]'
MENU_ITEM = '[role="menuitem"]:has-text("Save")'

# data-testid on menu items
MENU_ITEM = '[data-testid="menu-item-save"]'

# Anchor to menu container first
MENU = '[data-testid="action-menu"]'
MENU_ITEM = f'{MENU} [data-value="save"]'

# Playwright's role-based locators (most robust)
await page.get_by_role('button', name='Actions').click()
await page.get_by_role('menuitem', name='Save').click()
```

## Bad

```python
# Position-based - breaks if menu items reordered
MENU_ITEM = 'ul.dropdown-menu li:nth-child(3) a'

# Class-based on styling classes
MENU_ITEM = 'ul.nav.navbar-nav li.dropdown.open ul li a'

# Assumes visible state
MENU_ITEM = 'li.dropdown.open > ul > li > a[href="#save"]'
```

## Also Good: Text + Attribute Combo

```python
# Multiple attributes for specificity
MENU_ITEM = '[role="menuitem"][data-action="save"]:has-text("Save")'

# XPath for OR conditions (multiple text variants)
MENU_ITEM_XPATH = '''
    //*
    [@role="menuitem" or @data-action="save"]
    [contains(text(), "Save") or contains(text(), "save")]
'''
```

## Handling Submenus

```python
# Navigate through nested menus
PARENT_MENU = '[role="menuitem"][aria-haspopup="true"]'
SUBMENU_ITEM = '[role="menuitem"][aria-level="2"]:has-text("Export")'

# Wait strategy
await page.expect_response('**/api/menu/**')
await page.click(PARENT_MENU)
await page.wait_for_selector(SUBMENU_ITEM, state='visible')
await page.click(SUBMENU_ITEM)
```

---

*Why Good Works*: ARIA roles are part of the accessibility contract and rarely change. Position-based selectors break immediately when menu items are reordered.
