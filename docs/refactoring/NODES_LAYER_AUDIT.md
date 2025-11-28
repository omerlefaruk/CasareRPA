# Nodes Layer Refactoring Analysis

**Date:** 2025-11-28
**Status:** Analysis Complete
**Priority:** CRITICAL

---

## Executive Summary

Analyzed `src/casare_rpa/nodes/` directory.

**Findings:**
- **1 CRITICAL issue** (39 broken registry entries)
- **3 HIGH priority** issues (API inconsistency, massive duplication)
- **0 deprecated files** ✅
- **Multiple duplication patterns** across 20+ files

---

## CRITICAL Issue

### Broken Node Registry (39 entries)

**File:** `src/casare_rpa/nodes/__init__.py`

**Problem:** 39 registry entries point to non-existent modules, causing `ModuleNotFoundError` when loading these node types.

#### Broken Entries by Category:

**1. File Nodes (18 broken entries)**

**Wrong module:** `file_nodes`
**Actual paths:** `file.file_operations` or `file.structured_data`

```python
# BROKEN ENTRIES:
NodeRegistry.register("ReadTextFileNode", "file_nodes", "File Operations")
NodeRegistry.register("WriteTextFileNode", "file_nodes", "File Operations")
NodeRegistry.register("AppendToFileNode", "file_nodes", "File Operations")
NodeRegistry.register("ReadCSVNode", "file_nodes", "File Operations")
NodeRegistry.register("WriteCSVNode", "file_nodes", "File Operations")
NodeRegistry.register("ReadJSONNode", "file_nodes", "File Operations")
NodeRegistry.register("WriteJSONNode", "file_nodes", "File Operations")
NodeRegistry.register("ReadExcelNode", "file_nodes", "File Operations")
NodeRegistry.register("WriteExcelNode", "file_nodes", "File Operations")
NodeRegistry.register("CopyFileNode", "file_nodes", "File Management")
NodeRegistry.register("MoveFileNode", "file_nodes", "File Management")
NodeRegistry.register("DeleteFileNode", "file_nodes", "File Management")
NodeRegistry.register("CreateFolderNode", "file_nodes", "File Management")
NodeRegistry.register("ListFilesNode", "file_nodes", "File Management")
NodeRegistry.register("FileExistsNode", "file_nodes", "File Management")
NodeRegistry.register("GetFileInfoNode", "file_nodes", "File Management")
NodeRegistry.register("RenameFileNode", "file_nodes", "File Management")
NodeRegistry.register("GetFileSizeNode", "file_nodes", "File Management")
```

**FIX:**
```python
# File Operations → file.structured_data
NodeRegistry.register("ReadTextFileNode", "file.file_operations", "File Operations")
NodeRegistry.register("WriteTextFileNode", "file.file_operations", "File Operations")
NodeRegistry.register("ReadCSVNode", "file.structured_data", "File Operations")
NodeRegistry.register("WriteCSVNode", "file.structured_data", "File Operations")
NodeRegistry.register("ReadJSONNode", "file.structured_data", "File Operations")
NodeRegistry.register("WriteJSONNode", "file.structured_data", "File Operations")
NodeRegistry.register("ReadExcelNode", "file.structured_data", "File Operations")
NodeRegistry.register("WriteExcelNode", "file.structured_data", "File Operations")

# File Management → file.file_operations
NodeRegistry.register("CopyFileNode", "file.file_operations", "File Management")
NodeRegistry.register("MoveFileNode", "file.file_operations", "File Management")
NodeRegistry.register("DeleteFileNode", "file.file_operations", "File Management")
NodeRegistry.register("CreateFolderNode", "file.file_operations", "File Management")
NodeRegistry.register("ListFilesNode", "file.file_operations", "File Management")
NodeRegistry.register("FileExistsNode", "file.file_operations", "File Management")
NodeRegistry.register("GetFileInfoNode", "file.file_operations", "File Management")
NodeRegistry.register("RenameFileNode", "file.file_operations", "File Management")
NodeRegistry.register("GetFileSizeNode", "file.file_operations", "File Management")
```

**2. HTTP Nodes (11 broken entries)**

**Wrong module:** `http_nodes`
**Actual paths:** `http.http_basic` or `http.http_advanced`

```python
# BROKEN ENTRIES:
NodeRegistry.register("HTTPRequestNode", "http_nodes", "HTTP")
NodeRegistry.register("HTTPGetNode", "http_nodes", "HTTP")
NodeRegistry.register("HTTPPostNode", "http_nodes", "HTTP")
NodeRegistry.register("HTTPPutNode", "http_nodes", "HTTP")
NodeRegistry.register("HTTPDeleteNode", "http_nodes", "HTTP")
NodeRegistry.register("HTTPHeadersNode", "http_nodes", "HTTP")
NodeRegistry.register("ParseJSONResponseNode", "http_nodes", "HTTP")
NodeRegistry.register("DownloadFileNode", "http_nodes", "HTTP")
NodeRegistry.register("OAuth2Node", "http_nodes", "HTTP Auth")
NodeRegistry.register("BasicAuthNode", "http_nodes", "HTTP Auth")
NodeRegistry.register("APIKeyAuthNode", "http_nodes", "HTTP Auth")
```

