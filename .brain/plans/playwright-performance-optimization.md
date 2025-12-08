# Playwright Performance Optimization Research

**Date**: 2025-12-05
**Status**: COMPLETE
**Researcher**: Claude (Research Agent)

---

## Executive Summary

This research covers Playwright browser automation performance optimization techniques. CasareRPA already implements many best practices through its `BrowserContextPool` and `UnifiedResourceManager`. This document identifies optimization opportunities and confirms existing good patterns.

---

## 1. Browser Context vs Browser Instance Reuse

### Key Finding
Browser contexts are "fast and cheap to create" while launching new browser instances is expensive.

### Performance Hierarchy (fastest to slowest)
1. **Reuse existing page** - Fastest, reset state between uses
2. **Create new page in existing context** - Fast, isolated within context
3. **Create new context in existing browser** - Medium, fully isolated
4. **Launch new browser** - Slow, only when necessary

### CasareRPA Current Implementation
Located in `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\utils\pooling\browser_pool.py`:
- `BrowserContextPool` class implements proper context pooling
- Reuses single browser instance with multiple contexts
- Supports min/max pool sizes (default: min=1, max=10)
- Context age tracking and idle cleanup

**Assessment**: GOOD - Already follows best practices.

### Recommendations
1. Consider pre-warming 2-3 contexts on pool initialization for faster first-use
2. Current 5-minute max_context_age is reasonable; could extend to 10 minutes for long workflows

---

## 2. Page Pooling Patterns

### Best Practices
```python
# Page reset between uses (current implementation does this)
async def reset_page_state(page):
    await page.goto('about:blank')
    # Context.clear_cookies() called at context level
```

### CasareRPA Current Implementation
The `BrowserContextPool.release()` method:
- Clears cookies via `context.clear_cookies()`
- Closes all pages in context
- Returns context to available pool

**Assessment**: GOOD - Context cleanup is thorough.

### Optimization Opportunity
Consider page-level pooling within contexts for workflows that create many tabs:
```python
class PagePool:
    """Pool pages within a single context for tab-heavy workflows."""
    async def acquire_page(self) -> Page:
        if self._available_pages:
            page = self._available_pages.pop()
            await page.goto('about:blank')
            return page
        return await self._context.new_page()
```

---

## 3. Selector Engine Performance

### Performance Ranking (fastest to slowest)
1. **CSS selectors with ID** - `#my-element` - Browser-native, O(1)
2. **CSS selectors with class** - `.my-class` - Browser-native, fast
3. **CSS attribute selectors** - `[data-testid="x"]` - Browser-native
4. **Playwright role locators** - `getByRole()` - Optimized, resilient
5. **XPath** - `//div[@id="x"]` - Slower, but powerful for traversals
6. **Text selectors** - `text=Hello` - Playwright-optimized

### Playwright's Recommended Priority
1. `page.getByRole()` - Best for accessibility and resilience
2. `page.getByTestId()` - Fast and stable for test-specific selectors
3. `page.getByText()` - User-visible, resilient to structure changes

### Key Insight
> "Every locator operation retrieves fresh DOM elements."

This means resilient selectors reduce flaky retries - **overall faster** than "fast" but fragile selectors.

### CasareRPA Recommendations
For RPA scenarios (unlike testing):
1. **Prefer `[data-*]` attributes** when available - fast and stable
2. **Use CSS over XPath** unless navigating UP the DOM tree
3. **Avoid long chained selectors** like `#tsf > div:nth-child(2) > ...`
4. **Consider caching element handles** for repeated operations on same element

---

## 4. Network Interception Overhead

### Performance Impact
- Each intercepted request adds latency (round-trip to automation process)
- Overhead is typically 2-5ms per request
- Can accumulate significantly with many requests

### Best Practices
```python
# GOOD: Specific pattern
await page.route('**/api/**', handler)

# BAD: Intercepts everything
await page.route('**/*', handler)
```

### Resource Blocking for Speed
Blocking unnecessary resources can provide **2-4x speedup** for page loads:

```python
BLOCK_RESOURCE_TYPES = ['image', 'stylesheet', 'font', 'media']

async def block_resources(route):
    if route.request.resource_type in BLOCK_RESOURCE_TYPES:
        await route.abort()
    else:
        await route.continue_()

await page.route('**/*', block_resources)
```

### Benchmark Data
- Without blocking: ~1300-1500ms page load
- With blocking (images/CSS/fonts): ~300-500ms page load

### CasareRPA Recommendations
1. Add optional `block_resources` parameter to `LaunchBrowserNode`
2. Create `SetResourceBlockingNode` for workflow-level control
3. Default to allowing all resources (preserve current behavior)
4. For scraping workflows, recommend blocking images/fonts/media

---

## 5. Screenshot Optimization

### Format Comparison
| Format | Size | Speed | Quality |
|--------|------|-------|---------|
| PNG | Largest | Slow | Lossless |
| JPEG | Medium | Fast | Lossy (configurable) |
| WebP | Smallest | Fast | Best compression |

