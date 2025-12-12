# Browser Automation Nodes

Browser nodes provide web automation using Playwright. They support Chromium, Firefox, and WebKit browsers with powerful features like element interaction, data extraction, and form handling.

## Overview

| Category | Nodes |
|----------|-------|
| **Lifecycle** | LaunchBrowserNode, CloseBrowserNode, NewTabNode |
| **Navigation** | GoToURLNode, GoBackNode, GoForwardNode, RefreshPageNode |
| **Interaction** | ClickElementNode, TypeTextNode, SelectDropdownNode, PressKeyNode, ImageClickNode |
| **Extraction** | ExtractTextNode, GetAttributeNode, ScreenshotNode, TableScraperNode |
| **Forms** | FormFieldNode, FormFillerNode, DetectFormsNode |
| **Smart Selection** | SmartSelectorNode, VisualFindNode |
| **Waiting** | WaitForElementNode, WaitForNavigationNode |

---

## Lifecycle Nodes

### LaunchBrowserNode

Launches a new browser instance with configurable options.

#### Description

Opens a browser (Chromium, Firefox, or WebKit) using Playwright. The browser instance is stored in the execution context for use by subsequent nodes. Supports headless mode, custom profiles, anti-detection settings, and window state control.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `url` | STRING | No | `""` | Initial URL to navigate to |
| `browser_type` | CHOICE | No | `"chromium"` | Browser engine: chromium, firefox, webkit |
| `headless` | BOOLEAN | No | `false` | Run without visible window |
| `window_state` | CHOICE | No | `"normal"` | Window state: normal, maximized, minimized |
| `do_not_close` | BOOLEAN | No | `true` | Keep browser open after workflow |
| `profile_mode` | CHOICE | No | `"none"` | Profile: none, custom, chrome_default, edge_default |
| `viewport_width` | INTEGER | No | `1280` | Viewport width in pixels |
| `viewport_height` | INTEGER | No | `720` | Viewport height in pixels |
| `slow_mo` | INTEGER | No | `0` | Slow down operations (ms) for debugging |
| `user_agent` | STRING | No | `""` | Custom user agent string |
| `locale` | STRING | No | `""` | Browser locale (e.g., en-US) |
| `timezone_id` | STRING | No | `""` | Timezone (e.g., America/New_York) |
| `color_scheme` | CHOICE | No | `"light"` | Preferred color scheme: light, dark |
| `ignore_https_errors` | BOOLEAN | No | `false` | Ignore SSL certificate errors |
| `proxy_server` | STRING | No | `""` | Proxy server URL |
| `user_data_dir` | STRING | No | `""` | Custom profile directory |
| `retry_count` | INTEGER | No | `0` | Number of retries on failure |
| `retry_interval` | INTEGER | No | `2000` | Delay between retries (ms) |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC | Input | Execution flow |
| `exec_out` | EXEC | Output | Continue execution |
| `url` | STRING | Input | URL override |
| `browser` | BROWSER | Output | Browser instance |
| `page` | PAGE | Output | Page instance |
| `window` | ANY | Output | Desktop window handle |

#### Example Usage

```python
# Basic browser launch
[LaunchBrowser]
    url: "https://example.com"
    browser_type: "chromium"
    headless: false
    window_state: "maximized"

# With persistent profile for login sessions
[LaunchBrowser]
    profile_mode: "chrome_default"
    url: "https://accounts.google.com"
```

---

### CloseBrowserNode

Closes the browser instance and cleans up resources.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `timeout` | INTEGER | No | `30000` | Close timeout (ms) |
| `force_close` | BOOLEAN | No | `false` | Force close even with unsaved changes |
| `retry_count` | INTEGER | No | `0` | Retry count on failure |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC | Input | Execution flow |
| `exec_out` | EXEC | Output | Continue execution |
| `browser` | BROWSER | Input | Browser to close (optional) |

---

## Navigation Nodes

### GoToURLNode

Navigates to a specified URL with configurable wait conditions.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `url` | STRING | Yes | `""` | URL to navigate to |
| `timeout` | INTEGER | No | `30000` | Page load timeout (ms) |
| `wait_until` | CHOICE | No | `"load"` | Wait condition: load, domcontentloaded, networkidle, commit |
| `referer` | STRING | No | `""` | HTTP referer header |
| `retry_count` | INTEGER | No | `0` | Retry count |
| `retry_interval` | INTEGER | No | `1000` | Delay between retries (ms) |
| `screenshot_on_fail` | BOOLEAN | No | `false` | Take screenshot on failure |
| `screenshot_path` | FILE_PATH | No | `""` | Screenshot save path |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC | Input | Execution flow |
| `exec_out` | EXEC | Output | Continue execution |
| `page` | PAGE | Input | Page instance (optional) |
| `url` | STRING | Input | URL override |
| `page` | PAGE | Output | Page passthrough |

