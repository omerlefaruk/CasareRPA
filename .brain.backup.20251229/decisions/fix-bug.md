# Decision Tree: Fixing a Bug

## Quick Decision

```
What type of bug?
├─ CRASH/EXCEPTION → Step 1: Find stack trace
├─ WRONG OUTPUT → Step 2: Trace data flow
├─ UI NOT UPDATING → Step 3: Check signal/slot
├─ PERFORMANCE → Step 4: Profile bottleneck
└─ FLAKY TEST → Step 5: Check async/timing
```

---

## Step 1: Crash/Exception

### 1.1 Find the Stack Trace

```bash
# Search for error in logs
Grep: "ERROR|Exception|Traceback" --path logs/

# Find error handling in code
Grep: "except|raise" --path src/casare_rpa/
```

### 1.2 Locate the Source

| Stack Frame | Look At |
|-------------|---------|
| `nodes/*.py` | Node `execute()` method |
| `presentation/canvas/*.py` | UI event handlers |
| `infrastructure/*.py` | External API calls |
| `domain/*.py` | Business logic validation |

### 1.3 Common Crash Fixes

| Error | Likely Cause | Fix |
|-------|--------------|-----|
| `AttributeError: 'NoneType'` | Missing null check | Add `if obj is not None` |
| `KeyError` | Missing dict key | Use `dict.get(key, default)` |
| `TypeError: cannot unpack` | Wrong return type | Check function signature |
| `TimeoutError` | Playwright timeout | Increase timeout, add retry |
| `ConnectionError` | Network issue | Add retry with backoff |

---

## Step 2: Wrong Output

### 2.1 Trace Data Flow

```
Input → Node A → Node B → Output
         ↓         ↓
      Debug A   Debug B
```

### 2.2 Add Debug Points

```python
from loguru import logger

# In the suspected node
async def execute(self, context):
    input_val = self.get_input_value("input")
    logger.debug(f"Input: {input_val}")  # AI-DEBUG: Remove after fix

    result = transform(input_val)
    logger.debug(f"Output: {result}")  # AI-DEBUG: Remove after fix

    return {"success": True, "data": result}
```

### 2.3 Check These

- [ ] Input port connected correctly?
- [ ] Variable resolution working? (`{{variable}}` syntax)
- [ ] Type coercion correct? (string vs int)
- [ ] Previous node setting output correctly?

---

## Step 3: UI Not Updating

### 3.1 Signal/Slot Checklist

```python
# WRONG - Missing @Slot decorator
def on_button_clicked(self):
    self.update_ui()

# RIGHT - With @Slot
@Slot()
def on_button_clicked(self):
    self.update_ui()

# WRONG - Lambda in connection
button.clicked.connect(lambda: self.do_thing(arg))

# RIGHT - functools.partial
from functools import partial
button.clicked.connect(partial(self.do_thing, arg))
```

### 3.2 Thread Safety

```python
# WRONG - UI update from background thread
def background_task(self):
    result = long_operation()
    self.label.setText(result)  # Crash!

# RIGHT - Use signal to marshal to main thread
class MyWidget(QWidget):
    result_ready = Signal(str)

    def __init__(self):
        self.result_ready.connect(self._on_result)

    @Slot(str)
    def _on_result(self, result: str):
        self.label.setText(result)

    def background_task(self):
        result = long_operation()
        self.result_ready.emit(result)  # Safe!
```

### 3.3 Event Bus Issues

```python
# Check subscription
from casare_rpa.domain.events import get_event_bus

bus = get_event_bus()

# Verify handler is subscribed
bus.subscribe(EventType.NODE_COMPLETED, self._on_node_completed)

# Verify event is being published
bus.publish(NodeCompleted(node_id="x", ...))
```

---

## Step 4: Performance Bug

### 4.1 Profile First

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run slow operation
slow_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 slow functions
```

### 4.2 Common Performance Issues

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| UI freezes | Blocking main thread | Move to QThread/asyncio |
| Slow startup | Too many imports | Lazy load modules |
| Memory growth | Event handler leak | Disconnect signals on cleanup |
| Slow canvas | Too many repaints | Batch updates, use `update()` not `repaint()` |

### 4.3 Quick Fixes

```python
# Batch canvas updates
self.setUpdatesEnabled(False)
for node in nodes:
    self.add_node(node)
self.setUpdatesEnabled(True)

# Lazy load heavy modules
def get_playwright():
    global _playwright
    if _playwright is None:
        from playwright.async_api import async_playwright
        _playwright = async_playwright
    return _playwright
```

---

## Step 5: Flaky Test

### 5.1 Async Timing Issues

```python
# WRONG - Race condition
@pytest.mark.asyncio
async def test_flaky():
    start_async_task()
    assert result == expected  # May not be ready!

# RIGHT - Wait for completion
@pytest.mark.asyncio
async def test_stable():
    result = await start_async_task()
    assert result == expected
```

### 5.2 Mock Timing

```python
# WRONG - Mock returns immediately
mock_page.wait_for_selector.return_value = element

# RIGHT - Mock async behavior
mock_page.wait_for_selector = AsyncMock(return_value=element)
```

### 5.3 Isolate State

```python
# WRONG - Tests share state
class TestSuite:
    def test_a(self):
        global_state.append("a")

    def test_b(self):
        assert len(global_state) == 0  # Fails if test_a runs first!

# RIGHT - Fresh state per test
@pytest.fixture
def clean_state():
    yield []

def test_a(clean_state):
    clean_state.append("a")
    assert len(clean_state) == 1
```

---

## Bug Fix Workflow

```
1. REPRODUCE → Create minimal test case
2. LOCATE → Find exact file:line
3. UNDERSTAND → Read surrounding code
4. FIX → Make minimal change
5. TEST → Run related tests
6. VERIFY → Check no regressions
```

---

## Files to Check by Bug Type

| Bug Type | Check These Files |
|----------|-------------------|
| Node execution | `nodes/{category}/*.py`, `domain/entities/base_node.py` |
| Canvas display | `presentation/canvas/graph/*.py` |
| Connections | `presentation/canvas/connections/*.py` |
| Properties panel | `presentation/canvas/ui/properties*.py` |
| Serialization | `presentation/canvas/serialization/*.py` |
| Events | `domain/events.py`, `presentation/canvas/events/` |
| Credentials | `domain/credentials.py`, `infrastructure/security/` |

---

*See also: `.brain/systemPatterns.md` Section 6 (Error Handling)*
