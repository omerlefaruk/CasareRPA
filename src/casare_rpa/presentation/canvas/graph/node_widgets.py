"""
Custom Node Widget Wrappers for NodeGraphQt.

This module provides wrapper classes that extend NodeGraphQt's widget classes
with custom behavior and styling, replacing the monkey-patches in node_graph_widget.py.

Classes:
    CasareComboBox: Fixes combo dropdown z-order issue
    CasareCheckBox: Adds dark blue checkbox styling
    CasareLivePipe: Fixes draw_index_pointer text_pos bug
    CasarePipeItem: Fixes draw_path viewer None crash
    NodeFilePathWidget: File path input with browse button
    NodeDirectoryPathWidget: Directory path input with browse button
"""

from typing import Optional

from PySide6.QtGui import QColor, QFont, QTransform
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QSizePolicy,
)

from loguru import logger

# Import variable picker components
from casare_rpa.presentation.canvas.ui.widgets.variable_picker import (
    VariableAwareLineEdit,
)

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
            from pathlib import Path

            # Asset is in presentation/canvas/assets directory
            canvas_dir = Path(__file__).parent.parent
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

        # Fix NodeGraphQt's large font (11pt) - use 8pt to match other widgets
        from PySide6.QtGui import QFont, QFontMetrics

        font = checkbox.font()
        font.setPointSize(8)
        checkbox.setFont(font)

        # Fix NodeGraphQt's hardcoded max width (140px) that truncates labels
        # Remove the constraint and set proper minimum width based on text
        group_box = node_widget.widget()
        if group_box:
            group_box.setMaximumWidth(16777215)  # Qt's QWIDGETSIZE_MAX
            # Calculate required width: checkbox indicator (14px) + spacing (6px) + text
            fm = QFontMetrics(font)
            text_width = fm.horizontalAdvance(checkbox.text())
            min_width = 14 + 6 + text_width + 8  # indicator + spacing + text + padding
            checkbox.setMinimumWidth(min_width)
            group_box.setMinimumWidth(min_width)
            group_box.adjustSize()

        checkmark_path = cls._get_checkmark_path()

        # Dark blue checkbox styling with white checkmark - smaller indicator for 8pt font
        checkbox_style = f"""
            QCheckBox {{
                color: #a1a1aa;
                spacing: 6px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border: 1px solid #52525b;
                border-radius: 3px;
                background-color: #18181b;
            }}

            QCheckBox::indicator:unchecked:hover {{
                border-color: #6366f1;
            }}

            QCheckBox::indicator:checked {{
                background-color: #6366f1;
                border-color: #6366f1;
                image: url({checkmark_path});
            }}

            QCheckBox::indicator:checked:hover {{
                background-color: #4f46e5;
                border-color: #4f46e5;
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

            _original_draw_index_pointer = LivePipeItem.draw_index_pointer  # noqa: F841

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

        except ImportError as e:
            logger.warning(f"CasareLivePipe: Could not import LivePipeItem: {e}")
        except Exception as e:
            logger.warning(f"CasareLivePipe: Could not apply fix: {e}")


class CasarePipeItemFix:
    """
    Wrapper that fixes PipeItem draw_path viewer None crash.

    The original NodeGraphQt code crashes when viewer() returns None,
    which can happen during workflow loading or undo/redo operations.

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
                """Patched draw_path with viewer None check."""
                if not start_port:
                    return

                # Check if viewer is available - prevents crash during loading/undo
                viewer = self.viewer()
                if viewer is None and not cursor_pos:
                    return

                # Use original implementation
                return original_draw_path(self, start_port, end_port, cursor_pos)

            PipeItem.draw_path = fixed_draw_path

        except ImportError as e:
            logger.warning(f"CasarePipeItemFix: Could not import PipeItem: {e}")
        except Exception as e:
            logger.warning(f"CasarePipeItemFix: Could not apply fix: {e}")


class CasareNodeDataDropFix:
    """
    Wrapper that fixes the _on_node_data_dropped QUrl TypeError in NodeGraph.

    The original NodeGraphQt code fails when dragging files onto the canvas
    because it tries to join QUrl objects as strings without converting them.

    Error: TypeError: sequence item 0: expected str instance, PySide6.QtCore.QUrl found

    Usage:
        # Apply fix at module load time
        CasareNodeDataDropFix.apply_fix()
    """

    @staticmethod
    def apply_fix() -> None:
        """Apply the _on_node_data_dropped fix to NodeGraph."""
        try:
            from NodeGraphQt.base.graph import NodeGraph

            original_on_node_data_dropped = NodeGraph._on_node_data_dropped

            def fixed_on_node_data_dropped(self, data, pos):
                """Patched version that converts QUrl objects to strings."""
                from PySide6.QtCore import QUrl

                # Convert any QUrl objects in the data to strings
                if hasattr(data, "urls") and callable(data.urls):
                    urls = data.urls()
                    if urls:
                        # Convert QUrl to string paths
                        converted_urls = []
                        for url in urls:
                            if isinstance(url, QUrl):
                                converted_urls.append(
                                    url.toLocalFile() or url.toString()
                                )
                            else:
                                converted_urls.append(str(url))
                        # Create modified data with string paths
                        # The original code expects a list that can be joined
                        data._converted_paths = converted_urls

                # Call original method
                return original_on_node_data_dropped(self, data, pos)

            NodeGraph._on_node_data_dropped = fixed_on_node_data_dropped

        except ImportError as e:
            logger.warning(f"CasareNodeDataDropFix: Could not import NodeGraph: {e}")
        except Exception as e:
            logger.warning(f"CasareNodeDataDropFix: Could not apply fix: {e}")


# Maximum length for port labels before truncation
PORT_LABEL_MAX_LENGTH = 15


