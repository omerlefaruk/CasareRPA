"""
Custom table delegates for Deadline Monitor-style rendering.
Provides progress bars, status indicators, and priority visualization.
"""

from typing import Optional

from PySide6.QtCore import QModelIndex, QRect, QSize, Qt
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QStyle, QStyledItemDelegate, QStyleOptionViewItem

from casare_rpa.infrastructure.orchestrator.communication.theme import (
    THEME,
    get_priority_color,
    get_progress_color,
    get_status_color,
)


class ProgressBarDelegate(QStyledItemDelegate):
    """
    Delegate for rendering progress bars in table cells.
    Displays percentage with colored bar overlay.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bar_height = 14
        self._bar_margin = 3
        self._show_text = True

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Get data
        progress = index.data(Qt.ItemDataRole.DisplayRole)
        if progress is None:
            progress = 0
        try:
            progress = int(progress)
        except (ValueError, TypeError):
            progress = 0
        progress = max(0, min(100, progress))

        # Get status for color (from UserRole if available)
        status = index.data(Qt.ItemDataRole.UserRole) or "running"
        bar_color = QColor(get_progress_color(status))

        # Background
        rect = option.rect
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(rect, QColor(THEME.bg_selected))
        else:
            painter.fillRect(rect, QColor(THEME.bg_panel))

        # Progress bar background
        bar_rect = QRect(
            rect.left() + self._bar_margin,
            rect.top() + (rect.height() - self._bar_height) // 2,
            rect.width() - self._bar_margin * 2,
            self._bar_height,
        )
        painter.fillRect(bar_rect, QColor(THEME.progress_bg))
        painter.setPen(QPen(QColor(THEME.border_dark), 1))
        painter.drawRect(bar_rect)

        # Progress fill
        if progress > 0:
            fill_width = int((bar_rect.width() - 2) * progress / 100)
            fill_rect = QRect(
                bar_rect.left() + 1,
                bar_rect.top() + 1,
                fill_width,
                bar_rect.height() - 2,
            )

            # Gradient fill
            gradient = QLinearGradient(fill_rect.topLeft(), fill_rect.bottomLeft())
            gradient.setColorAt(0, bar_color.lighter(120))
            gradient.setColorAt(1, bar_color)
            painter.fillRect(fill_rect, QBrush(gradient))

        # Text
        if self._show_text:
            painter.setPen(QColor(THEME.text_primary))
            font = painter.font()
            font.setPointSize(8)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(bar_rect, Qt.AlignmentFlag.AlignCenter, f"{progress}%")

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(100, self._bar_height + self._bar_margin * 2 + 4)


class StatusDelegate(QStyledItemDelegate):
    """
    Delegate for rendering status with colored indicator dot.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dot_size = 8
        self._dot_margin = 6

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Get data
        status = index.data(Qt.ItemDataRole.DisplayRole) or ""
        status_lower = status.lower() if isinstance(status, str) else ""
        color = QColor(get_status_color(status_lower))

        rect = option.rect

        # Background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(rect, QColor(THEME.bg_selected))
        else:
            painter.fillRect(rect, QColor(THEME.bg_panel))

        # Status dot
        dot_x = rect.left() + self._dot_margin
        dot_y = rect.top() + (rect.height() - self._dot_size) // 2
        dot_rect = QRect(dot_x, dot_y, self._dot_size, self._dot_size)

        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(120), 1))
        painter.drawEllipse(dot_rect)

        # Glow effect for active statuses
        if status_lower in ("online", "running", "active"):
            glow_color = QColor(color)
            glow_color.setAlpha(60)
            painter.setBrush(QBrush(glow_color))
            painter.setPen(Qt.PenStyle.NoPen)
            glow_rect = dot_rect.adjusted(-2, -2, 2, 2)
            painter.drawEllipse(glow_rect)

        # Text
        text_rect = QRect(
            dot_x + self._dot_size + self._dot_margin,
            rect.top(),
            rect.width() - self._dot_size - self._dot_margin * 2,
            rect.height(),
        )
        painter.setPen(QColor(THEME.text_primary))
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        # Capitalize status text
        display_text = status.capitalize() if status else ""
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            display_text,
        )

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(100, 22)


class PriorityDelegate(QStyledItemDelegate):
    """
    Delegate for rendering priority with colored badge.
    """

    PRIORITY_LABELS = {0: "Low", 1: "Normal", 2: "High", 3: "Critical"}

    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Get data
        priority = index.data(Qt.ItemDataRole.DisplayRole)
        try:
            priority = int(priority)
        except (ValueError, TypeError):
            priority = 1
        priority = max(0, min(3, priority))

        color = QColor(get_priority_color(priority))
        label = self.PRIORITY_LABELS.get(priority, "Normal")

        rect = option.rect

        # Background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(rect, QColor(THEME.bg_selected))
        else:
            painter.fillRect(rect, QColor(THEME.bg_panel))

        # Badge background
        font = painter.font()
        font.setPointSize(9)
        font.setBold(priority >= 2)
        painter.setFont(font)

        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(label) + 12
        badge_height = 18
        badge_rect = QRect(
            rect.left() + 4,
            rect.top() + (rect.height() - badge_height) // 2,
            text_width,
            badge_height,
        )

        # Draw badge
        bg_color = QColor(color)
        bg_color.setAlpha(40)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(color.darker(110), 1))
        painter.drawRoundedRect(badge_rect, 3, 3)

        # Draw text
        painter.setPen(color)
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, label)

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(80, 24)


