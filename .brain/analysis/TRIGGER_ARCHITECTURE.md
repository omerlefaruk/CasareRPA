# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---

# Trigger Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Canvas (UI Layer)                        │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Visual Trigger Nodes                         │  │
│  │  (TriggerNode, WebhookTriggerNode, etc.)            │  │
│  │                                                      │  │
│  │  • Define output ports for trigger payload          │  │
│  │  • Configure trigger via properties                 │  │
│  │  • No exec_in port (start workflows)               │  │
│  │  • Only exec_out port                              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↑  ↓
              (Serialization/Deserialization)
                          ↑  ↓
┌─────────────────────────────────────────────────────────────┐
│                 Orchestrator (Runtime Layer)                │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Trigger Manager                            │  │
│  │                                                      │  │
│  │  • Start/stop triggers from workflow                │  │
│  │  • Manage trigger lifecycle                         │  │
│  │  • Route HTTP requests to webhooks                  │  │
│  │  • Convert TriggerEvent to JobSubmission            │  │
│  │  • Track trigger state                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↑  ↓                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Trigger Registry                           │  │
│  │                                                      │  │
│  │  • Singleton registry of trigger classes            │  │
│  │  • @register_trigger decorator auto-registers       │  │
│  │  • Maps TriggerType enum to trigger class           │  │
│  │  • Creates trigger instances                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↑  ↓
┌─────────────────────────────────────────────────────────────┐
│              Trigger Backend (Business Logic)               │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              BaseTrigger (Abstract)                  │  │
│  │                                                      │  │
│  │  async def start() → TriggerStatus.ACTIVE           │  │
│  │  async def stop()  → TriggerStatus.INACTIVE         │  │
│  │  async def emit(payload, metadata) → bool           │  │
│  │  validate_config() → (bool, error_msg)              │  │
│  │  pause() / resume() → bool                          │  │
│  │                                                      │  │
│  │  Properties:                                         │  │
│  │  • _status: TriggerStatus                           │  │
│  │  • _event_callback: Callback when fired             │  │
│  │  • config: BaseTriggerConfig                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↑                                   │
│         ┌────────────────┼────────────────┐                │
│         │                │                │                │
│  ┌─────────────┐  ┌────────────┐  ┌──────────────┐         │
│  │  Polling    │  │ Scheduler  │  │   Event      │  ...    │
│  │  Triggers   │  │  Trigger   │  │  Driven      │         │
│  │             │  │            │  │  Triggers    │         │
│  │ • Email     │  │ Schedule   │  │ • Error      │         │
│  │ • Gmail     │  │            │  │ • Workflow   │         │
│  │ • RSS       │  │ APScheduler│  │ • Form       │         │
│  │ • Telegram  │  │ asyncio    │  │ • Calendar   │         │
│  │             │  │            │  │              │         │
│  │ asyncio.    │  │ CronTrigger│  │ event_bus    │         │
│  │ create_task │  │ (APSched)  │  │ .subscribe() │         │
│  │             │  │            │  │              │         │
│  │ Polling     │  │ Time-based │  │ Event        │         │
│  │ interval    │  │ execution  │  │ subscription │         │
│  └─────────────┘  └────────────┘  └──────────────┘         │
│         ↓ (more types below)                                │
└─────────────────────────────────────────────────────────────┘
                          ↑  ↓
             (TriggerEvent with payload)
                          ↑  ↓
┌─────────────────────────────────────────────────────────────┐
│              Domain Layer (Business Events)                 │
│                                                             │
│  • TriggerEvent: Fired when trigger condition met          │
│  • TriggerType enum: Enum of all trigger types             │
│  • TriggerStatus: Status of trigger lifecycle              │
│  • TriggerEventCallback: Callback type signature           │
│  • BaseTriggerConfig: Configuration dataclass              │
└─────────────────────────────────────────────────────────────┘
```

---

## Trigger Pattern Breakdown

### 1. Polling Pattern (8 triggers)

```
┌─────────────────────────────────────────┐
│         Polling Trigger                 │
└─────────────────────────────────────────┘
         ↓ start()
    ┌─────────────────────────────────┐
    │ ✓ Validate config               │
    │ ✓ Set _running = True           │
    │ ✓ Create asyncio.Task           │
    │ ✓ Status = ACTIVE               │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │ _poll_loop() (Concurrent)       │
    │                                 │
    │ while _running:                 │
    │   new_items = await fetch()     │
    │   for item in new_items:        │
    │     await emit(payload)         │
    │   await sleep(interval)         │
    │                                 │
    │ Runs concurrently with main     │
    │ event loop - doesn't block      │
    └─────────────────────────────────┘
         ↓
         │ (Polling continues in background)
         │
    ┌─────────────────────────────────┐
    │  User calls stop()              │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │ ✓ Set _running = False          │
    │ ✓ task.cancel()                 │
    │ ✓ await task (wait for exit)    │
    │ ✓ Status = INACTIVE             │
    └─────────────────────────────────┘

