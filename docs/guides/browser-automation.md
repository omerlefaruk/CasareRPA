# Browser Automation Guide

Automate web browsers using Playwright nodes.

## Overview

CasareRPA uses Playwright for browser automation, supporting:

- Chromium (Chrome, Edge)
- Firefox
- WebKit (Safari)

## Getting Started

### Launch Browser

Use the **LaunchBrowserNode** to start a browser:

| Property | Description | Default |
|----------|-------------|---------|
| browser_type | chromium, firefox, webkit | chromium |
| headless | Run without visible window | false |
| viewport_width | Browser width | 1280 |
| viewport_height | Browser height | 720 |

### Navigate

Use **GoToURLNode** to navigate:

| Property | Description |
|----------|-------------|
| url | Target URL |
| timeout | Max wait time (ms) |
| wait_until | load, domcontentloaded, networkidle |

### Interact

Common interaction nodes:

| Node | Purpose |
|------|---------|
| ClickElementNode | Click on element |
| TypeTextNode | Type text into input |
| SelectDropdownNode | Select dropdown option |

### Extract Data

| Node | Purpose |
|------|---------|
| ExtractTextNode | Get text content |
| GetAttributeNode | Get element attribute |
| ScreenshotNode | Capture screenshot |

## Best Practices

1. **Use specific selectors** - Prefer ID > class > xpath
2. **Add waits** - Use WaitForElementNode before interaction
3. **Handle errors** - Wrap in Try/Catch
4. **Close browser** - Always use CloseBrowserNode

## Example Workflow

```
Start → LaunchBrowser → Navigate → WaitForElement → Click → ExtractText → End
```

## Example: Instagram Profile Scraper

A complete workflow for scraping post metadata from an Instagram profile.

### Workflow File
Location: `workflows/instagram_profile_scraper.json`

### Flow Overview
```
Start
  │
  ▼
LaunchBrowserNode (chromium, maximized)
  │  └─page─┐
  ▼         │
GoToURLNode (https://www.instagram.com/username/)
  │  └─page─┐
  ▼         │
WaitForElementNode (selector: article a[href*='/p/'])
  │  └─page─┐
  ▼         │
WaitNode (3 seconds for images to load)
  │         │
  ▼         │
ExtractTextNode (get all post links) ◄─page─┘
  │  └─page─┐
  ▼         │
GetAttributeNode (get image src attributes) ◄─page─┘
  │
  ▼
CloseBrowserNode
  │
  ▼
End
```

### Key Configuration

| Node | Property | Value | Purpose |
|------|----------|-------|---------|
| LaunchBrowserNode | browser_type | chromium | Modern rendering |
| LaunchBrowserNode | do_not_close | true | Keep browser for debugging |
| GoToURLNode | wait_until | networkidle | Wait for all content |
| WaitForElementNode | selector | `article a[href*='/p/']` | Instagram post links |
| ExtractTextNode | selector | `article a[href*='/p/']` | Get all post link hrefs |
| GetAttributeNode | selector | `article img` | Get image src URLs |
| GetAttributeNode | attribute | `src` | Extract the src attribute |

### Extracted Data

The workflow outputs:
- **Post URLs**: Links to individual Instagram posts
- **Image URLs**: Direct links to post images
- **Alt Text**: Image descriptions/captions

### Important Notes

1. **Login Required**: Instagram limits content for logged-out users. Log in manually before running, or add login nodes.
2. **Rate Limiting**: Instagram may block automated access. Use reasonable delays.
3. **Selector Changes**: Instagram updates its HTML structure frequently. Selectors may need updates.
4. **Legal Compliance**: Ensure your use complies with Instagram's Terms of Service.

### Extending the Workflow

To save extracted data:
```
... → GetAttributeNode → WriteJSONFileNode (save to file) → CloseBrowserNode → ...
```

To scroll for more posts:
```
... → WaitNode → [For Loop: RunPythonScriptNode(scroll) + Wait] → ExtractTextNode → ...
```

### Testing the Workflow

The workflow can be validated using the headless runner:
```python
from tests.integration.runners.test_headless_ui import QtHeadlessRunner
from pathlib import Path

runner = QtHeadlessRunner()
workflow = runner.load_workflow(Path("workflows/instagram_profile_scraper.json"))
# Workflow loaded successfully - all node types and connections are valid
```

## Related Nodes

- [Browser Nodes](../nodes/browser/index.md)
- [Navigation Nodes](../nodes/navigation/index.md)
- [Data Nodes](../nodes/data/index.md)
