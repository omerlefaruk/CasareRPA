"""
Input dialog nodes.

Nodes for getting user input via dialogs.
"""

import asyncio
from typing import Optional, Tuple

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext

from .widgets import _create_styled_line_edit, _create_styled_text_edit


@properties(
    PropertyDef(
        "title",
        PropertyType.STRING,
        default="Input",
        label="Title",
        tooltip="Dialog window title",
    ),
    PropertyDef(
        "prompt",
        PropertyType.STRING,
        default="Enter value:",
        label="Prompt",
        tooltip="Message displayed to the user",
    ),
    PropertyDef(
        "default_value",
        PropertyType.STRING,
        default="",
        label="Default Value",
        tooltip="Pre-filled value in the input field",
    ),
    PropertyDef(
        "password_mode",
        PropertyType.BOOLEAN,
        default=False,
        label="Password Mode",
        tooltip="Hide input characters",
    ),
)
@node(category="system")
class InputDialogNode(BaseNode):
    """
    Display an input dialog to get user input.

    Config (via @properties):
        title: Dialog window title (default: "Input")
        prompt: Message displayed to user (default: "Enter value:")
        default_value: Pre-filled value (default: "")
        password_mode: Hide input (default: False)

    Outputs:
        value: User input value
        confirmed: Whether OK was clicked
    """

    # @category: system
    # @requires: none
    # @ports: -> value, confirmed

    def __init__(self, node_id: str, name: str = "Input Dialog", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "InputDialogNode"

    def _define_ports(self) -> None:
        self.add_output_port("value", DataType.STRING)
        self.add_output_port("confirmed", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # Get config properties (now PropertyDefs, not input ports)
            title_raw = self.get_parameter("title", "Input")
            prompt_raw = self.get_parameter("prompt", "Enter value:")
            default_raw = self.get_parameter("default_value", "")
            password_mode = self.get_parameter("password_mode", False)

            # Resolve variables (supports {{variable}} syntax)
            title = str(context.resolve_value(title_raw) or "Input")
            prompt = str(context.resolve_value(prompt_raw) or "Enter value:")
            default_value = str(context.resolve_value(default_raw) or "")

            value = ""
            confirmed = False

            try:
                from PySide6.QtWidgets import QInputDialog, QApplication, QLineEdit
                from PySide6.QtCore import Qt

                app = QApplication.instance()
                if app is None:
                    app = QApplication([])

                dialog = QInputDialog()
                dialog.setWindowTitle(title)
                dialog.setLabelText(prompt)
                dialog.setTextValue(default_value)
                dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)

                if password_mode:
                    dialog.setTextEchoMode(QLineEdit.Password)

                future = asyncio.get_event_loop().create_future()

                def on_finished(result_code):
                    if not future.done():
                        future.set_result(
                            (dialog.textValue(), result_code == QInputDialog.Accepted)
                        )

                dialog.finished.connect(on_finished)
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()

                text, ok = await future

                value = text if ok else ""
                confirmed = ok

            except ImportError:
                value = default_value
                confirmed = True

            self.set_output_value("value", value)
            self.set_output_value("confirmed", confirmed)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"confirmed": confirmed},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("value", "")
            self.set_output_value("confirmed", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@properties(
    PropertyDef(
        "title",
        PropertyType.STRING,
        default="Enter Text",
        label="Title",
        tooltip="Dialog title",
    ),
    PropertyDef(
        "default_text",
        PropertyType.TEXT,
        default="",
        label="Default Text",
        tooltip="Default text in the input area",
    ),
    PropertyDef(
        "placeholder",
        PropertyType.STRING,
        default="",
        label="Placeholder",
        tooltip="Placeholder text when empty",
    ),
    PropertyDef(
        "max_chars",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Max Characters",
        tooltip="Maximum character limit (0 = unlimited)",
    ),
)
@node(category="system")
class MultilineInputDialogNode(BaseNode):
    """
    Display a multi-line text input dialog.

    Config (via @properties):
        title: Dialog title (default: 'Enter Text')
        default_text: Default text (default: '')
        placeholder: Placeholder text (default: '')
        max_chars: Max characters, 0 = unlimited (default: 0)

    Outputs:
        text: Entered text
        confirmed: True if OK was clicked
        char_count: Number of characters entered
    """

    # @category: system
    # @requires: none
    # @ports: none -> text, confirmed, char_count

    def __init__(self, node_id: str, name: str = "Multiline Input", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "MultilineInputDialogNode"

    def _define_ports(self) -> None:
        self.add_output_port("text", DataType.STRING)
        self.add_output_port("confirmed", DataType.BOOLEAN)
        self.add_output_port("char_count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            title = self.get_parameter("title", "Enter Text")
            default_text = self.get_parameter("default_text", "")
            placeholder = self.get_parameter("placeholder", "")
            max_chars = int(self.get_parameter("max_chars", 0) or 0)

            title = context.resolve_value(title)
            default_text = context.resolve_value(default_text)

            try:
                from PySide6.QtWidgets import (
                    QDialog,
                    QVBoxLayout,
                    QDialogButtonBox,
                    QApplication,
                    QLabel,
                )
                from PySide6.QtCore import Qt

                app = QApplication.instance()
                if app is None:
                    raise ImportError("No QApplication")

                dialog = QDialog()
                dialog.setWindowTitle(title)
                dialog.setMinimumSize(400, 300)
                dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)

                layout = QVBoxLayout(dialog)

                text_edit = _create_styled_text_edit(
                    placeholder=placeholder or "",
                    text=default_text,
                )
                layout.addWidget(text_edit)

                # Character counter
                char_label = QLabel(f"Characters: {len(default_text)}")
                layout.addWidget(char_label)

                def on_text_changed():
                    current_text = text_edit.toPlainText()
                    if max_chars > 0 and len(current_text) > max_chars:
                        text_edit.setPlainText(current_text[:max_chars])
                        from PySide6.QtGui import QTextCursor

                        text_edit.moveCursor(QTextCursor.MoveOperation.End)
                    char_label.setText(f"Characters: {len(text_edit.toPlainText())}")

                text_edit.textChanged.connect(on_text_changed)

                buttons = QDialogButtonBox(
                    QDialogButtonBox.Ok | QDialogButtonBox.Cancel
                )
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)

                future = asyncio.get_event_loop().create_future()

                def on_finished(result):
                    if not future.done():
                        if result == QDialog.Accepted:
                            entered_text = text_edit.toPlainText()
                            future.set_result((entered_text, True, len(entered_text)))
                        else:
                            future.set_result(("", False, 0))

                dialog.finished.connect(on_finished)
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()

                text, confirmed, char_count = await future

            except ImportError:
                text = default_text
                confirmed = True
                char_count = len(text)

            self.set_output_value("text", text)
            self.set_output_value("confirmed", confirmed)
            self.set_output_value("char_count", char_count)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {
                    "text": text,
                    "confirmed": confirmed,
                    "char_count": char_count,
                },
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("text", "")
            self.set_output_value("confirmed", False)
            self.set_output_value("char_count", 0)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@properties(
    PropertyDef(
        "title",
        PropertyType.STRING,
        default="Login",
        label="Title",
        tooltip="Dialog title",
    ),
    PropertyDef(
        "username_label",
        PropertyType.STRING,
        default="Username:",
        label="Username Label",
        tooltip="Label for username field",
    ),
    PropertyDef(
        "password_label",
        PropertyType.STRING,
        default="Password:",
        label="Password Label",
        tooltip="Label for password field",
    ),
    PropertyDef(
        "show_remember",
        PropertyType.BOOLEAN,
        default=True,
        label="Show Remember Me",
        tooltip="Show 'Remember me' checkbox",
    ),
    PropertyDef(
        "mask_password",
        PropertyType.BOOLEAN,
        default=True,
        label="Mask Password",
        tooltip="Hide password characters",
    ),
)
@node(category="system")
class CredentialDialogNode(BaseNode):
    """
    Display a username/password credential dialog.

    Config (via @properties):
        title: Dialog title (default: 'Login')
        username_label: Label for username (default: 'Username:')
        password_label: Label for password (default: 'Password:')
        show_remember: Show remember checkbox (default: True)
        mask_password: Mask password input (default: True)

    Outputs:
        username: Entered username
        password: Entered password
        remember: Whether remember was checked
        confirmed: True if OK was clicked
    """

    # @category: system
    # @requires: none
    # @ports: none -> username, password, remember, confirmed

    def __init__(self, node_id: str, name: str = "Credential Dialog", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "CredentialDialogNode"

    def _define_ports(self) -> None:
        self.add_output_port("username", DataType.STRING)
        self.add_output_port("password", DataType.STRING)
        self.add_output_port("remember", DataType.BOOLEAN)
        self.add_output_port("confirmed", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            title = self.get_parameter("title", "Login")
            username_label = self.get_parameter("username_label", "Username:")
            password_label = self.get_parameter("password_label", "Password:")
            show_remember = self.get_parameter("show_remember", True)
            mask_password = self.get_parameter("mask_password", True)

            title = context.resolve_value(title)

            try:
                from PySide6.QtWidgets import (
                    QDialog,
                    QVBoxLayout,
                    QFormLayout,
                    QLineEdit,
                    QCheckBox,
                    QDialogButtonBox,
                    QApplication,
                )
                from PySide6.QtCore import Qt

                app = QApplication.instance()
                if app is None:
                    raise ImportError("No QApplication")

                dialog = QDialog()
                dialog.setWindowTitle(title)
                dialog.setMinimumWidth(300)
                dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)

                layout = QVBoxLayout(dialog)
                form = QFormLayout()

                username_input = _create_styled_line_edit()
                form.addRow(username_label, username_input)

                password_input = _create_styled_line_edit(
                    echo_mode=QLineEdit.Password if mask_password else None,
                )
                form.addRow(password_label, password_input)

                layout.addLayout(form)

                remember_check = None
                if show_remember:
                    remember_check = QCheckBox("Remember me")
                    layout.addWidget(remember_check)

                buttons = QDialogButtonBox(
                    QDialogButtonBox.Ok | QDialogButtonBox.Cancel
                )
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)

                future = asyncio.get_event_loop().create_future()

                def on_finished(result):
                    if not future.done():
                        if result == QDialog.Accepted:
                            remember = (
                                remember_check.isChecked() if remember_check else False
                            )
                            future.set_result(
                                (
                                    username_input.text(),
                                    password_input.text(),
                                    remember,
                                    True,
                                )
                            )
                        else:
                            future.set_result(("", "", False, False))

                dialog.finished.connect(on_finished)
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()

                username, password, remember, confirmed = await future

            except ImportError:
                username = ""
                password = ""
                remember = False
                confirmed = False

            self.set_output_value("username", username)
            self.set_output_value("password", password)
            self.set_output_value("remember", remember)
            self.set_output_value("confirmed", confirmed)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"username": username, "confirmed": confirmed},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("username", "")
            self.set_output_value("password", "")
            self.set_output_value("remember", False)
            self.set_output_value("confirmed", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}
