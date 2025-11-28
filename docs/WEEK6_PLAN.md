# Week 6 Implementation Plan: Complete Node Test Coverage (60% → 100%)

## Objective

Increase node test coverage from 60% (145/242 nodes) to 100% (242/242 nodes) by adding ~241 new tests across 97 remaining nodes.

**Timeline**: 5 working days
**Target**: 1,676 → 1,917 total tests

---

## Day-by-Day Breakdown

### Day 1: Office Automation (42 tests)

**Focus**: Excel, Word, Outlook nodes (12 nodes)

**Test File**: `tests/nodes/desktop/test_office_nodes.py`

**Nodes**:
- Excel: OpenWorkbook, ReadCell, WriteCell, RunMacro (8 tests each)
- Word: OpenDocument, ReadText, WriteText, SaveDocument (5 tests each)
- Outlook: SendEmail, ReadInbox, GetAttachment (6 tests each)

**Mock Strategy**:
```python
# Mock win32com.client at module level
@pytest.fixture
def mock_win32com(monkeypatch):
    mock_excel = Mock()
    mock_word = Mock()
    mock_outlook = Mock()

    mock_dispatch = Mock(side_effect=lambda app: {
        'Excel.Application': mock_excel,
        'Word.Application': mock_word,
        'Outlook.Application': mock_outlook
    }[app])

    monkeypatch.setattr('win32com.client.Dispatch', mock_dispatch)
    return {'excel': mock_excel, 'word': mock_word, 'outlook': mock_outlook}
```

**Key Tests Per Node**:
- Success path with valid data
- Error handling (file not found, permission denied)
- COM object cleanup
- Path validation

**CI Consideration**: Mark Windows-only tests with `@pytest.mark.skipif(sys.platform != "win32")`

---

### Day 2: Desktop Advanced Features (58 tests)

**Focus**: Screenshot/OCR, Window operations, Wait/Verification (15 nodes)

**Test Files**:
- `tests/nodes/desktop/test_screenshot_ocr_nodes.py` (15 tests)
- `tests/nodes/desktop/test_window_nodes.py` (25 tests)
- `tests/nodes/desktop/test_wait_verification_nodes.py` (18 tests)

**Nodes**:
- Screenshot/OCR: CaptureScreen, CaptureWindow, OCRExtract, SaveScreenshot (4 nodes)
- Window: GetActiveWindow, SetWindowPosition, MinimizeWindow, MaximizeWindow, CloseWindow, ListWindows, FindWindow (7 nodes)
- Wait/Verify: WaitForElement, WaitForCondition, VerifyElement, VerifyText (4 nodes)

**Mock Strategy**:
```python
# Mock PIL/Pillow for screenshots
@pytest.fixture
def mock_screenshot(monkeypatch):
    mock_image = Mock()
    mock_image.save = Mock()
    monkeypatch.setattr('PIL.ImageGrab.grab', Mock(return_value=mock_image))
    return mock_image

# Mock OCR via desktop context
@pytest.fixture
def mock_ocr_context():
    context = MockDesktopContext()
    context.ocr_engine = Mock()
    context.ocr_engine.extract_text = Mock(return_value="Mocked OCR text")
    return context
```

**Key Tests**:
- Screenshot capture to file/memory
- OCR accuracy (mocked)
- Window operations with invalid handles
- Wait timeouts and success conditions

---

### Day 3: File System Operations (55 tests)

**Focus**: File read/write, CSV, JSON, ZIP (18 nodes, including untested ones)

**Test File**: `tests/nodes/test_file_nodes.py`

**Nodes**:
- Core: ReadFile, WriteFile, AppendFile, DeleteFile, CopyFile, MoveFile (6 nodes)
- Structured: ReadCSV, WriteCSV, ReadJSON, WriteJSON (4 nodes)
- Archives: CreateZIP, ExtractZIP, ListZIPContents (3 nodes)
- Directory: CreateDirectory, ListDirectory, DeleteDirectory (3 nodes)
- Others: GetFileInfo, WatchFile (2 nodes)

**Mock Strategy**:
```python
# Use pytest tmp_path for real file operations
@pytest.fixture
def sample_files(tmp_path):
    return {
        'text': tmp_path / "test.txt",
        'csv': tmp_path / "data.csv",
        'json': tmp_path / "config.json",
        'zip': tmp_path / "archive.zip"
    }

# Mock pathlib.Path for permission errors
def test_read_file_permission_error(monkeypatch):
    monkeypatch.setattr('pathlib.Path.read_text', Mock(side_effect=PermissionError))
```

**Key Tests Per Category**:
- Read/Write: encoding, large files, non-existent paths
- CSV: headers, delimiters, quoting
- JSON: nested objects, arrays, invalid JSON
- ZIP: compression levels, nested directories, password protection
- Directory: recursive operations, glob patterns

