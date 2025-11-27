"""
CasareRPA - Trigger Type Selector Dialog

Dialog for selecting the type of trigger to create.
Displays a grid of trigger type cards with icons and descriptions.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QScrollArea,
    QWidget,
    QDialogButtonBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QCursor

from ..theme import THEME
from ...triggers.base import TriggerType


# Trigger type metadata for display
TRIGGER_TYPE_INFO = {
    TriggerType.MANUAL: {
        "name": "Manual",
        "description": "Trigger workflow manually from the UI or API",
        "icon": "▶",
        "category": "Basic",
    },
    TriggerType.SCHEDULED: {
        "name": "Scheduled",
        "description": "Run on a schedule (cron) or at intervals",
        "icon": "⏰",
        "category": "Basic",
    },
    TriggerType.WEBHOOK: {
        "name": "Webhook",
        "description": "Trigger via HTTP POST request with authentication",
        "icon": "🌐",
        "category": "External",
    },
    TriggerType.FILE_WATCH: {
        "name": "File Watch",
        "description": "Monitor file system for changes (create, modify, delete)",
        "icon": "📁",
        "category": "External",
    },
    TriggerType.EMAIL: {
        "name": "Email",
        "description": "Trigger when matching emails are received",
        "icon": "📧",
        "category": "External",
    },
    TriggerType.APP_EVENT: {
        "name": "App Event",
        "description": "React to Windows, browser, or RPA system events",
        "icon": "🖥",
        "category": "Events",
    },
    TriggerType.ERROR: {
        "name": "Error Handler",
        "description": "Trigger when another workflow fails with an error",
        "icon": "⚠",
        "category": "Control",
    },
    TriggerType.WORKFLOW_CALL: {
        "name": "Workflow Call",
        "description": "Allow this workflow to be called by other workflows",
        "icon": "🔗",
        "category": "Control",
    },
    TriggerType.FORM: {
        "name": "Form Submission",
        "description": "Trigger when a form is submitted to this workflow",
        "icon": "📋",
        "category": "External",
    },
    TriggerType.CHAT: {
        "name": "Chat Message",
        "description": "Respond to chat messages (Slack, Teams, Discord)",
        "icon": "💬",
        "category": "External",
    },
}


class TriggerTypeCard(QFrame):
    """
    Clickable card representing a trigger type.
    """

    clicked = Signal(TriggerType)

    def __init__(
        self, trigger_type: TriggerType, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)

        self._trigger_type = trigger_type
        self._info = TRIGGER_TYPE_INFO.get(trigger_type, {})
        self._selected = False

        self._setup_ui()
        self._apply_styles()

        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def _setup_ui(self) -> None:
        """Set up the card UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Icon
        icon_label = QLabel(self._info.get("icon", "?"))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFont(QFont(icon_label.font().family(), 24))
        icon_label.setObjectName("icon")
        layout.addWidget(icon_label)

        # Name
        name_label = QLabel(self._info.get("name", str(self._trigger_type.value)))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setFont(QFont(name_label.font().family(), 11, QFont.Weight.Bold))
        name_label.setObjectName("name")
        layout.addWidget(name_label)

        # Description
        desc_label = QLabel(self._info.get("description", ""))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setObjectName("description")
        layout.addWidget(desc_label)

        # Category badge
        category = self._info.get("category", "")
        if category:
            category_label = QLabel(category)
            category_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            category_label.setObjectName("category")
            layout.addWidget(category_label)

        self.setFixedSize(180, 160)

    def _apply_styles(self) -> None:
        """Apply card styles."""
        self.setStyleSheet(f"""
            TriggerTypeCard {{
                background: {THEME.bg_dark};
                border: 1px solid {THEME.border};
                border-radius: 8px;
            }}
            TriggerTypeCard:hover {{
                background: {THEME.bg_medium};
                border-color: {THEME.accent_primary};
            }}
            TriggerTypeCard[selected="true"] {{
                background: {THEME.bg_medium};
                border: 2px solid {THEME.accent_primary};
            }}
            QLabel#icon {{
                color: {THEME.accent_primary};
            }}
            QLabel#name {{
                color: {THEME.text_primary};
            }}
            QLabel#description {{
                color: {THEME.text_muted};
                font-size: 10px;
            }}
            QLabel#category {{
                color: {THEME.text_secondary};
                background: {THEME.bg_darkest};
                border-radius: 3px;
                padding: 2px 6px;
                font-size: 9px;
            }}
        """)

    def mousePressEvent(self, event) -> None:
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._trigger_type)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool) -> None:
        """Set card selection state."""
        self._selected = selected
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    @property
    def trigger_type(self) -> TriggerType:
        """Get the trigger type for this card."""
        return self._trigger_type


