"""
Form and wizard dialog nodes.

Nodes for displaying custom forms and multi-step wizards.
"""

import asyncio
from typing import Optional, Tuple

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    PortType,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext

from .widgets import _create_styled_line_edit


@properties(
    PropertyDef(
        "title",
        PropertyType.STRING,
        default="Form",
        label="Title",
        tooltip="Dialog title",
    ),
    PropertyDef(
        "fields",
        PropertyType.JSON,
        default="[]",
        label="Fields (JSON)",
        tooltip='JSON array: [{"name": "field1", "type": "text", "label": "Field 1", "required": true}]',
        essential=True,
    ),
)
@node(category="system")
class FormDialogNode(BaseNode):
    """
    Display a custom form dialog with dynamic fields.

    Config (via @properties):
        title: Dialog title (default: 'Form')
        fields: JSON array defining fields (essential)
            Each field: {"name": "id", "type": "text|number|checkbox|select", "label": "...", "required": bool, "options": [...]}

    Outputs:
        data: Dictionary of field values
        confirmed: True if OK was clicked
    """

    # @category: system
    # @requires: none
    # @ports: fields -> data, confirmed

    def __init__(self, node_id: str, name: str = "Form Dialog", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FormDialogNode"

    def _define_ports(self) -> None:
        self.add_input_port("fields", DataType.ANY, required=False)
        self.add_output_port("data", DataType.DICT)
        self.add_output_port("confirmed", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            import json

            title = self.get_parameter("title", "Form")
            fields_input = self.get_input_value("fields")
            if fields_input is None:
                fields_input = self.get_parameter("fields", "[]")

            title = context.resolve_value(title)

            if isinstance(fields_input, str):
                fields_input = context.resolve_value(fields_input)
                try:
                    fields = json.loads(fields_input)
                except json.JSONDecodeError:
                    fields = []
            elif isinstance(fields_input, list):
                fields = fields_input
            else:
                fields = []

            if not fields:
                self.set_output_value("data", {})
                self.set_output_value("confirmed", False)
                self.status = NodeStatus.SUCCESS
                return {"success": True, "data": {}, "next_nodes": ["exec_out"]}

            try:
                from PySide6.QtWidgets import (
                    QDialog,
                    QVBoxLayout,
                    QFormLayout,
                    QLineEdit,
                    QSpinBox,
                    QDoubleSpinBox,
                    QCheckBox,
                    QComboBox,
                    QDialogButtonBox,
                    QApplication,
                )
                from PySide6.QtCore import Qt

                app = QApplication.instance()
                if app is None:
                    raise ImportError("No QApplication")

                dialog = QDialog()
                dialog.setWindowTitle(title)
                dialog.setMinimumWidth(350)
                dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)

                layout = QVBoxLayout(dialog)
                form = QFormLayout()

                widgets = {}
                for field in fields:
                    field_name = field.get("name", "")
                    field_type = field.get("type", "text")
                    field_label = field.get("label", field_name)
                    field_default = field.get("default", "")
                    field_options = field.get("options", [])

                    if field_type == "text":
                        widget = _create_styled_line_edit(text=str(field_default))
                        widgets[field_name] = ("text", widget)
                    elif field_type == "number":
                        if isinstance(field_default, float):
                            widget = QDoubleSpinBox()
                            widget.setRange(-999999, 999999)
                            widget.setValue(float(field_default or 0))
                        else:
                            widget = QSpinBox()
                            widget.setRange(-999999, 999999)
                            widget.setValue(int(field_default or 0))
                        widgets[field_name] = ("number", widget)
                    elif field_type == "checkbox":
                        widget = QCheckBox()
                        widget.setChecked(bool(field_default))
                        widgets[field_name] = ("checkbox", widget)
                    elif field_type == "select":
                        widget = QComboBox()
                        widget.addItems([str(opt) for opt in field_options])
                        if field_default and str(field_default) in [
                            str(o) for o in field_options
                        ]:
                            widget.setCurrentText(str(field_default))
                        widgets[field_name] = ("select", widget)
                    else:
                        widget = _create_styled_line_edit(text=str(field_default))
                        widgets[field_name] = ("text", widget)

                    form.addRow(field_label, widget)

                layout.addLayout(form)

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
                            form_data = {}
                            for name, (ftype, widget) in widgets.items():
                                if ftype == "text":
                                    form_data[name] = widget.text()
                                elif ftype == "number":
                                    form_data[name] = widget.value()
                                elif ftype == "checkbox":
                                    form_data[name] = widget.isChecked()
                                elif ftype == "select":
                                    form_data[name] = widget.currentText()
                            future.set_result((form_data, True))
                        else:
                            future.set_result(({}, False))

                dialog.finished.connect(on_finished)
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()

                data, confirmed = await future

            except ImportError:
                data = {}
                confirmed = False

            self.set_output_value("data", data)
            self.set_output_value("confirmed", confirmed)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"data": data, "confirmed": confirmed},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("data", {})
            self.set_output_value("confirmed", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@properties(
    PropertyDef(
        "title",
        PropertyType.STRING,
        default="Wizard",
        label="Title",
        tooltip="Wizard title",
    ),
    PropertyDef(
        "steps",
        PropertyType.JSON,
        default="[]",
        label="Steps (JSON)",
        tooltip='JSON array: [{"title": "Step 1", "fields": [...]}]',
        essential=True,
    ),
    PropertyDef(
        "allow_back",
        PropertyType.BOOLEAN,
        default=True,
        label="Allow Back",
        tooltip="Allow navigating to previous steps",
    ),
)
@node(category="system")
class WizardDialogNode(BaseNode):
    """
    Display a multi-step wizard dialog.

    Config (via @properties):
        title: Wizard title (default: 'Wizard')
        steps: JSON array of steps (essential)
            Each step: {"title": "Step N", "description": "...", "fields": [...]}
        allow_back: Allow going back (default: True)

    Outputs:
        data: Dictionary of all field values
        completed: True if wizard completed
        canceled: True if canceled
        last_step: Index of last completed step
    """

    # @category: system
    # @requires: none
    # @ports: steps -> data, completed, canceled, last_step

    def __init__(self, node_id: str, name: str = "Wizard Dialog", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "WizardDialogNode"

    def _define_ports(self) -> None:
        self.add_input_port("steps", DataType.ANY, required=False)
        self.add_output_port("data", DataType.DICT)
        self.add_output_port("completed", DataType.BOOLEAN)
        self.add_output_port("canceled", DataType.BOOLEAN)
        self.add_output_port("last_step", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            import json

            title = self.get_parameter("title", "Wizard")
            steps_input = self.get_input_value("steps")
            if steps_input is None:
                steps_input = self.get_parameter("steps", "[]")
            allow_back = self.get_parameter("allow_back", True)

            title = context.resolve_value(title)

            if isinstance(steps_input, str):
                steps_input = context.resolve_value(steps_input)
                try:
                    steps = json.loads(steps_input)
                except json.JSONDecodeError:
                    steps = []
            elif isinstance(steps_input, list):
                steps = steps_input
            else:
                steps = []

            if not steps:
                self.set_output_value("data", {})
                self.set_output_value("completed", False)
                self.set_output_value("canceled", True)
                self.set_output_value("last_step", -1)
                self.status = NodeStatus.SUCCESS
                return {"success": True, "data": {}, "next_nodes": ["exec_out"]}

            try:
                from PySide6.QtWidgets import (
                    QDialog,
                    QVBoxLayout,
                    QHBoxLayout,
                    QLabel,
                    QStackedWidget,
                    QPushButton,
                    QFormLayout,
                    QLineEdit,
                    QSpinBox,
                    QCheckBox,
                    QComboBox,
                    QApplication,
                    QWidget,
                )
                from PySide6.QtCore import Qt

                app = QApplication.instance()
                if app is None:
                    raise ImportError("No QApplication")

                dialog = QDialog()
                dialog.setWindowTitle(title)
                dialog.setMinimumSize(450, 350)
                dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)

                main_layout = QVBoxLayout(dialog)

                # Step indicator
                step_label = QLabel(f"Step 1 of {len(steps)}")
                step_label.setStyleSheet("font-weight: bold; font-size: 14px;")
                main_layout.addWidget(step_label)

                # Stacked widget for steps
                stack = QStackedWidget()
                all_widgets = {}

                for step_idx, step in enumerate(steps):
                    step_widget = QWidget()
                    step_layout = QVBoxLayout(step_widget)

                    step_title = step.get("title", f"Step {step_idx + 1}")
                    title_lbl = QLabel(step_title)
                    title_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
                    step_layout.addWidget(title_lbl)

                    description = step.get("description", "")
                    if description:
                        desc_lbl = QLabel(description)
                        desc_lbl.setWordWrap(True)
                        step_layout.addWidget(desc_lbl)

                    form = QFormLayout()
                    fields = step.get("fields", [])

                    for field in fields:
                        field_name = field.get("name", "")
                        field_type = field.get("type", "text")
                        field_label = field.get("label", field_name)
                        field_default = field.get("default", "")
                        field_options = field.get("options", [])

                        full_name = f"step{step_idx}_{field_name}"

                        if field_type == "text":
                            widget = _create_styled_line_edit(text=str(field_default))
                            all_widgets[full_name] = ("text", widget)
                        elif field_type == "number":
                            widget = QSpinBox()
                            widget.setRange(-999999, 999999)
                            widget.setValue(int(field_default or 0))
                            all_widgets[full_name] = ("number", widget)
                        elif field_type == "checkbox":
                            widget = QCheckBox()
                            widget.setChecked(bool(field_default))
                            all_widgets[full_name] = ("checkbox", widget)
                        elif field_type == "select":
                            widget = QComboBox()
                            widget.addItems([str(opt) for opt in field_options])
                            all_widgets[full_name] = ("select", widget)
                        else:
                            widget = _create_styled_line_edit(text=str(field_default))
                            all_widgets[full_name] = ("text", widget)

                        form.addRow(field_label, widget)

                    step_layout.addLayout(form)
                    step_layout.addStretch()
                    stack.addWidget(step_widget)

                main_layout.addWidget(stack)

                # Navigation buttons
                nav_layout = QHBoxLayout()
                back_btn = QPushButton("Back")
                back_btn.setEnabled(False)
                next_btn = QPushButton("Next")
                cancel_btn = QPushButton("Cancel")

                nav_layout.addWidget(back_btn)
                nav_layout.addStretch()
                nav_layout.addWidget(cancel_btn)
                nav_layout.addWidget(next_btn)
                main_layout.addLayout(nav_layout)

                current_step = [0]
                result_data = [{}]
                completed_flag = [False]

                def update_buttons():
                    back_btn.setEnabled(allow_back and current_step[0] > 0)
                    if current_step[0] == len(steps) - 1:
                        next_btn.setText("Finish")
                    else:
                        next_btn.setText("Next")
                    step_label.setText(f"Step {current_step[0] + 1} of {len(steps)}")

                def go_back():
                    if current_step[0] > 0:
                        current_step[0] -= 1
                        stack.setCurrentIndex(current_step[0])
                        update_buttons()

                def go_next():
                    if current_step[0] < len(steps) - 1:
                        current_step[0] += 1
                        stack.setCurrentIndex(current_step[0])
                        update_buttons()
                    else:
                        # Collect all data
                        for name, (ftype, widget) in all_widgets.items():
                            if ftype == "text":
                                result_data[0][name] = widget.text()
                            elif ftype == "number":
                                result_data[0][name] = widget.value()
                            elif ftype == "checkbox":
                                result_data[0][name] = widget.isChecked()
                            elif ftype == "select":
                                result_data[0][name] = widget.currentText()
                        completed_flag[0] = True
                        dialog.accept()

                back_btn.clicked.connect(go_back)
                next_btn.clicked.connect(go_next)
                cancel_btn.clicked.connect(dialog.reject)

                update_buttons()

                future = asyncio.get_event_loop().create_future()

                def on_finished(result):
                    if not future.done():
                        future.set_result(
                            (result_data[0], completed_flag[0], current_step[0])
                        )

                dialog.finished.connect(on_finished)
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()

                data, completed, last_step = await future

            except ImportError:
                data = {}
                completed = False
                last_step = -1

            self.set_output_value("data", data)
            self.set_output_value("completed", completed)
            self.set_output_value("canceled", not completed)
            self.set_output_value("last_step", last_step)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"data": data, "completed": completed, "last_step": last_step},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("data", {})
            self.set_output_value("completed", False)
            self.set_output_value("canceled", True)
            self.set_output_value("last_step", -1)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}