class CasareNodeBaseFontFix:
    """
    Fix for NodeBase._add_port() font handling bug and port label truncation.

    The original NodeGraphQt code at node_base.py:921-922 has:
        text.font().setPointSize(8)
        text.setFont(text.font())

    This is buggy because text.font() returns a copy. The setPointSize(8)
    modifies the copy, then setFont() applies the unmodified original font
    which may have -1 as its point size if no font was explicitly set.

    This fix patches _add_port to:
    1. Properly create and set the font
    2. Truncate long port labels (>15 chars) with ellipsis
    3. Set tooltip with full label on hover

    Usage:
        # Apply fix at module load time
        CasareNodeBaseFontFix.apply_fix()
    """

    @staticmethod
    def apply_fix() -> None:
        """Apply the font fix and port label truncation to NodeItem._add_port."""
        try:
            from PySide6.QtGui import QFont, QFontMetrics
            from PySide6.QtWidgets import QGraphicsTextItem
            from NodeGraphQt.qgraphics.node_base import (
                NodeItem,
                PortTypeEnum,
                ITEM_CACHE_MODE,
            )

            _original_add_port = NodeItem._add_port  # noqa: F841

            def fixed_add_port(self, port):
                """Patched version with font fix and port label truncation."""
                port_name = port.name
                display_name = port_name

                # Create font with explicit size
                font = QFont()
                font.setPointSize(8)

                # Truncate long labels with ellipsis (Phase 1 UI improvement)
                if len(port_name) > PORT_LABEL_MAX_LENGTH:
                    # Use QFontMetrics.elidedText for proper truncation
                    fm = QFontMetrics(font)
                    # Calculate max width based on max chars (approx 6px per char at 8pt)
                    max_width = PORT_LABEL_MAX_LENGTH * 6
                    from PySide6.QtCore import Qt

                    display_name = fm.elidedText(
                        port_name, Qt.TextElideMode.ElideRight, max_width
                    )

                text = QGraphicsTextItem(display_name, self)
                text.setFont(font)
                text.setVisible(port.display_name)
                text.setCacheMode(ITEM_CACHE_MODE)

                # Set tooltip with full port name for truncated labels
                if display_name != port_name:
                    text.setToolTip(f"{port_name}")
                else:
                    # Standard tooltip for non-truncated labels
                    conn_type = "multi" if port.multi_connection else "single"
                    text.setToolTip(f"{port_name}: ({conn_type})")

                if port.port_type == PortTypeEnum.IN.value:
                    self._input_items[port] = text
                elif port.port_type == PortTypeEnum.OUT.value:
                    self._output_items[port] = text
                if self.scene():
                    self.post_init()
                return port

            NodeItem._add_port = fixed_add_port

        except ImportError as e:
            logger.warning(f"CasareNodeBaseFontFix: Could not import NodeItem: {e}")
        except Exception as e:
            logger.warning(f"CasareNodeBaseFontFix: Could not apply fix: {e}")


class CasareViewerFontFix:
    """
    Fix for NodeViewer font initialization that can cause QFont -1 warnings.

    When QGraphicsTextItem.font() returns a font without an explicit point size,
    it may have -1 as the point size. This fix ensures fonts are properly
    initialized before calling setPointSize().

    Usage:
        # Apply fix at module load time
        CasareViewerFontFix.apply_fix()
    """

    @staticmethod
    def apply_fix() -> None:
        """Apply the font fix to NodeViewer._set_viewer_pan_zoom."""
        try:
            # Patch QGraphicsTextItem to ensure font() always returns valid font
            from PySide6.QtWidgets import QGraphicsTextItem

            original_font = QGraphicsTextItem.font

            def safe_font(self):
                """Return font, ensuring point size is valid (not -1)."""
                f = original_font(self)
                if f.pointSize() <= 0:
                    # Set a reasonable default if point size is invalid
                    f.setPointSize(9)
                return f

            QGraphicsTextItem.font = safe_font

        except Exception as e:
            logger.warning(f"CasareViewerFontFix: Could not apply fix: {e}")


class CasareQFontFix:
    """
    Fix for QFont.setPointSize being called with invalid values (-1 or 0).

    NodeGraphQt and Qt internally may call setPointSize with -1 when fonts
    are not properly initialized. This fix patches QFont.setPointSize to
    silently correct invalid values to a reasonable default.

    Usage:
        CasareQFontFix.apply_fix()
    """

    _applied = False

    @staticmethod
    def apply_fix() -> None:
        """Patch QFont.setPointSize to guard against invalid values."""
        if CasareQFontFix._applied:
            return

        try:
            original_setPointSize = QFont.setPointSize

            def safe_setPointSize(self, size: int) -> None:
                """Set point size, correcting invalid values."""
                if size <= 0:
                    size = 9  # Default to 9pt for invalid sizes
                original_setPointSize(self, size)

            QFont.setPointSize = safe_setPointSize
            CasareQFontFix._applied = True

        except Exception as e:
            logger.warning(f"CasareQFontFix: Could not apply fix: {e}")


class CasareNodeItemPaintFix:
    """
    Custom paint fix for NodeItem to provide VSCode-style selection border.

    Replaces the default NodeItem.paint with a version that:
    - Uses rounded corners (8px radius)
    - Shows thick blue border (3px) when selected (#007ACC)
    - Prevents dotted selection boxes on child items

    Usage:
        # Apply fix at module load time
        CasareNodeItemPaintFix.apply_fix()
    """

    @staticmethod
    def apply_fix() -> None:
        """Apply the custom paint fix to NodeItem."""
        try:
            from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
            from PySide6.QtCore import Qt
            from NodeGraphQt.qgraphics.node_base import NodeItem

            def patched_paint(self, painter, option, widget):
                """Custom paint with thicker blue border and rounded corners."""
                # Temporarily clear selection for child items to prevent dotted boxes
                option_copy = option.__class__(option)
                option_copy.state &= ~option_copy.state.State_Selected

                painter.save()
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

                # Get bounding rect
                rect = self.boundingRect()

                # Determine colors
                bg_color = QColor(*self.color)
                border_color = QColor(*self.border_color)

                if self.selected:
                    # GLOW EFFECT: Multi-layered soft border
                    # 1. Inner focus ring (Indigo 500)
                    border_width = 2.0
                    border_color = QColor("#6366f1")

                    # 2. Outer glow (Indigo 500 with alpha) - rendered below
                    glow_pen = QPen(QColor(99, 102, 241, 60), 6.0)
                    glow_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                    painter.setPen(glow_pen)
                    painter.drawRoundedRect(rect, 12.0, 12.0)
                else:
                    border_width = 1.0

                # Create rounded rectangle path with 12px radius (Modern look)
                radius = 12.0
                path = QPainterPath()
                path.addRoundedRect(rect, radius, radius)

                # Fill background (Base color)
                painter.fillPath(path, bg_color)

                # Draw border
                pen = QPen(border_color, border_width)
                pen.setCosmetic(self.viewer().get_zoom() < 0.0)
                painter.strokePath(path, pen)

                painter.restore()

                # Draw child items without selection indicators
                for child in self.childItems():
                    if child.isVisible():
                        painter.save()
                        painter.translate(child.pos())
                        child.paint(painter, option_copy, widget)
                        painter.restore()

            NodeItem.paint = patched_paint

        except ImportError as e:
            logger.warning(f"CasareNodeItemPaintFix: Could not import NodeItem: {e}")
        except Exception as e:
            logger.warning(f"CasareNodeItemPaintFix: Could not apply fix: {e}")