#### Wait Conditions

| Condition | Description |
|-----------|-------------|
| `load` | Wait for load event (default) |
| `domcontentloaded` | Wait for DOMContentLoaded |
| `networkidle` | Wait until no network activity for 500ms |
| `commit` | Wait for initial navigation response |

#### Example

```python
[GoToURL]
    url: "https://example.com/login"
    wait_until: "networkidle"
    timeout: 60000
```

---

### GoBackNode

Navigates back in browser history.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `timeout` | INTEGER | No | `30000` | Navigation timeout (ms) |
| `wait_until` | CHOICE | No | `"load"` | Wait condition |
| `retry_count` | INTEGER | No | `0` | Retry count |

---

### GoForwardNode

Navigates forward in browser history.

#### Properties

Same as GoBackNode.

---

### RefreshPageNode

Reloads the current page.

#### Properties

Same as GoBackNode.

---

## Interaction Nodes

### ClickElementNode

Clicks on a page element identified by selector.

#### Description

Finds an element using CSS or XPath selector and performs a click action. Supports various click options including double-click, right-click, and click with modifier keys. Includes selector healing for resilient automation.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `selector` | SELECTOR | Yes | `""` | CSS or XPath selector |
| `fast_mode` | BOOLEAN | No | `false` | Optimize for speed |
| `timeout` | INTEGER | No | `30000` | Element wait timeout (ms) |
| `button` | CHOICE | No | `"left"` | Mouse button: left, right, middle |
| `click_count` | INTEGER | No | `1` | Click count (2 for double-click) |
| `delay` | INTEGER | No | `0` | Delay between mousedown/mouseup (ms) |
| `force` | BOOLEAN | No | `false` | Bypass actionability checks |
| `position_x` | FLOAT | No | `null` | Click X offset |
| `position_y` | FLOAT | No | `null` | Click Y offset |
| `modifiers` | MULTI_CHOICE | No | `[]` | Modifier keys: Alt, Control, Meta, Shift |
| `no_wait_after` | BOOLEAN | No | `false` | Skip post-click waits |
| `trial` | BOOLEAN | No | `false` | Check only, don't click |
| `highlight_before_click` | BOOLEAN | No | `false` | Highlight element first |
| `retry_count` | INTEGER | No | `0` | Retry count |
| `screenshot_on_fail` | BOOLEAN | No | `false` | Screenshot on failure |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC | Input | Execution flow |
| `exec_out` | EXEC | Output | Continue execution |
| `page` | PAGE | Input | Page instance |
| `selector` | STRING | Input | Selector override |
| `page` | PAGE | Output | Page passthrough |

#### Selector Examples

```css
/* CSS Selectors */
#submit-button          /* By ID */
.btn-primary            /* By class */
button[type="submit"]   /* By attribute */
form input:first-child  /* By position */

/* XPath Selectors */
//button[@id='submit']
//input[@name='email']
//div[contains(@class, 'modal')]//button
```

#### Example

```python
# Double-click with modifier key
[ClickElement]
    selector: "#item-row"
    click_count: 2
    modifiers: ["Control"]

# Fast mode for bulk operations
[ClickElement]
    selector: ".checkbox"
    fast_mode: true
```

---

### TypeTextNode

Types text into an input field.

#### Description

Finds an input element and types the specified text. Supports character-by-character typing, field clearing, and post-type key presses. Includes auto-navigation from label to input elements.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `selector` | SELECTOR | Yes | `""` | Input element selector |
| `text` | STRING | Yes | `""` | Text to type |
| `fast_mode` | BOOLEAN | No | `false` | Optimize for speed |
| `delay` | INTEGER | No | `0` | Keystroke delay (ms) |
| `timeout` | INTEGER | No | `30000` | Element wait timeout (ms) |
| `clear_first` | BOOLEAN | No | `true` | Clear field before typing |
| `press_sequentially` | BOOLEAN | No | `false` | Type character-by-character |
| `force` | BOOLEAN | No | `false` | Bypass actionability checks |
| `press_enter_after` | BOOLEAN | No | `false` | Press Enter after typing |
| `press_tab_after` | BOOLEAN | No | `false` | Press Tab after typing |
| `retry_count` | INTEGER | No | `0` | Retry count |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC | Input | Execution flow |
| `exec_out` | EXEC | Output | Continue execution |
| `page` | PAGE | Input | Page instance |
| `selector` | STRING | Input | Selector override |
| `text` | STRING | Input | Text override |
| `page` | PAGE | Output | Page passthrough |

