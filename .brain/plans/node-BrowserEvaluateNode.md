# Node Specification: BrowserEvaluateNode

## Overview
Execute JavaScript code in the browser page context using Playwright's `page.evaluate()`. Returns the result of the JavaScript expression.

**Category:** browser
**Base Class:** BrowserBaseNode
**File:** `src/casare_rpa/nodes/browser/evaluate_node.py`

## Use Cases
- Extract structured data from card-based layouts (not HTML tables)
- Get computed styles or element properties
- Execute custom DOM queries
- Scrape dynamic content loaded by JavaScript
- Perform complex multi-element extractions

## Ports

### Input Ports
| Port | DataType | Required | Description |
|------|----------|----------|-------------|
| `page` | PAGE | Yes | Browser page instance (from BrowserBaseNode) |
| `script` | STRING | No | JavaScript code override (from input port) |
| `arg` | ANY | No | Argument to pass to script (available as first param in JS) |

### Output Ports
| Port | DataType | Description |
|------|----------|-------------|
| `result` | ANY | The result returned by the JavaScript code |
| `success` | BOOLEAN | Whether execution succeeded |
| `error` | STRING | Error message if failed (empty on success) |

### Exec Ports
- `exec_in` - Execution input (from @node decorator)
- `exec_out` - Success execution path
- `exec_error` - Error execution path (optional)

## Properties

| Property | PropertyType | Default | Description |
|----------|--------------|---------|-------------|
| `script` | CODE | `""` | JavaScript code to execute in browser context |
| `timeout` | INTEGER | `30000` | Execution timeout in milliseconds |
| `wait_for_selector` | SELECTOR | `""` | Optional: Wait for this selector before executing |
| `return_json` | BOOLEAN | `true` | Attempt to parse result as JSON |
| `store_variable` | STRING | `""` | Variable name to store result in context |

## JavaScript Execution Pattern

The script receives the `arg` input as its first parameter:

```javascript
// Script property or input:
(arg) => {
    const cards = document.querySelectorAll(arg.selector);
    return Array.from(cards).map(card => ({
        name: card.querySelector(arg.nameSelector)?.innerText?.trim(),
        price: card.querySelector(arg.priceSelector)?.innerText?.trim()
    }));
}

// arg input value:
{
    "selector": "[class*='productCard']",
    "nameSelector": ".title",
    "priceSelector": ".price"
}
```

## Implementation Pattern

```python
@node(category="browser")
@properties(
    PropertyDef("script", PropertyType.CODE, default="", label="JavaScript Code", ...),
    PropertyDef("timeout", PropertyType.INTEGER, default=30000, ...),
    PropertyDef("wait_for_selector", PropertyType.SELECTOR, default="", ...),
    PropertyDef("return_json", PropertyType.BOOLEAN, default=True, ...),
    PropertyDef("store_variable", PropertyType.STRING, default="", ...),
    BROWSER_TIMEOUT,
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
)
class BrowserEvaluateNode(BrowserBaseNode):

    def _define_ports(self) -> None:
        self.add_page_input_port()
        self.add_input_port("script", DataType.STRING, required=False)
        self.add_input_port("arg", DataType.ANY, required=False)
        self.add_output_port("result", DataType.ANY)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        page = self.get_page(context)

        # Get script from input port or property
        script = self.get_input_value("script") or self.get_parameter("script", "")
        script = context.resolve_value(script)

        # Get argument
        arg = self.get_input_value("arg")

        # Optional wait for selector
        wait_selector = self.get_parameter("wait_for_selector", "")
        if wait_selector:
            await page.wait_for_selector(wait_selector, timeout=timeout)

        # Execute with retry
        result = await page.evaluate(script, arg)

        # Store in context if requested
        store_var = self.get_parameter("store_variable", "")
        if store_var:
            context.set_variable(store_var, result)

        return success_result(...)
```

## Similar Nodes Reference
- `TableScraperNode` - JS execution with page.evaluate()
- `GetAllImagesNode` - Embedded JS code pattern
- `ExtractTextNode` - Page access and error handling

## Agent Assignments
- **builder**: Create `src/casare_rpa/nodes/browser/evaluate_node.py`
- **ui**: Create `src/casare_rpa/presentation/canvas/visual_nodes/browser/evaluate_node.py`
- **quality**: Create `tests/nodes/browser/test_evaluate_node.py`

## Test Cases
1. `test_init` - Verify ports and properties defined correctly
2. `test_execute_simple_script` - Execute simple JS returning string
3. `test_execute_with_arg` - Execute JS with argument passed
4. `test_execute_complex_extraction` - Extract array of objects
5. `test_execute_timeout` - Verify timeout handling
6. `test_execute_script_error` - Handle JavaScript errors
7. `test_wait_for_selector` - Wait before execution
8. `test_store_variable` - Store result in context

## Registration
- Add to `nodes/registry_data.py`: `"BrowserEvaluateNode": "browser.evaluate_node"`
- Add to `nodes/browser/__init__.py`: Export BrowserEvaluateNode
- Add to `visual_nodes/browser/__init__.py`: Export VisualBrowserEvaluateNode
