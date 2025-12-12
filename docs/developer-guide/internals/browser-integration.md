# Browser Integration Internals

This document describes CasareRPA's integration with Playwright for browser automation.

## Overview

CasareRPA uses Playwright for cross-browser automation. The integration includes:
- Singleton browser lifecycle management
- Multi-page handling
- Self-healing selector system
- Screenshot capture
- Network interception

## PlaywrightManager

**Location:** `src/casare_rpa/infrastructure/browser/playwright_manager.py`

Singleton manager for Playwright instance lifecycle.

### Why Singleton?

Starting Playwright has 200-500ms overhead. The singleton pattern:
- Pays startup cost only once per process
- Avoids memory churn from repeated initialization
- Enables faster browser launches on subsequent calls

### Usage

```python
from casare_rpa.infrastructure.browser import (
    PlaywrightManager,
    get_playwright_singleton,
    shutdown_playwright_singleton,
)

# Get Playwright instance (creates if needed)
pw = await PlaywrightManager.get_playwright()
browser = await pw.chromium.launch()

# Or use convenience function
pw = await get_playwright_singleton()

# Cleanup on app shutdown
await PlaywrightManager.cleanup()
# Or
await shutdown_playwright_singleton()
```

### Implementation

```python
class PlaywrightManager:
    _instance: Optional["PlaywrightManager"] = None
    _playwright = None
    _lock: threading.Lock = threading.Lock()

    @classmethod
    async def get_playwright(cls):
        if cls._playwright is not None:
            return cls._playwright

        with cls._lock:
            # Double-check after acquiring lock
            if cls._playwright is not None:
                return cls._playwright

            from playwright.async_api import async_playwright
            cls._playwright = await async_playwright().start()
            return cls._playwright

    @classmethod
    async def cleanup(cls) -> None:
        with cls._lock:
            if cls._playwright is not None:
                await cls._playwright.stop()
                cls._playwright = None
```

---

## Browser Lifecycle

### Typical Node Flow

```
LaunchBrowserNode
    |
    +-> PlaywrightManager.get_playwright()
    +-> pw.chromium.launch(headless=False)
    +-> context.set_browser(browser)
    +-> browser.new_context()
    +-> context.add_browser_context(browser_context)
    +-> browser_context.new_page()
    +-> context.set_active_page(page)
    |
NavigateNode
    |
    +-> page = context.get_active_page()
    +-> await page.goto(url)
    |
ClickElementNode
    |
    +-> page = context.get_active_page()
    +-> element = await page.wait_for_selector(selector)
    +-> await element.click()
    |
CloseBrowserNode
    |
    +-> Triggers cleanup via ExecutionContext
```

### Browser Resource Manager

**Location:** `src/casare_rpa/infrastructure/resources/browser_resource_manager.py`

Manages browser instances within ExecutionContext:

```python
class BrowserResourceManager:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.browser_contexts: List[BrowserContext] = []
        self.pages: Dict[str, Page] = {}
        self.active_page: Optional[Page] = None

    def set_active_page(self, page: Page, name: str = "default") -> None:
        self.pages[name] = page
        self.active_page = page

    def get_active_page(self) -> Optional[Page]:
        return self.active_page

    async def cleanup(self, skip_browser: bool = False) -> None:
        # Close all pages
        for name, page in list(self.pages.items()):
            try:
                await page.close()
            except Exception:
                pass
        self.pages.clear()

        # Close browser contexts
        for ctx in self.browser_contexts:
            try:
                await ctx.close()
            except Exception:
                pass
        self.browser_contexts.clear()

        # Close browser (unless skip flag)
        if not skip_browser and self.browser:
            try:
                await self.browser.close()
            except Exception:
                pass
            self.browser = None
```

### Keep Browser Open

Workflows can prevent browser closure:

```python
# In workflow node
context.set_variable("_browser_do_not_close", True)

# Checked during cleanup
skip_browser_close = context.get_variable("_browser_do_not_close", False)
await context._resources.cleanup(skip_browser=skip_browser_close)
```

