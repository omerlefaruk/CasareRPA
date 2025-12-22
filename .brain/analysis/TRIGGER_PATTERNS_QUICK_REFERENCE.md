# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---

# Trigger Lifecycle Patterns - Quick Reference

## Pattern Selection Guide

Choose your trigger pattern based on your use case:

### 1. **Polling Pattern** (8 triggers)
**Use when**: Checking external service at regular intervals
**Implementation**: EmailTrigger, RSSFeedTrigger, TelegramTrigger, GmailTrigger, etc.

```python
class MyTrigger(BaseTrigger):
    async def start(self) -> bool:
        self._running = True
        self._status = TriggerStatus.ACTIVE
        self._poll_task = asyncio.create_task(self._poll_loop())
        return True

    async def stop(self) -> bool:
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        self._status = TriggerStatus.INACTIVE
        return True

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                items = await self._fetch_items()
                for item in items:
                    await self.emit({"item": item})
            except Exception as e:
                logger.error(f"Poll error: {e}")
            await asyncio.sleep(poll_interval)
```

---

### 2. **Scheduler Pattern** (1 trigger)
**Use when**: Time-based execution (cron, interval, one-time)
**Implementation**: ScheduledTrigger (uses APScheduler)

```python
class MyScheduledTrigger(BaseTrigger):
    async def start(self) -> bool:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger

        self._scheduler = AsyncIOScheduler()
        trigger = CronTrigger(hour=9, minute=0)  # Daily at 9 AM
        self._job = self._scheduler.add_job(
            self._on_trigger,
            trigger,
            id=f"trigger_{self.config.id}"
        )
        self._scheduler.start()
        self._status = TriggerStatus.ACTIVE
        return True

    async def stop(self) -> bool:
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
        self._status = TriggerStatus.INACTIVE
        return True

    async def _on_trigger(self) -> None:
        await self.emit({"trigger_time": now})
```

---

### 3. **Event Subscription Pattern** (4 triggers)
**Use when**: Responding to domain events (no polling needed)
**Implementation**: ErrorTrigger

```python
class MyEventTrigger(BaseTrigger):
    async def start(self) -> bool:
        from casare_rpa.domain.events import get_event_bus, SomeEvent

        event_bus = get_event_bus()
        self._handler = lambda e: asyncio.create_task(self._on_event(e))
        event_bus.subscribe(SomeEvent, self._handler)

        self._status = TriggerStatus.ACTIVE
        return True

    async def stop(self) -> bool:
        from casare_rpa.domain.events import get_event_bus, SomeEvent

        event_bus = get_event_bus()
        if self._handler:
            event_bus.unsubscribe(SomeEvent, self._handler)

        self._status = TriggerStatus.INACTIVE
        return True

    async def _on_event(self, event) -> None:
        await self.emit({"error": event.error_message})
```

---

### 4. **HTTP Server Pattern** (2 triggers)
**Use when**: Passive HTTP listener (webhook)
**Implementation**: WebhookTrigger

```python
class WebhookTrigger(BaseTrigger):
    async def start(self) -> bool:
        # HTTP server managed by TriggerManager, not this trigger
        self._status = TriggerStatus.ACTIVE
        return True

    async def stop(self) -> bool:
        self._status = TriggerStatus.INACTIVE
        return True

    # When HTTP request arrives, TriggerManager calls:
    # trigger.emit(payload)
```

---

### 5. **File System Watch Pattern** (1 trigger)
**Use when**: Monitoring filesystem changes
**Implementation**: FileWatchTrigger (uses watchdog)

```python
class FileWatchTrigger(BaseTrigger):
    async def start(self) -> bool:
        from watchdog.observers import Observer

        # Capture event loop for thread-safe communication
        self._event_loop = asyncio.get_running_loop()

        class Handler(FileSystemEventHandler):
            def on_created(self, event):
                # This runs in watchdog's thread!
                # Use asyncio.run_coroutine_threadsafe() to call async
                asyncio.run_coroutine_threadsafe(
                    trigger._on_file_event(event.src_path),
                    self._event_loop  # Use captured loop
                )

        self._observer = Observer()
        self._observer.schedule(Handler(), path, recursive=True)
        self._observer.start()

        self._status = TriggerStatus.ACTIVE
        return True

    async def stop(self) -> bool:
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)  # Wait for thread

        self._status = TriggerStatus.INACTIVE
        return True
```

---

### 6. **Streaming Pattern** (1 trigger)
**Use when**: Long-lived HTTP connection (SSE, WebSocket)
**Implementation**: SSETrigger

```python
class SSETrigger(BaseTrigger):
    async def start(self) -> bool:
        # No timeout on socket (keep-alive connection)
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=None, sock_read=None)
        )

        self._listen_task = asyncio.create_task(self._listen_loop())
        self._status = TriggerStatus.ACTIVE
        return True

    async def stop(self) -> bool:
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

        if self._session:
            await self._session.close()

        self._status = TriggerStatus.INACTIVE
        return True

    async def _listen_loop(self) -> None:
        while True:  # Reconnect loop
            try:
                async with self._session.get(url) as response:
                    async for line in response.content:
                        if line.startswith(b"data:"):
                            await self.emit({"data": parse_sse(line)})
            except Exception as e:
                logger.error(f"SSE error: {e}")
                await asyncio.sleep(2)  # Backoff before reconnect
```

---

## Event Emission Template

All triggers emit via the same method:

```python
# In any trigger, when condition is met:
payload = {
    "port_name_1": value1,
    "port_name_2": value2,
}

metadata = {
    "source": "my_trigger",
    "timestamp": datetime.now(timezone.utc).isoformat(),
}

await self.emit(payload, metadata)
```

