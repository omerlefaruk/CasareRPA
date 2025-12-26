# Refactor Control Flow Visual Nodes

## Summary
Update control flow visual nodes to follow coding standards and add missing imports.

## Target Files
- `src/casare_rpa/presentation/canvas/visual_nodes/control_flow/nodes.py`
- Already exports properly in `__init__.py`

## Issues to Fix
1. **Missing imports**: Add `loguru` for logging
2. **Port methods**: Replace `add_typed_input`/`add_typed_output` with `add_input_port`/`add_output_port`
3. **Type hints**: Add missing type hints
4. **String literals**: Replace hardcoded values

## Implementation Steps
1. Add required imports (loguru, typing) ✓
2. Update port methods to use correct signatures ✓
3. Add type hints to method parameters ✓
4. Replace hardcoded strings with constants where applicable ✓

## Risk Assessment
- **Low risk**: Visual nodes are UI-only, no business logic changes
- **Testing needed**: Verify nodes still appear in canvas and connect properly ✓

## Success Criteria
- All imports added ✓
- Port method signatures match standard patterns ✓
- Type hints complete ✓
- No functional changes to behavior ✓

## Completed Changes
1. **Added imports**:
   - Added `from typing import TYPE_CHECKING`
   - Added `from loguru import logger`
   - Added `from PySide6.QtCore import QPoint` (TYPE_CHECKING)

2. **Added logging statements**: Added debug logging for composite node creation and node pairing

3. **Corrected port methods**:
   - Reverted incorrect port method changes (visual nodes use `add_typed_input`/`add_typed_output`)
   - Port methods already followed correct pattern in other visual nodes