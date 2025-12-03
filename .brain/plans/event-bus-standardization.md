# Event Bus Standardization Plan

## Current State Analysis

### Two Duplicate Event Bus Systems

**1. Domain EventBus** (`src/casare_rpa/domain/events.py`)
- Simple event bus for workflow execution
- Uses `EventType` from `domain/value_objects/types.py` (13 types)
- Includes `emit()` convenience method
- Has `get_event_bus()` singleton accessor
- Used by: Robot, Application layer (execute_workflow, workflow_migration, error_recovery)

**2. Presentation EventBus** (`src/casare_rpa/presentation/canvas/events/`)
- Rich event bus for Canvas UI
- Uses `EventType` from `event_types.py` (100+ types)
- Thread-safe with caching and metrics
- Includes: EventFilter, EventPriority, EventBatcher, LazySubscription, QtSignalBridge
- Used by: Canvas UI components

### EventType Overlap
| Domain EventType | Presentation EventType |
|-----------------|----------------------|
| NODE_STARTED | NODE_EXECUTION_STARTED |
| NODE_COMPLETED | NODE_EXECUTION_COMPLETED |
| NODE_ERROR | NODE_EXECUTION_FAILED |
| NODE_SKIPPED | NODE_EXECUTION_SKIPPED |
| WORKFLOW_STARTED | EXECUTION_STARTED |
| WORKFLOW_COMPLETED | EXECUTION_COMPLETED |
| WORKFLOW_ERROR | EXECUTION_FAILED |
| WORKFLOW_PAUSED | EXECUTION_PAUSED |
| WORKFLOW_RESUMED | EXECUTION_RESUMED |
| VARIABLE_SET | VARIABLE_SET |
| LOG_MESSAGE | LOG_MESSAGE |

## Decision: Keep Separate But Standardize

### Rationale
1. **Layer Separation**: Domain and Presentation have different concerns
2. **Dependency Flow**: Presentation can import from Domain, not vice versa
3. **Feature Richness**: Presentation needs Qt-specific features (signals, batching, lazy subscription)
4. **Robot Independence**: Robot (headless) should not depend on Qt/Presentation

### Standardization Actions

1. **Event Naming Convention** - Standardize across both systems
   - Use NOUN_VERB_STATE pattern
   - Past tense for completed: `_COMPLETED`, `_STARTED`, `_FAILED`
   - Present progressive for ongoing: `_RUNNING`, `_PAUSING`

2. **Bridge Pattern** - Create adapter when presentation needs domain events
   - Presentation subscribes to domain events and re-publishes as presentation events
   - Single point of translation

3. **Documentation** - Add event contracts documentation

## Event Naming Standards

### Format: `{SCOPE}_{ACTION}_{STATE?}`

**Scopes**: NODE, WORKFLOW, EXECUTION, CONNECTION, PORT, VARIABLE, PROJECT, TRIGGER, PANEL, UI

**Actions**:
- Lifecycle: START, COMPLETE, FAIL, SKIP, CANCEL, PAUSE, RESUME
- CRUD: CREATE, ADD, UPDATE, REMOVE, DELETE
- State: CHANGE, SELECT, ENABLE, DISABLE

**States** (optional):
- _ED suffix for completed actions
- _ING suffix for in-progress

### Examples
```
NODE_EXECUTION_STARTED    # Node began executing
NODE_EXECUTION_COMPLETED  # Node finished successfully
NODE_EXECUTION_FAILED     # Node encountered error
NODE_PROPERTY_CHANGED     # Node property was modified
WORKFLOW_SAVED           # Workflow was saved
WORKFLOW_MODIFIED        # Workflow has unsaved changes
```

## Implementation

### Phase 1: Document Current Contracts (This PR)
- [x] Analyze all event types
- [x] Document event data schemas
- [ ] Create EVENT_CONTRACTS.md

### Phase 2: Add Missing Event Types to Domain
- Add `WORKFLOW_STOPPED` and `WORKFLOW_PROGRESS` (already in domain)
- Ensure parity for execution events

### Phase 3: Create Domain-to-Presentation Bridge
- File: `presentation/canvas/events/domain_bridge.py`
- Subscribe to domain events, emit presentation events
- Run in Canvas startup

## Event Data Contracts

### Domain Events (from domain/value_objects/types.py)

```python
# NODE_STARTED
{
    "node_id": str,
    "node_type": str,
    "timestamp": datetime
}

# NODE_COMPLETED
{
    "node_id": str,
    "result": Dict[str, Any],
    "duration_ms": float
}

# NODE_ERROR
{
    "node_id": str,
    "error": str,
    "error_code": str,
    "traceback": Optional[str]
}

# WORKFLOW_STARTED
{
    "workflow_id": str,
    "workflow_name": str,
    "total_nodes": int
}

# WORKFLOW_COMPLETED
{
    "workflow_id": str,
    "status": str,
    "duration_ms": float,
    "results": Dict[str, Any]
}

# WORKFLOW_PROGRESS
{
    "workflow_id": str,
    "completed_nodes": int,
    "total_nodes": int,
    "current_node_id": Optional[str]
}

# VARIABLE_SET
{
    "name": str,
    "value": Any,
    "scope": str  # "workflow", "project", "global"
}

# LOG_MESSAGE
{
    "level": str,  # "DEBUG", "INFO", "WARNING", "ERROR"
    "message": str,
    "source": Optional[str]
}
```

## Unresolved Questions

1. Should domain EventBus also be singleton like presentation?
   - Currently: `get_event_bus()` returns global instance
   - Answer: Yes, keep singleton for simplicity

2. Should we add async event support to domain?
   - Answer: Not now. Keep domain simple and sync.

3. How to handle cross-process events (Robot to Canvas)?
   - Answer: WebSocket bridge already handles this via OrchestratorClient
