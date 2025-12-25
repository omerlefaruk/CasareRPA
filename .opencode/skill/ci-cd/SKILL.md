---
name: ci-cd
description: GitHub Actions workflows, quality gates, and release automation
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: devops
---

## What I do

- Create CI/CD pipelines with GitHub Actions
- Define quality gates (lint, type check, tests, coverage)
- Build release workflows with automated versioning
- Configure multi-version testing matrices

## When to use me

Use this when you need to:
- Create a new CI/CD pipeline
- Add quality gates to existing workflows
- Set up automated releases
- Configure testing across Python versions

## MCP-First Workflow

Always use MCP servers in this order:

1. **codebase** - Search for workflow patterns
   ```python
   search_codebase("GitHub Actions workflow CI/CD patterns", top_k=10)
   ```

2. **filesystem** - view_file existing workflows
   ```python
   read_file(".github/workflows/ci.yml")
   ```

3. **git** - Check workflow history
   ```python
   git_log("--oneline", path=".github/workflows/")
   ```

4. **exa** - Research best practices
   ```python
   web_search("GitHub Actions best practices 2025", num_results=5)
   ```

## Quality Gates

| Check | Tool | Fail Threshold |
|:------|:-----|:---------------|
| Linting | ruff | Any error |
| Type checking | mypy | Any error |
| Tests | pytest | Any failure |
| Coverage | pytest-cov | < 80% |

## Example Usage

```yaml
# Create CI workflow
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: ruff check src/
      - run: mypy src/casare_rpa
      - run: pytest tests/ -v --cov=casare_rpa
```
