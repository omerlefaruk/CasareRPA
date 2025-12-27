"""
Cron Builder Dialog for Schedule Management.

Visual cron expression builder with:
- Simple mode (dropdowns for common patterns)
- Advanced mode (raw expression editing)
- Preview of next N runs
"""

from datetime import datetime, timedelta

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
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

from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS
from casare_rpa.presentation.canvas.theme_system.helpers import (
    set_margins,
    set_min_size,
    set_spacing,
)


class CronBuilderDialog(QDialog):
    """
    Dialog for building cron expressions visually.

    Provides:
    - Simple mode: Dropdowns for frequency, time, day selection
    - Advanced mode: Raw cron expression with validation
    - Preview: Shows next 10 scheduled runs
    """

    expression_changed = Signal(str)

    def __init__(
        self,
        initial_expression: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._initial_expression = initial_expression
        self._current_expression = initial_expression or "0 0 * * *"
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

        if initial_expression:
            self._load_expression(initial_expression)

        self._update_preview()

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle("Cron Schedule Builder")
        set_min_size(self, TOKENS.sizes.dialog_md_width, TOKENS.sizes.dialog_height_lg)

        layout = QVBoxLayout(self)
        set_margins(layout, TOKENS.margin.dialog)
        set_spacing(layout, TOKENS.spacing.md)

        self._tab_widget = QTabWidget()

        simple_tab = QWidget()
        self._setup_simple_tab(simple_tab)
        self._tab_widget.addTab(simple_tab, "Simple")

        advanced_tab = QWidget()
        self._setup_advanced_tab(advanced_tab)
        self._tab_widget.addTab(advanced_tab, "Advanced")

        layout.addWidget(self._tab_widget)

        expression_group = QGroupBox("Cron Expression")
        expression_layout = QHBoxLayout(expression_group)

        self._expression_display = QLineEdit()
        self._expression_display.setReadOnly(True)
        self._expression_display.setStyleSheet(
            f"font-family: monospace; font-size: {TOKENS.typography.body}px;"
        )
        self._expression_display.setText(self._current_expression)
        expression_layout.addWidget(self._expression_display)

        layout.addWidget(expression_group)

        preview_group = QGroupBox("Next 10 Runs")
        preview_layout = QVBoxLayout(preview_group)

        self._preview_list = QListWidget()
        self._preview_list.setMaximumHeight(TOKENS.sizes.dialog_height_sm)
        self._preview_list.setAlternatingRowColors(True)
        preview_layout.addWidget(self._preview_list)

        layout.addWidget(preview_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _setup_simple_tab(self, tab: QWidget) -> None:
        """Set up the simple mode tab."""
        layout = QVBoxLayout(tab)
        set_margins(layout, TOKENS.margin.compact)
        set_spacing(layout, TOKENS.spacing.lg)

        freq_group = QGroupBox("Frequency")
        freq_layout = QHBoxLayout(freq_group)

        freq_layout.addWidget(QLabel("Run:"))
        self._frequency_combo = QComboBox()
        self._frequency_combo.addItem("Every minute", "minute")
        self._frequency_combo.addItem("Hourly", "hourly")
        self._frequency_combo.addItem("Daily", "daily")
        self._frequency_combo.addItem("Weekly", "weekly")
        self._frequency_combo.addItem("Monthly", "monthly")
        self._frequency_combo.setCurrentIndex(2)
        freq_layout.addWidget(self._frequency_combo)
        freq_layout.addStretch()

        layout.addWidget(freq_group)

        time_group = QGroupBox("Time")
        time_layout = QGridLayout(time_group)

        time_layout.addWidget(QLabel("Hour:"), 0, 0)
        self._hour_spin = QSpinBox()
        self._hour_spin.setRange(0, 23)
        self._hour_spin.setValue(9)
        time_layout.addWidget(self._hour_spin, 0, 1)

        time_layout.addWidget(QLabel("Minute:"), 0, 2)
        self._minute_spin = QSpinBox()
        self._minute_spin.setRange(0, 59)
        self._minute_spin.setValue(0)
        time_layout.addWidget(self._minute_spin, 0, 3)

        time_layout.setColumnStretch(4, 1)

        layout.addWidget(time_group)

        days_group = QGroupBox("Days of Week (for Weekly)")
        days_layout = QHBoxLayout(days_group)

        self._day_checkboxes = []
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            cb = QCheckBox(day)
            if day == "Mon":
                cb.setChecked(True)
            self._day_checkboxes.append(cb)
            days_layout.addWidget(cb)

        layout.addWidget(days_group)

        dom_group = QGroupBox("Day of Month (for Monthly)")
        dom_layout = QHBoxLayout(dom_group)

        dom_layout.addWidget(QLabel("Day:"))
        self._day_of_month_spin = QSpinBox()
        self._day_of_month_spin.setRange(1, 31)
        self._day_of_month_spin.setValue(1)
        dom_layout.addWidget(self._day_of_month_spin)
        dom_layout.addStretch()

        layout.addWidget(dom_group)

        layout.addStretch()

    def _setup_advanced_tab(self, tab: QWidget) -> None:
        """Set up the advanced mode tab."""
        layout = QVBoxLayout(tab)
        set_margins(layout, TOKENS.margin.compact)
        set_spacing(layout, TOKENS.spacing.lg)

        info_label = QLabel(
            "Enter a cron expression with 5 fields:\n"
            "minute hour day-of-month month day-of-week\n\n"
            "Examples:\n"
            "  0 9 * * *    - Every day at 9:00 AM\n"
            "  */15 * * * * - Every 15 minutes\n"
            "  0 0 1 * *    - First day of each month at midnight\n"
            "  0 9 * * 1-5  - Weekdays at 9:00 AM"
        )
        info_label.setStyleSheet(f"font-family: monospace; padding: {TOKENS.spacing.sm}px;")
        layout.addWidget(info_label)

        expr_layout = QHBoxLayout()
        expr_layout.addWidget(QLabel("Expression:"))
        self._advanced_input = QLineEdit()
        self._advanced_input.setPlaceholderText("0 9 * * *")
        self._advanced_input.setText(self._current_expression)
        expr_layout.addWidget(self._advanced_input)

        layout.addLayout(expr_layout)

        self._validation_label = QLabel()
        self._validation_label.setStyleSheet(f"color: {THEME.success};")
        layout.addWidget(self._validation_label)

        layout.addStretch()

    def _apply_styles(self) -> None:
        """Apply theme styles."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {THEME.bg_canvas};
            }}
            QLabel {{
                color: {THEME.text_primary};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.md}px;
                margin-top: {TOKENS.spacing.md}px;
                padding-top: {TOKENS.spacing.md}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 {TOKENS.spacing.sm}px;
                color: {THEME.text_secondary};
            }}
            QComboBox, QSpinBox, QLineEdit {{
                background-color: {THEME.bg_surface};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.md}px;
                padding: {TOKENS.spacing.sm}px;
                min-width: 80px;
            }}
            QComboBox:focus, QSpinBox:focus, QLineEdit:focus {{
                border-color: {THEME.border_focus};
            }}
            QCheckBox {{
                color: {THEME.text_primary};
            }}
            QListWidget {{
                background-color: {THEME.bg_surface};
                border: 1px solid {THEME.border};
            }}
            QListWidget::item {{
                padding: {TOKENS.spacing.xs}px {TOKENS.spacing.sm}px;
            }}
        """)

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

    def _on_simple_changed(self) -> None:
        """Handle simple mode changes."""
        if self._tab_widget.currentIndex() != 0:
            return

        self._current_expression = self._build_expression_from_simple()
        self._expression_display.setText(self._current_expression)
        self._update_preview()

    def _on_advanced_changed(self) -> None:
        """Handle advanced mode changes."""
        if self._tab_widget.currentIndex() != 1:
            return

        expr = self._advanced_input.text().strip()
        if self._validate_expression(expr):
            self._current_expression = expr
            self._expression_display.setText(self._current_expression)
            self._validation_label.setText("Valid expression")
            self._validation_label.setStyleSheet(f"color: {THEME.success};")
        else:
            self._validation_label.setText("Invalid expression")
            self._validation_label.setStyleSheet(f"color: {THEME.error};")

        self._update_preview()

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
