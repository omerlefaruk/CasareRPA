# User Guides

Advanced guides and best practices for building robust automation workflows.

---

## In This Section

| Document | Description |
|----------|-------------|
| [Control Flow](control-flow.md) | Loops, conditionals, and branching |
| [Subflows](subflows.md) | Reusable workflow components |
| [Credentials](credentials.md) | Secure credential management |
| [Debugging](debugging.md) | Troubleshooting workflow issues |
| [AI Assistant](ai-assistant.md) | Using AI for workflow generation |
| [Best Practices](best-practices.md) | Production-ready workflow design |

---

## Guide Overview

### Control Flow

Master workflow control structures:

```
┌─────────┐     ┌───────────┐     ┌─────────┐
│  Start  │────→│ Condition │──Y──│ Action  │
└─────────┘     └─────┬─────┘     └────┬────┘
                      │N               │
                      ▼                │
                ┌─────────┐           │
                │ Alt Act │───────────┘
                └─────────┘
```

- **If/Else**: Conditional branching
- **For Each**: Iterate over collections
- **While Loop**: Repeat until condition
- **Try/Catch**: Error handling

### Subflows

Create reusable workflow components:

```
┌─────────────────────────────────────────┐
│  Main Workflow                          │
│                                         │
│  [Start] → [Subflow: Login] → [Action]  │
│                   ↓                     │
│            ┌─────────────┐              │
│            │   Login     │              │
│            │  Subflow    │              │
│            │ ┌───┐ ┌───┐ │              │
│            │ │Nav│→│Log│ │              │
│            │ └───┘ └───┘ │              │
│            └─────────────┘              │
└─────────────────────────────────────────┘
```

### Credential Management

Secure handling of sensitive data:

| Method | Use Case |
|--------|----------|
| **Vault** | Enterprise secrets |
| **Environment** | Local development |
| **Credential Store** | Windows Credential Manager |

### Debugging

Troubleshoot workflows effectively:

- **Breakpoints**: Pause at specific nodes
- **Step Execution**: Execute node by node
- **Variable Inspector**: View runtime state
- **Log Viewer**: Track execution flow

### AI Assistant

Generate workflows with natural language:

```
User: "Create a workflow that downloads all images from a webpage"

AI: Creates workflow with:
    → Navigate to URL
    → Extract image URLs
    → For Each image:
        → Download file
        → Save to folder
```

### Best Practices

Production-ready patterns:

| Practice | Description |
|----------|-------------|
| **Error Handling** | Try/Catch around external calls |
| **Logging** | Log key actions and data |
| **Timeouts** | Set appropriate wait limits |
| **Cleanup** | Release resources on completion |

---

## Quick Navigation

| Goal | Guide |
|------|-------|
| Add conditions and loops | [Control Flow](control-flow.md) |
| Reuse workflow parts | [Subflows](subflows.md) |
| Handle passwords securely | [Credentials](credentials.md) |
| Fix workflow issues | [Debugging](debugging.md) |
| Generate with AI | [AI Assistant](ai-assistant.md) |
| Build for production | [Best Practices](best-practices.md) |

---

## Related Documentation

- [Core Concepts](../core-concepts/index.md)
- [Tutorials](../tutorials/index.md)
- [Troubleshooting](../../operations/troubleshooting.md)
