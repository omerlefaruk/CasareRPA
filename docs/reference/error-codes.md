# Error Codes Reference

CasareRPA uses standardized error codes for consistent error handling and troubleshooting. Each error code follows the format `ERR_CATEGORY_SPECIFIC` with numeric codes for programmatic handling.

---

## Error Code Format

```
ERR_<CATEGORY>_<SPECIFIC>
Numeric: <category_prefix><specific_number>
```

### Category Prefixes

| Category | Prefix | Numeric Range | Description |
|----------|--------|---------------|-------------|
| General | `ERR_` | 1000-1999 | General system errors |
| Browser | `ERR_BROWSER_` | 2000-2999 | Web automation errors |
| Desktop | `ERR_DESKTOP_` | 3000-3999 | Desktop automation errors |
| Data | `ERR_DATA_` | 4000-4999 | Data and validation errors |
| Config | `ERR_CONFIG_` | 5000-5999 | Configuration errors |
| Network | `ERR_NETWORK_` | 6000-6999 | Network and HTTP errors |
| Resource | `ERR_RESOURCE_` | 7000-7999 | Resource management errors |

---

## General Errors (1xxx)

### UNKNOWN_ERROR (1000)

**Description:** An unexpected error occurred that doesn't match known categories.

**Probable Causes:**
- Unhandled exception in node execution
- System-level error
- Bug in node implementation

**Troubleshooting:**
1. Check the full stack trace in logs
2. Review node inputs for unexpected data types
3. Verify system resources (memory, disk)
4. Report if reproducible

**Prevention:**
- Implement proper error handling in custom nodes
- Validate inputs before processing

---

### TIMEOUT (1001)

**Description:** Operation exceeded maximum allowed time.

**Probable Causes:**
- Network latency
- Slow application response
- Element not appearing in time
- Database query taking too long

**Troubleshooting:**
1. Increase timeout value in node configuration
2. Check network connectivity
3. Verify target application is responsive
4. Add explicit wait nodes before operations

**Prevention:**
- Set appropriate timeout values
- Use dynamic waits instead of fixed delays
- Implement retry logic for flaky operations

**Example:**
```python
# Increase timeout
config = {"timeout": 60000}  # 60 seconds
```

---

### CANCELLED (1002)

**Description:** Operation was cancelled by user or system.

**Probable Causes:**
- User clicked Stop button
- Workflow timeout exceeded
- System shutdown initiated
- Circuit breaker opened

**Troubleshooting:**
1. Check if cancellation was intentional
2. Review workflow timeout settings
3. Check circuit breaker status

---

### NOT_IMPLEMENTED (1003)

**Description:** Requested feature or operation is not implemented.

**Probable Causes:**
- Using unsupported node feature
- Platform-specific functionality not available
- Placeholder method called

**Troubleshooting:**
1. Check documentation for supported features
2. Use alternative approach
3. Request feature if needed

---

### INTERNAL_ERROR (1004)

**Description:** Internal system error occurred.

**Probable Causes:**
- Bug in CasareRPA core
- Corrupted state
- Memory corruption

**Troubleshooting:**
1. Restart the application
2. Clear cache and state
3. Report with full logs

---

### INVALID_INPUT (1005)

**Description:** Input data is invalid or malformed.

**Probable Causes:**
- Incorrect data type
- Missing required field
- Invalid format (URL, email, etc.)
- Out of range value

**Troubleshooting:**
1. Review input data types
2. Check required fields are populated
3. Validate format before passing to node

**Example:**
```python
# Validate URL format
if not url.startswith(("http://", "https://")):
    raise ValueError("Invalid URL format")
```

---

### PERMISSION_DENIED (1006)

**Description:** Operation was denied due to insufficient permissions.

**Probable Causes:**
- File system permissions
- API access denied
- Authentication required
- Resource locked by another process

**Troubleshooting:**
1. Check file/folder permissions
2. Verify API credentials
3. Run as administrator if needed
4. Release locked resources

---

## Browser/Web Errors (2xxx)

### BROWSER_NOT_FOUND (2000)

**Description:** Specified browser is not installed.

**Probable Causes:**
- Browser not installed
- Browser path incorrect
- Playwright browsers not installed

**Troubleshooting:**
```bash
# Install Playwright browsers
playwright install chromium
playwright install firefox
playwright install webkit
```

---

### BROWSER_LAUNCH_FAILED (2001)

**Description:** Failed to start browser instance.

**Probable Causes:**
- Browser crashed on startup
- Insufficient system resources
- Port conflict
- Corrupted browser profile

**Troubleshooting:**
1. Check available memory
2. Kill existing browser processes
3. Clear browser cache/profile
4. Try different browser type

---

### BROWSER_CLOSED (2002)

**Description:** Browser was closed unexpectedly.

**Probable Causes:**
- Browser crash
- Page closed externally
- Memory exhaustion
- Script error on page

**Troubleshooting:**
1. Check browser stability
2. Review page JavaScript errors
3. Monitor memory usage
4. Add browser health checks

---

### PAGE_NOT_FOUND (2003)

**Description:** Browser page reference is invalid.

