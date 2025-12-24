#!/usr/bin/env python
"""Get ruff statistics and output them line by line."""
import subprocess
import time

result = subprocess.run(['ruff', 'check', 'src/', '--statistics'], capture_output=True, text=True)
lines = result.stdout.strip().split('\n')

print("=" * 60)
print("RUFF CHECK STATISTICS")
print("=" * 60)

for line in lines:
    print(line)
    time.sleep(0.01)  # Small delay to prevent output buffering issues

print("=" * 60)
print(result.stderr)