### Options Affecting Performance
```python
await page.screenshot(
    type='jpeg',          # Faster than PNG
    quality=80,           # Lower = faster, smaller
    full_page=False,      # Element/viewport faster than full page
    scale='css',          # 'device' for higher DPI, slower
)
```

### Full Page vs Element Screenshots
- **Element screenshots** - Faster, smaller file, focused
- **Full page screenshots** - Requires scrolling/stitching, may fail with lazy-loaded content

### CasareRPA Recommendations
1. Default to JPEG with 85% quality for general use
2. Use PNG only when transparency/precision needed
3. Consider WebP for modern workflows (best size/quality ratio)
4. Add `optimize_size` parameter to `ScreenshotNode`

---

## 6. Parallel Page Operations

### Pattern: Promise.all for Independent Operations
```python
# Run multiple navigations in parallel
results = await asyncio.gather(
    page1.goto('https://site1.com'),
    page2.goto('https://site2.com'),
    page3.goto('https://site3.com'),
)
```

### Context-Level Parallelism
- Multiple contexts can run truly in parallel
- Pages within same context share network/cookie state
- Use separate contexts for full isolation

### CasareRPA Current Implementation
`UnifiedResourceManager` supports:
- Multiple browser contexts per job (quota-controlled)
- Job-level resource isolation

### Recommendations
1. Add `ParallelBrowserNode` for running multiple browser operations concurrently
2. Consider exposing parallel page operations in `ForEachNode` browser variant
3. Document best practices for parallel browser workflows

---

## 7. CDP Direct Commands vs High-Level API

### When to Use High-Level API (Default)
- Auto-waiting built-in
- Retry logic included
- Cross-browser compatibility
- Actionability checks (visible, enabled, etc.)

### When to Consider CDP
- Performance profiling
- Network interception at lower level
- Features not exposed by Playwright API
- Maximum speed for specific operations (sacrifice reliability)

### CDP Example
```python
# Create CDP session (Chromium only)
cdp = await context.new_cdp_session(page)

# Direct DOM access
result = await cdp.send('DOM.getDocument')
```

### CasareRPA Recommendations
1. Stay with high-level API for all standard nodes
2. Consider CDP for future `PerformanceProfileNode`
3. Document CDP availability for advanced users

---

## 8. Headless vs Headed Performance

### Performance Comparison
| Mode | CPU Usage | Memory | Speed |
|------|-----------|--------|-------|
| Headless | Lower | Lower | 10-30% faster |
| Headed | Higher | Higher | Baseline |

### When Headless is Slower
- Screenshots with complex CSS
- Some animation-heavy sites
- WebGL content

### CasareRPA Current Implementation
`BrowserContextPool` and `BrowserPool` support `headless` parameter.

### Recommendations
1. Default to headless for production/CI
2. Use headed for debugging/development
3. Consider `new_headless` mode in Chromium (faster, more compatible)

---

## 9. Additional Performance Tips

### From Playwright Best Practices

1. **Avoid fixed waits** - Use Playwright's auto-wait
2. **Use API for authentication** - Skip UI login flows
3. **Clean up resources** - Close pages/contexts when done
4. **Use trace viewer sparingly** - Very performance-heavy
5. **Shard tests across machines** - For large test suites

### Browser Launch Arguments
```python
await browser.launch(
    args=[
        '--disable-gpu',                    # Faster in headless
        '--disable-dev-shm-usage',          # Avoid /dev/shm issues
        '--disable-extensions',             # No extension overhead
        '--disable-background-networking',  # Less network noise
    ]
)
```

---

## 10. CasareRPA-Specific Recommendations Summary

### Already Implemented (Good)
- Browser context pooling with LRU eviction
- Context reuse and cleanup
- Job-level resource quotas
- Idle timeout and max age tracking

### Quick Wins (Low Effort, High Impact)
1. Add resource blocking option to browser nodes
2. Default screenshots to JPEG 85% quality
3. Add browser launch args for headless optimization

### Medium-Term Improvements
1. Page-level pooling for tab-heavy workflows
2. Parallel browser operations node
3. Selector performance hints in UI

### Future Considerations
1. CDP integration for performance profiling
2. WebP screenshot support
3. Automatic selector optimization suggestions

---

## Sources

- [Playwright Browser Contexts Documentation](https://playwright.dev/docs/browser-contexts)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Playwright Locators](https://playwright.dev/docs/locators)
- [Block Resources in Playwright](https://scrapingant.com/blog/block-requests-playwright)
- [Block Specific Network Resources for Faster Playwright Scripts](https://medium.com/@mikestopcontinues/block-specific-network-resources-for-faster-playwright-scripts-1b4f6a5a9e28)
- [Playwright Screenshot Optimization](https://screenshotone.com/blog/how-to-render-screenshots-with-playwright/)
- [Speed Up Playwright Tests](https://blog.nashtechglobal.com/speed-up-playwright-tests/)
- [Playwright Test Best Practices for Scalability](https://dev.to/aswani25/playwright-test-best-practices-for-scalability-4l0j)