#### Example

```python
# Form filling with Enter to submit
[TypeText]
    selector: "#username"
    text: "{{username}}"
    clear_first: true

[TypeText]
    selector: "#password"
    text: "{{password}}"
    press_enter_after: true

# Slow typing for anti-bot detection
[TypeText]
    selector: "#search"
    text: "search query"
    delay: 50
    press_sequentially: true
```

---

### SelectDropdownNode

Selects an option from a dropdown/select element.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `selector` | SELECTOR | Yes | `""` | Select element selector |
| `value` | STRING | Yes | `""` | Value to select |
| `select_by` | CHOICE | No | `"value"` | Selection method: value, label, index |
| `timeout` | INTEGER | No | `30000` | Element wait timeout (ms) |
| `force` | BOOLEAN | No | `false` | Bypass actionability checks |

#### Example

```python
# Select by visible label
[SelectDropdown]
    selector: "#country"
    value: "United States"
    select_by: "label"

# Select by option value
[SelectDropdown]
    selector: "#priority"
    value: "high"
    select_by: "value"

# Select by index (0-based)
[SelectDropdown]
    selector: "#month"
    value: "0"
    select_by: "index"
```

---

### PressKeyNode

Presses a keyboard key on the page.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `key` | STRING | Yes | `"Enter"` | Key to press |
| `delay` | INTEGER | No | `0` | Delay between keydown/keyup (ms) |
| `timeout` | INTEGER | No | `30000` | Operation timeout (ms) |

#### Supported Keys

```
Enter, Escape, Tab, Backspace, Delete
ArrowUp, ArrowDown, ArrowLeft, ArrowRight
Home, End, PageUp, PageDown
F1-F12
Control+A, Shift+Tab (combinations)
```

#### Example

```python
# Dismiss modal
[PressKey]
    key: "Escape"

# Select all text
[PressKey]
    key: "Control+A"
```

---

### ImageClickNode

Clicks at a location found by image/template matching.

#### Description

Uses computer vision to find a template image on the page and clicks at the center of the matched region. Useful when selectors are unreliable or for visual elements without proper DOM structure.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `image_template` | STRING | Yes | `""` | Base64-encoded template image |
| `similarity_threshold` | FLOAT | No | `0.8` | Match similarity (0.0-1.0) |
| `button` | CHOICE | No | `"left"` | Mouse button |
| `click_count` | INTEGER | No | `1` | Click count |
| `click_offset_x` | INTEGER | No | `0` | X offset from center |
| `click_offset_y` | INTEGER | No | `0` | Y offset from center |
| `timeout` | INTEGER | No | `30000` | Search timeout (ms) |

---

## Extraction Nodes

### ExtractTextNode

Extracts text content from page elements.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `selector` | SELECTOR | Yes | `""` | Element selector |
| `timeout` | INTEGER | No | `30000` | Wait timeout (ms) |
| `trim` | BOOLEAN | No | `true` | Trim whitespace |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `page` | PAGE | Input | Page instance |
| `selector` | STRING | Input | Selector override |
| `text` | STRING | Output | Extracted text |
| `page` | PAGE | Output | Page passthrough |

---

### GetAttributeNode

Gets an attribute value from an element.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `selector` | SELECTOR | Yes | `""` | Element selector |
| `attribute` | STRING | Yes | `""` | Attribute name (e.g., href, src, class) |
| `timeout` | INTEGER | No | `30000` | Wait timeout (ms) |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `page` | PAGE | Input | Page instance |
| `value` | STRING | Output | Attribute value |

---

### ScreenshotNode

Captures a screenshot of the page or element.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `path` | FILE_PATH | No | `""` | Save path (auto-generated if empty) |
| `selector` | SELECTOR | No | `""` | Element selector (full page if empty) |
| `full_page` | BOOLEAN | No | `false` | Capture full scrollable page |
| `type` | CHOICE | No | `"png"` | Image type: png, jpeg |
| `quality` | INTEGER | No | `80` | JPEG quality (0-100) |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `page` | PAGE | Input | Page instance |
| `path` | STRING | Output | Screenshot file path |
| `data` | ANY | Output | Screenshot bytes |