---

### Day 4: System + Script Nodes (61 tests)

**Focus**: System operations and script execution (18 nodes)

**Test Files**:
- `tests/nodes/test_system_nodes.py` (36 tests)
- `tests/nodes/test_script_nodes.py` (25 tests)

**System Nodes** (13 nodes):
- Clipboard: CopyToClipboard, PasteFromClipboard (4 tests each)
- Dialogs: ShowMessageBox, ShowInputDialog, ShowFileDialog (5 tests each)
- Process: StartProcess, KillProcess, ListProcesses (4 tests each)
- Services: StartService, StopService, CheckService (3 tests each)

**Script Nodes** (5 nodes):
- ExecutePython, ExecuteJavaScript, ExecutePowerShell, ExecuteBatch, ExecuteCommand

**Mock Strategy**:
```python
# Mock subprocess for all script execution
@pytest.fixture
def mock_subprocess(monkeypatch):
    mock_run = Mock(return_value=Mock(
        returncode=0,
        stdout="Success",
        stderr=""
    ))
    monkeypatch.setattr('subprocess.run', mock_run)
    return mock_run

# Mock pyperclip
@pytest.fixture
def mock_clipboard(monkeypatch):
    clipboard_data = []
    monkeypatch.setattr('pyperclip.copy', lambda x: clipboard_data.append(x))
    monkeypatch.setattr('pyperclip.paste', lambda: clipboard_data[-1] if clipboard_data else "")

# Mock Qt dialogs at import level
@pytest.fixture(autouse=True)
def mock_qt_dialogs(monkeypatch):
    monkeypatch.setattr('PySide6.QtWidgets.QMessageBox.information', Mock(return_value=QMessageBox.Ok))
    monkeypatch.setattr('PySide6.QtWidgets.QInputDialog.getText', Mock(return_value=("user input", True)))
```

**Key Tests**:
- Script execution: success, timeout, error codes, stderr
- Clipboard: copy/paste text, binary data
- Dialogs: user confirmation, cancellation
- Process: valid/invalid PIDs, permission errors
- Services: Windows service control (skip on non-Windows)

---

### Day 5: Basic + Variables + Gap Coverage (25 tests + Verification)

**Focus**: Remaining basic nodes, variable operations, and audit

**Test Files**:
- `tests/nodes/test_basic_nodes.py` (9 tests)
- `tests/nodes/test_variable_nodes.py` (16 tests)

**Basic Nodes** (3 nodes):
- StartNode, EndNode, CommentNode

**Variable Nodes** (3 nodes):
- SetVariable, GetVariable, IncrementVariable

**Key Activities**:
1. Test basic workflow structure nodes
2. Comprehensive variable scope testing
3. Run coverage audit: `pytest --cov=casare_rpa.nodes tests/nodes/ --cov-report=term-missing`
4. Identify and fill any remaining gaps
5. Verify all 242 nodes have at least 3 tests each

**Verification Checklist**:
- [ ] All 242 nodes have test files
- [ ] Coverage report shows 100% node coverage
- [ ] All tests pass on Windows
- [ ] CI tests pass (with appropriate skip markers)
- [ ] No regressions in existing tests
- [ ] Total test count: 1,917+

---

## Test File Structure

```
tests/
├── nodes/
│   ├── desktop/
│   │   ├── test_office_nodes.py              # Day 1 (42 tests)
│   │   ├── test_screenshot_ocr_nodes.py      # Day 2 (15 tests)
│   │   ├── test_window_nodes.py              # Day 2 (25 tests)
│   │   └── test_wait_verification_nodes.py   # Day 2 (18 tests)
│   ├── test_file_nodes.py                    # Day 3 (55 tests)
│   ├── test_system_nodes.py                  # Day 4 (36 tests)
│   ├── test_script_nodes.py                  # Day 4 (25 tests)
│   ├── test_basic_nodes.py                   # Day 5 (9 tests)
│   └── test_variable_nodes.py                # Day 5 (16 tests)
└── conftest.py                               # Shared fixtures
```

---

## Shared Fixtures (conftest.py additions)

```python
# Desktop context with OCR support
@pytest.fixture
def mock_desktop_context_with_ocr():
    context = MockDesktopContext()
    context.ocr_engine = Mock()
    context.ocr_engine.extract_text = Mock(return_value="Mocked OCR text")
    return context

# File system setup
@pytest.fixture
def file_system_setup(tmp_path):
    """Creates sample file structure for testing"""
    (tmp_path / "input").mkdir()
    (tmp_path / "output").mkdir()
    (tmp_path / "input" / "test.txt").write_text("Sample content")
    (tmp_path / "input" / "data.csv").write_text("col1,col2\nval1,val2")
    return tmp_path

# Win32com mock (Windows-only operations)
@pytest.fixture
def mock_win32com():
    """Mock entire win32com module"""
    if sys.platform != "win32":
        pytest.skip("Windows-only test")
    # ... (full mock implementation)
```