class CasarePortItemShapeFix:
    """
    Fix to replace NodeGraphQt's circle-only port rendering with custom shapes.

    This patches PortItem.paint to use our draw_port_shape function which
    renders different shapes based on DataType (diamond for boolean, square
    for list, hexagon for dict, triangle for exec, etc.).

    Provides visual accessibility for color-blind users per WCAG 2.1.
    """

    @staticmethod
    def apply_fix() -> None:
        """Apply the port shape rendering fix."""
        try:
            from NodeGraphQt.qgraphics.port import PortItem
            from NodeGraphQt.constants import PortTypeEnum
            from PySide6.QtCore import QPointF, QRectF
            from PySide6.QtGui import QPainter, QColor, QPen

            from casare_rpa.presentation.canvas.graph.port_shapes import draw_port_shape
            from casare_rpa.domain.value_objects.types import DataType

            # Store original paint method
            original_paint = PortItem.paint

            def patched_paint(self, painter, option, widget):
                """
                Draw the port with shape based on data type.

                Falls back to original paint for non-CasareRPA nodes.
                """
                painter.save()

                # Calculate port rect (same as original)
                rect_w = self._width / 1.8
                rect_h = self._height / 1.8
                rect_x = self.boundingRect().center().x() - (rect_w / 2)
                rect_y = self.boundingRect().center().y() - (rect_h / 2)
                port_rect = QRectF(rect_x, rect_y, rect_w, rect_h)
                center = port_rect.center()
                size = rect_w / 2

                # Determine colors based on state
                from NodeGraphQt.constants import PortEnum

                if self._hovered:
                    fill_color = PortEnum.HOVER_COLOR.value
                    border_color = PortEnum.HOVER_BORDER_COLOR.value
                elif self.connected_pipes:
                    fill_color = PortEnum.ACTIVE_COLOR.value
                    border_color = PortEnum.ACTIVE_BORDER_COLOR.value
                else:
                    fill_color = self.color
                    border_color = self.border_color

                # Try to get data type from visual node
                data_type = None
                is_exec = False
                is_output = self.port_type == PortTypeEnum.OUT.value

                try:
                    # Get parent node item
                    node_item = self.node
                    if node_item:
                        # Get visual node via NodeGraphQt's internal _node attribute
                        visual_node = getattr(node_item, "_node", None)
                        if visual_node and hasattr(visual_node, "get_port_type"):
                            port_name = self.name
                            data_type = visual_node.get_port_type(port_name)
                            # Check if it's an exec port (None means exec)
                            if hasattr(visual_node, "is_exec_port"):
                                is_exec = visual_node.is_exec_port(port_name)
                            elif data_type is None:
                                is_exec = True
                except Exception:
                    pass  # Fall through to default circle

                # Draw port shape
                draw_port_shape(
                    painter=painter,
                    center=QPointF(center.x(), center.y()),
                    size=size,
                    data_type=data_type,
                    fill_color=fill_color,
                    border_color=border_color,
                    is_exec=is_exec,
                    is_output=is_output,
                )

                # Draw connected indicator (inner shape) for non-hovered connected ports
                if self.connected_pipes and not self._hovered:
                    inner_size = size * 0.4
                    border_qcolor = QColor(*border_color)
                    painter.setPen(QPen(border_qcolor, 1.6))
                    painter.setBrush(border_qcolor)
                    painter.drawEllipse(center, inner_size, inner_size)
                elif self._hovered:
                    # Hover indicator
                    if self.multi_connection:
                        inner_size = size * 0.55
                        border_qcolor = QColor(*border_color)
                        fill_qcolor = QColor(*fill_color)
                        painter.setPen(QPen(border_qcolor, 1.4))
                        painter.setBrush(fill_qcolor)
                    else:
                        inner_size = size * 0.3
                        border_qcolor = QColor(*border_color)
                        painter.setPen(QPen(border_qcolor, 1.6))
                        painter.setBrush(border_qcolor)
                    painter.drawEllipse(center, inner_size, inner_size)

                painter.restore()

            PortItem.paint = patched_paint

        except ImportError as e:
            logger.warning(f"CasarePortItemShapeFix: Could not import: {e}")
        except Exception as e:
            logger.warning(f"CasarePortItemShapeFix: Could not apply fix: {e}")


def apply_all_node_widget_fixes() -> None:
    """
    Apply all NodeGraphQt widget fixes.

    This should be called once at module load time to apply all fixes
    before any NodeGraphQt widgets are created.

    The fixes include:
    - LivePipeItem.draw_index_pointer text_pos bug fix
    - PipeItem.draw_path viewer None crash fix
    - NodeGraph._on_node_data_dropped QUrl TypeError fix
    - NodeBaseItem._add_port font handling fix
    - QGraphicsTextItem.font() -1 point size fix
    - QFont.setPointSize -1 value fix
    - NodeItem.paint selection styling fix
    - PortItem.paint custom shapes per DataType (accessibility)

    Note: CasareComboBox and CasareCheckBox fixes are applied per-widget
    via the patched __init__ methods installed below.
    """
    # Apply QFont fix FIRST - it patches the core Qt class
    CasareQFontFix.apply_fix()
    CasareLivePipe.apply_fix()
    CasarePipeItemFix.apply_fix()
    CasareNodeDataDropFix.apply_fix()
    CasareNodeBaseFontFix.apply_fix()
    CasareViewerFontFix.apply_fix()
    CasareNodeItemPaintFix.apply_fix()
    CasarePortItemShapeFix.apply_fix()
    _install_widget_init_patches()


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

    except ImportError as e:
        logger.warning(f"Could not install widget init patches: {e}")
    except Exception as e:
        logger.warning(f"Error installing widget init patches: {e}")


# =============================================================================
# Variable-Aware Text Widget - Direct creation for performance
# =============================================================================


