"""
Panel UX Helpers for CasareRPA Bottom Panel.

Provides reusable UI components for consistent UX across all panels:
- Empty state widgets with icons and guidance
- Status badge labels
- Styled toolbar buttons
- Context menu builders
"""

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QCursor
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME


class EmptyStateWidget(QWidget):
    """
    Empty state display for panels with no data.

    Shows an icon, title, description, and optional action button.
    Uses muted styling to indicate placeholder content.
    """

    action_clicked = Signal()

    def __init__(
        self,
        icon_text: str = "",
        title: str = "No data",
        description: str = "",
        action_text: str = "",
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize empty state widget.

        Args:
            icon_text: Unicode icon or emoji to display (e.g., folder icon)
            title: Main title text
            description: Detailed description/guidance
            action_text: Optional button text (shows button if provided)
            parent: Parent widget
        """
        super().__init__(parent)

        self._setup_ui(icon_text, title, description, action_text)
        self._apply_styles()

    def _setup_ui(
        self,
        icon_text: str,
        title: str,
        description: str,
        action_text: str,
    ) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 40, 20, 40)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon (large, muted)
        if icon_text:
            icon_label = QLabel(icon_text)
            icon_label.setObjectName("emptyStateIcon")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)

        # Title
        title_label = QLabel(title)
        title_label.setObjectName("emptyStateTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Description
        if description:
            desc_label = QLabel(description)
            desc_label.setObjectName("emptyStateDescription")
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        # Action button
        if action_text:
            action_btn = QPushButton(action_text)
            action_btn.setObjectName("emptyStateAction")
            action_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            action_btn.clicked.connect(self.action_clicked.emit)

            # Center the button
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            btn_layout.addWidget(action_btn)
            btn_layout.addStretch()
            layout.addLayout(btn_layout)

    def _apply_styles(self) -> None:
        """Apply empty state styling."""
        self.setStyleSheet(f"""
            EmptyStateWidget {{
                background-color: {THEME.bg_panel};
            }}
            QLabel {{
                background: transparent;
            }}
            #emptyStateIcon {{
                font-size: 48px;
                color: {THEME.text_disabled};
            }}
            #emptyStateTitle {{
                font-size: 14px;
                font-weight: 600;
                color: {THEME.text_secondary};
            }}
            #emptyStateDescription {{
                font-size: 12px;
                color: {THEME.text_muted};
                line-height: 1.4;
            }}
            #emptyStateAction {{
                background-color: {THEME.accent_primary};
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            #emptyStateAction:hover {{
                background-color: {THEME.accent_hover};
            }}
        """)


class StatusBadge(QLabel):
    """
    Status badge label with color-coded backgrounds.

    Used to display status indicators like SUCCESS, ERROR, WARNING.
    """

    def __init__(
        self,
        text: str = "",
        status: str = "info",
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize status badge.

        Args:
            text: Badge text
            status: Status type (success, error, warning, info, idle)
            parent: Parent widget
        """
        super().__init__(text, parent)
        self.set_status(status)
        self._apply_base_styles()

    def _apply_base_styles(self) -> None:
        """Apply base badge styling."""
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumWidth(60)

    def set_status(self, status: str, text: str | None = None) -> None:
        """
        Set badge status and optionally update text.

        Args:
            status: Status type (success, error, warning, info, idle, running)
            text: Optional new text
        """
        if text is not None:
            self.setText(text)

        # Color mappings: (fg_color, bg_color) - None bg means no badge styling
        colors = {
            "success": (THEME.status_success, "#1a3d1a"),
            "error": (THEME.status_error, "#3d1a1a"),
            "warning": (THEME.status_warning, "#3d3a1a"),
            "info": (THEME.status_info, "#1a2d3d"),
            "idle": (THEME.text_muted, None),  # No badge, just plain text
            "running": (THEME.status_warning, "#3d3a1a"),
        }

        fg_color, bg_color = colors.get(status.lower(), colors["info"])

        if bg_color is None:
            # Idle: plain text, no background at all
            self.setAutoFillBackground(False)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setStyleSheet(f"""
                QLabel {{
                    background: none;
                    border: none;
                    color: {fg_color};
                    font-size: 10px;
                    font-weight: 600;
                    text-transform: uppercase;
                }}
            """)
        else:
            # Active states: badge with colored background
            self.setAutoFillBackground(False)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            self.setStyleSheet(f"""
                QLabel {{
                    background-color: {bg_color};
                    color: {fg_color};
                    padding: 2px 8px;
                    border-radius: 3px;
                    font-size: 10px;
                    font-weight: 600;
                    text-transform: uppercase;
                }}
            """)


