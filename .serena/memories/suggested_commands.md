# Suggested Commands - CasareRPA Development

## Windows Commands (Git Bash / PowerShell)

### Navigation
```bash
ls              # List directory
dir             # Alternative on Windows
cd <path>       # Change directory
pushd <path>    # Push directory (cd with bookmark)
popd            # Return to previous directory
```

### Git Operations
```bash
git status                  # Show working tree status
git branch                  # List branches
git checkout <branch>       # Switch branch
git worktree list           # List worktrees
git worktree add <path> -b <branch> main  # Create worktree
git worktree remove <path>  # Remove worktree
git log --oneline -10       # Recent commits
git diff                    # Show unstaged changes
git diff --staged           # Show staged changes
```

### Development Commands
```bash
# Install dependencies
pip install -e ".[dev]"

# Run application
python run.py
python manage.py canvas

# Tests
pytest tests/ -v
pytest tests/ -v -m "not slow"  # Skip slow tests
pytest tests/ --cov=src/casare_rpa --cov-report=html

# Linting and formatting
ruff check src/
black src/
mypy src/casare_rpa

# Playwright
playwright install

# Scripts
python scripts/create_worktree.py "feature-name"
python scripts/audit_node_modernization.py
```

### Finding Files/Patterns
```bash
# Find files (use Serena tools instead!)
find . -name "*.py"
rg --files -g "*.py"

# Search in files (use Serena tools instead!)
rg "class.*Node"
rg "def execute" src/
```

## Task Completion Checklist

After implementing any feature/fix:

1. **Run Tests**: `pytest tests/ -v`
2. **Lint**: `ruff check src/`
3. **Format**: `black src/`
4. **Type Check**: `mypy src/casare_rpa`
5. **Manual Test**: Run canvas `python run.py`
6. **Self Review**: Check for unused imports, proper error handling
7. **Update Docs** (if not small change): Update `_index.md`, `.brain/context/current.md`

## Small Change Exception
Skip docs update for <50 line changes:
- UI fixes (colors, layout)
- Typos
- Tiny refactor

Use commit prefix: `fix(ui):`, `chore(typo):`, `refactor(small):`
