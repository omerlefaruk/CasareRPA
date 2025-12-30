# Error Catalog - CasareRPA

Quick reference for error codes, exceptions, and resolution steps.

---

## Error Code Format

```
{LAYER}_{CATEGORY}_{NUMBER}

Layers: DOM (Domain), APP (Application), INF (Infrastructure), PRE (Presentation), NOD (Node)
Categories: VAL (Validation), EXE (Execution), CON (Connection), SER (Serialization), etc.
```

---

## Domain Errors (DOM_*)

### Validation Errors (DOM_VAL_*)

| Code | Exception | Message | Cause | Fix |
|------|-----------|---------|-------|-----|
| `DOM_VAL_001` | `ValidationError` | "Required field missing: {field}" | Missing required property | Provide the required field |
| `DOM_VAL_002` | `InvalidPortTypeError` | "Port type mismatch: {expected} vs {actual}" | Wrong data type connection | Connect compatible port types |
| `DOM_VAL_003` | `DuplicateNodeError` | "Node with ID {id} already exists" | Duplicate node ID | Use unique node IDs |
| `DOM_VAL_004` | `CircularDependencyError` | "Circular dependency detected" | Workflow has cycle | Remove circular connections |
| `DOM_VAL_005` | `InvalidWorkflowError` | "Workflow validation failed: {reasons}" | Multiple validation issues | Check validation details |

### Entity Errors (DOM_ENT_*)

| Code | Exception | Message | Cause | Fix |
|------|-----------|---------|-------|-----|
| `DOM_ENT_001` | `EntityNotFoundError` | "Entity not found: {type}/{id}" | Entity doesn't exist | Check entity ID |
| `DOM_ENT_002` | `InvalidStateError` | "Invalid state transition: {from} → {to}" | Illegal state change | Follow valid state transitions |
| `DOM_ENT_003` | `ConcurrencyError` | "Entity modified by another process" | Concurrent modification | Retry with fresh data |

---

## Node Errors (NOD_*)

### Execution Errors (NOD_EXE_*)

| Code | Exception | Message | Cause | Fix |
|------|-----------|---------|-------|-----|
| `NOD_EXE_001` | `NodeExecutionError` | "Node execution failed: {reason}" | Generic execution failure | Check node logs |
| `NOD_EXE_002` | `TimeoutError` | "Node timed out after {ms}ms" | Operation exceeded timeout | Increase timeout or optimize |
| `NOD_EXE_003` | `InputNotConnectedError` | "Required input '{port}' not connected" | Missing input connection | Connect required input |
| `NOD_EXE_004` | `OutputNotSetError` | "Output '{port}' was not set" | Node didn't set output | Check node implementation |
| `NOD_EXE_005` | `ContextMissingError` | "Required context key '{key}' missing" | Missing execution context | Ensure context is populated |

### Browser Node Errors (NOD_BRW_*)

| Code | Exception | Message | Cause | Fix |
|------|-----------|---------|-------|-----|
| `NOD_BRW_001` | `SelectorNotFoundError` | "Element not found: {selector}" | Element doesn't exist | Verify selector, add wait |
| `NOD_BRW_002` | `PageNotAvailableError` | "No page in execution context" | Browser not launched | Add LaunchBrowser node first |
| `NOD_BRW_003` | `NavigationError` | "Navigation failed: {url}" | Page load failed | Check URL, network |
| `NOD_BRW_004` | `ElementNotInteractableError` | "Element not interactable" | Element hidden/disabled | Wait for element state |
| `NOD_BRW_005` | `MultipleElementsError` | "Selector matched {count} elements" | Ambiguous selector | Use more specific selector |

### Desktop Node Errors (NOD_DSK_*)

| Code | Exception | Message | Cause | Fix |
|------|-----------|---------|-------|-----|
| `NOD_DSK_001` | `WindowNotFoundError` | "Window not found: {title}" | Window doesn't exist | Check window title, timing |
| `NOD_DSK_002` | `ControlNotFoundError` | "Control not found: {identifier}" | UI element missing | Verify control properties |
| `NOD_DSK_003` | `AccessDeniedError` | "Access denied to control" | Permission issue | Run as admin if needed |
| `NOD_DSK_004` | `PatternNotSupportedError` | "Pattern '{pattern}' not supported" | Control doesn't support action | Use different interaction |

### Data Node Errors (NOD_DAT_*)

| Code | Exception | Message | Cause | Fix |
|------|-----------|---------|-------|-----|
| `NOD_DAT_001` | `JSONParseError` | "Invalid JSON: {detail}" | Malformed JSON | Fix JSON syntax |
| `NOD_DAT_002` | `TypeConversionError` | "Cannot convert {from_type} to {to_type}" | Incompatible types | Use correct data type |
| `NOD_DAT_003` | `DataTransformError` | "Transform failed: {reason}" | Transform logic error | Check transform expression |

---

## Infrastructure Errors (INF_*)

### HTTP Errors (INF_HTTP_*)

| Code | Exception | Message | Cause | Fix |
|------|-----------|---------|-------|-----|
| `INF_HTTP_001` | `ConnectionError` | "Connection failed: {host}" | Network unreachable | Check network, host |
| `INF_HTTP_002` | `SSRFBlockedError` | "SSRF blocked: {url}" | Private IP access attempt | Use public URLs only |
| `INF_HTTP_003` | `RateLimitError` | "Rate limit exceeded" | Too many requests | Wait and retry |
| `INF_HTTP_004` | `CircuitOpenError` | "Circuit breaker open for {host}" | Repeated failures | Wait for circuit reset |
| `INF_HTTP_005` | `AuthenticationError` | "Authentication failed" | Invalid credentials | Check API key/token |