class TriggerTypeSelectorDialog(QDialog):
    """
    Dialog for selecting the type of trigger to create.

    Displays a grid of clickable cards for each trigger type.
    User double-clicks or selects and clicks OK to choose.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._selected_type: Optional[TriggerType] = None
        self._cards: dict[TriggerType, TriggerTypeCard] = {}

        self.setWindowTitle("Add Trigger")
        self.setMinimumSize(600, 500)
        self.setModal(True)

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("Select Trigger Type")
        header.setFont(QFont(header.font().family(), 14, QFont.Weight.Bold))
        layout.addWidget(header)

        # Info text
        info = QLabel(
            "Choose how this workflow should be triggered. "
            "You can add multiple triggers to the same workflow."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {THEME.text_muted}; font-size: 11px;")
        layout.addWidget(info)

        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        grid_layout = QGridLayout(scroll_content)
        grid_layout.setSpacing(16)
        grid_layout.setContentsMargins(4, 4, 4, 4)

        # Create cards by category
        categories = ["Basic", "External", "Events", "Control"]
        trigger_types_by_category = {}

        for tt, info in TRIGGER_TYPE_INFO.items():
            category = info.get("category", "Other")
            if category not in trigger_types_by_category:
                trigger_types_by_category[category] = []
            trigger_types_by_category[category].append(tt)

        row = 0
        for category in categories:
            if category not in trigger_types_by_category:
                continue

            # Category header
            cat_label = QLabel(category)
            cat_label.setFont(QFont(cat_label.font().family(), 10, QFont.Weight.Bold))
            cat_label.setStyleSheet(
                f"color: {THEME.text_secondary}; padding: 8px 0 4px 0;"
            )
            grid_layout.addWidget(cat_label, row, 0, 1, 3)
            row += 1

            # Cards in this category
            col = 0
            for trigger_type in trigger_types_by_category[category]:
                card = TriggerTypeCard(trigger_type)
                card.clicked.connect(self._on_card_clicked)
                self._cards[trigger_type] = card
                grid_layout.addWidget(card, row, col)
                col += 1
                if col >= 3:
                    col = 0
                    row += 1
            if col != 0:
                row += 1

        grid_layout.setRowStretch(row, 1)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)

        self._ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_button.setText("Continue")
        self._ok_button.setEnabled(False)

        layout.addWidget(button_box)

    def _apply_styles(self) -> None:
        """Apply dialog styles."""
        self.setStyleSheet(f"""
            QDialog {{
                background: {THEME.bg_panel};
                color: {THEME.text_primary};
            }}
            QScrollArea {{
                background: transparent;
            }}
            QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
            QPushButton {{
                background: {THEME.bg_medium};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background: {THEME.bg_hover};
            }}
            QPushButton:pressed {{
                background: {THEME.accent_primary};
            }}
            QPushButton:disabled {{
                background: {THEME.bg_dark};
                color: {THEME.text_disabled};
            }}
        """)

    def _on_card_clicked(self, trigger_type: TriggerType) -> None:
        """Handle card click."""
        # Deselect previous
        if self._selected_type and self._selected_type in self._cards:
            self._cards[self._selected_type].set_selected(False)

        # Select new
        self._selected_type = trigger_type
        if trigger_type in self._cards:
            self._cards[trigger_type].set_selected(True)

        self._ok_button.setEnabled(True)

    def _on_accept(self) -> None:
        """Handle accept."""
        if self._selected_type:
            self.accept()

    def mouseDoubleClickEvent(self, event) -> None:
        """Handle double-click to accept."""
        # Double-click on card accepts dialog
        if self._selected_type:
            self.accept()
        super().mouseDoubleClickEvent(event)

    # =========================================================================
    # Public Methods
    # =========================================================================

    def get_selected_type(self) -> Optional[TriggerType]:
        """Get the selected trigger type."""
        return self._selected_type
