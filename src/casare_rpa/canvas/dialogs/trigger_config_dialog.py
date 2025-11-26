"""
CasareRPA - Trigger Configuration Dialog

Dynamic dialog for configuring trigger settings based on trigger type.
Generates form fields from the trigger's JSON schema.
"""

import uuid
from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QPushButton,
    QDialogButtonBox,
    QScrollArea,
    QWidget,
    QFrame,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..theme import THEME
from ...triggers.base import TriggerType
from ...triggers.registry import get_trigger_registry


# Field type hints for better form generation
FIELD_HINTS = {
    # Webhook
    "secret_key": {"widget": "password", "placeholder": "API key or secret"},
    "jwt_secret": {"widget": "password", "placeholder": "JWT signing secret"},
    "allowed_ips": {"widget": "list", "placeholder": "IP address"},
    "expected_headers": {"widget": "key_value", "placeholder": "Header name"},

    # Scheduled
    "cron_expression": {"placeholder": "e.g., 0 9 * * MON-FRI (9am weekdays)"},
    "interval_seconds": {"min": 1, "max": 86400 * 365},
    "timezone": {"placeholder": "e.g., America/New_York"},

    # File Watch
    "watch_paths": {"widget": "list", "placeholder": "Path to watch"},
    "patterns": {"widget": "list", "placeholder": "e.g., *.csv, *.xlsx"},
    "ignore_patterns": {"widget": "list", "placeholder": "e.g., *.tmp"},

    # Email
    "imap_server": {"placeholder": "e.g., imap.gmail.com"},
    "email_address": {"placeholder": "your@email.com"},
    "email_password": {"widget": "password"},
    "from_filter": {"widget": "list", "placeholder": "sender@domain.com"},
    "subject_pattern": {"placeholder": "Regex pattern for subject"},
    "body_pattern": {"placeholder": "Regex pattern for body"},

    # App Event
    "event_name": {"placeholder": "e.g., window_created, file_downloaded"},
    "process_filter": {"widget": "list", "placeholder": "e.g., chrome.exe"},
    "window_title_pattern": {"placeholder": "Regex for window title"},

    # Error
    "source_scenario_ids": {"widget": "list", "placeholder": "Scenario ID"},
    "error_types": {"widget": "list", "placeholder": "Error type"},
    "error_pattern": {"placeholder": "Regex pattern for error message"},

    # Workflow Call
    "call_alias": {"placeholder": "e.g., process_invoice"},
    "allowed_callers": {"widget": "list", "placeholder": "Scenario ID"},

    # Chat
    "message_pattern": {"placeholder": "Regex pattern for messages"},
    "channel_filter": {"widget": "list", "placeholder": "Channel name or ID"},
    "user_filter": {"widget": "list", "placeholder": "Username or ID"},

    # Form
    "form_id": {"placeholder": "Unique form identifier"},
    "required_fields": {"widget": "list", "placeholder": "Field name"},
    "redirect_url": {"placeholder": "https://example.com/thank-you"},
    "success_message": {"placeholder": "Thank you for your submission!"},
}