def create_variable_text_widget(
    name: str,
    label: str,
    text: str = "",
    placeholder_text: str = "",
    tooltip: str = "",
):
    """
    Factory function to create a variable-aware text input widget.

    PERFORMANCE: This creates the widget directly with VariableAwareLineEdit,
    avoiding the two-step process of creating a standard widget then replacing
    its internal QLineEdit.

    Args:
        name: Property name for the node
        label: Label text displayed above the widget
        text: Initial text value
        placeholder_text: Placeholder text when empty
        tooltip: Tooltip text for the widget

    Returns:
        NodeBaseWidget with VariableAwareLineEdit, or None if unavailable
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget
        from casare_rpa.presentation.canvas.ui.widgets.variable_picker import (
            VariableProvider,
        )
    except ImportError:
        logger.error("NodeGraphQt or variable picker not available")
        return None

    # Create VariableAwareLineEdit directly
    line_edit = VariableAwareLineEdit()
    line_edit.setText(text)
    line_edit.setPlaceholderText(placeholder_text)

    # Apply standard styling with padding for {x} button
    line_edit.setStyleSheet("""
        QLineEdit {
            background: rgb(60, 60, 80);
            border: 1px solid rgb(80, 80, 100);
            border-radius: 3px;
            color: rgba(230, 230, 230, 255);
            padding: 2px 28px 2px 4px;
            selection-background-color: rgba(100, 150, 200, 150);
        }
        QLineEdit:focus {
            background: rgb(70, 70, 90);
            border: 1px solid rgb(100, 150, 200);
        }
    """)

    if tooltip:
        line_edit.setToolTip(tooltip)

    # Connect to global variable provider
    line_edit.set_provider(VariableProvider.get_instance())

    # Create NodeBaseWidget with VariableAwareLineEdit as custom widget
    widget = NodeBaseWidget(parent=None, name=name, label=label)
    widget.set_custom_widget(line_edit)

    # Connect signals
    line_edit.editingFinished.connect(widget.on_value_changed)
    line_edit.variable_inserted.connect(lambda _: widget.on_value_changed())

    # Store reference
    widget._line_edit = line_edit

    # Override get_value and set_value for consistent behavior
    def get_value():
        return line_edit.text()

    def set_value(value):
        line_edit.setText(str(value) if value else "")

    widget.get_value = get_value
    widget.set_value = set_value

    return widget


# =============================================================================
# NodeFilePathWidget - File path input with browse button for NodeGraphQt
# =============================================================================


def create_file_path_widget(
    name: str, label: str, file_filter: str, placeholder: str, text: str = ""
):
    """
    Factory function to create a NodeFilePathWidget.

    This creates a proper NodeBaseWidget subclass instance with file browse functionality.
    Includes variable picker integration via VariableAwareLineEdit - hover to see {x} button.
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget
        from PySide6 import QtWidgets
    except ImportError:
        logger.error("NodeGraphQt not available")
        return None

    # Create the container widget with horizontal layout
    container = QtWidgets.QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    # Set explicit minimum size to ensure visibility
    container.setMinimumHeight(26)
    container.setMinimumWidth(160)
    container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    # Create variable-aware line edit with {x} button for variable insertion
    line_edit = VariableAwareLineEdit()
    line_edit.setText(text)
    line_edit.setPlaceholderText(placeholder)
    line_edit.setMinimumHeight(24)
    line_edit.setMinimumWidth(100)
    line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    # Padding on right side accommodates the {x} variable button
    line_edit.setStyleSheet("""
        QLineEdit {
            background: #3c3c50;
            border: 1px solid #505064;
            border-radius: 3px;
            color: #e6e6e6;
            padding: 2px 28px 2px 4px;
        }
        QLineEdit:focus {
            border: 1px solid #6496c8;
        }
    """)
    layout.addWidget(line_edit, 1)

    # Create browse button - use "..." text for guaranteed cross-platform visibility
    browse_btn = QPushButton("...")
    browse_btn.setFixedSize(30, 24)
    browse_btn.setToolTip("Browse for file")
    # Bright blue background to ensure visibility in graphics scene
    browse_btn.setStyleSheet("""
        QPushButton {
            background-color: #0078d4;
            border: 1px solid #106ebe;
            border-radius: 3px;
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
            padding: 0px;
        }
        QPushButton:hover {
            background-color: #1a86d9;
        }
        QPushButton:pressed {
            background-color: #005a9e;
        }
    """)

    def on_browse():
        import os

        current_path = line_edit.text().strip()
        start_dir = ""
        if current_path:
            if os.path.isdir(current_path):
                start_dir = current_path
            elif os.path.dirname(current_path):
                parent = os.path.dirname(current_path)
                if os.path.isdir(parent):
                    start_dir = parent

        path, _ = QFileDialog.getOpenFileName(
            None,  # Use None for proper modal behavior
            "Select File",
            start_dir,
            file_filter,
        )
        if path:
            line_edit.setText(path)
            # CRITICAL: Manually trigger value change - setText() doesn't emit editingFinished
            # Without this, the property value is never synced to the model
            widget.on_value_changed()
            logger.debug(f"Selected file: {path}")

    browse_btn.clicked.connect(on_browse)
    layout.addWidget(browse_btn)

    # Create NodeBaseWidget and set up
    widget = NodeBaseWidget(parent=None, name=name, label=label)
    widget.set_custom_widget(container)

    # Force geometry update
    container.adjustSize()

    # Connect line edit changes to widget's value changed signal
    line_edit.editingFinished.connect(widget.on_value_changed)

    # Connect variable insertion to trigger value change
    line_edit.variable_inserted.connect(lambda _: widget.on_value_changed())

    # Store reference to line edit for get/set value
    widget._line_edit = line_edit
    widget._browse_btn = browse_btn

    # Override get_value and set_value
    def get_value():
        return line_edit.text()

    def set_value(value):
        line_edit.setText(str(value) if value else "")

    widget.get_value = get_value
    widget.set_value = set_value

    return widget


class NodeFilePathWidget:
    """
    File path widget for NodeGraphQt nodes.

    Provides a text input with a folder browse button that opens
    Windows Explorer to select a file.

    Usage in visual node:
        from casare_rpa.presentation.canvas.graph.node_widgets import NodeFilePathWidget

        def __init__(self):
            super().__init__()
            # Add file path widget with Excel filter
            widget = NodeFilePathWidget(
                name="file_path",
                label="Excel File",
                file_filter="Excel Files (*.xlsx *.xls);;All Files (*.*)",
            )
            self.add_custom_widget(widget)
    """

    def __new__(
        cls,
        name: str = "",
        label: str = "",
        file_filter: str = "All Files (*.*)",
        text: str = "",
        placeholder: str = "Select file...",
    ):
        """
        Create a new NodeFilePathWidget.

        Args:
            name: Property name for the node
            label: Label text displayed above the widget
            file_filter: File type filter for dialog (e.g., "Excel Files (*.xlsx)")
            text: Initial text value
            placeholder: Placeholder text when empty
        """
        return create_file_path_widget(name, label, file_filter, placeholder, text)