class ToolbarButton(QPushButton):
    """
    Styled toolbar button with icon and optional text.

    Provides consistent hover and pressed states.
    """

    def __init__(
        self,
        text: str = "",
        icon_text: str = "",
        tooltip: str = "",
        primary: bool = False,
        danger: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize toolbar button.

        Args:
            text: Button text
            icon_text: Unicode icon (prepended to text)
            tooltip: Tooltip text
            primary: Use primary accent color
            danger: Use danger/error color
            parent: Parent widget
        """
        display_text = f"{icon_text} {text}".strip() if icon_text else text
        super().__init__(display_text, parent)

        if tooltip:
            self.setToolTip(tooltip)

        self._apply_styles(primary, danger)

    def _apply_styles(self, primary: bool, danger: bool) -> None:
        """Apply button styling."""
        if primary:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {THEME.accent_primary};
                    color: #ffffff;
                    border: none;
                    border-radius: 3px;
                    padding: 4px 12px;
                    font-weight: 500;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {THEME.accent_hover};
                }}
                QPushButton:pressed {{
                    background-color: {THEME.accent_secondary};
                }}
                QPushButton:disabled {{
                    background-color: {THEME.bg_light};
                    color: {THEME.text_disabled};
                }}
            """)
        elif danger:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {THEME.bg_light};
                    color: {THEME.accent_error};
                    border: 1px solid {THEME.accent_error};
                    border-radius: 3px;
                    padding: 4px 12px;
                    font-weight: 500;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {THEME.accent_error};
                    color: #ffffff;
                }}
                QPushButton:pressed {{
                    background-color: #c53030;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {THEME.bg_light};
                    color: {THEME.text_secondary};
                    border: 1px solid {THEME.border};
                    border-radius: 3px;
                    padding: 4px 12px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {THEME.bg_hover};
                    color: {THEME.text_primary};
                    border-color: {THEME.border_light};
                }}
                QPushButton:pressed {{
                    background-color: {THEME.bg_lighter};
                }}
                QPushButton:disabled {{
                    background-color: {THEME.bg_medium};
                    color: {THEME.text_disabled};
                    border-color: {THEME.border_dark};
                }}
            """)


class SectionHeader(QFrame):
    """
    Section header with title and optional count badge.

    Used to separate sections within panels.
    """

    def __init__(
        self,
        title: str,
        count: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize section header.

        Args:
            title: Section title
            count: Optional count to display as badge
            parent: Parent widget
        """
        super().__init__(parent)

        self._title_label: QLabel
        self._count_label: QLabel | None = None

        self._setup_ui(title, count)
        self._apply_styles()

    def _setup_ui(self, title: str, count: int | None) -> None:
        """Set up the UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        self._title_label = QLabel(title.upper())
        self._title_label.setObjectName("sectionTitle")
        layout.addWidget(self._title_label)

        if count is not None:
            self._count_label = QLabel(str(count))
            self._count_label.setObjectName("sectionCount")
            layout.addWidget(self._count_label)

        layout.addStretch()

    def _apply_styles(self) -> None:
        """Apply section header styling."""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME.bg_header};
                border-bottom: 1px solid {THEME.border_dark};
            }}
            #sectionTitle {{
                color: {THEME.text_header};
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            #sectionCount {{
                background-color: {THEME.bg_lighter};
                color: {THEME.text_muted};
                padding: 1px 6px;
                border-radius: 8px;
                font-size: 10px;
            }}
        """)

    def set_count(self, count: int) -> None:
        """Update the count badge."""
        if self._count_label:
            self._count_label.setText(str(count))


