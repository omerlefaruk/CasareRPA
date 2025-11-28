"""
Custom Node Widget Wrappers for NodeGraphQt.

This module provides wrapper classes that extend NodeGraphQt's widget classes
with custom behavior and styling, replacing the monkey-patches in node_graph_widget.py.

Classes:
    CasareComboBox: Fixes combo dropdown z-order issue
    CasareCheckBox: Adds dark blue checkbox styling
    CasareLivePipe: Fixes draw_index_pointer text_pos bug
    CasarePipeItem: Fixes draw_path viewer None crash
"""

from pathlib import Path
from typing import List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTransform
from PySide6.QtWidgets import QComboBox

from loguru import logger

# Raised z-value when combo popup is open
COMBO_RAISED_Z = 10000


class CasareComboBox:
    """
    Mixin/wrapper that fixes combo dropdown z-order in QGraphicsProxyWidget.

    When QComboBox is embedded in a QGraphicsProxyWidget, the dropdown popup
    can get clipped by other widgets in the same node. This fix ensures the
    popup appears as a top-level window above all graphics items by raising
    the z-value when the popup is shown.

    Usage:
        # Apply to a NodeComboBox instance
        CasareComboBox.apply_fix(node_combo_widget)
    """

    @staticmethod
    def apply_fix(node_widget) -> None:
        """
        Apply z-order fix to a NodeComboBox widget.

        Args:
            node_widget: NodeComboBox instance from NodeGraphQt
        """
        # Store original z-value for restoration
        node_widget._original_z = node_widget.zValue()

        # Get the combo widget
        combo = node_widget.get_custom_widget()
        if not combo or not isinstance(combo, QComboBox):
            return

        # Store original methods
        original_show_popup = combo.showPopup
        original_hide_popup = combo.hidePopup

        def patched_show_popup():
            """Raise z-value when popup opens."""
            node_widget.setZValue(COMBO_RAISED_Z)
            original_show_popup()

        def patched_hide_popup():
            """Restore original z-value when popup closes."""
            try:
                original_hide_popup()
                if hasattr(node_widget, "_original_z"):
                    node_widget.setZValue(node_widget._original_z)
            except RuntimeError:
                # Widget already deleted
                pass

        # Apply patches
        combo.showPopup = patched_show_popup
        combo.hidePopup = patched_hide_popup


class CasareCheckBox:
    """
    Mixin/wrapper that applies dark blue checkbox styling with white checkmark.

    Provides a consistent VSCode-like dark theme styling for checkboxes
    inside nodes, with proper hover and checked states.

    Usage:
        # Apply to a NodeCheckBox instance
        CasareCheckBox.apply_styling(node_checkbox_widget)
    """

    # Path to checkmark SVG asset
    _checkmark_path: Optional[str] = None

    @classmethod
    def _get_checkmark_path(cls) -> str:
        """Get the checkmark asset path, cached for performance."""
        if cls._checkmark_path is None:
            # Asset is in old canvas/assets directory
            # TODO: Move to presentation/canvas/assets in future migration phase
            from pathlib import Path

            canvas_dir = Path(__file__).parent.parent.parent.parent / "canvas"
            asset_path = canvas_dir / "assets" / "checkmark.svg"
            cls._checkmark_path = asset_path.as_posix()
        return cls._checkmark_path

    @classmethod
    def apply_styling(cls, node_widget) -> None:
        """
        Apply dark blue styling to a NodeCheckBox widget.

        Args:
            node_widget: NodeCheckBox instance from NodeGraphQt
        """
        checkbox = node_widget.get_custom_widget()
        if not checkbox:
            return

        checkmark_path = cls._get_checkmark_path()

        # Dark blue checkbox styling with white checkmark
        checkbox_style = f"""
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid #3E3E42;
                border-radius: 3px;
                background-color: #252526;
            }}

            QCheckBox::indicator:unchecked:hover {{
                border-color: #0063B1;
            }}

            QCheckBox::indicator:checked {{
                background-color: #0063B1;
                border-color: #0063B1;
                image: url({checkmark_path});
            }}

            QCheckBox::indicator:checked:hover {{
                background-color: #005A9E;
                border-color: #005A9E;
            }}
        """

        # Append to existing stylesheet
        existing_style = checkbox.styleSheet()
        checkbox.setStyleSheet(existing_style + checkbox_style)