Examples: EmailTrigger, GmailTrigger, RSSFeedTrigger, TelegramTrigger
```

### 2. Scheduler Pattern (1 trigger)

```
┌─────────────────────────────────────────┐
│       APScheduler-Based Trigger         │
└─────────────────────────────────────────┘
         ↓ start()
    ┌─────────────────────────────────┐
    │ ✓ Create AsyncIOScheduler       │
    │ ✓ Build cron/interval trigger   │
    │ ✓ Add job: _on_schedule()       │
    │ ✓ scheduler.start()             │
    │ ✓ Status = ACTIVE               │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │ APScheduler monitors time       │
    │                                 │
    │ When schedule fires:            │
    │   await _on_schedule()          │
    │   await emit(payload)           │
    │                                 │
    │ Example: Every day at 9 AM      │
    │          Every Monday 10 AM     │
    │          Every 5 minutes        │
    │          Custom cron expr       │
    └─────────────────────────────────┘
         ↓
         │ (Scheduler continues in event loop)
         │
    ┌─────────────────────────────────┐
    │  User calls stop()              │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │ ✓ scheduler.shutdown(wait=False)│
    │ ✓ Status = INACTIVE             │
    └─────────────────────────────────┘

Example: ScheduledTrigger (cron, interval, once)
```

### 3. Event Subscription Pattern (4 triggers)

```
┌─────────────────────────────────────────┐
│      Event-Driven Trigger               │
└─────────────────────────────────────────┘
         ↓ start()
    ┌─────────────────────────────────┐
    │ ✓ Get event_bus singleton       │
    │ ✓ Create handler wrapper        │
    │ ✓ event_bus.subscribe()         │
    │ ✓ Status = ACTIVE               │
    │                                 │
    │ Handler bridges:                │
    │ sync event → async emit         │
    │                                 │
    │ = asyncio.create_task(...)      │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │ Waiting for domain event        │
    │                                 │
    │ When event fires (e.g.,         │
    │ WorkflowFailed):                │
    │   handler() called              │
    │   create_task(_on_event)        │
    │   await emit(payload)           │
    │                                 │
    │ Zero overhead when idle         │
    │ (purely event-driven)           │
    └─────────────────────────────────┘
         ↓
         │
    ┌─────────────────────────────────┐
    │  User calls stop()              │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │ ✓ event_bus.unsubscribe()       │
    │ ✓ Status = INACTIVE             │
    └─────────────────────────────────┘

Examples: ErrorTrigger, WorkflowCallTrigger, FormTrigger
```

### 4. Passive HTTP Pattern (2 triggers)

```
┌─────────────────────────────────────────┐
│       HTTP Server-Based Trigger         │
└─────────────────────────────────────────┘
         ↓ start()
    ┌─────────────────────────────────┐
    │ ✓ (No resources allocated)      │
    │ ✓ Status = ACTIVE               │
    │                                 │
    │ HTTP server managed by          │
    │ TriggerManager, not this         │
    │ trigger                         │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │ Listening for HTTP requests     │
    │                                 │
    │ When HTTP request arrives:      │
    │   TriggerManager routes to      │
    │   trigger.emit(payload)         │
    │                                 │
    │ Example:                        │
    │   POST /webhooks/invoice        │
    │   → trigger.emit(invoice_data)  │
    └─────────────────────────────────┘
         ↓
         │
    ┌─────────────────────────────────┐
    │  User calls stop()              │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │ ✓ Status = INACTIVE             │
    │ ✓ (No resources to clean up)    │
    └─────────────────────────────────┘

Examples: WebhookTrigger
```

### 5. File System Watch Pattern (1 trigger)

```
┌─────────────────────────────────────────┐
│    File System Watch Trigger            │
└─────────────────────────────────────────┘
         ↓ start()
    ┌─────────────────────────────────┐
    │ ✓ Capture asyncio.get_running   │
    │   _loop (IMPORTANT!)            │
    │                                 │
    │ ✓ Create watchdog.Observer      │
    │ ✓ Schedule with custom Handler  │
    │ ✓ observer.start() [=thread]    │
    │ ✓ Status = ACTIVE               │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │ watchdog.Observer (Thread)      │
    │                                 │
    │ Monitors filesystem              │
    │ When file event occurs:         │
    │   Handler.on_event()            │
    │   [Runs in watchdog thread!]    │
    │                                 │
    │   asyncio.run_coroutine_        │
    │   threadsafe(                   │
    │     _queue_event(),             │
    │     captured_loop  [Important]  │
    │   )                             │
    │                                 │
    │   ↓ Queued to main loop ↓       │
    │   await _queue_event()          │
    │   await emit(payload)           │
    └─────────────────────────────────┘
         ↓
         │ (File watching continues)
         │
    ┌─────────────────────────────────┐
    │  User calls stop()              │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │ ✓ observer.stop()               │
    │ ✓ observer.join(timeout=5)      │
    │   [Wait for thread to exit]     │
    │ ✓ Status = INACTIVE             │
    └─────────────────────────────────┘