def create_context_menu(
    actions: list[tuple[str, str, Callable]],
    parent: QWidget | None = None,
) -> QMenu:
    """
    Create a styled context menu.

    Args:
        actions: List of (icon_text, label, callback) tuples.
                 Use "-" as label for separator.
        parent: Parent widget

    Returns:
        Configured QMenu
    """
    menu = QMenu(parent)
    menu.setStyleSheet(f"""
        QMenu {{
            background-color: {THEME.bg_light};
            color: {THEME.text_primary};
            border: 1px solid {THEME.border};
            border-radius: 4px;
            padding: 4px;
        }}
        QMenu::item {{
            padding: 6px 24px 6px 12px;
            border-radius: 3px;
        }}
        QMenu::item:selected {{
            background-color: {THEME.accent_primary};
            color: #ffffff;
        }}
        QMenu::separator {{
            height: 1px;
            background-color: {THEME.border};
            margin: 4px 8px;
        }}
    """)

    for icon_text, label, callback in actions:
        if label == "-":
            menu.addSeparator()
        else:
            text = f"{icon_text} {label}" if icon_text else label
            action = QAction(text, menu)
            action.triggered.connect(callback)
            menu.addAction(action)

    return menu


def get_panel_table_stylesheet() -> str:
    """
    Get consistent table stylesheet for all panels.

    Returns:
        QSS stylesheet string
    """
    return f"""
        QTableWidget, QTreeWidget {{
            background-color: {THEME.bg_panel};
            alternate-background-color: {THEME.bg_dark};
            color: {THEME.text_primary};
            border: 1px solid {THEME.border_dark};
            gridline-color: {THEME.border_dark};
            selection-background-color: {THEME.bg_selected};
            selection-color: {THEME.text_primary};
            outline: none;
            font-family: 'Segoe UI', system-ui, sans-serif;
            font-size: 11px;
        }}
        QTableWidget::item, QTreeWidget::item {{
            padding: 6px 8px;
            border-bottom: 1px solid {THEME.border_dark};
        }}
        QTableWidget::item:selected, QTreeWidget::item:selected {{
            background-color: {THEME.bg_selected};
        }}
        QTableWidget::item:hover, QTreeWidget::item:hover {{
            background-color: {THEME.bg_hover};
        }}
        QTableWidget::item:focus, QTreeWidget::item:focus {{
            outline: 1px solid {THEME.border_focus};
            outline-offset: -1px;
        }}
        QHeaderView {{
            background-color: {THEME.bg_header};
        }}
        QHeaderView::section {{
            background-color: {THEME.bg_header};
            color: {THEME.text_header};
            padding: 8px 10px;
            border: none;
            border-right: 1px solid {THEME.border_dark};
            border-bottom: 1px solid {THEME.border_dark};
            font-weight: 600;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }}
        QHeaderView::section:last {{
            border-right: none;
        }}
        QHeaderView::section:hover {{
            background-color: {THEME.bg_hover};
            color: {THEME.text_primary};
        }}
        QHeaderView::section:pressed {{
            background-color: {THEME.bg_lighter};
        }}
    """


def get_panel_toolbar_stylesheet() -> str:
    """
    Get consistent toolbar stylesheet for all panels.

    Returns:
        QSS stylesheet string
    """
    return f"""
        QLabel {{
            background: transparent;
            color: {THEME.text_secondary};
            font-size: 11px;
        }}
        QLabel[muted="true"] {{
            color: {THEME.text_muted};
        }}
        QComboBox {{
            background-color: {THEME.bg_light};
            color: {THEME.text_primary};
            border: 1px solid {THEME.border};
            border-radius: 3px;
            padding: 4px 8px;
            min-width: 70px;
            font-size: 11px;
        }}
        QComboBox:hover {{
            border-color: {THEME.border_light};
        }}
        QComboBox:focus {{
            border-color: {THEME.border_focus};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 18px;
        }}
        QComboBox::down-arrow {{
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {THEME.text_secondary};
        }}
        QComboBox QAbstractItemView {{
            background-color: {THEME.bg_light};
            color: {THEME.text_primary};
            border: 1px solid {THEME.border};
            selection-background-color: {THEME.accent_primary};
            outline: none;
        }}
    """
