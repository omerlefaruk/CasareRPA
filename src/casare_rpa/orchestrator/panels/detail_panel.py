"""
Detail panel - Right sidebar showing job/robot details and logs.
Tabbed interface for Properties, Logs, and Output.
"""

from typing import Optional, Dict
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QPlainTextEdit,
    QFrame,
    QScrollArea,
    QProgressBar,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QTextCharFormat, QSyntaxHighlighter

from ..theme import THEME, get_status_color, get_priority_color


class PropertyRow(QWidget):
    """Single property row with label and value."""

    def __init__(self, label: str, value: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        self._label = QLabel(label)
        self._label.setStyleSheet(f"""
            color: {THEME.text_muted};
            font-size: 11px;
            min-width: 80px;
        """)
        layout.addWidget(self._label)

        self._value = QLabel(value)
        self._value.setStyleSheet(f"""
            color: {THEME.text_primary};
            font-size: 11px;
        """)
        self._value.setWordWrap(True)
        layout.addWidget(self._value, 1)

    def set_value(self, value: str, color: Optional[str] = None):
        self._value.setText(value)
        if color:
            self._value.setStyleSheet(f"color: {color}; font-size: 11px;")


class PropertiesTab(QScrollArea):
    """Properties tab showing job/robot details."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(f"""
            QScrollArea {{
                background-color: {THEME.bg_panel};
                border: none;
            }}
        """)

        self._content = QWidget()
        self._layout = QVBoxLayout(self._content)
        self._layout.setContentsMargins(12, 12, 12, 12)
        self._layout.setSpacing(4)

        self._props: Dict[str, PropertyRow] = {}
        self.setWidget(self._content)

    def set_job(self, job: Optional[Dict]):
        """Display job properties."""
        self._clear()

        if not job:
            self._add_empty_state("No job selected")
            return

        # Header
        self._add_section_header("Job Information")

        # Basic info
        self._add_property("ID", job.get("id", "")[:8] + "...")
        self._add_property("Name", job.get("workflow_name", "Unknown"))

        status = job.get("status", "pending")
        self._add_property("Status", status.capitalize(), get_status_color(status))

        priority = job.get("priority", 1)
        priority_names = {0: "Low", 1: "Normal", 2: "High", 3: "Critical"}
        self._add_property(
            "Priority",
            priority_names.get(priority, "Normal"),
            get_priority_color(priority),
        )

        # Progress section
        self._add_section_header("Progress")

        progress = job.get("progress", 0)
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(progress)
        progress_bar.setFormat(f"{progress}%")
        progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {THEME.progress_bg};
                border: 1px solid {THEME.border_dark};
                border-radius: 3px;
                height: 20px;
                text-align: center;
                color: {THEME.text_primary};
                font-weight: 600;
            }}
            QProgressBar::chunk {{
                background-color: {get_status_color(status)};
            }}
        """)
        self._layout.addWidget(progress_bar)

        self._add_property("Current Node", job.get("current_node", "-"))

        # Timing section
        self._add_section_header("Timing")

        if job.get("started_at"):
            started = job["started_at"]
            if hasattr(started, "strftime"):
                started = started.strftime("%Y-%m-%d %H:%M:%S")
            self._add_property("Started", str(started))
        else:
            self._add_property("Started", "-")

        if job.get("completed_at"):
            completed = job["completed_at"]
            if hasattr(completed, "strftime"):
                completed = completed.strftime("%Y-%m-%d %H:%M:%S")
            self._add_property("Completed", str(completed))

        duration_ms = job.get("duration_ms", 0)
        if duration_ms:
            duration = f"{duration_ms / 1000:.1f}s"
        else:
            duration = "-"
        self._add_property("Duration", duration)

        # Assignment section
        self._add_section_header("Assignment")
        self._add_property("Robot", job.get("robot_name", "-"))
        self._add_property(
            "Robot ID",
            job.get("robot_id", "-")[:8] + "..." if job.get("robot_id") else "-",
        )

        # Error info (if any)
        if job.get("error_message"):
            self._add_section_header("Error")
            error_label = QLabel(job["error_message"])
            error_label.setWordWrap(True)
            error_label.setStyleSheet(f"""
                color: {THEME.status_error};
                font-size: 11px;
                background-color: {THEME.status_error}20;
                padding: 8px;
                border: 1px solid {THEME.status_error}40;
                border-radius: 3px;
            """)
            self._layout.addWidget(error_label)

        self._layout.addStretch()

    def set_robot(self, robot: Optional[Dict]):
        """Display robot properties."""
        self._clear()

        if not robot:
            self._add_empty_state("No robot selected")
            return

        # Header
        self._add_section_header("Robot Information")

        self._add_property("ID", robot.get("id", "")[:8] + "...")
        self._add_property("Name", robot.get("name", "Unknown"))

        status = robot.get("status", "offline")
        self._add_property("Status", status.capitalize(), get_status_color(status))

        self._add_property("Environment", robot.get("environment", "default"))

        # Capacity section
        self._add_section_header("Capacity")

        current = robot.get("current_jobs", 0)
        max_jobs = robot.get("max_concurrent_jobs", 1)
        utilization = (current / max_jobs * 100) if max_jobs > 0 else 0

        self._add_property("Current Jobs", f"{current} / {max_jobs}")

        util_bar = QProgressBar()
        util_bar.setRange(0, 100)
        util_bar.setValue(int(utilization))
        util_bar.setFormat(f"{utilization:.0f}% utilized")
        util_color = THEME.status_online if utilization < 80 else THEME.status_busy
        util_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {THEME.progress_bg};
                border: 1px solid {THEME.border_dark};
                border-radius: 3px;
                height: 20px;
                text-align: center;
                color: {THEME.text_primary};
            }}
            QProgressBar::chunk {{
                background-color: {util_color};
            }}
        """)
        self._layout.addWidget(util_bar)

        # Timing section
        self._add_section_header("Activity")

        if robot.get("last_seen"):
            last_seen = robot["last_seen"]
            if hasattr(last_seen, "strftime"):
                last_seen = last_seen.strftime("%Y-%m-%d %H:%M:%S")
            self._add_property("Last Seen", str(last_seen))
        else:
            self._add_property("Last Seen", "-")

        # Tags
        if robot.get("tags"):
            self._add_section_header("Tags")
            tags_text = ", ".join(robot["tags"])
            tags_label = QLabel(tags_text)
            tags_label.setWordWrap(True)
            tags_label.setStyleSheet(f"color: {THEME.text_secondary}; font-size: 11px;")
            self._layout.addWidget(tags_label)

        self._layout.addStretch()

    def _clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._props.clear()

    def _add_section_header(self, text: str):
        header = QLabel(text)
        header.setStyleSheet(f"""
            color: {THEME.text_secondary};
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            padding-top: 12px;
            padding-bottom: 4px;
            border-bottom: 1px solid {THEME.border_dark};
        """)
        self._layout.addWidget(header)

    def _add_property(self, label: str, value: str, color: Optional[str] = None):
        row = PropertyRow(label, value)
        if color:
            row.set_value(value, color)
        self._props[label] = row
        self._layout.addWidget(row)

    def _add_empty_state(self, text: str):
        label = QLabel(text)
        label.setStyleSheet(f"""
            color: {THEME.text_muted};
            font-size: 12px;
            padding: 40px;
        """)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(label)
        self._layout.addStretch()


class LogHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for log output."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._formats = {}

        # Error format (red)
        error_fmt = QTextCharFormat()
        error_fmt.setForeground(QColor(THEME.status_error))
        self._formats["error"] = error_fmt

        # Warning format (orange)
        warning_fmt = QTextCharFormat()
        warning_fmt.setForeground(QColor(THEME.status_warning))
        self._formats["warning"] = warning_fmt

        # Success format (green)
        success_fmt = QTextCharFormat()
        success_fmt.setForeground(QColor(THEME.status_online))
        self._formats["success"] = success_fmt

        # Info format (blue)
        info_fmt = QTextCharFormat()
        info_fmt.setForeground(QColor(THEME.accent_secondary))
        self._formats["info"] = info_fmt

        # Timestamp format (gray)
        timestamp_fmt = QTextCharFormat()
        timestamp_fmt.setForeground(QColor(THEME.text_muted))
        self._formats["timestamp"] = timestamp_fmt

    def highlightBlock(self, text: str):
        text_lower = text.lower()

        # Highlight based on log level
        if "error" in text_lower or "exception" in text_lower or "failed" in text_lower:
            self.setFormat(0, len(text), self._formats["error"])
        elif "warning" in text_lower or "warn" in text_lower:
            self.setFormat(0, len(text), self._formats["warning"])
        elif "success" in text_lower or "completed" in text_lower:
            self.setFormat(0, len(text), self._formats["success"])
        elif "info" in text_lower:
            self.setFormat(0, len(text), self._formats["info"])

        # Highlight timestamps (HH:MM:SS pattern)
        import re

        for match in re.finditer(r"\d{2}:\d{2}:\d{2}", text):
            self.setFormat(
                match.start(), match.end() - match.start(), self._formats["timestamp"]
            )


class LogsTab(QWidget):
    """Logs tab showing job output and logs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(8, 4, 8, 4)
        toolbar.setSpacing(8)

        # Auto-scroll toggle
        self._auto_scroll = QPushButton("Auto-scroll")
        self._auto_scroll.setCheckable(True)
        self._auto_scroll.setChecked(True)
        self._auto_scroll.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {THEME.border};
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 10px;
                color: {THEME.text_secondary};
            }}
            QPushButton:checked {{
                background-color: {THEME.accent_primary};
                border-color: {THEME.accent_primary};
                color: {THEME.text_primary};
            }}
        """)
        toolbar.addWidget(self._auto_scroll)

        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_logs)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {THEME.border};
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 10px;
                color: {THEME.text_secondary};
            }}
            QPushButton:hover {{
                background-color: {THEME.bg_hover};
            }}
        """)
        toolbar.addWidget(clear_btn)

        toolbar.addStretch()

        toolbar_widget = QWidget()
        toolbar_widget.setLayout(toolbar)
        toolbar_widget.setStyleSheet(f"""
            background-color: {THEME.bg_header};
            border-bottom: 1px solid {THEME.border_dark};
        """)
        layout.addWidget(toolbar_widget)

        # Log text area
        self._log_view = QPlainTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._log_view.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {THEME.bg_darkest};
                color: {THEME.text_primary};
                border: none;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 11px;
                padding: 8px;
            }}
        """)

        # Apply syntax highlighter
        self._highlighter = LogHighlighter(self._log_view.document())

        layout.addWidget(self._log_view, 1)

    def set_logs(self, logs: str):
        """Set log content."""
        self._log_view.setPlainText(logs)
        if self._auto_scroll.isChecked():
            self._log_view.verticalScrollBar().setValue(
                self._log_view.verticalScrollBar().maximum()
            )

    def append_log(self, line: str):
        """Append a log line."""
        self._log_view.appendPlainText(line)
        if self._auto_scroll.isChecked():
            self._log_view.verticalScrollBar().setValue(
                self._log_view.verticalScrollBar().maximum()
            )

    def _clear_logs(self):
        self._log_view.clear()


class OutputTab(QWidget):
    """Output tab showing job result/output data."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tree view for structured output
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Key", "Value"])
        self._tree.setAlternatingRowColors(True)
        self._tree.header().setStretchLastSection(True)
        self._tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {THEME.bg_panel};
                alternate-background-color: {THEME.bg_row_alt};
                border: none;
            }}
            QTreeWidget::item {{
                padding: 4px;
            }}
        """)
        layout.addWidget(self._tree)

    def set_output(self, data: Optional[Dict]):
        """Display output data as tree."""
        self._tree.clear()

        if not data:
            item = QTreeWidgetItem(["No output data", ""])
            item.setForeground(0, QColor(THEME.text_muted))
            self._tree.addTopLevelItem(item)
            return

        self._add_dict_to_tree(data, self._tree.invisibleRootItem())
        self._tree.expandAll()

    def _add_dict_to_tree(self, data: Dict, parent_item):
        for key, value in data.items():
            if isinstance(value, dict):
                item = QTreeWidgetItem([str(key), ""])
                item.setForeground(0, QColor(THEME.accent_secondary))
                parent_item.addChild(item)
                self._add_dict_to_tree(value, item)
            elif isinstance(value, list):
                item = QTreeWidgetItem([str(key), f"[{len(value)} items]"])
                item.setForeground(0, QColor(THEME.accent_secondary))
                item.setForeground(1, QColor(THEME.text_muted))
                parent_item.addChild(item)
                for i, v in enumerate(value):
                    if isinstance(v, dict):
                        child = QTreeWidgetItem([f"[{i}]", ""])
                        item.addChild(child)
                        self._add_dict_to_tree(v, child)
                    else:
                        child = QTreeWidgetItem([f"[{i}]", str(v)])
                        item.addChild(child)
            else:
                item = QTreeWidgetItem([str(key), str(value)])
                parent_item.addChild(item)


class DetailPanel(QWidget):
    """
    Right detail panel with tabbed interface.
    Shows Properties, Logs, and Output for selected job/robot.
    """

    action_requested = Signal(str, str)  # item_id, action

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_job: Optional[Dict] = None
        self._current_robot: Optional[Dict] = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {THEME.bg_panel};
            }}
        """)

        # Header
        self._header = QLabel("Details")
        self._header.setStyleSheet(f"""
            QLabel {{
                background-color: {THEME.bg_header};
                color: {THEME.text_secondary};
                padding: 8px 12px;
                font-weight: 600;
                font-size: 11px;
                text-transform: uppercase;
                border-bottom: 1px solid {THEME.border_dark};
            }}
        """)
        layout.addWidget(self._header)

        # Tab widget
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                background-color: {THEME.bg_panel};
                border: none;
            }}
            QTabBar::tab {{
                background-color: {THEME.bg_header};
                color: {THEME.text_secondary};
                padding: 6px 16px;
                border: none;
                border-right: 1px solid {THEME.border_dark};
                font-size: 11px;
            }}
            QTabBar::tab:selected {{
                background-color: {THEME.bg_panel};
                color: {THEME.text_primary};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {THEME.bg_hover};
            }}
        """)

        # Create tabs
        self._props_tab = PropertiesTab()
        self._logs_tab = LogsTab()
        self._output_tab = OutputTab()

        self._tabs.addTab(self._props_tab, "Properties")
        self._tabs.addTab(self._logs_tab, "Logs")
        self._tabs.addTab(self._output_tab, "Output")

        layout.addWidget(self._tabs, 1)

        # Action buttons
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(8, 8, 8, 8)
        actions_layout.setSpacing(8)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(lambda: self._emit_action("cancel"))
        self._cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME.bg_light};
                border: 1px solid {THEME.border};
                border-radius: 3px;
                padding: 6px 16px;
                color: {THEME.text_primary};
            }}
            QPushButton:hover {{
                background-color: {THEME.bg_hover};
            }}
        """)
        actions_layout.addWidget(self._cancel_btn)

        self._retry_btn = QPushButton("Retry")
        self._retry_btn.clicked.connect(lambda: self._emit_action("retry"))
        self._retry_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME.accent_primary};
                border: none;
                border-radius: 3px;
                padding: 6px 16px;
                color: {THEME.text_primary};
            }}
            QPushButton:hover {{
                background-color: #0086e6;
            }}
        """)
        actions_layout.addWidget(self._retry_btn)

        actions_layout.addStretch()

        actions_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {THEME.bg_header};
                border-top: 1px solid {THEME.border_dark};
            }}
        """)
        layout.addWidget(actions_widget)

    def set_job(self, job: Optional[Dict]):
        """Display job details."""
        self._current_job = job
        self._current_robot = None

        if job:
            self._header.setText(f"Job: {job.get('workflow_name', 'Unknown')}")
            self._props_tab.set_job(job)
            self._logs_tab.set_logs(job.get("logs", ""))
            self._output_tab.set_output(job.get("result"))

            # Show/hide action buttons based on status
            status = job.get("status", "").lower()
            self._cancel_btn.setVisible(status in ("running", "pending", "queued"))
            self._retry_btn.setVisible(status in ("failed", "cancelled", "timeout"))
        else:
            self._header.setText("Details")
            self._props_tab.set_job(None)
            self._logs_tab.set_logs("")
            self._output_tab.set_output(None)
            self._cancel_btn.setVisible(False)
            self._retry_btn.setVisible(False)

    def set_robot(self, robot: Optional[Dict]):
        """Display robot details."""
        self._current_robot = robot
        self._current_job = None

        if robot:
            self._header.setText(f"Robot: {robot.get('name', 'Unknown')}")
            self._props_tab.set_robot(robot)
            self._logs_tab.set_logs("")  # Robots don't have logs in this view
            self._output_tab.set_output(robot.get("metrics"))
            self._cancel_btn.setVisible(False)
            self._retry_btn.setVisible(False)
        else:
            self._header.setText("Details")
            self._props_tab.set_robot(None)
            self._logs_tab.set_logs("")
            self._output_tab.set_output(None)

    def _emit_action(self, action: str):
        if self._current_job:
            self.action_requested.emit(self._current_job.get("id", ""), action)

    def append_log(self, line: str):
        """Append log line to logs tab."""
        self._logs_tab.append_log(line)
