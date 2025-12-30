<rules category="ui">
  <widgets>
    <name>Widget Patterns</name>

    <base_widget>
      <inherit>BaseWidget for consistent styling</inherit>
      <file>@src/casare_rpa/presentation/canvas/ui/widgets/</file>

      <correct><![CDATA[
from casare_rpa.presentation.canvas.ui.widgets import BaseWidget

class MyWidget(BaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self) -> None:
        """Initialize UI components - override this method."""
        self.label = QLabel("Hello")
        self.button = QPushButton("Click me")
        self.button.clicked.connect(self._on_click)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        self.setLayout(layout)

    @Slot()
    def _on_click(self):
        # Handle click
        pass
]]></correct>
    </base_widget>

    <v2_primitives>
      <inherit>BasePrimitive for V2 components</inherit>
      <file>@src/casare_rpa/presentation/canvas/ui/widgets/primitives/</file>

      <correct><![CDATA[
from casare_rpa.presentation.canvas.ui.widgets.primitives import BasePrimitive

class MyV2Button(BasePrimitive):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = text
        self.setup_ui()

    def setup_ui(self) -> None:
        self.setText(self._text)
        self.setStyleSheet(self._get_stylesheet())
]]></correct>
    </v2_primitives>

    <signals_slots>
      <rule>Use @Slot decorator on all slot methods</rule>
      <rule>Use functools.partial instead of lambdas</rule>

      <correct><![CDATA[
from PySide6.QtCore import Slot
from functools import partial

class MyController:
    def __init__(self):
        self.view.button.clicked.connect(
            partial(self._handle_click, id="my_id")
        )

    @Slot()
    def _handle_click(self):
        # Handle click
        pass
]]></correct>

      <forbidden><![CDATA[
# NO lambdas for signal handlers
self.button.clicked.connect(lambda: self.handle())

# NO @Slot missing
def handle_click(self):
    pass
]]></forbidden>
    </signals_slots>
  </widgets>

  <popups>
    <base>PopupWindowBase for all popups</base>
    <file>@src/casare_rpa/presentation/canvas/ui/widgets/popups/</file>

    <correct><![CDATA[
from casare_rpa.presentation.canvas.ui.widgets.popups import PopupWindowBase
from casare_rpa.presentation.canvas.managers.popup_manager import PopupManager

class MyPopup(PopupWindowBase):
    def __init__(self, parent=None):
        super().__init__(parent, title="My Popup", size=(400, 300))
        self.setup_ui()

    def setup_ui(self) -> None:
        self.content_label = QLabel("Popup content")
        layout = QVBoxLayout()
        layout.addWidget(self.content_label)
        self.setLayout(layout)

    def showEvent(self, event):
        super().showEvent(event)
        PopupManager.register(self)

    def closeEvent(self, event):
        PopupManager.unregister(self)
        super().closeEvent(event)
]]></correct>

    <pin_state>
      <use>PopupManager.register(self, pinned=True) for persistent popups</use>
      <description>Prevents click-outside-to-close</description>
    </pin_state>

    <lifecycle>
      <rule>Always register in showEvent</rule>
      <rule>Always unregister in closeEvent</rule>
      <forbidden>Don't manage popups manually with event filters</forbidden>
    </lifecycle>
  </popups>

  <graph>
    <name>Visual Node Patterns</name>

    <base>VisualNode for all visual nodes</base>
    <file>@src/casare_rpa/presentation/canvas/visual_nodes/base_visual_node.py</file>

    <correct><![CDATA[
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode

class VisualStartNode(VisualNode):
    __identifier__ = "casare_rpa.basic"
    NODE_NAME = "Start"
    NODE_CATEGORY = "basic"

    def setup_ports(self) -> None:
        self.add_exec_output("exec_out")

    def setup_widgets(self) -> None:
        # Add custom widgets if needed
        pass
]]></correct>

    <geometry>
      <critical>Call prepareGeometryChange() before geometry changes</critical>

      <correct><![CDATA[
def set_collapsed(self, collapsed: bool) -> None:
    if self._is_collapsed == collapsed:
        return
    self._is_collapsed = collapsed
    self.prepareGeometryChange()  # CRITICAL
    self.update()
]]></correct>

      <wrong><![CDATA[
def resize_node(self, new_size):
    self._size = new_size
    self.update()  # Missing prepareGeometryChange!
]]></wrong>
    </geometry>

    <animations>
      <use>AnimationCoordinator for centralized animations</use>

      <correct><![CDATA[
from casare_rpa.presentation.canvas.graph.custom_node_item import AnimationCoordinator

coordinator = AnimationCoordinator.get_instance()
coordinator.register_animation(self)
]]></correct>
    </animations>
  </graph>
</rules>
