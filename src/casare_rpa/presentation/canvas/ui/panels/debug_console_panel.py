"""
Debug Console Panel for CasareRPA.

Provides a terminal-like REPL interface for expression evaluation during debugging.
Features:
- Python expression evaluation
- Command history with arrow key navigation
- Variable auto-complete
- Built-in commands (vars, watch, clear, help)
- Pretty-printed output with syntax highlighting
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QKeyEvent, QTextCharFormat
from PySide6.QtWidgets import (
    QCompleter,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Epic 6.1: Migrated to v2 design system
from casare_rpa.presentation.canvas.theme_system import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.theme_system.helpers import (
    set_fixed_width,
    set_margins,
    set_spacing,
)

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.debugger.debug_controller import (
        DebugController,
    )


class HistoryLineEdit(QLineEdit):
    """
    QLineEdit with command history support.

    Handles Up/Down arrow keys to navigate through command history.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the history-enabled line edit."""
        super().__init__(parent)
        self._history: list[str] = []
        self._history_index: int = -1
        self._current_input: str = ""

    def add_to_history(self, command: str) -> None:
        """
        Add command to history.

        Args:
            command: Command string to add
        """
        if command and (not self._history or self._history[-1] != command):
            self._history.append(command)
        self._history_index = len(self._history)
        self._current_input = ""

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events for history navigation."""
        if event.key() == Qt.Key.Key_Up:
            self._navigate_history(-1)
            event.accept()
        elif event.key() == Qt.Key.Key_Down:
            self._navigate_history(1)
            event.accept()
        else:
            super().keyPressEvent(event)

    def _navigate_history(self, direction: int) -> None:
        """
        Navigate through command history.

        Args:
            direction: -1 for older, 1 for newer
        """
        if not self._history:
            return

        # Save current input if at the end
        if self._history_index == len(self._history):
            self._current_input = self.text()

        new_index = self._history_index + direction

        if new_index < 0:
            new_index = 0
        elif new_index > len(self._history):
            new_index = len(self._history)

        self._history_index = new_index

        if new_index == len(self._history):
            self.setText(self._current_input)
        else:
            self.setText(self._history[new_index])