def create_directory_path_widget(
    name: str, label: str, placeholder: str, text: str = ""
):
    """
    Factory function to create a NodeDirectoryPathWidget.

    This creates a proper NodeBaseWidget subclass instance with directory browse functionality.
    Includes variable picker integration via VariableAwareLineEdit - hover to see {x} button.
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget
        from PySide6 import QtWidgets
    except ImportError:
        logger.error("NodeGraphQt not available")
        return None

    # Create the container widget with horizontal layout
    container = QtWidgets.QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    # Set explicit minimum size to ensure visibility
    container.setMinimumHeight(26)
    container.setMinimumWidth(160)
    container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    # Create variable-aware line edit with {x} button for variable insertion
    line_edit = VariableAwareLineEdit()
    line_edit.setText(text)
    line_edit.setPlaceholderText(placeholder)
    line_edit.setMinimumHeight(24)
    line_edit.setMinimumWidth(100)
    line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    # Padding on right side accommodates the {x} variable button
    line_edit.setStyleSheet("""
        QLineEdit {
            background: #3c3c50;
            border: 1px solid #505064;
            border-radius: 3px;
            color: #e6e6e6;
            padding: 2px 28px 2px 4px;
        }
        QLineEdit:focus {
            border: 1px solid #6496c8;
        }
    """)
    layout.addWidget(line_edit, 1)

    # Create browse button - use folder icon style
    browse_btn = QPushButton("...")
    browse_btn.setFixedSize(30, 24)
    browse_btn.setToolTip("Browse for folder")
    # Orange background for folder selection (differentiate from file selection)
    browse_btn.setStyleSheet("""
        QPushButton {
            background-color: #d97706;
            border: 1px solid #b45309;
            border-radius: 3px;
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
            padding: 0px;
        }
        QPushButton:hover {
            background-color: #f59e0b;
        }
        QPushButton:pressed {
            background-color: #92400e;
        }
    """)

    def on_browse():
        import os

        current_path = line_edit.text().strip()
        start_dir = ""
        if current_path and os.path.isdir(current_path):
            start_dir = current_path

        path = QFileDialog.getExistingDirectory(
            None,
            "Select Directory",
            start_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if path:
            line_edit.setText(path)
            # CRITICAL: Manually trigger value change - setText() doesn't emit editingFinished
            # Without this, the property value is never synced to the model
            widget.on_value_changed()
            logger.debug(f"Selected directory: {path}")

    browse_btn.clicked.connect(on_browse)
    layout.addWidget(browse_btn)

    # Create NodeBaseWidget and set up
    widget = NodeBaseWidget(parent=None, name=name, label=label)
    widget.set_custom_widget(container)

    # Force geometry update
    container.adjustSize()

    # Connect line edit changes to widget's value changed signal
    line_edit.editingFinished.connect(widget.on_value_changed)

    # Connect variable insertion to trigger value change
    line_edit.variable_inserted.connect(lambda _: widget.on_value_changed())

    # Store reference to line edit for get/set value
    widget._line_edit = line_edit
    widget._browse_btn = browse_btn

    # Override get_value and set_value
    def get_value():
        return line_edit.text()

    def set_value(value):
        line_edit.setText(str(value) if value else "")

    widget.get_value = get_value
    widget.set_value = set_value

    return widget


class NodeDirectoryPathWidget:
    """
    Directory path widget for NodeGraphQt nodes.

    Provides a text input with a folder browse button that opens
    a directory selection dialog.

    Usage in visual node:
        from casare_rpa.presentation.canvas.graph.node_widgets import NodeDirectoryPathWidget

        def __init__(self):
            super().__init__()
            widget = NodeDirectoryPathWidget(
                name="output_dir",
                label="Output Directory",
            )
            self.add_custom_widget(widget)
            widget.setParentItem(self.view)
    """

    def __new__(
        cls,
        name: str = "",
        label: str = "",
        text: str = "",
        placeholder: str = "Select directory...",
    ):
        """
        Create a new NodeDirectoryPathWidget.

        Args:
            name: Property name for the node
            label: Label text displayed above the widget
            text: Initial text value
            placeholder: Placeholder text when empty
        """
        return create_directory_path_widget(name, label, placeholder, text)


# =============================================================================
# Helper function to set node context for variable picker
# =============================================================================


def set_variable_picker_node_context(
    line_edit: VariableAwareLineEdit,
    node_widget,
) -> None:
    """
    Set the node context on a VariableAwareLineEdit for upstream variable detection.

    This enables the variable picker to show output variables from nodes
    connected upstream of the current node.

    Args:
        line_edit: The VariableAwareLineEdit to configure
        node_widget: The NodeBaseWidget containing the line edit

    Note:
        This function attempts to discover the node and graph from the widget
        hierarchy. It should be called after the widget is added to a node.
        If discovery fails (widget not yet in hierarchy), context will be
        set to None and the picker will still work with workflow/system variables.
    """
    try:
        # Try to discover the owning node from the widget hierarchy
        node = None
        graph = None

        # Walk up the parent chain to find the node
        if hasattr(node_widget, "node"):
            node = node_widget.node
        elif hasattr(node_widget, "_node"):
            node = node_widget._node

        if node:
            # Get node ID
            node_id = None
            if hasattr(node, "get_property"):
                node_id = node.get_property("node_id")
            elif hasattr(node, "id") and callable(node.id):
                node_id = node.id()

            # Get graph reference
            if hasattr(node, "graph"):
                graph = node.graph

            # Set context on line edit
            if node_id and graph:
                line_edit.set_node_context(node_id, graph)
                logger.debug(f"Variable picker node context set: node_id={node_id}")
                return

        # If discovery failed, log debug message
        logger.debug(
            "Variable picker: Node context not available (widget not yet in hierarchy)"
        )

    except Exception as e:
        logger.debug(f"Variable picker: Could not set node context: {e}")


def update_node_context_for_widgets(node) -> None:
    """
    Update node context for all VariableAwareLineEdit widgets in a node.

    Call this after a node is fully added to the graph to enable
    upstream variable detection in all text inputs.

    Args:
        node: The visual node (VisualNode subclass) to update
    """
    try:
        # Get node ID
        node_id = None
        if hasattr(node, "get_property"):
            node_id = node.get_property("node_id")
        elif hasattr(node, "id") and callable(node.id):
            node_id = node.id()

        # Get graph
        graph = None
        if hasattr(node, "graph"):
            graph = node.graph

        if not node_id or not graph:
            return

        # Find all widgets in the node
        widgets = {}
        if hasattr(node, "widgets") and callable(node.widgets):
            widgets = node.widgets()

        for widget_name, widget in widgets.items():
            # Check if widget has a VariableAwareLineEdit
            if hasattr(widget, "_line_edit"):
                line_edit = widget._line_edit
                if isinstance(line_edit, VariableAwareLineEdit):
                    line_edit.set_node_context(node_id, graph)

            # Also check for direct custom widget
            if hasattr(widget, "get_custom_widget"):
                custom = widget.get_custom_widget()
                if custom and hasattr(custom, "findChildren"):
                    # Find any VariableAwareLineEdit in the custom widget tree
                    for child in custom.findChildren(VariableAwareLineEdit):
                        child.set_node_context(node_id, graph)

    except Exception as e:
        logger.debug(f"Could not update node context for widgets: {e}")


# =============================================================================
# Selector Widget for Element Picking
# =============================================================================


def create_selector_widget(name: str, label: str, placeholder: str, text: str = ""):
    """
    Factory function to create a NodeSelectorWidget.

    Creates a NodeBaseWidget with selector input and element picker button.
    The picker button opens the Element Selector Dialog for visual element selection.
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget
        from PySide6 import QtWidgets
    except ImportError:
        logger.error("NodeGraphQt not available")
        return None

    # Create the container widget with horizontal layout
    container = QtWidgets.QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    # Set explicit minimum size
    container.setMinimumHeight(26)
    container.setMinimumWidth(160)
    container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    # Create variable-aware line edit
    line_edit = VariableAwareLineEdit()
    line_edit.setText(text)
    line_edit.setPlaceholderText(placeholder)
    line_edit.setMinimumHeight(24)
    line_edit.setMinimumWidth(100)
    line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    # Blue-tinted styling for selectors
    line_edit.setStyleSheet("""
        QLineEdit {
            background: #3d3d3d;
            border: 1px solid #4a4a4a;
            border-radius: 3px;
            color: #60a5fa;
            padding: 2px 28px 2px 4px;
            font-family: Consolas, monospace;
        }
        QLineEdit:focus {
            border: 1px solid #3b82f6;
        }
    """)
    layout.addWidget(line_edit, 1)

    # Create element picker button
    picker_btn = QPushButton("...")
    picker_btn.setFixedSize(30, 24)
    picker_btn.setToolTip("Click to open Element Selector")
    # Blue background for selector picking
    picker_btn.setStyleSheet("""
        QPushButton {
            background-color: #3b82f6;
            border: 1px solid #2563eb;
            border-radius: 3px;
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
            padding: 0px;
        }
        QPushButton:hover {
            background-color: #2563eb;
        }
        QPushButton:pressed {
            background-color: #1d4ed8;
        }
    """)

    # Store references for later
    widget_ref = {"widget": None, "node": None}

    def on_picker_click():
        """Open Element Selector Dialog."""
        try:
            from casare_rpa.presentation.canvas.selectors.element_selector_dialog import (
                ElementSelectorDialog,
            )

            # Try to get browser page from node context
            browser_page = None
            node = widget_ref.get("node")

            if node:
                # Try to get browser page from execution context or controller
                if hasattr(node, "graph") and node.graph:
                    graph = node.graph
                    # Try to get from selector controller via main window
                    if hasattr(graph, "_viewer") and graph._viewer:
                        viewer = graph._viewer
                        if hasattr(viewer, "window"):
                            main_window = viewer.window()
                            if main_window and hasattr(
                                main_window, "_selector_controller"
                            ):
                                browser_page = (
                                    main_window._selector_controller.get_browser_page()
                                )

            # Determine mode
            mode = "browser" if browser_page else "desktop"

            # Create and show dialog
            dialog = ElementSelectorDialog(
                parent=None,
                mode=mode,
                browser_page=browser_page,
                initial_selector=line_edit.text(),
                target_node=node,
                property_name=name,
            )

            def on_selector_confirmed(result):
                """Handle confirmed selector."""
                if not result:
                    return

                # Special handling for image_template property
                if name == "image_template":
                    # Extract cv_template from healing_context
                    image_base64 = None
                    logger.info(
                        "ImageTemplate: Processing result for image_template property"
                    )
                    logger.info(
                        f"ImageTemplate: has healing_context={hasattr(result, 'healing_context')}"
                    )

                    if hasattr(result, "healing_context") and result.healing_context:
                        logger.info(
                            f"ImageTemplate: healing_context keys={list(result.healing_context.keys())}"
                        )
                        cv_template = result.healing_context.get("cv_template", {})
                        if cv_template:
                            logger.info(
                                f"ImageTemplate: cv_template keys={list(cv_template.keys())}"
                            )
                            image_base64 = cv_template.get("image_base64", "")
                            logger.info(
                                f"ImageTemplate: image_base64 length={len(image_base64) if image_base64 else 0}"
                            )
                        else:
                            logger.warning(
                                "ImageTemplate: cv_template is empty or missing"
                            )
                    else:
                        logger.warning(
                            f"ImageTemplate: No healing_context or empty. Value={getattr(result, 'healing_context', 'N/A')}"
                        )

                    if image_base64:
                        line_edit.setText(image_base64)
                        if widget_ref.get("widget"):
                            widget_ref["widget"].on_value_changed()
                        logger.info(f"Image template set: {len(image_base64)} chars")
                    else:
                        # Fallback: use selector_value if no cv_template
                        if hasattr(result, "selector_value"):
                            line_edit.setText(result.selector_value)
                            if widget_ref.get("widget"):
                                widget_ref["widget"].on_value_changed()
                        logger.warning(
                            "No cv_template found in result, using selector_value as fallback"
                        )
                    return

                # Standard selector handling
                if hasattr(result, "selector_value"):
                    line_edit.setText(result.selector_value)
                    # Trigger value change
                    if widget_ref.get("widget"):
                        widget_ref["widget"].on_value_changed()
                    logger.debug(f"Selector set: {result.selector_value[:50]}...")

                    # Save anchor config if present
                    _save_anchor_to_node(result, node, name)

            dialog.selector_confirmed.connect(on_selector_confirmed)
            dialog.exec()

        except ImportError as e:
            logger.warning(f"Element Selector Dialog not available: {e}")
        except Exception as e:
            logger.error(f"Failed to open Element Selector: {e}")

    picker_btn.clicked.connect(on_picker_click)
    layout.addWidget(picker_btn)

    # Create NodeBaseWidget
    widget = NodeBaseWidget(parent=None, name=name, label=label)
    widget.set_custom_widget(container)
    widget_ref["widget"] = widget

    # Force geometry update
    container.adjustSize()

    # Connect line edit changes
    line_edit.editingFinished.connect(widget.on_value_changed)
    line_edit.variable_inserted.connect(lambda _: widget.on_value_changed())

    # Store references
    widget._line_edit = line_edit
    widget._picker_btn = picker_btn

    # Override get_value and set_value
    def get_value():
        return line_edit.text()

    def set_value(value):
        line_edit.setText(str(value) if value else "")

    widget.get_value = get_value
    widget.set_value = set_value

    # Method to set node reference (called after widget is added to node)
    def set_node_ref(node):
        widget_ref["node"] = node

    widget.set_node_ref = set_node_ref

    return widget


