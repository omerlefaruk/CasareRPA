"""
Selector Format Support in CasareRPA
====================================

CasareRPA now supports ANY selector format through automatic normalization.
You can use XPath, CSS, ARIA, data attributes, text selectors, or any combination
without worrying about the format - the system automatically adapts.

Supported Selector Formats
--------------------------

1. **XPath Selectors**
   - Standard: `//input[@id="search"]`
   - With prefix: `xpath=//*[@class="btn"]`
   - Attributes: `//*[@data-testid="submit"]`
   - Text: `//*[contains(text(), "Click me")]`
   - ARIA: `//*[@aria-label="Search"]`

2. **CSS Selectors**
   - ID: `#myElementId`
   - Class: `.button-primary`
   - Attribute: `[data-testid="submit-btn"]`
   - ARIA: `[aria-label="Search"]`
   - Combined: `button.primary[type="submit"]`
   - Child: `div > button`
   - Descendant: `form button`

3. **Text Selectors**
   - Exact match: `text=Click me`
   - Partial: `text=Click` (matches "Click me", "Click here", etc.)

4. **Mixed/Complex Selectors**
   - Playwright chaining: `#container >> button.submit`
   - Multiple attributes: `[data-testid="btn"][aria-label="Submit"]`

How It Works
-----------

When you provide a selector to any node (Click Element, Type Text, Wait For Element, etc.),
the system:

1. Detects the selector type automatically
2. Normalizes it to Playwright's expected format
3. Uses it seamlessly with the browser automation

Examples in Practice
-------------------

**Before (had to match exact format):**
```python
# Only XPath worked in some cases
selector = "//*[@id='APjFqb']"
```

**Now (any format works):**
```python
# All of these work:
selector = "#APjFqb"                      # CSS ID
selector = "//*[@id='APjFqb']"           # XPath
selector = "[id='APjFqb']"               # CSS attribute
selector = "xpath=//input[@id='APjFqb']" # Explicit XPath
selector = "textarea#APjFqb"             # CSS with tag
```

**From Selector Picker:**
When you use the selector picker dialog, you get multiple options:
- XPath: `//*[@id="APjFqb"]` ✓ Works
- CSS: `#APjFqb` ✓ Works
- Data attr: `[data-testid="search"]` ✓ Works
- ARIA: `[aria-label="Search"]` ✓ Works
- Text: `text=Search` ✓ Works

Paste any of them directly into your nodes!

Node Compatibility
-----------------

All interaction and data nodes support this:
- ✓ Click Element
- ✓ Type Text
- ✓ Select Dropdown
- ✓ Wait For Element
- ✓ Extract Text
- ✓ Get Attribute
- ✓ All other selector-based nodes

Technical Details
----------------

The normalization happens in `selector_normalizer.py`:
- Detects selector type (XPath, CSS, text)
- Converts to Playwright-compatible format
- Handles edge cases (absolute paths, missing prefixes, etc.)
- Preserves already-correct selectors unchanged

Performance
----------

- Zero overhead for already-correct selectors
- Minimal overhead (<1ms) for normalization
- No network calls or page interactions
- All processing is local string manipulation

Best Practices
-------------

1. **Use what works for you**: CSS is often shorter, XPath is more powerful
2. **Trust the picker**: The selector dialog shows multiple options - use any
3. **Test in dialog**: Use the "Test" button to verify before using
4. **Mix and match**: Different nodes can use different selector types
5. **Copy/paste freely**: Selectors from any source work out of the box

Common Patterns
--------------

**Finding by text content:**
```
XPath:  //*[contains(text(), "Submit")]
Text:   text=Submit
```

**Finding by data attribute:**
```
CSS:    [data-testid="login-btn"]
XPath:  //*[@data-testid="login-btn"]
```

**Finding by ARIA label:**
```
CSS:    [aria-label="Close dialog"]
XPath:  //*[@aria-label="Close dialog"]
```

**Complex combinations:**
```
CSS:    button.primary[data-action="submit"]
XPath:  //button[contains(@class, "primary")][@data-action="submit"]
```

Troubleshooting
--------------

**If a selector doesn't work:**
1. Test it in the selector dialog first
2. Check the Playwright error message for hints
3. Try the auto-generated alternatives from the picker
4. Use the "Highlight" button to see what it matches

**Common issues:**
- Dynamic IDs: Use data attributes or ARIA labels instead
- Shadow DOM: Playwright handles this automatically
- Timing: Add "Wait For Element" before interaction
- Multiple matches: Refine selector to be more specific

For More Help
------------

See:
- Playwright selector documentation: https://playwright.dev/docs/selectors
- CasareRPA selector dialog: Right-click any selector input → "Pick Element"
- Test mode: Use Test/Highlight buttons before running workflow
"""

if __name__ == "__main__":
    print(__doc__)
