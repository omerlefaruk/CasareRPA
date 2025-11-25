# CasareRPA Error Codes Reference

This document provides a comprehensive guide to errors you may encounter in CasareRPA, along with solutions and troubleshooting steps.

## Error Code Format

Errors in CasareRPA follow this pattern:
- **Error Type**: The Python exception class name
- **Severity**: DEBUG | INFO | WARNING | ERROR | CRITICAL
- **Recovery Strategy**: STOP | CONTINUE | RETRY | RESTART | FALLBACK | NOTIFY_AND_STOP

---

## Browser Automation Errors

### BROWSER_001: PlaywrightError - Browser Disconnected
**Error:** `Browser closed unexpectedly` or `Target closed`

**Causes:**
- Browser process crashed
- System ran out of memory
- Browser update in progress

**Solutions:**
1. Increase system memory allocation
2. Disable unnecessary browser extensions
3. Use headless mode for stability:
   ```
   LaunchBrowserNode: headless = true
   ```
4. Add error handling with TryCatchNode around browser operations

### BROWSER_002: TimeoutError - Element Not Found
**Error:** `Timeout 30000ms exceeded while waiting for selector`

**Causes:**
- Element doesn't exist on page
- Incorrect selector
- Page hasn't loaded yet
- Element is in an iframe

**Solutions:**
1. Verify selector using browser DevTools (F12 > Elements)
2. Add WaitForNavigationNode after page navigation
3. Increase timeout in node configuration
4. Use more robust selectors:
   ```
   // Instead of: .btn-primary
   // Use: button[data-testid="submit"] or text="Submit"
   ```
5. For iframe elements, switch to iframe first

### BROWSER_003: Error - Page Navigation Failed
**Error:** `net::ERR_NAME_NOT_RESOLVED` or `net::ERR_CONNECTION_REFUSED`

**Causes:**
- Invalid URL
- Network connectivity issue
- Target server is down

**Solutions:**
1. Verify URL is correct and accessible
2. Check network connectivity
3. Add retry logic with RetryNode
4. Handle offline scenarios with TryCatchNode

### BROWSER_004: Error - Element Not Interactable
**Error:** `Element is not visible` or `Element is not clickable at point`

**Causes:**
- Element is hidden (display: none)
- Element is covered by another element
- Page is still loading/animating

**Solutions:**
1. Add WaitForElementNode with `visible: true`
2. Scroll element into view first
3. Wait for animations to complete
4. Use JavaScript click as fallback:
   ```
   ExecuteJavaScriptNode: document.querySelector('selector').click()
   ```

### BROWSER_005: Error - SSL Certificate Error
**Error:** `SSL_ERROR_HANDSHAKE_FAILURE_ALERT`

**Causes:**
- Invalid SSL certificate
- Self-signed certificate
- Expired certificate

**Solutions:**
1. In LaunchBrowserNode, set `ignore_https_errors: true` (development only)
2. Install proper SSL certificates on the target server

---

## Desktop Automation Errors

### DESKTOP_001: ElementNotFoundError
**Error:** `Window element not found` or `Control not found`

**Causes:**
- Window not open
- Incorrect window title/class
- Element doesn't exist

**Solutions:**
1. Use WaitForWindowNode before interaction
2. Verify window title using Windows Spy tools
3. Check if application requires elevated permissions

### DESKTOP_002: AccessDenied
**Error:** `Access denied` when interacting with system UI

**Causes:**
- Application running with different privilege level
- UAC prompt blocking access
- Protected system window

**Solutions:**
1. Run CasareRPA as Administrator
2. Add UIAccess manifest to target application
3. Use SendKeys as alternative to direct control interaction

### DESKTOP_003: StaleElementError
**Error:** `Element reference is stale`

**Causes:**
- UI refreshed after element was found
- Window redrawn
- Application state changed

**Solutions:**
1. Re-find element immediately before interaction
2. Use retry logic
3. Add small delay after UI changes

---

## File Operation Errors

### FILE_001: FileNotFoundError
**Error:** `File not found: [path]`