class DurationDelegate(QStyledItemDelegate):
    """
    Delegate for rendering duration with elapsed time formatting.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()

        # Get duration in milliseconds
        duration_ms = index.data(Qt.ItemDataRole.DisplayRole)
        try:
            duration_ms = int(duration_ms)
        except (ValueError, TypeError):
            duration_ms = 0

        rect = option.rect

        # Background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(rect, QColor(THEME.bg_selected))
        else:
            painter.fillRect(rect, QColor(THEME.bg_panel))

        # Format duration
        if duration_ms == 0:
            text = "-"
            color = QColor(THEME.text_muted)
        else:
            seconds = duration_ms / 1000
            if seconds < 60:
                text = f"{seconds:.1f}s"
            elif seconds < 3600:
                minutes = seconds / 60
                text = f"{minutes:.1f}m"
            else:
                hours = seconds / 3600
                text = f"{hours:.1f}h"
            color = QColor(THEME.text_secondary)

        # Draw text
        painter.setPen(color)
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        text_rect = rect.adjusted(6, 0, -6, 0)
        painter.drawText(
            text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, text
        )

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(70, 22)


class RobotStatusDelegate(QStyledItemDelegate):
    """
    Delegate for rendering robot status with utilization bar.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = option.rect

        # Background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(rect, QColor(THEME.bg_selected))
        else:
            painter.fillRect(rect, QColor(THEME.bg_panel))

        # Get data (expects dict with status and utilization)
        data = index.data(Qt.ItemDataRole.UserRole)
        if not isinstance(data, dict):
            data = {
                "status": str(index.data(Qt.ItemDataRole.DisplayRole) or "offline"),
                "utilization": 0,
            }

        status = data.get("status", "offline")
        utilization = data.get("utilization", 0)
        color = QColor(get_status_color(status))

        # Status icon
        icon_rect = QRect(rect.left() + 4, rect.top() + (rect.height() - 12) // 2, 12, 12)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(icon_rect)

        # Status text
        text_x = icon_rect.right() + 6
        painter.setPen(QColor(THEME.text_primary))
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(
            text_x,
            rect.top(),
            rect.width() - text_x - 50,
            rect.height(),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            status.capitalize(),
        )

        # Utilization mini bar
        if status != "offline":
            bar_width = 40
            bar_height = 6
            bar_x = rect.right() - bar_width - 6
            bar_y = rect.top() + (rect.height() - bar_height) // 2

            # Background
            painter.fillRect(bar_x, bar_y, bar_width, bar_height, QColor(THEME.progress_bg))

            # Fill
            fill_width = int(bar_width * min(utilization, 100) / 100)
            if fill_width > 0:
                fill_color = (
                    QColor(THEME.status_online) if utilization < 80 else QColor(THEME.status_busy)
                )
                painter.fillRect(bar_x, bar_y, fill_width, bar_height, fill_color)

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(150, 24)


class IconTextDelegate(QStyledItemDelegate):
    """
    Delegate for rendering text with an icon prefix.
    Used for workflow names, robot names with type icons.
    """

    def __init__(self, icon_map: dict | None = None, parent=None):
        super().__init__(parent)
        self._icon_map = icon_map or {}

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()

        rect = option.rect
        text = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        icon = index.data(Qt.ItemDataRole.DecorationRole) or ""

        # Background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(rect, QColor(THEME.bg_selected))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(rect, QColor(THEME.bg_hover))
        else:
            painter.fillRect(rect, QColor(THEME.bg_panel))

        # Icon
        text_x = rect.left() + 6
        if icon:
            painter.setPen(QColor(THEME.text_secondary))
            font = painter.font()
            font.setPointSize(10)
            painter.setFont(font)
            painter.drawText(
                text_x,
                rect.top(),
                20,
                rect.height(),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                str(icon),
            )
            text_x += 22

        # Text
        painter.setPen(QColor(THEME.text_primary))
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        text_rect = QRect(text_x, rect.top(), rect.width() - text_x - 4, rect.height())
        painter.drawText(
            text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text
        )

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(150, 22)


class TimeDelegate(QStyledItemDelegate):
    """
    Delegate for rendering timestamps in a compact format.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()

        rect = option.rect
        value = index.data(Qt.ItemDataRole.DisplayRole)

        # Background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(rect, QColor(THEME.bg_selected))
        else:
            painter.fillRect(rect, QColor(THEME.bg_panel))

        # Format time
        if value:
            if hasattr(value, "strftime"):
                text = value.strftime("%H:%M:%S")
            else:
                text = str(value)
            color = QColor(THEME.text_secondary)
        else:
            text = "-"
            color = QColor(THEME.text_muted)

        # Draw
        painter.setPen(color)
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        text_rect = rect.adjusted(6, 0, -6, 0)
        painter.drawText(
            text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text
        )

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(70, 22)
