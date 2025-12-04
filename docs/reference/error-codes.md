# Error Codes

Error codes and their meanings.

## Node Execution Errors

| Code | Name | Description |
|------|------|-------------|
| E001 | TIMEOUT | Operation timed out |
| E002 | ELEMENT_NOT_FOUND | Element not found |
| E003 | CONNECTION_FAILED | Connection failed |
| E004 | INVALID_INPUT | Invalid input value |
| E005 | AUTHENTICATION_FAILED | Auth failed |

## Browser Errors

| Code | Name | Description |
|------|------|-------------|
| B001 | BROWSER_LAUNCH_FAILED | Could not start browser |
| B002 | NAVIGATION_FAILED | Navigation error |
| B003 | SELECTOR_TIMEOUT | Element wait timeout |
| B004 | CLICK_FAILED | Click operation failed |
| B005 | TYPE_FAILED | Type operation failed |

## Desktop Errors

| Code | Name | Description |
|------|------|-------------|
| D001 | APP_LAUNCH_FAILED | Could not start application |
| D002 | WINDOW_NOT_FOUND | Window not found |
| D003 | ELEMENT_NOT_FOUND | UI element not found |
| D004 | INTERACTION_FAILED | Interaction failed |

## File Errors

| Code | Name | Description |
|------|------|-------------|
| F001 | FILE_NOT_FOUND | File does not exist |
| F002 | PERMISSION_DENIED | Access denied |
| F003 | DISK_FULL | No space left |
| F004 | INVALID_FORMAT | Invalid file format |

## Network Errors

| Code | Name | Description |
|------|------|-------------|
| N001 | CONNECTION_REFUSED | Server refused connection |
| N002 | DNS_FAILED | DNS lookup failed |
| N003 | SSL_ERROR | SSL/TLS error |
| N004 | REQUEST_TIMEOUT | Request timed out |

## Handling Errors

Use Try/Catch nodes to handle errors gracefully:

```
Try → [operation] → Catch (error code) → [recovery]
```

See [Error Handling Guide](../guides/error-handling.md)