**Causes:**
- File doesn't exist
- Incorrect path
- Network drive not connected

**Solutions:**
1. Use FileExistsNode to check before reading
2. Use absolute paths instead of relative
3. Verify network drives are connected

### FILE_002: PermissionError
**Error:** `Permission denied: [path]`

**Causes:**
- File is read-only
- File locked by another process
- Insufficient user permissions

**Solutions:**
1. Close applications that may have the file open
2. Check file permissions in Windows Explorer
3. Run as Administrator if needed
4. Use TryCatchNode with retry after delay

### FILE_003: OSError - Disk Full
**Error:** `No space left on device` or `Disk quota exceeded`

**Causes:**
- Disk is full
- User quota exceeded
- Temp files accumulated

**Solutions:**
1. Free up disk space
2. Use different output directory
3. Clean up temporary files

### FILE_004: UnicodeDecodeError
**Error:** `'utf-8' codec can't decode byte`

**Causes:**
- File has different encoding
- Binary file read as text

**Solutions:**
1. Specify correct encoding in ReadFileNode
2. Use binary read mode for non-text files
3. Check file format before reading

---

## Network Errors

### NET_001: ConnectionError
**Error:** `Connection refused` or `Failed to establish connection`

**Causes:**
- Server is down
- Incorrect host/port
- Firewall blocking connection

**Solutions:**
1. Verify server is running
2. Check firewall rules
3. Use retry logic with exponential backoff

### NET_002: TimeoutError
**Error:** `Request timed out`

**Causes:**
- Server is slow
- Network latency
- Large payload

**Solutions:**
1. Increase timeout in HTTPRequestNode
2. Use smaller request payloads
3. Check network connectivity

### NET_003: SSLError
**Error:** `SSL: CERTIFICATE_VERIFY_FAILED`

**Causes:**
- Invalid certificate
- Certificate chain issue
- Outdated CA certificates

**Solutions:**
1. Update system CA certificates
2. Set `verify_ssl: false` (development only)
3. Install required certificates

### NET_004: HTTPError - 4xx/5xx
**Error:** `HTTP 403 Forbidden` or `HTTP 500 Internal Server Error`

**Common Status Codes:**
| Code | Meaning | Solution |
|------|---------|----------|
| 400 | Bad Request | Check request format/parameters |
| 401 | Unauthorized | Verify API key/credentials |
| 403 | Forbidden | Check permissions/IP whitelist |
| 404 | Not Found | Verify URL path |
| 429 | Too Many Requests | Add delays between requests |
| 500 | Server Error | Retry later, contact server admin |
| 502 | Bad Gateway | Server-side issue, retry |
| 503 | Service Unavailable | Server overloaded, retry |

---

## Workflow Execution Errors

### EXEC_001: UnknownNodeType
**Error:** `Unknown node type: [NodeName]`

**Causes:**
- Node type not registered
- Workflow from newer version
- Corrupted workflow file

**Solutions:**
1. Update CasareRPA to latest version
2. Re-create the problematic node
3. Check workflow JSON for typos

### EXEC_002: CircularDependency
**Error:** `Circular dependency detected in workflow`

**Causes:**
- Nodes connected in a cycle
- Infinite loop in control flow

**Solutions:**
1. Review workflow connections
2. Use proper loop nodes (ForLoop, WhileLoop) instead
3. Add break conditions

### EXEC_003: InfiniteLoop
**Error:** `Execution exceeded maximum iterations`

**Causes:**
- WhileLoop condition never becomes false
- ForEach with continuously growing list
- Missing break condition

**Solutions:**
1. Add iteration limit to loops
2. Verify loop exit conditions
3. Add timeout to workflow execution

### EXEC_004: VariableNotFound
**Error:** `Variable 'name' not found in context`

**Causes:**
- Variable not set before use
- Typo in variable name
- Variable out of scope

**Solutions:**
1. Use SetVariableNode before GetVariableNode
2. Check variable name spelling
3. Use Variable Inspector to debug

