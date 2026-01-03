"""
Cron Builder Dialog for Schedule Management.

Visual cron expression builder with:
- Simple mode (dropdowns for common patterns)
- Advanced mode (raw expression editing)
- Preview of next N runs

Epic 7.x - Migrated to BaseDialogV2 with THEME_V2/TOKENS_V2.
"""

from datetime import datetime, timedelta

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.dialogs_v2 import (
    BaseDialogV2,
    DialogSizeV2,
)


class CronBuilderDialog(BaseDialogV2):
    """
    Dialog for building cron expressions visually.

    Provides:
    - Simple mode: Dropdowns for frequency, time, day selection
    - Advanced mode: Raw cron expression with validation
    - Preview: Shows next 10 scheduled runs

    Epic 7.x - Migrated to BaseDialogV2 with THEME_V2/TOKENS_V2.
    """

    expression_changed = Signal(str)

    def __init__(
        self,
        initial_expression: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            title="Cron Schedule Builder",
            parent=parent,
            size=DialogSizeV2.LG,
        )
        self._initial_expression = initial_expression
        self._current_expression = initial_expression or "0 0 * * *"

        self._setup_ui()
        self._connect_signals()

        if initial_expression:
            self._load_expression(initial_expression)

        self._update_preview()

        # Set footer buttons
        self.set_primary_button("OK", self.accept)
        self.set_secondary_button("Cancel", self.reject)

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(TOKENS_V2.spacing.md)
        layout.setContentsMargins(0, 0, 0, 0)

        self._tab_widget = QTabWidget()
        self._style_tab_widget(self._tab_widget)

        simple_tab = QWidget()
        self._setup_simple_tab(simple_tab)
        self._tab_widget.addTab(simple_tab, "Simple")

        advanced_tab = QWidget()
        self._setup_advanced_tab(advanced_tab)
        self._tab_widget.addTab(advanced_tab, "Advanced")

        layout.addWidget(self._tab_widget)

        expression_group = QGroupBox("Cron Expression")
        self._style_group_box(expression_group)
        expression_layout = QHBoxLayout(expression_group)

        self._expression_display = QLineEdit()
        self._expression_display.setReadOnly(True)
        self._expression_display.setStyleSheet(
            f"font-family: monospace; font-size: {TOKENS_V2.typography.body}px; "
            f"background: {THEME_V2.bg_component}; color: {THEME_V2.text_primary}; "
            f"border: 1px solid {THEME_V2.border}; border-radius: {TOKENS_V2.radius.sm}px; "
            f"padding: {TOKENS_V2.spacing.sm}px;"
        )
        self._expression_display.setText(self._current_expression)
        expression_layout.addWidget(self._expression_display)

        layout.addWidget(expression_group)

        preview_group = QGroupBox("Next 10 Runs")
        self._style_group_box(preview_group)
        preview_layout = QVBoxLayout(preview_group)

        self._preview_list = QListWidget()
        self._style_list_widget(self._preview_list)
        self._preview_list.setMaximumHeight(TOKENS_V2.sizes.dialog_height_sm)
        self._preview_list.setAlternatingRowColors(True)
        preview_layout.addWidget(self._preview_list)

        layout.addWidget(preview_group)

        layout.addStretch()

        self.set_body_widget(content)

    def _style_tab_widget(self, tab: QTabWidget) -> None:
        """Apply v2 styling to tab widget."""
        tab.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {THEME_V2.border};
                background: {THEME_V2.bg_surface};
            }}
            QTabBar::tab {{
                background: {THEME_V2.bg_component};
                color: {THEME_V2.text_primary};
                padding: {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.md}px;
                border: 1px solid {THEME_V2.border};
                border-bottom: none;
                border-top-left-radius: {TOKENS_V2.radius.sm}px;
                border-top-right-radius: {TOKENS_V2.radius.sm}px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {THEME_V2.bg_surface};
                border-bottom: 2px solid {THEME_V2.accent_base};
            }}
            QTabBar::tab:hover:!selected {{
                background: {THEME_V2.bg_hover};
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

    def _style_line_edit(self, edit: QLineEdit) -> None:
        """Apply v2 styling to line edit."""
        edit.setStyleSheet(f"""
            QLineEdit {{
                background: {THEME_V2.bg_component};
                color: {THEME_V2.text_primary};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                padding: {TOKENS_V2.spacing.sm}px;
            }}
            QLineEdit:focus {{
                border-color: {THEME_V2.border_focus};
            }}
        """)

    def _style_list_widget(self, list_w: QListWidget) -> None:
        """Apply v2 styling to list widget."""
        list_w.setStyleSheet(f"""
            QListWidget {{
                background: {THEME_V2.bg_component};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
            }}
            QListWidget::item {{
                padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.sm}px;
            }}
            QListWidget::item:selected {{
                background: {THEME_V2.bg_selected};
            }}
        """)

    def _setup_simple_tab(self, tab: QWidget) -> None:
        """Set up the simple mode tab."""
        layout = QVBoxLayout(tab)
        layout.setSpacing(TOKENS_V2.spacing.lg)

        freq_group = QGroupBox("Frequency")
        self._style_group_box(freq_group)
        freq_layout = QHBoxLayout(freq_group)

        freq_layout.addWidget(QLabel("Run:"))
        self._frequency_combo = QComboBox()
        self._frequency_combo.addItem("Every minute", "minute")
        self._frequency_combo.addItem("Hourly", "hourly")
        self._frequency_combo.addItem("Daily", "daily")
        self._frequency_combo.addItem("Weekly", "weekly")
        self._frequency_combo.addItem("Monthly", "monthly")
        self._frequency_combo.setCurrentIndex(2)
        self._style_combo_box(self._frequency_combo)
        freq_layout.addWidget(self._frequency_combo)
        freq_layout.addStretch()

        layout.addWidget(freq_group)

        time_group = QGroupBox("Time")
        self._style_group_box(time_group)
        time_layout = QGridLayout(time_group)

        time_layout.addWidget(QLabel("Hour:"), 0, 0)
        self._hour_spin = QSpinBox()
        self._hour_spin.setRange(0, 23)
        self._hour_spin.setValue(9)
        self._style_spin_box(self._hour_spin)
        time_layout.addWidget(self._hour_spin, 0, 1)

        time_layout.addWidget(QLabel("Minute:"), 0, 2)
        self._minute_spin = QSpinBox()
        self._minute_spin.setRange(0, 59)
        self._minute_spin.setValue(0)
        self._style_spin_box(self._minute_spin)
        time_layout.addWidget(self._minute_spin, 0, 3)

        time_layout.setColumnStretch(4, 1)

        layout.addWidget(time_group)

        days_group = QGroupBox("Days of Week (for Weekly)")
        self._style_group_box(days_group)
        days_layout = QHBoxLayout(days_group)

        self._day_checkboxes = []
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            cb = QCheckBox(day)
            cb.setStyleSheet(f"color: {THEME_V2.text_primary};")
            if day == "Mon":
                cb.setChecked(True)
            self._day_checkboxes.append(cb)
            days_layout.addWidget(cb)

        layout.addWidget(days_group)

        dom_group = QGroupBox("Day of Month (for Monthly)")
        self._style_group_box(dom_group)
        dom_layout = QHBoxLayout(dom_group)

        dom_layout.addWidget(QLabel("Day:"))
        self._day_of_month_spin = QSpinBox()
        self._day_of_month_spin.setRange(1, 31)
        self._day_of_month_spin.setValue(1)
        self._style_spin_box(self._day_of_month_spin)
        dom_layout.addWidget(self._day_of_month_spin)
        dom_layout.addStretch()

        layout.addWidget(dom_group)

        layout.addStretch()

    def _setup_advanced_tab(self, tab: QWidget) -> None:
        """Set up the advanced mode tab."""
        layout = QVBoxLayout(tab)
        layout.setSpacing(TOKENS_V2.spacing.lg)

        info_label = QLabel(
            "Enter a cron expression with 5 fields:\n"
            "minute hour day-of-month month day-of-week\n\n"
            "Examples:\n"
            "  0 9 * * *    - Every day at 9:00 AM\n"
            "  */15 * * * * - Every 15 minutes\n"
            "  0 0 1 * *    - First day of each month at midnight\n"
            "  0 9 * * 1-5  - Weekdays at 9:00 AM"
        )
        info_label.setStyleSheet(
            f"font-family: monospace; padding: {TOKENS_V2.spacing.sm}px; "
            f"color: {THEME_V2.text_secondary};"
        )
        layout.addWidget(info_label)

        expr_layout = QHBoxLayout()
        expr_layout.addWidget(QLabel("Expression:"))
        self._advanced_input = QLineEdit()
        self._advanced_input.setPlaceholderText("0 9 * * *")
        self._advanced_input.setText(self._current_expression)
        self._style_line_edit(self._advanced_input)
        expr_layout.addWidget(self._advanced_input)

        layout.addLayout(expr_layout)

        self._validation_label = QLabel()
        self._validation_label.setStyleSheet(f"color: {THEME_V2.success};")
        layout.addWidget(self._validation_label)

        layout.addStretch()

    def _connect_signals(self) -> None:
        """Connect UI signals."""
        self._frequency_combo.currentIndexChanged.connect(self._on_simple_changed)
        self._hour_spin.valueChanged.connect(self._on_simple_changed)
        self._minute_spin.valueChanged.connect(self._on_simple_changed)
        self._day_of_month_spin.valueChanged.connect(self._on_simple_changed)

        for cb in self._day_checkboxes:
            cb.stateChanged.connect(self._on_simple_changed)

        self._advanced_input.textChanged.connect(self._on_advanced_changed)
        self._tab_widget.currentChanged.connect(self._on_tab_changed)

    @Slot(int)
    def _on_simple_changed(self, index: int | None = None) -> None:
        """Handle simple mode changes."""
        if self._tab_widget.currentIndex() != 0:
            return

        self._current_expression = self._build_expression_from_simple()
        self._expression_display.setText(self._current_expression)
        self._update_preview()

    @Slot()
    def _on_advanced_changed(self) -> None:
        """Handle advanced mode changes."""
        if self._tab_widget.currentIndex() != 1:
            return

        expr = self._advanced_input.text().strip()
        if self._validate_expression(expr):
            self._current_expression = expr
            self._expression_display.setText(self._current_expression)
            self._validation_label.setText("Valid expression")
            self._validation_label.setStyleSheet(f"color: {THEME_V2.success};")
        else:
            self._validation_label.setText("Invalid expression")
            self._validation_label.setStyleSheet(f"color: {THEME_V2.error};")

        self._update_preview()

    @Slot(int)
    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change."""
        if index == 0:
            self._on_simple_changed()
        else:
            self._advanced_input.setText(self._current_expression)
            self._on_advanced_changed()

    def _build_expression_from_simple(self) -> str:
        """Build cron expression from simple mode inputs."""
        freq = self._frequency_combo.currentData()
        minute = self._minute_spin.value()
        hour = self._hour_spin.value()

        if freq == "minute":
            return "* * * * *"

        elif freq == "hourly":
            return f"{minute} * * * *"

        elif freq == "daily":
            return f"{minute} {hour} * * *"

        elif freq == "weekly":
            days = []
            day_map = {0: "1", 1: "2", 2: "3", 3: "4", 4: "5", 5: "6", 6: "0"}
            for i, cb in enumerate(self._day_checkboxes):
                if cb.isChecked():
                    days.append(day_map[i])
            if not days:
                days = ["1"]
            return f"{minute} {hour} * * {','.join(days)}"

        elif freq == "monthly":
            dom = self._day_of_month_spin.value()
            return f"{minute} {hour} {dom} * *"

        return "0 0 * * *"

    def _validate_expression(self, expr: str) -> bool:
        """Validate a cron expression."""
        parts = expr.split()
        if len(parts) != 5:
            return False

        ranges = [
            (0, 59),
            (0, 23),
            (1, 31),
            (1, 12),
            (0, 7),
        ]

        for i, part in enumerate(parts):
            if not self._validate_field(part, ranges[i]):
                return False

        return True

    def _validate_field(self, field: str, valid_range: tuple) -> bool:
        """Validate a single cron field."""
        min_val, max_val = valid_range

        if field == "*":
            return True

        if field.startswith("*/"):
            try:
                step = int(field[2:])
                return step > 0 and step <= max_val
            except ValueError:
                return False

        for part in field.split(","):
            if "-" in part:
                try:
                    start, end = part.split("-")
                    start_val = int(start)
                    end_val = int(end)
                    if not (min_val <= start_val <= max_val):
                        return False
                    if not (min_val <= end_val <= max_val):
                        return False
                except ValueError:
                    return False
            else:
                try:
                    val = int(part)
                    if not (min_val <= val <= max_val):
                        return False
                except ValueError:
                    return False

        return True

    def _load_expression(self, expr: str) -> None:
        """Load an expression into the UI."""
        if not self._validate_expression(expr):
            return

        parts = expr.split()
        minute, hour, dom, month, dow = parts

        if expr == "* * * * *":
            self._frequency_combo.setCurrentIndex(0)

        elif hour == "*" and dom == "*" and month == "*" and dow == "*":
            self._frequency_combo.setCurrentIndex(1)
            try:
                self._minute_spin.setValue(int(minute))
            except ValueError:
                pass

        elif dom == "*" and month == "*" and dow == "*":
            self._frequency_combo.setCurrentIndex(2)
            try:
                self._minute_spin.setValue(int(minute))
                self._hour_spin.setValue(int(hour))
            except ValueError:
                pass

        elif dom == "*" and month == "*":
            self._frequency_combo.setCurrentIndex(3)
            try:
                self._minute_spin.setValue(int(minute))
                self._hour_spin.setValue(int(hour))
            except ValueError:
                pass

            for cb in self._day_checkboxes:
                cb.setChecked(False)

            day_map = {"0": 6, "1": 0, "2": 1, "3": 2, "4": 3, "5": 4, "6": 5, "7": 6}
            for day in dow.split(","):
                if "-" in day:
                    try:
                        start, end = day.split("-")
                        for d in range(int(start), int(end) + 1):
                            idx = day_map.get(str(d % 7))
                            if idx is not None:
                                self._day_checkboxes[idx].setChecked(True)
                    except ValueError:
                        pass
                else:
                    idx = day_map.get(day)
                    if idx is not None:
                        self._day_checkboxes[idx].setChecked(True)

        elif month == "*" and dow == "*":
            self._frequency_combo.setCurrentIndex(4)
            try:
                self._minute_spin.setValue(int(minute))
                self._hour_spin.setValue(int(hour))
                self._day_of_month_spin.setValue(int(dom))
            except ValueError:
                pass

    def _update_preview(self) -> None:
        """Update the next runs preview."""
        self._preview_list.clear()

        next_runs = self._calculate_next_runs(self._current_expression, 10)

        if not next_runs:
            item = QListWidgetItem("Unable to calculate next runs")
            item.setForeground(Qt.GlobalColor.red)
            self._preview_list.addItem(item)
            return

        for i, run_time in enumerate(next_runs, 1):
            text = f"{i}. {run_time.strftime('%Y-%m-%d %H:%M:%S')}"
            item = QListWidgetItem(text)
            self._preview_list.addItem(item)

    def _calculate_next_runs(self, expr: str, count: int) -> list[datetime]:
        """Calculate the next N run times for a cron expression."""
        if not self._validate_expression(expr):
            return []

        parts = expr.split()
        minute_spec, hour_spec, dom_spec, month_spec, dow_spec = parts

        runs = []
        current = datetime.now().replace(second=0, microsecond=0)

        for _ in range(count * 1440):
            current += timedelta(minutes=1)

            if not self._matches_field(current.minute, minute_spec, 0, 59):
                continue
            if not self._matches_field(current.hour, hour_spec, 0, 23):
                continue
            if not self._matches_field(current.day, dom_spec, 1, 31):
                continue
            if not self._matches_field(current.month, month_spec, 1, 12):
                continue

            dow = current.weekday()
            dow_cron = (dow + 1) % 7

            if dow_spec != "*" and not self._matches_field(dow_cron, dow_spec, 0, 7):
                if not self._matches_field(
                    dow_cron + 7 if dow_cron == 0 else dow_cron, dow_spec, 0, 7
                ):
                    continue

            runs.append(current)
            if len(runs) >= count:
                break

        return runs

    def _matches_field(self, value: int, spec: str, min_val: int, max_val: int) -> bool:
        """Check if a value matches a cron field spec."""
        if spec == "*":
            return True

        if spec.startswith("*/"):
            try:
                step = int(spec[2:])
                return value % step == 0
            except ValueError:
                return False

        for part in spec.split(","):
            if "-" in part:
                try:
                    start, end = part.split("-")
                    if int(start) <= value <= int(end):
                        return True
                except ValueError:
                    pass
            else:
                try:
                    if int(part) == value:
                        return True
                except ValueError:
                    pass

        return False

    def get_expression(self) -> str:
        """Get the current cron expression."""
        return self._current_expression

