---
name: refactor
description: Safe code refactoring with DDD patterns and test preservation
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: refactoring
---

## What I do

- Safely refactor code without changing behavior
- Extract methods, classes, and interfaces
- Apply DDD patterns and clean code principles
- Preserve existing tests and functionality

## When to use me

Use this when you need to:
- Refactor legacy code
- Extract duplicated logic
- Apply design patterns
- Improve code organization

## MCP-First Workflow

Always use MCP servers in this order:

1. **codebase** - Search for refactoring patterns
   ```python
   search_codebase("refactoring patterns Python DDD clean code", top_k=10)
   ```

2. **filesystem** - view_file the code to refactor
   ```python
   read_file("src/module.py")
   ```

3. **git** - Check usages and history
   ```python
   git_diff("HEAD~10..HEAD", path="src/")
   ```

4. **exa** - Research best practices
   ```python
   web_search("Python refactoring patterns 2025", num_results=5)
   ```

## Safe Refactoring Principles

### Extract Method
```python
# BEFORE
def process_order(order):
    # 50 lines of code
    return order

# AFTER
def process_order(order):
    self._validate(order)
    self._calculate(order)
    return order
```

### Replace Conditional with Polymorphism
```python
# BEFORE
def calculate_shipping(weight, type):
    if type == "standard":
        return weight * 0.5
    elif type == "express":
        return weight * 1.5

# AFTER
class ShippingStrategy:
    def calculate(self, weight): ...

class StandardShipping(ShippingStrategy):
    def calculate(self, weight):
        return weight * 0.5
```

## Pre-Refactoring Checklist

- [ ] Tests exist and pass
- [ ] All usages identified
- [ ] Breaking changes evaluated
- [ ] Rollback plan ready

## Post-Refactoring Checklist

- [ ] All tests pass
- [ ] Type hints intact
- [ ] Docstrings updated
- [ ] No new lint errors
