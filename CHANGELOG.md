# Changelog

All notable changes to CasareRPA will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive chaos testing suite for browser, workflow runner, circuit breaker, and offline queue
- Enhanced test fixtures for simulating network failures, browser crashes, and selector failures
- Dynamic node type validation (VALID_NODE_TYPES now loads from NODE_TYPE_MAP)

### Fixed
- MessageBoxNode now properly displays message text from text widget
- UNKNOWN_NODE_TYPE error for MessageBoxNode and LogErrorNode resolved

## [0.1.0] - 2025-11-25

### Added

#### Core Platform
- Visual node-based workflow editor (Canvas) built with PySide6 and NodeGraphQt
- Headless workflow executor (Robot) with system tray integration
- Workflow management and scheduling UI (Orchestrator)
- 200+ automation node types across multiple categories

#### Browser Automation
- LaunchBrowserNode - Launch Chromium/Firefox/WebKit browsers via Playwright
- CloseBrowserNode - Clean browser shutdown
- GoToURLNode, GoBackNode, GoForwardNode, RefreshPageNode - Navigation
- ClickElementNode, TypeTextNode, FillInputNode - Element interaction
- WaitForElementNode, WaitForNavigationNode - Synchronization
- GetElementTextNode, GetElementAttributeNode - Data extraction
- TakeScreenshotNode, SavePageAsPDFNode - Capture operations
- SwitchTabNode, NewTabNode, CloseTabNode - Tab management
- ExecuteJavaScriptNode - Custom script execution
- Full selector support (CSS, XPath, text-based)

#### Desktop Automation
- Desktop Recorder with automatic workflow generation
- ClickWindowElementNode, TypeInWindowNode - Windows UI interaction
- GetWindowTextNode, SetWindowTextNode - Text operations
- FindWindowNode, FocusWindowNode, CloseWindowNode - Window management
- SendHotkeyNode, WaitForWindowNode - Advanced operations
- UIAutomation integration for accessibility tree access

#### Office Automation (Bite 11)
- ExcelReadNode, ExcelWriteNode, ExcelRangeNode - Spreadsheet operations
- WordReadNode, WordWriteNode, WordFindReplaceNode - Document operations
- OutlookSendEmailNode, OutlookReadEmailNode - Email automation

#### Control Flow
- IfNode, SwitchNode - Conditional branching
- ForLoopNode, WhileLoopNode, ForEachNode - Iteration
- BreakNode, ContinueNode - Loop control
- TryCatchNode, ThrowErrorNode - Error handling
- RetryNode with configurable attempts and delays
- ParallelNode for concurrent execution

#### Data Operations
- SetVariableNode, GetVariableNode - Variable management
- StringOperationNode (concat, split, replace, etc.)
- MathOperationNode (arithmetic, rounding, etc.)
- ListOperationNode (append, filter, sort, etc.)
- DictOperationNode (get, set, merge, etc.)
- JSONParseNode, JSONStringifyNode - JSON handling
- RegexMatchNode, RegexReplaceNode - Pattern matching

#### File Operations
- ReadFileNode, WriteFileNode, AppendFileNode
- DeleteFileNode, CopyFileNode, MoveFileNode
- FileExistsNode, GetFileInfoNode
- ListDirectoryNode, CreateDirectoryNode
- CSVReadNode, CSVWriteNode - CSV handling
- JSONReadNode, JSONWriteNode - JSON files

#### Network Operations
- HTTPRequestNode with all methods (GET, POST, PUT, DELETE, etc.)
- DownloadFileNode for file downloads
- Response parsing and error handling

#### System Operations
- LogNode with multiple log levels
- MessageBoxNode for user prompts
- RunCommandNode, RunPowerShellNode - Script execution
- DelayNode, CommentNode - Utility nodes
- EmailNode - SMTP email sending

#### Robot Hardening (Phase 8B)
- Circuit breaker pattern for API resilience
- Offline job queue with SQLite caching
- Checkpoint-based crash recovery
- Execution audit logging
- Watchdog process monitoring

#### Canvas Features
- Drag-and-drop node placement
- Visual connection system
- Properties panel for node configuration
- Node search dialog with fuzzy matching
- Variable inspector
- Execution history viewer
- Debug toolbar with step-through execution
- Minimap for large workflows
- Viewport culling for performance optimization
- Dark theme support

#### Orchestrator Features
- Workflow scheduling (one-time, recurring with cron)
- Multi-Robot management
- Execution monitoring and logging
- Real-time status updates via WebSocket
- Performance dashboard

#### Testing Infrastructure
- 600+ unit and integration tests
- pytest-qt for GUI testing
- Mock browser and page fixtures
- Chaos testing framework

### Technical Stack
- Python 3.12+ with strict type hints
- PySide6 for GUI framework
- NodeGraphQt for node graph editing
- Playwright for browser automation
- uiautomation for Windows desktop automation
- qasync for Qt + asyncio integration
- orjson for fast JSON serialization
- loguru for structured logging
- SQLite for local data persistence
- HashiCorp Vault integration for secure credentials

## Development Phases Completed

- Phase 1-7: Core platform implementation
- Phase 8A: Extended functionality (recorder, office automation)
- Phase 8B: Robot hardening (resilience, offline support)
- Security Hardening Sprint: Command injection fixes, credential security
- Architecture Fixes: NODE_TYPE_MAP completion, validation improvements
- Testing Expansion: Chaos tests, comprehensive fixtures

---

## Versioning Guidelines

- **Major (X.0.0)**: Breaking changes to workflow JSON format or API
- **Minor (0.X.0)**: New node types, features, or significant enhancements
- **Patch (0.0.X)**: Bug fixes, performance improvements, documentation