**Probable Causes:**
- Page was closed
- Tab was closed
- Page handle became stale

**Troubleshooting:**
1. Verify page is still open
2. Re-acquire page reference
3. Check for page navigation

---

### PAGE_LOAD_FAILED (2004)

**Description:** Failed to load web page.

**Probable Causes:**
- Network error
- DNS resolution failure
- Page doesn't exist (404)
- SSL certificate error

**Troubleshooting:**
1. Check URL is correct
2. Verify network connectivity
3. Test URL in regular browser
4. Check for SSL certificate issues

---

### ELEMENT_NOT_FOUND (2005)

**Description:** Could not find element matching selector.

**Probable Causes:**
- Selector is incorrect
- Element doesn't exist
- Element not yet loaded
- Element in iframe

**Troubleshooting:**
1. Verify selector in browser DevTools
2. Add wait for element
3. Check if element is in iframe
4. Update selector if page changed

**Example:**
```python
# Wait for element before clicking
await page.wait_for_selector("#submit-btn", timeout=10000)
await page.click("#submit-btn")
```

---

### ELEMENT_NOT_VISIBLE (2006)

**Description:** Element exists but is not visible.

**Probable Causes:**
- Element hidden (`display: none`)
- Element off-screen
- Element covered by overlay
- Element has zero dimensions

**Troubleshooting:**
1. Wait for element to be visible
2. Scroll element into view
3. Close modals/overlays
4. Check element CSS

---

### ELEMENT_NOT_ENABLED (2007)

**Description:** Element is disabled.

**Probable Causes:**
- Form field is disabled
- Button in disabled state
- Element is readonly

**Troubleshooting:**
1. Wait for element to be enabled
2. Check form validation state
3. Trigger enabling conditions

---

### ELEMENT_STALE (2008)

**Description:** Element reference is no longer valid.

**Probable Causes:**
- Page navigated
- DOM was modified
- Element was removed and re-added

**Troubleshooting:**
1. Re-find element after navigation
2. Use dynamic selectors
3. Avoid storing element references long-term

---

### SELECTOR_INVALID (2009)

**Description:** Selector syntax is invalid.

**Probable Causes:**
- Malformed CSS selector
- Invalid XPath expression
- Special characters not escaped

**Troubleshooting:**
1. Validate selector syntax
2. Test selector in browser console
3. Escape special characters

**Example:**
```css
/* Invalid */
button[data-id=foo bar]

/* Valid */
button[data-id="foo bar"]
```

---

### NAVIGATION_FAILED (2010)

**Description:** Page navigation failed.

**Probable Causes:**
- Network timeout
- Server error (5xx)
- Redirect loop
- Page blocked

**Troubleshooting:**
1. Check URL accessibility
2. Increase navigation timeout
3. Handle redirects explicitly
4. Check for blocking (CORS, CSP)

---

### CLICK_FAILED (2011)

**Description:** Click action failed.

**Probable Causes:**
- Element moved during click
- Element covered by overlay
- Page scrolled
- Click intercepted

**Troubleshooting:**
1. Wait for element stability
2. Close overlays before clicking
3. Use force click if needed
4. Scroll to element

---

### TYPE_FAILED (2012)

**Description:** Text input failed.

**Probable Causes:**
- Element not editable
- Element not focused
- Input blocked
- Element detached

**Troubleshooting:**
1. Click element before typing
2. Clear existing content first
3. Check element is editable
4. Try fill() instead of type()

---

## Desktop Automation Errors (3xxx)

### WINDOW_NOT_FOUND (3000)

**Description:** Could not find specified window.

**Probable Causes:**
- Application not running
- Window title changed
- Window minimized to tray
- Incorrect window identifier

**Troubleshooting:**
1. Verify application is running
2. Check window title/class
3. Restore from system tray
4. Use partial title match

---

### APPLICATION_LAUNCH_FAILED (3001)

**Description:** Failed to start application.

**Probable Causes:**
- Application not installed
- Path incorrect
- Insufficient permissions
- Missing dependencies

**Troubleshooting:**
1. Verify installation path
2. Check file permissions
3. Install missing dependencies
4. Run as administrator

---

### APPLICATION_NOT_RESPONDING (3002)

**Description:** Application stopped responding.

**Probable Causes:**
- Application hang
- High CPU/memory usage
- Waiting for user input
- Deadlock

**Troubleshooting:**
1. Increase timeout
2. Check application logs
3. Close blocking dialogs
4. Restart application

---

### DESKTOP_ELEMENT_NOT_FOUND (3003)

**Description:** UI Automation element not found.

**Probable Causes:**
- Element not in UI tree
- Element not accessible
- Incorrect automation ID
- Element hidden

**Troubleshooting:**
1. Use Inspect.exe to verify element
2. Check accessibility properties
3. Update element locator
4. Wait for element to appear

---

## Data/Validation Errors (4xxx)

### VALIDATION_FAILED (4000)

**Description:** Data validation failed.

**Probable Causes:**
- Required field missing
- Invalid data format
- Constraint violation
- Schema mismatch

**Troubleshooting:**
1. Review validation error message
2. Check required fields
3. Validate data format
4. Update schema if needed

---

