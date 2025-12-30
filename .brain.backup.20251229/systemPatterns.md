# System Patterns - CasareRPA Quick Reference

Quick reference for core patterns. Details in `.brain/docs/patterns/` and `.claude/rules/`.

## DDD Layers

```
Presentation → Application → Domain ← Infrastructure
```

| Layer | Purpose | Dependencies |
|-------|---------|--------------|
| Domain | Pure business logic, entities, VOs | NONE |
| Application | Use cases, orchestration | Domain |
| Infrastructure | APIs, persistence, adapters | Domain interfaces |
| Presentation | UI, Canvas, Controllers | Application |
| Nodes | Executable automation | Domain |

## Node Pattern

```python
@properties(PropertyDef("url", PropertyType.STRING))
@node(category="browser")
class MyNode(BaseNode):
    def _define_ports(self):
        self.add_input_port("url", DataType.STRING)
        self.add_output_port("result", DataType.ANY)

    async def execute(self, context):
        url = self.get_parameter("url")  # port or config
        # ... logic ...
        return {"success": True}
```

## BrowserBaseNode Pattern

```python
from casare_rpa.nodes.browser.browser_base import BrowserBaseNode

@properties(BROWSER_TIMEOUT, BROWSER_RETRY_COUNT)
@node(category="browser")
class MyBrowserNode(BrowserBaseNode):
    async def execute(self, context):
        page = await self.get_page(context)
        selector = await self.get_normalized_selector(context)
        # ...
```

## Testing by Layer

| Layer | Mocks | Location |
|-------|-------|----------|
| Domain | NONE (real objects) | `tests/domain/` |
| Application | Infrastructure only | `tests/application/` |
| Infrastructure | External APIs (Playwright, win32) | `tests/infrastructure/` |
| Nodes | Category fixtures | `tests/nodes/{category}/` |

## Agent Chain

```
PLAN → IMPLEMENT → TEST → REVIEW → (loop if issues) → APPROVE
```

| Phase | Agent |
|-------|-------|
| Explore | `Explore` (read-only) |
| Plan/Implement | `rpa-engine-architect` |
| Test | `chaos-qa-engineer` |
| Review (MANDATORY) | `code-security-auditor` |
| Docs | `rpa-docs-writer` |

## Event Bus

```python
from casare_rpa.domain.events import get_event_bus, NodeCompleted

bus = get_event_bus()
bus.subscribe(NodeCompleted, handler)
bus.publish(NodeCompleted(node_id="x", ...))
```

## Key Files

| Purpose | File |
|---------|------|
| Node dev | `.claude/rules/03-nodes.md` |
| Architecture | `.claude/rules/02-architecture.md` |
| Theme | `.claude/rules/ui/theme-rules.md` |
| Popups | `.claude/rules/ui/popup-rules.md` |
| Events | `.claude/rules/12-ddd-events.md` |
| Node templates | `.brain/archive/docs/` (archived) |

---

*Last updated: 2025-12-27*
