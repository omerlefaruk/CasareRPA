# CI/CD Skill

GitHub Actions workflows, quality gates, and release automation.

## MCP-First Workflow

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

## CI Workflow Template

```yaml
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

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run linting
        run: ruff check src/

      - name: Run type checking
        run: mypy src/casare_rpa

      - name: Run tests
        run: pytest tests/ -v --cov=casare_rpa --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

## Quality Gates

| Check | Tool | Fail Threshold |
|:------|:-----|:---------------|
| Linting | ruff | Any error |
| Type checking | mypy | Any error |
| Tests | pytest | Any failure |
| Coverage | pytest-cov | < 80% |

## Release Workflow

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build package
        run: python -m build

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/*
          generate_release_notes: true
```

## Example Usage

```python
Skill(skill="ci-cd", prompt="""
Create a GitHub Actions workflow for PR validation:

MCP Workflow:
1. codebase: Search for "GitHub Actions workflow testing patterns"
2. filesystem: Read .github/workflows/ci.yml
3. git: Check workflow history and changes
4. exa: Research GitHub Actions best practices 2025

Requirements:
- Multi-version Python testing
- Linting with ruff
- Type checking with mypy
- Coverage reporting
- Quality gates enforcement
""")
```
