# Tool Usage

## File Operations
- Use `view_file` before editing to understand context
- Use `view_file_outline` for large files
- Use `find_by_name` to locate files
- Use `grep_search` to find patterns

## Code Editing
- Use `replace_file_content` for single contiguous edits
- Use `multi_replace_file_content` for non-adjacent changes
- Use `write_to_file` for new files only
- Always specify `TargetFile` first

## Commands
```bash
# Run tests
pytest tests/ -v

# Run app
python run.py

# Type check
mypy src/

# Format
black src/ tests/

# Lint
ruff check src/
```

## Best Practices
1. Read before write
2. Make minimal, focused edits
3. Verify with tests after changes
4. Don't guess - use search tools