def _save_anchor_to_node(result, node, property_name: str):
    """Save anchor configuration to node if present in result."""
    if not node or not result:
        return

    try:
        if hasattr(result, "anchor") and result.anchor:
            from casare_rpa.nodes.browser.anchor_config import NodeAnchorConfig

            anchor_data = result.anchor
            config = NodeAnchorConfig(
                enabled=True,
                selector=getattr(anchor_data, "selector", ""),
                position=getattr(anchor_data, "position", "near"),
                text=getattr(anchor_data, "text_content", ""),
                tag_name=getattr(anchor_data, "tag_name", ""),
                stability_score=getattr(anchor_data, "stability_score", 0.0),
                offset_x=getattr(anchor_data, "offset_x", 0),
                offset_y=getattr(anchor_data, "offset_y", 0),
            )
            anchor_json = config.to_json()

            # Save to node
            if hasattr(node, "set_property"):
                node.set_property("anchor_config", anchor_json)
                logger.info(f"Saved anchor config to node for {property_name}")

    except Exception as e:
        logger.warning(f"Failed to save anchor config: {e}")


class NodeSelectorWidget:
    """
    Selector widget for NodeGraphQt nodes.

    Provides a text input with an element picker button that opens
    the Element Selector Dialog for visual element selection.

    Usage in visual node:
        from casare_rpa.presentation.canvas.graph.node_widgets import NodeSelectorWidget

        def __init__(self):
            super().__init__()
            widget = NodeSelectorWidget(
                name="selector",
                label="Element Selector",
            )
            self.add_custom_widget(widget)
            widget.setParentItem(self.view)
    """

    def __new__(
        cls,
        name: str = "",
        label: str = "",
        text: str = "",
        placeholder: str = "Enter selector or click ...",
    ):
        """
        Create a new NodeSelectorWidget.

        Args:
            name: Property name for the node
            label: Label text displayed above the widget
            text: Initial text value
            placeholder: Placeholder text when empty
        """
        return create_selector_widget(name, label, placeholder, text)


# =============================================================================
# Google Integration Widgets
# =============================================================================


def _apply_combo_z_fix(widget) -> None:
    """
    Apply z-value fix to a NodeBaseWidget containing a combo box.

    When QComboBox is embedded in a QGraphicsProxyWidget, the dropdown popup
    can get clipped by other widgets. This fix raises the z-value when
    the popup is shown and restores it when hidden.

    Args:
        widget: NodeBaseWidget containing a picker with _combo attribute
    """
    try:
        picker = getattr(widget, "_picker", None)
        if not picker:
            return

        combo = getattr(picker, "_combo", None)
        if not combo:
            return

        # Store original z-value for restoration
        widget._original_z = widget.zValue() if hasattr(widget, "zValue") else 0

        # Store original methods
        original_show_popup = combo.showPopup
        original_hide_popup = combo.hidePopup

        def patched_show_popup():
            """Raise z-value when popup opens."""
            if hasattr(widget, "setZValue"):
                widget.setZValue(COMBO_RAISED_Z)
            original_show_popup()

        def patched_hide_popup():
            """Restore original z-value when popup closes."""
            try:
                original_hide_popup()
                if hasattr(widget, "setZValue") and hasattr(widget, "_original_z"):
                    widget.setZValue(widget._original_z)
            except RuntimeError:
                pass  # Widget already deleted

        # Apply patches
        combo.showPopup = patched_show_popup
        combo.hidePopup = patched_hide_popup

    except Exception as e:
        logger.debug(f"Could not apply combo z-fix: {e}")