---

## Page Management

### Multiple Pages/Tabs

```python
# Create new tab
new_page = await browser_context.new_page()
context.add_page(new_page, "tab_2")

# Switch between pages
context.set_active_page(context.get_page("tab_2"))

# Close specific tab
context.close_page("tab_2")
```

### Page in Execution Context

```python
# Setting page (from LaunchBrowserNode)
context.set_active_page(page, name="default")

# Getting page (from any browser node)
page = context.get_active_page()

# Named pages
page = context.get_page("checkout_tab")
```

---

## Selector Healing

**Location:** `src/casare_rpa/infrastructure/browser/healing/`

CasareRPA includes a tiered self-healing selector system to handle UI changes gracefully.

### Healing Tiers

| Tier | Strategy | Speed | Reliability |
|------|----------|-------|-------------|
| 0 | Original selector | Fastest | Baseline |
| 1 | Heuristic | Fast (~50ms) | Good |
| 2 | Anchor-based | Medium (~100ms) | Better |
| 3 | Computer Vision | Slow (~2000ms) | High |
| 4 | Vision AI (GPT-4V) | Slowest (~10s) | Highest |

### Usage

```python
from casare_rpa.infrastructure.browser.healing import (
    SelectorHealingChain,
    create_healing_chain,
)

# Create chain with CV and Vision AI fallbacks
chain = create_healing_chain(
    healing_budget_ms=400.0,      # Tier 1-2 budget
    cv_budget_ms=2000.0,          # Tier 3 budget
    vision_budget_ms=10000.0,     # Tier 4 budget
    enable_cv=True,
    enable_vision=True,
    vision_model="gpt-4o",
)

# During recording, capture element context
await chain.capture_element_context(page, "#submit-btn")

# During playback, use healing chain
result = await chain.locate_element(page, "#submit-btn")
if result.success:
    if result.element:
        await result.element.click()
    elif result.is_cv_result:
        # CV returns coordinates, not element
        x, y = result.cv_click_coordinates
        await page.mouse.click(x, y)
```

### Tier 1: Heuristic Healing

Attribute-based fallbacks using element fingerprints:

```python
class ElementFingerprint:
    tag_name: str
    id: Optional[str]
    classes: List[str]
    text_content: str
    attributes: Dict[str, str]
    data_attributes: Dict[str, str]

# Healing strategies:
# 1. Try by ID if available
# 2. Try by data-testid
# 3. Try by unique class combination
# 4. Try by text content
```

### Tier 2: Anchor-based Healing

Uses spatial relationships to nearby stable elements:

```python
class SpatialContext:
    element_bounds: BoundingBox
    anchor_elements: List[AnchorElement]  # Nearby stable elements
    relative_positions: Dict[str, RelativePosition]

# Healing flow:
# 1. Find anchor elements (labels, headings, etc.)
# 2. Calculate relative position from anchors
# 3. Search for elements at expected positions
```

### Tier 3: Computer Vision

OCR and template matching when DOM-based healing fails:

```python
class CVHealer:
    async def heal(self, page, selector, search_text, context):
        # 1. Take screenshot
        screenshot = await page.screenshot()

        # 2. Try OCR text detection
        if search_text:
            coords = self._ocr_find_text(screenshot, search_text)
            if coords:
                return CVHealingResult(success=True, ...)

        # 3. Try template matching
        if context and context.template_image:
            coords = self._template_match(screenshot, context.template_image)
            if coords:
                return CVHealingResult(success=True, ...)
```

### Tier 4: Vision AI

Uses GPT-4V or Claude Vision for natural language element finding:

```python
class VisionElementFinder:
    async def find_element(self, screenshot, description, model):
        # 1. Send screenshot to vision model
        # 2. Describe element to find: "blue Submit button in the form"
        # 3. Model returns bounding box coordinates
        # 4. Return center coordinates for clicking
```

### Healing Telemetry