### PARSE_ERROR (4001)

**Description:** Failed to parse data.

**Probable Causes:**
- Invalid JSON/XML/CSV format
- Encoding issues
- Corrupted data
- Unexpected structure

**Troubleshooting:**
1. Validate input format
2. Check encoding (UTF-8)
3. Verify data structure
4. Handle malformed data

---

### TYPE_MISMATCH (4002)

**Description:** Data type doesn't match expected type.

**Probable Causes:**
- String passed where number expected
- Wrong data type from upstream node
- Automatic conversion failed

**Troubleshooting:**
1. Check upstream node output types
2. Add explicit type conversion
3. Validate data types

---

### EXPRESSION_ERROR (4008)

**Description:** Variable expression evaluation failed.

**Probable Causes:**
- Invalid expression syntax
- Referenced variable doesn't exist
- Type error in expression
- Circular reference

**Troubleshooting:**
1. Check expression syntax: `{{variable_name}}`
2. Verify variable is defined
3. Check for typos in variable name
4. Review expression dependencies

---

## Network Errors (6xxx)

### NETWORK_ERROR (6000)

**Description:** General network error.

**Probable Causes:**
- No network connectivity
- DNS failure
- Firewall blocking
- Proxy misconfiguration

**Troubleshooting:**
1. Check network connectivity
2. Verify DNS resolution
3. Check firewall rules
4. Configure proxy if needed

---

### CONNECTION_REFUSED (6001)

**Description:** Connection was refused by server.

**Probable Causes:**
- Server not running
- Wrong port
- Firewall blocking
- Service unavailable

**Troubleshooting:**
1. Verify server is running
2. Check port number
3. Review firewall rules
4. Test with curl/telnet

---

### CONNECTION_TIMEOUT (6002)

**Description:** Connection timed out.

**Probable Causes:**
- Network latency
- Server overloaded
- Packet loss
- Long-running operation

**Troubleshooting:**
1. Increase timeout
2. Check network latency
3. Verify server health
4. Use retry with backoff

---

### SSL_ERROR (6004)

**Description:** SSL/TLS error occurred.

**Probable Causes:**
- Invalid certificate
- Certificate expired
- Hostname mismatch
- TLS version incompatible

**Troubleshooting:**
1. Check certificate validity
2. Update CA certificates
3. Verify hostname
4. Try different TLS version

---

### HTTP_ERROR (6005)

**Description:** HTTP request returned error status.

**Probable Causes:**
- 4xx: Client error (bad request, auth failed)
- 5xx: Server error

**Troubleshooting:**
1. Check HTTP status code
2. Review request parameters
3. Check authentication
4. Review server logs

---

## Resource Errors (7xxx)

### RESOURCE_NOT_FOUND (7000)

**Description:** Required resource not found.

**Probable Causes:**
- File doesn't exist
- Database record missing
- API resource not found

**Troubleshooting:**
1. Verify resource exists
2. Check file path
3. Validate resource ID

---

### RESOURCE_LOCKED (7001)

**Description:** Resource is locked by another process.

**Probable Causes:**
- File open in another application
- Database row locked
- Resource in use

**Troubleshooting:**
1. Wait and retry
2. Close other applications
3. Use file locking options

---

### FILE_NOT_FOUND (7005)

**Description:** File does not exist.

**Probable Causes:**
- Incorrect path
- File deleted
- Permission denied
- Wrong drive

**Troubleshooting:**
1. Verify file path
2. Check file exists
3. Check path separators
4. Verify permissions

---

### FILE_ACCESS_DENIED (7006)

**Description:** Cannot access file due to permissions.

**Probable Causes:**
- Insufficient permissions
- File locked
- Protected directory
- Read-only file

**Troubleshooting:**
1. Check file permissions
2. Run as administrator
3. Close file in other apps
4. Remove read-only flag

---

## Using Error Codes

### In Node Implementation

```python
from casare_rpa.domain.value_objects.types import ErrorCode, NodeResult

async def execute(self, inputs, context):
    try:
        result = await some_operation()
        return NodeResult.ok(data=result)
    except TimeoutError:
        return NodeResult.fail(
            "Operation timed out",
            ErrorCode.TIMEOUT.name  # "TIMEOUT"
        )
    except FileNotFoundError as e:
        return NodeResult.fail(
            f"File not found: {e}",
            ErrorCode.FILE_NOT_FOUND.name
        )
```

### Error Code Properties

```python
from casare_rpa.domain.value_objects.types import ErrorCode

error = ErrorCode.ELEMENT_NOT_FOUND

# Get category
print(error.category)  # "Browser/Web"

# Check if retryable
if error.is_retryable:
    # Implement retry logic
    pass

# Get numeric value
print(error.value)  # 2005
```

### Mapping Exceptions to Codes

```python
# Automatic mapping
error_code = ErrorCode.from_exception(exception)
```

---

## Related Documentation

- [Troubleshooting Guide](../operations/troubleshooting.md) - Common issues
- [Error Handling Nodes](nodes/control-flow.md#error-handling) - Try-catch patterns
- [Retry Strategies](../user-guide/guides/error-handling.md) - Retry implementation