class CasareLivePipe:
    """
    Wrapper that fixes the draw_index_pointer text_pos bug in LivePipeItem.

    The original NodeGraphQt code has a bug where text_pos is undefined
    when viewer_layout_direction() returns None. This wrapper provides
    a fixed version that always initializes text_pos with a default value.

    Usage:
        # Apply fix at module load time
        CasareLivePipe.apply_fix()
    """

    @staticmethod
    def apply_fix() -> None:
        """Apply the draw_index_pointer fix to LivePipeItem."""
        try:
            from NodeGraphQt.qgraphics.pipe import (
                LayoutDirectionEnum,
                LivePipeItem,
                PipeEnum,
                PortTypeEnum,
            )

            original_draw_index_pointer = LivePipeItem.draw_index_pointer

            def fixed_draw_index_pointer(self, start_port, cursor_pos, color=None):
                """Fixed version that always initializes text_pos."""
                if start_port is None:
                    return

                text_rect = self._idx_text.boundingRect()
                transform = QTransform()
                transform.translate(cursor_pos.x(), cursor_pos.y())

                layout_dir = self.viewer_layout_direction()

                # FIXED: Always initialize text_pos with default value
                text_pos = (
                    cursor_pos.x() - (text_rect.width() / 2),
                    cursor_pos.y() - (text_rect.height() * 1.25),
                )

                # Use == instead of 'is' for reliable enum comparison
                if layout_dir == LayoutDirectionEnum.VERTICAL.value:
                    text_pos = (
                        cursor_pos.x() + (text_rect.width() / 2.5),
                        cursor_pos.y() - (text_rect.height() / 2),
                    )
                    if start_port.port_type == PortTypeEnum.OUT.value:
                        transform.rotate(180)
                elif layout_dir == LayoutDirectionEnum.HORIZONTAL.value:
                    text_pos = (
                        cursor_pos.x() - (text_rect.width() / 2),
                        cursor_pos.y() - (text_rect.height() * 1.25),
                    )
                    if start_port.port_type == PortTypeEnum.IN.value:
                        transform.rotate(-90)
                    else:
                        transform.rotate(90)

                self._idx_text.setPos(*text_pos)
                self._idx_text.setPlainText("{}".format(start_port.name))
                self._idx_pointer.setPolygon(transform.map(self._poly))

                pen_color = QColor(*PipeEnum.HIGHLIGHT_COLOR.value)
                if isinstance(color, (list, tuple)):
                    pen_color = QColor(*color)

                pen = self._idx_pointer.pen()
                pen.setColor(pen_color)
                self._idx_pointer.setBrush(pen_color.darker(300))
                self._idx_pointer.setPen(pen)

            LivePipeItem.draw_index_pointer = fixed_draw_index_pointer
            logger.debug("CasareLivePipe: Fixed draw_index_pointer text_pos bug")

        except ImportError as e:
            logger.warning(f"CasareLivePipe: Could not import LivePipeItem: {e}")
        except Exception as e:
            logger.warning(f"CasareLivePipe: Could not apply fix: {e}")


class CasarePipeItemFix:
    """
    Wrapper that fixes the draw_path viewer None crash in PipeItem.

    The original NodeGraphQt code crashes when viewer() returns None,
    which can happen during workflow loading or undo/redo operations.
    This wrapper adds a None check before proceeding.

    Usage:
        # Apply fix at module load time
        CasarePipeItemFix.apply_fix()
    """

    @staticmethod
    def apply_fix() -> None:
        """Apply the draw_path fix to PipeItem."""
        try:
            from NodeGraphQt.qgraphics.pipe import PipeItem

            original_draw_path = PipeItem.draw_path

            def fixed_draw_path(self, start_port, end_port=None, cursor_pos=None):
                """Patched draw_path that handles viewer() returning None."""
                # Check if viewer is available before proceeding
                viewer = self.viewer()
                if viewer is None:
                    # Viewer not ready - skip drawing, will be called again later
                    return

                # Call original method
                return original_draw_path(self, start_port, end_port, cursor_pos)

            PipeItem.draw_path = fixed_draw_path
            logger.debug("CasarePipeItemFix: Fixed draw_path viewer None crash")

        except ImportError as e:
            logger.warning(f"CasarePipeItemFix: Could not import PipeItem: {e}")
        except Exception as e:
            logger.warning(f"CasarePipeItemFix: Could not apply fix: {e}")


def apply_all_node_widget_fixes() -> None:
    """
    Apply all NodeGraphQt widget fixes.

    This should be called once at module load time to apply all fixes
    before any NodeGraphQt widgets are created.

    The fixes include:
    - LivePipeItem.draw_index_pointer text_pos bug fix
    - PipeItem.draw_path viewer None crash fix

    Note: CasareComboBox and CasareCheckBox fixes are applied per-widget
    via the patched __init__ methods installed below.
    """
    CasareLivePipe.apply_fix()
    CasarePipeItemFix.apply_fix()
    _install_widget_init_patches()

    logger.debug("All NodeGraphQt widget fixes applied")


def _install_widget_init_patches() -> None:
    """
    Install patches on NodeComboBox and NodeCheckBox __init__ methods.

    This ensures that every new instance gets the fixes applied automatically.
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeCheckBox, NodeComboBox

        # Patch NodeComboBox
        original_combo_init = NodeComboBox.__init__

        def patched_combo_init(self, parent=None, name="", label="", items=None):
            original_combo_init(self, parent, name, label, items)
            CasareComboBox.apply_fix(self)

        NodeComboBox.__init__ = patched_combo_init

        # Patch NodeCheckBox
        original_checkbox_init = NodeCheckBox.__init__

        def patched_checkbox_init(
            self, parent=None, name="", label="", text="", state=False
        ):
            original_checkbox_init(self, parent, name, label, text, state)
            CasareCheckBox.apply_styling(self)

        NodeCheckBox.__init__ = patched_checkbox_init

        logger.debug("Installed NodeComboBox and NodeCheckBox init patches")

    except ImportError as e:
        logger.warning(f"Could not install widget init patches: {e}")
    except Exception as e:
        logger.warning(f"Error installing widget init patches: {e}")
