"""
Custom modernized widgets for NodeGraphQt.

This module provides proper subclasses for NodeGraphQt's NodeComboBox and NodeCheckBox,
integrating our custom styling and z-order fixes without monkey-patching instances.
"""

from NodeGraphQt.widgets.node_widgets import NodeCheckBox, NodeComboBox
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QComboBox, QSizePolicy

from casare_rpa.presentation.canvas.theme import THEME

# Raised z-value when combo popup is open
COMBO_RAISED_Z = 10000


class CasareComboBox(NodeComboBox):
    """
    Subclass of NodeComboBox that fixes combo dropdown z-order in QGraphicsProxyWidget.
    """

    @staticmethod
    def apply_fix(instance: NodeComboBox) -> None:
        """Apply z-fix to an existing NodeComboBox instance."""
        if not hasattr(instance, "_original_z"):
            instance._original_z = instance.zValue()

        combo = instance.get_custom_widget()
        if combo and isinstance(combo, QComboBox):
            original_show_popup = combo.showPopup
            original_hide_popup = combo.hidePopup

            def patched_show_popup():
                """Raise z-value when popup opens."""
                instance.setZValue(COMBO_RAISED_Z)
                original_show_popup()

            def patched_hide_popup():
                """Restore original z-value when popup closes."""
                try:
                    original_hide_popup()
                    if hasattr(instance, "_original_z"):
                        instance.setZValue(instance._original_z)
                except RuntimeError:
                    pass

            combo.showPopup = patched_show_popup
            combo.hidePopup = patched_hide_popup

    def __init__(self, parent=None, name="", label="", items: list[str] | None = None):
        super().__init__(parent, name, label, items)
        self.apply_fix(self)


class CasareCheckBox(NodeCheckBox):
    """
    Subclass of NodeCheckBox that applies dark blue styling and font size fixes.
    """

    _checkmark_path: str | None = None

    @classmethod
    def _get_checkmark_path(cls) -> str:
        """Get the checkmark asset path, cached for performance."""
        if cls._checkmark_path is None:
            from pathlib import Path

            # Asset is in presentation/canvas/assets directory
            canvas_dir = Path(__file__).parent.parent
            asset_path = canvas_dir / "assets" / "checkmark.svg"
            cls._checkmark_path = asset_path.as_posix()
        return cls._checkmark_path

    @staticmethod
    def apply_styling(instance: NodeCheckBox) -> None:
        """Apply styling to an existing NodeCheckBox instance."""
        checkbox = instance.get_custom_widget()
        if not checkbox:
            return

        # Fix NodeGraphQt's large font - use 8pt to match other widgets
        font = checkbox.font()
        font.setPointSize(8)
        checkbox.setFont(font)

        # Fix NodeGraphQt's hardcoded max width (140px) that truncates labels
        group_box = instance.widget()
        if group_box:
            group_box.setMaximumWidth(16777215)  # Qt's QWIDGETSIZE_MAX

            fm = QFontMetrics(font)
            try:
                title_text = instance.get_label() or ""
            except Exception:
                title_text = ""

            checkbox_text = checkbox.text() or ""
            title_width = fm.horizontalAdvance(title_text) if title_text else 0
            checkbox_text_width = fm.horizontalAdvance(checkbox_text) if checkbox_text else 0

            indicator_width = 14
            indicator_spacing = 6
            horizontal_padding = 18
            required_width = max(
                200,
                title_width + horizontal_padding,
                indicator_width + indicator_spacing + checkbox_text_width + horizontal_padding,
            )

            group_box.setMinimumWidth(required_width)
            group_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            checkbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            checkbox.setMinimumWidth(max(0, required_width - horizontal_padding))

            try:
                instance.setMinimumWidth(required_width)
                instance.resize(required_width, group_box.sizeHint().height())
            except Exception:
                pass

            group_box.adjustSize()

        checkmark_path = CasareCheckBox._get_checkmark_path()
        checkbox_style = f"""
            QCheckBox {{
                color: {THEME.text_secondary};
                spacing: 6px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border: 1px solid { THEME.border_light };
                border-radius: 3px;
                background-color: { THEME.bg_darkest };
            }}
            QCheckBox::indicator:unchecked:hover {{
                border-color: { THEME.accent_primary };
            }}
            QCheckBox::indicator:checked {{
                background-color: { THEME.accent_primary };
                border-color: { THEME.accent_primary };
                image: url({checkmark_path});
            }}
            QCheckBox::indicator:checked:hover {{
                background-color: { THEME.accent_hover };
                border-color: { THEME.accent_hover };
            }}
        """
        existing_style = checkbox.styleSheet()
        checkbox.setStyleSheet(existing_style + checkbox_style)

    def __init__(self, parent=None, name="", label="", text="", state=False):
        super().__init__(parent, name, label, text, state)
        self.apply_styling(self)
