# Code Review: Pre-Commit Hooks - Improvements Applied

## Summary
Applied comprehensive code review improvements to all 10 custom pre-commit hooks. Fixes addressed robustness, cross-platform compatibility, false positives, and edge cases.

## Files Modified
- `scripts/check_node_registry_sync.py`
- `scripts/check_domain_purity.py`
- `scripts/check_event_serialization.py` (rewritten)
- `scripts/check_theme_colors.py`
- `scripts/check_blocking_io.py`
- `scripts/check_signal_slot_usage.py`
- `scripts/check_http_client_usage.py`
- `scripts/check_node_port_definitions.py`
- `scripts/check_secrets.py`
- `scripts/check_logger_usage.py`

## Key Improvements Applied

### 1. **Encoding Consistency**
- Added explicit `encoding="utf-8"` to all `open()` calls
- Prevents Windows console encoding errors

### 2. **Cross-Platform Path Handling**
- Added `filepath.replace("\\", "/")` normalization in 4 scripts
- Ensures consistent path matching on Windows (backslashes) vs Unix (forward slashes)
- Applied to:
  - `check_http_client_usage.py` (infrastructure/http detection)
  - `check_node_port_definitions.py` (nodes/ detection)
  - `check_logger_usage.py` (infrastructure/nodes detection)

### 3. **Improved Regex and Pattern Matching**

#### check_node_registry_sync.py
- Changed registry pattern from `r'"(\w+)"\s*:\s*'` to `r'"(\w+Node)"\s*:\s*'`
- Removes false positives from non-node entries
- Removed unused `visual_prefix` variable

#### check_domain_purity.py
- Better logic: check for "from/import" statements first, then forbidden imports
- Prevents matching in comments and docstrings
- Added early break to avoid duplicate errors per line

#### check_theme_colors.py
- Removed overly aggressive import line skipping
- Better distinction between THEME assignments and color usage
- Fixed path separator detection (removed hardcoded forward slash)

#### check_signal_slot_usage.py
- Simplified lambda detection with line-by-line parsing
- Added comment skipping
- Support for `@AsyncSlot` decorator variant

#### check_http_client_usage.py
- Path normalization for Windows compatibility
- Proper comment detection in import lines

### 4. **Enhanced AST Analysis**

#### check_event_serialization.py (Complete Rewrite)
- Now handles generic types: `Optional[Page]`, `List[Driver]`, `Dict[str, Page]`
- Recursive type extraction via `_extract_forbidden_types()` method
- Checks `ast.Subscript` (generics), `ast.Tuple`, and nested structures
- More accurate error messages with all forbidden types listed

#### check_node_port_definitions.py
- Added validation that 2nd argument to `add_input_port()`/`add_output_port()` is a reference, not string literal
- Detects mistakes like `add_input_port("name", "STRING")` (should be `DataType.STRING`)

### 5. **Reduced False Positives**

#### check_blocking_io.py
- Removed overly broad blocking call list: `wait()`, `join()`, `read()`, `write()`
- These are common in non-I/O contexts (threading, custom methods)
- Kept strict list: `sleep`, `open`

#### check_logger_usage.py
- Removed fragile `"logger" not in line` check
- Now properly skips comments
- Simpler, more reliable regex: `r'\bprint\s*\('`

#### check_secrets.py
- Skip `.example` files (safe for documentation)
- Only check `.py` files (avoids false positives in JSON, YAML)
- Better test/doc pattern filtering

### 6. **Comment Handling**
- All scripts now consistently skip `line.strip().startswith("#")` checks
- Prevents false positives in commented-out code and documentation

## Test Results

All hooks ran successfully with the improvements:

✓ **check_node_registry_sync** - Reports unregistered nodes (expected behavior)
✓ **check_domain_purity** - Detects 4 domain purity violations (found real issues!)
✓ **check_event_serialization** - No violations (generic type handling works)
✓ **check_theme_colors** - Found 548+ hardcoded colors (good coverage)
✓ **check_http_client_usage** - Found 40+ raw aiohttp imports (Windows path handling works)
✓ **check_signal_slot_usage** - No violations
✓ **check_blocking_io** - No violations
✓ **check_logger_usage** - No violations
✓ **check_node_port_definitions** - No violations
✓ **check_secrets** - No violations

## Breaking Changes
None. All improvements are backward compatible with the hook interface.

## Performance Impact
Negligible. Minimal additional AST parsing or regex operations.

## Recommendations
1. Address domain purity violations in:
   - `domain/port_type_system.py` (imports application)
   - `domain/services/headless_validator.py` (imports presentation)
   - `domain/services/workflow_validator.py` (imports presentation)

2. Consider updating hooks to auto-fix or provide detailed remediation guidance

3. Monitor color violations (548+ in presentation layer) - plan theme refactor