---

### TableScraperNode

Extracts data from HTML tables.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `selector` | SELECTOR | Yes | `"table"` | Table element selector |
| `has_header` | BOOLEAN | No | `true` | First row is header |
| `include_links` | BOOLEAN | No | `false` | Include link URLs |
| `timeout` | INTEGER | No | `30000` | Wait timeout (ms) |

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `page` | PAGE | Input | Page instance |
| `data` | LIST | Output | Table data (list of dicts/lists) |
| `headers` | LIST | Output | Column headers |
| `row_count` | INTEGER | Output | Number of rows |

---

## Form Nodes

### FormFieldNode

Handles individual form fields with smart detection.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `selector` | SELECTOR | Yes | `""` | Field selector |
| `value` | STRING | Yes | `""` | Value to set |
| `field_type` | CHOICE | No | `"auto"` | Field type: auto, text, select, checkbox, radio |

---

### FormFillerNode

Fills multiple form fields from a data dictionary.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `form_selector` | SELECTOR | No | `"form"` | Form container selector |
| `field_mapping` | JSON | Yes | `{}` | Field name to value mapping |
| `submit` | BOOLEAN | No | `false` | Submit form after filling |

#### Example

```python
[FormFiller]
    form_selector: "#registration-form"
    field_mapping: {
        "email": "user@example.com",
        "password": "secure123",
        "country": "US",
        "newsletter": true
    }
    submit: true
```

---

### DetectFormsNode

Detects and analyzes forms on the page.

#### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `page` | PAGE | Input | Page instance |
| `forms` | LIST | Output | Detected form structures |
| `count` | INTEGER | Output | Number of forms found |

---

## Smart Selection Nodes

### SmartSelectorNode

Generates robust selectors with multiple fallback strategies.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `selector` | SELECTOR | Yes | `""` | Initial selector |
| `strategies` | LIST | No | All | Healing strategies to use |

---

### VisualFindNode

Finds elements using visual/image matching.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `template` | STRING | Yes | `""` | Base64 template image |
| `threshold` | FLOAT | No | `0.8` | Match threshold |
| `region` | JSON | No | `null` | Search region bounds |

---

## Wait Nodes

### WaitForElementNode

Waits for an element to appear or meet a condition.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `selector` | SELECTOR | Yes | `""` | Element selector |
| `state` | CHOICE | No | `"visible"` | Wait state: attached, detached, visible, hidden |
| `timeout` | INTEGER | No | `30000` | Wait timeout (ms) |

#### Wait States

| State | Description |
|-------|-------------|
| `attached` | Element exists in DOM |
| `detached` | Element removed from DOM |
| `visible` | Element is visible |
| `hidden` | Element is hidden |

---

### WaitForNavigationNode

Waits for page navigation to complete.

#### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `url` | STRING | No | `""` | Expected URL pattern (regex) |
| `wait_until` | CHOICE | No | `"load"` | Wait condition |
| `timeout` | INTEGER | No | `30000` | Wait timeout (ms) |

---

## Complete Workflow Example

```
[Start]
    |
[LaunchBrowser]
    browser_type: "chromium"
    headless: false
    window_state: "maximized"
    |
[GoToURL]
    url: "https://example.com/login"
    wait_until: "networkidle"
    |
[TypeText]
    selector: "#email"
    text: "{{email}}"
    |
[TypeText]
    selector: "#password"
    text: "{{password}}"
    |
[ClickElement]
    selector: "button[type='submit']"
    |
[WaitForNavigation]
    url: ".*dashboard.*"
    timeout: 10000
    |
[ExtractText]
    selector: ".welcome-message"
    |
[Log]
    message: "Login successful: {extracted_text}"
    |
[CloseBrowser]
    |
[End]
```

## Best Practices

1. **Use `wait_until: "networkidle"`** for pages with dynamic content
2. **Enable `fast_mode`** for bulk operations where reliability is less critical
3. **Use variables** for credentials and sensitive data: `{{password}}`
4. **Add retries** for flaky elements: `retry_count: 3`
5. **Enable screenshots on failure** for debugging: `screenshot_on_fail: true`
6. **Use specific selectors**: Prefer `#id` over complex XPath
7. **Handle popups**: Add `PressKeyNode` with "Escape" to dismiss modals
