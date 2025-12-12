# Web Browser Automation Tutorial

Learn to automate web interactions: launch a browser, navigate to a website, extract data from a table, and save results to a CSV file.

**Time required:** 20 minutes

**What you will build:**
A workflow that scrapes product data from a website and exports it to a spreadsheet.

## Prerequisites

- CasareRPA installed and running
- Basic understanding of the Canvas interface
- Internet connection

## Goals

By the end of this tutorial, you will:
- Launch and configure a browser instance
- Navigate to web pages
- Wait for dynamic content to load
- Extract data from HTML tables
- Save extracted data to CSV format
- Close browser resources properly

---

## Step 1: Create a New Workflow

1. Open CasareRPA Canvas
2. Click **File** > **New Workflow** (or `Ctrl+N`)
3. Save immediately: **File** > **Save As** > `web_scraper_tutorial.json`

---

## Step 2: Add the Start Node

Every workflow begins with a Start node:

1. From the **Node Palette**, expand **Basic**
2. Drag **Start** onto the canvas at position (100, 300)

---

## Step 3: Launch Browser

Add a LaunchBrowserNode to open a web browser:

1. From **Node Palette** > **Browser**, drag **Launch Browser** onto the canvas
2. Position it at (400, 300)
3. Connect: Start `exec_out` -> Launch Browser `exec_in`

### Configure Launch Browser

Select the Launch Browser node and set these properties:

| Property | Value |
|----------|-------|
| url | `https://example.com/products` |
| browser_type | `chromium` |
| headless | `false` (unchecked) |
| window_state | `maximized` |
| do_not_close | `false` |

> **Note:** Set `headless: true` for production to run without a visible window.

### Visual Configuration

```
[Launch Browser]
    url: "https://example.com/products"
    browser_type: "chromium"
    headless: false
    window_state: "maximized"
```

---

## Step 4: Wait for Page Content

Web pages often load content dynamically. Add a wait node:

1. Drag **Wait For Element** from **Browser** category
2. Position at (700, 300)
3. Connect: Launch Browser `exec_out` -> Wait For Element `exec_in`

### Configure Wait For Element

| Property | Value |
|----------|-------|
| selector | `table.products` |
| state | `visible` |
| timeout | `30000` |

This ensures the products table is visible before we attempt to scrape it.

---

## Step 5: Extract Table Data

Now extract data from the HTML table:

1. Drag **Table Scraper** from **Browser** category
2. Position at (1000, 300)
3. Connect: Wait For Element `exec_out` -> Table Scraper `exec_in`

### Configure Table Scraper

| Property | Value |
|----------|-------|
| selector | `table.products` |
| has_header | `true` |
| include_links | `true` |
| timeout | `30000` |

### Output Ports

The Table Scraper outputs:
- `data` (LIST) - Table rows as list of dictionaries
- `headers` (LIST) - Column names
- `row_count` (INTEGER) - Number of rows extracted

---

## Step 6: Store Data in Variable

Save the extracted data to a workflow variable:

1. Drag **Set Variable** from **Variable** category
2. Position at (1300, 300)
3. Connect: Table Scraper `exec_out` -> Set Variable `exec_in`
4. Connect: Table Scraper `data` -> Set Variable `value`

### Configure Set Variable

| Property | Value |
|----------|-------|
| name | `products` |

---

## Step 7: Write Data to CSV

Export the extracted data to a CSV file:

1. Drag **Write CSV** from **File** category
2. Position at (1600, 300)
3. Connect: Set Variable `exec_out` -> Write CSV `exec_in`

### Configure Write CSV

| Property | Value |
|----------|-------|
| file_path | `C:\output\products.csv` |
| data | `{{products}}` |
| include_header | `true` |
| encoding | `utf-8` |

> **Tip:** Use `{{variables.products}}` or connect the data port for dynamic data.

---

## Step 8: Close Browser

Always clean up browser resources:

1. Drag **Close Browser** from **Browser** category
2. Position at (1900, 300)
3. Connect: Write CSV `exec_out` -> Close Browser `exec_in`

### Configure Close Browser

| Property | Value |
|----------|-------|
| timeout | `5000` |
| force_close | `false` |

---

## Step 9: Add End Node

Complete the workflow:

1. Drag **End** from **Basic** category
2. Position at (2200, 300)
3. Connect: Close Browser `exec_out` -> End `exec_in`

---

## Complete Workflow Diagram

```
[Start] --> [Launch Browser] --> [Wait For Element] --> [Table Scraper]
                                                              |
                                                              v
[End] <-- [Close Browser] <-- [Write CSV] <-- [Set Variable]
```

---

## Step 10: Run the Workflow

1. Click the **Run** button (or press `F5`)
2. Watch the browser open and navigate
3. Observe nodes highlighting as they execute
4. Check `C:\output\products.csv` for results

### Expected Log Output