class DebugConsolePanel(QWidget):
    """
    Debug console panel with REPL functionality.

    Provides an interactive Python REPL for evaluating expressions
    during workflow debugging. Integrates with DebugController for
    variable context access.

    Signals:
        expression_evaluated: Emitted when expression is evaluated (expr, result)
        watch_added: Emitted when watch expression is requested (expr)
        watch_removed: Emitted when watch removal is requested (expr)
    """

    expression_evaluated = Signal(str, object)
    watch_added = Signal(str)
    watch_removed = Signal(str)

    # Built-in commands
    BUILTIN_COMMANDS = {
        "vars": "List all variables in current context",
        "watch": "Add watch expression: watch <expr>",
        "unwatch": "Remove watch expression: unwatch <expr>",
        "clear": "Clear console output",
        "help": "Show available commands",
        "history": "Show command history",
    }

    def __init__(
        self,
        parent: QWidget | None = None,
        debug_controller: Optional["DebugController"] = None,
    ) -> None:
        """
        Initialize the debug console panel.

        Args:
            parent: Optional parent widget
            debug_controller: Optional debug controller for integration
        """
        super().__init__(parent)
        self._debug_controller = debug_controller
        self._completer: QCompleter | None = None

        self._setup_ui()
        self._apply_styles()
        self._print_welcome()

        logger.debug("DebugConsolePanel initialized")

    def set_debug_controller(self, controller: "DebugController") -> None:
        """
        Set the debug controller for expression evaluation.

        Args:
            controller: Debug controller instance
        """
        self._debug_controller = controller
        self._update_completer()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        set_margins(layout, (4, 4, 4, 4))
        set_spacing(layout, 4)

        # Output area
        self._output = QPlainTextEdit()
        self._output.setReadOnly(True)
        self._output.setFont(QFont("Consolas", 10))
        self._output.setMaximumBlockCount(5000)  # Limit scrollback
        layout.addWidget(self._output)

        # Input area
        input_layout = QHBoxLayout()
        set_spacing(input_layout, 4)

        # Prompt label
        self._prompt_label = QLabel(">>>")
        self._prompt_label.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        input_layout.addWidget(self._prompt_label)

        # Input line with history support
        self._input = HistoryLineEdit()
        self._input.setFont(QFont("Consolas", 10))
        self._input.setPlaceholderText("Enter expression or command...")
        self._input.returnPressed.connect(self._on_execute)
        input_layout.addWidget(self._input)

        # Execute button
        self._btn_execute = QPushButton("Run")
        set_fixed_width(self._btn_execute, 50)
        self._btn_execute.clicked.connect(self._on_execute)
        self._btn_execute.setToolTip("Execute expression (Enter)")
        input_layout.addWidget(self._btn_execute)

        # Clear button
        self._btn_clear = QPushButton("Clear")
        set_fixed_width(self._btn_clear, 50)
        self._btn_clear.clicked.connect(self.clear)
        self._btn_clear.setToolTip("Clear console output (Ctrl+L)")
        input_layout.addWidget(self._btn_clear)

        layout.addLayout(input_layout)

        # Setup auto-complete
        self._setup_completer()

    def _setup_completer(self) -> None:
        """Setup auto-complete for variable names and commands."""
        completions = list(self.BUILTIN_COMMANDS.keys())
        self._completer = QCompleter(completions, self)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._input.setCompleter(self._completer)

    def _update_completer(self) -> None:
        """Update auto-complete with current variable names."""
        completions = list(self.BUILTIN_COMMANDS.keys())

        if self._debug_controller and self._debug_controller._current_context:
            variables = self._debug_controller._current_context.variables
            completions.extend(variables.keys())

        model = self._completer.model()
        if hasattr(model, "setStringList"):
            model.setStringList(completions)

    def _apply_styles(self) -> None:
        """Apply VSCode-style dark theme using THEME_V2 tokens."""
        # NOTE: Syntax highlighting colors below are intentional VSCode Dark+ theme colors
        # for code display purposes. These are not semantic UI colors.
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {THEME_V2.bg_surface};
                color: {THEME_V2.text_primary};
            }}
            QPlainTextEdit {{
                background-color: {THEME_V2.bg_canvas};
                color: #d4d4d4;
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                padding: {TOKENS_V2.spacing.md}px;
                selection-background-color: #264f78;
            }}
            QLineEdit {{
                background-color: {THEME_V2.bg_canvas};
                color: #d4d4d4;
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                padding: {TOKENS_V2.spacing.sm}px 8px;
            }}
            QLineEdit:focus {{
                border-color: {THEME_V2.primary};
            }}
            QLabel {{
                color: #569cd6;
                font-weight: bold;
                padding: 0 4px;
            }}
            QPushButton {{
                background-color: {THEME_V2.bg_hover};
                color: {THEME_V2.text_primary};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                padding: {TOKENS_V2.spacing.sm}px 12px;
                font-size: {TOKENS_V2.typography.body}px;
            }}
            QPushButton:hover {{
                background-color: {THEME_V2.bg_hover};
                border-color: {THEME_V2.primary};
            }}
            QPushButton:pressed {{
                background-color: {THEME_V2.bg_hover};
            }}
        """)

    def _print_welcome(self) -> None:
        """Print welcome message."""
        # NOTE: Using VSCode Dark+ syntax highlighting colors (intentional)
        self._write_output("Debug Console", "#569cd6", bold=True)
        self._write_output("=" * 50, "#808080")
        self._write_output("Enter Python expressions to evaluate in debug context.", "#808080")
        self._write_output("Type 'help' for available commands.", "#808080")
        self._write_output("")

    def _on_execute(self) -> None:
        """Execute the current input."""
        # NOTE: Using VSCode Dark+ syntax highlighting colors (intentional)
        command = self._input.text().strip()
        if not command:
            return

        # Add to history
        self._input.add_to_history(command)

        # Echo input
        self._write_output(f">>> {command}", "#569cd6")

        # Check for built-in commands
        if self._handle_builtin_command(command):
            self._input.clear()
            return

        # Evaluate expression
        self._evaluate_expression(command)
        self._input.clear()

    def _handle_builtin_command(self, command: str) -> bool:
        """
        Handle built-in commands.

        Args:
            command: Command string

        Returns:
            True if command was handled
        """
        # NOTE: Using VSCode Dark+ syntax highlighting colors (intentional)
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd == "help":
            self._cmd_help()
            return True
        elif cmd == "vars":
            self._cmd_vars()
            return True
        elif cmd == "watch":
            if args:
                self._cmd_watch(args)
            else:
                self._write_output("Usage: watch <expression>", "#f44747")
            return True
        elif cmd == "unwatch":
            if args:
                self._cmd_unwatch(args)
            else:
                self._write_output("Usage: unwatch <expression>", "#f44747")
            return True
        elif cmd == "clear":
            self.clear()
            return True
        elif cmd == "history":
            self._cmd_history()
            return True

        return False

    def _cmd_help(self) -> None:
        """Display help for built-in commands."""
        # NOTE: Using VSCode Dark+ syntax highlighting colors (intentional)
        self._write_output("\nAvailable commands:", "#4ec9b0")
        for cmd, description in self.BUILTIN_COMMANDS.items():
            self._write_output(f"  {cmd:10} - {description}", "#d4d4d4")
        self._write_output("")

    def _cmd_vars(self) -> None:
        """Display all variables in current context."""
        # NOTE: Using VSCode Dark+ syntax highlighting colors (intentional)
        if not self._debug_controller or not self._debug_controller._current_context:
            self._write_output("No active debug context", "#f44747")
            return

        variables = self._debug_controller._current_context.variables
        if not variables:
            self._write_output("No variables defined", "#808080")
            return

        self._write_output("\nVariables:", "#4ec9b0")
        for name, value in sorted(variables.items()):
            type_name = type(value).__name__
            value_str = self._format_value(value, max_len=60)
            self._write_output(f"  {name} ({type_name}): {value_str}", "#d4d4d4")
        self._write_output("")

    def _cmd_watch(self, expression: str) -> None:
        """Add a watch expression."""
        # NOTE: Using VSCode Dark+ syntax highlighting colors (intentional)
        if self._debug_controller:
            self._debug_controller.add_watch(expression)
        self.watch_added.emit(expression)
        self._write_output(f"Added watch: {expression}", "#89d185")

    def _cmd_unwatch(self, expression: str) -> None:
        """Remove a watch expression."""
        # NOTE: Using VSCode Dark+ syntax highlighting colors (intentional)
        if self._debug_controller:
            self._debug_controller.remove_watch(expression)
        self.watch_removed.emit(expression)
        self._write_output(f"Removed watch: {expression}", "#89d185")

    def _cmd_history(self) -> None:
        """Display command history."""
        # NOTE: Using VSCode Dark+ syntax highlighting colors (intentional)
        history = self._input._history
        if not history:
            self._write_output("No command history", "#808080")
            return

        self._write_output("\nCommand history:", "#4ec9b0")
        for i, cmd in enumerate(history[-20:], 1):  # Show last 20
            self._write_output(f"  {i:3}. {cmd}", "#d4d4d4")
        self._write_output("")

    def _evaluate_expression(self, expression: str) -> None:
        """
        Evaluate a Python expression.

        Args:
            expression: Python expression to evaluate
        """
        # NOTE: Using VSCode Dark+ syntax highlighting colors (intentional)
        if not self._debug_controller:
            self._write_output("No debug controller available", "#f44747")
            return

        result, error = self._debug_controller.evaluate_expression(expression)

        if error:
            self._write_output(f"Error: {error}", "#f44747")
        else:
            formatted = self._format_value(result)
            self._write_output(formatted, "#89d185")

        self.expression_evaluated.emit(expression, result)
        self._update_completer()

    def _format_value(self, value: Any, max_len: int = TOKENS_V2.sizes.dialog_md_width) -> str:
        """
        Format a value for display.

        Args:
            value: Value to format
            max_len: Maximum string length

        Returns:
            Formatted string representation
        """
        if value is None:
            return "None"

        try:
            # Pretty print dicts and lists
            if isinstance(value, dict):
                import json

                try:
                    formatted = json.dumps(value, indent=2, default=str)
                except (TypeError, ValueError):
                    formatted = repr(value)
            elif isinstance(value, list | tuple):
                if len(value) > 10:
                    formatted = f"[{len(value)} items: {repr(value[:5])[:-1]}, ...]"
                else:
                    formatted = repr(value)
            else:
                formatted = repr(value)

            if len(formatted) > max_len:
                formatted = formatted[:max_len] + "..."

            return formatted

        except Exception:
            return str(value)

    def _write_output(
        self,
        text: str,
        color: str = "#d4d4d4",
        bold: bool = False,
    ) -> None:
        """
        Write text to output area with optional formatting.

        Args:
            text: Text to write
            color: Text color (hex) - NOTE: Uses VSCode Dark+ syntax colors for code display
            bold: Whether to use bold font
        """
        cursor = self._output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)

        cursor.insertText(text + "\n", fmt)
        self._output.setTextCursor(cursor)
        self._output.ensureCursorVisible()

    def write(self, text: str, level: str = "info") -> None:
        """
        Write text to console output.

        Args:
            text: Text to write
            level: Log level for coloring (info, warning, error, success)
        """
        # NOTE: Using VSCode Dark+ syntax highlighting colors for code display
        color_map = {
            "info": "#d4d4d4",
            "warning": "#cca700",
            "error": "#f44747",
            "success": "#89d185",
            "debug": "#808080",
        }
        color = color_map.get(level, "#d4d4d4")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._write_output(f"[{timestamp}] {text}", color)

    def clear(self) -> None:
        """Clear the console output."""
        self._output.clear()
        self._print_welcome()

    def focus_input(self) -> None:
        """Focus the input field."""
        self._input.setFocus()

    def get_entry_count(self) -> int:
        """Get number of output lines."""
        return self._output.blockCount()
