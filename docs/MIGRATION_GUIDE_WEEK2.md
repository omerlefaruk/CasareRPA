# Week 2 Migration Guide - Domain Layer Refactoring

## Overview

Week 2 introduces a Domain Layer following DDD principles with zero breaking changes.

## What Changed

### New Domain Layer
- domain/value_objects/types.py - Type definitions
- domain/value_objects/port.py - Port value object

### Moved Components

| Old | New |
|-----|-----|
| casare_rpa.core.types | casare_rpa.domain.value_objects.types |
| casare_rpa.core.base_node.Port | casare_rpa.domain.value_objects.Port |

## Import Changes

### OLD (deprecated):
```python
from casare_rpa.core.types import DataType, NodeId
from casare_rpa.core import Port
```

### NEW (recommended):
```python
from casare_rpa.domain.value_objects.types import DataType, NodeId
from casare_rpa.domain.value_objects import Port
```

## Testing

```bash
# Suppress warnings
pytest -v -W ignore::DeprecationWarning

# See warnings
pytest -v
```

## Timeline

- v2.1: Compatibility layer active
- v3.0: Compatibility layer removed

---
Last Updated: 2025-11-27