```
[INFO] Workflow started
[INFO] Executing: Launch Browser
[INFO] Browser launched: chromium
[INFO] Navigating to: https://example.com/products
[INFO] Executing: Wait For Element
[INFO] Element found: table.products
[INFO] Executing: Table Scraper
[INFO] Extracted 25 rows from table
[INFO] Executing: Set Variable
[INFO] Variable 'products' set (25 items)
[INFO] Executing: Write CSV
[INFO] CSV written: C:\output\products.csv
[INFO] Executing: Close Browser
[INFO] Browser closed
[INFO] Workflow completed successfully
```

---

## Handling Pagination

To scrape multiple pages, add a loop:

### Enhanced Workflow

```
[Start]
    |
[Launch Browser]
    |
[Set Variable: page_num = 1]
    |
[While Loop Start]
    expression: "{{page_num}} <= {{total_pages}}"
        |
      body
        |
    [Go To URL]
        url: "https://example.com/products?page={{page_num}}"
        |
    [Wait For Element]
        |
    [Table Scraper]
        |
    [List Append]  # Append to accumulated data
        |
    [Math Operation]  # Increment page_num
        operation: "add"
        a: {{page_num}}
        b: 1
        |
    [Set Variable: page_num]
        |
    [While Loop End]
        |
    completed
        |
[Write CSV]
    |
[Close Browser]
    |
[End]
```

---

## Adding Error Handling

Wrap browser operations in Try/Catch for resilience:

```
[Start]
    |
[Try]
    |
  try_body
    |
[Launch Browser] --> [Wait For Element] --> [Table Scraper]
    |                        |
    |                    (on error)
    |                        |
    |                    [Catch]
    |                        |
    |                   catch_body
    |                        |
    |                   [Screenshot]
    |                        path: "C:\errors\{{timestamp}}.png"
    |                        |
    |                   [Log: "Error: {{error_message}}"]
    |                        |
    +------------+-----------+
                 |
             [Finally]
                 |
            finally_body
                 |
            [Close Browser]
                 |
             [End]
```

---

## Best Practices

### 1. Use Appropriate Wait Strategies

| Wait Condition | Use When |
|----------------|----------|
| `load` | Simple static pages |
| `domcontentloaded` | Page structure is ready |
| `networkidle` | SPAs with AJAX calls |

### 2. Selector Best Practices

```css
/* Prefer: IDs (unique) */
#products-table

/* Good: Data attributes */
[data-testid="product-list"]

/* Acceptable: Semantic classes */
table.products

/* Avoid: Positional selectors */
div > div:nth-child(3) > table
```

### 3. Handle Dynamic Content

Always add wait nodes before interacting with dynamic elements.

### 4. Close Resources

Always close browser in a Finally block to prevent resource leaks.

### 5. Use Variables for Selectors

Store selectors in variables for easier maintenance:

```
[Set Variable]
    name: "table_selector"
    value: "table.products"
```

---

## Troubleshooting

### Browser doesn't launch

**Cause:** Playwright browsers not installed
**Solution:** Run `python -m playwright install chromium`

### Element not found

**Cause:** Selector doesn't match or element not loaded
**Solution:**
- Verify selector in browser DevTools
- Increase timeout
- Add explicit wait before interaction

### Data extraction returns empty

**Cause:** Wrong selector or table structure
**Solution:**
- Use browser DevTools to inspect table
- Check if table uses `<thead>` and `<tbody>`
- Try different selector

### CSV file empty or malformed

**Cause:** Data format mismatch
**Solution:**
- Log the extracted data to verify structure
- Ensure data is a list of dictionaries

---

## Complete Node Configuration Reference

### LaunchBrowserNode

| Property | Type | Description |
|----------|------|-------------|
| url | STRING | Initial URL |
| browser_type | CHOICE | chromium/firefox/webkit |
| headless | BOOLEAN | Run without UI |
| window_state | CHOICE | normal/maximized/minimized |
| viewport_width | INTEGER | Browser width (px) |
| viewport_height | INTEGER | Browser height (px) |

### TableScraperNode

| Property | Type | Description |
|----------|------|-------------|
| selector | SELECTOR | Table element selector |
| has_header | BOOLEAN | First row is header |
| include_links | BOOLEAN | Extract href attributes |
| timeout | INTEGER | Wait timeout (ms) |

### WriteCSVNode

| Property | Type | Description |
|----------|------|-------------|
| file_path | FILE_PATH | Output file path |
| data | ANY | Data to write |
| include_header | BOOLEAN | Write header row |
| delimiter | STRING | Field delimiter |
| encoding | STRING | File encoding |

---

## Next Steps

- [Desktop Automation](desktop-automation.md) - Automate Windows applications
- [Data Processing](data-processing.md) - Transform extracted data
- [Error Handling](error-handling.md) - Build resilient workflows
- [Scheduled Workflows](scheduled-workflows.md) - Run scrapers on a schedule

---

## Summary

You learned how to:
1. Launch a browser with LaunchBrowserNode
2. Navigate and wait for content
3. Extract table data with TableScraperNode
4. Save results to CSV
5. Clean up resources properly
6. Handle errors gracefully

Browser automation is foundational for web scraping, form filling, and testing workflows.
