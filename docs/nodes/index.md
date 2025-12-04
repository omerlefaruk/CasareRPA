# Node Reference

Complete reference for all automation nodes in CasareRPA v3.1.

**Total Nodes:** 405 across 33 categories

## Node Categories

### Core Workflow

| Category | Nodes | Description |
|----------|-------|-------------|
| [Basic](basic/index.md) | 3 | Start, End, Comment nodes |
| [Control Flow](control-flow/index.md) | 12 | If, Loop, Switch, Try/Catch |
| [Variable](variable/index.md) | 3 | Get/Set/Delete variables |
| [Trigger Nodes](trigger_nodes/index.md) | 18 | Workflow triggers (Manual, Scheduled, Webhook, etc.) |

### Web Automation

| Category | Nodes | Description |
|----------|-------|-------------|
| [Browser](browser/index.md) | 6 | Playwright browser automation |
| [Navigation](navigation/index.md) | 4 | Page navigation |
| [Wait](wait/index.md) | 3 | Wait conditions |

### Desktop Automation

| Category | Nodes | Description |
|----------|-------|-------------|
| [Desktop Nodes](desktop_nodes/index.md) | 48 | Windows UIAutomation |
| [Interaction](interaction/index.md) | 3 | Mouse/keyboard interaction |

### Data Operations

| Category | Nodes | Description |
|----------|-------|-------------|
| [Data](data/index.md) | 3 | Data extraction |
| [Dict](dict/index.md) | 12 | Dictionary operations |
| [List](list/index.md) | 14 | List/array operations |
| [String](string/index.md) | 4 | String manipulation |
| [Text](text/index.md) | 14 | Text processing |
| [Math](math/index.md) | 2 | Mathematical operations |
| [Random](random/index.md) | 5 | Random value generation |
| [Datetime](datetime/index.md) | 7 | Date/time operations |

### File & Document

| Category | Nodes | Description |
|----------|-------|-------------|
| [File](file/index.md) | 18 | File I/O, CSV, JSON, Excel |
| [Pdf](pdf/index.md) | 6 | PDF operations |
| [Xml](xml/index.md) | 8 | XML processing |
| [Document](document/index.md) | 2 | Document handling |
| [Ftp](ftp/index.md) | 10 | FTP/SFTP operations |

### External Services

| Category | Nodes | Description |
|----------|-------|-------------|
| [Http](http/index.md) | 12 | HTTP/REST API requests |
| [Email](email/index.md) | 8 | SMTP/IMAP email |
| [Database](database/index.md) | 10 | SQL operations |
| [Google](google/index.md) | 116 | Google Workspace (Calendar, Docs, Gmail, Sheets, Drive) |
| [Messaging](messaging/index.md) | 18 | Telegram, WhatsApp |
| [Llm](llm/index.md) | 1 | LLM/AI integration (LiteLLM multi-provider) |

### Execution Control

| Category | Nodes | Description |
|----------|-------|-------------|
| [Error Handling](error-handling/index.md) | 37 | Try/Catch, Retry, Recovery |
| [Parallel](parallel/index.md) | 3 | Parallel execution |
| [Script](script/index.md) | 5 | Python/JavaScript execution |
| [System](system/index.md) | 13 | System commands, dialogs |
| [Utility](utility/index.md) | 4 | Utility functions |

## Node Decorators

All nodes use decorators for configuration:

```python
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType

@node_schema(
    PropertyDef("url", PropertyType.STRING, required=True),
    PropertyDef("timeout", PropertyType.INTEGER, default=30000),
)
@executable_node
class NavigateNode(BaseNode):
    ...
```

## Trigger Types

Available workflow triggers:

| Trigger | Description |
|---------|-------------|
| Manual | User-initiated execution |
| Scheduled | Cron-based scheduling |
| Webhook | HTTP webhook trigger |
| File Watch | File system events |
| Email | Incoming email trigger |
| Telegram | Telegram message trigger |
| WhatsApp | WhatsApp message trigger |
| Gmail | Gmail message trigger |
| Sheets | Google Sheets changes |
| Drive | Google Drive events |
| Calendar | Google Calendar events |

## Related Resources

- [API Reference](../api/index.md) - Architecture layers
- [User Guides](../guides/index.md) - Step-by-step tutorials
- [Data Types](../reference/data-types.md) - Port data types
