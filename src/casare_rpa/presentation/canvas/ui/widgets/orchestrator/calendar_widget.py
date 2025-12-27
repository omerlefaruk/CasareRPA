"""
Calendar Widget for Schedule Builder.

Visual calendar for displaying and creating schedules.
Shows scheduled runs with markers and supports day selection.
"""

from datetime import date, timedelta

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QTextCharFormat
from PySide6.QtWidgets import (
    QCalendarWidget,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.domain.orchestrator.entities import Schedule
from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS


class ScheduleCalendarWidget(QWidget):
    """
    Calendar widget for viewing and managing schedules.

    Features:
    - Month view with schedule markers
    - Day selection to see schedules
    - Color-coded by schedule status
    """

    date_selected = Signal(object)
    schedule_clicked = Signal(str)
    create_schedule_requested = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._schedules: list[Schedule] = []
        self._schedule_dates: dict[date, list[Schedule]] = {}
        self._blackout_dates: set[date] = set()
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the calendar UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(8)

        self._prev_btn = QPushButton("<")
        self._prev_btn.setFixedWidth(32)
        header.addWidget(self._prev_btn)

        self._month_label = QLabel()
        self._month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._month_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header.addWidget(self._month_label, stretch=1)

        self._next_btn = QPushButton(">")
        self._next_btn.setFixedWidth(32)
        header.addWidget(self._next_btn)

        self._today_btn = QPushButton("Today")
        header.addWidget(self._today_btn)

        layout.addLayout(header)

        self._calendar = QCalendarWidget()
        self._calendar.setGridVisible(True)
        self._calendar.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        self._calendar.setHorizontalHeaderFormat(
            QCalendarWidget.HorizontalHeaderFormat.ShortDayNames
        )
        self._calendar.setSelectionMode(QCalendarWidget.SelectionMode.SingleSelection)
        self._calendar.setMinimumHeight(250)
        layout.addWidget(self._calendar)

        self._selected_date_label = QLabel("Schedules for selected date:")
        self._selected_date_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        layout.addWidget(self._selected_date_label)

        self._schedule_list = QListWidget()
        self._schedule_list.setMaximumHeight(120)
        self._schedule_list.setAlternatingRowColors(True)
        layout.addWidget(self._schedule_list)

        self._update_month_label()

    def _apply_styles(self) -> None:
        """Apply theme styles."""
        c = THEME
        self.setStyleSheet(f"""
            QCalendarWidget {{
                background-color: {c.bg_elevated};
            }}
            QCalendarWidget QWidget {{
                alternate-background-color: {c.bg_canvas};
            }}
            QCalendarWidget QAbstractItemView:enabled {{
                color: {c.text_primary};
                background-color: {c.bg_elevated};
                selection-background-color: {c.accent};
                selection-color: white;
            }}
            QCalendarWidget QAbstractItemView:disabled {{
                color: {c.text_muted};
            }}
            QCalendarWidget QWidget#qt_calendar_navigationbar {{
                background-color: {c.bg_header};
            }}
            QCalendarWidget QToolButton {{
                color: {c.text_primary};
                background-color: transparent;
                border: none;
                padding: 4px;
            }}
            QCalendarWidget QToolButton:hover {{
                background-color: {c.bg_hover};
                border-radius: 4px;
            }}
            QCalendarWidget QSpinBox {{
                background-color: {c.bg_canvas};
                color: {c.text_primary};
                border: 1px solid {c.border};
            }}
            QListWidget {{
                background-color: {c.bg_elevated};
                border: 1px solid {c.border_dark};
            }}
            QListWidget::item {{
                padding: 6px 8px;
            }}
            QListWidget::item:selected {{
                background-color: {c.bg_selected};
            }}
        """)

    def _connect_signals(self) -> None:
        """Connect UI signals."""
        self._prev_btn.clicked.connect(self._on_prev_month)
        self._next_btn.clicked.connect(self._on_next_month)
        self._today_btn.clicked.connect(self._on_today)
        self._calendar.selectionChanged.connect(self._on_date_selected)
        self._calendar.currentPageChanged.connect(self._on_page_changed)
        self._schedule_list.itemDoubleClicked.connect(self._on_schedule_double_click)

    def _update_month_label(self) -> None:
        """Update the month/year label."""
        current_date = self._calendar.selectedDate()
        month_name = current_date.toString("MMMM yyyy")
        self._month_label.setText(month_name)

    def _on_prev_month(self) -> None:
        """Navigate to previous month."""
        self._calendar.showPreviousMonth()
        self._update_month_label()

    def _on_next_month(self) -> None:
        """Navigate to next month."""
        self._calendar.showNextMonth()
        self._update_month_label()

    def _on_today(self) -> None:
        """Navigate to today."""
        self._calendar.setSelectedDate(QDate.currentDate())
        self._update_month_label()

    def _on_date_selected(self) -> None:
        """Handle date selection."""
        qdate = self._calendar.selectedDate()
        selected = date(qdate.year(), qdate.month(), qdate.day())

        self._selected_date_label.setText(f"Schedules for {selected.strftime('%B %d, %Y')}:")
        self._update_schedule_list(selected)
        self.date_selected.emit(selected)

    def _on_page_changed(self, year: int, month: int) -> None:
        """Handle month/year page change."""
        self._update_month_label()
        self._update_calendar_markers()

    def _on_schedule_double_click(self, item: QListWidgetItem) -> None:
        """Handle schedule double-click."""
        schedule_id = item.data(Qt.ItemDataRole.UserRole)
        if schedule_id:
            self.schedule_clicked.emit(schedule_id)

    def set_schedules(self, schedules: list[Schedule]) -> None:
        """Set the schedules to display."""
        self._schedules = schedules
        self._build_schedule_dates()
        self._update_calendar_markers()
        self._on_date_selected()

    def set_blackout_dates(self, dates: set[date]) -> None:
        """Set blackout dates (no execution)."""
        self._blackout_dates = dates
        self._update_calendar_markers()

    def _build_schedule_dates(self) -> None:
        """Build a map of dates to schedules."""
        self._schedule_dates.clear()

        for schedule in self._schedules:
            if not schedule.enabled:
                continue

            if schedule.next_run:
                d = schedule.next_run.date()
                self._schedule_dates.setdefault(d, []).append(schedule)

            for next_date in self._calculate_next_runs(schedule, 30):
                self._schedule_dates.setdefault(next_date, []).append(schedule)

    def _calculate_next_runs(self, schedule: Schedule, days: int) -> list[date]:
        """Calculate next run dates for a schedule."""
        from casare_rpa.domain.orchestrator.entities import ScheduleFrequency

        runs = []
        today = date.today()

        if schedule.frequency == ScheduleFrequency.ONCE:
            if schedule.next_run:
                runs.append(schedule.next_run.date())

        elif schedule.frequency == ScheduleFrequency.DAILY:
            for i in range(days):
                runs.append(today + timedelta(days=i))

        elif schedule.frequency == ScheduleFrequency.WEEKLY:
            for i in range(days):
                d = today + timedelta(days=i)
                if schedule.next_run and d.weekday() == schedule.next_run.weekday():
                    runs.append(d)

        elif schedule.frequency == ScheduleFrequency.HOURLY:
            for i in range(days):
                runs.append(today + timedelta(days=i))

        elif schedule.frequency == ScheduleFrequency.MONTHLY:
            if schedule.next_run:
                day_of_month = schedule.next_run.day
                for i in range(days // 30 + 2):
                    try:
                        d = today.replace(
                            month=(today.month + i - 1) % 12 + 1,
                            day=day_of_month,
                        )
                        if d >= today:
                            runs.append(d)
                    except ValueError:
                        pass

        return runs[:30]

    def _update_calendar_markers(self) -> None:
        """Update calendar date formatting with schedule markers."""
        normal_format = QTextCharFormat()

        scheduled_format = QTextCharFormat()
        scheduled_format.setBackground(QBrush(QColor(THEME.bg_selected)))

        blackout_format = QTextCharFormat()
        blackout_format.setBackground(QBrush(QColor(THEME.error_bg)))
        blackout_format.setForeground(QBrush(QColor(THEME.error)))

        for i in range(1, 32):
            for m in range(1, 13):
                try:
                    self._calendar.setDateTextFormat(
                        QDate(self._calendar.yearShown(), m, i),
                        normal_format,
                    )
                except Exception:
                    pass

        for d, schedules in self._schedule_dates.items():
            if schedules:
                qdate = QDate(d.year, d.month, d.day)
                if d in self._blackout_dates:
                    self._calendar.setDateTextFormat(qdate, blackout_format)
                else:
                    self._calendar.setDateTextFormat(qdate, scheduled_format)

        for d in self._blackout_dates:
            if d not in self._schedule_dates:
                qdate = QDate(d.year, d.month, d.day)
                self._calendar.setDateTextFormat(qdate, blackout_format)

    def _update_schedule_list(self, selected_date: date) -> None:
        """Update the schedule list for selected date."""
        self._schedule_list.clear()

        schedules = self._schedule_dates.get(selected_date, [])

        if not schedules:
            item = QListWidgetItem("No schedules for this date")
            item.setForeground(QColor(THEME.text_disabled))
            self._schedule_list.addItem(item)
            return

        for schedule in schedules:
            item = QListWidgetItem(f"{schedule.name} ({schedule.frequency.value})")
            item.setData(Qt.ItemDataRole.UserRole, schedule.id)

            if not schedule.enabled:
                item.setForeground(QColor("#6B6B6B"))
            elif selected_date in self._blackout_dates:
                item.setForeground(QColor(THEME.error))
                item.setText(f"{schedule.name} (BLACKOUT)")

            self._schedule_list.addItem(item)
