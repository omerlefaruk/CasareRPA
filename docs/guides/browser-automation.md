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

## Related Nodes

- [Browser Nodes](../nodes/browser/index.md)
- [Navigation Nodes](../nodes/navigation/index.md)
- [Data Nodes](../nodes/data/index.md)
