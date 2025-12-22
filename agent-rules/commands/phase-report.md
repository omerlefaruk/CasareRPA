---
description: Generate a phase/progress report and append it to .brain/context/current.md
---
# Phase Report

Use this when you need to report current phase/progress and keep context in sync.

## Command
```bash
python scripts/phase_report.py --phase Plan --in-progress "searching rules" --completed "scanned indexes" --next "draft plan"
```

## Output
- Prints a short phase block for response use.
- Appends the same block to `.brain/context/current.md`.
