# CasareRPA Example Workflows

This directory contains example workflows demonstrating various automation scenarios.

## Available Workflows

### Web Scraping

| File | Description |
|------|-------------|
| `instagram_profile_scraper.json` | Scrape post metadata from an Instagram profile |
| `web_scraping_leads.json` | Login to CRM and scrape leads table |

### Data Processing

| File | Description |
|------|-------------|
| `data_reconciliation.json` | Compare and reconcile data from multiple sources |
| `invoice_processing.json` | Process and extract data from invoices |

## Workflow Schema

All workflows follow the schema version 1.0 format:

```json
{
  "metadata": {
    "name": "Workflow Name",
    "description": "What the workflow does",
    "version": "1.0.0",
    "tags": ["category", "type"],
    "schema_version": "1.0"
  },
  "nodes": { ... },
  "connections": [ ... ],
  "variables": { ... },
  "settings": {
    "stop_on_error": true,
    "timeout": 300,
    "retry_count": 0
  }
}
```

## Loading Workflows

1. Open CasareRPA Canvas
2. File > Open Workflow (Ctrl+O)
3. Select the `.json` workflow file
4. Configure any required variables
5. Run with F5 or the Play button

## Creating New Workflows

1. Design your workflow in the Canvas editor
2. File > Save Workflow (Ctrl+S)
3. Add descriptive metadata
4. Test thoroughly before production use

## Instagram Profile Scraper

### Purpose
Extract post metadata from a public Instagram profile including:
- Post URLs (via ExtractTextNode)
- Image URLs (via GetAttributeNode)
- Alt text/captions from image elements

### Workflow Structure
```
Start → LaunchBrowser → GoToURL → WaitForElement → Wait → ExtractText → GetAttribute → CloseBrowser → End
```

### Node Configuration
| Node | Key Setting |
|------|-------------|
| LaunchBrowserNode | `browser_type: chromium`, `do_not_close: true` |
| GoToURLNode | `url: https://www.instagram.com/omer.okumuss/`, `wait_until: networkidle` |
| WaitForElementNode | `selector: article a[href*='/p/']` |
| ExtractTextNode | `selector: article a[href*='/p/']`, `attribute: href` |
| GetAttributeNode | `selector: article img`, `attribute: src` |

### Requirements
- Chromium browser (auto-installed via Playwright)
- Network access to Instagram
- Login may be required for full content access

### Data Connections (Page Flow)
The workflow passes the browser `page` object between nodes:
- LaunchBrowser outputs `page` → GoToURL
- GoToURL outputs `page` → WaitForElement
- WaitForElement outputs `page` → ExtractText (via connection skipping WaitNode)
- ExtractText outputs `page` → GetAttribute

### Testing
Run validation tests:
```bash
pytest tests/test_instagram_workflow.py -v
```

### Usage Notes
1. Instagram may require login to view all posts
2. Selectors may change when Instagram updates their UI
3. Use responsibly and comply with Terms of Service
4. Add delays between requests to avoid rate limiting