def create_google_credential_widget(
    name: str,
    label: str,
    scopes: list = None,
):
    """
    Factory function to create a Google credential picker widget.

    Creates a dropdown showing only Google OAuth credentials with
    "Add Google Account..." option at the bottom.

    Args:
        name: Property name for the node
        label: Label text displayed above the widget
        scopes: Optional list of required scopes (for filtering)

    Returns:
        NodeBaseWidget with GoogleCredentialPicker
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget
        from casare_rpa.presentation.canvas.ui.widgets.google_credential_picker import (
            GoogleCredentialPicker,
        )
    except ImportError as e:
        logger.error(f"Google credential picker not available: {e}")
        return None

    # Create the picker widget
    picker = GoogleCredentialPicker(required_scopes=scopes or [])

    # Create NodeBaseWidget
    widget = NodeBaseWidget(parent=None, name=name, label=label)
    widget.set_custom_widget(picker)

    # Connect signals
    picker.credential_changed.connect(lambda _: widget.on_value_changed())

    # Store reference
    widget._picker = picker

    # Apply z-value fix for combo popup visibility
    _apply_combo_z_fix(widget)

    # Override get_value and set_value
    def get_value():
        return picker.get_credential_id()

    def set_value(value):
        if value:
            picker.set_credential_id(value)

    widget.get_value = get_value
    widget.set_value = set_value

    return widget


def create_google_spreadsheet_widget(
    name: str,
    label: str,
    credential_widget=None,
):
    """
    Factory function to create a Google Spreadsheet picker widget.

    Creates a cascading dropdown that loads spreadsheets when a
    credential is selected.

    Args:
        name: Property name for the node
        label: Label text displayed above the widget
        credential_widget: Optional parent credential widget for cascading

    Returns:
        NodeBaseWidget with GoogleSpreadsheetPicker
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget
        from casare_rpa.presentation.canvas.ui.widgets.google_pickers import (
            GoogleSpreadsheetPicker,
        )
    except ImportError as e:
        logger.error(f"Google spreadsheet picker not available: {e}")
        return None

    # Create the picker widget
    picker = GoogleSpreadsheetPicker()

    # Connect to parent credential widget if provided
    if credential_widget and hasattr(credential_widget, "_picker"):
        cred_picker = credential_widget._picker
        cred_picker.credential_changed.connect(
            lambda cred_id: picker.set_parent_value(cred_id)
        )
        # Initialize with current credential if already selected
        current_cred = cred_picker.get_credential_id()
        if current_cred:
            picker.set_parent_value(current_cred)

    # Create NodeBaseWidget
    widget = NodeBaseWidget(parent=None, name=name, label=label)
    widget.set_custom_widget(picker)

    # Connect signals
    picker.selection_changed.connect(lambda: widget.on_value_changed())

    # Store reference
    widget._picker = picker

    # Apply z-value fix for combo popup visibility
    _apply_combo_z_fix(widget)

    # Override get_value and set_value
    def get_value():
        return picker.get_selected_id()

    def set_value(value):
        if value:
            picker.set_selected_id(value)

    widget.get_value = get_value
    widget.set_value = set_value

    return widget


def create_google_sheet_widget(
    name: str,
    label: str,
    spreadsheet_widget=None,
    credential_widget=None,
):
    """
    Factory function to create a Google Sheet picker widget.

    Creates a cascading dropdown that loads sheets when a
    spreadsheet is selected.

    Args:
        name: Property name for the node
        label: Label text displayed above the widget
        spreadsheet_widget: Optional parent spreadsheet widget for cascading
        credential_widget: Optional credential widget for authentication

    Returns:
        NodeBaseWidget with GoogleSheetPicker
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget
        from casare_rpa.presentation.canvas.ui.widgets.google_pickers import (
            GoogleSheetPicker,
        )
    except ImportError as e:
        logger.error(f"Google sheet picker not available: {e}")
        return None

    # Create the picker widget
    picker = GoogleSheetPicker()

    # Connect to parent credential widget if provided
    if credential_widget and hasattr(credential_widget, "_picker"):
        credential_widget._picker.credential_changed.connect(
            lambda cred_id: picker.set_credential_id(cred_id)
        )

    # Connect to parent spreadsheet widget if provided
    if spreadsheet_widget and hasattr(spreadsheet_widget, "_picker"):
        spreadsheet_widget._picker.selection_changed.connect(
            lambda: picker.set_parent_value(
                spreadsheet_widget._picker.get_selected_id()
            )
        )

    # Create NodeBaseWidget
    widget = NodeBaseWidget(parent=None, name=name, label=label)
    widget.set_custom_widget(picker)

    # Connect signals
    picker.selection_changed.connect(lambda: widget.on_value_changed())

    # Store reference
    widget._picker = picker

    # Apply z-value fix for combo popup visibility
    _apply_combo_z_fix(widget)

    # Override get_value and set_value
    def get_value():
        return picker.get_selected_id()

    def set_value(value):
        if value:
            picker.set_selected_id(value)

    widget.get_value = get_value
    widget.set_value = set_value

    return widget


def create_google_drive_file_widget(
    name: str,
    label: str,
    credential_widget=None,
    mime_types: list = None,
    folder_id: str = None,
):
    """
    Factory function to create a Google Drive file picker widget.

    Args:
        name: Property name for the node
        label: Label text displayed above the widget
        credential_widget: Optional parent credential widget for cascading
        mime_types: Optional list of MIME types to filter (first one used)
        folder_id: Optional folder ID to restrict search

    Returns:
        NodeBaseWidget with GoogleDriveFilePicker
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget
        from casare_rpa.presentation.canvas.ui.widgets.google_pickers import (
            GoogleDriveFilePicker,
        )
    except ImportError as e:
        logger.error(f"Google Drive file picker not available: {e}")
        return None

    # Create the picker widget (GoogleDriveFilePicker takes mime_type singular)
    mime_type = mime_types[0] if mime_types else None
    picker = GoogleDriveFilePicker(mime_type=mime_type, folder_id=folder_id)

    # Connect to parent credential widget if provided
    if credential_widget and hasattr(credential_widget, "_picker"):
        cred_picker = credential_widget._picker
        cred_picker.credential_changed.connect(
            lambda cred_id: picker.set_parent_value(cred_id)
        )
        # Initialize with current credential if already selected
        current_cred = cred_picker.get_credential_id()
        if current_cred:
            picker.set_parent_value(current_cred)

    # Create NodeBaseWidget
    widget = NodeBaseWidget(parent=None, name=name, label=label)
    widget.set_custom_widget(picker)

    # Connect signals
    picker.selection_changed.connect(lambda: widget.on_value_changed())

    # Store reference
    widget._picker = picker

    # Apply z-value fix for combo popup visibility
    _apply_combo_z_fix(widget)

    # Override get_value and set_value
    def get_value():
        return picker.get_selected_id()

    def set_value(value):
        if value:
            picker.set_selected_id(value)

    widget.get_value = get_value
    widget.set_value = set_value

    return widget


