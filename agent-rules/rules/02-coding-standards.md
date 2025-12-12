# Coding Standards

## Python Style
- **Python 3.12+** features allowed
- **Type hints** on all functions and methods
- **Docstrings** on all public APIs
- **Async/await** for all I/O operations
- **100 char** line length (Black formatter)

## Imports
```python
# Standard library
import asyncio
from typing import Any, Dict, Optional

# Third party
from loguru import logger
from pydantic import BaseModel

# Local - use absolute imports
from casare_rpa.domain.entities import BaseNode
from casare_rpa.infrastructure.browser import PlaywrightManager
```

## Naming
- `snake_case` - functions, variables, modules
- `PascalCase` - classes
- `UPPER_SNAKE` - constants
- `_prefix` - private/internal

## Error Handling
- Use custom exceptions from `domain/errors/`
- Always log errors with context
- Return result objects, don't raise for control flow
