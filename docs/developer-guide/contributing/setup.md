# Development Environment Setup

This guide walks you through setting up a complete CasareRPA development environment.

## Prerequisites

Before starting, ensure you have the following installed:

| Requirement | Version | Verification |
|------------|---------|--------------|
| Python | 3.12+ | `python --version` |
| Git | 2.30+ | `git --version` |
| Node.js | 18+ (optional, for docs) | `node --version` |

> **Note:** CasareRPA is Windows-only due to UIAutomation and pywin32 dependencies.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/omerlefaruk/CasareRPA.git
cd CasareRPA

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# Install in development mode
pip install -e ".[dev]"

# Install Playwright browsers
playwright install chromium

# Verify installation
python run.py --help
pytest tests/ -v -m "not slow" --maxfail=3
```

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone https://github.com/omerlefaruk/CasareRPA.git
cd CasareRPA
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (PowerShell)
.venv\Scripts\Activate.ps1
```

> **Important:** Always work within the virtual environment. Your terminal prompt should show `(.venv)`.

### 3. Install Dependencies

```bash
# Development install with all dev dependencies
pip install -e ".[dev]"

# Optional: Install cloud provider SDKs
pip install -e ".[dev,azure,aws]"  # Azure Key Vault + AWS Secrets Manager
```

The `[dev]` extra includes:
- pytest, pytest-asyncio, pytest-qt, pytest-cov
- black, mypy, ruff (linting/formatting)
- pip-audit (security scanning)

### 4. Install Playwright Browsers

```bash
# Install Chromium (required for browser automation)
playwright install chromium

# Optional: Install all browsers
playwright install
```

### 5. Install Pre-commit Hooks

```bash
# Install hooks to run on every commit
pre-commit install

# Run hooks manually on all files
pre-commit run --all-files
```

Pre-commit hooks automatically:
- Trim trailing whitespace
- Fix end-of-file issues
- Check YAML/JSON syntax
- Run Ruff linter and formatter
- Detect debug statements

### 6. Verify Installation

```bash
# Run the application
python run.py

# Run quick tests
pytest tests/ -v -m "not slow" --maxfail=3

# Run full test suite
pytest tests/ -v
```

## Environment Variables

Create a `.env` file in the project root for local configuration:

```bash
# .env (never commit this file)

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=logs/casare.log

# Database (optional - for Orchestrator)
DATABASE_URL=postgresql://user:pass@localhost:5432/casare

# AI Assistant (optional)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Vault Providers (optional)
AZURE_TENANT_ID=...
AZURE_CLIENT_ID=...
AZURE_CLIENT_SECRET=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

> **Warning:** Never commit `.env` files. The `.gitignore` already excludes them.

## IDE Setup

### VS Code (Recommended)

Install these extensions:
- **Python** (ms-python.python)
- **Pylance** (ms-python.vscode-pylance)
- **Ruff** (charliermarsh.ruff)
- **Python Test Explorer** (littlefoxteam.vscode-python-test-adapter)

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
    "python.analysis.typeCheckingMode": "basic",
    "python.analysis.autoImportCompletions": true,
    "[python]": {
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.codeActionsOnSave": {
            "source.fixAll.ruff": "explicit",
            "source.organizeImports.ruff": "explicit"
        }
    },
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/", "-v"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/.pytest_cache": true,
        "**/*.pyc": true
    }
}
```

Create `.vscode/launch.json` for debugging:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Run CasareRPA",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/run.py",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "Debug Current Test",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "args": ["${file}", "-v", "-s"],
            "console": "integratedTerminal"
        }
    ]
}
```

### PyCharm

1. Open the project folder
2. Set interpreter to `.venv\Scripts\python.exe`
3. Enable pytest as test runner: Settings > Tools > Python Integrated Tools > Default test runner: pytest
4. Configure Ruff: Settings > Editor > Inspections > Enable Ruff

Recommended settings:
- Editor > Code Style > Python: Line length = 100
- Editor > General > Auto Import: Enable auto-import

## Project Structure

```
CasareRPA/
├── src/casare_rpa/           # Main source code
│   ├── domain/               # Pure business logic (no deps)
│   ├── application/          # Use cases, orchestration
│   ├── infrastructure/       # Adapters, persistence, HTTP
│   ├── presentation/         # Qt UI (Canvas)
│   └── nodes/                # Node implementations
├── tests/                    # Test suite
│   ├── domain/               # Domain layer tests
│   ├── application/          # Use case tests
│   ├── infrastructure/       # Adapter tests
│   ├── nodes/                # Node tests by category
│   └── e2e/                  # End-to-end tests
├── docs/                     # Documentation
├── .brain/                   # AI context files
└── scripts/                  # Development scripts
```

## Common Commands

| Task | Command |
|------|---------|
| Run application | `python run.py` |
| Run tests | `pytest tests/ -v` |
| Run fast tests | `pytest tests/ -v -m "not slow"` |
| Run with coverage | `pytest tests/ -v --cov=casare_rpa --cov-report=html` |
| Format code | `ruff format src/ tests/` |
| Lint code | `ruff check src/ tests/ --fix` |
| Type check | `mypy src/` |
| Security audit | `pip-audit` |
| Re-index for semantic search | `python scripts/index_codebase_qdrant.py` |

## Troubleshooting

### Import Errors

```bash
# Ensure you're in the virtual environment
.venv\Scripts\activate

# Reinstall in editable mode
pip install -e ".[dev]"
```

### Qt/PySide6 Issues

```bash
# If Qt fails to start, set platform plugin
set QT_QPA_PLATFORM=windows

# For headless environments
set QT_QPA_PLATFORM=offscreen
```

### Playwright Browser Issues

```bash
# Reinstall browsers
playwright install --force chromium

# Check browser installation
playwright show-browsers
```

### Test Failures

```bash
# Run with verbose output
pytest tests/ -vv -s

# Stop on first failure
pytest tests/ -x

# Debug with pdb
pytest tests/ --pdb
```

## Next Steps

- Read [Coding Standards](coding-standards.md) for style guidelines
- Review [Testing Guide](testing.md) for TDD practices
- Check [Pull Request Guidelines](pull-requests.md) before contributing

---

**Questions?** Open an issue on GitHub or check the existing documentation in `.brain/projectRules.md`.
