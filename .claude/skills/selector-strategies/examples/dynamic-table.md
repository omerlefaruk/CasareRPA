# Dynamic Table Selectors

## Scenario
Table with rows that load dynamically. Need to click "Edit" button for row containing "John Doe".

## Good

```python
# Find row by text, then click button within that row
ROW_BY_NAME = 'tr:has-text("John Doe")'
EDIT_BUTTON_IN_ROW = 'tr:has-text("John Doe") button[data-action="edit"]'

# XPath version (often cleaner for complex conditions)
ROW_BY_NAME_XPATH = '//tr[td[contains(text(),"John Doe")]]'
EDIT_BUTTON_XPATH = '//tr[td[contains(text(),"John Doe")]]//button[@data-action="edit"]'

# For Playwright specifically
async def click_edit_for_user(page, username):
    await page.get_by_role('row', name=username).get_by_role('button', name='Edit').click()
```

## Bad

```python
# Assumes row position - breaks when data changes
EDIT_ROW_3 = 'table tbody tr:nth-child(3) button.edit-btn'

# Assumes static table length
LAST_ROW = 'table tbody tr:last-child button'

# Too broad - matches any row with any text
ANY_EDIT_BUTTON = 'tr button[data-action="edit"]'
```

## Also Good: Header-anchored

```python
# Anchor to table by its header, then find row
TABLE = 'table:has(th:text("Username"))'
ROW_IN_TABLE = f'{TABLE} tr:has-text("John Doe")'
```

---

*Why Good Works*: Selectors based on data (row content) not position. Table can have 1 or 1000 rows, selector still works.