### EXEC_005: TypeMismatch
**Error:** `Expected [type1], got [type2]`

**Causes:**
- Incorrect data type passed to node
- Missing type conversion

**Solutions:**
1. Use appropriate conversion node (ToString, ToNumber, etc.)
2. Check input port data type requirements

---

## System Errors

### SYS_001: MemoryError
**Error:** `Out of memory`

**Causes:**
- Large data operations
- Memory leak
- Too many browser tabs

**Solutions:**
1. Close unused browser tabs
2. Process data in smaller chunks
3. Restart workflow periodically
4. Increase system virtual memory

### SYS_002: CommandExecutionError
**Error:** `Command failed with exit code [N]`

**Common Exit Codes:**
| Code | Meaning |
|------|---------|
| 1 | General error |
| 2 | Misuse of command |
| 126 | Permission denied |
| 127 | Command not found |
| 128+N | Killed by signal N |

**Solutions:**
1. Verify command syntax
2. Check command exists in PATH
3. Run as Administrator if needed
4. Check command output for details

### SYS_003: PowerShellError
**Error:** `PowerShell script execution failed`

**Causes:**
- Execution policy restriction
- Script syntax error
- Missing module

**Solutions:**
1. Check PowerShell execution policy
2. Validate script syntax
3. Install required modules

---

## Credential & Security Errors

### SEC_001: VaultUnavailable
**Error:** `Cannot connect to HashiCorp Vault`

**Causes:**
- Vault server is down
- Network issue
- Invalid Vault address

**Solutions:**
1. Verify VAULT_ADDR in .env
2. Check Vault server status
3. Verify network connectivity

### SEC_002: InvalidCredentials
**Error:** `Invalid credentials` or `Authentication failed`

**Causes:**
- Wrong username/password
- Expired credentials
- Revoked API key

**Solutions:**
1. Update credentials in Vault
2. Regenerate API keys
3. Check credential expiration

### SEC_003: PermissionDenied
**Error:** `Permission denied for secret`

**Causes:**
- Insufficient Vault permissions
- Secret path doesn't exist

**Solutions:**
1. Check Vault policy permissions
2. Verify secret path exists
3. Contact administrator

---

## Recovery Strategies

CasareRPA supports configurable error recovery:

| Strategy | Behavior |
|----------|----------|
| STOP | Halt workflow execution immediately |
| CONTINUE | Skip failed node, proceed to next |
| RETRY | Retry the failed node (configurable count) |
| RESTART | Restart entire workflow from beginning |
| FALLBACK | Execute alternative workflow/node |
| NOTIFY_AND_STOP | Send notification then stop |

### Configuring Recovery

Use the GlobalErrorHandler to set strategies:

```python
from casare_rpa.utils.error_handler import get_global_error_handler, RecoveryStrategy

handler = get_global_error_handler()
handler.set_default_strategy(RecoveryStrategy.RETRY)
handler.set_strategy_for_error("TimeoutError", RecoveryStrategy.RETRY)
handler.set_strategy_for_error("ConnectionError", RecoveryStrategy.NOTIFY_AND_STOP)
```

---

## Debugging Tips

1. **Enable Debug Logging:**
   - Set log level to DEBUG in loguru configuration
   - Check logs at `%USERPROFILE%\.casare_rpa\logs\`

2. **Use Variable Inspector:**
   - View > Variable Inspector
   - Watch variable values during execution

3. **Step Through Execution:**
   - Press F10 to execute one node at a time
   - Set breakpoints on problematic nodes

4. **Check Execution History:**
   - View > Execution History
   - Review detailed timing and results

5. **Validate Selectors:**
   - Use browser DevTools (F12)
   - Test selectors in Console: `document.querySelector('selector')`

---

## Getting Help

If you can't resolve an error:

1. Check this document for common solutions
2. Search [GitHub Issues](https://github.com/yourusername/casare-rpa/issues)
3. Open a new issue with:
   - Full error message and stack trace
   - Workflow that caused the error (anonymized)
   - CasareRPA version
   - Python version
   - Windows version
   - Steps to reproduce
