# CasareRPA Agent Guide

## Quick Commands
```bash
pytest tests/ -v && ruff check src/ && black src/ tests/
python run.py && python manage.py canvas
```

## Core Rules

| Rule | Description |
|------|-------------|
| index-first | Read _index.md before grep/glob |
| parallel | Launch independent reads in parallel |
| no-silent-failures | Wrap external calls in try/except |
| async-first | No blocking I/O in async |
| theme-only | No hardcoded colors |

## Node Standard

```python
@properties(PropertyDef("url", PropertyType.STRING))
@node(category="browser")
class MyNode(BaseNode):
    def _define_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_input_port("url", DataType.STRING)
```

## Key Indexes
- `src/casare_rpa/nodes/_index.md`
- `src/casare_rpa/domain/_index.md`
- `.brain/_index.md`
