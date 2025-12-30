"""
Recording Preview Dialog

Shows recorded actions and allows editing before generating workflow.

Epic 7.1 Migration: Migrated to BaseDialogV2 with THEME_V2/TOKENS_V2.
"""

from loguru import logger
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.dialogs_v2 import BaseDialogV2, DialogSizeV2


class RecordingPreviewDialog(BaseDialogV2):
    """Dialog for previewing and editing recorded actions."""

    def __init__(self, actions: list, parent=None):
        """
        Initialize recording preview dialog.

        Args:
            actions: List of recorded action dictionaries
            parent: Parent widget
        """
        super().__init__(
            title="Recording Preview",
            parent=parent,
            size=DialogSizeV2.LG,  # Larger for table display
            resizable=True,
        )

        self.actions = actions.copy()

        # Override title
        self.setWindowTitle("Recording Preview")

        self._setup_ui()
        self._load_actions()

        # Set button text
        self.set_primary_button("Generate Workflow", self.accept)
        self.set_secondary_button("Cancel", self.reject)

        logger.info(f"Recording preview dialog opened with {len(actions)} actions")

    def _setup_ui(self):
        """Setup the user interface."""
        # Main content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.md)

        # Title
        title_label = QLabel("Review Recorded Actions")
        title_label.setStyleSheet(f"""
            font-size: {TOKENS_V2.typography.heading_lg}px;
            font-weight: {TOKENS_V2.typography.weight_semibold};
            color: {THEME_V2.text_header};
            margin-bottom: {TOKENS_V2.spacing.sm}px;
        """)
        layout.addWidget(title_label)

        # Info label
        info_label = QLabel(
            f"Recorded {len(self.actions)} actions. "
            "Review and edit before generating workflow."
        )
        info_label.setStyleSheet(f"""
            color: {THEME_V2.text_secondary};
            margin-bottom: {TOKENS_V2.spacing.md}px;
        """)
        layout.addWidget(info_label)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Action", "Selector", "Value", "Time"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self._apply_table_styles()
        layout.addWidget(self.table)

        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(TOKENS_V2.spacing.md)

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self._on_delete_selected)
        action_layout.addWidget(self.delete_btn)

        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self._on_clear_all)
        action_layout.addWidget(self.clear_btn)

        action_layout.addStretch()
        layout.addLayout(action_layout)

        # Set as body
        self.set_body_widget(content)

    def _apply_table_styles(self):
        """Apply THEME_V2 styles to table."""
        t = THEME_V2
        tok = TOKENS_V2

        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {t.bg_surface};
                alternate-background-color: {t.bg_elevated};
                gridline-color: {t.border};
                border: 1px solid {t.border};
                border-radius: {tok.radius.sm}px;
                color: {t.text_primary};
                font-size: {tok.typography.body}px;
            }}
            QTableWidget::item {{
                padding: {tok.spacing.sm}px;
            }}
            QTableWidget::item:selected {{
                background-color: {t.bg_selected};
                color: {t.text_primary};
            }}
            QHeaderView::section {{
                background-color: {t.bg_component};
                color: {t.text_header};
                padding: {tok.spacing.sm}px {tok.spacing.md}px;
                border: none;
                border-right: 1px solid {t.border};
                border-bottom: 1px solid {t.border};
                font-weight: {tok.typography.weight_semibold};
                font-size: {tok.typography.body_sm}px;
            }}
            QHeaderView::section:first {{
                border-top-left-radius: {tok.radius.sm}px;
            }}
            QHeaderView::section:last {{
                border-top-right-radius: {tok.radius.sm}px;
                border-right: none;
            }}
            QScrollBar:vertical {{
                background-color: {t.bg_surface};
                width: {tok.sizes.scrollbar_width}px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {t.scrollbar_handle};
                border-radius: {tok.radius.xs}px;
                min-height: {tok.sizes.scrollbar_min_height}px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {t.scrollbar_hover};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)

        # Style action buttons
        button_style = f"""
            QPushButton {{
                background-color: {t.bg_component};
                border: 1px solid {t.border};
                border-radius: {tok.radius.sm}px;
                padding: {tok.spacing.sm}px {tok.spacing.md}px;
                color: {t.text_primary};
                font-size: {tok.typography.body}px;
            }}
            QPushButton:hover {{
                background-color: {t.bg_hover};
                border-color: {t.border_light};
            }}
            QPushButton:pressed {{
                background-color: {t.bg_selected};
            }}
        """
        self.delete_btn.setStyleSheet(button_style)
        self.clear_btn.setStyleSheet(button_style)

    def _load_actions(self):
        """Load actions into the table."""
        self.table.setRowCount(len(self.actions))

        for i, action in enumerate(self.actions):
            # Action type
            action_type = action.get("action", "unknown").upper()
            action_item = QTableWidgetItem(action_type)
            action_item.setFlags(action_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 0, action_item)

            # Selector - handle both dict and ElementFingerprint
            element_info = action.get("element", {})

            # Check if element_info is an ElementFingerprint object
            if hasattr(element_info, "selectors"):
                # It's an ElementFingerprint object - selectors is a List[SelectorStrategy]
                selector = ""
                if element_info.selectors:
                    # Try to find xpath or css selector
                    for strat in element_info.selectors:
                        if strat.selector_type.value == "xpath":
                            selector = strat.value
                            break
                    if not selector:
                        # Fallback to first available selector
                        selector = element_info.selectors[0].value
            elif isinstance(element_info, dict):
                # It's a dictionary
                selectors = element_info.get("selectors", {})
                selector = selectors.get("xpath", selectors.get("css", ""))
            else:
                selector = ""

            selector_item = QTableWidgetItem(self._truncate(selector, 50))
            selector_item.setToolTip(selector)
            self.table.setItem(i, 1, selector_item)

            # Value
            value = action.get("value", "")
            value_item = QTableWidgetItem(str(value) if value else "-")
            self.table.setItem(i, 2, value_item)

            # Timestamp
            timestamp = action.get("timestamp", 0)
            from datetime import datetime

            time_str = datetime.fromtimestamp(timestamp / 1000).strftime("%H:%M:%S")
            time_item = QTableWidgetItem(time_str)
            time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 3, time_item)

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text for display."""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."

    def _on_delete_selected(self):
        """Delete selected rows."""
        selected_rows = sorted(set(item.row() for item in self.table.selectedItems()), reverse=True)

        if not selected_rows:
            from casare_rpa.presentation.canvas.ui.dialogs_v2 import MessageBoxV2
            MessageBoxV2.show_warning(self, "No Selection", "Please select actions to delete.")
            return

        for row in selected_rows:
            self.table.removeRow(row)
            del self.actions[row]

        logger.info(f"Deleted {len(selected_rows)} actions")

    def _on_clear_all(self):
        """Clear all actions."""
        from casare_rpa.presentation.canvas.ui.dialogs_v2 import ConfirmDialogV2

        reply = ConfirmDialogV2.show(
            parent=self,
            title="Clear All",
            message="Are you sure you want to clear all recorded actions?",
        )

        if reply:
            self.table.setRowCount(0)
            self.actions.clear()
            logger.info("Cleared all actions")

    def get_actions(self) -> list:
        """
        Get the edited actions.

        Returns:
            List of action dictionaries
        """
        # Update values from table
        result = []
        for i in range(self.table.rowCount()):
            if i < len(self.actions):
                action = self.actions[i].copy()

                # Update value if edited
                value_item = self.table.item(i, 2)
                if value_item and value_item.text() != "-":
                    action["value"] = value_item.text()

                result.append(action)

        return result
