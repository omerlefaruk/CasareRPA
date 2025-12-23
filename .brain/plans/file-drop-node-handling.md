# Plan: File Drop Node Handling

## Goal
- Restore drag/drop handling for file drops.
- Map .xlsx/.xls to Excel Open and other file types to File System (Read File).
- Add unit coverage for drop mapping and mime handling.

## Scope
- Update CasareNodeGraph drop handling and file-type mapping.
- Add presentation-layer tests for drop handling.
- Keep NodeGraphQt session import behavior intact.

## Steps
1. Tests first: add coverage for QMimeData with .xls/.xlsx and non-Excel file types.
2. Implement: parse QMimeData safely, map extensions, set FileSystemSuperNode action, and preserve fallback behaviors.
3. QA: run targeted pytest for new tests.
4. Docs: update .brain/context and note test results.
5. Fix warning from expand_clicked disconnect during canvas tests.
6. QA: rerun canvas tests to confirm warnings resolved.
7. Address review items (session import fallback, undo stack noise).
8. QA: rerun drop tests after review fixes.
9. Add size guard for session drop parsing.

## Status
- Step 1: completed
- Step 2: completed
- Step 3: completed
- Step 4: completed
- Step 5: completed
- Step 6: completed
- Step 7: completed
- Step 8: completed
- Step 9: completed