**FIX:**
```python
# Basic HTTP → http.http_basic
NodeRegistry.register("HTTPRequestNode", "http.http_basic", "HTTP")
NodeRegistry.register("HTTPGetNode", "http.http_basic", "HTTP")
NodeRegistry.register("HTTPPostNode", "http.http_basic", "HTTP")
NodeRegistry.register("HTTPPutNode", "http.http_basic", "HTTP")
NodeRegistry.register("HTTPDeleteNode", "http.http_basic", "HTTP")

# Advanced HTTP → http.http_advanced
NodeRegistry.register("HTTPHeadersNode", "http.http_advanced", "HTTP")
NodeRegistry.register("ParseJSONResponseNode", "http.http_advanced", "HTTP")
NodeRegistry.register("DownloadFileNode", "http.http_advanced", "HTTP")

# Auth → http.http_auth
NodeRegistry.register("OAuth2Node", "http.http_auth", "HTTP Auth")
NodeRegistry.register("BasicAuthNode", "http.http_auth", "HTTP Auth")
NodeRegistry.register("APIKeyAuthNode", "http.http_auth", "HTTP Auth")
```

**3. Database Nodes (10 broken entries)**

**Wrong module:** `database_nodes`
**Actual path:** `database.sql_nodes`

```python
# BROKEN ENTRIES:
NodeRegistry.register("SQLQueryNode", "database_nodes", "Database")
NodeRegistry.register("SQLExecuteNode", "database_nodes", "Database")
NodeRegistry.register("SQLConnectionNode", "database_nodes", "Database")
NodeRegistry.register("SQLTransactionNode", "database_nodes", "Database")
NodeRegistry.register("SQLBulkInsertNode", "database_nodes", "Database")
NodeRegistry.register("SQLiteNode", "database_nodes", "Database")
NodeRegistry.register("PostgreSQLNode", "database_nodes", "Database")
NodeRegistry.register("MySQLNode", "database_nodes", "Database")
NodeRegistry.register("SQLServerNode", "database_nodes", "Database")
NodeRegistry.register("OracleNode", "database_nodes", "Database")
```

**FIX:**
```python
NodeRegistry.register("SQLQueryNode", "database.sql_nodes", "Database")
NodeRegistry.register("SQLExecuteNode", "database.sql_nodes", "Database")
NodeRegistry.register("SQLConnectionNode", "database.sql_nodes", "Database")
NodeRegistry.register("SQLTransactionNode", "database.sql_nodes", "Database")
NodeRegistry.register("SQLBulkInsertNode", "database.sql_nodes", "Database")
NodeRegistry.register("SQLiteNode", "database.sql_nodes", "Database")
NodeRegistry.register("PostgreSQLNode", "database.sql_nodes", "Database")
NodeRegistry.register("MySQLNode", "database.sql_nodes", "Database")
NodeRegistry.register("SQLServerNode", "database.sql_nodes", "Database")
NodeRegistry.register("OracleNode", "database.sql_nodes", "Database")
```

**Impact:** CRITICAL - Nodes fail to load
**Priority:** Fix immediately after broken imports

---

## HIGH PRIORITY Issues

### 1. Duplicated `safe_int()` Function (20+ files)

**Files with duplication:**
- `browser_nodes.py`
- `interaction_nodes.py`
- `data_nodes.py`
- `email_nodes.py`
- `wait_nodes.py`
- `database/sql_nodes.py`
- 15+ more files

**Current (duplicated in each file):**
```python
def safe_int(value, default=0):
    """Safely convert value to integer."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
```

**Fix:** Create utility module

**File:** `src/casare_rpa/nodes/utils/type_converters.py`
```python
"""Type conversion utilities for node implementations."""

def safe_int(value, default: int = 0) -> int:
    """Safely convert value to integer."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value, default: float = 0.0) -> float:
    """Safely convert value to float."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_str(value, default: str = "") -> str:
    """Safely convert value to string."""
    try:
        return str(value)
    except (ValueError, TypeError):
        return default
```

**Update all files:**
```python
from casare_rpa.nodes.utils.type_converters import safe_int, safe_float, safe_str
```

**Impact:** Remove ~100+ lines of duplication
**Priority:** HIGH

---

### 2. Retry Logic Duplication (15+ nodes)

**Files affected:**
- `browser_nodes.py` (5 nodes)
- `interaction_nodes.py` (4 nodes)
- `http/http_basic.py` (3 nodes)
- `database/sql_nodes.py` (3 nodes)

**Current (30-line pattern in each node):**
```python
max_retries = self.get_input_value("retries", context) or 3
retry_delay = self.get_input_value("retry_delay", context) or 1.0

for attempt in range(max_retries):
    try:
        # Node execution logic
        result = do_something()
        break
    except Exception as e:
        if attempt < max_retries - 1:
            await asyncio.sleep(retry_delay)
            continue
        else:
            raise
```

