#!/usr/bin/env python
"""Find files with syntax errors."""
import subprocess
import json

result = subprocess.run(
    ['ruff', 'check', 'src/', '--output-format=json'],
    capture_output=True,
    text=True,
)
violations = json.loads(result.stdout) if result.stdout else []
syntax_errors = [x for x in violations if x.get('code') is None]

print(f"Found {len(syntax_errors)} syntax errors:")
for err in syntax_errors:
    row = err.get('location', {}).get('row', '?')
    print(f"  {err['filename']}:{row}")
    print(f"    {err.get('message', 'unknown')}")