```python
# Get healing statistics
stats = chain.get_stats()
# {
#     "total_attempts": 1500,
#     "success_rate": 0.95,
#     "tier_breakdown": {
#         "original": 0.85,
#         "heuristic": 0.08,
#         "anchor": 0.05,
#         "cv": 0.02
#     },
#     "avg_healing_time_ms": 45.2
# }

# Find problematic selectors
problematic = chain.get_problematic_selectors(
    min_uses=5,
    max_success_rate=0.8
)
```

---

## Screenshot Capture

### Full Page Screenshot

```python
# In browser node
page = context.get_active_page()
screenshot_bytes = await page.screenshot(
    type="png",
    full_page=True,
)

# Save to file
await page.screenshot(path="screenshot.png")
```

### Element Screenshot

```python
element = await page.wait_for_selector("#target")
screenshot = await element.screenshot()
```

### Viewport Screenshot with Clipping

```python
screenshot = await page.screenshot(
    clip={
        "x": 0,
        "y": 0,
        "width": 800,
        "height": 600,
    }
)
```

---

## Network Interception

### Request Interception

```python
async def intercept_request(route, request):
    if "api.example.com" in request.url:
        # Modify or block requests
        await route.abort()
    else:
        await route.continue_()

await page.route("**/*", intercept_request)
```

### Response Interception

```python
async def intercept_response(response):
    if "api.example.com" in response.url:
        body = await response.body()
        # Process response data

page.on("response", intercept_response)
```

### HAR Recording

```python
# Record network traffic
await browser_context.route_from_har(
    "recording.har",
    update=True,  # Update HAR file
)
```

---

## Browser Node Base Class

**Location:** `src/casare_rpa/nodes/browser/browser_base.py`

All browser nodes inherit from BrowserBaseNode:

```python
class BrowserBaseNode(BaseNode):
    """Base class for browser automation nodes."""

    def get_page(self, context) -> Page:
        """Get active page or raise error."""
        page = context.get_active_page()
        if not page:
            raise RuntimeError("No active browser page")
        return page

    async def wait_for_selector(
        self,
        page: Page,
        selector: str,
        timeout: int = 30000,
        state: str = "visible"
    ):
        """Wait for element with healing support."""
        try:
            return await page.wait_for_selector(
                selector,
                timeout=timeout,
                state=state,
            )
        except PlaywrightTimeoutError:
            # Attempt healing
            if self._healing_chain:
                result = await self._healing_chain.locate_element(
                    page, selector
                )
                if result.success:
                    return result.element
            raise
```

---

## Error Handling

### Common Browser Errors

| Error | Error Code | Cause |
|-------|------------|-------|
| TimeoutError | `ELEMENT_NOT_FOUND` | Selector not found within timeout |
| Element detached | `ELEMENT_STALE` | Element removed from DOM |
| Navigation failed | `NAVIGATION_FAILED` | Page load error |
| Browser closed | `BROWSER_CLOSED` | Browser unexpectedly closed |

### Retry Pattern

```python
async def click_with_retry(page, selector, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            element = await page.wait_for_selector(selector)
            await element.click()
            return True
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            await asyncio.sleep(1)
```

---

## Performance Tips

### Launch Options

```python
browser = await pw.chromium.launch(
    headless=True,  # Faster execution
    args=[
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--no-sandbox",
    ],
)
```

### Context Options

```python
context = await browser.new_context(
    viewport={"width": 1920, "height": 1080},
    ignore_https_errors=True,
    java_script_enabled=True,
)
```

### Waiting Strategies

```python
# Wait for network idle (slowest but most reliable)
await page.goto(url, wait_until="networkidle")

# Wait for DOM content loaded (faster)
await page.goto(url, wait_until="domcontentloaded")

# Wait for specific element (most precise)
await page.wait_for_selector("#main-content")
```

---

## Related Documentation

- [Execution Engine](execution-engine.md) - Overall execution architecture
- [Desktop Integration](desktop-integration.md) - Windows desktop automation
- [Error Codes Reference](../../reference/error-codes.md) - Browser error codes