**Fix:** Create retry decorator

**File:** `src/casare_rpa/nodes/utils/retry_decorator.py`
```python
"""Retry decorator for node operations."""
import asyncio
from functools import wraps
from typing import Callable, TypeVar, Any

T = TypeVar('T')

def with_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0
):
    """Decorator to retry async operations.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay on each retry
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise last_exception

        return wrapper
    return decorator
```

**Usage:**
```python
from casare_rpa.nodes.utils.retry_decorator import with_retry

class SomeNode(BaseNode):
    @with_retry(max_attempts=3, delay=1.0)
    async def _perform_operation(self, context):
        """Operation with automatic retry."""
        return await do_something()
```

**Impact:** Remove ~450+ lines of duplication
**Priority:** HIGH

---

### 3. Screenshot-on-Fail Duplication (10+ nodes)

**Files affected:**
- `browser_nodes.py` (4 nodes)
- `interaction_nodes.py` (3 nodes)
- `desktop_nodes/interaction_nodes.py` (3 nodes)

**Current (20-line pattern):**
```python
try:
    # Node logic
    pass
except Exception as e:
    if context.get("screenshot_on_error"):
        try:
            screenshot_path = f"error_{node_id}_{timestamp}.png"
            await page.screenshot(path=screenshot_path)
            logger.error(f"Error screenshot saved: {screenshot_path}")
        except:
            pass
    raise
```

**Fix:** Create mixin or decorator

**File:** `src/casare_rpa/nodes/utils/error_capture.py`
```python
"""Error capture utilities for nodes."""
from functools import wraps
from pathlib import Path
from datetime import datetime

def capture_screenshot_on_error(screenshot_dir: str = "error_screenshots"):
    """Decorator to capture screenshot when node fails."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, context, *args, **kwargs):
            try:
                return await func(self, context, *args, **kwargs)
            except Exception as e:
                if context.get("screenshot_on_error"):
                    await self._capture_error_screenshot(context, screenshot_dir)
                raise
        return wrapper
    return decorator
```

**Impact:** Remove ~200+ lines of duplication
**Priority:** HIGH

---

### 4. Port API Inconsistency

**Files with WRONG API:**
- `string_nodes.py`
- `list_nodes.py`
- `dict_nodes.py`

**Current (WRONG):**
```python
self.add_input_port("text", DataType.STRING)
self.add_output_port("result", DataType.STRING)
```

**Expected:**
```python
self.add_input_port("text", PortType.INPUT, DataType.STRING)
self.add_output_port("result", PortType.OUTPUT, DataType.STRING)
```

**Fix:** Update all port definitions in these 3 files

**Impact:** API consistency
**Priority:** HIGH

---

## MEDIUM PRIORITY Issues

### Long Execute Methods (100-200+ lines)

**Files:**
1. `browser_nodes.py`:
   - `LaunchBrowserNode.execute()` - 156 lines
   - `DownloadFileNode.execute()` - 124 lines

2. `interaction_nodes.py`:
   - `ClickElementNode.execute()` - 132 lines
   - `TypeTextNode.execute()` - 118 lines

3. `data_nodes.py`:
   - `ScreenshotNode.execute()` - 145 lines

**Fix:** Extract helper methods, use composition

**Priority:** MEDIUM

---

## Deprecated Files

**✅ None found**

Grep searches for deprecation markers and legacy imports returned empty.

---

## Files Needing Attention

| Priority | File | Issue |
|----------|------|-------|
| CRITICAL | `nodes/__init__.py` | 39 broken registry paths |
| HIGH | `string_nodes.py` | Port API inconsistency |
| HIGH | `list_nodes.py` | Port API inconsistency |
| HIGH | `dict_nodes.py` | Port API inconsistency |
| HIGH | 20+ files | `safe_int()` duplication |
| HIGH | 15+ files | Retry logic duplication |
| HIGH | 10+ files | Screenshot duplication |
| MEDIUM | `browser_nodes.py` | Long methods |
| MEDIUM | `interaction_nodes.py` | Long methods |

---

## Recommended Refactoring Order

1. **Fix CRITICAL registry entries** (39 fixes) - IMMEDIATE
2. Fix Port API inconsistency (3 files)
3. Create `nodes/utils/` directory with:
   - `type_converters.py` (safe_int, safe_float, safe_str)
   - `retry_decorator.py` (@with_retry)
   - `error_capture.py` (@capture_screenshot_on_error)
4. Update 20+ files to use utility functions
5. Refactor long execute methods

---

## Estimated Impact

- **Lines to delete:** ~750+ (duplications)
- **Lines to add:** ~200 (utility modules)
- **Net reduction:** ~550 lines
- **Files to create:** 4 (utils directory + 3 modules)
- **Files to modify:** 39 (registry) + 3 (API) + 45 (duplication removal)