Example: FileWatchTrigger
Key Pattern: asyncio.run_coroutine_threadsafe()
```

### 6. Streaming Pattern (1 trigger)

```
┌─────────────────────────────────────────┐
│    Server-Sent Events Trigger           │
└─────────────────────────────────────────┘
         ↓ start()
    ┌─────────────────────────────────┐
    │ ✓ Create aiohttp.ClientSession  │
    │   (no timeout on socket!)       │
    │ ✓ create_task(_listen_loop)     │
    │ ✓ Status = ACTIVE               │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │ _listen_loop() (Concurrent)     │
    │                                 │
    │ while True:  # Reconnect        │
    │   try:                          │
    │     async with get() as resp:   │
    │       async for line in resp:   │
    │         await emit(payload)     │
    │   except:                       │
    │     await sleep(backoff)        │
    │     [try reconnect]             │
    │                                 │
    │ Handles long connections        │
    │ with auto-reconnect             │
    └─────────────────────────────────┘
         ↓
         │ (SSE stream continues)
         │
    ┌─────────────────────────────────┐
    │  User calls stop()              │
    └─────────────────────────────────┘
         ↓
    ┌─────────────────────────────────┐
    │ ✓ task.cancel()                 │
    │ ✓ await task                    │
    │ ✓ await session.close()         │
    │ ✓ Status = INACTIVE             │
    └─────────────────────────────────┘

Example: SSETrigger
```

---

## Data Flow: Trigger Fire → Workflow Execution

```
┌────────────────────────────────────────────────────────────────┐
│                    Trigger Fires                              │
│  (Schedule, poll, event, HTTP, file, SSE detected)            │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│                   trigger.emit(payload)                        │
│  (in BaseTrigger base class)                                   │
│                                                                │
│  1. Check cooldown (skip if in cooldown)                      │
│  2. Create TriggerEvent                                        │
│  3. Update last_triggered timestamp                            │
│  4. Increment trigger_count                                    │
│  5. Call event_callback(event)                                │
│     → TriggerManager receives event                            │
│  6. Increment success_count                                    │
│  7. Log the event                                             │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│              TriggerManager.on_trigger_event()                 │
│                                                                │
│  1. Receive TriggerEvent                                      │
│  2. Get trigger node from workflow                            │
│  3. Populate trigger node output ports from payload           │
│  4. Create JobSubmission                                      │
│  5. Submit to OrchestratorEngine                              │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│            OrchestratorEngine.execute_job()                    │
│                                                                │
│  1. Load workflow                                             │
│  2. Find trigger node (marked as entry point)                 │
│  3. Execute nodes starting from trigger's exec_out            │
│  4. Access trigger payload from output ports                  │
│     (subject, sender, body, etc.)                            │
│  5. Execute rest of workflow                                  │
│  6. Complete job                                              │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│                   Workflow Complete                            │
│  (Results, logs, state stored)                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Configuration Layer

```
┌─────────────────────────────────────┐
│     Visual Node Properties          │
│     (UI configures via properties)  │
│                                     │
│  • endpoint: "/webhook/invoice"     │
│  • auth_type: "api_key"             │
│  • methods: ["POST", "PUT"]         │
│  • poll_interval: 60                │
│  • cron_expression: "0 9 * * *"     │
│  • enabled: true                    │
│  • cooldown_seconds: 0              │
└─────────────────────────────────────┘
         ↓ (Serialize to workflow JSON)
         ↓
┌─────────────────────────────────────┐
│    Workflow Serialization           │
│    (Stored in .casare file)         │
│                                     │
│  {                                  │
│    "node_id": "trigger_1",          │
│    "node_type": "WebhookTriggerNode"│
│    "properties": {                  │
│      "endpoint": "...",             │
│      "auth_type": "...",            │
│      ...                            │
│    }                                │
│  }                                  │
└─────────────────────────────────────┘
         ↓ (Deserialize at runtime)
         ↓
┌─────────────────────────────────────┐
│   TriggerNode Instance              │
│   (Created in canvas)               │
│                                     │
│   config = {"endpoint": "...", ...} │
└─────────────────────────────────────┘
         ↓ (get_trigger_type() → TriggerType.WEBHOOK)
         ↓ (get_trigger_config() → {...})
         ↓
┌─────────────────────────────────────┐
│  BaseTriggerConfig                  │
│  (Passed to trigger implementation) │
│                                     │
│  id = "trig_abc123"                 │
│  name = "Invoice Webhook"           │
│  trigger_type = TriggerType.WEBHOOK │
│  config = {"endpoint": "...", ...}  │
│  enabled = true                     │
│  priority = 1                       │
│  cooldown_seconds = 0               │
└─────────────────────────────────────┘
         ↓ (Passed to constructor)
         ↓
┌─────────────────────────────────────┐
│    Trigger Implementation            │
│    (WebhookTrigger, etc.)           │
│                                     │
│    validate_config()                │
│    start()                          │
│    stop()                           │
│    emit(payload)                    │
└─────────────────────────────────────┘
```