---

## Mock Strategies Summary

| Dependency | Approach | Reason |
|------------|----------|--------|
| **win32com** | Module-level mock + skip markers | Not available on CI |
| **subprocess** | Mock subprocess.run | Prevent actual execution |
| **Qt dialogs** | Patch at import with auto-close | Prevent UI blocking |
| **pyperclip** | In-memory clipboard simulation | CI compatibility |
| **PIL/Pillow** | Mock ImageGrab.grab | No display on CI |
| **File system** | pytest tmp_path (real files) | Accurate behavior |
| **OCR engines** | Mock via desktop context | No engines on CI |

---

## Critical Source Files to Review

Before starting, review these node implementation files:

1. `src/casare_rpa/nodes/desktop_nodes/office_nodes.py` (12 nodes)
2. `src/casare_rpa/nodes/desktop_nodes/screenshot_ocr_nodes.py` (4 nodes)
3. `src/casare_rpa/nodes/desktop_nodes/window_nodes.py` (7 nodes)
4. `src/casare_rpa/nodes/desktop_nodes/wait_verification_nodes.py` (4 nodes)
5. `src/casare_rpa/nodes/file_nodes.py` (18 nodes)
6. `src/casare_rpa/nodes/system_nodes.py` (13 nodes)
7. `src/casare_rpa/nodes/script_nodes.py` (5 nodes)
8. `src/casare_rpa/nodes/basic_nodes.py` (3 nodes)
9. `src/casare_rpa/nodes/variable_nodes.py` (3 nodes)

**Also review**:
- `tests/conftest.py` - Shared fixtures
- `tests/nodes/desktop/test_desktop_interaction_nodes.py` - Desktop test patterns
- `tests/nodes/test_http_nodes.py` - External dependency mock patterns

---

## Risk Mitigations

1. **win32com unavailable on CI**
   - Solution: Skip markers + manual Windows testing
   - `@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only")`

2. **Qt dialog blocking**
   - Solution: Patch at import level with auto-return
   - Use `monkeypatch` in `autouse` fixture

3. **File permission errors on CI**
   - Solution: Use tmp_path, skip privileged operations
   - Handle PermissionError gracefully in tests

4. **Subprocess security**
   - Solution: Mock all subprocess calls
   - Never execute user-provided code in tests

5. **Async timing issues**
   - Solution: Proper pytest-asyncio, avoid time-based assertions
   - Use event-based waits

---

## Implementation Commands

```powershell
# Day 1: Office
pytest tests/nodes/desktop/test_office_nodes.py -v

# Day 2: Desktop Advanced
pytest tests/nodes/desktop/test_screenshot_ocr_nodes.py tests/nodes/desktop/test_window_nodes.py tests/nodes/desktop/test_wait_verification_nodes.py -v

# Day 3: File System
pytest tests/nodes/test_file_nodes.py -v

# Day 4: System + Scripts
pytest tests/nodes/test_system_nodes.py tests/nodes/test_script_nodes.py -v

# Day 5: Verification
pytest tests/nodes/ -v --cov=casare_rpa.nodes --cov-report=term-missing

# Full suite
pytest tests/ -v
```

---

## Success Criteria

- [ ] 241+ new tests added
- [ ] All 242 nodes have test coverage
- [ ] Total test count: 1,917+
- [ ] All tests pass locally (Windows)
- [ ] CI tests pass (with appropriate skip markers)
- [ ] Coverage report shows 100% node coverage
- [ ] No breaking changes to existing tests
- [ ] Documentation updated in REFACTORING_ROADMAP.md

---

## Decisions Made

1. **Windows CI runner**: ✅ Available (GitHub Actions windows-latest)
2. **Skip strategy**: ✅ Use `@pytest.mark.skipif(sys.platform != "win32")`
3. **Coverage gate**: ✅ No blocking gate (informational only)
4. **Parallelization**: ✅ Add pytest-xdist for parallel execution
5. **File tests**: ✅ Real files via tmp_path (accurate behavior)

---

## Additional Setup Required

**Install pytest-xdist**:
```powershell
pip install pytest-xdist
```

**Parallel execution**:
```powershell
# Run tests with 4 workers
pytest tests/nodes/ -v -n 4

# Auto-detect CPU count
pytest tests/nodes/ -v -n auto
```

**Note**: Some tests may need `@pytest.mark.serial` for sequential execution (file locks, global state).

---

**Created**: 2025-11-28
**Status**: Ready for implementation
**Estimated Duration**: 5 working days