### Persistence Errors (INF_PER_*)

| Code | Exception | Message | Cause | Fix |
|------|-----------|---------|-------|-----|
| `INF_PER_001` | `FileNotFoundError` | "File not found: {path}" | File doesn't exist | Check file path |
| `INF_PER_002` | `FilePermissionError` | "Permission denied: {path}" | No read/write access | Check file permissions |
| `INF_PER_003` | `SerializationError` | "Failed to serialize: {reason}" | Object not serializable | Check data types |
| `INF_PER_004` | `DeserializationError` | "Failed to deserialize: {reason}" | Corrupted/invalid data | Check file format |

### Credential Errors (INF_CRD_*)

| Code | Exception | Message | Cause | Fix |
|------|-----------|---------|-------|-----|
| `INF_CRD_001` | `CredentialNotFoundError` | "Credential not found: {name}" | Credential doesn't exist | Create credential first |
| `INF_CRD_002` | `CredentialDecryptError` | "Failed to decrypt credential" | Wrong master key | Check encryption key |
| `INF_CRD_003` | `CredentialExpiredError` | "Credential expired: {name}" | Token/key expired | Refresh credential |

---

## Presentation Errors (PRE_*)

### Canvas Errors (PRE_CAN_*)

| Code | Exception | Message | Cause | Fix |
|------|-----------|---------|-------|-----|
| `PRE_CAN_001` | `NodeCreationError` | "Failed to create visual node" | Invalid node type | Check node registration |
| `PRE_CAN_002` | `ConnectionError` | "Cannot connect ports" | Incompatible ports | Check port types |
| `PRE_CAN_003` | `SerializationError` | "Failed to save workflow" | Data corruption | Check workflow state |
| `PRE_CAN_004` | `LoadError` | "Failed to load workflow: {file}" | Invalid file format | Check file integrity |

### UI Errors (PRE_UI_*)

| Code | Exception | Message | Cause | Fix |
|------|-----------|---------|-------|-----|
| `PRE_UI_001` | `ThreadError` | "UI update from non-main thread" | Wrong thread | Use signal/slot |
| `PRE_UI_002` | `WidgetError` | "Widget already deleted" | Stale reference | Check object lifecycle |
| `PRE_UI_003` | `SignalError` | "Signal connection failed" | Invalid slot | Check @Slot decorator |

---

## Application Errors (APP_*)

### Orchestration Errors (APP_ORC_*)

| Code | Exception | Message | Cause | Fix |
|------|-----------|---------|-------|-----|
| `APP_ORC_001` | `WorkflowNotFoundError` | "Workflow not found: {id}" | Invalid workflow ID | Check workflow exists |
| `APP_ORC_002` | `ExecutionInProgressError` | "Execution already in progress" | Duplicate execution | Wait for current to finish |
| `APP_ORC_003` | `ExecutionCancelledError` | "Execution was cancelled" | User cancellation | N/A - expected behavior |

---

## Error Handling Patterns

### In Node Execute

```python
async def execute(self, context):
    try:
        result = await self._do_work()
        return {"success": True, "data": result}
    except SelectorNotFoundError as e:
        return {
            "success": False,
            "error": str(e),
            "error_code": "NOD_BRW_001",
            "is_retryable": True,
        }
    except Exception as e:
        logger.exception(f"Node execution failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_code": "NOD_EXE_001",
            "is_retryable": False,
        }
```

### In Infrastructure

```python
async def fetch_data(self, url: str):
    try:
        async with UnifiedHttpClient() as client:
            return await client.get(url)
    except ConnectionError:
        raise InfrastructureError("INF_HTTP_001", f"Connection failed: {url}")
    except SSRFBlockedError:
        raise SecurityError("INF_HTTP_002", f"SSRF blocked: {url}")
```

### In Presentation

```python
@Slot()
def on_action_triggered(self):
    try:
        self._do_action()
    except Exception as e:
        logger.error(f"Action failed: {e}")
        self._show_error_dialog(str(e))
```

---

## Logging Convention

```python
from loguru import logger

# ERROR - Unrecoverable, needs attention
logger.error(f"[NOD_EXE_001] Node failed: {node_id}")

# WARNING - Recoverable, but notable
logger.warning(f"[NOD_BRW_001] Selector retry: {selector}")

# INFO - Normal operation
logger.info(f"Node completed: {node_id}")

# DEBUG - Development/troubleshooting
logger.debug(f"Input value: {value}")
```

---

## Quick Lookup by Symptom

| Symptom | Likely Error | First Check |
|---------|--------------|-------------|
| "Element not found" | `NOD_BRW_001` | Selector valid? Page loaded? |
| "Connection refused" | `INF_HTTP_001` | Host reachable? Port open? |
| "Timeout" | `NOD_EXE_002` | Increase timeout, check network |
| "Permission denied" | `INF_PER_002` | File/folder permissions |
| "Invalid JSON" | `NOD_DAT_001` | Validate JSON syntax |
| "Credential not found" | `INF_CRD_001` | Create credential in settings |
| "SSRF blocked" | `INF_HTTP_002` | Can't access private IPs |

---

*Last updated: 2025-12-14*
