"""
Breakpoint Edit Dialog for configuring breakpoint properties.

Allows editing breakpoint type, condition expression, hit count target,
and log message for log points.

Epic 7.x - Migrated to BaseDialogV2 with THEME_V2/TOKENS_V2.
"""

from typing import TYPE_CHECKING, Optional

from loguru import logger
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.dialogs_v2 import (
    BaseDialogV2,
    DialogSizeV2,
)

if TYPE_CHECKING:
    from ...debugger.debug_controller import (
        Breakpoint,
        DebugController,
    )


class BreakpointEditDialog(BaseDialogV2):
    """
    Dialog for editing breakpoint properties.

    Supports configuration of all breakpoint types:
    - Regular: Simple breakpoint, no conditions
    - Conditional: Breaks when Python expression evaluates to True
    - Hit-Count: Breaks after specified number of hits
    - Log Point: Logs a message without breaking

    Epic 7.x - Migrated to BaseDialogV2 with THEME_V2/TOKENS_V2.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        breakpoint: Optional["Breakpoint"] = None,
        node_id: str = "",
        debug_controller: Optional["DebugController"] = None,
    ) -> None:
        """
        Initialize breakpoint edit dialog.

        Args:
            parent: Parent widget
            breakpoint: Existing breakpoint to edit (None for new)
            node_id: Node ID for the breakpoint
            debug_controller: Debug controller for testing expressions
        """
        super().__init__(
            title="Edit Breakpoint" if breakpoint else "Add Breakpoint",
            parent=parent,
            size=DialogSizeV2.MD,
        )
        self._breakpoint = breakpoint
        self._node_id = node_id or (breakpoint.node_id if breakpoint else "")
        self._debug_controller = debug_controller

        self._setup_ui()
        self._populate_from_breakpoint()
        self._connect_signals()

        # Set footer buttons
        self.set_primary_button("OK", self.accept)
        self.set_secondary_button("Cancel", self.reject)

        logger.debug(f"BreakpointEditDialog opened for node: {self._node_id}")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(TOKENS_V2.spacing.md)
        layout.setContentsMargins(0, 0, 0, 0)

        # Node info
        node_label = QLabel(f"Node: {self._node_id}")
        node_label.setStyleSheet(
            f"color: {THEME_V2.text_secondary}; padding-bottom: {TOKENS_V2.spacing.sm}px;"
        )
        layout.addWidget(node_label)

        # Breakpoint type selector
        type_layout = QHBoxLayout()
        type_label = QLabel("Type:")
        type_label.setMinimumWidth(80)
        type_label.setStyleSheet(f"color: {THEME_V2.text_primary};")
        self._type_combo = QComboBox()
        self._type_combo.addItems(
            [
                "Regular",
                "Conditional",
                "Hit-Count",
                "Log Point",
            ]
        )
        self._style_combo_box(self._type_combo)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self._type_combo, 1)
        layout.addLayout(type_layout)

        # Stacked widget for type-specific options
        self._options_stack = QStackedWidget()

        # Page 0: Regular (no options)
        regular_page = QWidget()
        regular_layout = QVBoxLayout(regular_page)
        regular_info = QLabel("Execution will pause when this node is reached.")
        regular_info.setStyleSheet(f"color: {THEME_V2.text_secondary};")
        regular_info.setWordWrap(True)
        regular_layout.addWidget(regular_info)
        regular_layout.addStretch()
        self._options_stack.addWidget(regular_page)

        # Page 1: Conditional
        conditional_page = self._create_conditional_page()
        self._options_stack.addWidget(conditional_page)

        # Page 2: Hit-Count
        hit_count_page = self._create_hit_count_page()
        self._options_stack.addWidget(hit_count_page)

        # Page 3: Log Point
        log_point_page = self._create_log_point_page()
        self._options_stack.addWidget(log_point_page)

        layout.addWidget(self._options_stack)

        # Test result label
        self._test_result = QLabel()
        self._test_result.setWordWrap(True)
        self._test_result.hide()
        layout.addWidget(self._test_result)

        layout.addStretch()

        self.set_body_widget(content)

    def _style_combo_box(self, combo: QComboBox) -> None:
        """Apply v2 styling to combo box."""
        combo.setStyleSheet(f"""
            QComboBox {{
                background: {THEME_V2.bg_component};
                color: {THEME_V2.text_primary};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                padding: {TOKENS_V2.spacing.sm}px;
            }}
            QComboBox:focus {{
                border-color: {THEME_V2.border_focus};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME_V2.border};
                selection-background-color: {THEME_V2.bg_selected};
            }}
        """)

    def _style_group_box(self, group: QGroupBox) -> None:
        """Apply v2 styling to group box."""
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                margin-top: {TOKENS_V2.spacing.md}px;
                padding-top: {TOKENS_V2.spacing.md}px;
                color: {THEME_V2.text_primary};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {TOKENS_V2.spacing.md}px;
                padding: 0 {TOKENS_V2.spacing.xs}px;
            }}
        """)

    def _style_text_edit(self, text_edit: QTextEdit) -> None:
        """Apply v2 styling to text edit."""
        text_edit.setStyleSheet(f"""
            QTextEdit {{
                background: {THEME_V2.bg_component};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                padding: {TOKENS_V2.spacing.sm}px;
                color: {THEME_V2.text_primary};
            }}
            QTextEdit:focus {{
                border-color: {THEME_V2.border_focus};
            }}
        """)

    def _style_spin_box(self, spin: QSpinBox) -> None:
        """Apply v2 styling to spin box."""
        spin.setStyleSheet(f"""
            QSpinBox {{
                background: {THEME_V2.bg_component};
                color: {THEME_V2.text_primary};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                padding: {TOKENS_V2.spacing.sm}px;
            }}
            QSpinBox:focus {{
                border-color: {THEME_V2.border_focus};
            }}
        """)

    def _style_button(self, button: QPushButton) -> None:
        """Apply v2 styling to button."""
        button.setStyleSheet(f"""
            QPushButton {{
                background: {THEME_V2.bg_component};
                color: {THEME_V2.text_primary};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                padding: {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.md}px;
            }}
            QPushButton:hover {{
                background: {THEME_V2.bg_hover};
            }}
            QPushButton:pressed {{
                background: {THEME_V2.bg_selected};
            }}
        """)

    def _create_conditional_page(self) -> QWidget:
        """Create the conditional breakpoint options page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, TOKENS_V2.spacing.md, 0, 0)

        # Description
        info = QLabel(
            "Execution will pause when the condition evaluates to True.\n"
            "Use workflow variables in your expression (e.g., count > 5)."
        )
        info.setStyleSheet(f"color: {THEME_V2.text_secondary};")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Condition input
        condition_group = QGroupBox("Condition Expression")
        self._style_group_box(condition_group)
        condition_layout = QVBoxLayout(condition_group)

        self._condition_edit = QTextEdit()
        self._condition_edit.setPlaceholderText("Python expression (e.g., len(items) > 10)")
        self._condition_edit.setMinimumHeight(60)
        self._condition_edit.setMaximumHeight(80)
        self._style_text_edit(self._condition_edit)
        condition_layout.addWidget(self._condition_edit)

        # Test button
        test_btn = QPushButton("Test Condition")
        self._style_button(test_btn)
        test_btn.clicked.connect(self._test_condition)
        condition_layout.addWidget(test_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(condition_group)
        layout.addStretch()

        return page

    def _create_hit_count_page(self) -> QWidget:
        """Create the hit-count breakpoint options page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, TOKENS_V2.spacing.md, 0, 0)

        # Description
        info = QLabel(
            "Execution will pause after the node has been hit the specified\n"
            "number of times. Useful for debugging loops."
        )
        info.setStyleSheet(f"color: {THEME_V2.text_secondary};")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Hit count input
        hit_count_group = QGroupBox("Hit Count Target")
        self._style_group_box(hit_count_group)
        hit_count_layout = QHBoxLayout(hit_count_group)

        hit_count_label = QLabel("Break after")
        hit_count_label.setStyleSheet(f"color: {THEME_V2.text_primary};")
        self._hit_count_spin = QSpinBox()
        self._hit_count_spin.setMinimum(1)
        self._hit_count_spin.setMaximum(10000)
        self._hit_count_spin.setValue(1)
        self._hit_count_spin.setMinimumWidth(100)
        self._style_spin_box(self._hit_count_spin)
        hit_count_suffix = QLabel("hit(s)")
        hit_count_suffix.setStyleSheet(f"color: {THEME_V2.text_primary};")

        hit_count_layout.addWidget(hit_count_label)
        hit_count_layout.addWidget(self._hit_count_spin)
        hit_count_layout.addWidget(hit_count_suffix)
        hit_count_layout.addStretch()

        layout.addWidget(hit_count_group)
        layout.addStretch()

        return page

    def _create_log_point_page(self) -> QWidget:
        """Create the log point options page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, TOKENS_V2.spacing.md, 0, 0)

        # Description
        info = QLabel(
            "Log a message without pausing execution.\n"
            "Use {variable_name} syntax to include variable values."
        )
        info.setStyleSheet(f"color: {THEME_V2.text_secondary};")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Log message input
        log_group = QGroupBox("Log Message")
        self._style_group_box(log_group)
        log_layout = QVBoxLayout(log_group)

        self._log_message_edit = QTextEdit()
        self._log_message_edit.setPlaceholderText("Processing item {index} of {total}...")
        self._log_message_edit.setMinimumHeight(60)
        self._log_message_edit.setMaximumHeight(80)
        self._style_text_edit(self._log_message_edit)
        log_layout.addWidget(self._log_message_edit)

        layout.addWidget(log_group)
        layout.addStretch()

        return page

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)

    def _populate_from_breakpoint(self) -> None:
        """Populate dialog fields from existing breakpoint."""
        if not self._breakpoint:
            return

        from ...debugger.debug_controller import BreakpointType

        # Set type combo
        type_index = {
            BreakpointType.REGULAR: 0,
            BreakpointType.CONDITIONAL: 1,
            BreakpointType.HIT_COUNT: 2,
            BreakpointType.LOG_POINT: 3,
        }.get(self._breakpoint.breakpoint_type, 0)

        self._type_combo.setCurrentIndex(type_index)
        self._options_stack.setCurrentIndex(type_index)

        # Populate type-specific fields
        if self._breakpoint.condition:
            self._condition_edit.setPlainText(self._breakpoint.condition)

        self._hit_count_spin.setValue(self._breakpoint.hit_count_target)

        if self._breakpoint.log_message:
            self._log_message_edit.setPlainText(self._breakpoint.log_message)

    @Slot(int)
    def _on_type_changed(self, index: int) -> None:
        """Handle breakpoint type change."""
        self._options_stack.setCurrentIndex(index)
        self._test_result.hide()

    @Slot()
    def _test_condition(self) -> None:
        """Test the condition expression."""
        condition = self._condition_edit.toPlainText().strip()
        if not condition:
            self._show_test_result("Please enter a condition expression", "warning")
            return

        # Try to compile the expression
        try:
            compile(condition, "<condition>", "eval")
            self._show_test_result("Condition is syntactically valid", "success")
        except SyntaxError as e:
            self._show_test_result(f"Syntax error: {e.msg}", "error")

    def _show_test_result(self, message: str, status: str) -> None:
        """Show test result message."""
        color_map = {
            "success": THEME_V2.success,
            "error": THEME_V2.error,
            "warning": THEME_V2.warning,
        }
        self._test_result.setStyleSheet(f"color: {color_map.get(status, THEME_V2.text_secondary)};")
        self._test_result.setText(message)
        self._test_result.show()

    def get_breakpoint_data(self) -> dict:
        """
        Get breakpoint configuration from dialog.

        Returns:
            Dictionary with breakpoint configuration:
            - node_id: str
            - breakpoint_type: BreakpointType
            - condition: Optional[str]
            - hit_count_target: int
            - log_message: Optional[str]
        """
        from ...debugger.debug_controller import BreakpointType

        type_map = {
            0: BreakpointType.REGULAR,
            1: BreakpointType.CONDITIONAL,
            2: BreakpointType.HIT_COUNT,
            3: BreakpointType.LOG_POINT,
        }

        bp_type = type_map.get(self._type_combo.currentIndex(), BreakpointType.REGULAR)

        data = {
            "node_id": self._node_id,
            "breakpoint_type": bp_type,
            "condition": None,
            "hit_count_target": 1,
            "log_message": None,
        }

        if bp_type == BreakpointType.CONDITIONAL:
            condition = self._condition_edit.toPlainText().strip()
            data["condition"] = condition if condition else None

        elif bp_type == BreakpointType.HIT_COUNT:
            data["hit_count_target"] = self._hit_count_spin.value()

        elif bp_type == BreakpointType.LOG_POINT:
            log_msg = self._log_message_edit.toPlainText().strip()
            data["log_message"] = log_msg if log_msg else None

        return data


def show_breakpoint_edit_dialog(
    parent: QWidget | None,
    node_id: str,
    breakpoint: Optional["Breakpoint"] = None,
    debug_controller: Optional["DebugController"] = None,
) -> dict | None:
    """
    Show breakpoint edit dialog and return configuration.

    Args:
        parent: Parent widget
        node_id: Node ID for the breakpoint
        breakpoint: Existing breakpoint to edit (None for new)
        debug_controller: Debug controller for testing expressions

    Returns:
        Breakpoint configuration dict or None if cancelled
    """
    from PySide6.QtWidgets import QDialog

    dialog = BreakpointEditDialog(
        parent=parent,
        breakpoint=breakpoint,
        node_id=node_id,
        debug_controller=debug_controller,
    )

    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_breakpoint_data()

    return None