The `emit()` method (from BaseTrigger):
- ✅ Checks cooldown
- ✅ Calls event_callback
- ✅ Updates timestamps and counters
- ✅ Logs the event

---

## Configuration Validation Template

```python
def validate_config(self) -> tuple[bool, Optional[str]]:
    config = self.config.config

    # Check required fields
    if not config.get("required_field"):
        return False, "required_field is required"

    # Validate enums
    if config.get("mode") not in ["option1", "option2"]:
        return False, "Invalid mode"

    # Validate ranges
    interval = config.get("interval", 60)
    if not (1 <= interval <= 3600):
        return False, "interval must be 1-3600 seconds"

    return True, None
```

Called automatically in `start()`:
```python
async def start(self) -> bool:
    is_valid, error = self.validate_config()
    if not is_valid:
        self._error_message = error
        self._status = TriggerStatus.ERROR
        return False

    # ... rest of start logic
```

---

## Resource Cleanup Checklist

When implementing `stop()`, clean up:

- [ ] AsyncIO tasks → `task.cancel()` + exception handling
- [ ] HTTP sessions → `await session.close()`
- [ ] Background threads → `.stop()` + `.join(timeout=N)`
- [ ] Event subscriptions → `event_bus.unsubscribe()`
- [ ] Scheduler → `scheduler.shutdown(wait=False)`
- [ ] File observers → `observer.stop()` + `observer.join()`

Example:
```python
async def stop(self) -> bool:
    self._running = False

    # Cancel task
    if self._poll_task:
        self._poll_task.cancel()
        try:
            await self._poll_task
        except asyncio.CancelledError:
            pass

    # Close session
    if self._session:
        await self._session.close()

    # Unsubscribe from events
    if self._handler:
        get_event_bus().unsubscribe(EventType, self._handler)

    self._status = TriggerStatus.INACTIVE
    return True
```

---

## Testing Checklist

For each trigger implementation:

- [ ] `start()` sets status to ACTIVE
- [ ] `stop()` sets status to INACTIVE
- [ ] Resources properly cleaned up in `stop()` (no leaks)
- [ ] `validate_config()` returns (False, msg) for invalid input
- [ ] `emit()` called with correct payload structure
- [ ] Polling tasks cancelled without hanging
- [ ] Event callbacks executed successfully
- [ ] Error handling doesn't crash trigger
- [ ] Metadata captured correctly
- [ ] Success/error counters incremented

---

## Trigger Type Summary

| Pattern | Count | Examples | Use Case |
|---------|-------|----------|----------|
| Polling | 8 | Email, Gmail, RSS, Telegram | External service checks |
| Scheduler | 1 | Scheduled | Time-based execution |
| Event-Driven | 4 | Error, WorkflowCall, Form | Domain events |
| HTTP Server | 2 | Webhook, Calendar | Passive listeners |
| File Watch | 1 | FileWatch | Filesystem monitoring |
| Stream | 1 | SSE | Long-lived connections |

---

## Common Mistakes to Avoid

### ❌ Don't: Blocking calls in async
```python
# WRONG
async def _poll_loop(self):
    while True:
        time.sleep(60)  # BLOCKS entire event loop!
        items = requests.get(url).json()  # Blocks!
        await self.emit(payload)
```

### ✅ Do: Async all the way
```python
# CORRECT
async def _poll_loop(self):
    while True:
        await asyncio.sleep(60)  # Non-blocking
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                items = await resp.json()
        await self.emit(payload)
```

---

### ❌ Don't: Call asyncio.get_event_loop() in threads
```python
# WRONG - Called from watchdog thread
def on_file_event(self, event):
    loop = asyncio.get_event_loop()  # FAILS in different thread!
    loop.create_task(...)
```

### ✅ Do: Capture loop once in start()
```python
async def start(self):
    self._loop = asyncio.get_running_loop()  # Capture in main thread

    class Handler:
        def on_file_event(self, event):
            asyncio.run_coroutine_threadsafe(
                self._async_handler(),
                self._loop  # Use captured loop
            )
```

---

### ❌ Don't: Forget to cancel tasks
```python
# WRONG
async def stop(self):
    self._running = False
    # Task still running! Memory leak!
    self._status = TriggerStatus.INACTIVE
    return True
```

### ✅ Do: Cancel and await
```python
# CORRECT
async def stop(self):
    self._running = False
    if self._task:
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
    self._status = TriggerStatus.INACTIVE
    return True
```

---

### ❌ Don't: Emit without handling exceptions
```python
# WRONG
await self.emit(payload)  # If callback fails, trigger crashes!
```

### ✅ Do: Exceptions handled in emit()
```python
# CORRECT - emit() catches and logs exceptions
result = await self.emit(payload)
# Returns False if emit failed, True if succeeded
```

---

## Performance Tips

1. **Set appropriate polling intervals**
   - Too fast (1-5s): High CPU/network load
   - Just right (30-60s): Good for most use cases
   - Too slow (10+ min): May miss events

2. **Implement debouncing for fast events**
   ```python
   async def _queue_event(self, file_path):
       self._pending[file_path] = now
       # Wait debounce_ms before processing
       await asyncio.sleep(debounce_ms / 1000)
       await self.emit(payload)
   ```

3. **Use context managers for HTTP sessions**
   ```python
   async with aiohttp.ClientSession() as session:
       async with session.get(url) as resp:
           data = await resp.json()
   ```

4. **Set timeouts to prevent hanging**
   ```python
   aiohttp.ClientSession(
       timeout=aiohttp.ClientTimeout(total=30, sock_read=10)
   )
   ```

---

**See TRIGGER_LIFECYCLE_REVIEW.md for comprehensive analysis**