def create_google_drive_folder_widget(
    name: str,
    label: str,
    credential_widget=None,
    enhanced: bool = False,
):
    """
    Factory function to create a Google Drive folder picker widget.

    Args:
        name: Property name for the node
        label: Label text displayed above the widget
        credential_widget: Optional parent credential widget for cascading
        enhanced: If True, use the enhanced folder navigator with
                  browse/search/manual ID modes. If False (default),
                  use simple dropdown picker.

    Returns:
        NodeBaseWidget with GoogleDriveFolderPicker or GoogleDriveFolderNavigator
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget
    except ImportError as e:
        logger.error(f"NodeGraphQt not available: {e}")
        return None

    if enhanced:
        # Use enhanced navigator with browse/search/manual modes
        return _create_enhanced_folder_widget(name, label, credential_widget)
    else:
        # Use simple dropdown picker (original behavior)
        return _create_simple_folder_widget(name, label, credential_widget)


def _create_simple_folder_widget(
    name: str,
    label: str,
    credential_widget=None,
):
    """Create simple folder dropdown widget (original implementation)."""
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget
        from casare_rpa.presentation.canvas.ui.widgets.google_pickers import (
            GoogleDriveFolderPicker,
        )
    except ImportError as e:
        logger.error(f"Google Drive folder picker not available: {e}")
        return None

    # Create the picker widget
    picker = GoogleDriveFolderPicker()

    # Connect to parent credential widget if provided
    if credential_widget and hasattr(credential_widget, "_picker"):
        cred_picker = credential_widget._picker
        cred_picker.credential_changed.connect(
            lambda cred_id: picker.set_parent_value(cred_id)
        )
        # Initialize with current credential if already selected
        current_cred = cred_picker.get_credential_id()
        if current_cred:
            picker.set_parent_value(current_cred)

    # Create NodeBaseWidget
    widget = NodeBaseWidget(parent=None, name=name, label=label)
    widget.set_custom_widget(picker)

    # Connect signals
    picker.selection_changed.connect(lambda: widget.on_value_changed())

    # Store reference
    widget._picker = picker

    # Apply z-value fix for combo popup visibility
    _apply_combo_z_fix(widget)

    # Override get_value and set_value
    def get_value():
        return picker.get_selected_id()

    def set_value(value):
        if value:
            picker.set_selected_id(value)

    widget.get_value = get_value
    widget.set_value = set_value

    return widget


def _create_enhanced_folder_widget(
    name: str,
    label: str,
    credential_widget=None,
):
    """
    Create enhanced folder navigator widget with browse/search/manual ID modes.

    Features:
    - Browse mode: Navigate folder hierarchy with breadcrumb
    - Search mode: Search folders across Drive
    - Manual ID mode: Paste folder ID from Google Drive URL
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget
        from casare_rpa.presentation.canvas.ui.widgets.google_folder_navigator import (
            GoogleDriveFolderNavigator,
        )
    except ImportError as e:
        logger.error(f"Google Drive folder navigator not available: {e}")
        # Fall back to simple widget
        return _create_simple_folder_widget(name, label, credential_widget)

    # Create the navigator widget
    navigator = GoogleDriveFolderNavigator(show_mode_buttons=True)

    # Connect to parent credential widget if provided
    if credential_widget and hasattr(credential_widget, "_picker"):
        cred_picker = credential_widget._picker
        cred_picker.credential_changed.connect(
            lambda cred_id: navigator.set_credential_id(cred_id)
        )
        # Initialize with current credential if already selected
        current_cred = cred_picker.get_credential_id()
        if current_cred:
            navigator.set_credential_id(current_cred)

    # Create NodeBaseWidget
    widget = NodeBaseWidget(parent=None, name=name, label=label)
    widget.set_custom_widget(navigator)

    # Connect signals
    navigator.folder_selected.connect(lambda: widget.on_value_changed())

    # Store reference
    widget._navigator = navigator
    widget._picker = navigator  # For compatibility with z-fix

    # Override get_value and set_value
    def get_value():
        return navigator.get_folder_id()

    def set_value(value):
        if value:
            navigator.set_folder_id(value)

    widget.get_value = get_value
    widget.set_value = set_value

    return widget


class NodeGoogleCredentialWidget:
    """
    Google credential picker widget for NodeGraphQt nodes.

    Shows a dropdown with connected Google accounts and
    "Add Google Account..." option to add new ones.

    Usage:
        widget = NodeGoogleCredentialWidget(name="credential", label="Google Account")
        self.add_custom_widget(widget)
    """

    def __new__(
        cls,
        name: str = "",
        label: str = "",
        scopes: list = None,
    ):
        return create_google_credential_widget(name, label, scopes)


class NodeGoogleSpreadsheetWidget:
    """
    Google Spreadsheet picker widget for NodeGraphQt nodes.

    Cascading dropdown that loads spreadsheets from Google Drive.

    Usage:
        cred_widget = NodeGoogleCredentialWidget(...)
        sheet_widget = NodeGoogleSpreadsheetWidget(
            name="spreadsheet",
            label="Spreadsheet",
            credential_widget=cred_widget,
        )
    """

    def __new__(
        cls,
        name: str = "",
        label: str = "",
        credential_widget=None,
    ):
        return create_google_spreadsheet_widget(name, label, credential_widget)


class NodeGoogleSheetWidget:
    """
    Google Sheet picker widget for NodeGraphQt nodes.

    Cascading dropdown that loads sheet tabs from a spreadsheet.
    """

    def __new__(
        cls,
        name: str = "",
        label: str = "",
        spreadsheet_widget=None,
        credential_widget=None,
    ):
        return create_google_sheet_widget(
            name, label, spreadsheet_widget, credential_widget
        )


class NodeGoogleDriveFileWidget:
    """
    Google Drive file picker widget for NodeGraphQt nodes.
    """

    def __new__(
        cls,
        name: str = "",
        label: str = "",
        credential_widget=None,
        mime_types: list = None,
        folder_id: str = None,
    ):
        return create_google_drive_file_widget(
            name, label, credential_widget, mime_types, folder_id
        )


class NodeGoogleDriveFolderWidget:
    """
    Google Drive folder picker widget for NodeGraphQt nodes.

    With enhanced=False (default): Simple dropdown with folder list.
    With enhanced=True: Full navigator with browse/search/manual ID modes.

    Usage:
        # Simple dropdown
        widget = NodeGoogleDriveFolderWidget(
            name="folder_id",
            label="Destination Folder",
            credential_widget=cred_widget,
        )

        # Enhanced navigator
        widget = NodeGoogleDriveFolderWidget(
            name="folder_id",
            label="Destination Folder",
            credential_widget=cred_widget,
            enhanced=True,
        )
    """

    def __new__(
        cls,
        name: str = "",
        label: str = "",
        credential_widget=None,
        enhanced: bool = False,
    ):
        return create_google_drive_folder_widget(
            name, label, credential_widget, enhanced
        )
