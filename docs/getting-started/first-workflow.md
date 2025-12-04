# First Workflow

Create a simple web automation workflow.

## Goal

Open a browser, navigate to a website, and take a screenshot.

## Steps

### 1. Add Start Node

- Drag "Start" from the node library
- This is the workflow entry point

### 2. Add Launch Browser Node

- Drag "Launch Browser" from Browser category
- Connect Start → Launch Browser
- Configure: Browser Type = chromium, Headless = false

### 3. Add Navigate Node

- Drag "Navigate" from Browser category
- Connect Launch Browser → Navigate
- Configure: URL = https://example.com

### 4. Add Screenshot Node

- Drag "Screenshot" from Data category
- Connect Navigate → Screenshot
- Configure: Path = screenshot.png

### 5. Add End Node

- Drag "End" from Basic category
- Connect Screenshot → End

### 6. Run

- Press F5 or click Run button
- Watch the browser open and navigate

## Result

You should see:
- Browser opens
- Navigates to example.com
- Saves screenshot.png
- Browser closes

## Next Steps

- [Learn Core Concepts](concepts.md)
- [Browser Automation Guide](../guides/browser-automation.md)