---

## Lifecycle State Machine

```
┌──────────┐
│ INACTIVE │ (Initial state, or after stop())
└────┬─────┘
     │ start() called
     ↓
┌───────────┐
│ STARTING  │ (Optional intermediate)
└────┬──────┘
     │ validation passed
     ↓ resources allocated
┌──────────┐
│  ACTIVE  │ (Trigger is monitoring)
├────┬─────┤
│    │     │ pause()
│    │     ↓ (optional)
│    │  ┌─────────┐
│    │  │ PAUSED  │
│    │  │         │
│    │  └────┬────┘
│    │       │ resume()
│    └───────┘
│
│ stop() called
↓
┌──────────┐
│ INACTIVE │
└──────────┘

ERROR state (if validation fails):
INACTIVE ──→ ERROR (validation fail)
             │
             └→ (must start() again)
```

---

## Configuration Validation Pipeline

```
┌──────────────────────────────┐
│  User configures in Canvas   │
│  via properties              │
└──────────────────────────────┘
           ↓
┌──────────────────────────────┐
│  Workflow saved              │
│  Config in JSON              │
└──────────────────────────────┘
           ↓
┌──────────────────────────────┐
│  Workflow loaded             │
│  TriggerNode created         │
│  config set                  │
└──────────────────────────────┘
           ↓
┌──────────────────────────────┐
│  trigger.start() called      │
└──────────────────────────────┘
           ↓
┌──────────────────────────────┐
│  validate_config()           │
│  Returns (valid, error_msg)  │
└──────────────────────────────┘
           ↓
      ┌────┴─────┐
      │           │
    TRUE        FALSE
      │           │
      ↓           ↓
  ┌─────┐    ┌──────┐
  │ACTIVE│   │ERROR │
  └─────┘    └──────┘
                ↓
          error_message
          logged/shown
          to user
```

---

## Thread Safety Model

```
┌────────────────────────────────────────┐
│    Main Event Loop (Asyncio)           │
│                                        │
│  • Runs all async code                │
│  • All triggers' coroutines            │
│  • emit() calls                        │
│  • WebhookTrigger API handler          │
│                                        │
│  Thread: Main Python thread            │
└────────────────────────────────────────┘

ISOLATED from:

┌────────────────────────────────────────┐
│    watchdog.Observer (Thread)          │
│    [Only in FileWatchTrigger]          │
│                                        │
│  • Monitors filesystem                │
│  • Calls Handler.on_event()            │
│  • Different thread!                   │
│                                        │
│  Thread: Separate observer thread      │
└────────────────────────────────────────┘

BRIDGE:
  asyncio.run_coroutine_threadsafe()
  (Queues coroutine to main loop)

┌────────────────────────────────────────┐
│  Handler.on_event()                    │
│  (runs in watchdog thread)             │
│                                        │
│  asyncio.run_coroutine_threadsafe(     │
│      trigger._on_file_event(path),     │
│      captured_event_loop               │
│  )                                     │
│                                        │
│  ↓ Queues to main loop ↓               │
│                                        │
│  await _on_file_event(path)            │
│  await emit(payload)                   │
│                                        │
│  [Executes in main event loop]         │
└────────────────────────────────────────┘
```

---

## Resource Lifecycle Matrix

| Component | Allocated | Deallocated | Mechanism |
|-----------|-----------|-------------|-----------|
| **AsyncIO Task** | start() | stop() | create_task() / cancel() / await |
| **APScheduler** | start() | stop() | AsyncIOScheduler() / shutdown() |
| **Event Sub** | start() | stop() | subscribe() / unsubscribe() |
| **HTTP Session** | start() | stop() | ClientSession() / await close() |
| **Observer (file)** | start() | stop() | Observer() / stop() / join() |
| **Config** | start() | - | validate_config() |

All resources properly cleaned up in `stop()`.

---

**See TRIGGER_LIFECYCLE_REVIEW.md for detailed analysis**
