# Core Concepts

Understand the fundamental concepts of CasareRPA to build effective automation workflows.

---

## In This Section

| Document | Description |
|----------|-------------|
| [Workflows](workflows.md) | Understanding workflow structure |
| [Nodes and Ports](nodes-and-ports.md) | Node types, connections, and data flow |
| [Variables](variables.md) | Working with workflow variables |
| [Execution Modes](execution-modes.md) | Local, robot, and debug execution |
| [Triggers](triggers.md) | Event-driven workflow execution |

---

## Concept Overview

### Workflows

A **workflow** is a sequence of automated steps represented as a directed graph:

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│  Start  │────→│ Action1 │────→│ Action2 │────→│   End   │
└─────────┘     └─────────┘     └─────────┘     └─────────┘
```

- Nodes execute in topological order
- Data flows through port connections
- Variables persist across nodes

### Nodes

**Nodes** are the building blocks of automation:

| Component | Purpose |
|-----------|---------|
| **Input Ports** | Receive data from other nodes |
| **Output Ports** | Send results to connected nodes |
| **Properties** | Configure node behavior |
| **Execute Logic** | Perform the automation action |

```
        ┌──────────────────┐
  In ●──│   Click Node     │──● Out
        ├──────────────────┤
        │ selector: "#btn" │
        │ wait: 1000ms     │
        └──────────────────┘
```

### Data Flow

Data flows through port connections:

```python
# Expression syntax for referencing data
{{ variable_name }}           # Variable reference
{{ prev.output_field }}       # Previous node output
{{ nodes.NodeName.result }}   # Specific node output
```

### Variables

**Variables** store and share data across nodes:

| Type | Scope | Example |
|------|-------|---------|
| Local | Current workflow | `loop_counter` |
| Global | All workflows | `api_key` |
| Environment | System | `HOME_DIR` |

### Execution Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Local** | Direct execution | Development, testing |
| **Robot** | Distributed execution | Production |
| **Debug** | Step-by-step with breakpoints | Troubleshooting |

### Triggers

**Triggers** start workflows automatically:

| Trigger Type | Event Source |
|--------------|--------------|
| Schedule | Cron expressions |
| Webhook | HTTP requests |
| File Watch | File system changes |
| Email | Incoming messages |
| Telegram/WhatsApp | Chat messages |

---

## Visual Guide

```
                    ┌─────────────────────┐
                    │      WORKFLOW       │
                    └──────────┬──────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
  ┌────▼────┐            ┌────▼────┐            ┌────▼────┐
  │  NODES  │            │VARIABLES│            │TRIGGERS │
  └────┬────┘            └────┬────┘            └────┬────┘
       │                       │                       │
  ┌────▼────┐            ┌────▼────┐            ┌────▼────┐
  │ Ports   │            │ Local   │            │Schedule │
  │ Props   │            │ Global  │            │Webhook  │
  │ Logic   │            │ Env     │            │Events   │
  └─────────┘            └─────────┘            └─────────┘
```

---

## Quick Reference

### Port Data Types

| Type | Description | Example |
|------|-------------|---------|
| `any` | Any data type | Pass-through |
| `string` | Text data | `"Hello"` |
| `number` | Numeric | `42`, `3.14` |
| `boolean` | True/False | `true` |
| `object` | JSON object | `{"key": "value"}` |
| `array` | List of items | `[1, 2, 3]` |
| `file` | File path | `C:\data.csv` |

### Property Types

| Type | Widget | Example |
|------|--------|---------|
| `STRING` | Text input | URL field |
| `TEXT` | Multi-line | Script content |
| `INTEGER` | Number input | Timeout |
| `BOOLEAN` | Checkbox | Enable flag |
| `CHOICE` | Dropdown | Browser type |
| `SELECTOR` | CSS/XPath input | Element selector |

---

## Next Steps

| Topic | Document |
|-------|----------|
| Detailed workflow guide | [Workflows](workflows.md) |
| Node connections | [Nodes and Ports](nodes-and-ports.md) |
| Using variables | [Variables](variables.md) |
| Execution options | [Execution Modes](execution-modes.md) |
| Auto-start workflows | [Triggers](triggers.md) |

---

## Related Documentation

- [Node Reference](../../reference/nodes/index.md)
- [Trigger Reference](../../reference/triggers/index.md)
- [Tutorials](../tutorials/index.md)