class ListEditorWidget(QWidget):
    """Widget for editing a list of strings."""

    def __init__(
        self,
        placeholder: str = "",
        parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self._placeholder = placeholder
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # List
        self._list = QListWidget()
        self._list.setMaximumHeight(100)
        layout.addWidget(self._list)

        # Input row
        input_row = QHBoxLayout()
        input_row.setSpacing(4)

        self._input = QLineEdit()
        self._input.setPlaceholderText(self._placeholder)
        self._input.returnPressed.connect(self._add_item)
        input_row.addWidget(self._input)

        add_btn = QPushButton("+")
        add_btn.setFixedWidth(30)
        add_btn.clicked.connect(self._add_item)
        input_row.addWidget(add_btn)

        remove_btn = QPushButton("-")
        remove_btn.setFixedWidth(30)
        remove_btn.clicked.connect(self._remove_item)
        input_row.addWidget(remove_btn)

        layout.addLayout(input_row)

    def _add_item(self) -> None:
        text = self._input.text().strip()
        if text:
            self._list.addItem(text)
            self._input.clear()

    def _remove_item(self) -> None:
        current = self._list.currentRow()
        if current >= 0:
            self._list.takeItem(current)

    def get_value(self) -> List[str]:
        return [self._list.item(i).text() for i in range(self._list.count())]

    def set_value(self, values: List[str]) -> None:
        self._list.clear()
        for v in values:
            self._list.addItem(v)


class TriggerConfigDialog(QDialog):
    """
    Dynamic dialog for configuring trigger settings.

    Generates form fields based on the trigger type's JSON schema.
    """

    def __init__(
        self,
        trigger_type: TriggerType,
        existing_config: Optional[Dict[str, Any]] = None,
        parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)

        self._trigger_type = trigger_type
        self._existing_config = existing_config or {}
        self._field_widgets: Dict[str, QWidget] = {}
        self._is_edit_mode = bool(existing_config and existing_config.get('id'))

        self.setWindowTitle(
            f"{'Edit' if self._is_edit_mode else 'Configure'} "
            f"{self._get_trigger_display_name()} Trigger"
        )
        self.setMinimumSize(550, 500)
        self.setModal(True)

        self._setup_ui()
        self._apply_styles()
        self._load_existing_values()

    def _get_trigger_display_name(self) -> str:
        """Get display name for the trigger type."""
        registry = get_trigger_registry()
        trigger_class = registry.get(self._trigger_type)
        if trigger_class:
            return getattr(trigger_class, 'display_name', self._trigger_type.value.title())
        return self._trigger_type.value.title()

    def _get_schema(self) -> Dict[str, Any]:
        """Get the configuration schema for the trigger type."""
        registry = get_trigger_registry()
        trigger_class = registry.get(self._trigger_type)
        if trigger_class and hasattr(trigger_class, 'get_config_schema'):
            return trigger_class.get_config_schema()
        return {"type": "object", "properties": {"name": {"type": "string"}}}

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel(
            f"{'Edit' if self._is_edit_mode else 'Configure'} "
            f"{self._get_trigger_display_name()} Trigger"
        )
        header.setFont(QFont(header.font().family(), 14, QFont.Weight.Bold))
        layout.addWidget(header)

        # Tabs for organization
        tabs = QTabWidget()

        # General tab
        general_tab = self._create_general_tab()
        tabs.addTab(general_tab, "General")

        # Type-specific settings tab
        specific_tab = self._create_specific_tab()
        if specific_tab:
            tabs.addTab(specific_tab, "Settings")

        # Advanced tab
        advanced_tab = self._create_advanced_tab()
        tabs.addTab(advanced_tab, "Advanced")

        layout.addWidget(tabs, 1)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)

        self._ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_button.setText("Save" if self._is_edit_mode else "Create")

        layout.addWidget(button_box)

    def _create_general_tab(self) -> QWidget:
        """Create the general settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        form = QFormLayout(content)
        form.setSpacing(12)

        # Name
        name_input = QLineEdit()
        name_input.setPlaceholderText("e.g., Daily Report Trigger")
        self._field_widgets['name'] = name_input
        form.addRow("Name:", name_input)

        # Description (optional)
        desc_input = QTextEdit()
        desc_input.setPlaceholderText("Describe what this trigger does...")
        desc_input.setMaximumHeight(60)
        self._field_widgets['description'] = desc_input
        form.addRow("Description:", desc_input)

        # Enabled
        enabled_check = QCheckBox("Enabled")
        enabled_check.setChecked(True)
        self._field_widgets['enabled'] = enabled_check
        form.addRow("", enabled_check)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        return widget

    def _create_specific_tab(self) -> Optional[QWidget]:
        """Create trigger-type-specific settings tab."""
        schema = self._get_schema()
        properties = schema.get('properties', {})

        # Filter out general properties
        general_props = {'name', 'description', 'enabled', 'priority', 'cooldown_seconds'}
        specific_props = {k: v for k, v in properties.items() if k not in general_props}

        if not specific_props:
            return None

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        form = QFormLayout(content)
        form.setSpacing(12)

        for prop_name, prop_schema in specific_props.items():
            field_widget = self._create_field_widget(prop_name, prop_schema)
            if field_widget:
                label = self._format_label(prop_name)
                if prop_schema.get('description'):
                    label += f"\n({prop_schema['description'][:50]}...)" if len(prop_schema.get('description', '')) > 50 else f"\n({prop_schema.get('description', '')})"
                form.addRow(self._format_label(prop_name) + ":", field_widget)
                self._field_widgets[prop_name] = field_widget

        scroll.setWidget(content)
        layout.addWidget(scroll)

        return widget

    def _create_advanced_tab(self) -> QWidget:
        """Create advanced settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        form = QFormLayout(content)
        form.setSpacing(12)

        # Priority
        priority_spin = QSpinBox()
        priority_spin.setRange(0, 3)
        priority_spin.setValue(1)
        priority_spin.setToolTip("0=Low, 1=Normal, 2=High, 3=Critical")
        self._field_widgets['priority'] = priority_spin
        form.addRow("Priority:", priority_spin)

        # Cooldown
        cooldown_spin = QSpinBox()
        cooldown_spin.setRange(0, 86400)
        cooldown_spin.setValue(0)
        cooldown_spin.setSuffix(" seconds")
        cooldown_spin.setToolTip("Minimum time between triggers")
        self._field_widgets['cooldown_seconds'] = cooldown_spin
        form.addRow("Cooldown:", cooldown_spin)

        # Max runs
        max_runs_spin = QSpinBox()
        max_runs_spin.setRange(0, 1000000)
        max_runs_spin.setValue(0)
        max_runs_spin.setSpecialValueText("Unlimited")
        max_runs_spin.setToolTip("Maximum number of times to trigger (0 = unlimited)")
        self._field_widgets['max_runs'] = max_runs_spin
        form.addRow("Max Runs:", max_runs_spin)

        scroll.setWidget(content)
        layout.addWidget(scroll)
        layout.addStretch()

        return widget

    def _create_field_widget(
        self,
        prop_name: str,
        prop_schema: Dict[str, Any]
    ) -> Optional[QWidget]:
        """Create appropriate widget for a schema property."""
        prop_type = prop_schema.get('type', 'string')
        hint = FIELD_HINTS.get(prop_name, {})
        widget_type = hint.get('widget', prop_type)

        if widget_type == 'password':
            widget = QLineEdit()
            widget.setEchoMode(QLineEdit.EchoMode.Password)
            widget.setPlaceholderText(hint.get('placeholder', ''))
            return widget

        elif widget_type == 'list' or prop_type == 'array':
            return ListEditorWidget(hint.get('placeholder', 'Item'))

        elif prop_type == 'string':
            if 'enum' in prop_schema:
                widget = QComboBox()
                widget.addItems(prop_schema['enum'])
                return widget
            else:
                widget = QLineEdit()
                widget.setPlaceholderText(hint.get('placeholder', prop_schema.get('description', '')))
                return widget

        elif prop_type == 'integer':
            widget = QSpinBox()
            widget.setRange(
                prop_schema.get('minimum', hint.get('min', 0)),
                prop_schema.get('maximum', hint.get('max', 999999))
            )
            widget.setValue(prop_schema.get('default', 0))
            return widget

        elif prop_type == 'number':
            widget = QDoubleSpinBox()
            widget.setRange(
                prop_schema.get('minimum', hint.get('min', 0)),
                prop_schema.get('maximum', hint.get('max', 999999))
            )
            widget.setValue(prop_schema.get('default', 0))
            return widget

        elif prop_type == 'boolean':
            widget = QCheckBox()
            widget.setChecked(prop_schema.get('default', False))
            return widget

        elif prop_type == 'object':
            # For complex objects, use a text area with JSON
            widget = QTextEdit()
            widget.setMaximumHeight(100)
            widget.setPlaceholderText("JSON object")
            return widget

        return None

    def _format_label(self, prop_name: str) -> str:
        """Format property name as label."""
        return prop_name.replace('_', ' ').title()

    def _load_existing_values(self) -> None:
        """Load existing configuration values into widgets."""
        if not self._existing_config:
            return

        for prop_name, widget in self._field_widgets.items():
            value = self._existing_config.get(prop_name)
            if value is None:
                # Check nested config dict
                value = self._existing_config.get('config', {}).get(prop_name)

            if value is None:
                continue

            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QTextEdit):
                if isinstance(value, dict):
                    import json
                    widget.setText(json.dumps(value, indent=2))
                else:
                    widget.setText(str(value))
            elif isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
                widget.setValue(value)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, QComboBox):
                idx = widget.findText(str(value))
                if idx >= 0:
                    widget.setCurrentIndex(idx)
            elif isinstance(widget, ListEditorWidget):
                if isinstance(value, list):
                    widget.set_value(value)

    def _apply_styles(self) -> None:
        """Apply dialog styles."""
        self.setStyleSheet(f"""
            QDialog {{
                background: {THEME.bg_panel};
                color: {THEME.text_primary};
            }}
            QTabWidget::pane {{
                border: 1px solid {THEME.border};
                border-radius: 4px;
                background: {THEME.bg_dark};
            }}
            QTabBar::tab {{
                background: {THEME.bg_medium};
                color: {THEME.text_secondary};
                border: 1px solid {THEME.border};
                border-bottom: none;
                padding: 8px 16px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {THEME.bg_dark};
                color: {THEME.text_primary};
                border-bottom: 1px solid {THEME.bg_dark};
            }}
            QTabBar::tab:hover {{
                background: {THEME.bg_hover};
            }}
            QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                background: {THEME.bg_darkest};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 6px;
            }}
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border-color: {THEME.accent_primary};
            }}
            QCheckBox {{
                color: {THEME.text_primary};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {THEME.border};
                border-radius: 3px;
                background: {THEME.bg_darkest};
            }}
            QCheckBox::indicator:checked {{
                background: {THEME.accent_primary};
                border-color: {THEME.accent_primary};
            }}
            QPushButton {{
                background: {THEME.bg_medium};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background: {THEME.bg_hover};
            }}
            QListWidget {{
                background: {THEME.bg_darkest};
                border: 1px solid {THEME.border};
                border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 4px;
            }}
            QListWidget::item:selected {{
                background: {THEME.selection_bg};
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QLabel {{
                color: {THEME.text_primary};
            }}
        """)

    def _on_accept(self) -> None:
        """Handle accept - validate and close."""
        # Validate required fields
        name_widget = self._field_widgets.get('name')
        if isinstance(name_widget, QLineEdit):
            if not name_widget.text().strip():
                name_widget.setFocus()
                return

        self.accept()

    # =========================================================================
    # Public Methods
    # =========================================================================

    def get_config(self) -> Dict[str, Any]:
        """Get the complete trigger configuration."""
        config = {
            'id': self._existing_config.get('id', str(uuid.uuid4())),
            'type': self._trigger_type.value,
            'config': {},
        }

        # Extract values from widgets
        for prop_name, widget in self._field_widgets.items():
            value = None

            if isinstance(widget, QLineEdit):
                value = widget.text().strip()
            elif isinstance(widget, QTextEdit):
                text = widget.toPlainText().strip()
                # Try to parse as JSON for object fields
                if text.startswith('{'):
                    try:
                        import json
                        value = json.loads(text)
                    except json.JSONDecodeError:
                        value = text
                else:
                    value = text
            elif isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
                value = widget.value()
            elif isinstance(widget, QCheckBox):
                value = widget.isChecked()
            elif isinstance(widget, QComboBox):
                value = widget.currentText()
            elif isinstance(widget, ListEditorWidget):
                value = widget.get_value()

            # Top-level vs nested config
            if prop_name in ('name', 'enabled', 'priority', 'cooldown_seconds', 'description', 'max_runs'):
                config[prop_name] = value
            else:
                config['config'][prop_name] = value

        return config
