---
description: Tool usage guidelines
---

# Tool Usage

## File Operations
- Use `view_file` for reading.
- Use `replace_file_content` for surgical edits.
- Use `write_to_file` for new files.

## Command Execution
- Always check `SafeToAutoRun`.
- Use `run_command` for shell operations.

## Search
- Use `grep_search` for exact matches.
- Use `find_by_name` for file discovery.
