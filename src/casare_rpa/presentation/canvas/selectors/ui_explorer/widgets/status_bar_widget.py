"""
Enhanced Status Bar Widget for UI Explorer.

Custom status bar with three sections:
- Left: Target element type and name
- Center: Element match count (for validation results)
- Right: Mode indicator (Browser/Desktop)
"""

from loguru import logger
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QWidget,
)


class StatusSection(QLabel):
    """
    Individual status section with consistent styling.
    """

    def __init__(
        self,
        initial_text: str = "",
        alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(initial_text, parent)
        self.setAlignment(alignment | Qt.AlignmentFlag.AlignVCenter)
        self._apply_style()

    def _apply_style(self) -> None:
        """Apply default styling."""
        self.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-size: 11px;
                padding: 0 8px;
            }
        """)

    def set_success(self) -> None:
        """Set success state (green text)."""
        self.setStyleSheet("""
            QLabel {
                color: #22c55e;
                font-size: 11px;
                font-weight: bold;
                padding: 0 8px;
            }
        """)

    def set_error(self) -> None:
        """Set error state (red text)."""
        self.setStyleSheet("""
            QLabel {
                color: #ef4444;
                font-size: 11px;
                font-weight: bold;
                padding: 0 8px;
            }
        """)

    def set_warning(self) -> None:
        """Set warning state (yellow text)."""
        self.setStyleSheet("""
            QLabel {
                color: #fbbf24;
                font-size: 11px;
                font-weight: bold;
                padding: 0 8px;
            }
        """)

    def set_info(self) -> None:
        """Set info state (blue text)."""
        self.setStyleSheet("""
            QLabel {
                color: #60a5fa;
                font-size: 11px;
                font-weight: bold;
                padding: 0 8px;
            }
        """)

    def reset_style(self) -> None:
        """Reset to default style."""
        self._apply_style()


class UIExplorerStatusBar(QWidget):
    """
    Enhanced status bar for UI Explorer.

    Three-section layout:
    +----------------------------------------------------------+
    | Target: BUTTON 'Start' | 1 match found | Browser (PW)    |
    +----------------------------------------------------------+

    Left section: Current target element type and name
    Center section: Match count during validation
    Right section: Mode indicator (Browser/Desktop)
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(28)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the status bar UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(0)

        # Left section: Target element info
        self._target_label = StatusSection(
            "Target: (none)",
            Qt.AlignmentFlag.AlignLeft,
        )
        self._target_label.setMinimumWidth(200)
        layout.addWidget(self._target_label, 2)

        # Left separator
        layout.addWidget(self._create_separator())

        # Center section: Match count / Status message
        self._match_label = StatusSection(
            "",
            Qt.AlignmentFlag.AlignCenter,
        )
        self._match_label.setMinimumWidth(150)
        layout.addWidget(self._match_label, 1)

        # Right separator
        layout.addWidget(self._create_separator())

        # Right section: Mode indicator
        self._mode_label = StatusSection(
            "Browser (Playwright)",
            Qt.AlignmentFlag.AlignRight,
        )
        self._mode_label.setMinimumWidth(150)
        self._mode_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 10px;
                padding: 0 8px;
            }
        """)
        layout.addWidget(self._mode_label, 1)

        self._apply_styles()

    def _create_separator(self) -> QFrame:
        """Create a vertical separator line."""
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("background: #3a3a3a;")
        sep.setFixedWidth(1)
        return sep

    def _apply_styles(self) -> None:
        """Apply status bar styling."""
        self.setStyleSheet("""
            QWidget {
                background: #252525;
                border-top: 1px solid #3a3a3a;
            }
        """)

    # =========================================================================
    # Public API
    # =========================================================================

    def set_target_element(
        self,
        element_type: str,
        element_name: str | None = None,
    ) -> None:
        """
        Set the target element display.

        Args:
            element_type: Element type (BUTTON, INPUT, DIV, etc.)
            element_name: Optional element name/text
        """
        if not element_type:
            self._target_label.setText("Target: (none)")
            self._target_label.reset_style()
            return

        display = f"Target: {element_type.upper()}"
        if element_name:
            # Truncate long names
            name = element_name[:30] + "..." if len(element_name) > 30 else element_name
            display += f" '{name}'"

        self._target_label.setText(display)
        self._target_label.reset_style()
        logger.debug(f"Status bar target: {display}")

    def set_match_count(self, count: int) -> None:
        """
        Set the match count display.

        Args:
            count: Number of matching elements
        """
        if count == 0:
            self._match_label.setText("No matches")
            self._match_label.set_error()
        elif count == 1:
            self._match_label.setText("1 match found")
            self._match_label.set_success()
        else:
            self._match_label.setText(f"{count} matches found")
            self._match_label.set_warning()

    def set_status_message(self, message: str, state: str = "info") -> None:
        """
        Set a status message in the center section.

        Args:
            message: Message to display
            state: "info", "success", "warning", "error"
        """
        self._match_label.setText(message)

        if state == "success":
            self._match_label.set_success()
        elif state == "error":
            self._match_label.set_error()
        elif state == "warning":
            self._match_label.set_warning()
        else:
            self._match_label.set_info()

    def clear_status_message(self) -> None:
        """Clear the center status message."""
        self._match_label.setText("")
        self._match_label.reset_style()

    def set_mode(self, mode: str) -> None:
        """
        Set the mode indicator.

        Args:
            mode: "browser" or "desktop"
        """
        if mode.lower() == "browser":
            self._mode_label.setText("Browser (Playwright)")
        elif mode.lower() == "desktop":
            self._mode_label.setText("Desktop (UIAutomation)")
        else:
            self._mode_label.setText(f"{mode.capitalize()}")

        logger.debug(f"Status bar mode: {mode}")

    def show_validation_result(self, count: int, time_ms: float) -> None:
        """
        Show validation result.

        Args:
            count: Number of matching elements
            time_ms: Time taken in milliseconds
        """
        if count == 0:
            self._match_label.setText(f"No matches ({time_ms:.0f}ms)")
            self._match_label.set_error()
        elif count == 1:
            self._match_label.setText(f"1 match ({time_ms:.0f}ms)")
            self._match_label.set_success()
        else:
            self._match_label.setText(f"{count} matches ({time_ms:.0f}ms)")
            self._match_label.set_warning()

    def show_picking_active(self, picking_type: str = "element") -> None:
        """
        Show picking mode active indicator.

        Args:
            picking_type: "element" or "anchor"
        """
        if picking_type == "anchor":
            self._match_label.setText("Click on anchor element...")
        else:
            self._match_label.setText("Click on element to select...")
        self._match_label.set_info()

    def show_highlight_active(self, active: bool) -> None:
        """
        Show highlight mode indicator.

        Args:
            active: Whether highlight is active
        """
        if active:
            self._match_label.setText("Highlight enabled")
            self._match_label.set_info()
        else:
            self.clear_status_message()

    def set_anchor_element(
        self,
        element_type: str,
        element_name: str | None = None,
    ) -> None:
        """
        Set the anchor element display (appends to target).

        Args:
            element_type: Element type (BUTTON, LABEL, etc.)
            element_name: Optional element name/text
        """
        if not element_type:
            return

        display = f"Anchor: {element_type.upper()}"
        if element_name:
            name = element_name[:20] + "..." if len(element_name) > 20 else element_name
            display += f" '{name}'"

        # Update target label to show both anchor and target
        current_target = self._target_label.text()
        if current_target.startswith("Target:"):
            # Append anchor info
            self._target_label.setText(f"{display} → {current_target}")
        else:
            self._target_label.setText(display)

        self._target_label.setStyleSheet("""
            QLabel {
                color: #60a5fa;
                font-size: 11px;
                font-weight: bold;
                padding: 0 8px;
            }
        """)
        logger.debug(f"Status bar anchor: {display}")

    def clear_anchor_element(self) -> None:
        """Clear the anchor element display."""
        current = self._target_label.text()
        if "→" in current:
            # Remove anchor part, keep target
            parts = current.split("→")
            if len(parts) > 1:
                self._target_label.setText(parts[-1].strip())
        self._target_label.reset_style()
